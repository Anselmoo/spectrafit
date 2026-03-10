"""Scan spectrafit/ for known anti-patterns and produce a tabular report.

This script has zero imports from spectrafit.* — it operates purely on
file-system text scanning with regex patterns.

Usage::

    uv run python scripts/scan_antipatterns.py
    uv run python scripts/scan_antipatterns.py --module jupyter
    uv run python scripts/scan_antipatterns.py --severity critical
    uv run python scripts/scan_antipatterns.py --json

Each anti-pattern is defined with a regex, a severity level, a recommended
fix, and an optional design-pattern reference (Facade, Builder, Catalog, etc.).
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

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Files that are intentionally frozen — skip for actionable findings
_FROZEN_FILES = {"preprocessing.py", "postprocessing.py"}

# Files where dict[str, object] is intentional (legacy bridges)
_DICT_INTENTIONAL_COMMENT = "# intentional"


# ---------------------------------------------------------------------------
# Anti-pattern definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AntiPattern:
    """A single anti-pattern definition for scanning."""

    name: str
    regex: str
    severity: str
    fix: str
    pattern_ref: str
    exclude_files: tuple[str, ...] = ()


ANTI_PATTERNS: list[AntiPattern] = [
    AntiPattern(
        name="dict[str, object] boundary",
        regex=r"dict\[str,\s*object\]",
        severity="critical",
        fix="Replace with Pydantic model (extra='forbid')",
        pattern_ref="—",
    ),
    AntiPattern(
        name="@property -> None (side-effect)",
        regex=r"@property",
        severity="critical",
        fix="Convert to explicit def method",
        pattern_ref="Catalog",
    ),
    AntiPattern(
        name="God-class __init__ (15+ params)",
        regex=r"def __init__\(  # noqa: C901",
        severity="critical",
        fix="Decompose into config models",
        pattern_ref="Facade",
    ),
    AntiPattern(
        name="None-defaulting in __init__",
        regex=r"if \w+ is None:",
        severity="high",
        fix="Use Field(default_factory=...)",
        pattern_ref="Builder",
    ),
    AntiPattern(
        name="Multiple inheritance (3+ bases)",
        regex=r"class \w+\([^)]*,\s*[^)]*,\s*[^)]+\):",
        severity="high",
        fix="Composition via delegation",
        pattern_ref="Delegation",
    ),
    AntiPattern(
        name="global_: int (bare-int mode)",
        regex=r"global_:\s*int",
        severity="high",
        fix="Use FittingMode StrEnum",
        pattern_ref="—",
    ),
    AntiPattern(
        name="Dict-key access in Jupyter",
        regex=r"self\.args_out\[",
        severity="high",
        fix="Use SolverResults.<attr> typed access",
        pattern_ref="—",
    ),
    AntiPattern(
        name="Inline param f-string",
        regex=r'f"{\w+}_',
        severity="medium",
        fix="Route through lmfit_param_name(id, field)",
        pattern_ref="—",
        exclude_files=("naming.py",),
    ),
    AntiPattern(
        name="extra='allow' on input model",
        regex=r'extra\s*=\s*"allow"',
        severity="medium",
        fix="Change to extra='forbid' or add # intentional",
        pattern_ref="—",
    ),
    AntiPattern(
        name="**dict model construction",
        regex=r"\w+\(\*\*\w+\)",
        severity="medium",
        fix="Accept typed model directly",
        pattern_ref="—",
    ),
    AntiPattern(
        name="sys.exit() in business logic",
        regex=r"sys\.exit\(",
        severity="high",
        fix="Raise typed exception instead",
        pattern_ref="—",
        exclude_files=("main.py",),
    ),
]

app = typer.Typer(
    add_completion=False,
    pretty_exceptions_enable=False,
    help="Scan spectrafit/ for known anti-patterns.",
)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """A single anti-pattern finding."""

    file: str
    line: int
    pattern_name: str
    severity: str
    fix: str
    pattern_ref: str
    match_text: str


def _relative_path(path: Path) -> str:
    """Return path relative to spectrafit/ for display."""
    try:
        return str(path.relative_to(_SPECTRAFIT_DIR))
    except ValueError:
        return str(path)


def _is_intentional(line_text: str) -> bool:
    """Check if the line has an intentional marker comment."""
    return _DICT_INTENTIONAL_COMMENT in line_text


def _is_property_side_effect(lines: list[str], prop_line_idx: int) -> bool:
    """Check if a @property is followed by a def returning None."""
    next_idx = prop_line_idx + 1
    return next_idx < len(lines) and "-> None" in lines[next_idx]


def _is_none_default_in_init(content: str, match_start: int) -> bool:
    """Check if a None-check occurs inside an __init__ method."""
    preceding = content[:match_start]
    last_def = preceding.rsplit("\ndef ", 1)[-1]
    return "def __init__(" in last_def


def _should_skip_match(
    ap: AntiPattern,
    line_text: str,
    lines: list[str],
    line_num: int,
    content: str,
    match_start: int,
) -> bool:
    """Return True if this match should be excluded from findings.

    A line annotated with # intentional is always suppressed regardless of
    pattern type — this covers accepted trade-offs documented inline (e.g.,
    legacy adapter fields, compat shims, pending facade refactors).
    """
    # Universal intentional suppression — any pattern can be silenced inline.
    if _is_intentional(line_text):
        return True
    # Pattern-specific structural exclusions (no comment-based suppression present).
    if ap.name == "@property -> None (side-effect)":
        return not _is_property_side_effect(lines, line_num - 1)
    return ap.name == "None-defaulting in __init__" and not (
        _is_none_default_in_init(content, match_start)
    )


def scan_file(filepath: Path, patterns: list[AntiPattern]) -> list[Finding]:
    """Scan a single file for all anti-patterns."""
    findings: list[Finding] = []

    if filepath.name in _FROZEN_FILES:
        return findings

    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return findings

    lines = content.split("\n")

    for ap in patterns:
        if filepath.name in ap.exclude_files:
            continue

        for match in re.finditer(ap.regex, content):
            line_num = content[: match.start()].count("\n") + 1
            line_text = lines[line_num - 1] if line_num <= len(lines) else ""

            if _should_skip_match(
                ap, line_text, lines, line_num, content, match.start()
            ):
                continue

            match_preview = match.group(0)[:60].replace("\n", " ").strip()

            findings.append(
                Finding(
                    file=_relative_path(filepath),
                    line=line_num,
                    pattern_name=ap.name,
                    severity=ap.severity,
                    fix=ap.fix,
                    pattern_ref=ap.pattern_ref,
                    match_text=match_preview,
                )
            )

    return findings


def scan_directory(
    root: Path,
    patterns: list[AntiPattern],
    module_filter: str | None = None,
) -> list[Finding]:
    """Scan all Python files under root."""
    findings: list[Finding] = []
    search_dir = root / module_filter if module_filter else root

    if not search_dir.exists():
        typer.echo(f"Error: directory {search_dir} does not exist", err=True)
        raise SystemExit(1)

    for py_file in sorted(search_dir.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        findings.extend(scan_file(py_file, patterns))

    findings.sort(key=lambda f: (_SEVERITY_ORDER.get(f.severity, 99), f.file, f.line))
    return findings


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def _format_table(findings: list[Finding]) -> str:
    """Format findings as a readable table."""
    if not findings:
        return "No anti-patterns found."

    header = (
        f"{'#':>3} {'File':<35} {'Line':>5}"
        f" {'Pattern':<35} {'Severity':<9}"
        f" {'Fix':<40} {'Ref':<12}"
    )
    sep = "=" * len(header)
    rows = [header, sep]

    for i, f in enumerate(findings, 1):
        rows.append(
            f"{i:>3} {f.file:<35} {f.line:>5}"
            f" {f.pattern_name:<35} {f.severity:<9}"
            f" {f.fix:<40} {f.pattern_ref:<12}"
        )

    # Summary
    counts = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    summary_parts = [
        f"{sev.title()}: {cnt}"
        for sev, cnt in sorted(
            counts.items(),
            key=lambda x: _SEVERITY_ORDER.get(x[0], 99),
        )
    ]
    rows.append(sep)
    rows.append(f"Total: {len(findings)} findings | {' | '.join(summary_parts)}")

    return "\n".join(rows)


def _format_json(findings: list[Finding]) -> str:
    """Format findings as JSON."""
    return json.dumps(
        [
            {
                "file": f.file,
                "line": f.line,
                "pattern": f.pattern_name,
                "severity": f.severity,
                "fix": f.fix,
                "design_pattern": f.pattern_ref,
                "match": f.match_text,
            }
            for f in findings
        ],
        indent=2,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@app.command()
def main(
    module: str | None = typer.Option(
        None,
        "--module",
        "-m",
        help="Scan only this subdirectory (e.g. 'jupyter', 'core').",
    ),
    severity: str | None = typer.Option(
        None,
        "--severity",
        "-s",
        help="Filter by minimum severity: critical, high, medium, low.",
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON instead of table."
    ),
) -> None:
    """Scan spectrafit/ for known anti-patterns and produce a report."""
    findings = scan_directory(_SPECTRAFIT_DIR, ANTI_PATTERNS, module_filter=module)

    if severity:
        threshold = _SEVERITY_ORDER.get(severity.lower(), 99)
        findings = [
            f for f in findings if _SEVERITY_ORDER.get(f.severity, 99) <= threshold
        ]

    header = f"Anti-Pattern Report for spectrafit/{module or ''}"
    typer.echo(header)
    typer.echo("=" * len(header))
    typer.echo()

    if output_json:
        typer.echo(_format_json(findings))
    else:
        typer.echo(_format_table(findings))

    # Exit with non-zero if critical findings exist
    critical_count = sum(1 for f in findings if f.severity == "critical")
    if critical_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    app()
