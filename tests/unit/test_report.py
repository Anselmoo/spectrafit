"""Unit tests for canonical report models and shared report rendering services."""

from __future__ import annotations

import importlib
import json
import sys
import warnings

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from spectrafit.adapters.fit_result_json import load_fit_result
from spectrafit.adapters.fit_result_json import save_fit_result
from spectrafit.cli.main import app
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import FitStatistics
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.split_frame import SplitFrame
from typer.testing import CliRunner


if TYPE_CHECKING:
    import pandas as pd


runner = CliRunner()
report_module = importlib.import_module("spectrafit.cli.commands.report")


@pytest.mark.unit
class TestCanonicalResultModels:
    """Tests for the canonical FitResult reporting surface."""

    def test_variable_fit_result_defaults_none(self) -> None:
        var = VariableFitResult()
        assert var.init_value is None
        assert var.model_value is None
        assert var.best_value is None
        assert var.stderr is None

    def test_fit_insights_validates_variables_as_models(self) -> None:
        insights = FitInsights(
            variables={"p1_amplitude": {"best_value": 1.25, "init_value": 1.0}}
        )
        var = insights.variables["p1_amplitude"]
        assert isinstance(var, VariableFitResult)
        assert var.best_value == pytest.approx(1.25)

    def test_fit_result_json_adapter_round_trip(self, tmp_path: Path) -> None:
        result_path = tmp_path / "fit_result.json"
        fit_result = FitResult(
            fit_insights=FitInsights(
                statistics={"chi_square": 0.0012},
                variables={"p1_center": VariableFitResult(best_value=0.1)},
            ),
            data_summary=DataSummary(
                regression_metrics={
                    "index": ["r2"],
                    "columns": ["value"],
                    "data": [[0.99]],
                },
                linear_correlation={
                    "index": ["energy"],
                    "columns": ["energy"],
                    "data": [[1.0]],
                },
            ),
        )

        save_fit_result(fit_result, result_path)
        loaded = load_fit_result(result_path)

        assert loaded.fit_insights.statistics["chi_square"] == pytest.approx(0.0012)
        assert loaded.fit_insights.variables["p1_center"].best_value == pytest.approx(
            0.1
        )
        assert loaded.data_summary.regression_metrics["columns"] == ["value"]


