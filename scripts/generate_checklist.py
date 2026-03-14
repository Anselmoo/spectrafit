"""Generate SpectraFit review checklists with file structure and hyperlinks.

This script scans source, test, or example trees, respects .gitignore rules,
and produces Markdown checklists with optional review prompts.
"""

from __future__ import annotations

import argparse
import logging
import pathlib
import re

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

logger = logging.getLogger(__name__)


def _count_files(structure: dict[str, list[str]]) -> int:
    """Count files in the grouped review structure."""
    return sum(len(files) for files in structure.values())


class ReviewTarget(StrEnum):
    """Supported review targets."""

    SRC = "src"
    TESTS = "tests"
    EXAMPLES = "examples"


@dataclass(frozen=True)
class ReviewTargetConfig:
    """Configuration for a review target."""

    root_parts: tuple[str, ...]
    heading_label: str
    title_label: str
    section_label: str
    default_checklist_output: str
    default_feedback_output: str
    include_suffixes: frozenset[str]
    include_names: frozenset[str]
    file_todos: tuple[str, ...]
    section_pros: tuple[str, ...]
    section_cons: tuple[str, ...]


REVIEW_TARGETS: dict[ReviewTarget, ReviewTargetConfig] = {
    ReviewTarget.SRC: ReviewTargetConfig(
        root_parts=("spectrafit",),
        heading_label="spectrafit",
        title_label="Source",
        section_label="module",
        default_checklist_output="CHECKLIST.md",
        default_feedback_output="REVIEW_SRC.md",
        include_suffixes=frozenset({".py"}),
        include_names=frozenset(),
        file_todos=(
            "Review implementation",
            "Check docstrings and type hints",
            "Verify tests exist",
            "Add notes or suggestions",
        ),
        section_pros=(
            "Clear separation of concerns",
            "Well-documented interfaces",
            "Comprehensive test coverage",
        ),
        section_cons=(
            "Potential for refactoring",
            "Could benefit from optimization",
            "Documentation could be enhanced",
        ),
    ),
    ReviewTarget.TESTS: ReviewTargetConfig(
        root_parts=("tests",),
        heading_label="tests",
        title_label="Test",
        section_label="test suite",
        default_checklist_output="CHECKLIST_TESTS.md",
        default_feedback_output="REVIEW_TESTS.md",
        include_suffixes=frozenset({".py"}),
        include_names=frozenset(),
        file_todos=(
            "Review assertions and fixtures",
            "Check marker usage and naming",
            "Verify edge cases are covered",
            "Add notes or suggestions",
        ),
        section_pros=(
            "Tests are focused and readable",
            "Fixtures are well scoped",
            "Coverage matches important workflows",
        ),
        section_cons=(
            "Missing regression or edge-case coverage",
            "Assertions could be more explicit",
            "Setup may be heavier than necessary",
        ),
    ),
    ReviewTarget.EXAMPLES: ReviewTargetConfig(
        root_parts=("examples",),
        heading_label="examples",
        title_label="Example",
        section_label="example set",
        default_checklist_output="CHECKLIST_EXAMPLES.md",
        default_feedback_output="REVIEW_EXAMPLES.md",
        include_suffixes=frozenset(
            {".csv", ".ipynb", ".json", ".md", ".py", ".toml", ".yaml", ".yml"}
        ),
        include_names=frozenset(),
        file_todos=(
            "Review documentation and setup steps",
            "Validate example inputs and outputs",
            "Check reproducibility for a new user",
            "Add notes or suggestions",
        ),
        section_pros=(
            "Example tells a clear story",
            "Inputs are easy to reproduce",
            "Files reflect a realistic workflow",
        ),
        section_cons=(
            "Instructions may be incomplete",
            "Generated artifacts may be outdated",
            "Scenario could use more explanation",
        ),
    ),
}


