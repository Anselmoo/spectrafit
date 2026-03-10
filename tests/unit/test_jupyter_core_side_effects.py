"""Unit tests for explicit SpectraFitNotebook side-effect methods and property shims."""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest
import spectrafit.jupyter.core as jupyter_core

from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.models.preprocess_result import PreprocessResult


def _notebook_stub() -> SpectraFitNotebook:
    """Create a lightweight SpectraFitNotebook instance without running ``__init__``."""
    return object.__new__(SpectraFitNotebook)


class TestSideEffectMethods:
    """Method-first API for side effects."""

    @pytest.mark.unit
    def test_preprocess_df_updates_dataframe_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        notebook = _notebook_stub()
        notebook.df = pd.DataFrame({"x": [0.0, 1.0], "y": [2.0, 3.0]})
        notebook.args_pre = DataPreProcessingAPI(
            column=["x", "y"],
            shift=0.5,
            smooth=0,
            oversampling=False,
            energy_start=None,
            energy_stop=None,
        )

        processed_df = pd.DataFrame({"x": [0.5, 1.5], "y": [2.0, 3.0]})
        captured: dict[str, object] = {}

        class FakePreProcessing:
            def __init__(self, df: pd.DataFrame, config: object) -> None:
                captured["df"] = df
                captured["config"] = config

            def __call__(self) -> PreprocessResult:
                return PreprocessResult(
                    df=processed_df,
                    data_statistic={"data": [[1.0]], "index": [0], "columns": ["rows"]},
                )

        monkeypatch.setattr(jupyter_core, "PreProcessing", FakePreProcessing)

        notebook.preprocess_df()

        pd.testing.assert_frame_equal(notebook.df, processed_df)
        pd.testing.assert_frame_equal(notebook.df_pre, processed_df)
        assert notebook.pre_statistic["columns"] == ["rows"]
        assert captured["df"] is not None
        assert captured["config"] is not None

    @pytest.mark.unit
    def test_export_active_df_calls_export_with_act_prefix(self) -> None:
        notebook = _notebook_stub()
        notebook.df = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.export_args_df = FnameAPI(fname="results", suffix="csv")
        notebook.export_df = MagicMock()

        notebook.export_active_df()

        assert notebook.export_args_df.prefix == "act"
        notebook.export_df.assert_called_once_with(df=notebook.df, args=notebook.export_args_df)

    @pytest.mark.unit
    def test_plot_original_calls_plot_dataframe(self) -> None:
        notebook = _notebook_stub()
        notebook.df_org = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.args_plot = MagicMock()
        notebook.plot_dataframe = MagicMock()

        notebook.plot_original()

        notebook.plot_dataframe.assert_called_once_with(
            args_plot=notebook.args_plot,
            df=notebook.df_org,
        )

    @pytest.mark.unit
    def test_generate_fit_report_calls_export_report(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        notebook = _notebook_stub()
        notebook.args_desc = MagicMock()
        notebook.initial_model = []
        notebook.args_pre = DataPreProcessingAPI(column=["x", "y"])
        notebook.settings_solver_models = MagicMock()
        notebook.export_args_out = FnameAPI(fname="report", suffix="lock")
        notebook.__dict__["_solver_results"] = MagicMock()
        notebook.df_org = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.df_pre = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.df_fit = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.export_report = MagicMock()

        class FakeExportReport:
            def __init__(self, **kwargs: object) -> None:
                self.kwargs = kwargs

            def __call__(self) -> dict[str, bool]:
                return {"ok": True}

        monkeypatch.setattr(jupyter_core, "ExportReport", FakeExportReport)

        notebook.generate_fit_report()

        notebook.export_report.assert_called_once_with(
            report={"ok": True},
            args=notebook.export_args_out,
        )


class TestLegacyPropertyShims:
    """Compatibility properties delegate to method-first APIs."""

    @pytest.mark.unit
    def test_pre_process_property_calls_preprocess_df(self) -> None:
        notebook = _notebook_stub()
        notebook.preprocess_df = MagicMock()

        notebook.pre_process

        notebook.preprocess_df.assert_called_once_with()

    @pytest.mark.unit
    def test_export_df_act_property_calls_export_active_df(self) -> None:
        notebook = _notebook_stub()
        notebook.export_active_df = MagicMock()

        notebook.export_df_act

        notebook.export_active_df.assert_called_once_with()

    @pytest.mark.unit
    def test_plot_original_df_property_calls_plot_original(self) -> None:
        notebook = _notebook_stub()
        notebook.plot_original = MagicMock()

        notebook.plot_original_df

        notebook.plot_original.assert_called_once_with()

    @pytest.mark.unit
    def test_generate_report_property_calls_generate_fit_report(self) -> None:
        notebook = _notebook_stub()
        notebook.generate_fit_report = MagicMock()

        notebook.generate_report

        notebook.generate_fit_report.assert_called_once_with()
