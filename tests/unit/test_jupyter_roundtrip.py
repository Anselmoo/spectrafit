"""Unit tests for SpectraFitNotebook round-trip methods (Phase 11c).

Covers:
- ``export_config_toml`` — serialize current notebook state to v2 TOML
- ``load_cli_config`` — load a v2 TOML/JSON back into UnifiedFittingConfig
"""

from __future__ import annotations

import warnings

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.jupyter.config_io import build_notebook_from_config
from spectrafit.jupyter.config_io import load_notebook_config
from spectrafit.jupyter.config_io import notebook_args_to_config
from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import SolverConfig


_SIMPLE_COMPONENTS: list[dict[str, object]] = [
    {
        "id": "p1",
        "model": "gaussian",
        "parameters": {
            "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
            "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
            "fwhmg": {"value": 0.1, "vary": True, "min": 0.02, "max": 0.5},
        },
    },
    {
        "id": "p2",
        "model": "lorentzian",
        "parameters": {
            "amplitude": {"value": 0.5, "vary": True, "min": 0.0, "max": 2.0},
            "center": {"value": -1.0, "vary": True, "min": -2.0, "max": 2.0},
            "fwhml": {"value": 0.1, "vary": True, "min": 0.01, "max": 0.5},
        },
    },
]


def _mock_notebook(
    components: list[dict[str, object]] = _SIMPLE_COMPONENTS,
) -> MagicMock:
    """Return a MagicMock that behaves like a SpectraFitNotebook for export tests."""
    nb = MagicMock(spec=SpectraFitNotebook)
    nb.args_to_config.return_value = UnifiedFittingConfig(components=components)
    return nb


