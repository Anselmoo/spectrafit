"""Pydantic models for scientific validation and user attribution.

This module provides models for validating spectral fitting results against
analytical ground truths, reference benchmarks, and user-defined expectations.
It supports dual export as JSON and self-contained HTML reports.
"""

from __future__ import annotations

import json

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class AnalyticalCheck(BaseModel):
    """Result of an analytical ground-truth validation.

    Attributes:
        name: Identifier for the check, e.g. ``"gaussian_area_recovery"``.
        passed: Whether the check passed.
        expected: The expected ground-truth value.
        measured: The measured value from the fit.
        tolerance: The tolerance used for comparison.
        metric: The comparison metric, either ``"rtol"`` or ``"atol"``.
        description: Optional human-readable description.
    """

    name: str
    passed: bool
    expected: float
    measured: float
    tolerance: float
    metric: str
    description: str = ""


class ReferenceBenchmark(BaseModel):
    """Result of a reference data comparison.

    Attributes:
        dataset_name: Name of the reference dataset.
        passed: Whether the benchmark passed.
        deviation_metric: The metric used, e.g. ``"rmse"`` or ``"max_abs_error"``.
        deviation_value: The computed deviation value.
        threshold: The maximum acceptable deviation.
        description: Optional human-readable description.
    """

    dataset_name: str
    passed: bool
    deviation_metric: str
    deviation_value: float
    threshold: float
    description: str = ""


class ExpectationResult(BaseModel):
    """Result of a user-defined expectation check.

    Attributes:
        expectation: The original expectation text.
        passed: Whether the expectation was met.
        details: Optional details about the result.
    """

    expectation: str
    passed: bool
    details: str = ""


class FitExpectation(BaseModel):
    """User-defined qualitative and quantitative expectations for validation.

    This model captures domain knowledge and scientific context about what
    a fit should look like. It enables:

    - Automated validation against known constraints
    - Scientific attribution (documenting why certain results are expected)
    - Future MCP/LLM consumption of domain knowledge

    Attributes:
        parameter_bounds: Mapping of parameter names to ``(min, max)`` bounds.
        max_residual_rms: Maximum acceptable RMS of residuals.
        min_r_squared: Minimum acceptable R-squared value.
        description: Free-text description of the expectation.
        expected_behavior: List of expected qualitative behaviors.
        physical_context: Physical context for the fit.
        literature_reference: Literature reference supporting the expectation.
    """

    parameter_bounds: dict[str, tuple[float, float]] = Field(default_factory=dict)
    max_residual_rms: float | None = None
    min_r_squared: float | None = None
    description: str = ""
    expected_behavior: list[str] = Field(default_factory=list)
    physical_context: str = ""
    literature_reference: str = ""


