"""Pytest of report model."""

from math import isclose
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import numpy as np
import pandas as pd
import pytest

from lmfit import Parameter
from lmfit import Parameters
from pytest_mock.plugin import MockerFixture
from spectrafit.report import CIReport
from spectrafit.report import FitReport
from spectrafit.report import PrintingResults
from spectrafit.report import PrintingStatus
from spectrafit.report import RegressionMetrics
from spectrafit.report import _extracted_gof_from_results
from spectrafit.report import get_init_value


class TestRegressionMetrics:
    """Test of the regression metrics module."""

    def test_raise_error(self) -> None:
        """Testing raise error."""
        with pytest.raises(ValueError) as excinfo:
            _ = RegressionMetrics(
                pd.DataFrame(
                    {
                        "intensity_0": np.random.default_rng(0).normal(size=10),
                        "intensity_1": np.random.default_rng(1).normal(size=10),
                        "fit_0": np.random.default_rng(2).normal(size=10),
                    }
                )
            )
        assert "The shape of the real and fit data-values are not equal!" in str(
            excinfo.value
        )


def test_extracted_gof_from_results(mocker: MockerFixture) -> None:
    """Test of the extracted gof from results.

    Args:
        mocker (MockerFixture): Pytest mocker fixture.

    !!! info "About `_extracted_gof_from_results` mock"
        This test is not a real test. It is just a mock to get the coverage
        up. The test is not really necessary, because the function is just
        a wrapper for the print function. The print function is tested
        in the test of the report module.

        The mock-up is realized with the `mocker` fixture. The mocker fixture
        is an extension and `built-in` pytest fixture. It is used to mock
        functions and classes.

        Mockup over `lmfit` is necessary for the test, because the `results` and
        `params` attributes have to be defined.
    """
    with mocker.patch("spectrafit.report._extracted_gof_from_results") as result:
        result = mocker.MagicMock()
        result.errorbars = False
        result.method = "not_a_method"
        with mocker.patch("spectrafit.report._extracted_gof_from_results") as params:
            params = mocker.MagicMock()
            buffer: Dict[str, Dict[Any, Any]] = {
                "configurations": {},
                "statistics": {},
                "variables": {},
                "errorbars": {},
                "correlations": {},
                "covariance_matrix": {},
            }
            _extracted_gof_from_results(result, buffer, params)


def test_printing_results() -> None:
    """Test of the printing results."""
    pr = PrintingResults(
        args={
            "conf_interval": {
                "wrong_key": "wrong_value",
            },
            "linear_correlation": {
                "intensity_0": np.arange(10),
                "intensity_1": np.arange(10),
            },
        },
        result=None,
        minimizer=None,
    )
    pr.print_confidence_interval()
    assert pr.args["confidence_interval"] == {}


@pytest.fixture(
    scope="module",
    name="par_init",
)
def par_init() -> Parameter:
    """Parameter with init value."""
    return Parameter(name="par_init", value=1.0)


@pytest.fixture(
    scope="module",
    name="par_expr",
)
def par_expr() -> Parameter:
    """Parameter with expression."""
    return Parameter(name="par_expr", expr="par_init")


@pytest.fixture(
    scope="module",
    name="par_model",
)
def par_model() -> Dict[str, Union[Parameter, Parameters]]:
    """Parameter with expression."""
    modelpars = Parameters()
    modelpars.add("param", value=2.0)

    return {"param": Parameter(name="param"), "modelpars": modelpars}


@pytest.fixture(
    scope="module",
    name="par_fixed",
)
def par_fixed() -> Parameter:
    """Parameter with expression."""
    return Parameter(name="par_fixed", value=None, vary=False, min=3.0)


def test_get_init_value(
    par_init: Parameter,
    par_expr: Parameter,
    par_model: Dict[str, Union[Parameter, Parameters]],
    par_fixed: Parameter,
) -> None:
    """Test of the get init value."""
    assert isclose(float(get_init_value(par_init)), 1.0)
    assert get_init_value(par_expr) == f"As expressed value: {par_expr.expr}"
    assert isclose(float(get_init_value(**par_model)), 2.0)
    assert get_init_value(par_fixed) == f"As fixed value: {par_fixed.min}"


class TestPrintingStatus:
    """Test of the printing status."""

    ps = PrintingStatus()

    def assert_capfd(self, capfd: Any) -> None:
        """Assert the capfd."""
        out, err = capfd.readouterr()
        assert isinstance(out, str)
        assert err == ""

    def test_welcome(self, capfd: Any) -> None:
        """Test of the welcome message."""
        self.ps.welcome()
        self.assert_capfd(capfd=capfd)

    def test_version(self, capfd: Any) -> None:
        """Test of the version message."""
        self.ps.version()
        self.assert_capfd(capfd=capfd)

    def test_start(self, capfd: Any) -> None:
        """Test of the start message."""
        self.ps.start()
        self.assert_capfd(capfd=capfd)

    def test_end(self, capfd: Any) -> None:
        """Test of the end message."""
        self.ps.end()
        self.assert_capfd(capfd=capfd)

    def test_yes_no(self, capfd: Any) -> None:
        """Test of the yes no message."""
        self.ps.yes_no()
        self.assert_capfd(capfd=capfd)

    def test_credits(self, capfd: Any) -> None:
        """Test of the credits message."""
        self.ps.credits()
        self.assert_capfd(capfd=capfd)


