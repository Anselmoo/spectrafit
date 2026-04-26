"""Solver option normalization helpers for Jupyter notebook fitting."""

from __future__ import annotations

from spectrafit.api.models_model import ConfIntervalAPI
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import SolverConfig
from spectrafit.models.solver_config import normalize_conf_interval_value


def normalize_conf_interval(
    conf_interval: bool | ConfIntervalAPI | ConfIntervalConfig,
) -> ConfIntervalConfig | None:
    """Normalize confidence interval settings for the solver layer.

    Args:
        conf_interval: Raw confidence interval settings from notebook/config API.

    Returns:
        Typed model when enabled, ``None`` when disabled.
    """
    if isinstance(conf_interval, ConfIntervalAPI):
        return normalize_conf_interval_value(
            conf_interval.model_dump(exclude_none=True),
        )
    return normalize_conf_interval_value(conf_interval)


def resolve_solver_options(
    conf_interval: bool | ConfIntervalAPI | ConfIntervalConfig,
    solver_settings: SolverConfig | None,
    config: UnifiedFittingConfig | None,
) -> tuple[ConfIntervalConfig | None, SolverConfig | None]:
    """Resolve solver options from explicit params and optional unified config.

    Args:
        conf_interval: Direct confidence-interval argument from notebook API.
        solver_settings: Direct solver-settings argument from notebook API.
        config: Optional unified config override source.

    Returns:
        Normalized confidence model (or ``None``) and resolved solver settings.
    """
    if config is not None:
        conf_interval = config.conf_interval
        return (
            normalize_conf_interval(conf_interval),
            SolverConfig(
                minimizer=config.minimizer,
                optimizer=config.optimizer,
            ),
        )

    return normalize_conf_interval(conf_interval), solver_settings


def apply_solver_settings(
    current_settings: SolverConfig,
    solver_settings: SolverConfig | None,
) -> SolverConfig:
    """Apply solver settings while preserving existing notebook defaults.

    Args:
        current_settings: Current notebook solver settings.
        solver_settings: New settings model, or ``None`` to keep current.

    Returns:
        SolverConfig: Effective solver settings after applying overrides.
    """
    if solver_settings is None:
        return current_settings
    return solver_settings.model_copy(deep=True)
