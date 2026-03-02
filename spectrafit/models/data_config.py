"""DataConfig — typed configuration for the data loading step.

Replaces the raw ``dict[str, str]`` / ``dict[str, Any]`` that was passed to
:func:`~spectrafit.core.data_loader.load_data`.  All keys consumed by the
loader are now validated Pydantic fields with sensible defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


if TYPE_CHECKING:
    from spectrafit.core.fitting_config import UnifiedFittingConfig


class DataConfig(BaseModel):
    r"""Typed, validated configuration for loading a spectrum data file.

    All fields mirror the keys consumed by
    :func:`~spectrafit.core.data_loader.load_data`.

    Attributes:
        infile: Path to the input data file (CSV / TXT / similar).
        separator: Column separator forwarded to :func:`pandas.read_csv`.
        header: Row index to use as column header (``None`` for no header).
        decimal: Decimal point character.
        comment: Character indicating comment lines; ``None`` disables.
        column: Two column identifiers ``[x_col, y_col]`` used when
            ``global_`` is falsy (single-dataset mode).
        global_: Forwarded global fitting flag; non-zero means *all* columns
            are loaded (no ``usecols`` restriction).

    Examples:
        >>> cfg = DataConfig(infile="spectrum.txt", column=["energy", "intensity"])
        >>> cfg.infile
        PosixPath('spectrum.txt')
        >>> cfg.separator
        '\\s+'
    """

    model_config = ConfigDict(populate_by_name=True)

    infile: Path = Field(..., description="Path to the input data file")
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
    column: list[str] = Field(
        default_factory=list,
        description="[x_col, y_col] column identifiers for single-dataset mode",
    )
    global_: int = Field(
        default=0,
        alias="global",
        description="Fitting mode flag; non-zero loads all columns (no usecols)",
    )

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
            >>> peaks = {"1": {"gaussian": {"amplitude": {"value": 1.0, "vary": True}}}}
            >>> cfg = UnifiedFittingConfig(peaks=peaks)
            >>> dc = DataConfig.from_unified(cfg, "spectrum.txt")
            >>> dc.column
            ['energy', 'intensity']
        """
        resolved_infile = Path(infile) if infile is not None else config.infile
        if resolved_infile is None:
            msg = "infile must be provided either via the argument or config.infile"
            raise ValueError(msg)
        return cls(
            infile=resolved_infile,
            separator=separator if separator is not None else config.separator,
            header=config.header if header is ... else header,
            decimal=decimal if decimal is not None else config.decimal,
            comment=config.comment if comment is ... else comment,
            column=[config.column.x, config.column.y],
            **{"global": int(config.global_)},
        )

    @classmethod
    def from_args_dict(cls, args: dict[str, Any]) -> DataConfig:
        """Construct a :class:`DataConfig` from a legacy args dictionary.

        This provides a bridge from the ``dict[str, Any]`` interface that
        :func:`~spectrafit.core.data_loader.load_data` historically accepted.

        Args:
            args: Legacy argument dictionary with keys ``infile``,
                ``separator``, ``header``, ``decimal``, ``comment``,
                ``column``, ``global_``.

        Returns:
            DataConfig: Validated data loading configuration.
        """
        return cls(
            infile=Path(args["infile"]),
            separator=args.get("separator", r"\s+"),
            header=args.get("header", 0),
            decimal=args.get("decimal", "."),
            comment=args.get("comment"),
            column=list(args.get("column", [])),
            **{"global": int(args.get("global_", 0))},
        )
