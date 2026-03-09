"""Unit tests for Jupyter export report typing boundaries."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.report_model import ReportAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.jupyter.export import ExportReport
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.types import DataSplitDict


def _build_solver_results() -> SolverResults:
    fit_result = FitResult(
        fit_insights=FitInsights(
            configurations=FitConfigurations(method="leastsq", max_nfev=120, nan_policy="raise"),
            statistics={"chi_square": 0.1},
            variables={
                "p1_amplitude": VariableFitResult(
                    init_value=1.0,
                    model_value=1.1,
                    best_value=1.1,
                    stderr=0.01,
                )
            },
            errorbars={"p1_amplitude": "True"},
            computational={"nfev": 42},
        ),
        data_summary=DataSummary(
            regression_metrics=DataSplitDict(data=[[0.99]], index=[0], columns=["r2"]),
            descriptive_statistic=DataSplitDict(data=[[1.0]], index=[0], columns=["mean"]),
            linear_correlation=DataSplitDict(data=[[0.95]], index=[0], columns=["pearson"]),
        ),
        confidence=ConfidenceResults(
            settings={"trace": True, "maxiter": 100, "sigmas": [1.0, 2.0]},
        ),
    )
    return SolverResults(result=fit_result)


@pytest.fixture
def export_report_fixture() -> ExportReport:
    """Build a report exporter with typed solver output."""
    return ExportReport(
        description=DescriptionAPI(),
        initial_model=[
            {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
                    "center": {"value": 0.0, "vary": True, "min": -1.0, "max": 1.0},
                }
            }
        ],
        pre_processing=DataPreProcessingAPI(),
        settings_solver_models=SolverModelsAPI(),
        fname=FnameAPI(fname="report", suffix="lock"),
        solver=_build_solver_results(),
        df_org=pd.DataFrame({"energy": [1.0, 2.0], "data": [3.0, 4.0]}),
        df_fit=pd.DataFrame({"energy": [1.0, 2.0], "best_fit": [3.1, 3.9]}),
    )


@pytest.mark.unit
def test_export_report_call_returns_serializable_report(
    export_report_fixture: ExportReport,
) -> None:
    """Report payload is returned as nested dict structure without unsupported keys."""
    report = export_report_fixture()
    confidence_settings = report["input"]["method"]["confidence_interval"]
    assert isinstance(confidence_settings, dict)
    assert "sigmas" not in confidence_settings
    assert "solver" in report


@pytest.mark.unit
def test_export_results_accepts_report_model(
    tmp_path: Path,
    export_report_fixture: ExportReport,
) -> None:
    """``ExportResults.export_report`` accepts both dict payloads and ReportAPI models."""
    report_model = ReportAPI(
        input=export_report_fixture.make_input_contribution,
        solver=export_report_fixture.make_solver_contribution,
        output=export_report_fixture.make_output_contribution,
    )
    args = FnameAPI(fname="typed_report", suffix="toml", folder=str(tmp_path))
    ExportResults().export_report(report_model, args)
    assert (tmp_path / "typed_report.toml").exists()
