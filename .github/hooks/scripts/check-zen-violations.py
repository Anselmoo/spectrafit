#!/usr/bin/env python3
# ruff: noqa: T201,D,PLR2004,N802,N815,ANN,RUF
# Hook: check-zen-violations.py
# Event: PreToolUse
# Purpose: Lightweight Pydantic v2 / SpectraFit v2 zen-of-languages style checks.
#
# Uses only stdlib (ast, re) — no dependency on zen-of-langua MCP tool at write time.
# For full batch analysis use: mcp_zen-of-langua_analyze_batch
#
# Checks (all soft-warn / ask):
#   - PEP 695 type alias: X: TypeAlias = ... instead of `type X = ...`
#   - StrEnum pattern: class X(str, Enum) instead of class X(StrEnum)
#   - Pydantic dict contract: model fields typed as dict[str, Any]
#   - Return type Any: def f(...) -> Any
#   - Mutable default: list() or {} as default argument
#   - Catch-all except clause: bare `except:` or `except Exception as e: pass`
#   - Missing __future__ annotations import in spectrafit/ modules

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_PACKAGE_DIRS = frozenset(
    {
        "adapters",
        "api",
        "app",
        "cli",
        "core",
        "generators",
        "jupyter",
        "models",
        "notebook",
        "plugins",
        "report",
        "reporting",
        "utilities",
        "workflow",
    }
)


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


def is_package_source(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    return any(f"/spectrafit/{pkg_dir}/" in norm for pkg_dir in _PACKAGE_DIRS)


def allow() -> None:
    print(json.dumps({"continue": True}))
    sys.exit(0)


def ask(file_path: str, violations: list[str]) -> None:
    bullets = "\n".join(f"  * {v}" for v in violations)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"Zen/style advisory in {Path(file_path).name}:\n{bullets}\n\n"
                "These are quality recommendations, not hard blocks. "
                "Consider fixing before merging, or run: "
                "mcp_zen-of-langua_analyze_batch for full analysis."
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(0)


class ZenViolationVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[str] = []
        self._has_future_annotations = False
        self._imports_checked = False

    # -- __future__ annotations ----------------------------------------------

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "__future__":
            names = {alias.name for alias in node.names}
            if "annotations" in names:
                self._has_future_annotations = True
        if node.module == "typing":
            names = {alias.name for alias in node.names}
            if "TypeAlias" in names:
                self.violations.append(
                    f"Line {node.lineno}: TypeAlias from typing -- "
                    "use PEP 695 `type X = ...` keyword (Python 3.12)"
                )
        self.generic_visit(node)

    # -- class definitions ---------------------------------------------------

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
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
                f"Line {node.lineno}: class {node.name}(str, Enum) -- "
                "use class {node.name}(StrEnum) from enum (PEP 663 / Python 3.11)"
            )
        self.generic_visit(node)

    # -- function definitions ------------------------------------------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_return_any(node)
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_return_any(node)
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def _check_return_any(self, node: ast.FunctionDef) -> None:
        if (
            node.returns
            and isinstance(node.returns, ast.Name)
            and node.returns.id == "Any"
        ):
            self.violations.append(
                f"Line {node.lineno}: def {node.name}(...) -> Any -- "
                "explicit Any return type disables type checking; use a concrete type"
            )

    def _check_mutable_defaults(self, node: ast.FunctionDef) -> None:
        for default in node.args.defaults + node.args.kw_defaults:
            if default is None:
                continue
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.violations.append(
                    f"Line {node.lineno}: mutable default argument in '{node.name}' -- "
                    "use None + `if x is None: x = []` pattern"
                )
                break
            if isinstance(default, ast.Call):
                func = default.func
                name = (
                    func.id
                    if isinstance(func, ast.Name)
                    else func.attr
                    if isinstance(func, ast.Attribute)
                    else ""
                )
                if name in {"list", "dict", "set"}:
                    self.violations.append(
                        f"Line {node.lineno}: mutable default `{name}()` in '{node.name}' -- "
                        "use None sentinel or Field(default_factory={name}) in Pydantic model"
                    )
                    break

    # -- exception handling --------------------------------------------------

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.violations.append(
                f"Line {node.lineno}: bare `except:` clause -- "
                "catch specific exceptions; bare except swallows KeyboardInterrupt"
            )
        elif (
            isinstance(node.type, ast.Name)
            and node.type.id == "Exception"
            and len(node.body) == 1
            and isinstance(node.body[0], ast.Pass)
        ):
            self.violations.append(
                f"Line {node.lineno}: `except Exception: pass` -- "
                "silently swallowing exceptions hides bugs; at minimum log or re-raise"
            )
        self.generic_visit(node)

    # -- AnnAssign: dict[str, Any] fields ------------------------------------

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        ann = node.annotation
        if (
            isinstance(ann, ast.Subscript)
            and isinstance(ann.value, ast.Name)
            and ann.value.id == "dict"
        ):
            slc = ann.slice
            if isinstance(slc, ast.Tuple) and len(slc.elts) == 2:
                v = slc.elts[1]
                if isinstance(v, ast.Name) and v.id in {"Any", "object"}:
                    field_name = (
                        ann.value.id if isinstance(ann.value, ast.Name) else "?"
                    )
                    self.violations.append(
                        f"Line {node.lineno}: dict[str, {v.id}] field annotation -- "
                        "define a typed Pydantic model instead of an open dict"
                    )
        self.generic_visit(node)


def check_missing_future_annotations(tree: ast.Module) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            for alias in node.names:
                if alias.name == "annotations":
                    return None
    return "Missing `from __future__ import annotations` (required in all spectrafit/ modules)"


def main() -> None:
    data = load_input()
    if not is_writing_tool(data.get("tool_name", "")):
        allow()

    file_path = get_file_path(data)
    if not file_path.endswith(".py") or not is_package_source(file_path):
        allow()

    content = get_content(data)
    if not content:
        allow()

    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError:
        allow()

    visitor = ZenViolationVisitor()
    visitor.visit(tree)

    missing_future = check_missing_future_annotations(tree)
    if missing_future:
        visitor.violations.append(missing_future)

    if not visitor.violations:
        allow()

    ask(Path(file_path).name, visitor.violations)


if __name__ == "__main__":
    main()
