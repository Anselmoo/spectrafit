"""Focused regression tests for the shared Plotly plotting core."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest

from plotly.subplots import make_subplots
from spectrafit.api.notebook_model import PlotAPI
from spectrafit.jupyter.plotting import DataFramePlot
from spectrafit.models.plot_config import PlotConfig
from spectrafit.plotting import PlotSpectra


def _capture_show(calls: list[str]) -> object:
    def _show(_figure: go.Figure, **_kwargs: object) -> None:
        calls.append("show")

    return _show


def _noop_show(_figure: go.Figure, **_kwargs: object) -> None:
    return None


def _local_fit_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "energy": [0.0, 1.0, 2.0],
            "intensity": [1.0, 2.0, 3.0],
            "fit": [0.8, 1.9, 3.1],
            "residual": [0.2, 0.1, -0.1],
            "component_peak": [0.4, 0.8, 1.2],
        }
    )


def _global_fit_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "energy": [0.0, 1.0, 2.0],
            "intensity_1": [1.0, 2.0, 3.0],
            "fit_1": [0.8, 1.9, 3.1],
            "residual_1": [0.2, 0.1, -0.1],
            "component_peak_1": [0.4, 0.8, 1.2],
            "intensity_2": [1.5, 2.5, 3.5],
            "fit_2": [1.4, 2.4, 3.4],
            "residual_2": [0.1, 0.1, 0.1],
            "component_peak_2": [0.6, 0.9, 1.1],
        }
    )


@pytest.mark.unit
def test_plot_spectra_preserves_constructor_and_call_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import spectrafit.plotting as plotting_module

    calls: list[str] = []

    def _fake_builder(df: pd.DataFrame, **_: object) -> go.Figure:
        pd.testing.assert_frame_equal(df, _local_fit_dataframe())
        return go.Figure()

    monkeypatch.setattr(plotting_module, "build_local_fit_figure", _fake_builder)
    monkeypatch.setattr(go.Figure, "show", _capture_show(calls))

    PlotSpectra(df=_local_fit_dataframe(), config=PlotConfig())()

    assert calls == ["show"]


@pytest.mark.unit
def test_plotting_module_has_no_matplotlib_or_seaborn_imports() -> None:
    plotting_source = Path("spectrafit/plotting.py").read_text(encoding="utf-8")

    assert "matplotlib" not in plotting_source
    assert "seaborn" not in plotting_source


@pytest.mark.unit
def test_jupyter_single_fit_reuses_shared_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import spectrafit.jupyter.plotting as jupyter_plotting

    calls: list[pd.DataFrame] = []

    def _fake_builder(df: pd.DataFrame, **_: object) -> go.Figure:
        calls.append(df.copy())
        return make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)

    monkeypatch.setattr(jupyter_plotting, "build_local_fit_figure", _fake_builder)
    monkeypatch.setattr(go.Figure, "show", _noop_show)

    DataFramePlot().plot_2dataframes(
        args_plot=PlotAPI(x="energy", y=["intensity", "fit"]),
        df_1=_local_fit_dataframe(),
    )

    assert len(calls) == 1
    pd.testing.assert_frame_equal(calls[0], _local_fit_dataframe())


@pytest.mark.unit
def test_jupyter_global_fit_reuses_shared_global_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import spectrafit.jupyter.plotting as jupyter_plotting

    global_df = _global_fit_dataframe()
    local_frames = [
        (
            1,
            _local_fit_dataframe(),
        ),
        (
            2,
            _local_fit_dataframe().rename(
                columns={"component_peak": "component_peak_2"}
            ),
        ),
    ]
    iter_calls: list[pd.DataFrame] = []
    build_calls: list[pd.DataFrame] = []

    def _fake_iter(df: pd.DataFrame, **_: object) -> list[tuple[int, pd.DataFrame]]:
        iter_calls.append(df.copy())
        return local_frames

    def _fake_builder(df: pd.DataFrame, **_: object) -> go.Figure:
        build_calls.append(df.copy())
        return make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)

    monkeypatch.setattr(jupyter_plotting, "iter_global_fit_frames", _fake_iter)
    monkeypatch.setattr(jupyter_plotting, "build_local_fit_figure", _fake_builder)
    monkeypatch.setattr(go.Figure, "show", _noop_show)

    DataFramePlot().plot_global_fit(
        args_plot=PlotAPI(x="energy", y=["intensity", "fit"]),
        df=global_df,
    )

    assert len(iter_calls) == 1
    pd.testing.assert_frame_equal(iter_calls[0], global_df)
    assert len(build_calls) == 2
