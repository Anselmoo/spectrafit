"""Test of the jupyter plugin."""

import sys

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from typing import Dict
from typing import List

import pandas as pd
import pytest

from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.notebook_model import PlotAPI
from spectrafit.api.report_model import InputAPI
from spectrafit.api.report_model import OutputAPI
from spectrafit.api.report_model import SolverAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.plugins.notebook import DataFrameDisplay
from spectrafit.plugins.notebook import DataFramePlot
from spectrafit.plugins.notebook import ExportReport
from spectrafit.plugins.notebook import ExportResults


@pytest.fixture(name="dataframe")
def dataframe_fixture() -> pd.DataFrame:
    """Create a DataFrameDisplay object."""
    return pd.read_csv(
        "https://raw.githubusercontent.com/Anselmoo/spectrafit/main/Examples/data.csv"
    )


@pytest.fixture(name="dataframe_2")
def dataframe_2_fixture() -> pd.DataFrame:
    """Create a DataFrameDisplay object."""
    return pd.read_csv(
        "https://raw.githubusercontent.com/Anselmoo/"
        "spectrafit/main/Examples/example_1_fit.csv"
    )


@pytest.fixture(name="initial_model")
def initial_model_fixture() -> List[Dict[str, Dict[str, Dict[str, Any]]]]:
    """Create a DataFrameDisplay object."""
    return [
        {
            "pseudovoigt": {
                "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
                "center": {"max": 2, "min": -2, "vary": True, "value": 0},
                "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
                "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
            }
        },
        {
            "gaussian": {
                "amplitude": {"max": 1.2, "min": 0.5, "vary": True, "value": 0.3},
                "center": {"max": 4, "min": 2, "vary": True, "value": 3.5},
                "fwhmg": {"max": 0.1, "min": 0.02, "vary": False, "value": 1.3},
            }
        },
    ]


@pytest.fixture(name="args_out")
def args_out_fixture() -> Dict[str, Any]:
    """Create a DataFrameDisplay object."""
    return {
        "global_": False,
        "fit_insights": {
            "correlations": {"a": {"a": 1, "b": 2}, "b": {"a": 2, "b": 3}},
            "configurations": {"n_components": 2, "n_iter": 1000},
            "covariance_matrix": {"a": {"a": 1, "b": 2}, "b": {"a": 2, "b": 3}},
            "statistics": {"aic": True, "bic": True, "aicc": True},
            "variables": {"a": {"value": 1, "std": 2}, "b": {"value": 3, "std": 4}},
            "errorbars": {
                "error_a": {"value": 1, "std": 2},
                "error_b": {"value": 3, "std": 4},
            },
        },
        "descriptive_statistic": pd.DataFrame({"mean": [1, 2], "std": [1, 2]}).to_dict(
            orient="list"
        ),
        "linear_correlation": pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        .corr()
        .to_dict(orient="list"),
        "regression_metrics": {"MSE": [1], "RMSE": [1], "R2": [1]},
        "conf_interval": {"alpha": 0.05, "max_nfev": 100000},
        "confidence_interval": {"val_1": 2, "val_2": 3},
    }


@pytest.fixture(name="export_report")
def export_report_fixture(
    initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
    args_out: Dict[str, Any],
    dataframe: pd.DataFrame,
    dataframe_2: pd.DataFrame,
) -> Dict[Any, Any]:
    """Create a ExportReport object."""
    return {
        "description": DescriptionAPI(),
        "initial_model": initial_model,
        "pre_processing": DataPreProcessingAPI(),
        "fname": FnameAPI(fname="test", suffix="out"),
        "args_out": args_out,
        "df_org": dataframe,
        "df_fit": dataframe_2,
        "df_pre": dataframe,
    }


