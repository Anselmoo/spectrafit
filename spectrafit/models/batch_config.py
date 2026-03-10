"""BatchFittingConfig — parallel multi-spectrum fitting configuration.

Enables fitting multiple spectra in a single call using
``concurrent.futures.ProcessPoolExecutor``.  Each spectrum is described by its
own `UnifiedFittingConfig` so that peak
models can differ between spectra.

Examples:
    ```python
    from spectrafit.models.batch_config import BatchFittingConfig

    batch = BatchFittingConfig.model_validate({
        "workers": 4,
        "configs": [
            {"infile": "s1.csv", "components": [...]},
            {"infile": "s2.csv", "components": [...]},
        ],
    })
    # results: list[FitResult] = batch.run()
    ```

!!! note
    ``workers > 1`` requires the calling code to guard with
    ``if __name__ == "__main__":`` on Windows / macOS spawn context.

See also `UnifiedFittingConfig` and `FitResult`.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from spectrafit.core.fitting_config import UnifiedFittingConfig


class BatchFittingConfig(BaseModel):
    """Configuration for fitting a batch of spectra in parallel.

    Attributes:
        configs: List of per-spectrum fitting configurations.  Each entry is
            validated as `UnifiedFittingConfig`
            at construction time via a lazy import to avoid circular dependency.
        workers: Number of parallel worker processes.  ``1`` disables
            parallelism (useful for debugging or small batches).
        timeout: Optional per-spectrum timeout in seconds passed to
            ``ProcessPoolExecutor``.  ``None`` means no timeout.
        fail_fast: If ``True``, raise immediately on the first spectrum that
            fails to fit.  If ``False``, collect all results and raise a
            ``BatchFittingError`` at the end with a summary of failures.
    """

    model_config = ConfigDict(extra="forbid")

    configs: list[UnifiedFittingConfig] = Field(
        default_factory=list,
        description="List of per-spectrum UnifiedFittingConfig instances",
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

    @field_validator("configs", mode="before")
    @classmethod
    def _coerce_configs(cls, v: object) -> list[object]:
        """Coerce plain dicts to ``UnifiedFittingConfig`` instances.

        Args:
            v: Raw list of dicts or ``UnifiedFittingConfig`` instances.

        Returns:
            list[UnifiedFittingConfig]: Validated config instances.
        """
        if not isinstance(v, list):
            return v  # type: ignore[return-value]
        return [
            UnifiedFittingConfig.model_validate(item)
            if isinstance(item, dict)
            else item
            for item in v
        ]

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
        _max_workers = 64
        if v > _max_workers:
            msg = f"workers must be ≤ {_max_workers}; got {v}"
            raise ValueError(msg)
        return v

    @property
    def n_spectra(self) -> int:
        """Return the number of spectra in the batch.

        Returns:
            int: Length of the configs list.
        """
        return len(self.configs)
