"""Unit tests for the shared runtime-to-export result bridge."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from spectrafit.adapters.fit_result_json import load_fit_result
from spectrafit.core.result_bridge import build_fit_result_from_runtime
from spectrafit.core.result_bridge import write_cli_outputs
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import ComponentResult
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import FitStatistics
from spectrafit.models.results.fit_result import ParameterResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.split_frame import SplitFrame


def _split_frame() -> dict[str, object]:
    return {
        "index": [0, 1],
        "columns": ["energy", "intensity", "fit"],
        "data": [[1.0, 2.0, 1.9], [2.0, 3.0, 3.1]],
    }


def _build_fit_result() -> FitResult:
    return FitResult(
        statistics=FitStatistics(
            method="leastsq",
            nfev=42,
            ndata=2,
            nvarys=2,
            nfree=0,
            chisqr=0.12,
            redchi=0.06,
            aic=-10.0,
            bic=-9.5,
            success=True,
            message="ok",
        ),
        parameters=[
            ParameterResult(
                name="p1_amplitude",
                init_value=1.0,
                best_value=1.1,
                stderr=0.02,
            )
        ],
        fit_insights=FitInsights(
            statistics={
                "chi_square": 0.12,
                "reduced_chi_square": 0.06,
                "akaike_information": -10.0,
                "bayesian_information": -9.5,
            },
            variables={
                "p1_amplitude": VariableFitResult(
                    init_value=1.0,
                    model_value=1.05,
                    best_value=1.1,
                    stderr=0.02,
                )
            },
            computational={"success": True, "message": "ok", "nfev": 42},
        ),
        data_summary=DataSummary(
            regression_metrics=_split_frame(),
            descriptive_statistic=_split_frame(),
            linear_correlation=_split_frame(),
        ),
        confidence=ConfidenceResults(
            settings=ConfIntervalConfig(sigmas=[1.0, 2.0]),
            results={"p1_amplitude": [(0.95, 0.9), (0.99, 1.2)]},
        ),
    )


@pytest.mark.unit
def test_write_cli_outputs_creates_report_compatible_artifacts(tmp_path: Path) -> None:
    """CLI artifacts should be written from canonical typed data."""
    fit_result = _build_fit_result()
    fit_df = pd.DataFrame(
        {"energy": [1.0, 2.0], "intensity": [2.0, 3.0], "fit": [1.9, 3.1]}
    )
    outfile = tmp_path / "bridge"

    write_cli_outputs(
        fit_result=fit_result,
        fit_df=fit_df,
        outfile=str(outfile),
    )

    summary = load_fit_result(f"{outfile}_summary.json")
    assert summary.statistics.method == "leastsq"
    assert "p1_amplitude" in summary.fit_insights.variables
    assert isinstance(summary.confidence.settings, ConfIntervalConfig)
    assert summary.confidence.settings.sigmas == [1.0, 2.0]
    assert summary.data_summary.regression_metrics["columns"] == [
        "energy",
        "intensity",
        "fit",
    ]
    assert Path(f"{outfile}_fit.csv").exists()
    assert Path(f"{outfile}_correlation.csv").exists()
    assert Path(f"{outfile}_components.csv").exists()


@pytest.mark.unit
def test_build_fit_result_from_runtime_normalizes_legacy_confidence_payload() -> None:
    """Bridge should canonicalize legacy confidence payloads at the ownership boundary."""
    minimizer_result = SimpleNamespace(
        method="leastsq",
        nfev=7,
        ndata=1,
        nvarys=1,
        nfree=0,
        chisqr=0.1,
        redchi=0.1,
        aic=-1.0,
        bic=-0.9,
        success=True,
        message="ok",
        params={
            "p1_center": SimpleNamespace(
                init_value=1.0,
                value=1.1,
                stderr=0.02,
                vary=True,
                expr=None,
            )
        },
    )
    empty_summary = DataSummary()
    post_result = SimpleNamespace(
        df=pd.DataFrame({"energy": [1.0], "intensity": [2.0], "fit": [2.1]}),
        fit_insights=FitInsights(),
        regression_metrics=empty_summary.regression_metrics,
        descriptive_statistic=empty_summary.descriptive_statistic,
        linear_correlation=empty_summary.linear_correlation,
        confidence_interval={
            "settings": {
                "sigma": [1.0, 2.0],
                "trace": True,
                "prob_func": object(),
            },
            "results": {
                "p1_center": [(1, 0.95), [2, 1.05], ("bad", 1.2)],
                "p2_center": "invalid",
            },
        },
    )

    fit_result = build_fit_result_from_runtime(
        global_mode=FittingMode.STANDARD,
        minimizer_result=minimizer_result,
        post_result=post_result,  # type: ignore[arg-type]
    )

    assert isinstance(fit_result.confidence.settings, ConfIntervalConfig)
    assert fit_result.confidence.settings.sigmas == [1.0, 2.0]
    assert fit_result.confidence.results == {"p1_center": [(1.0, 0.95), (2.0, 1.05)]}


@pytest.mark.unit
def test_build_fit_result_from_runtime_prefers_typed_fit_result_frame() -> None:
    """Bridge should prefer canonical split-frame fit data over raw dataframe seams."""
    minimizer_result = SimpleNamespace(
        method="leastsq",
        nfev=7,
        ndata=1,
        nvarys=1,
        nfree=0,
        chisqr=0.1,
        redchi=0.1,
        aic=-1.0,
        bic=-0.9,
        success=True,
        message="ok",
        params={
            "p1_center": SimpleNamespace(
                init_value=1.0,
                value=1.1,
                stderr=0.02,
                vary=True,
                expr=None,
            )
        },
    )
    empty_summary = DataSummary()
    post_result = SimpleNamespace(
        df=pd.DataFrame({"energy": [99.0], "intensity": [88.0], "fit": [77.0]}),
        fit_result_data=SplitFrame(
            index=[0],
            columns=["energy", "intensity", "fit"],
            data=[[1.0, 2.0, 2.1]],
        ),
        fit_insights=FitInsights(),
        regression_metrics=empty_summary.regression_metrics,
        descriptive_statistic=empty_summary.descriptive_statistic,
        linear_correlation=empty_summary.linear_correlation,
        confidence_interval=ConfidenceResults(settings=False),
    )

    fit_result = build_fit_result_from_runtime(
        global_mode=FittingMode.STANDARD,
        minimizer_result=minimizer_result,
        post_result=post_result,  # type: ignore[arg-type]
    )

    assert fit_result.x == [1.0]
    assert fit_result.y_data == [2.0]
    assert fit_result.y_fit == [2.1]


@pytest.mark.unit
def test_build_fit_result_from_runtime_projects_component_curves() -> None:
    """Bridge should capture component curves in the canonical FitResult payload."""
    minimizer_result = SimpleNamespace(
        method="leastsq",
        nfev=7,
        ndata=2,
        nvarys=1,
        nfree=1,
        chisqr=0.1,
        redchi=0.1,
        aic=-1.0,
        bic=-0.9,
        success=True,
        message="ok",
        params={
            "p1_center": SimpleNamespace(
                init_value=1.0,
                value=1.1,
                stderr=0.02,
                vary=True,
                expr=None,
            )
        },
    )
    empty_summary = DataSummary()
    post_result = SimpleNamespace(
        df=pd.DataFrame({"energy": [99.0], "intensity": [88.0], "fit": [77.0]}),
        fit_result_data=SplitFrame(
            index=[0, 1],
            columns=["energy", "intensity", "fit", "p1"],
            data=[[1.0, 2.0, 2.1, 0.7], [2.0, 3.0, 3.1, 1.4]],
        ),
        fit_insights=FitInsights(),
        regression_metrics=empty_summary.regression_metrics,
        descriptive_statistic=empty_summary.descriptive_statistic,
        linear_correlation=empty_summary.linear_correlation,
        confidence_interval=ConfidenceResults(settings=False),
    )

    fit_result = build_fit_result_from_runtime(
        global_mode=FittingMode.STANDARD,
        minimizer_result=minimizer_result,
        post_result=post_result,  # type: ignore[arg-type]
        input_snapshot={"components": [{"id": "p1", "model": "gaussian"}]},
    )

    assert fit_result.components == [
        ComponentResult(id="p1", model="gaussian", curve=[0.7, 1.4])
    ]
