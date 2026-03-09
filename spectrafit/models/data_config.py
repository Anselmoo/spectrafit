"""DataConfig — typed configuration for the data loading step.

Replaces the raw ``dict[str, str]`` that was passed to
:func:`~spectrafit.core.data_loader.load_data`.  All keys consumed by the
loader are now validated Pydantic fields with sensible defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode


if TYPE_CHECKING:
    from spectrafit.core.fitting_config import UnifiedFittingConfig


class DataConfig(BaseModel):
    r"""Typed, validated configuration for loading a spectrum data file.

    Maps to the ``[data]`` section in the v2 input TOML::

        [data]
        infile    = "spectrum.csv"
        x_col     = "energy"
        y_col     = "intensity"
        separator = "\t"
        decimal   = "."
        header    = 0

    All fields mirror the keys consumed by
    :func:`~spectrafit.core.data_loader.load_data`.

    Attributes:
        infile: Path to the input data file (CSV / TXT / similar).
        x_col: Column name (or index) for the independent variable (energy axis).
        y_col: Column name (or index) for the dependent variable (intensity).
        separator: Column separator forwarded to :func:`pandas.read_csv`.
        header: Row index to use as column header (``None`` for no header).
        decimal: Decimal point character.
        comment: Character indicating comment lines; ``None`` disables.
        context: Typed fitting context. Non-standard modes load all columns
            (no ``usecols`` restriction).

    Examples:
        >>> cfg = DataConfig(infile="spectrum.txt")
        >>> cfg.x_col
        'energy'
        >>> cfg.y_col
        'intensity'
        >>> cfg.separator
        '\\s+'
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    infile: Path = Field(..., description="Path to the input data file")
    x_col: str = Field(
        default="energy",
        description="Column name (or index) for the x-axis (energy)",
    )
    y_col: str = Field(
        default="intensity",
        description="Column name (or index) for the y-axis (intensity)",
    )
    separator: str = Field(
        default=r"\s+",
        description="Column separator forwarded to pandas.read_csv",
    )
    header: int | None = Field(
        default=0,
        description="Row index to use as column header; None means no header",
    )
    decimal: str = Field(default=".", description="Decimal point character")
    comment: str | None = Field(
        default=None,
        description="Character marking comment lines; None disables comment parsing",
    )
    context: FittingContext = Field(
        default_factory=FittingContext,
        description="Typed fitting context; non-standard modes load all columns.",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_global(cls, raw: object) -> object:
        """Accept legacy ``global``/``global_`` inputs and map to ``context``.

        Args:
            raw: Raw mapping passed to model validation.

        Returns:
            object: Normalized mapping with ``context`` when legacy keys are used.
        """
        if not isinstance(raw, dict):
            return raw
        data: dict[str, object] = dict(raw)
        if "context" in data:
            return data
        legacy = data.pop("global_", data.pop("global", None))
        if legacy is None:
            return data
        if isinstance(legacy, FittingContext):
            data["context"] = legacy
            return data
        if isinstance(legacy, FittingMode):
            data["context"] = FittingContext(mode=legacy)
            return data
        if isinstance(legacy, bool):
            data["context"] = FittingContext.from_global_int(1 if legacy else 0)
            return data
        if isinstance(legacy, int):
            data["context"] = FittingContext.from_global_int(legacy)
            return data
        data["context"] = FittingContext(mode=FittingMode(str(legacy)))
        return data

    @property
    def global_(self) -> int:
        """Legacy int accessor retained for frozen loader compatibility."""
        return self.context.global_int

    @classmethod
    def from_unified(
        cls,
        config: UnifiedFittingConfig,
        infile: str | Path | None = None,
        *,
        separator: str | None = None,
        header: int | None = ...,  # type: ignore[assignment]
        decimal: str | None = None,
        comment: str | None = ...,  # type: ignore[assignment]
    ) -> DataConfig:
        r"""Construct a :class:`DataConfig` from a :class:`UnifiedFittingConfig`.

        All keyword arguments fall back to the corresponding field on *config*
        when left at their sentinel ``...`` / ``None`` default, so callers
        only need to pass overrides.

        Args:
            config: Validated fitting configuration providing column names and
                global fitting mode.
            infile: Path to the data file.  Defaults to ``config.infile`` when
                ``None``.
            separator: Column separator.  Defaults to ``config.separator``.
            header: Header row index.  Defaults to ``config.header``.
            decimal: Decimal character.  Defaults to ``config.decimal``.
            comment: Comment character.  Defaults to ``config.comment``.

        Returns:
            DataConfig: Ready-to-use data loading configuration.

        Raises:
            ValueError: If no ``infile`` can be determined.

        Examples:
            >>> from spectrafit.core.fitting_config import UnifiedFittingConfig
            >>> cfg = UnifiedFittingConfig(components=[{
            ...     "id": "p1",
            ...     "model": "gaussian",
            ...     "parameters": {"amplitude": {"value": 1.0, "vary": True}},
            ... }])
            >>> dc = DataConfig.from_unified(cfg, "spectrum.txt")
            >>> dc.x_col
            'energy'
        """
        resolved_infile = Path(infile) if infile is not None else config.infile
        if resolved_infile is None:
            msg = "infile must be provided either via the argument or config.infile"
            raise ValueError(msg)
        return cls(
            infile=resolved_infile,
            x_col=config.column.x,
            y_col=config.column.y,
            separator=separator if separator is not None else config.separator,
            header=config.header if header is ... else header,
            decimal=decimal if decimal is not None else config.decimal,
            comment=config.comment if comment is ... else comment,
            context=config.context,
        )

    @classmethod
    def from_args_dict(cls, args: dict[str, object]) -> DataConfig:
        """Construct a :class:`DataConfig` from a legacy args dictionary.

        Supports both the old ``column`` list format and the new ``x_col``/``y_col``
        format so that v1→v2 migration scripts can call this transparently.

        Args:
            args: Legacy argument dictionary with keys ``infile``, ``separator``,
                ``header``, ``decimal``, ``comment``, ``column`` (old) or
                ``x_col``/``y_col`` (new), ``global_``.

        Returns:
            DataConfig: Validated data loading configuration.
        """
        col = args.get("column", [])
        x_col = (
            str(col[0])
            if isinstance(col, list) and col
            else str(args.get("x_col", "energy"))
        )
        y_col = (
            str(col[1])
            if isinstance(col, list) and len(col) > 1
            else str(args.get("y_col", "intensity"))
        )
        return cls(
            infile=Path(str(args["infile"])),
            x_col=x_col,
            y_col=y_col,
            separator=str(args.get("separator", r"\s+")),
            header=int(str(args["header"])) if args.get("header") is not None else None,
            decimal=str(args.get("decimal", ".")),
            comment=str(args["comment"]) if args.get("comment") is not None else None,
            context=FittingContext.from_global_int(int(str(args.get("global_", 0)))),
        )
