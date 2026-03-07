"""Model parameter definition for curve fitting.

This module contains the :class:`ModelParameters` class, moved here from
``spectrafit.models.autopeak`` in v2.0.0 as part of the pipeline refactor.

A re-export shim in ``spectrafit.models.autopeak`` preserves backward
compatibility until v2.1.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from lmfit import Parameters

from spectrafit.api.models_model import DistributionModelAPI
from spectrafit.models.fitting_context import FittingMode


if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

    from numpy.typing import NDArray

    from spectrafit.core.fitting_config import UnifiedFittingConfig
    from spectrafit.models.bundle import CompositeModelBundle
    from spectrafit.models.global_fitting import GlobalFittingConfig

# Minimum datasets needed when applying shared-parameter constraints
_MIN_DATASETS_FOR_SHARING = 2


@dataclass(frozen=True)
class ReferenceKeys:
    """Reference keys for model fitting — canonical location since v2.0.0.

    Previously defined in ``spectrafit.models.autopeak``. The re-export
    shim there will be removed in v2.1.0.
    """

    __models__: ClassVar[list[str]] = list(
        DistributionModelAPI.model_json_schema()["properties"].keys(),
    )

    def model_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model (str): Model name.

        Raises:
            NotImplementedError: If the model is not implemented.

        """
        model_prefix = model.split("_", maxsplit=1)[0]
        if model_prefix not in self.__models__:
            msg = f"{model} is not supported!"
            raise NotImplementedError(msg)


class ModelParameters:
    """Class to define the model parameters."""

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Initialize the model parameters.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (``x`` and ``data``).
            config (UnifiedFittingConfig): Validated fitting configuration.

        """
        self.col_len = df.shape[1] - 1
        self.config = config
        self.params: Parameters = Parameters()
        self._bundle: CompositeModelBundle | None = None
        self.x, self.data = self.df_to_numvalues(df=df, config=config)

    @property
    def bundle(self) -> CompositeModelBundle | None:
        """Return the composite model bundle after parameter definition."""
        return self._bundle

    def df_to_numvalues(
        self,
        df: pd.DataFrame,
        config: UnifiedFittingConfig,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Transform the dataframe to numeric values of ``x`` and ``data``.

        Args:
            df (pd.DataFrame): DataFrame containing the input data.
            config (UnifiedFittingConfig): Validated fitting configuration.

        Returns:
            tuple[NDArray[np.float64], NDArray[np.float64]]: Tuple of ``x`` and
                 ``data`` as numpy arrays.

        """
        if config.global_ == FittingMode.GLOBAL:
            return (
                df[config.column.x].to_numpy(),
                df.loc[:, df.columns != config.column.x].to_numpy(),
            )
        return (df[config.column.x].to_numpy(), df[config.column.y].to_numpy())

    @property
    def return_params(self) -> Parameters:
        """Return the ``Parameters`` object built from the current config.

        Returns:
            Parameters: Model parameters class.

        """
        self.__perform__()
        return self.params

    def __str__(self) -> str:
        """Return the ``string`` representation of the model parameters.

        Returns:
            str: String representation of the model parameters.

        """
        self.__perform__()
        return str(self.params)

    def __perform__(self) -> None:
        """Dispatch to the correct parameter-builder based on :class:`FittingMode`."""
        if self.config.global_ == FittingMode.STANDARD:
            self._build_local()
        elif self.global_fitting_config is not None:
            self.define_parameters_global_pre()
        else:
            self.define_parameters_global()

    @property
    def global_fitting_config(self) -> GlobalFittingConfig | None:
        """Return the :class:`GlobalFittingConfig` from the unified config.

        Returns:
            GlobalFittingConfig | None: Config object, or *None* when absent.
        """
        return self.config.global_fitting_config

    def _build_local(self) -> None:
        """Build a :class:`CompositeModelBundle` for single-dataset local fitting."""
        bundle = self.config.build_composite_model()
        self._bundle = bundle
        self.params = bundle.params

    def define_parameters_global(self) -> None:
        """Build global-fitting parameters via typed :class:`Component` iteration.

        Parameter naming: ``{comp.id}_{field}_{dataset_idx}``
        e.g. ``p1_center_1``, ``p1_amplitude_2``.

        For each dataset beyond the first, shape parameters (everything except
        ``amplitude``) are linked to dataset 1 via ``expr``.  Amplitudes remain
        free across all datasets.
        """
        for dataset_idx in range(self.col_len):
            for comp in self.config.components:
                for field_name, fp in comp.parameters.items():
                    param_name = f"{comp.id}_{field_name}_{dataset_idx + 1}"
                    if dataset_idx == 0 or field_name == "amplitude":
                        self.params.add(
                            param_name,
                            value=fp.value,
                            min=fp.min,
                            max=fp.max,
                            vary=fp.vary,
                            expr=fp.expr,
                        )
                    else:
                        self.params.add(param_name, expr=f"{comp.id}_{field_name}_1")
        self._apply_shared_parameters()

    def _apply_shared_parameters(self) -> None:
        """Apply shared-parameter constraints from :class:`GlobalFittingConfig`.

        When a :class:`GlobalFittingConfig` is present its
        ``shared_parameters`` override the default linking behaviour so
        that callers can specify exactly *which* parameters are shared and
        across *which* datasets.
        """
        cfg = self.global_fitting_config
        if cfg is None:
            return

        for sp in cfg.shared_parameters:
            target_datasets = sp.datasets or list(range(cfg.n_datasets))
            if len(target_datasets) < _MIN_DATASETS_FOR_SHARING:
                continue

            first_ds = target_datasets[0]
            source_name = f"{sp.name}_{first_ds + 1}"
            if source_name not in self.params:
                continue

            expr = sp.constraint_expr or source_name
            for ds_idx in target_datasets[1:]:
                dest_name = f"{sp.name}_{ds_idx + 1}"
                if dest_name in self.params:
                    self.params[dest_name].set(expr=expr, vary=False)

    def define_parameters_global_pre(self) -> None:
        """Build parameters for pre-specified global fitting via :class:`Component`.

        !!! warning "About ``params`` for global fitting"

            ``define_parameters_global_pre`` requires a fully defined
            ``params``-dictionary in the json, toml, or yaml file input:

            1. Number of the spectra must be defined.
            2. Number of the peaks must be defined.
            3. Number of the parameters must be defined.
            4. The parameters must be defined.

        Parameter naming: ``{comp.id}_{field}_{peak_key}``
        where ``peak_key`` encodes the dataset index in the user-supplied input.
        """
        for comp in self.config.components:
            for field_name, fp in comp.parameters.items():
                param_name = f"{comp.id}_{field_name}"
                self.params.add(
                    param_name,
                    value=fp.value,
                    min=fp.min,
                    max=fp.max,
                    vary=fp.vary,
                    expr=fp.expr,
                )
