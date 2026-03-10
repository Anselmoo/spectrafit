"""Check spectrafit/ for architecture invariant violations.

This script has zero imports from spectrafit.* — it operates purely on
file-system text scanning to enforce project-level architecture rules.

Usage::

    uv run python scripts/architecture_check.py
    uv run python scripts/architecture_check.py --module jupyter
    uv run python scripts/architecture_check.py --json

Each invariant maps to a rule from architecture.instructions.md or
code-style.instructions.md. Violations are categorized as error vs. warning.
"""

from __future__ import annotations

import json
import re
import sys

from dataclasses import dataclass
from pathlib import Path

import typer


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SPECTRAFIT_DIR = _REPO_ROOT / "spectrafit"

_LEVEL_ORDER = {"error": 0, "warning": 1}

# CLI entry points where sys.exit() is acceptable
_CLI_FILES = {"main.py", "app.py"}

# Files where extra="allow" is intentional (legacy result containers)
_ALLOW_INTENTIONAL_COMMENT = "# intentional"

# Frozen modules — some checks are skipped for these
_FROZEN_FILES = {
    "preprocessing.py",
    "postprocessing.py",
}


# ---------------------------------------------------------------------------
# Invariant definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Invariant:
    """A single architecture invariant."""

    name: str
    doc_ref: str


INVARIANTS = {
    "future-annotations": Invariant(
        name="from __future__ import annotations required",
        doc_ref="code-style.instructions.md §Module Header",
    ),
    "sys-exit": Invariant(
        name="No sys.exit() in business logic",
        doc_ref="code-style.instructions.md §Error Handling",
    ),
    "extra-allow": Invariant(
        name="extra='forbid' on input models",
        doc_ref="architecture.instructions.md §Critical Invariant 3",
    ),
    "pydantic-v1-dict": Invariant(
        name="No .dict() — use model_dump()",
        doc_ref="code-style.instructions.md §Pydantic v2",
    ),
    "pydantic-v1-parse": Invariant(
        name="No parse_obj — use model_validate()",
        doc_ref="code-style.instructions.md §Pydantic v2",
    ),
    "pydantic-v1-config": Invariant(
        name="No class Config — use model_config",
        doc_ref="code-style.instructions.md §Pydantic v2",
    ),
    "module-docstring": Invariant(
        name="Module docstring required",
        doc_ref="code-style.instructions.md §Module Header",
    ),
    "global-int-flag": Invariant(
        name="No global_: int bare-int mode flag",
        doc_ref="architecture.instructions.md §Critical Invariant via fitting_context",
    ),
}


# ---------------------------------------------------------------------------
# Violation data
# ---------------------------------------------------------------------------


@dataclass
class Violation:
    """A single architecture violation."""

    file: str
    line: int
    invariant_id: str
    invariant_name: str
    level: str  # "error" or "warning"
    detail: str
    doc_ref: str


def _relative_path(path: Path) -> str:
    """Return path relative to spectrafit/ for display."""
    try:
        return str(path.relative_to(_SPECTRAFIT_DIR))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Individual checkers
# ---------------------------------------------------------------------------


def _check_future_annotations(
    filepath: Path, content: str, lines: list[str]
) -> list[Violation]:
    """Every .py file must have 'from __future__ import annotations'."""
    rel = _relative_path(filepath)

    # Skip empty __init__.py files
    if filepath.name == "__init__.py" and len(content.strip()) == 0:
        return []

    if "from __future__ import annotations" not in content:
        return [
            Violation(
                file=rel,
                line=1,
                invariant_id="future-annotations",
                invariant_name=INVARIANTS["future-annotations"].name,
                level="error",
                detail="Missing 'from __future__ import annotations'",
                doc_ref=INVARIANTS["future-annotations"].doc_ref,
            )
        ]
    return []


def _check_sys_exit(filepath: Path, content: str, lines: list[str]) -> list[Violation]:
    """No sys.exit() in business logic — only CLI entry points."""
    if filepath.name in _CLI_FILES:
        return []

    rel = _relative_path(filepath)
    violations: list[Violation] = []

    for match in re.finditer(r"sys\.exit\(", content):
        line_num = content[: match.start()].count("\n") + 1
        line_text = lines[line_num - 1] if line_num <= len(lines) else ""
        if _ALLOW_INTENTIONAL_COMMENT in line_text:
            continue
        violations.append(
            Violation(
                file=rel,
                line=line_num,
                invariant_id="sys-exit",
                invariant_name=INVARIANTS["sys-exit"].name,
                level="error",
                detail="sys.exit() in non-CLI module",
                doc_ref=INVARIANTS["sys-exit"].doc_ref,
            )
        )
    return violations


