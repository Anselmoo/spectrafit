"""Shared synthetic truth + materialization surfaces for examples and notebooks."""

from __future__ import annotations

import json

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum
from spectrafit.models.naming import restore_dot_notation
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter


if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd


class SyntheticTruth(BaseModel):
    """Synthetic ground-truth ownership for a reusable scenario."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str
    spectrum: SyntheticSpectrum

    def to_dataframe(
        self,
        *,
        seed: int | None = None,
        energy_col: str = "energy",
        intensity_col: str = "intensity",
    ) -> pd.DataFrame:
        """Render the synthetic spectrum as a dataframe."""
        spectrum = self.spectrum_with_seed(seed)
        return spectrum.to_dataframe(energy_col=energy_col, intensity_col=intensity_col)

    def spectrum_with_seed(self, seed: int | None) -> SyntheticSpectrum:
        """Return the configured spectrum, optionally overriding the seed."""
        if seed is None:
            return self.spectrum.model_copy(deep=True)
        return self.spectrum.model_copy(update={"seed": seed}, deep=True)


class ExampleInputMeta(BaseModel):
    """Typed ``[meta]`` block for committed example configs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str


class ExampleInputData(BaseModel):
    """Typed ``[data]`` block for committed example configs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    infile: str
    x_col: str
    y_col: str
    separator: str

    @classmethod
    def from_config_data(cls, config: UnifiedFittingConfig) -> ExampleInputData:
        """Build the example data block from a canonical config."""
        if config.data is None:
            msg = "Example input config requires a materialized data block."
            raise ValueError(msg)
        return cls(
            infile=str(config.data.infile),
            x_col=config.data.x_col,
            y_col=config.data.y_col,
            separator=config.data.separator,
        )


class ExampleInputSolver(BaseModel):
    """Typed flat ``[solver]`` block for committed example configs."""

    model_config = ConfigDict(extra="allow", frozen=True)

    method: str = "leastsq"
    max_nfev: int | None = None
    nan_policy: str = "propagate"
    calc_covar: bool = True

    @classmethod
    def from_config(cls, config: UnifiedFittingConfig) -> ExampleInputSolver:
        """Build the example solver block from canonical solver models."""
        return cls.model_validate(
            {
                **config.optimizer.model_dump(mode="json", exclude_none=True),
                **config.minimizer.model_dump(mode="json", exclude_none=True),
            }
        )


class ExampleInputParameter(BaseModel):
    """Typed inline parameter payload used by committed example configs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: float
    bounds: list[float]
    vary: bool
    expr: str | None = None

    @classmethod
    def from_parameter(
        cls,
        parameter: FitParameter,
        *,
        known_parameters: dict[str, tuple[str, ...]],
    ) -> ExampleInputParameter:
        """Build the example payload for a canonical fit parameter."""
        expr = parameter.expr
        if isinstance(expr, str):
            expr = restore_dot_notation(expr, known_parameters=known_parameters)
        return cls(
            value=parameter.value,
            bounds=[parameter.min, parameter.max],
            vary=parameter.vary,
            expr=expr,
        )


class ExampleInputComponent(BaseModel):
    """Typed component payload used by committed example configs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    model: str
    parameters: dict[str, ExampleInputParameter]

    @classmethod
    def from_component(
        cls,
        component: Component,
        *,
        known_parameters: dict[str, tuple[str, ...]],
    ) -> ExampleInputComponent:
        """Build the example payload for a canonical component."""
        return cls(
            id=component.id,
            model=component.model,
            parameters={
                param_name: ExampleInputParameter.from_parameter(
                    parameter,
                    known_parameters=known_parameters,
                )
                for param_name, parameter in component.parameters.items()
            },
        )


class ExampleInputConfig(BaseModel):
    """Typed committed example payload owned separately from canonical fit config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "2.0"
    config_type: str = "peak_fit"
    meta: ExampleInputMeta
    data: ExampleInputData
    solver: ExampleInputSolver
    components: list[ExampleInputComponent]