@pytest.mark.parametrize(
    "sort_pars,show_correl,min_correl,modelpars,expected_parnames",
    [
        (True, True, 0.0, None, ["a", "b"]),  # ID: sort-true-showcorrel-true
        (False, False, 0.0, None, ["a", "b"]),  # ID: sort-false-showcorrel-false
        (
            True,
            True,
            0.5,
            {"a": Parameter(name="a", value=2)},
            ["a", "b"],
        ),  # ID: mincorrel-0.5-modelpars
    ],
    ids=[
        "sort-true-showcorrel-true",
        "sort-false-showcorrel-false",
        "mincorrel-0.5-modelpars",
    ],
)
def test_fit_report_init(
    sort_pars: bool,
    show_correl: bool,
    min_correl: float,
    modelpars: Union[None, Dict[str, Parameters]],
    expected_parnames: List[str],
) -> None:
    """Test the initialization of the FitReport class.

    Args:
        sort_pars (bool): The input value for the sort_pars parameter.
        show_correl (bool): The input value for the show_correl parameter.
        min_correl (float): The input value for the min_correl parameter.
        modelpars (Union[None, Dict[str, Parameters]]): The input value for the
            modelpars parameter.
        expected_parnames (List[str]): The expected parnames attribute of the
            FitReport class.
    """
    params = Parameters()
    params.add_many(("a", 1, True), ("b", 2, True))
    report = FitReport(
        inpars=params,
        sort_pars=sort_pars,
        show_correl=show_correl,
        min_correl=min_correl,
        modelpars=modelpars,  # type: ignore
    )
    assert report.parnames == expected_parnames


@pytest.mark.parametrize(
    "inpars,expected_result",
    [
        (Parameters(), None),  # ID: empty-parameters
        ("not_parameters", AttributeError),  # ID: incorrect-type
    ],
    ids=["empty-parameters", "incorrect-type"],
)
def test_generate_fit_statistics_edge_cases(
    inpars: Union[Parameters, str], expected_result: Union[None, Exception]
) -> None:
    """Test the edge cases of the  method in the FitReport class.

    Args:
        inpars (Union[Parameters, str]): The input parameters for the
            FitReport class. If it is a string, it is expected to
            raise an exception.
        expected_result (Union[None, Exception]): The expected
            result of the generate_fit_statistics method.
    """
    if isinstance(inpars, str):
        with pytest.raises(expected_result) as exc_info:  # type: ignore
            FitReport(inpars=inpars)
        assert isinstance(exc_info.value, expected_result)  # type: ignore
        return
    report = FitReport(inpars=inpars)
    result = report.generate_fit_statistics()
    assert result is expected_result


# Error cases
@pytest.mark.parametrize(
    "inpars,exception",
    [
        ([], AttributeError),
    ],
    ids=["list-instead-parameters"],
)
def test_fit_report_init_error_cases(inpars: List[Any], exception: Exception) -> None:
    """Test the initialization of FitReport with error cases.

    Args:
        inpars (List[Any]): The input parameters for FitReport.
        exception (Exception): The expected exception to be raised.
    """
    with pytest.raises(exception):  # type: ignore
        FitReport(inpars=inpars)


@pytest.mark.parametrize(
    "ci, with_offset, ndigits, expected_output, test_id",
    [
        (
            {"param1": [(0.025, 2), (0.975, 4)], "param2": [(0.025, 3), (0.975, 5)]},
            True,
            5,
            pd.DataFrame(
                index=["param1", "param2"],
                columns=["BEST", "0.025% - LOWER", "0.975% - UPPER"],
                data=[[1.0, 2.0, 4.0], [2.0, 3.0, 5.0]],
            ),
            "Run - 1",
        ),
        (
            {
                "param1": [(0.0, 1), (0.025, 2), (0.975, 4)],
                "param2": [(0.0, 2), (0.025, 3), (0.975, 5)],
            },
            False,
            3,
            pd.DataFrame(
                index=["param1", "param2"],
                columns=["BEST", "0.025% - LOWER", "0.975% - UPPER"],
                data=[[1.0, 2.0, 4.0], [2.0, 3.0, 5.0]],
            ),
            "2",
        ),
        (
            {"param1": [(0.0, 1)]},
            True,
            2,
            pd.DataFrame({"BEST": {"param1": 1.0}}),
            "3",
        ),
        ({}, True, 5, pd.DataFrame(), "4"),
    ],
)
def test_CIReport(
    ci: Dict[str, List[Any]],
    with_offset: bool,
    ndigits: int,
    expected_output: pd.DataFrame,
    test_id: str,
) -> None:
    """Test the CIReport class."""
    report = CIReport(ci=ci, with_offset=with_offset, ndigits=ndigits)

    report()
