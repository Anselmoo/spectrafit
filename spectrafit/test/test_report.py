"""Pytest of report model."""
import numpy as np
import pandas as pd
import pytest

from spectrafit.report import RegressionMetrics


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