class ScenarioMaterialization(BaseModel):
    """Fit-config and artifact materialization ownership for a scenario."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config: UnifiedFittingConfig
    example_dir: str | None = Field(default=None)
    data_file: str = Field(default="data.csv")
    config_file: str = Field(default="input.toml")
    energy_col: str = Field(default="energy")
    intensity_col: str = Field(default="intensity")
    separator: str = Field(default=",")

    def to_config(self) -> UnifiedFittingConfig:
        """Return an isolated copy of the fitting config."""
        return self.config.model_copy(deep=True)

    def example_input_config(self, *, description: str) -> ExampleInputConfig:
        """Build the typed committed example config from canonical ownership."""
        config = self.to_config()
        known_parameters = {
            component.id: tuple(component.parameters.keys())
            for component in config.components
        }
        return ExampleInputConfig(
            meta=ExampleInputMeta(description=description),
            data=ExampleInputData(
                infile=self.data_file,
                x_col=self.energy_col,
                y_col=self.intensity_col,
                separator=self.separator,
            ),
            solver=ExampleInputSolver.from_config(config),
            components=[
                ExampleInputComponent.from_component(
                    component,
                    known_parameters=known_parameters,
                )
                for component in config.components
            ],
        )

    def example_input_payload(self, *, description: str) -> dict[str, object]:
        """Render the committed example input payload from the canonical config."""
        return self.example_input_config(description=description).model_dump(
            mode="json",
            exclude_none=True,
        )

    def example_input_toml(self, *, description: str) -> str:
        """Render the committed example input TOML with human-friendly inline parameters."""
        payload = self.example_input_config(description=description)
        solver = payload.solver.model_dump(mode="python", exclude_none=True)

        lines = [
            _render_toml_assignment("schema_version", payload.schema_version),
            _render_toml_assignment("config_type", payload.config_type),
            "",
            "[meta]",
            _render_toml_assignment("description", payload.meta.description),
            "",
            "[data]",
            _render_toml_assignment("infile", payload.data.infile),
            _render_toml_assignment("x_col", payload.data.x_col),
            _render_toml_assignment("y_col", payload.data.y_col),
            _render_toml_assignment("separator", payload.data.separator),
            "",
            "[solver]",
        ]
        lines.extend(
            _render_toml_assignment(key, solver[key])
            for key in _ordered_keys(
                solver,
                preferred=("method", "max_nfev", "nan_policy", "calc_covar"),
            )
        )

        for component in payload.components:
            lines.extend(
                (
                    "",
                    "[[components]]",
                    _render_toml_assignment("id", component.id),
                    _render_toml_assignment("model", component.model),
                    "",
                    "[components.parameters]",
                )
            )
            for parameter_name, parameter_payload in component.parameters.items():
                lines.append(
                    _render_toml_assignment(
                        parameter_name,
                        parameter_payload.model_dump(mode="python", exclude_none=True),
                    )
                )

        return "\n".join(lines) + "\n"

    def write_example_artifacts(
        self,
        *,
        root: Path,
        truth: SyntheticTruth,
        seed: int | None = None,
    ) -> None:
        """Materialize committed example artifacts for a scenario."""
        if self.example_dir is None:
            msg = "Scenario does not define an example_dir for committed artifacts."
            raise ValueError(msg)

        example_dir = root / self.example_dir
        example_dir.mkdir(parents=True, exist_ok=True)

        truth.to_dataframe(
            seed=seed,
            energy_col=self.energy_col,
            intensity_col=self.intensity_col,
        ).to_csv(example_dir / self.data_file, index=False)

        (example_dir / self.config_file).write_text(
            self.example_input_toml(description=truth.description),
            encoding="utf-8",
        )


class SyntheticScenario(BaseModel):
    """Reusable synthetic scenario composed from truth and materialization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    truth: SyntheticTruth
    materialization: ScenarioMaterialization

    @property
    def name(self) -> str:
        """Backward-compatible scenario name accessor."""
        return self.truth.name

    @property
    def description(self) -> str:
        """Backward-compatible scenario description accessor."""
        return self.truth.description

    @property
    def spectrum(self) -> SyntheticSpectrum:
        """Backward-compatible synthetic spectrum accessor."""
        return self.truth.spectrum

    @property
    def config(self) -> UnifiedFittingConfig:
        """Backward-compatible fit config accessor."""
        return self.materialization.config

    @property
    def example_dir(self) -> str | None:
        """Backward-compatible committed example directory accessor."""
        return self.materialization.example_dir

    def to_dataframe(
        self,
        *,
        seed: int | None = None,
        energy_col: str = "energy",
        intensity_col: str = "intensity",
    ) -> pd.DataFrame:
        """Render the synthetic spectrum as a dataframe."""
        return self.truth.to_dataframe(
            seed=seed,
            energy_col=energy_col,
            intensity_col=intensity_col,
        )

    def to_config(self) -> UnifiedFittingConfig:
        """Return an isolated copy of the fitting config."""
        return self.materialization.to_config()

    def spectrum_with_seed(self, seed: int | None) -> SyntheticSpectrum:
        """Return the configured spectrum, optionally overriding the seed."""
        return self.truth.spectrum_with_seed(seed)

    def example_input_payload(self) -> dict[str, object]:
        """Render the committed example config from the canonical materialization."""
        return self.materialization.example_input_payload(description=self.description)

    def example_input_config(self) -> ExampleInputConfig:
        """Render the committed example config as a typed model."""
        return self.materialization.example_input_config(description=self.description)

    def example_input_toml(self) -> str:
        """Render the committed example config as formatted TOML text."""
        return self.materialization.example_input_toml(description=self.description)

    def write_example_artifacts(self, *, root: Path, seed: int | None = None) -> None:
        """Write committed example artifacts from a single scenario definition."""
        self.materialization.write_example_artifacts(
            root=root,
            truth=self.truth,
            seed=seed,
        )


