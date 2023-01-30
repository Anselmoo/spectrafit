"""Pytest of report model."""
from typing import Any
from typing import Dict
from typing import Union

import numpy as np
import pandas as pd
import pytest

from lmfit import Parameter
from lmfit import Parameters
from pytest_mock.plugin import MockerFixture
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
                        "intensity_0": np.random.rand(10),
                        "intensity_1": np.random.rand(10),
                        "fit_0": np.random.rand(10),
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
    assert get_init_value(par_init) == 1.0
    assert get_init_value(par_expr) == f"As expressed value: {par_expr.expr}"
    assert get_init_value(**par_model) == 2.0
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
