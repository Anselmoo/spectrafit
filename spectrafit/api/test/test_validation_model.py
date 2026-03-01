"""Tests for the scientific validation models."""

from __future__ import annotations

import json

from datetime import datetime
from datetime import timezone

import pytest

from spectrafit.api.validation_model import AnalyticalCheck
from spectrafit.api.validation_model import ExpectationResult
from spectrafit.api.validation_model import FitExpectation
from spectrafit.api.validation_model import ReferenceBenchmark
from spectrafit.api.validation_model import ValidationReport


pytestmark = pytest.mark.unit


@pytest.fixture
def sample_expectation() -> FitExpectation:
    """Create a sample FitExpectation for testing."""
    return FitExpectation(
        parameter_bounds={"amplitude": (0.0, 2.0), "center": (-1.0, 1.0)},
        max_residual_rms=0.05,
        min_r_squared=0.99,
        description="Gaussian peak should be recovered within 1%.",
        expected_behavior=["Single symmetric peak", "No baseline drift"],
        physical_context="Isolated Gaussian emission line",
        literature_reference="Doe et al. 2024",
    )


@pytest.fixture
def mixed_report() -> ValidationReport:
    """Create a ValidationReport with mixed pass/fail results."""
    return ValidationReport(
        timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        spectrafit_version="1.4.1",
        config_hash="abc123",
        analytical_checks=[
            AnalyticalCheck(
                name="gaussian_area_recovery",
                passed=True,
                expected=1.0,
                measured=0.998,
                tolerance=0.01,
                metric="rtol",
                description="Area under Gaussian curve",
            ),
            AnalyticalCheck(
                name="center_position",
                passed=False,
                expected=0.0,
                measured=0.05,
                tolerance=0.01,
                metric="atol",
                description="Peak center",
            ),
        ],
        reference_benchmarks=[
            ReferenceBenchmark(
                dataset_name="NIST_SRM_2242",
                passed=True,
                deviation_metric="rmse",
                deviation_value=0.002,
                threshold=0.01,
            ),
        ],
        expectation_results=[
            ExpectationResult(
                expectation="Peak amplitude > 0.5",
                passed=True,
                details="Measured amplitude: 0.95",
            ),
            ExpectationResult(
                expectation="No negative residuals > 3-sigma",
                passed=False,
                details="Found 2 outliers",
            ),
        ],
        chi_squared=45.2,
        reduced_chi_squared=1.02,
        r_squared=0.998,
        residual_rms=0.003,
        parameter_uncertainties={"amplitude": 0.01, "center": 0.002},
    )


class TestFitExpectation:
    """Tests for the FitExpectation model."""

    def test_creation_with_defaults(self) -> None:
        """Test that FitExpectation can be created with defaults."""
        exp = FitExpectation()
        assert exp.parameter_bounds == {}
        assert exp.max_residual_rms is None
        assert exp.min_r_squared is None
        assert exp.description == ""
        assert exp.expected_behavior == []

    def test_creation_with_values(self, sample_expectation: FitExpectation) -> None:
        """Test FitExpectation creation with explicit values."""
        assert sample_expectation.parameter_bounds["amplitude"] == (0.0, 2.0)
        assert sample_expectation.max_residual_rms == 0.05
        assert sample_expectation.min_r_squared == 0.99
        assert len(sample_expectation.expected_behavior) == 2

    def test_serialization_roundtrip(self, sample_expectation: FitExpectation) -> None:
        """Test JSON serialization and deserialization roundtrip."""
        json_str = sample_expectation.model_dump_json()
        restored = FitExpectation.model_validate_json(json_str)
        assert restored.parameter_bounds == sample_expectation.parameter_bounds
        assert restored.max_residual_rms == sample_expectation.max_residual_rms
        assert restored.literature_reference == sample_expectation.literature_reference

    def test_model_dump(self, sample_expectation: FitExpectation) -> None:
        """Test model_dump produces expected dict structure."""
        data = sample_expectation.model_dump()
        assert isinstance(data, dict)
        assert "parameter_bounds" in data
        assert data["physical_context"] == "Isolated Gaussian emission line"


