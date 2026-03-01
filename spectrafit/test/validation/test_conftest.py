"""Tests for the validation conftest pytest plugin.

These tests verify that the ``record_validation`` fixture, the session
collector, and the JSON/HTML report generation work correctly.
"""

from __future__ import annotations

from typing import ClassVar

import pytest


pytest_plugins = ["pytester"]


class TestRecordValidationFixture:
    """Tests for the ``record_validation`` fixture callable."""

    categories: ClassVar[list[str]] = ["analytical", "reference", "expectation"]

    def test_record_analytical(self, record_validation, validation_collector) -> None:  # type: ignore[no-untyped-def]
        """Recording an analytical result appends to the collector."""
        record_validation(
            name="test_area",
            passed=True,
            measured=1.0,
            expected=1.0,
            tolerance=0.01,
            category="analytical",
        )
        assert len(validation_collector.analytical) >= 1
        last = validation_collector.analytical[-1]
        assert last.name == "test_area"
        assert last.passed is True

    def test_record_reference(self, record_validation, validation_collector) -> None:  # type: ignore[no-untyped-def]
        """Recording a reference result appends to the collector."""
        record_validation(
            name="ref_dataset",
            passed=False,
            measured=1.05,
            expected=1.0,
            tolerance=0.02,
            category="reference",
            metric="rmse",
        )
        assert len(validation_collector.reference) >= 1
        last = validation_collector.reference[-1]
        assert last.dataset_name == "ref_dataset"
        assert last.passed is False

    def test_record_expectation(self, record_validation, validation_collector) -> None:  # type: ignore[no-untyped-def]
        """Recording an expectation result appends to the collector."""
        record_validation(
            name="peak_count_is_two",
            passed=True,
            measured=2.0,
            expected=2.0,
            tolerance=0.0,
            category="expectation",
            description="Two peaks expected",
        )
        assert len(validation_collector.expectation) >= 1
        last = validation_collector.expectation[-1]
        assert last.expectation == "peak_count_is_two"
        assert last.details == "Two peaks expected"

    def test_invalid_category_raises(self, record_validation) -> None:  # type: ignore[no-untyped-def]
        """An unknown category should raise ``ValueError``."""
        with pytest.raises(ValueError, match="Unknown validation category"):
            record_validation(
                name="bad",
                passed=True,
                measured=0.0,
                expected=0.0,
                tolerance=0.0,
                category="nonexistent",
            )


class TestValidationCollector:
    """Tests for the ``_ValidationCollector`` accumulation logic."""

    def test_total_and_passed(self, record_validation, validation_collector) -> None:  # type: ignore[no-untyped-def]
        """Collector correctly counts total and passed results."""
        initial_total = validation_collector.total
        initial_passed = validation_collector.passed

        record_validation(
            name="count_check",
            passed=True,
            measured=5.0,
            expected=5.0,
            tolerance=0.1,
            category="analytical",
        )
        assert validation_collector.total == initial_total + 1
        assert validation_collector.passed == initial_passed + 1

    def test_build_report(self, record_validation, validation_collector) -> None:  # type: ignore[no-untyped-def]
        """``build_report()`` produces a valid ``ValidationReport``."""
        record_validation(
            name="report_check",
            passed=True,
            measured=3.0,
            expected=3.0,
            tolerance=0.01,
            category="analytical",
        )
        report = validation_collector.build_report()
        assert len(report.analytical_checks) >= 1
        assert report.spectrafit_version


class TestReportGeneration:
    """Tests for JSON/HTML report file generation via pytester."""

    test_file_content: ClassVar[str] = '''
"""Inline test that uses record_validation to produce output."""

from __future__ import annotations


def test_generate_report(record_validation):
    """Record one result per category to exercise report generation."""
    record_validation(
        name="area_recovery",
        passed=True,
        measured=1.0,
        expected=1.0,
        tolerance=0.01,
        category="analytical",
    )
    record_validation(
        name="benchmark_a",
        passed=True,
        measured=0.99,
        expected=1.0,
        tolerance=0.05,
        category="reference",
        metric="max_abs_error",
    )
    record_validation(
        name="peak_exists",
        passed=True,
        measured=1.0,
        expected=1.0,
        tolerance=0.0,
        category="expectation",
        description="Peak detected",
    )
'''

    def test_json_and_html_generated(self, pytester: pytest.Pytester) -> None:
        """Running with ``--validation-report`` produces both output files."""
        pytester.makeconftest(
            _read_conftest_source(),
        )
        pytester.makepyfile(test_inline=self.test_file_content)
        result = pytester.runpytest(
            "--validation-report",
            str(pytester.path / "validation-report"),
            "-q",
        )
        result.assert_outcomes(passed=1)

        json_path = pytester.path / "validation-report.json"
        html_path = pytester.path / "validation-report.html"

        assert json_path.exists(), "JSON report was not generated"
        assert html_path.exists(), "HTML report was not generated"

        import json

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert len(data["analytical_checks"]) == 1
        assert len(data["reference_benchmarks"]) == 1
        assert len(data["expectation_results"]) == 1

        html = html_path.read_text(encoding="utf-8")
        assert "area_recovery" in html
        assert "PASS" in html

    def test_no_report_without_flag(self, pytester: pytest.Pytester) -> None:
        """Without ``--validation-report``, no files are written."""
        pytester.makeconftest(
            _read_conftest_source(),
        )
        pytester.makepyfile(test_inline=self.test_file_content)
        result = pytester.runpytest("-q")
        result.assert_outcomes(passed=1)

        json_files = list(pytester.path.glob("*.json"))
        html_files = list(pytester.path.glob("*.html"))
        assert not json_files, "JSON report should not be generated without flag"
        assert not html_files, "HTML report should not be generated without flag"


def _read_conftest_source() -> str:
    """Read the validation conftest.py source for injection into pytester.

    Returns:
        The full source code of the validation conftest module.
    """
    from pathlib import Path

    conftest_path = Path(__file__).parent / "conftest.py"
    return conftest_path.read_text(encoding="utf-8")
