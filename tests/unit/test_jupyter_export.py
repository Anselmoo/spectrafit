"""Unit tests for Jupyter export report typing boundaries."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.jupyter.export import ExportReport
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import SolverConfig
from spectrafit.models.split_frame import SplitFrame
from spectrafit.reporting.service import CanonicalReportSchema
from spectrafit.reporting.service import project_solver_report
from spectrafit.utilities.transformer import list2components


def _build_solver_results() -> SolverResults:
    fit_result = FitResult(
        fit_insights=FitInsights(
            configurations=FitConfigurations(
                method="leastsq", max_nfev=120, nan_policy="raise"
            ),
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
            regression_metrics=SplitFrame(data=[[0.99]], index=[0], columns=["r2"]),
            descriptive_statistic=SplitFrame(data=[[1.0]], index=[0], columns=["mean"]),
            linear_correlation=SplitFrame(
                data=[[0.95]], index=[0], columns=["pearson"]
            ),
        ),
        confidence=ConfidenceResults(
            settings=ConfIntervalConfig(trace=True, maxiter=100, sigmas=[1.0, 2.0]),
        ),
    )
    return SolverResults(result=fit_result)


def _build_solver_results_with_snapshot() -> SolverResults:
    snapshot_config = UnifiedFittingConfig.from_dict(
        {
            "components": [
                {
                    "id": "snapshot_peak",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 4.0, "vary": True},
                        "center": {"value": 1.5, "vary": True},
                        "fwhmg": {"value": 0.7, "vary": True},
                    },
                }
            ],
            "column": {"x": "binding_energy", "y": "counts"},
            "context": {"mode": "global", "n_datasets": 2},
            "minimizer": {"nan_policy": "omit"},
            "optimizer": {"method": "least_squares", "max_nfev": 321},
            "preprocessing": {
                "energy_start": 280.0,
                "energy_stop": 295.0,
                "shift": 0.25,
                "smooth": 4,
                "oversampling": True,
            },
        }
    )
    fit_result = _build_solver_results().result.model_copy(
        update={
            "input_snapshot": snapshot_config.model_dump(
                mode="python", exclude_none=True
            )
        }
    )
    solver = SolverResults(result=fit_result)
    solver.__dict__["_snapshot_config"] = snapshot_config
    return solver


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
        settings_solver_models=SolverConfig(),
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
def test_export_results_writes_report_document(
    tmp_path: Path,
    export_report_fixture: ExportReport,
) -> None:
    """``ExportResults.export_report`` writes the plain report document."""
    args = FnameAPI(fname="typed_report", suffix="toml", folder=str(tmp_path))
    ExportResults().export_report(export_report_fixture(), args)
    assert (tmp_path / "typed_report.toml").exists()


@pytest.mark.unit
def test_export_report_avoids_result_roundtrip_helpers() -> None:
    """ExportReport should not rebuild deleted report DTO models."""
    import inspect

    import spectrafit.jupyter.export as export_module

    source = inspect.getsource(export_module.ExportReport)
    assert "ReportAPI" not in source
    assert "SolverAPI" not in source
    assert "InputAPI" not in source
    assert "OutputAPI" not in source


@pytest.mark.unit
def test_export_report_builds_solver_contribution_from_fit_result(
    export_report_fixture: ExportReport,
) -> None:
    """ExportReport should delegate solver payload projection from canonical FitResult."""
    solver = export_report_fixture.make_solver_contribution
    assert isinstance(export_report_fixture.canonical_report, CanonicalReportSchema)
    assert solver == project_solver_report(_build_solver_results().result)
    assert solver == export_report_fixture.canonical_report.solver
    assert solver.goodness_of_fit == {"chi_square": pytest.approx(0.1)}
    assert solver.variables["p1_amplitude"].best_value == pytest.approx(1.1)
    assert solver.computational.nfev == 42


@pytest.mark.unit
def test_export_report_preserves_initial_model_boundary_shape(
    export_report_fixture: ExportReport,
) -> None:
    """ExportReport should keep typed components until the final export boundary."""
    report_input = export_report_fixture.make_input_contribution
    assert report_input["initial_model"] == list2components(
        [
            {
                "gaussian": {
                    "amplitude": {
                        "value": 1.0,
                        "vary": True,
                        "min": 0.0,
                        "max": 2.0,
                    },
                    "center": {
                        "value": 0.0,
                        "vary": True,
                        "min": -1.0,
                        "max": 1.0,
                    },
                }
            }
        ]
    )
    assert isinstance(report_input["method"]["configurations"], FitConfigurations)


@pytest.mark.unit
def test_export_report_accepts_typed_initial_components() -> None:
    components = list2components(
        [
            {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True},
                    "center": {"value": 0.0, "vary": True},
                }
            }
        ]
    )
    exporter = ExportReport(
        description=DescriptionAPI(),
        initial_model=components,
        pre_processing=DataPreProcessingAPI(),
        settings_solver_models=SolverConfig(),
        fname=FnameAPI(fname="report", suffix="lock"),
        solver=_build_solver_results(),
        df_org=pd.DataFrame({"energy": [1.0], "data": [3.0]}),
        df_fit=pd.DataFrame({"energy": [1.0], "best_fit": [3.1]}),
    )

    assert exporter.make_input_contribution["initial_model"] == components
    assert exporter()["input"]["initial_model"] == [
        {
            "gaussian": {
                "amplitude": {"value": 1.0, "vary": True},
                "center": {"value": 0.0, "vary": True},
            }
        }
    ]


@pytest.mark.unit
def test_export_report_accepts_canonical_preprocessing_and_serializes_compat_boundary() -> (
    None
):
    exporter = ExportReport(
        description=DescriptionAPI(),
        initial_model=[],
        pre_processing=PreprocessingConfig(
            energy_start=280.0,
            energy_stop=295.0,
            shift=0.25,
            smooth=4,
            oversampling=True,
        ),
        column=["energy", "intensity"],
        settings_solver_models=SolverConfig(),
        fname=FnameAPI(fname="report", suffix="lock"),
        solver=_build_solver_results(),
        df_org=pd.DataFrame({"energy": [1.0, 2.0], "data": [3.0, 4.0]}),
        df_fit=pd.DataFrame({"energy": [1.0, 2.0], "best_fit": [3.1, 3.9]}),
    )

    assert exporter.make_input_contribution["pre_processing"] == DataPreProcessingAPI(
        column=["energy", "intensity"],
        energy_start=280.0,
        energy_stop=295.0,
        shift=0.25,
        smooth=4,
        oversampling=True,
    )


@pytest.mark.unit
def test_export_report_prefers_fit_result_snapshot_for_input_ownership() -> None:
    exporter = ExportReport(
        description=DescriptionAPI(),
        initial_model=[
            {
                "lorentzian": {
                    "amplitude": {"value": 9.0, "vary": True},
                    "center": {"value": 8.0, "vary": True},
                }
            }
        ],
        pre_processing=DataPreProcessingAPI(
            column=["wrong_x", "wrong_y"],
            energy_start=1.0,
            shift=9.0,
        ),
        settings_solver_models=SolverConfig(
            minimizer={"nan_policy": "raise"},
            optimizer={"method": "nelder", "max_nfev": 9},
        ),
        fname=FnameAPI(fname="report", suffix="lock"),
        solver=_build_solver_results_with_snapshot(),
        df_org=pd.DataFrame({"binding_energy": [1.0], "counts": [3.0]}),
        df_fit=pd.DataFrame({"binding_energy": [1.0], "best_fit": [3.1]}),
        column=["shadow_x", "shadow_y"],
    )

    report_input = exporter.make_input_contribution
    expected_snapshot = _build_solver_results_with_snapshot().__dict__[
        "_snapshot_config"
    ]

    assert report_input["initial_model"] == expected_snapshot.components
    assert report_input["pre_processing"] == DataPreProcessingAPI(
        column=["binding_energy", "counts"],
        energy_start=280.0,
        energy_stop=295.0,
        shift=0.25,
        smooth=4,
        oversampling=True,
    )
    assert report_input["method"]["global_fitting"] == "standard"
    assert report_input["method"]["settings_solver_models"] == SolverConfig(
        minimizer={"nan_policy": "omit"},
        optimizer={"method": "least_squares", "max_nfev": 321},
    )


@pytest.mark.unit
def test_export_report_snapshots_compat_preprocessing_at_boundary() -> None:
    compat_preprocessing = DataPreProcessingAPI(
        column=["energy", "intensity"],
        energy_start=280.0,
        shift=0.25,
        smooth=2,
    )
    exporter = ExportReport(
        description=DescriptionAPI(),
        initial_model=[],
        pre_processing=compat_preprocessing,
        settings_solver_models=SolverConfig(),
        fname=FnameAPI(fname="report", suffix="lock"),
        solver=_build_solver_results(),
        df_org=pd.DataFrame({"energy": [1.0, 2.0], "data": [3.0, 4.0]}),
        df_fit=pd.DataFrame({"energy": [1.0, 2.0], "best_fit": [3.1, 3.9]}),
    )

    compat_preprocessing.shift = 9.0
    compat_preprocessing.column = ["mutated", "signal"]

    expected = DataPreProcessingAPI(
        column=["energy", "intensity"],
        energy_start=280.0,
        shift=0.25,
        smooth=2,
    )
    assert exporter.pre_processing == expected
    assert exporter.make_input_contribution["pre_processing"] == expected


@pytest.mark.unit
def test_data_preprocessing_api_projects_canonical_preprocessing_config() -> None:
    canonical = PreprocessingConfig(
        energy_start=280.0,
        energy_stop=295.0,
        shift=0.25,
        smooth=4,
        oversampling=True,
    )

    boundary = DataPreProcessingAPI.from_preprocessing_config(
        canonical,
        column=["energy", "intensity"],
    )

    assert boundary.to_preprocessing_config() == canonical
    assert boundary.column == ["energy", "intensity"]
