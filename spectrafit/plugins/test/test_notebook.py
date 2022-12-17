"""Test of the jupyter plugin."""

import sys

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from unittest import mock

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
from spectrafit.plugins.notebook import SpectraFitNotebook


__plotly_io_show__ = "plotly.io.show"


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


@pytest.fixture(name="x_column")
def x_column_fixture(dataframe: pd.DataFrame) -> str:
    """Create a x_column object."""
    return str(dataframe.columns[1])


@pytest.fixture(name="y_column")
def y_column_fixture(dataframe: pd.DataFrame) -> str:
    """Create a y_column object."""
    return str(dataframe.columns[2])


@pytest.fixture(name="y_columns")
def y_columns_fixture(dataframe: pd.DataFrame) -> List[str]:
    """Create a y_column object."""
    return [str(dataframe.columns[2]), str(dataframe.columns[3])]


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


@pytest.fixture(name="class_spectrafit")
def class_spectrafit_fixture(
    dataframe_2: pd.DataFrame,
    initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
    tmp_path: Path,
) -> Dict[Any, Any]:
    """Create a SpectraFitNotebook object."""
    _df = pd.DataFrame(data={"x": [1, 2, 3], "y": [1, 2, 3]})
    sp = SpectraFitNotebook(
        df=_df,
        x_column="x",
        y_column="y",
        folder=str(tmp_path),
        fname="test",
    )
    sp.df_fit = dataframe_2
    sp.initial_model = initial_model
    sp.df_pre = _df
    sp.df_metric = _df
    return {"sp": sp, "tmpdir": tmp_path}