class ValidationReport(BaseModel):
    """Scientific validation report with dual export as JSON and HTML.

    Attributes:
        timestamp: When the validation was performed.
        spectrafit_version: Version of SpectraFit used.
        config_hash: Hash of the configuration used for reproducibility.
        analytical_checks: Results of analytical ground-truth checks.
        reference_benchmarks: Results of reference data comparisons.
        expectation_results: Results of user-defined expectation checks.
        chi_squared: Chi-squared statistic of the fit.
        reduced_chi_squared: Reduced chi-squared statistic.
        r_squared: R-squared coefficient of determination.
        residual_rms: Root mean square of residuals.
        parameter_uncertainties: Mapping of parameter names to uncertainties.
    """

    timestamp: datetime
    spectrafit_version: str
    config_hash: str = ""
    analytical_checks: list[AnalyticalCheck] = Field(default_factory=list)
    reference_benchmarks: list[ReferenceBenchmark] = Field(default_factory=list)
    expectation_results: list[ExpectationResult] = Field(default_factory=list)
    chi_squared: float | None = None
    reduced_chi_squared: float | None = None
    r_squared: float | None = None
    residual_rms: float | None = None
    parameter_uncertainties: dict[str, float] = Field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        """Return True if all checks passed."""
        all_checks: list[bool] = [c.passed for c in self.analytical_checks]
        all_checks.extend(b.passed for b in self.reference_benchmarks)
        all_checks.extend(e.passed for e in self.expectation_results)
        return all(all_checks) if all_checks else True

    @property
    def summary(self) -> str:
        """Return a human-readable summary of the validation report."""
        total = (
            len(self.analytical_checks)
            + len(self.reference_benchmarks)
            + len(self.expectation_results)
        )
        passed = (
            sum(c.passed for c in self.analytical_checks)
            + sum(b.passed for b in self.reference_benchmarks)
            + sum(e.passed for e in self.expectation_results)
        )
        failed = total - passed
        status = "PASSED" if self.all_passed else "FAILED"
        return f"Validation {status}: {passed}/{total} checks passed, {failed} failed."

    def to_json(self) -> str:
        """Export as JSON string.

        Returns:
            A JSON-serialized string of the validation report.
        """
        return self.model_dump_json(indent=2)

    def to_html(self) -> str:
        """Export as a self-contained HTML report with tables and badges.

        Returns:
            A self-contained HTML string with inline CSS styling.
        """
        status = "PASSED" if self.all_passed else "FAILED"
        badge_color = "#28a745" if self.all_passed else "#dc3545"

        rows_analytical = ""
        for c in self.analytical_checks:
            badge = _html_badge(c.passed)
            rows_analytical += (
                f"<tr><td>{_esc(c.name)}</td><td>{badge}</td>"
                f"<td>{c.expected}</td><td>{c.measured}</td>"
                f"<td>{c.tolerance}</td><td>{_esc(c.metric)}</td></tr>\n"
            )

        rows_benchmark = ""
        for b in self.reference_benchmarks:
            badge = _html_badge(b.passed)
            rows_benchmark += (
                f"<tr><td>{_esc(b.dataset_name)}</td><td>{badge}</td>"
                f"<td>{_esc(b.deviation_metric)}</td>"
                f"<td>{b.deviation_value}</td><td>{b.threshold}</td></tr>\n"
            )

        rows_expectation = ""
        for e in self.expectation_results:
            badge = _html_badge(e.passed)
            rows_expectation += (
                f"<tr><td>{_esc(e.expectation)}</td><td>{badge}</td>"
                f"<td>{_esc(e.details)}</td></tr>\n"
            )

        metrics_rows = "".join(
            f"<tr><td>{label}</td><td>{value}</td></tr>\n"
            for label, value in [
                ("Chi-squared", self.chi_squared),
                ("Reduced Chi-squared", self.reduced_chi_squared),
                ("R-squared", self.r_squared),
                ("Residual RMS", self.residual_rms),
            ]
            if value is not None
        )
        data = json.loads(self.model_dump_json())
        ts = data.get("timestamp", str(self.timestamp))

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SpectraFit Validation Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2em; }}
h1 {{ color: #333; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5em; }}
th, td {{ border: 1px solid #ccc; padding: 0.5em 0.75em; text-align: left; }}
th {{ background-color: #f4f4f4; }}
.badge {{ padding: 0.2em 0.6em; border-radius: 4px; color: #fff; font-weight: bold; }}
.badge-pass {{ background-color: #28a745; }}
.badge-fail {{ background-color: #dc3545; }}
</style>
</head>
<body>
<h1>SpectraFit Validation Report</h1>
<p><strong>Timestamp:</strong> {ts}</p>
<p><strong>Version:</strong> {_esc(self.spectrafit_version)}</p>
<p><strong>Status:</strong> \
<span class="badge" style="background-color:{badge_color}">{status}</span></p>
<p>{_esc(self.summary)}</p>

<h2>Analytical Checks</h2>
<table>
<tr><th>Name</th><th>Result</th><th>Expected</th>\
<th>Measured</th><th>Tolerance</th><th>Metric</th></tr>
{rows_analytical}</table>

<h2>Reference Benchmarks</h2>
<table>
<tr><th>Dataset</th><th>Result</th><th>Metric</th>\
<th>Deviation</th><th>Threshold</th></tr>
{rows_benchmark}</table>

<h2>Expectation Results</h2>
<table>
<tr><th>Expectation</th><th>Result</th><th>Details</th></tr>
{rows_expectation}</table>

<h2>Fit Quality Metrics</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
{metrics_rows}</table>
</body>
</html>"""


def _html_badge(passed: bool) -> str:
    """Return an HTML badge span for pass/fail status.

    Args:
        passed: Whether the check passed.

    Returns:
        An HTML ``<span>`` element with the appropriate badge class.
    """
    if passed:
        return '<span class="badge badge-pass">PASS</span>'
    return '<span class="badge badge-fail">FAIL</span>'


def _esc(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: The raw text to escape.

    Returns:
        The escaped text safe for HTML insertion.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
