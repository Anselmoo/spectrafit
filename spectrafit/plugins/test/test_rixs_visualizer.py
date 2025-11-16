"""Test of the RIXS Visualizer."""

from __future__ import annotations

import json
import sys

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import numpy as np
import plotly.graph_objects as go
import pytest
import tomli_w

from spectrafit.plugins.rixs_visualizer import RIXSApp
from spectrafit.plugins.rixs_visualizer import RIXSFigure
from spectrafit.plugins.rixs_visualizer import RIXSVisualizer


if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9 or higher")
@pytest.fixture(scope="module", autouse=True, name="test_data")
def fixture_test_data() -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Test data."""
    space_x_y = np.arange(0, 10, 0.1, dtype=np.float64)
    space_x, space_y = np.meshgrid(space_x_y, space_x_y)
    return space_x_y, space_x_y, np.sin(space_x) * np.cos(space_y)


# Write test  RIXSFigure
@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9 or higher")
class TestRixsFigure:
    """Test of the RIXS Figure."""

    def test__init__(self, test_data: NDArray[np.float64]) -> None:
        """Test the initialization."""
        _rixs_figure = RIXSFigure(
            incident_energy=test_data[0],
            emission_energy=test_data[1],
            rixs_map=test_data[2],
        )
        assert _rixs_figure.incident_energy.shape == (100,)
        assert _rixs_figure.emission_energy.shape == (100,)
        assert _rixs_figure.rixs_map.shape == (100, 100)

    def test_create_rixs_figure(self, test_data: NDArray[np.float64]) -> None:
        """Test the creation of RIXS figure."""
        _rixs_figure = RIXSFigure(
            incident_energy=test_data[0],
            emission_energy=test_data[1],
            rixs_map=test_data[2],
        )
        fig_rixs = _rixs_figure.create_rixs()
        fig_xes = _rixs_figure.create_xes(test_data[0], test_data[1])
        fig_xas = _rixs_figure.create_xas(test_data[0], test_data[1])

        assert _rixs_figure.rixs_map.shape == (100, 100)
        assert isinstance(fig_rixs, go.Figure)
        assert isinstance(fig_xes, go.Figure)
        assert isinstance(fig_xas, go.Figure)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9 or higher")
class TestRIXSApp:
    """Test of the App."""

    def test__init__(self, test_data: NDArray[np.float64]) -> None:
        """Test the initialization."""
        _app = RIXSApp(
            incident_energy=test_data[0],
            emission_energy=test_data[1],
            rixs_map=test_data[2],
        )
        assert _app.incident_energy.shape == (100,)
        assert _app.emission_energy.shape == (100,)
        assert _app.rixs_map.shape == (100, 100)

    # Create a pytest for load data

    @pytest.mark.parametrize("file_format", ["npy", "npz", "json", "toml", "lock"])
    def test_load_data(
        self,
        file_format: str,
        tmp_path: Path,
        test_data: tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]],
    ) -> None:
        """Test the loading of data."""
        incident_energy, emission_energy, rixs_map = test_data
        arrays = {
            "incident_energy": incident_energy,
            "emission_energy": emission_energy,
            "rixs_map": rixs_map,
        }
        outfile = tmp_path / f"test.{file_format}"

        if file_format == "npy":
            # Save dict as pickled object in .npy file; cast to "Any" (string)
            # to satisfy typing linter and numpy type stubs.
            np.save(str(outfile), cast("Any", arrays), allow_pickle=True)
        elif file_format == "npz":
            np.savez(
                str(outfile),
                incident_energy=incident_energy,
                emission_energy=emission_energy,
                rixs_map=rixs_map,
            )
        else:
            serializable = {key: value.tolist() for key, value in arrays.items()}
            if file_format == "json":
                with outfile.open("w", encoding="utf-8") as f:
                    json.dump(serializable, f)
            elif file_format in {"toml", "lock"}:
                with outfile.open("wb") as f:
                    tomli_w.dump(serializable, f)
            else:
                pytest.fail(f"Unsupported test format: {file_format}")

        _model = RIXSVisualizer().load_data(infile=outfile)
        assert _model.incident_energy.shape == (100,)
        assert _model.emission_energy.shape == (100,)
        assert _model.rixs_map.shape == (100, 100)

    def test_load_data_error(self, tmp_path: Path) -> None:
        """Test the loading of data."""
        with pytest.raises(ValueError, match=r"File type") as excinfo:
            RIXSVisualizer().load_data(infile=tmp_path / "test.txt")

        assert "File type" in str(excinfo.value)

    # test cmd line
    def test_cmd_line(self, script_runner: Any) -> None:
        """Test the command line."""
        ret = script_runner.run(
            "spectrafit-rixs-visualizer",
            "--help",
            expect_error=True,
        )
        assert ret.success
