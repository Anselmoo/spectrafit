"""SpectraFit, the command line tool for fitting."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any

import typer

from spectrafit.api.cmd_model import CMDModelAPI
from spectrafit.core.pipeline import fitting_routine_pipeline
from spectrafit.models.builtin import SolverModels
from spectrafit.plotting import PlotSpectra
from spectrafit.report import PrintingResults
from spectrafit.report import PrintingStatus
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.tools import SaveResult
from spectrafit.tools import load_data
from spectrafit.tools import read_input_file


if TYPE_CHECKING:
    from collections.abc import MutableMapping

    import pandas as pd


class SeparatorEnum(str, Enum):
    """Enum for separator choices."""

    TAB = "\t"
    COMMA = ","
    SEMICOLON = ";"
    COLON = ":"
    PIPE = "|"
    SPACE = " "
    REGEX = "s+"


class DecimalEnum(str, Enum):
    """Enum for decimal separator choices."""

    DOT = "."
    COMMA = ","


class GlobalFitEnum(int, Enum):
    """Enum for global fitting mode choices."""

    CLASSIC = 0
    AUTO = 1
    CUSTOM = 2


class VerboseEnum(int, Enum):
    """Enum for verbose level choices."""

    SILENT = 0
    TABLE = 1
    DICT = 2


# Create Typer app
app = typer.Typer(
    help="Fast Fitting Program for ascii txt files.",
    epilog="For more information, visit https://anselmoo.github.io/spectrafit/",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        status = PrintingStatus()
        typer.echo(status.version())
        raise typer.Exit


@app.command()
def cli_main(
    infile: Annotated[str, typer.Argument(help="Filename of the spectra data")],
    outfile: Annotated[
        str,
        typer.Option(
            "-o",
            "--outfile",
            help="Filename for the export, default to set to 'spectrafit_results'.",
        ),
    ] = "spectrafit_results",
    input_: Annotated[
        str,
        typer.Option(
            "-i",
            "--input",
            help=(
                "Filename for the input parameter, default to set to 'fitting_input.toml'. "
                "Supported fileformats are: '*.json', '*.yml', '*.yaml', and '*.toml'"
            ),
        ),
    ] = "fitting_input.toml",
    oversampling: Annotated[
        bool,
        typer.Option(
            "-ov",
            "--oversampling",
            help="Oversampling the spectra by using factor of 5; default to False.",
        ),
    ] = False,
    energy_start: Annotated[
        float | None,
        typer.Option(
            "-e0",
            "--energy-start",
            help="Starting energy in eV; default to start of energy; default to None.",
        ),
    ] = None,
    energy_stop: Annotated[
        float | None,
        typer.Option(
            "-e1",
            "--energy-stop",
            help="Ending energy in eV; default to end of energy; default to None.",
        ),
    ] = None,
    smooth: Annotated[
        int,
        typer.Option(
            "-s",
            "--smooth",
            help="Number of smooth points for lmfit; default to 0.",
        ),
    ] = 0,
    shift: Annotated[
        float,
        typer.Option(
            "-sh",
            "--shift",
            help="Constant applied energy shift; default to 0.",
        ),
    ] = 0,
    column: Annotated[
        list[str] | None,
        typer.Option(
            "-c",
            "--column",
            help=(
                "Selected columns for the energy- and intensity-values; default to '0' for "
                "energy (x-axis) and '1' for intensity (y-axis). In case of working with "
                "header, the column should be set to the column names as 'str'; default "
                "to 0 and 1."
            ),
        ),
    ] = None,
    separator: Annotated[
        SeparatorEnum,
        typer.Option(
            "-sep",
            "--separator",
            help="Redefine the type of separator; default to '\\t'.",
        ),
    ] = SeparatorEnum.TAB,
    decimal: Annotated[
        DecimalEnum,
        typer.Option(
            "-dec",
            "--decimal",
            help="Type of decimal separator; default to '.'.",
        ),
    ] = DecimalEnum.DOT,
    header: Annotated[
        int | None,
        typer.Option(
            "-hd",
            "--header",
            help="Selected the header for the dataframe; default to None.",
        ),
    ] = None,
    comment: Annotated[
        str | None,
        typer.Option(
            "-cm",
            "--comment",
            help="Lines with comment characters like '#' should not be parsed; default to None.",
        ),
    ] = None,
    global_: Annotated[
        GlobalFitEnum,
        typer.Option(
            "-g",
            "--global",
            help=(
                "Perform a global fit over the complete dataframe. The options are '0' "
                "for classic fit (default). The option '1' for global fitting with "
                "auto-definition of the peaks depending on the column size and '2' for "
                "self-defined global fitting routines."
            ),
        ),
    ] = GlobalFitEnum.CLASSIC,
    autopeak: Annotated[
        bool,
        typer.Option(
            "-auto",
            "--autopeak",
            help=(
                "Auto detection of peaks in the spectra based on `SciPy`. The position, "
                "height, and width are used as estimation for the `Gaussian` models. "
                "The default option is 'False' for manual peak definition."
            ),
        ),
    ] = False,
    noplot: Annotated[
        bool,
        typer.Option(
            "-np",
            "--noplot",
            help="No plotting the spectra and the fit of `SpectraFit`.",
        ),
    ] = False,
    verbose: Annotated[
        VerboseEnum,
        typer.Option(
            "-vb",
            "--verbose",
            help=(
                "Display the initial configuration parameters and fit results, as a table "
                "'1', as a dictionary '2', or not in the terminal '0'. The default option "
                "is set to 1 for table `printout`."
            ),
        ),
    ] = VerboseEnum.TABLE,
    version: Annotated[
        bool | None,
        typer.Option(
            "-v",
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Display the current version of `SpectraFit`.",
        ),
    ] = None,
) -> None:
    """Run spectrafit from the command line."""
    # Convert column to proper format
    if column is None:
        # Typing expects list[str]; keep defaults as strings so conversion logic
        # below can safely parse numeric column indices with str.isdigit().
        column = ["0", "1"]
    else:
        # Convert to list of strings, parsing integers where applicable
        # This maintains type consistency for mypy while preserving the logic
        column = [
            str(int(c)) if (isinstance(c, str) and c.isdigit()) else str(c)
            for c in column
        ]

    # Build args dictionary with enum values converted to their underlying types
    args_dict = {
        "infile": infile,
        "outfile": outfile,
        "input": input_,
        "oversampling": oversampling,
        "energy_start": energy_start,
        "energy_stop": energy_stop,
        "smooth": smooth,
        "shift": shift,
        "column": column,
        "separator": separator.value,
        "decimal": decimal.value,
        "header": header,
        "comment": comment,
        "global_": global_.value,
        "autopeak": autopeak,
        "noplot": noplot,
        "verbose": verbose.value,
    }

    # Run the fitting routine with the interactive loop
    run_fitting_workflow(args=args_dict)


def run_fitting_workflow(
    args: dict[str, Any],
    status: PrintingStatus | None = None,
) -> None:
    """Run the interactive fitting workflow.

    Args:
        args (Dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.
        status (PrintingStatus, optional): Status printer for output messages.
             If None, creates a new instance. Defaults to None.

    """
    if status is None:
        status = PrintingStatus()

    status.welcome()
    while True:
        status.start()

        # Process arguments with input file
        processed_args = extracted_from_command_line_runner_with_args(args)

        df_result, processed_args = fitting_routine(args=processed_args)
        PlotSpectra(df=df_result, args=processed_args)()
        SaveResult(df=df_result, args=processed_args)()

        status.end()

        again = typer.confirm("Would you like to fit again?", default=False)
        if not again:
            status.thanks()
            status.credits()
            return


def command_line_runner(args: dict[str, Any] | None = None) -> None:
    """Entry point for spectrafit CLI.

    This function maintains backward compatibility and serves as the entry point
    configured in pyproject.toml. It delegates to the Typer app.

    Args:
        args (Dict[str, Any], optional): The input file arguments as a
             dictionary with additional information beyond the command line arguments.
             Defaults to None. If provided, runs in programmatic mode.

    """
    if args is not None:
        # Programmatic mode: args provided directly
        run_fitting_workflow(args=args)
    else:
        # CLI mode: let Typer handle argument parsing
        app()


def extracted_from_command_line_runner_with_args(
    args: dict[str, Any],
) -> dict[str, Any]:
    """Extract and merge command line arguments with input file settings.

    Args:
        args (Dict[str, Any]): The command line arguments.

    Raises:
        KeyError: Missing key `minimizer` in `parameters`.
        KeyError: Missing key `optimizer` in `parameters`.

    Returns:
        Dict[str, Any]: The merged arguments dictionary.

    """
    _args: MutableMapping[str, Any] = read_input_file(args["input"])

    if "settings" in _args:
        for key in _args["settings"]:
            args[key] = _args["settings"][key]
    args = CMDModelAPI(**args).model_dump()
    if "description" in _args["fitting"]:
        args["description"] = _args["fitting"]["description"]
    if "parameters" in _args["fitting"]:
        if "minimizer" in _args["fitting"]["parameters"]:
            args["minimizer"] = _args["fitting"]["parameters"]["minimizer"]
        else:
            msg = "Missing 'minimizer' in 'parameters'!"
            raise KeyError(msg)
        if "optimizer" in _args["fitting"]["parameters"]:
            args["optimizer"] = _args["fitting"]["parameters"]["optimizer"]
        else:
            msg = "Missing key 'optimizer' in 'parameters'!"
            raise KeyError(msg)
        if "report" in _args["fitting"]["parameters"]:
            args["report"] = _args["fitting"]["parameters"]["report"]
        else:
            args["report"] = {
                "show_correl": True,
                "min_correl": 0.1,
                "sort_pars": False,
            }
        if "conf_interval" in _args["fitting"]["parameters"]:
            args["conf_interval"] = _args["fitting"]["parameters"]["conf_interval"]
        else:
            args["conf_interval"] = None

    if "peaks" in _args["fitting"]:
        args["peaks"] = _args["fitting"]["peaks"]
    return args


def fitting_routine(
    args: dict[str, Any],
    use_pipeline: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the fitting algorithm.

    Args:
        args (Dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.
        use_pipeline (bool): If True, use the new pipeline pattern. If False,
             use the legacy sequential approach. Defaults to True.

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Returns a DataFrame and a dictionary,
             which is containing the input data (`x` and `data`), as well as the best
             fit, single contributions of each peak and the corresponding residuum. The
             dictionary contains the raw input data, the best fit, the single
             contributions and the corresponding residuum. Furthermore, the dictionary
             is extended by advanced statistical information of the fit.

    """
    if use_pipeline:
        # Use the new pipeline pattern
        return fitting_routine_pipeline(args)

    # Legacy approach (backward compatibility)
    df: pd.DataFrame = load_data(args)
    df, args = PreProcessing(df=df, args=args)()
    minimizer, result = SolverModels(df=df, args=args)()
    df, args = PostProcessing(df=df, args=args, minimizer=minimizer, result=result)()
    PrintingResults(args=args, minimizer=minimizer, result=result)()

    return df, args


# Re-export CLI app for backward compatibility
# The new CLI with subcommands is available in spectrafit.cli.main
try:
    from spectrafit.cli.main import app as cli_app
except ImportError:
    cli_app = app  # Fall back to original app if cli module not available
