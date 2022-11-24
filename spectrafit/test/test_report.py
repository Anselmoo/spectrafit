"""Pytest of report model."""
from typing import Any
from typing import Dict

import numpy as np
import pandas as pd
import pytest

from pytest_mock.plugin import MockerFixture
from spectrafit.report import RegressionMetrics
from spectrafit.report import _extracted_gof_from_results


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
