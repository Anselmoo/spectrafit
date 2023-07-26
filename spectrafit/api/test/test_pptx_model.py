"""Test the pptx_model module."""
from typing import Tuple
from typing import Type
from typing import Union

import pandas as pd
import pytest

from spectrafit.api.pptx_model import DescriptionAPI
from spectrafit.api.pptx_model import Field43API
from spectrafit.api.pptx_model import Field169API
from spectrafit.api.pptx_model import Field169HDRAPI
from spectrafit.api.pptx_model import GoodnessOfFitAPI
from spectrafit.api.pptx_model import InputAPI
from spectrafit.api.pptx_model import MethodAPI
from spectrafit.api.pptx_model import OutputAPI
from spectrafit.api.pptx_model import PPTXDataAPI
from spectrafit.api.pptx_model import PPTXLayoutAPI
from spectrafit.api.pptx_model import RegressionMetricsAPI
from spectrafit.api.pptx_model import SolverAPI


@pytest.fixture
def project_name() -> str:
    """Return a project name."""
    return "Test Project"


def test_method() -> None:
    """Test the Method class."""
    method = MethodAPI(global_fitting=True)
    assert method.global_fitting is True


def test_description(project_name: str) -> None:
    """Test the Description class."""
    description = DescriptionAPI(project_name=project_name, version="1.0")
    assert description.project_name == project_name
    assert description.version == "1.0"


def test_input(project_name: str) -> None:
    """Test the Input class."""
    method = MethodAPI(global_fitting=True)
    description = DescriptionAPI(project_name=project_name, version="1.0")
    input_data = InputAPI(method=method, description=description)
    assert input_data.method == method
    assert input_data.description == description


def test_output() -> None:
    """Test the Output class."""
    output_data = OutputAPI(df_fit={"x": [1, 2, 3], "y": [4, 5, 6]})
    assert output_data.df_fit == {"x": [1, 2, 3], "y": [4, 5, 6]}


def test_goodness_of_fit() -> None:
    """Test the GoodnessOfFit class."""
    goodness_of_fit = GoodnessOfFitAPI(
        chi_square=1.0,
        reduced_chi_square=0.5,
        akaike_information=2.0,
        bayesian_information=3.0,
    )
    assert goodness_of_fit.chi2 == 1.0
    assert goodness_of_fit.r_chi2 == 0.5
    assert goodness_of_fit.akaike == 2.0
    assert goodness_of_fit.bayesian == 3.0


def test_regression_metrics() -> None:
    """Test the RegressionMetrics class."""
    regression_metrics = RegressionMetricsAPI(
        index=["r2_score", "mean_squared_error"],
        columns=[1, 2],
        data=[[1.0, 2.0], [3.0, 4.0]],
    )
    assert regression_metrics.index == ["r2", "me"]
    assert regression_metrics.columns == [1, 2]
    assert regression_metrics.data == [[1.0, 2.0], [3.0, 4.0]]


def test_solver() -> None:
    """Test the Solver class."""
    goodness_of_fit = GoodnessOfFitAPI(
        chi_square=1.0,
        reduced_chi_square=0.5,
        akaike_information=2.0,
        bayesian_information=3.0,
    )
    regression_metrics = RegressionMetricsAPI(
        index=["r2_score", "mean_squared_error"],
        columns=[1, 2],
        data=[[1.0, 2.0], [3.0, 4.0]],
    )
    variables = {"x": {"init_value": 1.0, "model_value": 0.1, "best_fit_value": 0.2}}
    solver = SolverAPI(
        goodness_of_fit=goodness_of_fit,
        regression_metrics=regression_metrics,
        variables=variables,
    )
    assert solver.goodness_of_fit == goodness_of_fit
    assert solver.regression_metrics == regression_metrics


@pytest.fixture
def pptx_data(project_name: str) -> Tuple[PPTXDataAPI, OutputAPI, InputAPI, SolverAPI]:
    """Return a PPTXData object."""
    method = MethodAPI(global_fitting=True)
    description = DescriptionAPI(project_name=project_name, version="1.0")
    input_data = InputAPI(method=method, description=description)
    output_data = OutputAPI(
        df_fit=pd.read_csv(
            "https://raw.githubusercontent.com/Anselmoo"
            "/spectrafit/main/Examples/example_1_fit.csv"
        ).to_dict(orient="list")
    )
    goodness_of_fit = GoodnessOfFitAPI(
        chi_square=1.0,
        reduced_chi_square=0.5,
        akaike_information=2.0,
        bayesian_information=3.0,
    )
    regression_metrics = RegressionMetricsAPI(
        index=["r2_score", "mean_squared_error"],
        columns=[1, 2],
        data=[[1.0, 2.0], [3.0, 4.0]],
    )
    variables = {"x": {"init_value": 1.0, "model_value": 0.1, "best_fit_value": 0.2}}
    solver = SolverAPI(
        goodness_of_fit=goodness_of_fit,
        regression_metrics=regression_metrics,
        variables=variables,
    )
    return (
        PPTXDataAPI(output=output_data, input=input_data, solver=solver),
        output_data,
        input_data,
        solver,
    )


def test_pptx_data(
    pptx_data: Tuple[PPTXDataAPI, OutputAPI, InputAPI, SolverAPI]
) -> None:
    """Test the PPTXData class."""
    assert pptx_data[0].output == pptx_data[1]
    assert pptx_data[0].input == pptx_data[2]
    assert pptx_data[0].solver == pptx_data[3]


@pytest.mark.parametrize("format", ["16:9", "16:9HDR", "4:3"])
def test_pptx_layout_init(
    format: str,
    pptx_data: Tuple[PPTXDataAPI, OutputAPI, InputAPI, SolverAPI],
    project_name: str,
) -> None:
    """Test the PPTXLayout class."""
    layout = PPTXLayoutAPI(format, pptx_data[0])
    assert layout._format == format
    assert layout.title == project_name
    assert isinstance(layout.df_gof, pd.DataFrame)
    assert isinstance(layout.df_regression, pd.DataFrame)
    assert isinstance(layout.df_variables, pd.DataFrame)


def test_pptx_layout_tmp_plot(
    project_name: str,
    pptx_data: Tuple[PPTXDataAPI, OutputAPI, InputAPI, SolverAPI],
) -> None:
    """Test the PPTXLayout class."""
    layout = PPTXLayoutAPI(project_name, pptx_data[0])

    assert layout.tmp_fname.exists()
    assert layout.tmp_fname.suffix == ".png"


@pytest.mark.parametrize(
    "format, expected_output",
    [("16:9", Field169API), ("16:9HDR", Field169HDRAPI), ("4:3", Field43API)],
)
def test_get_pptx_layout(
    format: str,
    pptx_data: Tuple[PPTXDataAPI, OutputAPI, InputAPI, SolverAPI],
    expected_output: Type[Union[Field169API, Field169HDRAPI, Field43API]],
) -> None:
    """Test the PPTXLayout class."""
    layout = PPTXLayoutAPI(format, pptx_data[0])
    assert isinstance(layout.get_pptx_layout(), expected_output)
