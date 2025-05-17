"""Test the model model."""

from __future__ import annotations

import pytest

from spectrafit.api.models_model import DistributionModelAPI


@pytest.mark.parametrize(
    "distribution_model",
    [
        "gaussian",
        "orcagaussian",
        "lorentzian",
        "voigt",
        "pseudovoigt",
        "exponential",
        "power",
        "linear",
        "constant",
        "erf",
        "heaviside",
        "atan",
        "log",
        "cgaussian",
        "clorentzian",
        "cvoigt",
        "polynom2",
        "polynom3",
        "pearson1",
        "pearson2",
        "pearson3",
        "pearson4",
        "moessbauersinglet",
        "moessbauerdoublet",
        "moessbauersextet",
        "moessbaueroctet",
    ],
)
def test_distribution_model(distribution_model: str) -> None:
    """Test the distribution model."""
    assert distribution_model in list(
        DistributionModelAPI.model_json_schema()["properties"].keys(),
    )
