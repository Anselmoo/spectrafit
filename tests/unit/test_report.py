"""Unit tests for FitSummaryReport and Pydantic-first report CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest

from spectrafit.models.fit_summary import FitInsightsReport
from spectrafit.models.fit_summary import FitStatisticsReport
from spectrafit.models.fit_summary import FitSummaryReport
from spectrafit.models.fit_summary import FitVariableReport
from spectrafit.models.fit_summary import SplitOrientFrame


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SUMMARY_JSON = Path("spectrafit_results_summary.json")


# ---------------------------------------------------------------------------
# FitStatisticsReport
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFitStatisticsReport:
    """Tests for FitStatisticsReport model."""

    def test_default_none(self) -> None:
        stats = FitStatisticsReport()
        assert stats.chi_square is None
        assert stats.reduced_chi_square is None
        assert stats.akaike_information is None
        assert stats.bayesian_information is None

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("chi_square", 0.001),
            ("reduced_chi_square", 0.0005),
            ("akaike_information", -120.5),
            ("bayesian_information", -110.0),
        ],
    )
    def test_round_trip_float(self, field: str, value: float) -> None:
        stats = FitStatisticsReport(**{field: value})
        assert getattr(stats, field) == pytest.approx(value)


# ---------------------------------------------------------------------------
# FitVariableReport
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFitVariableReport:
    """Tests for FitVariableReport model."""

    def test_defaults_none(self) -> None:
        var = FitVariableReport()
        assert var.init_value is None
        assert var.model_value is None
        assert var.best_value is None
        assert var.stderr is None

    def test_populated(self) -> None:
        var = FitVariableReport(init_value=1.0, model_value=1.25, best_value=1.25, stderr=0.01)
        assert var.best_value == pytest.approx(1.25)
        assert var.stderr == pytest.approx(0.01)

    def test_model_dump_exclude_none(self) -> None:
        var = FitVariableReport(best_value=2.0)
        dumped = var.model_dump(exclude_none=True)
        assert "best_value" in dumped
        assert "init_value" not in dumped


# ---------------------------------------------------------------------------
# FitInsightsReport
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFitInsightsReport:
    """Tests for FitInsightsReport model."""

    def test_empty_defaults(self) -> None:
        ins = FitInsightsReport()
        assert isinstance(ins.statistics, FitStatisticsReport)
        assert ins.variables == {}

    def test_validates_variables_as_models(self) -> None:
        ins = FitInsightsReport(
            variables={"p1_amplitude": {"best_value": 1.25, "init_value": 1.0}}
        )
        var = ins.variables["p1_amplitude"]
        assert isinstance(var, FitVariableReport)
        assert var.best_value == pytest.approx(1.25)


# ---------------------------------------------------------------------------
# FitSummaryReport
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFitSummaryReport:
    """Tests for FitSummaryReport model."""

    def test_empty_defaults(self) -> None:
        rpt = FitSummaryReport()
        assert isinstance(rpt.fit_insights, FitInsightsReport)
        assert isinstance(rpt.regression_metrics, SplitOrientFrame)
        assert rpt.regression_metrics.columns == []
        assert isinstance(rpt.linear_correlation, SplitOrientFrame)
        assert rpt.linear_correlation.columns == []
        assert rpt.outfile is None

    def test_model_validate_nested(self) -> None:
        data: dict[str, object] = {
            "fit_insights": {
                "statistics": {"chi_square": 0.0012, "reduced_chi_square": 0.0006},
                "variables": {
                    "p1_amplitude": {
                        "init_value": 1.0,
                        "model_value": 1.25,
                        "best_value": 1.25,
                    }
                },
            },
            "outfile": "my_fit",
        }
        rpt = FitSummaryReport.model_validate(data)
        assert rpt.fit_insights.statistics.chi_square == pytest.approx(0.0012)
        assert rpt.outfile == "my_fit"

    def test_extra_keys_ignored(self) -> None:
        """FitSummaryReport uses extra='allow' — unknown top-level keys don't raise."""
        rpt = FitSummaryReport.model_validate({"unknown_key": "foo", "outfile": "bar"})
        assert rpt.outfile == "bar"

    @pytest.mark.skipif(
        not SUMMARY_JSON.exists(),
        reason="spectrafit_results_summary.json not present in working directory",
    )
    def test_load_real_summary_json(self) -> None:
        """End-to-end: load the real output file from the repo root."""
        rpt = FitSummaryReport.from_json_file(SUMMARY_JSON)
        stats = rpt.fit_insights.statistics
        assert stats.chi_square is not None
        assert stats.reduced_chi_square is not None
        assert len(rpt.fit_insights.variables) > 0


# ---------------------------------------------------------------------------
# Report generators
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestReportGenerators:
    """Tests for the three _generate_*_report functions."""

    @pytest.fixture()
    def sample_summary(self) -> FitSummaryReport:
        return FitSummaryReport.model_validate(
            {
                "fit_insights": {
                    "statistics": {
                        "chi_square": 0.001,
                        "reduced_chi_square": 0.0005,
                        "akaike_information": -100.0,
                        "bayesian_information": -90.0,
                    },
                    "variables": {
                        "p1_amplitude": {
                            "init_value": 1.0,
                            "model_value": 1.25,
                            "best_value": 1.25,
                        }
                    },
                },
                "outfile": "test_fit",
            }
        )

    def test_text_report_contains_stats(self, sample_summary: FitSummaryReport) -> None:
        from spectrafit.cli.commands.report import _generate_text_report

        text = _generate_text_report(sample_summary, ["summary"])
        assert "Chi-square" in text
        assert "0.001" in text

    def test_text_report_contains_variables(self, sample_summary: FitSummaryReport) -> None:
        from spectrafit.cli.commands.report import _generate_text_report

        text = _generate_text_report(sample_summary, ["variables"])
        assert "p1_amplitude" in text
        assert "1.25" in text

    def test_markdown_report_structure(self, sample_summary: FitSummaryReport) -> None:
        from spectrafit.cli.commands.report import _generate_markdown_report

        md = _generate_markdown_report(sample_summary, ["summary", "variables"])
        assert "# SpectraFit Report" in md
        assert "## Fit Summary" in md
        assert "| Chi-square |" in md
        assert "| p1_amplitude |" in md

    def test_json_report_round_trip(self, sample_summary: FitSummaryReport) -> None:
        import json

        from spectrafit.cli.commands.report import _generate_json_report

        json_str = _generate_json_report(sample_summary, ["summary", "variables"])
        parsed = json.loads(json_str)
        assert "summary" in parsed
        assert "variables" in parsed
        assert "p1_amplitude" in parsed["variables"]

    def test_json_report_sections_filtered(self, sample_summary: FitSummaryReport) -> None:
        import json

        from spectrafit.cli.commands.report import _generate_json_report

        json_str = _generate_json_report(sample_summary, ["summary"])
        parsed = json.loads(json_str)
        assert "summary" in parsed
        assert "variables" not in parsed

    def test_no_cast_in_report_module(self) -> None:
        """Regression guard: cast() must not appear in report.py."""
        import importlib
        import inspect

        import spectrafit.cli.commands.report as report_mod

        source = inspect.getsource(report_mod)
        assert "cast(" not in source, "cast() detected in report.py — use Pydantic attribute access"
