"""Configuration models for SpectraFit workflow and output settings.

This module provides Pydantic models for configuring various aspects of the
SpectraFit workflow, including output settings and pipeline configuration.
"""

from __future__ import annotations

from typing import Annotated
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class OutputConfig(BaseModel):
    """Configuration model for output settings.

    This model defines settings related to result output, including file formats,
    paths, and visualization options.

    Attributes:
        outfile: Base filename for exported results (without extension).
        formats: List of output formats to generate (e.g., csv, json, xlsx).
        save_figures: Whether to save plot figures to disk.
        figure_format: Format for saved figures (png, pdf, svg, etc.).
        figure_dpi: DPI resolution for saved figures.
        noplot: Disable interactive plotting if True.
        verbose: Verbosity level (0=silent, 1=table, 2=dict).
        export_residuals: Include residuals in output files.
        export_components: Export individual fit components.
        decimal_places: Number of decimal places for numeric output.

    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
    )

    outfile: Annotated[
        str,
        Field(
            default="spectrafit_results",
            description="Base filename for exported results",
        ),
    ]
    formats: Annotated[
        list[str],
        Field(
            default=["csv"],
            description="Output formats to generate (csv, json, xlsx, etc.)",
        ),
    ]
    save_figures: Annotated[
        bool,
        Field(
            default=False,
            description="Save plot figures to disk",
        ),
    ]
    figure_format: Annotated[
        str,
        Field(
            default="png",
            description="Format for saved figures",
        ),
    ]
    figure_dpi: Annotated[
        int,
        Field(
            default=300,
            ge=72,
            le=600,
            description="DPI resolution for saved figures",
        ),
    ]
    noplot: Annotated[
        bool,
        Field(
            default=False,
            description="Disable interactive plotting",
        ),
    ]
    verbose: Annotated[
        int,
        Field(
            default=1,
            ge=0,
            le=2,
            description="Verbosity level (0=silent, 1=table, 2=dict)",
        ),
    ]
    export_residuals: Annotated[
        bool,
        Field(
            default=True,
            description="Include residuals in output files",
        ),
    ]
    export_components: Annotated[
        bool,
        Field(
            default=True,
            description="Export individual fit components",
        ),
    ]
    decimal_places: Annotated[
        int,
        Field(
            default=6,
            ge=1,
            le=15,
            description="Number of decimal places for numeric output",
        ),
    ]


class PipelineConfig(BaseModel):
    """Configuration model for full workflow pipeline.

    This model combines all configuration aspects for a complete SpectraFit
    workflow, including data input, preprocessing, fitting, and output.

    Attributes:
        infile: Path to input spectra data file.
        input: Path to input parameter file (json, yaml, toml).
        outfile: Base filename for exported results.
        preprocessing: Data preprocessing settings.
        fitting: Fitting algorithm and optimization settings.
        output: Output and visualization settings.
        description: Project metadata and description.
        autopeak: Auto-peak detection settings or False to disable.

    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
    )

    infile: Annotated[
        str,
        Field(
            ...,
            description="Path to input spectra data file",
        ),
    ]
    input: Annotated[
        str,
        Field(
            default="fitting_input.toml",
            description="Path to input parameter file",
        ),
    ]
    outfile: Annotated[
        str,
        Field(
            default="spectrafit_results",
            description="Base filename for exported results",
        ),
    ]
    preprocessing: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="Data preprocessing settings",
        ),
    ]
    fitting: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="Fitting algorithm and optimization settings",
        ),
    ]
    output: Annotated[
        dict[str, Any] | OutputConfig,
        Field(
            default_factory=dict,
            description="Output and visualization settings",
        ),
    ]
    description: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description="Project metadata and description",
        ),
    ]
    autopeak: Annotated[
        dict[str, Any] | bool,
        Field(
            default=False,
            description="Auto-peak detection settings",
        ),
    ]


class CLIConfig(BaseModel):
    """Configuration model for CLI arguments.

    This is an alias/wrapper for CMDModelAPI for consistency in naming.
    It represents all command-line interface arguments in a structured format.

    Note:
        For actual CLI usage, prefer using CMDModelAPI from cmd_model module.
        This model is provided for consistency with the config naming convention.

    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
    )

    # Core file paths
    infile: Annotated[
        str,
        Field(
            ...,
            description="Filename of the spectra data",
        ),
    ]
    outfile: Annotated[
        str,
        Field(
            default="spectrafit_results",
            description="Filename for the export",
        ),
    ]
    input: Annotated[
        str,
        Field(
            default="fitting_input.toml",
            description="Filename for the input parameter file",
        ),
    ]

    # Data preprocessing
    oversampling: Annotated[
        bool,
        Field(
            default=False,
            description="Oversample the spectra by factor of 5",
        ),
    ]
    energy_start: Annotated[
        float | None,
        Field(
            default=None,
            description="Starting energy in eV",
        ),
    ]
    energy_stop: Annotated[
        float | None,
        Field(
            default=None,
            description="Ending energy in eV",
        ),
    ]
    smooth: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            description="Number of smooth points",
        ),
    ]
    shift: Annotated[
        float,
        Field(
            default=0,
            description="Constant applied energy shift",
        ),
    ]
    column: Annotated[
        list[int | str],
        Field(
            default=[0, 1],
            description="Selected columns for energy and intensity",
        ),
    ]

    # File format settings
    separator: Annotated[
        str,
        Field(
            default="\t",
            description="Type of separator",
        ),
    ]
    decimal: Annotated[
        str,
        Field(
            default=".",
            description="Type of decimal separator",
        ),
    ]
    header: Annotated[
        int | None,
        Field(
            default=None,
            description="Selected header for the dataframe",
        ),
    ]
    comment: Annotated[
        str | None,
        Field(
            default=None,
            description="Comment character to skip lines",
        ),
    ]

    # Fitting settings
    global_: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            le=2,
            description="Global fitting mode",
        ),
    ]
    autopeak: Annotated[
        dict[str, Any] | bool,
        Field(
            default=False,
            description="Auto detection of peaks",
        ),
    ]

    # Output settings
    noplot: Annotated[
        bool,
        Field(
            default=False,
            description="Disable plotting",
        ),
    ]
    verbose: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            le=2,
            description="Verbosity level",
        ),
    ]

    # Metadata
    description: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description="Project description and metadata",
        ),
    ]
