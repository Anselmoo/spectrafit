"""Unit tests for the review checklist generator script."""

from __future__ import annotations

from pathlib import Path

from scripts.generate_checklist import REVIEW_TARGETS
from scripts.generate_checklist import GitIgnoreParser
from scripts.generate_checklist import ReviewTarget
from scripts.generate_checklist import generate_checklist
from scripts.generate_checklist import scan_review_target


def test_scan_review_target_filters_example_artifacts(tmp_path: Path) -> None:
    examples_dir = tmp_path / "examples"
    basic_dir = examples_dir / "basic"
    basic_dir.mkdir(parents=True)
    (basic_dir / "README.md").write_text("# Example\n")
    (basic_dir / "input.toml").write_text("title = 'demo'\n")
    (basic_dir / "data.csv").write_text("x,y\n0,1\n")
    (basic_dir / "fit_validation.html").write_text("<html></html>\n")

    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("\n")
    parser = GitIgnoreParser(gitignore)

    structure = scan_review_target(
        examples_dir,
        parser,
        REVIEW_TARGETS[ReviewTarget.EXAMPLES],
    )

    assert structure == {"basic": ["README.md", "data.csv", "input.toml"]}


def test_generate_checklist_uses_test_review_labels() -> None:
    structure = {"unit": ["test_cli_runtime.py"]}
    config = REVIEW_TARGETS[ReviewTarget.TESTS]

    content = generate_checklist(
        structure,
        package_name=config.heading_label,
        add_conclusions=True,
        feedback_mode=True,
        document_title="SpectraFit Test Review",
        section_label=config.section_label,
        file_todos=config.file_todos,
        section_pros=config.section_pros,
        section_cons=config.section_cons,
    )

    assert "# SpectraFit Test Review" in content
    assert "## [tests/unit](tests/unit)" in content
    assert "Review assertions and fixtures" in content
    assert "> **Reviewed**: unit test suite" in content
    assert "Tests are focused and readable" in content