def _parameter(
    value: float,
    *,
    lower_bound: float,
    upper_bound: float,
    vary: bool = True,
    expr: str | None = None,
) -> FitParameter:
    """Create a canonical fit parameter for synthetic scenario configs."""
    return FitParameter(
        value=value,
        min=lower_bound,
        max=upper_bound,
        vary=vary,
        expr=expr,
    )


def _component(
    component_id: str,
    model: str,
    **parameters: FitParameter,
) -> Component:
    """Create a canonical component for synthetic scenario configs."""
    return Component(id=component_id, model=model, parameters=parameters)


def _ordered_keys(
    payload: dict[str, object],
    *,
    preferred: tuple[str, ...],
) -> tuple[str, ...]:
    """Return keys with preferred entries first while preserving remaining order."""
    ordered = [key for key in preferred if key in payload]
    ordered.extend(key for key in payload if key not in preferred)
    return tuple(ordered)


def _render_toml_assignment(key: str, value: object) -> str:
    """Render a TOML key/value assignment."""
    return f"{key} = {_render_toml_value(value)}"


def _render_toml_value(value: object) -> str:
    """Render supported TOML values for committed example configs."""
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, list):
        return f"[{', '.join(_render_toml_value(item) for item in value)}]"
    if isinstance(value, dict):
        rendered_items = ", ".join(
            f"{item_key} = {_render_toml_value(item_value)}"
            for item_key, item_value in value.items()
        )
        return f"{{ {rendered_items} }}"

    msg = f"Unsupported TOML value type for examples: {type(value)!r}"
    raise TypeError(msg)


def _scenario_config(
    *components: Component,
    minimizer: dict[str, object] | None = None,
    optimizer: dict[str, object] | None = None,
) -> UnifiedFittingConfig:
    """Create a canonical fitting config for a synthetic scenario."""
    return UnifiedFittingConfig(
        components=[component.model_copy(deep=True) for component in components],
        minimizer=minimizer or {},
        optimizer=optimizer or {},
    )


def _scenario(
    *,
    name: str,
    description: str,
    spectrum: SyntheticSpectrum,
    config: UnifiedFittingConfig,
    example_dir: str | None = None,
) -> SyntheticScenario:
    """Build a composed synthetic scenario from separated ownership models."""
    return SyntheticScenario(
        truth=SyntheticTruth(
            name=name,
            description=description,
            spectrum=spectrum,
        ),
        materialization=ScenarioMaterialization(
            config=config,
            example_dir=example_dir,
        ),
    )


def _starter_notebook_scenario() -> SyntheticScenario:
    return _scenario(
        name="starter-notebook",
        description="Synthetic Gaussian + Lorentzian notebook walkthrough.",
        spectrum=SyntheticSpectrum(
            x_min=-5.0,
            x_max=5.0,
            num_points=200,
            noise_level=0.02,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 0.8, "center": 0.5, "fwhmg": 0.4},
                ),
                PeakDefinition(
                    model="lorentzian",
                    params={"amplitude": 0.5, "center": -1.0, "fwhml": 0.3},
                ),
            ],
            seed=42,
        ),
        config=_scenario_config(
            _component(
                "p1",
                "pseudovoigt",
                amplitude=_parameter(0.8, lower_bound=0.0, upper_bound=2.0),
                center=_parameter(0.5, lower_bound=-3.0, upper_bound=3.0),
                fwhmg=_parameter(0.4, lower_bound=0.05, upper_bound=2.0),
                fwhml=_parameter(0.3, lower_bound=0.05, upper_bound=2.0),
            ),
            _component(
                "p2",
                "lorentzian",
                amplitude=_parameter(0.5, lower_bound=0.0, upper_bound=2.0),
                center=_parameter(-1.0, lower_bound=-3.0, upper_bound=3.0),
                fwhml=_parameter(0.3, lower_bound=0.05, upper_bound=2.0),
            ),
            minimizer={"nan_policy": "propagate"},
            optimizer={"max_nfev": 2000, "method": "leastsq"},
        ),
    )


