"""Unit tests for the synthetic spectrum generator boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter


if TYPE_CHECKING:
    from spectrafit.models.types import CanonicalSpectraFitInput
    from spectrafit.models.types import LegacySpectraFitInput


@pytest.mark.unit
def test_peak_definition_promotes_shorthand_to_fit_parameters() -> None:
    peak = PeakDefinition(
        model="gaussian",
        params={"amplitude": 2.0, "center": 0.0, "fwhmg": 0.4},
    )

    amplitude = peak.parameters["amplitude"]
    center = peak.parameters["center"]
    fwhmg = peak.parameters["fwhmg"]

    assert amplitude.value == pytest.approx(2.0)
    assert amplitude.min == pytest.approx(1.0)
    assert amplitude.max == pytest.approx(3.0)
    assert amplitude.vary is True

    assert center.value == pytest.approx(0.0)
    assert center.min == pytest.approx(0.0)
    assert center.max == pytest.approx(0.0)
    assert center.vary is False

    assert fwhmg.value == pytest.approx(0.4)
    assert fwhmg.min == pytest.approx(0.2)
    assert fwhmg.max == pytest.approx(0.6)
    assert fwhmg.vary is True


@pytest.mark.unit
def test_peak_definition_to_component_preserves_explicit_parameter_models() -> None:
    peak = PeakDefinition(
        model="lorentzian",
        parameters={
            "amplitude": FitParameter(value=1.0, min=0.0, max=3.0, vary=False),
            "center": FitParameter(value=-0.5, min=-1.0, max=1.0),
            "fwhml": FitParameter(value=0.3, min=0.1, max=0.8),
        },
    )

    component = peak.to_component("main")

    assert component.id == "main"
    assert component.model == "lorentzian"
    assert component.parameters == peak.parameters


@pytest.mark.unit
def test_peak_definition_reuses_canonical_component_contract() -> None:
    peak = PeakDefinition(
        model="gaussian",
        params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.4},
    )

    dumped = peak.model_dump(mode="json", exclude_none=True)

    assert isinstance(peak, Component)
    assert peak.id == "synthetic"
    assert "id" not in dumped
    assert dumped["model"] == "gaussian"
    assert dumped["parameters"]["amplitude"]["value"] == pytest.approx(1.0)


@pytest.mark.unit
def test_synthetic_spectrum_to_config_returns_canonical_v2_components() -> None:
    spectrum = SyntheticSpectrum(
        x_min=-5.0,
        x_max=5.0,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.5},
            ),
            PeakDefinition(
                model="linear",
                params={"slope": 0.0, "intercept": 0.1},
            ),
        ],
    )

    config = spectrum.to_config()

    assert isinstance(config, UnifiedFittingConfig)
    assert [component.id for component in config.components] == ["p1", "p2"]
    assert [component.model for component in config.components] == [
        "gaussian",
        "linear",
    ]
    assert config.components[0].parameters["amplitude"].value == pytest.approx(1.0)
    assert config.components[1].parameters["intercept"].value == pytest.approx(0.1)


@pytest.mark.unit
def test_to_spectrafit_input_defaults_to_canonical_v2_shape() -> None:
    spectrum = SyntheticSpectrum(
        x_min=-5.0,
        x_max=5.0,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.5},
            ),
        ],
    )

    payload = spectrum.to_spectrafit_input()

    assert isinstance(payload, dict)
    assert "components" in payload
    assert "peaks" not in payload
    assert payload["components"] == [
        {
            "id": "p1",
            "model": "gaussian",
            "parameters": {
                "amplitude": {"value": 1.0, "min": 0.5, "max": 1.5, "vary": True},
                "center": {"value": 0.0, "min": 0.0, "max": 0.0, "vary": False},
                "fwhmg": {"value": 0.5, "min": 0.25, "max": 0.75, "vary": True},
            },
        }
    ]


@pytest.mark.unit
def test_to_spectrafit_input_matches_canonical_payload_contract() -> None:
    spectrum = SyntheticSpectrum(
        x_min=-5.0,
        x_max=5.0,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.5},
            ),
        ],
    )

    payload = spectrum.to_spectrafit_input()
    typed_payload: CanonicalSpectraFitInput = payload

    assert typed_payload["components"][0]["parameters"]["center"]["vary"] is False
    assert typed_payload["components"][0]["id"] == "p1"


@pytest.mark.unit
def test_to_spectrafit_input_can_still_render_legacy_peak_mapping() -> None:
    spectrum = SyntheticSpectrum(
        x_min=-5.0,
        x_max=5.0,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.5},
            ),
        ],
    )

    payload = spectrum.to_spectrafit_input(legacy=True)
    typed_payload: LegacySpectraFitInput = payload

    assert typed_payload == {
        "peaks": {
            "1": {
                "gaussian": {
                    "amplitude": {
                        "value": 1.0,
                        "vary": True,
                        "min": 0.5,
                        "max": 1.5,
                    },
                    "center": {
                        "value": 0.0,
                        "vary": False,
                        "min": 0.0,
                        "max": 0.0,
                    },
                    "fwhmg": {
                        "value": 0.5,
                        "vary": True,
                        "min": 0.25,
                        "max": 0.75,
                    },
                }
            }
        }
    }