@pytest.mark.unit
class TestReportGenerators:
    """Tests for the shared report rendering and CLI adapter."""

    @pytest.fixture
    def sample_result(self) -> FitResult:
        return FitResult(
            fit_insights=FitInsights(
                statistics={
                    "chi_square": 0.001,
                    "reduced_chi_square": 0.0005,
                    "akaike_information": -100.0,
                    "bayesian_information": -90.0,
                },
                variables={
                    "p1_amplitude": VariableFitResult(
                        init_value=1.0,
                        model_value=1.25,
                        best_value=1.25,
                    )
                },
            ),
            data_summary=DataSummary(
                regression_metrics={
                    "index": ["r2"],
                    "columns": ["value"],
                    "data": [[0.99]],
                },
                linear_correlation={
                    "index": ["energy"],
                    "columns": ["energy"],
                    "data": [[1.0]],
                },
            ),
        )

    def test_text_report_contains_stats(self, sample_result: FitResult) -> None:
        from spectrafit.reporting.service import render_text_report

        text = render_text_report(sample_result, ["summary"])
        assert "Chi-square" in text
        assert "0.001" in text

    def test_text_report_falls_back_to_canonical_fit_statistics(self) -> None:
        from spectrafit.reporting.service import render_text_report

        fit_result = FitResult(
            statistics=FitStatistics(
                method="leastsq",
                chisqr=0.00123,
                redchi=0.00061,
                aic=-42.0,
                bic=-40.5,
                success=True,
                message="ok",
            )
        )

        text = render_text_report(fit_result, ["summary"])

        assert "0.00123" in text
        assert "-42.0" in text

    def test_dashboard_summary_falls_back_to_canonical_fit_statistics(self) -> None:
        from spectrafit.reporting.service import project_dashboard_payload

        fit_result = FitResult(
            statistics=FitStatistics(
                method="leastsq",
                chisqr=0.00123,
                redchi=0.00061,
                aic=-42.0,
                bic=-40.5,
                success=True,
                message="ok",
            ),
            x=[0.0, 1.0],
            y_data=[1.0, 2.0],
            y_fit=[1.1, 1.9],
        )

        payload = project_dashboard_payload(fit_result)

        assert payload.summary.chi_square == pytest.approx(0.00123)
        assert payload.summary.reduced_chi_square == pytest.approx(0.00061)

    def test_text_report_contains_variables(self, sample_result: FitResult) -> None:
        from spectrafit.reporting.service import render_text_report

        text = render_text_report(sample_result, ["variables"])
        assert "p1_amplitude" in text
        assert "1.25" in text
        assert "best=1.25" in text

    def test_markdown_report_structure(self, sample_result: FitResult) -> None:
        from spectrafit.reporting.service import render_markdown_report

        md = render_markdown_report(sample_result, ["summary", "variables"])
        assert "# SpectraFit Report" in md
        assert "## Fit Summary" in md
        assert "| Chi-square |" in md
        assert "| p1_amplitude |" in md

    def test_json_report_round_trip(self, sample_result: FitResult) -> None:
        from spectrafit.reporting.service import render_json_report

        json_str = render_json_report(sample_result, ["summary", "variables"])
        parsed = json.loads(json_str)
        assert "summary" in parsed
        assert "variables" in parsed
        assert "p1_amplitude" in parsed["variables"]

    def test_json_report_sections_filtered(self, sample_result: FitResult) -> None:
        from spectrafit.reporting.service import render_json_report

        json_str = render_json_report(sample_result, ["summary"])
        parsed = json.loads(json_str)
        assert "summary" in parsed
        assert "variables" not in parsed

    def test_runtime_report_includes_preprocessing_section(
        self, sample_result: FitResult
    ) -> None:
        from spectrafit.reporting.service import render_runtime_report

        text = render_runtime_report(
            fit_result=sample_result,
            data_statistic=SplitFrame(
                index=["mean"],
                columns=["energy", "intensity"],
                data=[[1.0, 2.0]],
            ),
            verbose=1,
        )
        assert "Preprocessing statistics" in text
        assert "mean" in text
        assert "SpectraFit Report" in text

    def test_runtime_report_detailed_mode_is_json(
        self, sample_result: FitResult
    ) -> None:
        from spectrafit.reporting.service import render_runtime_report

        payload = json.loads(
            render_runtime_report(
                fit_result=sample_result,
                data_statistic=SplitFrame.empty(),
                verbose=2,
            )
        )
        assert "preprocessing" in payload
        assert payload["fit_result"]["fit_insights"]["statistics"][
            "chi_square"
        ] == pytest.approx(0.001)

    def test_dashboard_payload_projects_canonical_series(
        self, sample_result: FitResult
    ) -> None:
        from spectrafit.models.results.fit_result import ComponentResult
        from spectrafit.models.results.fit_result import FitStatistics
        from spectrafit.models.results.fit_result import ParameterResult
        from spectrafit.reporting.service import project_dashboard_payload

        sample_result.statistics = FitStatistics(
            method="leastsq",
            chisqr=0.001,
            redchi=0.0005,
            aic=-100.0,
            bic=-90.0,
            success=True,
            message="ok",
        )
        sample_result.parameters = [
            ParameterResult(
                name="p1_amplitude",
                init_value=1.0,
                best_value=1.25,
                stderr=0.02,
            )
        ]
        sample_result.x = [0.0, 1.0, 2.0]
        sample_result.y_data = [1.0, 2.0, 3.0]
        sample_result.y_fit = [0.9, 2.1, 2.9]
        sample_result.components = [
            ComponentResult(id="p1", model="gaussian", curve=[0.4, 0.9, 1.1])
        ]

        payload = project_dashboard_payload(sample_result)

        assert payload.summary.chi_square == pytest.approx(0.001)
        assert payload.traces[0].label == "Observed"
        assert payload.traces[0].y_values == [1.0, 2.0, 3.0]
        assert payload.traces[1].label == "Fit"
        assert payload.traces[2].trace_kind == "component"
        assert payload.traces[2].component_id == "p1"
        assert payload.parameters[0].name == "p1_amplitude"

    def test_dashboard_png_renderer_writes_static_artifact(
        self, tmp_path: Path, sample_result: FitResult
    ) -> None:
        from spectrafit.models.results.fit_result import ComponentResult
        from spectrafit.reporting.dashboard import write_dashboard_png

        sample_result.x = [0.0, 1.0, 2.0]
        sample_result.y_data = [1.0, 2.0, 3.0]
        sample_result.y_fit = [0.9, 2.1, 2.9]
        sample_result.components = [
            ComponentResult(id="p1", model="gaussian", curve=[0.4, 0.9, 1.1])
        ]

        output_path = write_dashboard_png(
            sample_result,
            tmp_path / "dashboard.png",
        )

        assert output_path.exists()
        assert output_path.suffix == ".png"
        assert output_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    def test_legacy_printer_delegates_to_shared_runtime_report(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import pandas as pd

        from spectrafit.core.postprocessing import PostProcessingResult
        from spectrafit.models.fitting_context import FittingMode

        captured: dict[str, object] = {}

        def capture_emit_runtime_report(
            *,
            fit_result: FitResult,
            data_statistic: SplitFrame,
            verbose: int,
        ) -> None:
            captured["fit_result"] = fit_result
            captured["data_statistic"] = data_statistic
            captured["verbose"] = verbose

        for module_name in list(sys.modules):
            if module_name == "spectrafit.report" or module_name.startswith(
                "spectrafit.report."
            ):
                monkeypatch.delitem(sys.modules, module_name, raising=False)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            legacy_printer = importlib.import_module("spectrafit.report.printer")

        monkeypatch.setattr(
            legacy_printer,
            "emit_runtime_report",
            capture_emit_runtime_report,
        )

        fit_df = pd.DataFrame(
            {
                "energy": [1.0, 2.0],
                "intensity": [3.0, 4.0],
                "fit": [2.9, 4.1],
            }
        )
        post = PostProcessingResult(
            df=fit_df,
            fit_insights=FitInsights(
                statistics={"chi_square": 0.125},
                variables={"p1_center": VariableFitResult(best_value=1.2)},
            ),
            confidence_interval=ConfidenceResults(
                settings={"sigma": [1.0]},
                results={"p1_center": [(0.0, 1.2), (1.0, 1.1), (1.0, 1.3)]},
            ),
            fit_result_data=SplitFrame.from_dataframe(fit_df),
            regression_metrics=SplitFrame(
                index=["r2"],
                columns=["value"],
                data=[[0.99]],
            ),
            descriptive_statistic=SplitFrame(
                index=["mean"],
                columns=["energy", "intensity"],
                data=[[1.5, 3.5]],
            ),
            linear_correlation=SplitFrame(
                index=["energy"],
                columns=["energy"],
                data=[[1.0]],
            ),
        )
        result = SimpleNamespace(
            params={
                "p1_center": SimpleNamespace(
                    init_value=1.0,
                    value=1.2,
                    stderr=0.1,
                    vary=True,
                    expr=None,
                )
            },
            method="leastsq",
            nfev=7,
            ndata=2,
            nvarys=1,
            nfree=1,
            chisqr=0.125,
            redchi=0.0625,
            aic=1.0,
            bic=2.0,
            success=True,
            message="ok",
        )
        minimizer = SimpleNamespace(max_nfev=25, nan_policy="raise")
        data_statistic = SplitFrame(
            index=["mean"],
            columns=["energy", "intensity"],
            data=[[1.5, 3.5]],
        )

        legacy_printer.PrintingResults(
            post=post,
            result=result,
            minimizer=minimizer,
            data_statistic=data_statistic,
            conf_interval=True,
            verbose=1,
        )()

        assert captured["verbose"] == 1
        delegated_fit_result = captured["fit_result"]
        delegated_data_statistic = captured["data_statistic"]
        assert isinstance(delegated_fit_result, FitResult)
        assert isinstance(delegated_data_statistic, SplitFrame)
        assert delegated_fit_result.global_fitting == FittingMode.STANDARD
        assert delegated_fit_result.fit_insights.statistics[
            "chi_square"
        ] == pytest.approx(0.125)
        assert delegated_data_statistic.columns == ["energy", "intensity"]

    def test_legacy_printer_verbose_fit_section_outputs_structured_json(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import pandas as pd

        from spectrafit.core.postprocessing import PostProcessingResult

        for module_name in list(sys.modules):
            if module_name == "spectrafit.report" or module_name.startswith(
                "spectrafit.report."
            ):
                monkeypatch.delitem(sys.modules, module_name, raising=False)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            legacy_printer = importlib.import_module("spectrafit.report.printer")

        fit_df = pd.DataFrame(
            {
                "energy": [1.0],
                "intensity": [2.0],
                "fit": [2.0],
            }
        )
        printer = legacy_printer.PrintingResults(
            post=PostProcessingResult(
                df=fit_df,
                fit_insights=FitInsights(
                    statistics={"chi_square": 0.5},
                    variables={"p1_amplitude": VariableFitResult(best_value=2.0)},
                ),
                fit_result_data=SplitFrame.from_dataframe(fit_df),
            ),
            result=SimpleNamespace(
                params={
                    "p1_amplitude": SimpleNamespace(
                        init_value=1.5,
                        value=2.0,
                        stderr=0.2,
                        vary=True,
                        expr=None,
                    )
                },
                method="leastsq",
                nfev=3,
                ndata=1,
                nvarys=1,
                nfree=1,
                chisqr=0.5,
                redchi=0.5,
                aic=1.0,
                bic=1.0,
                success=True,
                message="ok",
            ),
            minimizer=SimpleNamespace(max_nfev=10, nan_policy="propagate"),
            verbose=2,
        )

        printer.print_fit_results_verbose()

        payload = json.loads(capsys.readouterr().out)
        assert payload["fit_insights"]["statistics"]["chi_square"] == pytest.approx(0.5)
        assert "p1_amplitude" in payload["fit_insights"]["variables"]

    def test_solver_projection_reuses_canonical_fit_result(
        self, sample_result: FitResult
    ) -> None:
        from spectrafit.reporting.service import CanonicalReportSchema
        from spectrafit.reporting.service import project_canonical_report
        from spectrafit.reporting.service import project_solver_report

        projection = project_solver_report(sample_result)
        assert projection.goodness_of_fit == sample_result.fit_insights.statistics
        assert projection.variables is sample_result.fit_insights.variables
        assert (
            projection.descriptive_statistic
            == sample_result.data_summary.descriptive_statistic
        )

        report_schema = project_canonical_report(sample_result)
        assert isinstance(report_schema, CanonicalReportSchema)
        assert report_schema.solver == projection
        assert report_schema.statistics == sample_result.statistics
        assert report_schema.configurations == sample_result.fit_insights.configurations

    def test_confidence_projection_preserves_legacy_reporting_contract(self) -> None:
        from spectrafit.reporting.service import normalize_confidence_interval_settings
        from spectrafit.reporting.service import project_canonical_report
        from spectrafit.reporting.service import project_solver_report

        fit_result = FitResult(
            confidence=ConfidenceResults(
                settings=ConfIntervalConfig(
                    p_names=["p1_amplitude"],
                    sigmas=[1.0, 2.0],
                    trace=True,
                    maxiter=75,
                    verbose=True,
                    prob_func="f_compare",
                ),
                results={"p1_amplitude": [(1.0, 0.9), (2.0, 1.1)]},
            )
        )

        assert normalize_confidence_interval_settings(fit_result) == {
            "p_names": ["p1_amplitude"],
            "trace": True,
            "maxiter": 75,
            "verbose": True,
        }
        assert project_solver_report(fit_result).confidence_interval == {
            "p1_amplitude": [(1.0, 0.9), (2.0, 1.1)]
        }
        assert project_canonical_report(fit_result).confidence_settings == {
            "p_names": ["p1_amplitude"],
            "trace": True,
            "maxiter": 75,
            "verbose": True,
        }

    def test_json_report_uses_single_canonical_report_schema(
        self,
        sample_result: FitResult,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from spectrafit.models.results.fit_result import FitConfigurations
        from spectrafit.models.results.fit_result import FitStatistics
        from spectrafit.reporting.service import CanonicalReportSchema
        from spectrafit.reporting.service import FitSummaryProjection
        from spectrafit.reporting.service import SolverReportProjection
        from spectrafit.reporting.service import render_json_report

        canonical_report = CanonicalReportSchema(
            summary=FitSummaryProjection(
                chi_square=7.5,
                reduced_chi_square=3.25,
            ),
            solver=SolverReportProjection.model_construct(
                goodness_of_fit=sample_result.fit_insights.statistics,
                regression_metrics=sample_result.data_summary.regression_metrics,
                descriptive_statistic=sample_result.data_summary.descriptive_statistic,
                linear_correlation=sample_result.data_summary.linear_correlation,
                component_correlation=sample_result.fit_insights.correlations,
                confidence_interval=sample_result.confidence.report_results(),
                covariance_matrix=sample_result.fit_insights.covariance_matrix,
                variables={
                    "projected_peak": VariableFitResult(best_value=9.9, stderr=0.2)
                },
                errorbars=sample_result.fit_insights.errorbars,
                computational=sample_result.fit_insights.computational,
            ),
            statistics=FitStatistics(method="custom"),
            configurations=FitConfigurations(method="custom"),
            confidence_settings=False,
        )

        monkeypatch.setattr(
            "spectrafit.reporting.service.project_canonical_report",
            lambda _fit_result: canonical_report,
        )

        payload = json.loads(
            render_json_report(sample_result, ["summary", "variables"])
        )
        assert payload["summary"] == {
            "chi_square": 7.5,
            "reduced_chi_square": 3.25,
        }
        assert payload["variables"] == {
            "projected_peak": {"best_value": 9.9, "stderr": 0.2}
        }
        assert "p1_amplitude" not in payload["variables"]

    def test_text_report_uses_shared_solver_projection_for_projected_sections(
        self,
        sample_result: FitResult,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from spectrafit.reporting.service import SolverReportProjection
        from spectrafit.reporting.service import render_text_report

        projection = SolverReportProjection.model_construct(
            goodness_of_fit=sample_result.fit_insights.statistics,
            regression_metrics=SplitFrame(
                index=[0],
                columns=["projection_metric"],
                data=[[7.7]],
            ),
            descriptive_statistic=sample_result.data_summary.descriptive_statistic,
            linear_correlation=SplitFrame.empty(),
            component_correlation=sample_result.fit_insights.correlations,
            confidence_interval=sample_result.confidence.report_results(),
            covariance_matrix=sample_result.fit_insights.covariance_matrix,
            variables={"projected_peak": VariableFitResult(best_value=9.9, stderr=0.2)},
            errorbars=sample_result.fit_insights.errorbars,
            computational=sample_result.fit_insights.computational,
        )

        monkeypatch.setattr(
            "spectrafit.reporting.service.project_solver_report",
            lambda _fit_result: projection,
        )

        text = render_text_report(sample_result, ["variables", "statistics"])
        assert "projected_peak: best=9.9, stderr=0.2" in text
        assert "projection_metric: [7.7]" in text
        assert "p1_amplitude" not in text

    def test_json_report_uses_shared_solver_projection_for_variables(
        self,
        sample_result: FitResult,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from spectrafit.reporting.service import SolverReportProjection
        from spectrafit.reporting.service import render_json_report

        projection = SolverReportProjection.model_construct(
            goodness_of_fit=sample_result.fit_insights.statistics,
            regression_metrics=sample_result.data_summary.regression_metrics,
            descriptive_statistic=sample_result.data_summary.descriptive_statistic,
            linear_correlation=sample_result.data_summary.linear_correlation,
            component_correlation=sample_result.fit_insights.correlations,
            confidence_interval=sample_result.confidence.report_results(),
            covariance_matrix=sample_result.fit_insights.covariance_matrix,
            variables={"projected_peak": VariableFitResult(best_value=9.9, stderr=0.2)},
            errorbars=sample_result.fit_insights.errorbars,
            computational=sample_result.fit_insights.computational,
        )

        monkeypatch.setattr(
            "spectrafit.reporting.service.project_solver_report",
            lambda _fit_result: projection,
        )

        payload = json.loads(
            render_json_report(sample_result, ["summary", "variables"])
        )
        assert payload["summary"]["chi_square"] == pytest.approx(0.001)
        assert payload["variables"] == {
            "projected_peak": {"best_value": 9.9, "stderr": 0.2}
        }
        assert "p1_amplitude" not in payload["variables"]

    def test_json_report_uses_shared_summary_projection(
        self,
        sample_result: FitResult,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from spectrafit.reporting.service import FitSummaryProjection
        from spectrafit.reporting.service import render_json_report

        monkeypatch.setattr(
            "spectrafit.reporting.service.project_fit_summary",
            lambda _fit_result: FitSummaryProjection(
                chi_square=7.5,
                reduced_chi_square=3.25,
            ),
        )

        payload = json.loads(render_json_report(sample_result, ["summary"]))
        assert payload["summary"] == {
            "chi_square": 7.5,
            "reduced_chi_square": 3.25,
        }

    def test_legacy_ci_report_renders_canonical_confidence_projection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rendered: dict[str, pd.DataFrame] = {}

        def capture_table(df: pd.DataFrame, floatfmt: str = ".5f") -> None:
            del floatfmt
            rendered["df"] = df.copy()

        for module_name in list(sys.modules):
            if module_name == "spectrafit.report" or module_name.startswith(
                "spectrafit.report."
            ):
                monkeypatch.delitem(sys.modules, module_name, raising=False)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            legacy_confidence = importlib.import_module("spectrafit.report.confidence")

        monkeypatch.setattr(legacy_confidence, "print_tabulate_df", capture_table)

        confidence = ConfidenceResults(
            settings={"sigma": [1.0, 2.0]},
            results={"p1_center": [(0.0, 1.0), (1.0, 0.9), (1.0, 1.1)]},
        )

        legacy_confidence.CIReport(confidence.report_results())()

        assert "df" in rendered
        assert "p1_center" in rendered["df"].index
        assert "BEST" in rendered["df"].columns

    def test_legacy_ci_report_accepts_typed_confidence_results(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rendered: dict[str, pd.DataFrame] = {}

        def capture_table(df: pd.DataFrame, floatfmt: str = ".5f") -> None:
            del floatfmt
            rendered["df"] = df.copy()

        for module_name in list(sys.modules):
            if module_name == "spectrafit.report" or module_name.startswith(
                "spectrafit.report."
            ):
                monkeypatch.delitem(sys.modules, module_name, raising=False)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            legacy_confidence = importlib.import_module("spectrafit.report.confidence")

        monkeypatch.setattr(legacy_confidence, "print_tabulate_df", capture_table)

        confidence = ConfidenceResults(
            settings={"sigma": [1.0]},
            results={"p1_center": [(0.0, 1.0), (1.0, 0.9), (1.0, 1.1)]},
        )

        legacy_confidence.CIReport(confidence)()

        assert "df" in rendered
        assert "p1_center" in rendered["df"].index

    def test_no_cast_in_report_module(self) -> None:
        """Regression guard: cast() must not appear in report layers."""
        import inspect

        import spectrafit.cli.commands.report as report_mod
        import spectrafit.reporting.service as reporting_service

        report_source = inspect.getsource(report_mod)
        service_source = inspect.getsource(reporting_service)
        assert "cast(" not in report_source, (
            "cast() detected in report.py — use Pydantic attribute access"
        )
        assert "cast(" not in service_source, (
            "cast() detected in reporting service — use Pydantic attribute access"
        )
        assert "PrintingResults" not in service_source

    def test_report_service_avoids_statistics_dict_getters(self) -> None:
        """Report rendering should normalize fit statistics before presentation."""
        import inspect

        import spectrafit.reporting.service as reporting_service

        service_source = inspect.getsource(reporting_service)
        assert "stats.get(" not in service_source

    def test_report_command_reads_fitresult_json(self, tmp_path: Path) -> None:
        """CLI report should read canonical FitResult JSON files directly."""
        result_path = tmp_path / "fit_result.json"
        save_fit_result(
            FitResult(
                fit_insights=FitInsights(
                    statistics={"chi_square": 0.001},
                    variables={"p1_amplitude": VariableFitResult(best_value=1.25)},
                ),
            ),
            result_path,
        )

        result = runner.invoke(app, ["report", str(result_path)])
        assert result.exit_code == 0
        assert "Chi-square" in result.output

    def test_report_command_falls_back_to_canonical_statistics(self, tmp_path: Path) -> None:
        """CLI report should render canonical statistics even without summary dicts."""
        result_path = tmp_path / "fit_result.json"
        save_fit_result(
            FitResult(
                statistics=FitStatistics(
                    method="leastsq",
                    chisqr=0.125,
                    redchi=0.0625,
                    aic=1.0,
                    bic=2.0,
                    success=True,
                    message="ok",
                )
            ),
            result_path,
        )

        result = runner.invoke(app, ["report", str(result_path)])

        assert result.exit_code == 0
        assert "0.125" in result.output

    def test_report_command_writes_report_to_output_file(
        self,
        sample_result: FitResult,
        tmp_path: Path,
    ) -> None:
        result_path = tmp_path / "fit_result.json"
        output_path = tmp_path / "report.md"
        save_fit_result(sample_result, result_path)

        result = runner.invoke(
            app,
            [
                "report",
                str(result_path),
                "--output",
                str(output_path),
                "--format",
                "markdown",
                "--section",
                "summary",
            ],
        )

        assert result.exit_code == 0, result.output
        assert output_path.exists()
        assert "Report saved" in result.output
        assert "# SpectraFit Report" in output_path.read_text(encoding="utf-8")

    def test_report_command_surfaces_render_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_result: FitResult,
        tmp_path: Path,
    ) -> None:
        result_path = tmp_path / "fit_result.json"
        save_fit_result(sample_result, result_path)

        def _raise_render_error(*args: object, **kwargs: object) -> str:
            msg = "boom"
            raise ValueError(msg)

        monkeypatch.setattr(report_module, "render_report", _raise_render_error)

        result = runner.invoke(app, ["report", str(result_path)])

        assert result.exit_code == 1
        assert "Error generating report: boom" in result.output

    def test_report_command_is_thin_adapter(self) -> None:
        """CLI report command should delegate rendering to the shared service."""
        import inspect

        import spectrafit.cli.commands.report as report_mod

        source = inspect.getsource(report_mod)
        assert "render_report(" in source
        assert "def _generate_text_report" not in source
        assert "def _generate_markdown_report" not in source
        assert "def _generate_json_report" not in source
