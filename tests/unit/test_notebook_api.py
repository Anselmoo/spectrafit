"""Unit tests for the compact ``spectrafit.notebook`` facade."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import spectrafit.notebook as sf
import spectrafit.notebook._result as result_module

from pandas.testing import assert_frame_equal


if TYPE_CHECKING:
    import pandas as pd


@pytest.mark.unit
def test_component_helpers_build_canonical_components() -> None:
    component = sf.peak(
        "gaussian",
        id="main",
        amplitude=(1.0, 0.0, 2.0),
        center=0.0,
        fwhmg=sf.fixed(0.4),
    )
    tied = sf.peak(
        "gaussian",
        id="satellite",
        amplitude=sf.tie("main.amplitude"),
        center=(0.2, -1.0, 1.0),
        fwhmg=(0.5, 0.1, 1.0),
    )

    assert component.model == "gaussian"
    assert component.parameters["amplitude"].min == 0.0
    assert component.parameters["center"].vary is True
    assert component.parameters["fwhmg"].vary is False
    assert tied.parameters["amplitude"].expr == "main_amplitude"


@pytest.mark.unit
def test_read_path_preserves_notebook_metadata(tmp_path: Path) -> None:
    data_path = tmp_path / "data.csv"
    data_path.write_text("energy,intensity\n0.0,1.0\n1.0,0.5\n", encoding="utf-8")

    dataframe = sf.read(data_path)

    assert list(dataframe.columns) == ["energy", "intensity"]
    assert dataframe.attrs["spectrafit.notebook"]["path"] == str(data_path.resolve())
    assert dataframe.attrs["spectrafit.notebook"]["x"] == "energy"
    assert dataframe.attrs["spectrafit.notebook"]["y"] == "intensity"


@pytest.mark.unit
def test_read_rejects_unknown_columns(sample_dataframe: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Unknown x column 'missing'"):
        sf.read(sample_dataframe, x="missing", y="intensity")

    with pytest.raises(ValueError, match="Unknown y column 'missing'"):
        sf.read(sample_dataframe, x="energy", y="missing")


@pytest.mark.unit
def test_fit_path_builds_path_backed_canonical_config(tmp_path: Path) -> None:
    data_path = tmp_path / "data.csv"
    data_path.write_text(
        "energy,intensity\n-2.0,0.0\n-1.0,0.1\n0.0,1.0\n1.0,0.1\n2.0,0.0\n",
        encoding="utf-8",
    )

    session = sf.fit(
        data_path,
        peaks=[
            sf.peak(
                "gaussian",
                id="peak1",
                amplitude=(1.0, 0.0, 2.0),
                center=0.0,
                fwhmg=(0.5, 0.1, 1.0),
            )
        ],
        background=sf.background("constant", id="baseline", c=sf.fixed(0.0)),
        x="energy",
        y="intensity",
        name="path-backed",
    )

    assert session.config.data is not None
    assert session.config.data.infile == data_path.resolve()
    assert session.config.x_column == "energy"
    assert session.config.y_column == "intensity"
    assert session.source_dataframe.attrs["spectrafit.notebook"]["path"] == str(
        data_path.resolve()
    )


@pytest.mark.unit
def test_fit_session_runs_and_exports(sample_dataframe: pd.DataFrame, tmp_path: Path) -> None:
    dataframe = sf.read(sample_dataframe, x="energy", y="intensity")
    session = sf.fit(
        dataframe,
        peaks=[
            sf.peak(
                "gaussian",
                id="peak1",
                amplitude=(1.0, 0.0, 2.0),
                center=(0.0, -1.0, 1.0),
                fwhmg=(1.0, 0.1, 2.0),
            )
        ],
        name="demo",
    )

    assert not session.metrics.empty
    assert not session.peaks.empty
    assert not session.parameters.empty

    artifacts = session.save(tmp_path)

    assert all(path.exists() for path in artifacts)
    assert (tmp_path / "demo.lock").exists()

    config_path = session.to_toml(tmp_path / "config.toml", force=True)
    assert config_path.exists()


@pytest.mark.unit
def test_fit_session_exposes_summary_tables_and_escape_hatches(
    sample_dataframe: pd.DataFrame,
) -> None:
    session = sf.fit(
        sf.read(sample_dataframe, x="energy", y="intensity"),
        peaks=[
            sf.peak(
                "gaussian",
                id="peak1",
                amplitude=(1.0, 0.0, 2.0),
                center=(0.0, -1.0, 1.0),
                fwhmg=(1.0, 0.1, 2.0),
            )
        ],
        name="demo",
    )

    assert session.summary_frame().to_dict("records") == [session.summary]
    assert {
        "name",
        "init_value",
        "best_value",
        "vary",
    }.issubset(session.parameters.columns)
    assert session.fit_result is session.pipeline_result.fit_result
    assert_frame_equal(
        session.metrics,
        session.solver_results.current_metric,
    )
    assert_frame_equal(
        session.peaks,
        session.solver_results.peaks_projection.to_dataframe(),
    )

    escaped_config = session.config
    escaped_config.column.x = "shifted"
    assert session.config.column.x == "energy"
    assert session.to_config().column.x == "energy"


@pytest.mark.unit
def test_fit_session_plot_uses_pipeline_plot_config(
    sample_dataframe: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = sf.fit(
        sf.read(sample_dataframe, x="energy", y="intensity"),
        peaks=[
            sf.peak(
                "gaussian",
                id="peak1",
                amplitude=(1.0, 0.0, 2.0),
                center=(0.0, -1.0, 1.0),
                fwhmg=(1.0, 0.1, 2.0),
            )
        ],
        name="demo",
    )
    captured: dict[str, object] = {}

    class DummyFigure:
        def show(self) -> None:
            captured["shown"] = True

    dummy_figure = DummyFigure()

    class DummyPlotSpectra:
        def __init__(self, *, df: pd.DataFrame, config: object) -> None:
            captured["df"] = df
            captured["config"] = config

        def figure(self) -> DummyFigure:
            return dummy_figure

    monkeypatch.setattr(result_module, "PlotSpectra", DummyPlotSpectra)

    figure = session.plot()

    assert figure is dummy_figure
    assert captured["shown"] is True
    assert_frame_equal(captured["df"], session.pipeline_result.df)
    assert captured["config"].noplot is True
    assert (
        captured["config"].global_fitting
        == session.pipeline_result.config.context.mode
    )
    assert (
        captured["config"].data_statistic
        == session.pipeline_result.data_statistic
    )
