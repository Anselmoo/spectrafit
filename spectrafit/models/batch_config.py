"""BatchFittingConfig — parallel multi-spectrum fitting configuration.

Enables fitting multiple spectra in a single call using
``concurrent.futures.ProcessPoolExecutor``.  Each spectrum is described by its
own :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig` so that peak
models can differ between spectra.

Example::

    from spectrafit.models.batch_config import BatchFittingConfig

    batch = BatchFittingConfig.model_validate({
        "workers": 4,
        "configs": [
            {"infile": "s1.csv", "components": [...]},
            {"infile": "s2.csv", "components": [...]},
        ],
    })
    # results: list[FitResult] = batch.run()

.. note::
    ``workers > 1`` requires the calling code to guard with
    ``if __name__ == "__main__":`` on Windows / macOS spawn context.

.. seealso::
    :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig`
    :class:`~spectrafit.models.fit_result.FitResult`
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator


class BatchFittingConfig(BaseModel):
    """Configuration for fitting a batch of spectra in parallel.

    Attributes:
        configs: List of per-spectrum fitting configurations.  Each entry is a
            plain dict that will be validated as
            :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig` at
            run time.  Using plain dicts avoids circular import during model
            construction.
        workers: Number of parallel worker processes.  ``1`` disables
            parallelism (useful for debugging or small batches).
        timeout: Optional per-spectrum timeout in seconds passed to
            ``ProcessPoolExecutor``.  ``None`` means no timeout.
        fail_fast: If ``True``, raise immediately on the first spectrum that
            fails to fit.  If ``False``, collect all results and raise a
            ``BatchFittingError`` at the end with a summary of failures.
    """

    model_config = ConfigDict(extra="forbid")

    configs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of per-spectrum UnifiedFittingConfig dicts",
        min_length=1,
    )
    workers: int = Field(
        default=1,
        ge=1,
        description="Number of parallel worker processes (1 = sequential)",
    )
    timeout: float | None = Field(
        default=None,
        description="Per-spectrum timeout in seconds (None = no limit)",
    )
    fail_fast: bool = Field(
        default=False,
        description="Raise on first failure (True) or collect all failures (False)",
    )

    @field_validator("workers")
    @classmethod
    def _workers_reasonable(cls, v: int) -> int:
        """Cap workers at 64 to avoid accidental resource exhaustion.

        Args:
            v: Requested worker count.

        Returns:
            int: Validated worker count.

        Raises:
            ValueError: If workers > 64.
        """
        _MAX_WORKERS = 64  # noqa: N806
        if v > _MAX_WORKERS:
            msg = f"workers must be ≤ {_MAX_WORKERS}; got {v}"
            raise ValueError(msg)
        return v

    @property
    def n_spectra(self) -> int:
        """Return the number of spectra in the batch.

        Returns:
            int: Length of the configs list.
        """
        return len(self.configs)