def _check_extra_allow(
    filepath: Path, content: str, lines: list[str]
) -> list[Violation]:
    """extra='allow' must have # intentional comment."""
    rel = _relative_path(filepath)
    violations: list[Violation] = []

    for match in re.finditer(r'extra\s*=\s*"allow"', content):
        line_num = content[: match.start()].count("\n") + 1
        line_text = lines[line_num - 1] if line_num <= len(lines) else ""
        if _ALLOW_INTENTIONAL_COMMENT in line_text:
            continue
        violations.append(
            Violation(
                file=rel,
                line=line_num,
                invariant_id="extra-allow",
                invariant_name=INVARIANTS["extra-allow"].name,
                level="error",
                detail=("extra='allow' without # intentional comment"),
                doc_ref=INVARIANTS["extra-allow"].doc_ref,
            )
        )
    return violations


def _check_pydantic_v1_dict(
    filepath: Path, content: str, lines: list[str]
) -> list[Violation]:
    """No .dict() calls — use model_dump() instead."""
    rel = _relative_path(filepath)
    violations: list[Violation] = []

    # Match .dict() but not model_dump(), not dict(), not in comments
    for match in re.finditer(r"\.dict\(\)", content):
        line_num = content[: match.start()].count("\n") + 1
        line_text = lines[line_num - 1] if line_num <= len(lines) else ""
        stripped = line_text.lstrip()
        if stripped.startswith("#"):
            continue
        violations.append(
            Violation(
                file=rel,
                line=line_num,
                invariant_id="pydantic-v1-dict",
                invariant_name=INVARIANTS["pydantic-v1-dict"].name,
                level="warning",
                detail=".dict() is Pydantic v1 — use model_dump()",
                doc_ref=INVARIANTS["pydantic-v1-dict"].doc_ref,
            )
        )
    return violations


def _check_pydantic_v1_parse(
    filepath: Path, content: str, lines: list[str]
) -> list[Violation]:
    """No parse_obj() calls — use model_validate() instead."""
    rel = _relative_path(filepath)
    violations: list[Violation] = []

    for match in re.finditer(r"\.parse_obj\(", content):
        line_num = content[: match.start()].count("\n") + 1
        line_text = lines[line_num - 1] if line_num <= len(lines) else ""
        stripped = line_text.lstrip()
        if stripped.startswith("#"):
            continue
        violations.append(
            Violation(
                file=rel,
                line=line_num,
                invariant_id="pydantic-v1-parse",
                invariant_name=INVARIANTS["pydantic-v1-parse"].name,
                level="warning",
                detail=("parse_obj() is Pydantic v1 — use model_validate()"),
                doc_ref=INVARIANTS["pydantic-v1-parse"].doc_ref,
            )
        )
    return violations


def _check_pydantic_v1_config(
    filepath: Path, content: str, lines: list[str]
) -> list[Violation]:
    """No inner class Config — use model_config = ConfigDict(...)."""
    rel = _relative_path(filepath)
    violations: list[Violation] = []

    # Match 'class Config:' that's indented (inner class)
    for match in re.finditer(r"^(\s+)class Config:", content, re.MULTILINE):
        line_num = content[: match.start()].count("\n") + 1
        violations.append(
            Violation(
                file=rel,
                line=line_num,
                invariant_id="pydantic-v1-config",
                invariant_name=INVARIANTS["pydantic-v1-config"].name,
                level="warning",
                detail=(
                    "Inner class Config is Pydantic v1 — use "
                    "model_config = ConfigDict(...)"
                ),
                doc_ref=INVARIANTS["pydantic-v1-config"].doc_ref,
            )
        )
    return violations


def _check_module_docstring(
    filepath: Path, content: str, lines: list[str]
) -> list[Violation]:
    """Every module should have a module-level docstring."""
    rel = _relative_path(filepath)

    # Skip empty __init__.py files
    if filepath.name == "__init__.py" and len(content.strip()) == 0:
        return []

    stripped = content.lstrip()
    if not stripped.startswith(('"""', "'''")):
        return [
            Violation(
                file=rel,
                line=1,
                invariant_id="module-docstring",
                invariant_name=INVARIANTS["module-docstring"].name,
                level="warning",
                detail="Missing module-level docstring",
                doc_ref=INVARIANTS["module-docstring"].doc_ref,
            )
        ]
    return []