@pytest.fixture(name="class_spectrafit_fit")
def class_spectrafit_fixture_fit(
    dataframe: pd.DataFrame, x_column: str, y_column: str, tmp_path: Path
) -> SpectraFitNotebook:
    """Create a SpectraFitNotebook object."""
    return SpectraFitNotebook(
        df=dataframe,
        x_column=x_column,
        y_column=y_column,
        fname="test",
        folder=str(tmp_path),
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


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
@pytest.mark.webtest
class TestDataFramePlot:
    """Test the DataFramePlot class."""

    def test_dataframe_plot_1(self, dataframe: pd.DataFrame) -> None:
        """Test single plot with one y-column."""
        pp = DataFramePlot()
        with mock.patch(__plotly_io_show__) as mock_show:
            pp.plot_dataframe(
                args_plot=PlotAPI(x="Energy", y="Noisy", title="Test"), df=dataframe
            )
            mock_show.assert_called_once()

    def test_dataframe_plot_2(self, dataframe: pd.DataFrame) -> None:
        """Test single plot with two y-column."""
        pp = DataFramePlot()
        with mock.patch(__plotly_io_show__) as mock_show:
            pp.plot_dataframe(
                args_plot=PlotAPI(x="Energy", y=["Intensity", "Noisy"], title="Test"),
                df=dataframe,
            )
            mock_show.assert_called_once()

    def test_dataframe_plot_3(self, dataframe_2: pd.DataFrame) -> None:
        """Test douple plot."""
        pp = DataFramePlot()
        with mock.patch(__plotly_io_show__) as mock_show:
            pp.plot_2dataframes(
                args_plot=PlotAPI(x="energy", y="intensity", title="Test"),
                df_1=dataframe_2,
                df_2=dataframe_2,
            )
            mock_show.assert_called_once()

    def test_dataframe_plot_4(self, dataframe_2: pd.DataFrame) -> None:
        """Test double plot with residual."""
        pp = DataFramePlot()
        with mock.patch(__plotly_io_show__) as mock_show:
            pp.plot_2dataframes(
                args_plot=PlotAPI(x="energy", y="intensity", title="Test"),
                df_1=dataframe_2,
            )
            mock_show.assert_called_once()


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

    def test_export_df(self, dataframe: pd.DataFrame, tmp_path: Path) -> None:
        """Test the export function."""
        fname = "test"
        prefix = "test"
        suffix = "csv"
        folder = str(tmp_path)
        ExportResults().export_df(
            df=dataframe,
            args=FnameAPI(fname=fname, prefix=prefix, suffix=suffix, folder=folder),
        )
        assert Path(folder).joinpath(f"{prefix}_{fname}.{suffix}").exists()

    def test_export_report(self, dataframe: pd.DataFrame, tmp_path: Path) -> None:
        """Test the export function."""
        fname = "test"
        prefix = "test"
        suffix = "lock"
        folder = str(tmp_path)
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


class TestSpectraFitNotebook:
    """Test the SpectraFitNotebook class."""

    def test_init(
        self,
        dataframe: pd.DataFrame,
        x_column: str,
        y_column: str,
        y_columns: List[str],
    ) -> None:
        """Test the initialization of the class."""
        assert isinstance(
            SpectraFitNotebook(df=dataframe, x_column=x_column, y_column=y_column),
            SpectraFitNotebook,
        )
        assert isinstance(
            SpectraFitNotebook(df=dataframe, x_column=x_column, y_column=y_columns),
            SpectraFitNotebook,
        )

    def test_init_fail(self, dataframe: pd.DataFrame, x_column: str) -> None:
        """Test the initialization of the class."""
        with pytest.raises(ValueError) as excinfo:
            SpectraFitNotebook(
                df=dataframe[[x_column]], x_column=x_column, y_column="wrong"
            )

        assert "The dataframe must have 2 or more columns." in str(excinfo.value)

    def test_pre_process(
        self, dataframe: pd.DataFrame, x_column: str, y_column: str
    ) -> None:
        """Test the pre_process function."""
        sp = SpectraFitNotebook(df=dataframe, x_column=x_column, y_column=y_column)
        sp.pre_process
        sp.df_fit = dataframe
        assert isinstance(sp.return_df_org, pd.DataFrame)
        assert isinstance(sp.return_df_pre, pd.DataFrame)
        assert isinstance(sp.return_df_fit, pd.DataFrame)
        assert isinstance(sp.return_df, pd.DataFrame)
        assert isinstance(sp.return_pre_statistic, dict)

    def test_export_df(self, class_spectrafit: Dict[Any, Any]) -> None:
        """Test the export_df function."""
        class_spectrafit["sp"].export_df_act
        class_spectrafit["sp"].export_df_fit
        class_spectrafit["sp"].export_df_org
        class_spectrafit["sp"].export_df_pre
        class_spectrafit["sp"].export_df_metric
        assert ExportResults.fname2Path(
            folder=class_spectrafit["tmpdir"], fname="test", prefix="act", suffix="csv"
        ).exists()
        assert ExportResults.fname2Path(
            folder=class_spectrafit["tmpdir"], fname="test", prefix="fit", suffix="csv"
        ).exists()
        assert ExportResults.fname2Path(
            folder=class_spectrafit["tmpdir"], fname="test", prefix="org", suffix="csv"
        ).exists()
        assert ExportResults.fname2Path(
            folder=class_spectrafit["tmpdir"], fname="test", prefix="pre", suffix="csv"
        ).exists()
        assert ExportResults.fname2Path(
            folder=class_spectrafit["tmpdir"],
            fname="test",
            prefix="metric",
            suffix="csv",
        ).exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
    @pytest.mark.webtest
    def test_plot_org(
        self,
        class_spectrafit: Dict[Any, Any],
    ) -> None:
        """Test the plot function."""
        with mock.patch(__plotly_io_show__) as mock_show:
            class_spectrafit["sp"].plot_original_df
            mock_show.assert_called_once()

    @pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
    @pytest.mark.webtest
    def test_plot_current(
        self,
        class_spectrafit: Dict[Any, Any],
    ) -> None:
        """Test the plot function."""
        with mock.patch(__plotly_io_show__) as mock_show:
            class_spectrafit["sp"].plot_current_df
            mock_show.assert_called_once()

    @pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
    @pytest.mark.webtest
    def test_plot_preprocess(
        self,
        class_spectrafit: Dict[Any, Any],
    ) -> None:
        """Test the plot function."""
        with mock.patch(__plotly_io_show__) as mock_show:
            class_spectrafit["sp"].plot_preprocessed_df
            mock_show.assert_called_once()

    @pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
    @pytest.mark.webtest
    def test_plot_fit(
        self,
        class_spectrafit: Dict[Any, Any],
    ) -> None:
        """Test the plot function."""
        with mock.patch(__plotly_io_show__) as mock_show:
            class_spectrafit["sp"].plot_fit_df
            mock_show.assert_called_once()

    def test_display(
        self,
        class_spectrafit: Dict[Any, Any],
    ) -> None:
        """Test the display function."""
        class_spectrafit["sp"].display_preprocessed_df
        class_spectrafit["sp"].display_original_df
        class_spectrafit["sp"].display_current_df
        class_spectrafit["sp"].display_fit_df

    def test_generate_report(
        self,
        class_spectrafit_fit: SpectraFitNotebook,
        dataframe_2: pd.DataFrame,
        initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
        args_out: Dict[str, Any],
    ) -> None:
        """Test the generate_report function."""
        sp = class_spectrafit_fit
        sp.initial_model = initial_model
        sp.args = args_out
        sp.df_fit = dataframe_2
        sp.generate_report

        assert ExportResults.fname2Path(
            folder=sp.export_args_out.folder,
            fname="test",
            suffix="lock",
        ).exists()

    def test_fit(
        self,
        class_spectrafit_fit: SpectraFitNotebook,
        initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
    ) -> None:
        """Test the fit function."""
        sp = class_spectrafit_fit

        with mock.patch(__plotly_io_show__) as mock_show:
            sp.solver_model(
                initial_model=initial_model,
                show_plot=True,
                show_df=True,
                show_metric=False,
            )
            mock_show.assert_called_once()

    def test_metric(
        self,
        class_spectrafit_fit: SpectraFitNotebook,
        initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
    ) -> None:
        """Test the metric plot function."""
        sp = class_spectrafit_fit

        with mock.patch(__plotly_io_show__) as mock_show:
            sp.solver_model(
                initial_model=initial_model,
                show_plot=False,
                show_df=True,
                show_metric=True,
            )
            mock_show.assert_called_once()

    def test_conv_1(
        self,
        class_spectrafit_fit: SpectraFitNotebook,
        initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
    ) -> None:
        """Test conf interval via bool."""
        sp = class_spectrafit_fit

        with mock.patch(__plotly_io_show__) as mock_show:
            sp.solver_model(
                initial_model=initial_model,
                show_plot=False,
                show_df=True,
                show_metric=True,
                show_peaks=True,
                conf_interval=True,
            )
            mock_show.assert_called_once()

    def test_conv_2(
        self,
        class_spectrafit_fit: SpectraFitNotebook,
        initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
    ) -> None:
        """Test conf interval via bool."""
        sp = class_spectrafit_fit

        with mock.patch(__plotly_io_show__) as mock_show:
            sp.solver_model(
                initial_model=initial_model,
                show_plot=False,
                show_df=True,
                show_metric=True,
                show_peaks=True,
                conf_interval={},
            )

            mock_show.assert_called_once()

    def test_display_current_df(
        self,
        class_spectrafit_fit: SpectraFitNotebook,
        dataframe_2: pd.DataFrame,
    ) -> None:
        """Test the display_current_df function."""
        sp = class_spectrafit_fit
        sp.df_pre = sp.df_org = sp.df_fit = dataframe_2
        sp.display_current_df()
        sp.display_original_df()
        sp.display_preprocessed_df()
        sp.display_fit_df()