class TestExportConfigToml:
    """Tests for SpectraFitNotebook.export_config_toml."""

    @pytest.mark.unit
    def test_creates_toml_file(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        assert dest.exists()

    @pytest.mark.unit
    def test_toml_is_valid_v2_format(self, tmp_path: Path) -> None:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        with dest.open("rb") as fh:
            data = tomllib.load(fh)
        assert "components" in data, "Must use v2 'components' key"
        assert "fitting" not in data, "v1 'fitting' key must not be present"

    @pytest.mark.unit
    def test_toml_validates_through_unified_config(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        cfg = SpectraFitNotebook.load_cli_config(dest)
        assert isinstance(cfg, UnifiedFittingConfig)

    @pytest.mark.unit
    def test_components_count_matches_peaks(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        cfg = SpectraFitNotebook.load_cli_config(dest)
        assert len(cfg.components) == 2

    @pytest.mark.unit
    def test_roundtrip_preserves_component_identity(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        cfg = SpectraFitNotebook.load_cli_config(dest)
        assert [(component.id, component.model) for component in cfg.components] == [
            ("p1", "gaussian"),
            ("p2", "lorentzian"),
        ]

    @pytest.mark.unit
    def test_roundtrip_preserves_canonical_context_and_conf_interval(
        self,
        tmp_path: Path,
    ) -> None:
        config = UnifiedFittingConfig(
            components=_SIMPLE_COMPONENTS,
            column={"x": "energy_ev", "y": "rixs_a"},
            context=FittingContext(mode=FittingMode.GLOBAL, n_datasets=3),
            conf_interval=ConfIntervalConfig(sigmas=[1.0, 2.0], maxiter=25),
            preprocessing=PreprocessingConfig(
                energy_start=280.0,
                energy_stop=295.0,
                shift=0.25,
                smooth=3,
                oversampling=True,
            ),
        )
        nb = _mock_notebook()
        nb.args_to_config.return_value = config
        dest = tmp_path / "fit.toml"

        SpectraFitNotebook.export_config_toml(nb, dest)
        loaded = SpectraFitNotebook.load_cli_config(dest)

        assert loaded.column.x == "energy_ev"
        assert loaded.column.y == "rixs_a"
        assert loaded.context.mode == FittingMode.GLOBAL
        assert loaded.context.n_datasets == 3
        assert isinstance(loaded.conf_interval, ConfIntervalConfig)
        assert loaded.conf_interval.sigmas == [1.0, 2.0]
        assert loaded.conf_interval.maxiter == 25
        assert loaded.preprocessing == config.preprocessing

    @pytest.mark.unit
    def test_raises_if_file_exists_without_force(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        dest.write_text("existing content")
        with pytest.raises(FileExistsError, match="already exists"):
            SpectraFitNotebook.export_config_toml(nb, dest)

    @pytest.mark.unit
    def test_force_true_overwrites(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        dest.write_text("old content")
        SpectraFitNotebook.export_config_toml(nb, dest, force=True)
        assert dest.stat().st_size > 0

    @pytest.mark.unit
    def test_accepts_string_path(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = str(tmp_path / "fit.toml")
        SpectraFitNotebook.export_config_toml(nb, dest)
        assert Path(dest).exists()


class TestLoadCliConfig:
    """Tests for SpectraFitNotebook.load_cli_config (classmethod)."""

    @pytest.mark.unit
    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            SpectraFitNotebook.load_cli_config(tmp_path / "nonexistent.toml")

    @pytest.mark.unit
    def test_raises_on_invalid_yaml_payload(self, tmp_path: Path) -> None:
        bad = tmp_path / "config.yaml"
        bad.write_text("key: value")
        with pytest.raises(
            Exception,
            match=r"validation error|Extra inputs are not permitted",
        ):
            SpectraFitNotebook.load_cli_config(bad)

    @pytest.mark.unit
    def test_loads_valid_toml(self, tmp_path: Path) -> None:
        from spectrafit.cli._types import OutputFormatEnum
        from spectrafit.cli.commands.scaffolding import _build_config
        from spectrafit.cli.commands.scaffolding import _write_config

        toml_path = tmp_path / "config.toml"
        _write_config(_build_config([(1, "voigt")]), toml_path, OutputFormatEnum.TOML)
        cfg = SpectraFitNotebook.load_cli_config(toml_path)
        assert isinstance(cfg, UnifiedFittingConfig)
        assert len(cfg.components) == 1
        assert cfg.components[0].model == "voigt"

    @pytest.mark.unit
    def test_loads_valid_json(self, tmp_path: Path) -> None:
        from spectrafit.cli._types import OutputFormatEnum
        from spectrafit.cli.commands.scaffolding import _build_config
        from spectrafit.cli.commands.scaffolding import _write_config

        json_path = tmp_path / "config.json"
        _write_config(
            _build_config([(1, "gaussian")]), json_path, OutputFormatEnum.JSON
        )
        cfg = SpectraFitNotebook.load_cli_config(json_path)
        assert isinstance(cfg, UnifiedFittingConfig)
        assert len(cfg.components) == 1

    @pytest.mark.unit
    def test_accepts_path_object_and_string(self, tmp_path: Path) -> None:
        from spectrafit.cli._types import OutputFormatEnum
        from spectrafit.cli.commands.scaffolding import _build_config
        from spectrafit.cli.commands.scaffolding import _write_config

        toml_path = tmp_path / "cfg.toml"
        _write_config(
            _build_config([(1, "gaussian")]), toml_path, OutputFormatEnum.TOML
        )
        # Path object
        cfg1 = SpectraFitNotebook.load_cli_config(toml_path)
        # String path
        cfg2 = SpectraFitNotebook.load_cli_config(str(toml_path))
        assert len(cfg1.components) == len(cfg2.components)

    @pytest.mark.unit
    def test_rebases_relative_infile_against_config_dir(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """\
[data]
infile = "data/spectrum.csv"
x_col = "energy"
y_col = "intensity"

[solver]
method = "leastsq"
max_nfev = 1000
nan_policy = "propagate"
calc_covar = true

[[components]]
id = "p1"
model = "gaussian"

[components.parameters]
amplitude = { value = 1.0, vary = true }
center = { value = 0.0, vary = true }
fwhmg = { value = 0.5, vary = true }
""",
            encoding="utf-8",
        )

        cfg = SpectraFitNotebook.load_cli_config(config_path)

        assert cfg.data is not None
        assert cfg.data.infile == (tmp_path / "data" / "spectrum.csv").resolve()

    @pytest.mark.unit
    def test_load_notebook_config_delegates_to_unified_config_from_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text("placeholder", encoding="utf-8")
        expected = UnifiedFittingConfig(components=_SIMPLE_COMPONENTS)
        captured: dict[str, Path] = {}

        def fake_from_file(
            cls: type[UnifiedFittingConfig],
            path: Path | str,
        ) -> UnifiedFittingConfig:
            del cls
            captured["path"] = Path(path)
            return expected

        monkeypatch.setattr(
            UnifiedFittingConfig,
            "from_file",
            classmethod(fake_from_file),
        )

        loaded = load_notebook_config(config_path)

        assert loaded is expected
        assert captured["path"] == config_path

    @pytest.mark.unit
    def test_load_notebook_config_matches_unified_config_from_file(
        self,
        tmp_path: Path,
    ) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """\
data:
  infile: data/spectrum.csv
  x_col: energy
  y_col: intensity
solver:
  method: leastsq
  max_nfev: 1000
  nan_policy: propagate
  calc_covar: true
components:
  - id: p1
    model: gaussian
    parameters:
      amplitude: { value: 1.0, vary: true }
      center: { value: 0.0, vary: true }
      fwhmg: { value: 0.5, vary: true }
""",
            encoding="utf-8",
        )

        notebook_cfg = load_notebook_config(config_path)
        canonical_cfg = UnifiedFittingConfig.from_file(config_path)

        assert notebook_cfg.model_dump(mode="json") == canonical_cfg.model_dump(
            mode="json"
        )
        assert notebook_cfg.data is not None
        assert (
            notebook_cfg.data.infile == (tmp_path / "data" / "spectrum.csv").resolve()
        )

    @pytest.mark.unit
    def test_loads_valid_yaml(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "config.yaml"
        yaml_path.write_text(
            """\
data:
  infile: spectrum.csv
  x_col: energy
  y_col: intensity
solver:
  method: leastsq
  max_nfev: 1000
  nan_policy: propagate
  calc_covar: true
components:
  - id: p1
    model: gaussian
    parameters:
      amplitude:
        value: 1.0
        vary: true
      center:
        value: 0.0
        vary: true
      fwhmg:
        value: 0.5
        vary: true
""",
            encoding="utf-8",
        )

        cfg = SpectraFitNotebook.load_cli_config(yaml_path)

        assert isinstance(cfg, UnifiedFittingConfig)
        assert cfg.data is not None
        assert cfg.data.infile == (tmp_path / "spectrum.csv").resolve()


@pytest.mark.unit
def test_build_notebook_from_config_uses_canonical_fitting_mode_setter() -> None:
    class NotebookDouble:
        def __init__(self, df: pd.DataFrame, x_column: str, y_column: str) -> None:
            self.df = df
            self.x_column = x_column
            self.y_column = y_column
            self.settings_solver_models = None
            self._fitting_mode = FittingMode.STANDARD

        @property
        def fitting_mode(self) -> FittingMode:
            return self._fitting_mode

        @fitting_mode.setter
        def fitting_mode(self, value: FittingMode) -> None:
            self._fitting_mode = value

        @property
        def global_(self) -> FittingMode:
            return self._fitting_mode

        @global_.setter
        def global_(self, value: FittingMode) -> None:
            msg = "legacy global_ setter should not be used internally"
            raise AssertionError(msg)

    config = UnifiedFittingConfig(
        components=_SIMPLE_COMPONENTS,
        column={"x": "energy", "y": "intensity_a"},
        context=FittingContext(mode=FittingMode.GLOBAL, n_datasets=2),
    )
    notebook = build_notebook_from_config(
        notebook_cls=NotebookDouble,
        df=pd.DataFrame(
            {
                "energy": [0.0],
                "intensity_a": [1.0],
                "intensity_b": [2.0],
            }
        ),
        config=config,
    )

    assert notebook.fitting_mode == FittingMode.GLOBAL


@pytest.mark.unit
def test_build_notebook_from_config_uses_canonical_initial_components_setter() -> None:
    class NotebookDouble:
        def __init__(self, df: pd.DataFrame, x_column: str, y_column: str) -> None:
            self.df = df
            self.x_column = x_column
            self.y_column = y_column
            self.settings_solver_models = None
            self._initial_components: list[object] = []

        @property
        def initial_components(self) -> list[object]:
            return list(self._initial_components)

        @initial_components.setter
        def initial_components(self, value: list[object]) -> None:
            self._initial_components = list(value)

        @property
        def initial_model(self) -> list[object]:
            return []

        @initial_model.setter
        def initial_model(self, value: list[object]) -> None:
            msg = "legacy initial_model setter should not be used internally"
            raise AssertionError(msg)

    config = UnifiedFittingConfig(components=_SIMPLE_COMPONENTS)
    notebook = build_notebook_from_config(
        notebook_cls=NotebookDouble,
        df=pd.DataFrame({"energy": [0.0], "intensity": [1.0]}),
        config=config,
    )

    assert notebook.initial_components == config.components


@pytest.mark.unit
def test_build_notebook_from_config_preserves_canonical_preprocessing_ownership() -> (
    None
):
    config = UnifiedFittingConfig(
        components=_SIMPLE_COMPONENTS,
        column={"x": "energy", "y": "intensity"},
        preprocessing=PreprocessingConfig(
            energy_start=280.0,
            energy_stop=295.0,
            shift=0.5,
            smooth=2,
            oversampling=True,
        ),
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        notebook = build_notebook_from_config(
            notebook_cls=SpectraFitNotebook,
            df=pd.DataFrame({"energy": [0.0, 1.0], "intensity": [1.0, 2.0]}),
            config=config,
        )

    assert notebook.preprocessing_config == config.preprocessing
    assert notebook.preprocessing_config is not config.preprocessing
    assert not [
        warning
        for warning in caught
        if issubclass(warning.category, FutureWarning)
        and "SpectraFitNotebook.initial_model" in str(warning.message)
    ]
    assert notebook.initial_components == config.components
    with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.initial_model"):
        legacy_initial_model = notebook.initial_model
    assert legacy_initial_model == [
        {
            "gaussian": {
                "amplitude": {
                    "value": 1.0,
                    "vary": True,
                    "min": 0.0,
                    "max": 2.0,
                },
                "center": {
                    "value": 0.0,
                    "vary": True,
                    "min": -2.0,
                    "max": 2.0,
                },
                "fwhmg": {
                    "value": 0.1,
                    "vary": True,
                    "min": 0.02,
                    "max": 0.5,
                },
            }
        },
        {
            "lorentzian": {
                "amplitude": {
                    "value": 0.5,
                    "vary": True,
                    "min": 0.0,
                    "max": 2.0,
                },
                "center": {
                    "value": -1.0,
                    "vary": True,
                    "min": -2.0,
                    "max": 2.0,
                },
                "fwhml": {
                    "value": 0.1,
                    "vary": True,
                    "min": 0.01,
                    "max": 0.5,
                },
            }
        },
    ]
    with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.args_pre"):
        projected_args = DataPreProcessingAPI.model_validate(
            notebook.args_pre.model_dump()
        )
    assert projected_args == DataPreProcessingAPI(
        column=["energy", "intensity"],
        energy_start=280.0,
        energy_stop=295.0,
        shift=0.5,
        smooth=2,
        oversampling=True,
    )
    notebook.preprocessing_config.shift = 1.25
    assert notebook.preprocessing_config.shift == pytest.approx(1.25)
    assert config.preprocessing is not None
    assert config.preprocessing.shift == pytest.approx(0.5)
    assert notebook.args_to_config().preprocessing == notebook.preprocessing_config


@pytest.mark.unit
def test_args_to_config_preserves_loaded_global_dataset_count() -> None:
    config = UnifiedFittingConfig(
        components=_SIMPLE_COMPONENTS,
        column={"x": "energy", "y": "intensity_a"},
        context=FittingContext(mode=FittingMode.GLOBAL, n_datasets=3),
    )
    notebook = build_notebook_from_config(
        notebook_cls=SpectraFitNotebook,
        df=pd.DataFrame({"energy": [0.0, 1.0], "intensity_a": [1.0, 2.0]}),
        config=config,
    )
    notebook.initial_model = [
        {
            "gaussian": {
                "amplitude": {
                    "value": 1.0,
                    "vary": True,
                    "min": 0.0,
                    "max": 2.0,
                },
                "center": {
                    "value": 0.0,
                    "vary": True,
                    "min": -2.0,
                    "max": 2.0,
                },
                "fwhmg": {
                    "value": 0.1,
                    "vary": True,
                    "min": 0.02,
                    "max": 0.5,
                },
            }
        }
    ]

    roundtrip = notebook.args_to_config()

    assert notebook.y_columns == ["intensity_a"]
    assert notebook.y_column == "intensity_a"
    assert roundtrip.context.mode == FittingMode.GLOBAL
    assert roundtrip.context.n_datasets == 3
    assert roundtrip.column.y == "intensity_a"


@pytest.mark.unit
def test_build_notebook_from_config_restores_global_y_columns_from_dataframe() -> None:
    df = pd.DataFrame(
        {
            "energy": [0.0, 1.0],
            "intensity_a": [1.0, 2.0],
            "intensity_b": [1.5, 2.5],
            "intensity_c": [2.0, 3.0],
        }
    )
    config = UnifiedFittingConfig(
        components=_SIMPLE_COMPONENTS,
        column={"x": "energy", "y": "intensity_a"},
        context=FittingContext(mode=FittingMode.GLOBAL, n_datasets=3),
    )

    notebook = build_notebook_from_config(
        notebook_cls=SpectraFitNotebook,
        df=df,
        config=config,
    )

    assert notebook.fitting_mode == FittingMode.GLOBAL
    assert notebook.n_datasets == 3
    assert notebook.y_columns == ["intensity_a", "intensity_b", "intensity_c"]
    assert notebook.y_column == ["intensity_a", "intensity_b", "intensity_c"]


@pytest.mark.unit
def test_build_notebook_from_config_rejects_dataframe_dataset_count_drift() -> None:
    df = pd.DataFrame(
        {
            "energy": [0.0, 1.0],
            "intensity_a": [1.0, 2.0],
            "intensity_b": [1.5, 2.5],
            "intensity_c": [2.0, 3.0],
        }
    )
    config = UnifiedFittingConfig(
        components=_SIMPLE_COMPONENTS,
        column={"x": "energy", "y": "intensity_a"},
        context=FittingContext(mode=FittingMode.GLOBAL, n_datasets=2),
    )

    with pytest.raises(
        ValueError,
        match="context\\.n_datasets=2 does not match dataframe y-columns=3",
    ):
        build_notebook_from_config(
            notebook_cls=SpectraFitNotebook,
            df=df,
            config=config,
        )


@pytest.mark.unit
def test_export_load_and_rebuild_preserves_global_notebook_y_column_ownership(
    tmp_path: Path,
) -> None:
    df = pd.DataFrame(
        {
            "energy": [0.0, 1.0],
            "intensity_a": [1.0, 2.0],
            "intensity_b": [1.5, 2.5],
            "intensity_c": [2.0, 3.0],
        }
    )
    notebook = SpectraFitNotebook(
        df=df,
        x_column="energy",
        y_column=["intensity_a", "intensity_b", "intensity_c"],
    )
    notebook.initial_model = [
        {
            "gaussian": {
                "amplitude": {
                    "value": 1.0,
                    "vary": True,
                    "min": 0.0,
                    "max": 2.0,
                },
                "center": {
                    "value": 0.0,
                    "vary": True,
                    "min": -2.0,
                    "max": 2.0,
                },
                "fwhmg": {
                    "value": 0.1,
                    "vary": True,
                    "min": 0.02,
                    "max": 0.5,
                },
            }
        }
    ]

    dest = tmp_path / "fit.toml"

    notebook.export_config_toml(dest)
    loaded = SpectraFitNotebook.load_cli_config(dest)
    rebuilt = SpectraFitNotebook.from_config(df=df, config=loaded)

    assert loaded.context.mode == FittingMode.GLOBAL
    assert loaded.context.n_datasets == 3
    assert loaded.column.y == "intensity_a"
    assert rebuilt.fitting_mode == FittingMode.GLOBAL
    assert rebuilt.n_datasets == 3
    assert rebuilt.y_columns == ["intensity_a", "intensity_b", "intensity_c"]
    assert rebuilt.y_column == ["intensity_a", "intensity_b", "intensity_c"]
    assert rebuilt.initial_components == notebook.initial_components
    with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.initial_model"):
        rebuilt_initial_model = rebuilt.initial_model
    with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.initial_model"):
        notebook_initial_model = notebook.initial_model
    assert rebuilt_initial_model == notebook_initial_model


@pytest.mark.unit
def test_notebook_args_to_config_prefers_canonical_initial_components() -> None:
    class NotebookDouble:
        def __init__(self) -> None:
            self.x_column = "energy"
            self.y_columns = ["intensity"]
            self.fitting_mode = FittingMode.STANDARD
            self.n_datasets = 1
            self.preprocessing_config = PreprocessingConfig()
            self.settings_solver_models = SolverConfig()
            self.initial_components = UnifiedFittingConfig(
                components=_SIMPLE_COMPONENTS
            ).components

        @property
        def initial_model(self) -> list[object]:
            msg = "legacy initial_model fallback should not be used on primary ETL path"
            raise AssertionError(msg)

    notebook = NotebookDouble()
    config = notebook_args_to_config(notebook)

    assert config.components == notebook.initial_components
