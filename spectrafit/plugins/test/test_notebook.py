"""Test of the jupyter plugin."""

import pandas as pd
import pytest

from spectrafit.api.notebook_model import PlotAPI
from spectrafit.plugins.notebook import DataFrameDisplay
from spectrafit.plugins.notebook import DataFramePlot


@pytest.fixture
def dataframe() -> pd.DataFrame:
    """Create a DataFrameDisplay object."""
    return pd.read_csv(
        "https://raw.githubusercontent.com/Anselmoo/spectrafit/main/Examples/data.csv"
    )


@pytest.fixture
def dataframe_2() -> pd.DataFrame:
    """Create a DataFrameDisplay object."""
    return pd.read_csv(
        "https://raw.githubusercontent.com/Anselmoo/"
        "spectrafit/main/Examples/example_1_fit.csv"
    )


def test_dataframe_display(dataframe: pd.DataFrame) -> None:
    """Test the DataFrameDisplay class."""
    DataFrameDisplay().df_display(df=dataframe, mode="regular")
    DataFrameDisplay().df_display(df=dataframe, mode="markdown")
    DataFrameDisplay().df_display(df=dataframe, mode="interactive")
    DataFrameDisplay().df_display(df=dataframe, mode="dtale")

    with pytest.raises(ValueError) as excinfo:
        DataFrameDisplay().df_display(df=dataframe, mode="wrong")

    assert "Invalid mode: wrong." in str(excinfo.value)


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