class GitIgnoreParser:
    """Parse and match .gitignore patterns (simplified but effective)."""

    def __init__(self, gitignore_path: Path) -> None:
        """Initialize parser with .gitignore file."""
        self.patterns: list[tuple[re.Pattern, bool]] = []
        self._load_patterns(gitignore_path)

    def _load_patterns(self, gitignore_path: Path) -> None:
        """Load and compile patterns from .gitignore."""
        if not gitignore_path.exists():
            return

        for line in gitignore_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            negated = line.startswith("!")
            if negated:
                line = line[1:]

            if "/" in line:
                pattern = re.compile(f"({re.escape(line)}|{re.escape(line)}/.*)")
            else:
                pattern = re.compile(f"(^|/){re.escape(line)}($|/)")

            self.patterns.append((pattern, negated))

    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored based on .gitignore rules."""
        path_str = str(path).replace("\\", "/")

        ignored = False
        for pattern, negated in self.patterns:
            if pattern.search(path_str):
                ignored = not negated

        return ignored


def _group_file(structure: dict[str, list[str]], root_path: Path, entry: Path) -> None:
    """Add a file to the grouped structure."""
    rel_path = entry.relative_to(root_path)
    parts = rel_path.parts

    if len(parts) == 1:
        dir_key = ""
        fname = parts[0]
    else:
        dir_key = "/".join(parts[:-1])
        fname = parts[-1]

    structure.setdefault(dir_key, []).append(fname)


def scan_package(
    package_path: Path,
    gitignore_parser: GitIgnoreParser,
) -> dict[str, list[str]]:
    """Scan a Python package and group files by directory."""
    structure: dict[str, list[str]] = {}

    for py_file in sorted(package_path.rglob("*.py")):
        if gitignore_parser.should_ignore(py_file):
            continue
        if "__pycache__" in py_file.parts:
            continue
        _group_file(structure, package_path, py_file)

    for files in structure.values():
        files.sort()

    return structure


def _should_include_file(path: Path, config: ReviewTargetConfig) -> bool:
    """Return whether the file should be included for the selected target."""
    return path.name in config.include_names or path.suffix in config.include_suffixes


def scan_review_target(
    root_path: Path,
    gitignore_parser: GitIgnoreParser,
    config: ReviewTargetConfig,
) -> dict[str, list[str]]:
    """Scan a review target and group files by directory."""
    structure: dict[str, list[str]] = {}

    if config.include_suffixes == frozenset({".py"}) and not config.include_names:
        return scan_package(root_path, gitignore_parser)

    for entry in sorted(root_path.rglob("*")):
        if not entry.is_file():
            continue
        if gitignore_parser.should_ignore(entry):
            continue
        if "__pycache__" in entry.parts:
            continue
        if not _should_include_file(entry, config):
            continue
        _group_file(structure, root_path, entry)

    for files in structure.values():
        files.sort()

    return structure


def _generate_file_todos(todo_items: tuple[str, ...]) -> list[str]:
    """Generate indented todo items for feedback mode."""
    return [f"  - [ ] {item}" for item in todo_items]


def _generate_pro_con_section(
    pros: tuple[str, ...],
    cons: tuple[str, ...],
) -> list[str]:
    """Generate pro/con evaluation section for feedback mode."""
    lines = ["### Pro & Con\n", "**Pros:**"]
    lines.extend(f"- [ ] {item}" for item in pros)
    lines.extend(["", "**Cons:**"])
    lines.extend(f"- [ ] {item}" for item in cons)
    lines.append("")
    return lines


def _build_document_title(
    config: ReviewTargetConfig,
    feedback_mode: bool,
) -> str:
    """Build the document title for the selected target and mode."""
    suffix = "Review" if feedback_mode else "Checklist"
    return f"SpectraFit {config.title_label} {suffix}"


def _build_output_name(
    config: ReviewTargetConfig,
    feedback_mode: bool,
) -> str:
    """Build the default output filename for the selected target and mode."""
    if feedback_mode:
        return config.default_feedback_output
    return config.default_checklist_output


def _build_refresh_command(
    target: ReviewTarget,
    feedback_mode: bool,
    output_name: str,
    use_src_layout: bool,
) -> str:
    """Build a helpful refresh command for check mode errors."""
    command_parts = ["python scripts/generate_checklist.py", f"--target {target.value}"]
    if use_src_layout:
        command_parts.append("--src")
    if feedback_mode:
        command_parts.append("--feedback")
    default_output = _build_output_name(REVIEW_TARGETS[target], feedback_mode)
    if output_name != default_output:
        command_parts.append(f"--output {output_name}")
    return " ".join(command_parts)


def _resolve_target_config(
    target: ReviewTarget, use_src_layout: bool
) -> ReviewTargetConfig:
    """Return the target config, applying the optional src/ layout override."""
    config = REVIEW_TARGETS[target]
    if target is not ReviewTarget.SRC or not use_src_layout:
        return config

    return ReviewTargetConfig(
        root_parts=("src", "spectrafit"),
        heading_label="src/spectrafit",
        title_label=config.title_label,
        section_label=config.section_label,
        default_checklist_output=config.default_checklist_output,
        default_feedback_output=config.default_feedback_output,
        include_suffixes=config.include_suffixes,
        include_names=config.include_names,
        file_todos=config.file_todos,
        section_pros=config.section_pros,
        section_cons=config.section_cons,
    )


def generate_checklist(
    structure: dict[str, list[str]],
    package_name: str = "spectrafit",
    use_github_urls: bool = False,
    github_repo: str = "Anselmoo/spectrafit",
    github_branch: str = "main",
    add_conclusions: bool = False,
    feedback_mode: bool = False,
    document_title: str = "SpectraFit File Checklist",
    section_label: str = "module",
    file_todos: tuple[str, ...] = (),
    section_pros: tuple[str, ...] = (),
    section_cons: tuple[str, ...] = (),
) -> str:
    """Generate Markdown checklist from file structure."""
    lines = [f"# {document_title}\n"]
    sorted_dirs = sorted(structure.keys(), key=lambda x: (x != "", x))

    for dir_path in sorted_dirs:
        heading_text = package_name if dir_path == "" else f"{package_name}/{dir_path}"
        if use_github_urls:
            heading_link = (
                f"https://github.com/{github_repo}/tree/{github_branch}/{heading_text}"
            )
        else:
            heading_link = heading_text

        lines.append(f"## [{heading_text}]({heading_link})\n")

        for fname in structure[dir_path]:
            if use_github_urls:
                file_link = (
                    f"https://github.com/{github_repo}/blob/"
                    f"{github_branch}/{heading_text}/{fname}"
                )
            else:
                file_link = (
                    f"{heading_text}/{fname}" if dir_path else f"{package_name}/{fname}"
                )

            lines.append(f"- [`{fname}`]({file_link}): comment-later")
            if feedback_mode:
                lines.extend(_generate_file_todos(file_todos))

        if add_conclusions:
            lines.append(
                f"> **Reviewed**: {dir_path or package_name} {section_label}\n"
            )

        if feedback_mode:
            lines.extend(_generate_pro_con_section(section_pros, section_cons))

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Launch the main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate SpectraFit review checklists with hyperlinks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--src",
        action="store_true",
        help="Scan src/spectrafit/ instead of spectrafit/ for source reviews",
    )
    parser.add_argument(
        "--target",
        type=ReviewTarget,
        choices=list(ReviewTarget),
        default=ReviewTarget.SRC,
        help="Select review target: src, tests, or examples",
    )
    parser.add_argument(
        "--github",
        action="store_true",
        help="Generate full GitHub URLs (blob/tree) instead of relative links",
    )
    parser.add_argument(
        "--github-repo",
        default="Anselmoo/spectrafit",
        help="GitHub repo slug (owner/repo) for URLs (default: Anselmoo/spectrafit)",
    )
    parser.add_argument(
        "--github-branch",
        default="v2.0.0",
        help="GitHub branch name for URLs (default: v2.0.0)",
    )
    parser.add_argument(
        "--conclusions",
        action="store_true",
        help="Add per-section conclusion blockquotes (> Reviewed: ...)",
    )
    parser.add_argument(
        "--output",
        help="Output filepath (default depends on target and mode)",
    )
    parser.add_argument(
        "--feedback",
        action="store_true",
        help="Feedback mode: add target-specific todos and pro/con sections",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Deprecated alias for --feedback",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated file is up-to-date (CI mode)",
    )

    args = parser.parse_args(argv)

    cwd = pathlib.Path.cwd()
    feedback_mode = args.feedback or args.dev
    target_config = _resolve_target_config(args.target, args.src)
    package_path = cwd.joinpath(*target_config.root_parts)
    package_name = target_config.heading_label
    output_name = args.output or _build_output_name(target_config, feedback_mode)
    document_title = _build_document_title(target_config, feedback_mode)

    if not package_path.exists():
        logger.error("%s does not exist", package_path)
        return 1

    gitignore_path = cwd / ".gitignore"
    gitignore_parser = GitIgnoreParser(gitignore_path)
    structure = scan_review_target(package_path, gitignore_parser, target_config)
    checklist = generate_checklist(
        structure,
        package_name=package_name,
        use_github_urls=args.github,
        github_repo=args.github_repo,
        github_branch=args.github_branch,
        add_conclusions=args.conclusions or feedback_mode,
        feedback_mode=feedback_mode,
        document_title=document_title,
        section_label=target_config.section_label,
        file_todos=target_config.file_todos,
        section_pros=target_config.section_pros,
        section_cons=target_config.section_cons,
    )

    output_path = cwd / output_name
    if args.check:
        if output_path.exists():
            existing = output_path.read_text()
            if existing == checklist:
                logger.info(
                    "%s is up-to-date (%d sections, %d files)",
                    output_name,
                    len(structure),
                    _count_files(structure),
                )
                return 0

            logger.error(
                "%s is out of date. Run: %s",
                output_name,
                _build_refresh_command(
                    args.target, feedback_mode, output_name, args.src
                ),
            )
            return 1
        logger.error("%s does not exist (run generator first)", output_name)
        return 1

    output_path.write_text(checklist)
    logger.info(
        "Generated %s (%d sections, %d files)",
        output_path,
        len(structure),
        _count_files(structure),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