def _basic_example_scenario() -> SyntheticScenario:
    return _scenario(
        name="basic",
        description="Single Gaussian peak with a flat linear background.",
        example_dir="basic",
        spectrum=SyntheticSpectrum(
            x_min=-2.0,
            x_max=2.0,
            num_points=200,
            noise_level=0.02,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.4},
                ),
                PeakDefinition(
                    model="linear",
                    params={"slope": 0.0, "intercept": 0.02},
                ),
            ],
            seed=42,
        ),
        config=_scenario_config(
            _component(
                "peak1",
                "gaussian",
                amplitude=_parameter(1.0, lower_bound=0.0, upper_bound=3.0),
                center=_parameter(0.0, lower_bound=-1.0, upper_bound=1.0),
                fwhmg=_parameter(0.4, lower_bound=0.05, upper_bound=1.5),
            ),
            _component(
                "bg",
                "linear",
                slope=_parameter(0.0, lower_bound=-0.2, upper_bound=0.2, vary=False),
                intercept=_parameter(0.02, lower_bound=0.0, upper_bound=0.5),
            ),
            minimizer={"nan_policy": "propagate", "calc_covar": True},
            optimizer={"max_nfev": 500, "method": "leastsq"},
        ),
    )


def _two_peak_constrained_scenario() -> SyntheticScenario:
    return _scenario(
        name="two-peak-constrained",
        description="Gaussian + pseudo-Voigt example with cross-component constraints.",
        example_dir="two-peak-constrained",
        spectrum=SyntheticSpectrum(
            x_min=-2.0,
            x_max=2.0,
            num_points=200,
            noise_level=0.02,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 1.0, "center": -0.5, "fwhmg": 0.3},
                ),
                PeakDefinition(
                    model="pseudovoigt",
                    params={
                        "amplitude": 0.8,
                        "center": 0.5,
                        "fwhmg": 0.25,
                        "fwhml": 0.25,
                    },
                ),
                PeakDefinition(
                    model="linear",
                    params={"slope": 0.0, "intercept": 0.02},
                ),
            ],
            seed=42,
        ),
        config=_scenario_config(
            _component(
                "p1",
                "gaussian",
                amplitude=_parameter(1.0, lower_bound=0.0, upper_bound=3.0),
                center=_parameter(-0.5, lower_bound=-2.0, upper_bound=0.0),
                fwhmg=_parameter(0.3, lower_bound=0.05, upper_bound=1.0),
            ),
            _component(
                "p2",
                "pseudovoigt",
                amplitude=_parameter(0.8, lower_bound=0.0, upper_bound=3.0),
                center=_parameter(
                    0.5,
                    lower_bound=0.0,
                    upper_bound=2.0,
                    vary=False,
                    expr="p1.center + 1.0",
                ),
                fwhmg=_parameter(0.25, lower_bound=0.05, upper_bound=1.0),
                fwhml=_parameter(
                    0.25,
                    lower_bound=0.05,
                    upper_bound=1.0,
                    vary=False,
                    expr="p2.fwhmg",
                ),
            ),
            _component(
                "bg",
                "linear",
                slope=_parameter(0.0, lower_bound=-0.5, upper_bound=0.5, vary=False),
                intercept=_parameter(0.02, lower_bound=0.0, upper_bound=0.2),
            ),
            minimizer={"nan_policy": "propagate", "calc_covar": True},
            optimizer={"max_nfev": 1000, "method": "leastsq"},
        ),
    )


