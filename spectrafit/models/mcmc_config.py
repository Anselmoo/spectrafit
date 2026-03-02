"""MCMC configuration for Bayesian posterior sampling via lmfit + emcee.

When ``OptimizerConfig.method = "emcee"`` the solver passes this config to
``lmfit.Minimizer.emcee()`` rather than ``Minimizer.minimize()``.

Example::

    from spectrafit.models.mcmc_config import MCMCConfig
    from spectrafit.core.fitting_config import UnifiedFittingConfig

    cfg = UnifiedFittingConfig.model_validate({
        "optimizer": {"method": "emcee"},
        "mcmc": {"nwalkers": 100, "steps": 1000, "burn": 300, "thin": 5},
        "components": [...],
    })

.. note::
    ``emcee`` must be installed: ``pip install emcee``.
    The ``progress`` field controls the tqdm progress bar; set ``False`` in
    non-interactive / CI environments.

.. seealso::
    `lmfit emcee documentation <https://lmfit.github.io/lmfit-py/fitting.html#lmfit.minimizer.Minimizer.emcee>`_
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class MCMCConfig(BaseModel):
    """Configuration for ``lmfit.Minimizer.emcee`` MCMC sampling.

    All fields map 1-to-1 to ``Minimizer.emcee()`` keyword arguments.

    Attributes:
        nwalkers: Number of ensemble walkers.  Must satisfy ``nwalkers >> nvarys``
            where ``nvarys`` is the number of free parameters.
        steps: Number of MCMC steps (samples per walker after burn-in).
        burn: Number of initial samples to discard (burn-in).
        thin: Thinning factor — keep every *n*-th sample.
        is_weighted: If ``True`` the residuals are weighted by the data
            uncertainties.  If ``False`` an additional ``__lnsigma`` parameter
            is added.
        float_behavior: How walker positions are recorded in
            ``MinimizerResult.flatchain``.  ``"posterior"`` records the
            posterior; ``"chi2"`` records the chi-squared.
        progress: Show tqdm progress bar during sampling.  Set ``False`` in
            CI / non-interactive environments.
        seed: Random seed for reproducibility (``int`` or ``None``).
    """

    model_config = ConfigDict(extra="forbid")

    nwalkers: int = Field(
        default=100,
        ge=2,
        description="Number of ensemble walkers (must be >> nvarys)",
    )
    steps: int = Field(
        default=1000,
        ge=1,
        description="Number of MCMC steps per walker",
    )
    burn: int = Field(
        default=0,
        ge=0,
        description="Number of burn-in samples to discard",
    )
    thin: int = Field(
        default=1,
        ge=1,
        description="Thinning factor (keep every n-th sample)",
    )
    is_weighted: bool = Field(
        default=True,
        description="Weight residuals by data uncertainties",
    )
    float_behavior: str = Field(
        default="posterior",
        description="Walker position recording: 'posterior' or 'chi2'",
    )
    progress: bool = Field(
        default=True,
        description="Show tqdm progress bar (set False in CI)",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )
