"""SpectraFit, the command line tool for fitting."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any

import typer

from spectrafit.api.cmd_model import CMDModelAPI
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


__status__ = PrintingStatus()

# Create Typer app
app = typer.Typer(
    help="Fast Fitting Program for ascii txt files.",
    epilog="For more information, visit https://anselmoo.github.io/spectrafit/",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        typer.echo(__status__.version())
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
        str,
        typer.Option(
            "-sep",
            "--separator",
            help="Redefine the type of separator; default to '\\t'.",
        ),
    ] = "\t",
    decimal: Annotated[
        str,
        typer.Option(
            "-dec",
            "--decimal",
            help="Type of decimal separator; default to '.'.",
        ),
    ] = ".",
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
        int,
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
    ] = 0,
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
        int,
        typer.Option(
            "-vb",
            "--verbose",
            help=(
                "Display the initial configuration parameters and fit results, as a table "
                "'1', as a dictionary '2', or not in the terminal '0'. The default option "
                "is set to 1 for table `printout`."
            ),
        ),
    ] = 1,
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
        # Try to convert to int if possible (only call isdigit on strings)
        column = [int(c) if (isinstance(c, str) and c.isdigit()) else c for c in column]

    # Validate choices
    if separator not in ["\t", ",", ";", ":", "|", " ", "s+"]:
        typer.echo(f"Error: Invalid separator '{separator}'", err=True)
        raise typer.Exit(1)

    if decimal not in [".", ","]:
        typer.echo(f"Error: Invalid decimal '{decimal}'", err=True)
        raise typer.Exit(1)

    if global_ not in [0, 1, 2]:
        typer.echo(f"Error: Invalid global value '{global_}'", err=True)
        raise typer.Exit(1)

    if verbose not in [0, 1, 2]:
        typer.echo(f"Error: Invalid verbose value '{verbose}'", err=True)
        raise typer.Exit(1)

    # Build args dictionary
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
        "separator": separator,
        "decimal": decimal,
        "header": header,
        "comment": comment,
        "global_": global_,
        "autopeak": autopeak,
        "noplot": noplot,
        "verbose": verbose,
    }

    # Run the fitting routine with the interactive loop
    run_fitting_workflow(args=args_dict)


def run_fitting_workflow(args: dict[str, Any]) -> None:
    """Run the interactive fitting workflow.

    Args:
        args (Dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.

    """
    __status__.welcome()
    while True:
        __status__.start()

        # Process arguments with input file
        processed_args = extracted_from_command_line_runner_with_args(args)

        df_result, processed_args = fitting_routine(args=processed_args)
        PlotSpectra(df=df_result, args=processed_args)()
        SaveResult(df=df_result, args=processed_args)()

        __status__.end()

        again = input("Would you like to fit again ...? Enter y/n: ").lower()
        if again == "n":
            __status__.thanks()
            __status__.credits()
            return
        if again == "y":
            continue
        __status__.yes_no()


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


def extracted_from_command_line_runner() -> dict[str, Any]:
    """Extract the input commands from the terminal.

    This function is deprecated and kept only for backward compatibility.
    It should not be called when using Typer.

    Raises:
        RuntimeError: This function should not be called with Typer.

    Returns:
        Dict[str, Any]: The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    """
    _msg = (
        "extracted_from_command_line_runner() is deprecated. "
        "The Typer CLI handles argument parsing automatically."
    )
    raise RuntimeError(_msg)


def fitting_routine(args: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the fitting algorithm.

    Args:
        args (Dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Returns a DataFrame and a dictionary,
             which is containing the input data (`x` and `data`), as well as the best
             fit, single contributions of each peak and the corresponding residuum. The
             dictionary contains the raw input data, the best fit, the single
             contributions and the corresponding residuum. Furthermore, the dictionary
             is extended by advanced statistical information of the fit.

    """
    df: pd.DataFrame = load_data(args)
    df, args = PreProcessing(df=df, args=args)()
    minimizer, result = SolverModels(df=df, args=args)()
    df, args = PostProcessing(df=df, args=args, minimizer=minimizer, result=result)()
    PrintingResults(args=args, minimizer=minimizer, result=result)()

    return df, args
