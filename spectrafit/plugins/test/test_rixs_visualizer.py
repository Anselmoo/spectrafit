"""Test of the RIXS Visualizer."""


from pathlib import Path
from typing import Any
from typing import Tuple

import numpy as np
import plotly.graph_objects as go
import pytest

from numpy.typing import NDArray
from spectrafit.plugins.rixs_converter import RIXSConverter
from spectrafit.plugins.rixs_visualizer import RIXSApp
from spectrafit.plugins.rixs_visualizer import RIXSFigure
from spectrafit.plugins.rixs_visualizer import RIXSVisualizer


@pytest.fixture(scope="module", autouse=True, name="test_data")
def fixture_test_data() -> (
    Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]
):
    """Test data."""
    space_x_y = np.arange(0, 10, 0.1)
    space_x, space_y = np.meshgrid(space_x_y, space_x_y)
    return space_x_y, space_x_y, np.sin(space_x) * np.cos(space_y)


# Write test  RIXSFigure


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
        test_data: Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]],
    ) -> None:
        """Test the loading of data."""
        data = {
            "incident_energy": test_data[0],
            "emission_energy": test_data[1],
            "rixs_map": test_data[2],
        }

        RIXSConverter().save(
            data=data,
            fname=tmp_path / f"test.{file_format}",
            export_format=file_format,
        )

        _model = RIXSVisualizer().load_data(infile=tmp_path / f"test.{file_format}")
        assert _model.incident_energy.shape == (100,)
        assert _model.emission_energy.shape == (100,)
        assert _model.rixs_map.shape == (100, 100)

    def test_load_data_error(self, tmp_path: Path) -> None:
        """Test the loading of data."""
        with pytest.raises(ValueError) as excinfo:
            RIXSVisualizer().load_data(infile=tmp_path / "test.txt")

        assert "File type" in str(excinfo.value)

    # test cmd line
    def test_cmd_line(self, script_runner: Any) -> None:
        """Test the command line."""
        ret = script_runner.run(
            "spectrafit-rixs-visualizer", "--help", expect_error=True
        )
        assert ret.success