class TestValidationReport:
    """Tests for the ValidationReport model."""

    def test_creation(self, mixed_report: ValidationReport) -> None:
        """Test ValidationReport creation with mixed results."""
        assert len(mixed_report.analytical_checks) == 2
        assert len(mixed_report.reference_benchmarks) == 1
        assert len(mixed_report.expectation_results) == 2
        assert mixed_report.chi_squared == 45.2

    def test_all_passed_false(self, mixed_report: ValidationReport) -> None:
        """Test all_passed returns False when some checks fail."""
        assert mixed_report.all_passed is False

    def test_all_passed_true(self) -> None:
        """Test all_passed returns True when all checks pass."""
        report = ValidationReport(
            timestamp=datetime(2025, 1, 15, tzinfo=timezone.utc),
            spectrafit_version="1.4.1",
            analytical_checks=[
                AnalyticalCheck(
                    name="check1",
                    passed=True,
                    expected=1.0,
                    measured=1.0,
                    tolerance=0.01,
                    metric="rtol",
                ),
            ],
            expectation_results=[
                ExpectationResult(expectation="test", passed=True),
            ],
        )
        assert report.all_passed is True

    def test_all_passed_empty(self) -> None:
        """Test all_passed returns True for empty report."""
        report = ValidationReport(
            timestamp=datetime(2025, 1, 15, tzinfo=timezone.utc),
            spectrafit_version="1.4.1",
        )
        assert report.all_passed is True

    def test_summary_with_failures(self, mixed_report: ValidationReport) -> None:
        """Test summary reports correct pass/fail counts."""
        summary = mixed_report.summary
        assert "FAILED" in summary
        assert "3/5" in summary
        assert "2 failed" in summary

    def test_summary_all_passed(self) -> None:
        """Test summary when all checks pass."""
        report = ValidationReport(
            timestamp=datetime(2025, 1, 15, tzinfo=timezone.utc),
            spectrafit_version="1.4.1",
            analytical_checks=[
                AnalyticalCheck(
                    name="ok",
                    passed=True,
                    expected=1.0,
                    measured=1.0,
                    tolerance=0.01,
                    metric="rtol",
                ),
            ],
        )
        assert "PASSED" in report.summary
        assert "1/1" in report.summary

    def test_to_json_roundtrip(self, mixed_report: ValidationReport) -> None:
        """Test to_json produces valid JSON that can be deserialized."""
        json_str = mixed_report.to_json()
        data = json.loads(json_str)
        assert data["spectrafit_version"] == "1.4.1"
        assert data["config_hash"] == "abc123"
        assert len(data["analytical_checks"]) == 2
        assert data["chi_squared"] == 45.2

        restored = ValidationReport.model_validate(data)
        assert restored.spectrafit_version == mixed_report.spectrafit_version
        assert len(restored.analytical_checks) == 2
        assert restored.all_passed is False

    def test_to_html_structure(self, mixed_report: ValidationReport) -> None:
        """Test to_html produces valid HTML structure."""
        html = mixed_report.to_html()
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "SpectraFit Validation Report" in html

    def test_to_html_contains_results(self, mixed_report: ValidationReport) -> None:
        """Test to_html includes check results and metrics."""
        html = mixed_report.to_html()
        assert "gaussian_area_recovery" in html
        assert "center_position" in html
        assert "NIST_SRM_2242" in html
        assert "PASS" in html
        assert "FAIL" in html
        assert "45.2" in html

    def test_to_html_badges(self, mixed_report: ValidationReport) -> None:
        """Test to_html includes pass/fail badge styling."""
        html = mixed_report.to_html()
        assert "badge-pass" in html
        assert "badge-fail" in html

    def test_to_html_escapes_special_chars(self) -> None:
        """Test to_html escapes HTML special characters."""
        report = ValidationReport(
            timestamp=datetime(2025, 1, 15, tzinfo=timezone.utc),
            spectrafit_version="1.4.1",
            expectation_results=[
                ExpectationResult(
                    expectation="value < 0.5 & value > 0.1",
                    passed=True,
                    details='uses "quotes"',
                ),
            ],
        )
        html = report.to_html()
        assert "&lt;" in html
        assert "&amp;" in html
        assert "&quot;" in html
