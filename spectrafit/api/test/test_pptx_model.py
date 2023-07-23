"""Test the pptx_model module."""
import pytest

from spectrafit.api.pptx_model import DescriptionAPI
from spectrafit.api.pptx_model import GoodnessOfFitAPI
from spectrafit.api.pptx_model import InputAPI
from spectrafit.api.pptx_model import MethodAPI
from spectrafit.api.pptx_model import OutputAPI
from spectrafit.api.pptx_model import PPTXDataAPI
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
    assert goodness_of_fit.chi_square == 1.0
    assert goodness_of_fit.reduced_chi_square == 0.5
    assert goodness_of_fit.akaike_information == 2.0
    assert goodness_of_fit.bayesian_information == 3.0


def test_regression_metrics() -> None:
    """Test the RegressionMetrics class."""
    regression_metrics = RegressionMetricsAPI(
        index=["x", "y"], columns=[1, 2], data=[[1.0, 2.0], [3.0, 4.0]]
    )
    assert regression_metrics.index == ["x", "y"]
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
        index=["x", "y"], columns=[1, 2], data=[[1.0, 2.0], [3.0, 4.0]]
    )
    variables = {"x": {"init_value": 1.0, "model_value": 0.1, "best_fit_value": 0.2}}
    solver = SolverAPI(
        goodness_of_fit=goodness_of_fit,
        regression_metrics=regression_metrics,
        variables=variables,
    )
    assert solver.goodness_of_fit == goodness_of_fit
    assert solver.regression_metrics == regression_metrics


def test_pptx_data(project_name: str) -> None:
    """Test the PPTXData class."""
    method = MethodAPI(global_fitting=True)
    description = DescriptionAPI(project_name=project_name, version="1.0")
    input_data = InputAPI(method=method, description=description)
    output_data = OutputAPI(df_fit={"x": [1, 2, 3], "y": [4, 5, 6]})
    goodness_of_fit = GoodnessOfFitAPI(
        chi_square=1.0,
        reduced_chi_square=0.5,
        akaike_information=2.0,
        bayesian_information=3.0,
    )
    regression_metrics = RegressionMetricsAPI(
        index=["x", "y"], columns=[1, 2], data=[[1.0, 2.0], [3.0, 4.0]]
    )
    variables = {"x": {"init_value": 1.0, "model_value": 0.1, "best_fit_value": 0.2}}
    solver = SolverAPI(
        goodness_of_fit=goodness_of_fit,
        regression_metrics=regression_metrics,
        variables=variables,
    )
    pptx_data = PPTXDataAPI(output=output_data, input=input_data, solver=solver)
    assert pptx_data.output == output_data
    assert pptx_data.input == input_data
    assert pptx_data.solver == solver
