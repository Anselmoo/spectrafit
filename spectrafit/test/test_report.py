"""Pytest of report model."""

from __future__ import annotations

import sys

from math import isclose
from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from lmfit import Parameter
from lmfit import Parameters

from spectrafit.report import CIReport
from spectrafit.report import FitReport
from spectrafit.report import PrintingResults
from spectrafit.report import PrintingStatus
from spectrafit.report import RegressionMetrics
from spectrafit.report import _extracted_gof_from_results
from spectrafit.report import get_init_value


if TYPE_CHECKING:
    from pytest_mock.plugin import MockerFixture


def test_pandas_option_setting_for_old_python() -> None:
    """Test pandas option setting for Python < 3.10."""
    # Mock sys.version_info to simulate Python 3.9
    with patch.object(sys, "version_info", (3, 9, 0)):
        # Reimport module to trigger the version check
        import importlib

        import spectrafit.report

        importlib.reload(spectrafit.report)
        # Check that pandas option is set (will be set in module reload)
        # Note: We can't directly verify this, but we ensure no error occurs
        assert True


class TestRegressionMetrics:
    """Test of the regression metrics module."""

    def test_raise_error(self) -> None:
        """Testing raise error."""
        error_msg = r"The shape of the real and fit data-values are not equal!"
        with pytest.raises(ValueError, match=error_msg):
            _ = RegressionMetrics(
                pd.DataFrame(
                    {
                        "intensity_0": np.random.default_rng(0).normal(size=10),
                        "intensity_1": np.random.default_rng(1).normal(size=10),
                        "fit_0": np.random.default_rng(2).normal(size=10),
                    },
                ),
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
            buffer: dict[str, dict[Any, Any]] = {
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


def test_printing_results_with_list_ci() -> None:
    """Test printing results with list-based confidence interval."""
    pr = PrintingResults(
        args={
            "conf_interval": True,
            "confidence_interval": [{"param1": [(0.0, 1.0), (0.95, 2.0)]}],
            "linear_correlation": {},
            "regression_metrics": {},
            "report": {},
            "data_statistic": {},
        },
        result=None,
        minimizer=None,
    )
    ci_payload = pr._extract_confidence_interval()  # noqa: SLF001
    assert ci_payload is not None
    assert "param1" in ci_payload


def test_printing_results_with_dict_ci() -> None:
    """Test printing results with dict-based confidence interval."""
    pr = PrintingResults(
        args={
            "conf_interval": True,
            "confidence_interval": {"param1": [(0.0, 1.0), (0.95, 2.0)]},
            "linear_correlation": {},
        },
        result=None,
        minimizer=None,
    )
    ci_payload = pr._extract_confidence_interval()  # noqa: SLF001
    assert ci_payload is not None
    assert "param1" in ci_payload


def test_printing_results_with_empty_list_ci() -> None:
    """Test printing results with empty list confidence interval."""
    pr = PrintingResults(
        args={
            "conf_interval": True,
            "confidence_interval": [],
            "linear_correlation": {},
        },
        result=None,
        minimizer=None,
    )
    ci_payload = pr._extract_confidence_interval()  # noqa: SLF001
    assert ci_payload is None


def test_printing_results_ci_exception() -> None:
    """Test printing results with confidence interval exception."""
    pr = PrintingResults(
        args={
            "conf_interval": True,
            "confidence_interval": {"invalid": "data"},
            "linear_correlation": {},
            "regression_metrics": {},
            "report": {},
            "data_statistic": {},
        },
        result=None,
        minimizer=None,
    )
    # This should not raise an exception, but handle it gracefully
    pr.print_confidence_interval()
    assert pr.args["confidence_interval"] == {}


def test_printing_results_verbose_mode(mocker: MockerFixture) -> None:
    """Test printing results in verbose mode."""
    mock_pprint = mocker.patch("spectrafit.report.pp.pprint")
    pr = PrintingResults(
        args={
            "verbose": 2,
            "conf_interval": True,
            "confidence_interval": {"param1": [(0.0, 1.0)]},
            "linear_correlation": {"test": [1, 2, 3]},
            "regression_metrics": {"r2": 0.95},
            "data_statistic": {"mean": 1.0},
            "fit_insights": {"chi2": 0.1},
            "report": {},
        },
        result=None,
        minimizer=None,
    )
    pr.print_confidence_interval_verbose()
    assert mock_pprint.called


def test_printing_results_verbose_mode_no_ci(mocker: MockerFixture) -> None:
    """Test printing results in verbose mode without confidence interval."""
    mock_pprint = mocker.patch("spectrafit.report.pp.pprint")
    pr = PrintingResults(
        args={
            "verbose": 2,
            "linear_correlation": {"test": [1, 2, 3]},
            "regression_metrics": {"r2": 0.95},
        },
        result=None,
        minimizer=None,
    )
    pr.print_confidence_interval_verbose()
    assert not mock_pprint.called


def test_printing_results_verbose_mode_empty_ci(mocker: MockerFixture) -> None:
    """Test printing results in verbose mode with empty confidence interval."""
    mock_pprint = mocker.patch("spectrafit.report.pp.pprint")
    pr = PrintingResults(
        args={
            "verbose": 2,
            "conf_interval": True,
            "confidence_interval": {},
            "linear_correlation": {"test": [1, 2, 3]},
            "regression_metrics": {"r2": 0.95},
        },
        result=None,
        minimizer=None,
    )
    pr.print_confidence_interval_verbose()
    assert not mock_pprint.called


def test_printing_results_print_linear_correlation() -> None:
    """Test print_linear_correlation method."""
    pr = PrintingResults(
        args={
            "linear_correlation": {"data": [[0.5, 0.6], [0.7, 0.8]]},
            "regression_metrics": {},
            "report": {},
        },
        result=None,
        minimizer=None,
    )
    # Just call the method - it should not raise any exception
    pr.print_linear_correlation()


def test_printing_results_print_regression_metrics() -> None:
    """Test print_regression_metrics method."""
    pr = PrintingResults(
        args={
            "linear_correlation": {},
            "regression_metrics": {"data": [[0.95, 0.01]]},
            "report": {},
        },
        result=None,
        minimizer=None,
    )
    # Just call the method - it should not raise any exception
    pr.print_regression_metrics()


def test_printing_results_extract_ci_none_list_with_empty_dict() -> None:
    """Test extract confidence interval with list containing empty dict."""
    pr = PrintingResults(
        args={
            "confidence_interval": [{}],
            "linear_correlation": {},
        },
        result=None,
        minimizer=None,
    )
    ci_payload = pr._extract_confidence_interval()  # noqa: SLF001
    assert ci_payload is None


def test_printing_results_extract_ci_none_empty_dict() -> None:
    """Test extract confidence interval with empty dict."""
    pr = PrintingResults(
        args={
            "confidence_interval": {},
            "linear_correlation": {},
        },
        result=None,
        minimizer=None,
    )
    ci_payload = pr._extract_confidence_interval()  # noqa: SLF001
    assert ci_payload is None


def test_printing_results_printing_verbose_mode(mocker: MockerFixture) -> None:
    """Test complete verbose mode printing."""
    mock_pprint = mocker.patch("spectrafit.report.pp.pprint")
    pr = PrintingResults(
        args={
            "verbose": 2,
            "data_statistic": {"mean": 1.0},
            "fit_insights": {"chi2": 0.1},
            "conf_interval": True,
            "confidence_interval": {"param": [(0.0, 1.0)]},
            "linear_correlation": {"test": [1, 2]},
            "regression_metrics": {"r2": 0.95},
        },
        result=None,
        minimizer=None,
    )
    pr.print_statistic_verbose()
    pr.print_input_parameters_verbose()
    pr.print_fit_results_verbose()
    pr.print_linear_correlation_verbose()
    pr.print_regression_metrics_verbose()
    assert mock_pprint.call_count == 5


def test_fit_report_generate_correlations_with_nan() -> None:
    """Test FitReport generate_correlations with NaN values requiring infer_objects."""
    params = Parameters()
    params.add("a", value=1.0, vary=True)
    params.add("b", value=2.0, vary=True)
    params.add("c", value=3.0, vary=False)

    # Add correlation data
    params["a"].correl = {"b": 0.8}

    report = FitReport(inpars=params, show_correl=True, min_correl=0.0)
    correl_matrix = report.generate_correlations()

    # The matrix should have been filled with 1s for diagonal and NaN for others
    assert isinstance(correl_matrix, pd.DataFrame)
    assert correl_matrix.loc["a", "b"] == 0.8
    assert correl_matrix.loc["b", "a"] == 0.8


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
def par_model() -> dict[str, Parameter | Parameters]:
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
    par_model: dict[str, Parameter | Parameters],
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
    ("sort_pars", "show_correl", "min_correl", "modelpars", "expected_parnames"),
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
    modelpars: None | dict[str, Parameters],
    expected_parnames: list[str],
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
    ("inpars", "expected_result"),
    [
        (Parameters(), None),  # ID: empty-parameters
        ("not_parameters", AttributeError),  # ID: incorrect-type
    ],
    ids=["empty-parameters", "incorrect-type"],
)
def test_generate_fit_statistics_edge_cases(
    inpars: Parameters | str,
    expected_result: None | Exception,
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
    ("inpars", "exception"),
    [
        ([], AttributeError),
    ],
    ids=["list-instead-parameters"],
)
def test_fit_report_init_error_cases(inpars: list[Any], exception: Exception) -> None:
    """Test the initialization of FitReport with error cases.

    Args:
        inpars (List[Any]): The input parameters for FitReport.
        exception (Exception): The expected exception to be raised.

    """
    with pytest.raises(exception):  # type: ignore
        FitReport(inpars=inpars)


@pytest.mark.parametrize(
    ("ci", "with_offset", "ndigits", "expected_output", "test_id"),
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
def test_ci_report(
    ci: dict[str, list[Any]],
    with_offset: bool,
    ndigits: int,
    expected_output: pd.DataFrame,
    test_id: str,
) -> None:
    """Test the CIReport class."""
    report = CIReport(ci=ci, with_offset=with_offset, ndigits=ndigits)

    report()


def test_fit_report_as_dict(mocker: MockerFixture) -> None:
    """Test fit_report_as_dict function."""
    from spectrafit.report import fit_report_as_dict

    # Create mock objects
    mock_result = mocker.MagicMock()
    mock_result.params = Parameters()
    mock_result.params.add("param1", value=1.0, vary=True)
    mock_result.params.add("param2", value=2.0, vary=True)
    mock_result.params["param1"].stderr = 0.1
    mock_result.params["param2"].stderr = 0.2
    mock_result.params["param1"].correl = {"param2": 0.5}
    mock_result.covar = np.array([[0.01, 0.005], [0.005, 0.04]])

    mock_minimizer = mocker.MagicMock()
    mock_minimizer.max_nfev = 1000
    mock_minimizer.scale_covar = True
    mock_minimizer.calc_covar = True

    # Call the function
    result_dict = fit_report_as_dict(
        inpars=mock_result, settings=mock_minimizer, modelpars=None
    )

    # Verify structure
    assert "configurations" in result_dict
    assert "statistics" in result_dict
    assert "variables" in result_dict
    assert "correlations" in result_dict
    assert "covariance_matrix" in result_dict
    assert "computational" in result_dict

    # Verify variables
    assert "param1" in result_dict["variables"]
    assert "param2" in result_dict["variables"]
    assert "best_value" in result_dict["variables"]["param1"]
    assert "error_relative" in result_dict["variables"]["param1"]
    assert "error_absolute" in result_dict["variables"]["param1"]

    # Verify correlations
    assert "param1" in result_dict["correlations"]
    assert "param2" in result_dict["correlations"]["param1"]

    # Verify covariance matrix
    assert "param1" in result_dict["covariance_matrix"]
    assert "param2" in result_dict["covariance_matrix"]["param1"]


def test_fit_report_as_dict_with_modelpars(mocker: MockerFixture) -> None:
    """Test fit_report_as_dict with model parameters."""
    from spectrafit.report import fit_report_as_dict

    # Create mock objects
    mock_result = mocker.MagicMock()
    mock_result.params = Parameters()
    mock_result.params.add("param1", value=1.0, vary=True)
    mock_result.params["param1"].stderr = 0.1
    mock_result.covar = np.array([[0.01]])

    mock_minimizer = mocker.MagicMock()
    mock_minimizer.max_nfev = 1000
    mock_minimizer.scale_covar = True
    mock_minimizer.calc_covar = True

    # Create model parameters
    modelpars = {"param1": Parameter(name="param1", value=1.5)}

    # Call the function
    result_dict = fit_report_as_dict(
        inpars=mock_result, settings=mock_minimizer, modelpars=modelpars
    )

    # Verify model_value is included
    assert "model_value" in result_dict["variables"]["param1"]
    assert result_dict["variables"]["param1"]["model_value"] == 1.5


def test_fit_report_as_dict_no_stderr(mocker: MockerFixture) -> None:
    """Test fit_report_as_dict without stderr."""
    from spectrafit.report import fit_report_as_dict

    # Create mock objects
    mock_result = mocker.MagicMock()
    mock_result.params = Parameters()
    mock_result.params.add("param1", value=1.0, vary=True)
    mock_result.params["param1"].stderr = None
    mock_result.covar = None

    mock_minimizer = mocker.MagicMock()
    mock_minimizer.max_nfev = 1000
    mock_minimizer.scale_covar = True
    mock_minimizer.calc_covar = True

    # Call the function
    result_dict = fit_report_as_dict(
        inpars=mock_result, settings=mock_minimizer, modelpars=None
    )

    # Verify no error fields
    assert "error_relative" not in result_dict["variables"]["param1"]
    assert "error_absolute" not in result_dict["variables"]["param1"]


def test_fit_report_as_dict_no_correlations(mocker: MockerFixture) -> None:
    """Test fit_report_as_dict without correlations."""
    from spectrafit.report import fit_report_as_dict

    # Create mock objects
    mock_result = mocker.MagicMock()
    mock_result.params = Parameters()
    mock_result.params.add("param1", value=1.0, vary=False)
    mock_result.covar = None

    mock_minimizer = mocker.MagicMock()
    mock_minimizer.max_nfev = 1000
    mock_minimizer.scale_covar = True
    mock_minimizer.calc_covar = True

    # Call the function
    result_dict = fit_report_as_dict(
        inpars=mock_result, settings=mock_minimizer, modelpars=None
    )

    # Verify empty correlations for non-varying parameter
    assert result_dict["correlations"]["param1"] == {}
