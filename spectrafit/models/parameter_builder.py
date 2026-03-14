"""Explicit parameter-builder ownership for solver preparation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from lmfit import Parameters

from spectrafit.api.models_model import DistributionModelAPI
from spectrafit.models.naming import dataset_scoped_name
from spectrafit.models.naming import global_lmfit_param_name
from spectrafit.models.naming import lmfit_param_name
from spectrafit.models.naming import sanitize_component_id


if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

    from numpy.typing import NDArray

    from spectrafit.core.fitting_config import UnifiedFittingConfig
    from spectrafit.models.bundle import CompositeModelBundle
    from spectrafit.models.global_fitting import GlobalFittingConfig

# Minimum datasets needed when applying shared-parameter constraints
_MIN_DATASETS_FOR_SHARING = 2


@dataclass(frozen=True, slots=True)
class PreparedInputData:
    """Prepared numeric input arrays derived from a validated dataframe/config pair."""

    x: NDArray[np.float64]
    data: NDArray[np.float64]
    dataset_count: int


@dataclass(frozen=True, slots=True)
class PreparedModelParameters:
    """Prepared lmfit parameter state ready for solver execution."""

    params: Parameters
    bundle: CompositeModelBundle | None = None
    component_models: dict[str, str] | None = None


@dataclass(frozen=True)
class ReferenceKeys:
    """Reference keys for model fitting — canonical location since v2.0.0."""

    __models__: ClassVar[list[str]] = list(
        DistributionModelAPI.model_json_schema()["properties"].keys(),
    )

    def model_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model: Model name.

        Raises:
            NotImplementedError: If the model is not implemented.
        """
        model_prefix = model.split("_", maxsplit=1)[0]
        if model_prefix not in self.__models__:
            msg = f"{model} is not supported!"
            raise NotImplementedError(msg)


class ParameterBuilder:
    """Build prepared solver inputs and lmfit parameters from validated config."""

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Initialize the parameter builder.

        Args:
            df: DataFrame containing the input data (``x`` and ``data``).
            config: Validated fitting configuration.
        """
        self.config = config
        self._input_data = self.prepare_input_data(df=df, config=config)

    @property
    def x(self) -> NDArray[np.float64]:
        """Return prepared x-values for solver execution."""
        return self._input_data.x

    @property
    def data(self) -> NDArray[np.float64]:
        """Return prepared y-values for solver execution."""
        return self._input_data.data

    @property
    def dataset_count(self) -> int:
        """Return the number of prepared datasets."""
        return self._input_data.dataset_count

    @property
    def bundle(self) -> CompositeModelBundle | None:
        """Return the prepared local-fit bundle when present."""
        return self.build().bundle

    @staticmethod
    def prepare_input_data(
        df: pd.DataFrame,
        config: UnifiedFittingConfig,
    ) -> PreparedInputData:
        """Prepare numeric input arrays from the validated source dataframe."""
        x_values = df[config.x_column].to_numpy()
        if config.context.is_global:
            y_columns = [
                str(column) for column in df.columns if str(column) != config.x_column
            ]
            return PreparedInputData(
                x=x_values,
                data=df[y_columns].to_numpy(),
                dataset_count=len(y_columns),
            )
        return PreparedInputData(
            x=x_values,
            data=df[config.y_column].to_numpy(),
            dataset_count=1,
        )

    def build(self) -> PreparedModelParameters:
        """Build lmfit parameters explicitly from the validated config."""
        if self.config.context.is_global:
            return PreparedModelParameters(
                params=self.define_parameters_global(),
                component_models=self.component_models,
            )
        return self._build_local()

    def __str__(self) -> str:
        """Return the string representation of the built model parameters."""
        return str(self.build().params)

    @property
    def global_fitting_config(self) -> GlobalFittingConfig | None:
        """Return the global fitting config from the unified config."""
        return self.config.global_fitting_config

    def _build_local(self) -> PreparedModelParameters:
        """Build a composite bundle for single-dataset local fitting."""
        bundle = self.config.build_composite_model()
        return PreparedModelParameters(params=bundle.params, bundle=bundle)

    @property
    def component_models(self) -> dict[str, str]:
        """Return the canonical component-id → registry-model mapping."""
        return {
            sanitize_component_id(component.id): component.model
            for component in self.config.components
        }

    def _shared_parameter_aliases(self) -> dict[str, str]:
        """Map raw and canonical shared-parameter tokens to canonical base names."""
        aliases: dict[str, str] = {}
        for component in self.config.components:
            for field_name in component.parameters:
                canonical_name = lmfit_param_name(component.id, field_name)
                aliases[canonical_name] = canonical_name
                aliases[f"{component.id}_{field_name}"] = canonical_name
        return aliases

    def _resolve_shared_parameter_name(self, shared_name: str) -> str:
        """Resolve shared-parameter references to the canonical base name."""
        return self._shared_parameter_aliases().get(shared_name, shared_name)

    def define_parameters_global(self) -> Parameters:
        """Build parameters for canonical global fitting."""
        params = Parameters()
        for dataset_idx in range(self.dataset_count):
            for comp in self.config.components:
                for field_name, fp in comp.parameters.items():
                    param_name = global_lmfit_param_name(
                        comp.id,
                        field_name,
                        dataset_idx + 1,
                    )
                    if dataset_idx == 0 or field_name == "amplitude":
                        params.add(
                            param_name,
                            value=fp.value,
                            min=fp.min,
                            max=fp.max,
                            vary=fp.vary,
                            expr=fp.expr,
                        )
                    else:
                        params.add(
                            param_name,
                            expr=global_lmfit_param_name(comp.id, field_name, 1),
                        )
        self._apply_shared_parameters(params)
        return params

    def _apply_shared_parameters(self, params: Parameters) -> None:
        """Apply shared-parameter constraints from the global-fitting config."""
        if (cfg := self.global_fitting_config) is None:
            return

        for sp in cfg.shared_parameters:
            target_datasets = sp.datasets or list(range(cfg.n_datasets))
            if len(target_datasets) < _MIN_DATASETS_FOR_SHARING:
                continue

            first_ds = target_datasets[0]
            base_name = self._resolve_shared_parameter_name(sp.name)
            source_name = dataset_scoped_name(base_name, first_ds + 1)
            if source_name not in params:
                continue

            expr = sp.constraint_expr or source_name
            for ds_idx in target_datasets[1:]:
                dest_name = dataset_scoped_name(base_name, ds_idx + 1)
                if dest_name in params:
                    params[dest_name].set(expr=expr, vary=False)

    def define_parameters_global_pre(self) -> Parameters:
        """Build parameters for pre-specified global fitting via typed components."""
        params = Parameters()
        for comp in self.config.components:
            for field_name, fp in comp.parameters.items():
                param_name = lmfit_param_name(comp.id, field_name)
                params.add(
                    param_name,
                    value=fp.value,
                    min=fp.min,
                    max=fp.max,
                    vary=fp.vary,
                    expr=fp.expr,
                )
        return params