def test_dataframe_display(dataframe: pd.DataFrame) -> None:
    """Test the DataFrameDisplay class."""
    DataFrameDisplay().df_display(df=dataframe, mode="regular")
    DataFrameDisplay().df_display(df=dataframe, mode="markdown")
    DataFrameDisplay().df_display(df=dataframe, mode="interactive")
    DataFrameDisplay().df_display(df=dataframe, mode="dtale")

    with pytest.raises(ValueError) as excinfo:
        DataFrameDisplay().df_display(df=dataframe, mode="wrong")

    assert "Invalid mode: wrong." in str(excinfo.value)


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
class TestDataFramePlot:
    """Test the DataFramePlot class."""

    def test_dataframe_plot_1(self, dataframe: pd.DataFrame) -> None:
        """Test single plot with one y-column."""
        dp = DataFramePlot(args_plot=PlotAPI(x="Energy", y="Noisy", title="Test"))
        dp.plot_dataframe(dataframe)

    def test_dataframe_plot_2(self, dataframe: pd.DataFrame) -> None:
        """Test single plot with two y-column."""
        dp = DataFramePlot(
            args_plot=PlotAPI(x="Energy", y=["Intensity", "Noisy"], title="Test")
        )
        dp.plot_dataframe(dataframe)

    def test_dataframe_plot_3(self, dataframe_2: pd.DataFrame) -> None:
        """Test douple plot."""
        dp = DataFramePlot(args_plot=PlotAPI(x="energy", y="intensity", title="Test"))
        dp.plot_2dataframes(df_1=dataframe_2, df_2=dataframe_2)

    def test_dataframe_plot_4(self, dataframe_2: pd.DataFrame) -> None:
        """Test double plot with residual."""
        dp = DataFramePlot(args_plot=PlotAPI(x="energy", y="intensity", title="Test"))
        dp.plot_2dataframes(df_1=dataframe_2)


def test_dataframe_display_all(dataframe: pd.DataFrame) -> None:
    """Test the DataFrameDisplay class."""
    DataFrameDisplay().df_display(df=dataframe, mode="regular")
    DataFrameDisplay().df_display(df=dataframe, mode="markdown")
    DataFrameDisplay().df_display(df=dataframe, mode="interactive")
    DataFrameDisplay().df_display(df=dataframe, mode="dtale")

    with pytest.raises(ValueError) as excinfo:
        DataFrameDisplay().df_display(df=dataframe, mode="wrong")

    assert "Invalid mode: wrong." in str(excinfo.value)


class TestExportResults:
    """Test of the Export Results class."""

    def test_export_df(self, dataframe: pd.DataFrame) -> None:
        """Test the export function."""
        with TemporaryDirectory() as tmpdir:
            fname = "test"
            prefix = "test"
            suffix = "csv"
            folder = str(tmpdir)
            ExportResults().export_df(
                df=dataframe,
                args=FnameAPI(fname=fname, prefix=prefix, suffix=suffix, folder=folder),
            )
            assert Path(folder).joinpath(f"{prefix}_{fname}.{suffix}").exists()

    def test_export_report(self, dataframe: pd.DataFrame) -> None:
        """Test the export function."""
        with TemporaryDirectory() as tmpdir:
            fname = "test"
            prefix = "test"
            suffix = "lock"
            folder = str(tmpdir)
            ExportResults().export_report(
                report=dataframe.to_dict(orient="list"),
                args=FnameAPI(fname=fname, prefix=prefix, suffix=suffix, folder=folder),
            )
            assert Path(folder).joinpath(f"{prefix}_{fname}.{suffix}").exists()

    def test_static_fname(self) -> None:
        """Test the static function of generating PathPosixs."""
        assert isinstance(ExportResults.fname2Path(fname="test", suffix="csv"), Path)
        assert isinstance(
            ExportResults.fname2Path(
                fname="test", suffix="csv", folder="tmp", prefix="prefix"
            ),
            Path,
        )


class TestExportReport:
    """Test the ExportReport class."""

    def test_input(self, export_report: Dict[str, Any]) -> None:
        """Test the input function."""
        assert isinstance(
            ExportReport(**export_report).make_input_contribution, InputAPI
        )

    def test_solver(self, export_report: Dict[str, Any]) -> None:
        """Test the solver function."""
        assert isinstance(
            ExportReport(**export_report).make_solver_contribution, SolverAPI
        )

    def test_output(self, export_report: Dict[str, Any]) -> None:
        """Test the output function."""
        assert isinstance(
            ExportReport(**export_report).make_output_contribution, OutputAPI
        )
