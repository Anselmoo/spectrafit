#!/usr/bin/env python3
# ruff: noqa: T201,D,PLR2004,N802,N815,ANN,RUF
# Hook: check-legacy-banned.py
# Event: PreToolUse
# Purpose: AST-based v1 legacy pattern enforcement (accurate, no grep false-positives)
#
# Hard-deny: args_out subscript, global_:int param, from_legacy_dict outside bridge,
#            SolverModels() outside models/solver.py
# Soft-warn: normalize_unified_config_input(), bare print() in spectrafit/

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_BRIDGE_FILES = frozenset({"adapters/v1_config_migration.py", "models/solver.py"})
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
    # Match /spectrafit/<package_subdir>/
    for pkg_dir in _PACKAGE_DIRS:
        if f"/spectrafit/{pkg_dir}/" in norm:
            return True
    return False


def is_bridge_file(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    return any(norm.endswith(b) for b in _BRIDGE_FILES)


def allow() -> None:
    print(json.dumps({"continue": True}))
    sys.exit(0)


def block(file_path: str, violations: list[str]) -> None:
    bullets = "\n".join(f"  * {v}" for v in violations)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "block",
            "permissionDecisionReason": (
                f"HARD BLOCK: v1 legacy pattern in {Path(file_path).name}:\n{bullets}\n\n"
                "These patterns are permanently banned. Use typed v2 API: "
                "UnifiedFittingConfig / model_validate()."
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(2)


def ask(file_path: str, violations: list[str]) -> None:
    bullets = "\n".join(f"  * {v}" for v in violations)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"v1 compatibility warning in {Path(file_path).name}:\n{bullets}\n\n"
                "Confirm this edit reduces (not expands) usage of these migration targets."
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(0)


class LegacyBannedVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        self.hard: list[str] = []
        self.soft: list[str] = []
        self._in_bridge = is_bridge_file(file_path)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "args_out"
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            self.hard.append(
                f"Line {node.lineno}: args_out subscript access "
                f"key='{node.slice.value}' -- use typed Pydantic model"
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if (
                arg.arg == "global_"
                and isinstance(arg.annotation, ast.Name)
                and arg.annotation.id == "int"
            ):
                self.hard.append(
                    f"Line {node.lineno}: param 'global_: int' in '{node.name}' -- "
                    "v1 global count; use typed model field"
                )
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        # Reuse FunctionDef logic for async functions
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if (
                arg.arg == "global_"
                and isinstance(arg.annotation, ast.Name)
                and arg.annotation.id == "int"
            ):
                self.hard.append(
                    f"Line {node.lineno}: param 'global_: int' in '{node.name}' (async) -- "
                    "v1 global count; use typed model field"
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr
            if isinstance(func, ast.Attribute)
            else ""
        )

        if (
            name == "from_legacy_dict"
            and isinstance(func, ast.Attribute)
            and not self._in_bridge
        ):
            self.hard.append(
                f"Line {node.lineno}: .from_legacy_dict() outside bridge files -- "
                "use model_validate() or explicit adapter"
            )

        if name == "SolverModels" and not self._in_bridge:
            self.hard.append(
                f"Line {node.lineno}: SolverModels() outside models/solver.py -- "
                "use LmfitSolverRuntime directly"
            )

        if name == "normalize_unified_config_input":
            self.soft.append(
                f"Line {node.lineno}: normalize_unified_config_input() -- "
                "migration target; prefer UnifiedFittingConfig.model_validate()"
            )

        if isinstance(func, ast.Name) and func.id == "print":
            self.soft.append(
                f"Line {node.lineno}: bare print() -- "
                "use logging or raise typed exception"
            )

        self.generic_visit(node)


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

    visitor = LegacyBannedVisitor(file_path)
    visitor.visit(tree)

    if visitor.hard:
        block(file_path, visitor.hard)
    if visitor.soft:
        ask(file_path, visitor.soft)

    allow()


if __name__ == "__main__":
    main()
