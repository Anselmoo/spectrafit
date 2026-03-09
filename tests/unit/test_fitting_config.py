"""Unit tests for UnifiedFittingConfig (v2 components-only contract)."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig


MINIMAL_V2: dict[str, object] = {
    "components": [
        {
            "id": "p1",
            "model": "gaussian",
            "parameters": {
                "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                "center": {"min": -2, "max": 2, "value": 0.0, "vary": True},
                "fwhmg": {"min": 0.01, "max": 1.0, "value": 0.5, "vary": True},
            },
        }
    ],
    "column": {"x": "energy", "y": "intensity"},
    "minimizer": {"nan_policy": "propagate", "calc_covar": True},
    "optimizer": {"max_nfev": 1000, "method": "leastsq"},
    "global_": 0,
}


@pytest.mark.unit
class TestFromDict:
    """UnifiedFittingConfig.from_dict() — v2 components input."""

    def test_minimal_valid(self) -> None:
        config = UnifiedFittingConfig.from_dict(MINIMAL_V2)
        assert config is not None

    def test_components_accessible(self) -> None:
        config = UnifiedFittingConfig.from_dict(MINIMAL_V2)
        assert len(config.components) == 1
        assert config.components[0].id == "p1"

    def test_multiple_components(self) -> None:
        data: dict[str, object] = {
            **MINIMAL_V2,
            "components": [
                {
                    "id": "p1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": -1.0},
                        "fwhmg": {"value": 0.5},
                    },
                },
                {
                    "id": "p2",
                    "model": "lorentzian",
                    "parameters": {
                        "amplitude": {"value": 0.8},
                        "center": {"value": 1.0},
                        "fwhml": {"value": 0.6},
                    },
                },
            ],
        }
        config = UnifiedFittingConfig.from_dict(data)
        assert len(config.components) == 2

    def test_mapping_payload_supported(self) -> None:
        config = UnifiedFittingConfig.from_dict(MappingProxyType(MINIMAL_V2))
        assert len(config.components) == 1


@pytest.mark.unit
class TestComponentsValidation:
    """Components are required for fit-capable configs."""

    def test_empty_config_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            UnifiedFittingConfig.from_dict({})

    def test_empty_components_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            UnifiedFittingConfig.from_dict({"components": []})

    def test_v1_peaks_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            UnifiedFittingConfig.from_dict(
                {"peaks": {"1": {"gaussian": {"amplitude": {"value": 1.0}}}}}
            )


_MINIMAL_TOML = """\
[data]
infile = "data.csv"
separator = ","

[column]
x = "energy"
y = "intensity"

[minimizer]
nan_policy = "propagate"
calc_covar = true

[optimizer]
max_nfev = 1000
method = "leastsq"

global_ = 0

[[components]]
id = "p1"
model = "gaussian"

[components.parameters]
amplitude = { value = 1.0, vary = true }
center = { value = 0.0, vary = true }
fwhmg = { value = 0.5, vary = true }
"""


@pytest.mark.unit
class TestFromFilePaths:
    """from_file() must rebase a relative infile against the config file's directory."""

    def test_relative_infile_rebased_to_config_dir(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "input.toml"
        toml_file.write_text(_MINIMAL_TOML, encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(toml_file)
        expected = (tmp_path / "data.csv").resolve()
        assert Path(str(cfg.data.infile)).resolve() == expected

    def test_absolute_infile_not_changed(self, tmp_path: Path) -> None:
        abs_path = (tmp_path / "data.csv").resolve()
        toml_content = _MINIMAL_TOML.replace(
            'infile = "data.csv"', f'infile = "{abs_path}"'
        )
        toml_file = tmp_path / "input.toml"
        toml_file.write_text(toml_content, encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(toml_file)
        assert Path(str(cfg.data.infile)).resolve() == abs_path

    def test_infile_in_subdir_rebased(self, tmp_path: Path) -> None:
        (tmp_path / "data").mkdir()
        toml_content = _MINIMAL_TOML.replace(
            'infile = "data.csv"', 'infile = "data/spectrum.csv"'
        )
        toml_file = tmp_path / "input.toml"
        toml_file.write_text(toml_content, encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(toml_file)
        expected = (tmp_path / "data" / "spectrum.csv").resolve()
        assert Path(str(cfg.data.infile)).resolve() == expected