def _curved_background_scenario() -> SyntheticScenario:
    return _scenario(
        name="curved-background",
        description="Single Gaussian peak on a curved quadratic background.",
        example_dir="curved-background",
        spectrum=SyntheticSpectrum(
            x_min=-3.0,
            x_max=3.0,
            num_points=240,
            noise_level=0.015,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 1.1, "center": 0.35, "fwhmg": 0.45},
                ),
                PeakDefinition(
                    model="polynom2",
                    params={
                        "coefficient0": 0.08,
                        "coefficient1": -0.03,
                        "coefficient2": 0.02,
                    },
                ),
            ],
            seed=42,
        ),
        config=_scenario_config(
            _component(
                "peak1",
                "gaussian",
                amplitude=_parameter(1.1, lower_bound=0.0, upper_bound=2.5),
                center=_parameter(0.35, lower_bound=-0.5, upper_bound=1.0),
                fwhmg=_parameter(0.45, lower_bound=0.1, upper_bound=1.0),
            ),
            _component(
                "bg",
                "polynom2",
                coefficient0=_parameter(0.08, lower_bound=0.0, upper_bound=0.2),
                coefficient1=_parameter(-0.03, lower_bound=-0.1, upper_bound=0.1),
                coefficient2=_parameter(0.02, lower_bound=0.0, upper_bound=0.08),
            ),
            minimizer={"nan_policy": "propagate", "calc_covar": True},
            optimizer={"max_nfev": 800, "method": "leastsq"},
        ),
    )


def _peak_plus_edge_scenario() -> SyntheticScenario:
    return _scenario(
        name="peak-plus-edge",
        description="Pseudo-Voigt peak riding on a smooth erf edge and constant offset.",
        example_dir="peak-plus-edge",
        spectrum=SyntheticSpectrum(
            x_min=-3.5,
            x_max=3.5,
            num_points=280,
            noise_level=0.012,
            peaks=[
                PeakDefinition(
                    model="pseudovoigt",
                    params={
                        "amplitude": 0.9,
                        "center": 0.65,
                        "fwhmg": 0.35,
                        "fwhml": 0.3,
                    },
                ),
                PeakDefinition(
                    model="erf",
                    params={"amplitude": 0.4, "center": -0.3, "sigma": 0.45},
                ),
                PeakDefinition(
                    model="constant",
                    params={"amplitude": 0.06},
                ),
            ],
            seed=42,
        ),
        config=_scenario_config(
            _component(
                "peak1",
                "pseudovoigt",
                amplitude=_parameter(0.9, lower_bound=0.0, upper_bound=2.0),
                center=_parameter(0.65, lower_bound=0.0, upper_bound=1.5),
                fwhmg=_parameter(0.35, lower_bound=0.1, upper_bound=1.0),
                fwhml=_parameter(0.3, lower_bound=0.1, upper_bound=1.0),
            ),
            _component(
                "edge",
                "erf",
                amplitude=_parameter(0.4, lower_bound=0.0, upper_bound=1.0),
                center=_parameter(-0.3, lower_bound=-1.0, upper_bound=0.5),
                sigma=_parameter(0.45, lower_bound=0.1, upper_bound=1.2),
            ),
            _component(
                "bg",
                "constant",
                amplitude=_parameter(0.06, lower_bound=0.0, upper_bound=0.2),
            ),
            minimizer={"nan_policy": "propagate", "calc_covar": True},
            optimizer={"max_nfev": 1200, "method": "leastsq"},
        ),
    )


_SCENARIOS: dict[str, SyntheticScenario] = {
    scenario.name: scenario
    for scenario in (
        _starter_notebook_scenario(),
        _basic_example_scenario(),
        _two_peak_constrained_scenario(),
        _curved_background_scenario(),
        _peak_plus_edge_scenario(),
    )
}

_EXAMPLE_SCENARIO_NAMES: tuple[str, ...] = (
    "basic",
    "two-peak-constrained",
    "curved-background",
    "peak-plus-edge",
)


def get_synthetic_scenario(name: str) -> SyntheticScenario:
    """Return a shared synthetic scenario by name."""
    try:
        return _SCENARIOS[name].model_copy(deep=True)
    except KeyError as exc:
        msg = f"Unknown synthetic scenario '{name}'. Available: {sorted(_SCENARIOS)}"
        raise ValueError(msg) from exc


def iter_example_scenarios() -> tuple[SyntheticScenario, ...]:
    """Return the scenarios that back committed examples/ fixtures."""
    return tuple(get_synthetic_scenario(name) for name in _EXAMPLE_SCENARIO_NAMES)
