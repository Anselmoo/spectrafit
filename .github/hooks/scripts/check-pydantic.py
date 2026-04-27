#!/usr/bin/env python3
# ruff: noqa  — hook script, not part of spectrafit/ package; print() is the hook I/O protocol
"""Hook: check-pydantic.py — AST-based Pydantic v2 enforcement.

Event: PreToolUse
Purpose: AST-based Pydantic v2 enforcement — far more accurate than grep.

Violations detected:
  - @dataclass without BaseModel inheritance (class-level check)
  - ClassVar[<scalar>] fields that should be Pydantic fields
  - dict[str, Any] / dict[str, object] as return type or field annotation
  - extra="allow" without a migration comment on the same or adjacent line
  - from typing import Optional (use X | None instead)
  - TypeAlias usage (use PEP 695 type keyword)
  - class X(str, Enum) pattern (use StrEnum)
  - Field(default_factory=dict) without an explicit inner type annotation
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_input() -> dict:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def get_file_path(data: dict) -> str:
    inp = data.get("tool_input", {})
    return inp.get("filePath") or inp.get("path") or ""


def get_content(data: dict) -> str:
    inp = data.get("tool_input", {})
    return inp.get("content") or inp.get("newString") or ""


def is_writing_tool(tool_name: str) -> bool:
    return tool_name in {
        "create_file",
        "replace_string_in_file",
        "multi_replace_string_in_file",
    }


def allow() -> None:
    print(json.dumps({"continue": True}))
    sys.exit(0)


def ask(file_path: str, violations: list[str]) -> None:
    bullet_list = "\n".join(f"  • {v}" for v in violations)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"Pydantic v2 enforcement violations in {file_path}:\n"
                f"{bullet_list}\n\n"
                "Fix before proceeding, or confirm this is an intentional exception with a comment."
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(0)


# ---------------------------------------------------------------------------
# AST visitors
# ---------------------------------------------------------------------------


class PydanticViolationVisitor(ast.NodeVisitor):
    """Walk an AST and collect Pydantic v2 violations."""

    def __init__(self, source_lines: list[str]) -> None:
        self.violations: list[str] = []
        self._source_lines = source_lines

    # -- Imports ----------------------------------------------------------------

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module == "typing":
            names = {alias.name for alias in node.names}
            if "Optional" in names:
                self.violations.append(
                    f"Line {node.lineno}: `from typing import Optional` — use `X | None` (Python 3.12+)"
                )
            if "TypeAlias" in names:
                self.violations.append(
                    f"Line {node.lineno}: `from typing import TypeAlias` — use PEP 695 `type X = ...` keyword"
                )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        self.generic_visit(node)

    # -- Class definitions -------------------------------------------------------

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._check_dataclass(node)
        self._check_str_enum(node)
        self._check_classvar_fields(node)
        self.generic_visit(node)

    def _check_dataclass(self, node: ast.ClassDef) -> None:
        decorator_names = {
            (
                d.id
                if isinstance(d, ast.Name)
                else d.func.id
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
                else d.attr
                if isinstance(d, ast.Attribute)
                else d.func.attr
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                else ""
            )
            for d in node.decorator_list
        }
        base_names = {
            (
                b.id
                if isinstance(b, ast.Name)
                else b.attr
                if isinstance(b, ast.Attribute)
                else ""
            )
            for b in node.bases
        }
        if "dataclass" in decorator_names and "BaseModel" not in base_names:
            self.violations.append(
                f"Line {node.lineno}: `@dataclass` on `{node.name}` without BaseModel — "
                "use `class {node.name}(BaseModel):` with `ConfigDict(frozen=True)` instead"
            )

    def _check_str_enum(self, node: ast.ClassDef) -> None:
        """Detect class X(str, Enum) — should be StrEnum."""
        base_names = [
            (
                b.id
                if isinstance(b, ast.Name)
                else b.attr
                if isinstance(b, ast.Attribute)
                else ""
            )
            for b in node.bases
        ]
        if "str" in base_names and "Enum" in base_names:
            self.violations.append(
                f"Line {node.lineno}: `class {node.name}(str, Enum)` — use `class {node.name}(StrEnum)` instead"
            )

    def _check_classvar_fields(self, node: ast.ClassDef) -> None:
        """Detect ClassVar[scalar] used in Pydantic models (Pydantic ignores them)."""
        # Only check classes that appear to extend BaseModel
        base_names = {
            (
                b.id
                if isinstance(b, ast.Name)
                else b.attr
                if isinstance(b, ast.Attribute)
                else ""
            )
            for b in node.bases
        }
        if "BaseModel" not in base_names:
            return
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign):
                continue
            ann = stmt.annotation
            if (
                isinstance(ann, ast.Subscript)
                and isinstance(ann.value, ast.Name)
                and ann.value.id == "ClassVar"
            ):
                # Check the inner type
                inner = ann.slice
                inner_name = (
                    inner.id
                    if isinstance(inner, ast.Name)
                    else inner.attr
                    if isinstance(inner, ast.Attribute)
                    else ""
                )
                if inner_name in {"float", "int", "str", "bool"}:
                    field_name = (
                        stmt.target.id if isinstance(stmt.target, ast.Name) else "?"
                    )
                    self.violations.append(
                        f"Line {stmt.lineno}: `ClassVar[{inner_name}]` on field `{field_name}` "
                        "in a BaseModel — Pydantic v2 ignores ClassVar fields; "
                        "use `{field_name}: {inner_name} = ...` (plain field) instead"
                    )

    # -- Annotations (return types, field types) --------------------------------

    # Third-party modules commonly placed under TYPE_CHECKING that must be at
    # runtime when used as Pydantic field types.
    _TC_MODULES = {"lmfit", "numpy", "pandas", "plotly", "scipy"}

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
        self._check_dict_any_annotation(node.annotation, node.lineno, context="field")
        self._check_module_dot_class_field(node.annotation, node.lineno)
        self.generic_visit(node)

    def _check_module_dot_class_field(self, ann: ast.expr, lineno: int) -> None:
        """Detect `module.ClassName` in a field annotation where module is a known TC-only lib."""
        if not isinstance(ann, ast.Attribute):
            return
        if not isinstance(ann.value, ast.Name):
            return
        module_name = ann.value.id
        if module_name in self._TC_MODULES:
            self.violations.append(
                f"Line {lineno}: `{module_name}.{ann.attr}` used as field annotation — "
                f"import the specific class at runtime instead: "
                f"`from {module_name} import {ann.attr}  # noqa: TC002`"
            )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        if node.returns:
            self._check_dict_any_annotation(node.returns, node.lineno, context="return")
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def _check_dict_any_annotation(
        self, ann: ast.expr, lineno: int, context: str
    ) -> None:
        if not isinstance(ann, ast.Subscript):
            return
        value = ann.value
        if not (isinstance(value, ast.Name) and value.id == "dict"):
            return
        # dict[str, <key2>] — check key2
        slc = ann.slice
        if isinstance(slc, ast.Tuple) and len(slc.elts) == 2:
            key2 = slc.elts[1]
            key2_name = (
                key2.id
                if isinstance(key2, ast.Name)
                else key2.attr
                if isinstance(key2, ast.Attribute)
                else ""
            )
            if key2_name in {"Any", "object"}:
                self.violations.append(
                    f"Line {lineno}: `dict[str, {key2_name}]` as {context} type — "
                    'define a Pydantic model with `extra="forbid"` instead'
                )

    # -- extra="allow" without comment ------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        self._check_field_default_factory_dict(node)
        self._check_configdict_extra_allow(node)
        self.generic_visit(node)

    def _check_field_default_factory_dict(self, node: ast.Call) -> None:
        func_name = (
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else ""
        )
        if func_name != "Field":
            return
        for kw in node.keywords:
            if (
                kw.arg == "default_factory"
                and isinstance(kw.value, ast.Name)
                and kw.value.id == "dict"
            ):
                self.violations.append(
                    f"Line {node.lineno}: `Field(default_factory=dict)` without explicit inner type — "
                    "use a typed Pydantic model instead of a bare dict"
                )

    def _check_configdict_extra_allow(self, node: ast.Call) -> None:
        func_name = (
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else ""
        )
        if func_name != "ConfigDict":
            return
        for kw in node.keywords:
            if (
                kw.arg == "extra"
                and isinstance(kw.value, ast.Constant)
                and kw.value.s == "allow"
            ):
                # Check the line and nearby lines for a migration comment
                lineno = node.lineno
                nearby = "\n".join(self._source_lines[max(0, lineno - 3) : lineno + 2])
                if (
                    "migration target" not in nearby
                    and "result container" not in nearby
                    and "parse-time adapter" not in nearby
                ):
                    self.violations.append(
                        f'Line {lineno}: `ConfigDict(extra="allow")` without migration comment — '
                        "add `# intentional: <reason>, v2.x migration target` nearby"
                    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    data = load_input()
    tool_name = data.get("tool_name", "")

    if not is_writing_tool(tool_name):
        allow()

    file_path = get_file_path(data)
    if not file_path.endswith(".py"):
        allow()

    content = get_content(data)
    if not content:
        allow()

    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError:
        # Let the editor handle syntax errors
        allow()

    source_lines = content.splitlines()
    visitor = PydanticViolationVisitor(source_lines)
    visitor.visit(tree)

    if not visitor.violations:
        allow()

    ask(Path(file_path).name, visitor.violations)


if __name__ == "__main__":
    main()