def _check_global_int_flag(
    filepath: Path, content: str, lines: list[str]
) -> list[Violation]:
    """No global_: int bare-int mode flags."""
    # fitting_context.py defines FittingMode (the replacement) and
    # references global_: int only in docstrings/comments.
    if filepath.name == "fitting_context.py":
        return []

    rel = _relative_path(filepath)
    violations: list[Violation] = []

    for match in re.finditer(r"global_:\s*int", content):
        line_num = content[: match.start()].count("\n") + 1
        violations.append(
            Violation(
                file=rel,
                line=line_num,
                invariant_id="global-int-flag",
                invariant_name=INVARIANTS["global-int-flag"].name,
                level="error",
                detail=(
                    "global_: int — use FittingMode StrEnum from fitting_context.py"
                ),
                doc_ref=INVARIANTS["global-int-flag"].doc_ref,
            )
        )
    return violations


# Ordered list of all checker functions
_CHECKERS = [
    _check_future_annotations,
    _check_sys_exit,
    _check_extra_allow,
    _check_pydantic_v1_dict,
    _check_pydantic_v1_parse,
    _check_pydantic_v1_config,
    _check_module_docstring,
    _check_global_int_flag,
]


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def check_file(filepath: Path) -> list[Violation]:
    """Run all invariant checks on a single file."""
    if filepath.name in _FROZEN_FILES:
        return []

    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    lines = content.split("\n")
    violations: list[Violation] = []

    for checker in _CHECKERS:
        violations.extend(checker(filepath, content, lines))

    return violations


def check_directory(
    root: Path,
    module_filter: str | None = None,
) -> list[Violation]:
    """Run all invariant checks on all Python files under root."""
    violations: list[Violation] = []
    search_dir = root / module_filter if module_filter else root

    if not search_dir.exists():
        typer.echo(f"Error: directory {search_dir} does not exist", err=True)
        raise SystemExit(1)

    for py_file in sorted(search_dir.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        violations.extend(check_file(py_file))

    violations.sort(
        key=lambda v: (
            _LEVEL_ORDER.get(v.level, 99),
            v.file,
            v.line,
        )
    )
    return violations


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def _format_table(violations: list[Violation]) -> str:
    """Format violations as a readable table."""
    if not violations:
        return "All architecture invariants pass."

    header = (
        f"{'#':>3} {'File':<35} {'Line':>5}"
        f" {'Invariant':<40} {'Level':<7}"
        f" {'Detail':<50}"
    )
    sep = "=" * len(header)
    rows = [header, sep]

    for i, v in enumerate(violations, 1):
        rows.append(
            f"{i:>3} {v.file:<35} {v.line:>5}"
            f" {v.invariant_name:<40} {v.level:<7}"
            f" {v.detail:<50}"
        )

    # Summary
    counts: dict[str, int] = {}
    for v in violations:
        counts[v.level] = counts.get(v.level, 0) + 1

    summary_parts = [
        f"{lvl.title()}: {cnt}"
        for lvl, cnt in sorted(
            counts.items(),
            key=lambda x: _LEVEL_ORDER.get(x[0], 99),
        )
    ]
    rows.append(sep)
    rows.append(f"Total: {len(violations)} violations | {' | '.join(summary_parts)}")

    return "\n".join(rows)


def _format_json(violations: list[Violation]) -> str:
    """Format violations as JSON."""
    return json.dumps(
        [
            {
                "file": v.file,
                "line": v.line,
                "invariant": v.invariant_id,
                "name": v.invariant_name,
                "level": v.level,
                "detail": v.detail,
                "doc_ref": v.doc_ref,
            }
            for v in violations
        ],
        indent=2,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

app = typer.Typer(
    add_completion=False,
    pretty_exceptions_enable=False,
    help="Check spectrafit/ for architecture invariant violations.",
)


@app.command()
def main(
    module: str | None = typer.Option(
        None,
        "--module",
        "-m",
        help=("Check only this subdirectory (e.g. 'jupyter', 'core', 'models')."),
    ),
    invariant: str | None = typer.Option(
        None,
        "--invariant",
        "-i",
        help=(
            "Filter by invariant id: future-annotations, sys-exit, extra-allow, etc."
        ),
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON instead of table.",
    ),
) -> None:
    """Check spectrafit/ architecture invariants and produce a report."""
    violations = check_directory(_SPECTRAFIT_DIR, module_filter=module)

    if invariant:
        violations = [v for v in violations if v.invariant_id == invariant]

    header = f"Architecture Check for spectrafit/{module or ''}"
    typer.echo(header)
    typer.echo("=" * len(header))
    typer.echo()

    if output_json:
        typer.echo(_format_json(violations))
    else:
        typer.echo(_format_table(violations))

    # Exit with non-zero if any errors exist
    error_count = sum(1 for v in violations if v.level == "error")
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    app()
