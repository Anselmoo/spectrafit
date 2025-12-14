"""Fit command for SpectraFit CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any

import typer

from spectrafit.api.cmd_model import CMDModelAPI
from spectrafit.cli._types import DecimalEnum
from spectrafit.cli._types import GlobalFitEnum
from spectrafit.cli._types import SeparatorEnum
from spectrafit.cli._types import VerboseEnum
from spectrafit.models.builtin import SolverModels
from spectrafit.plotting import PlotSpectra
from spectrafit.report import PrintingResults
from spectrafit.report import PrintingStatus
from spectrafit.core import PostProcessing
from spectrafit.core import PreProcessing
from spectrafit.core import SaveResult
from spectrafit.core import load_data
from spectrafit.core import read_input_file


if TYPE_CHECKING:
    from collections.abc import MutableMapping

    import pandas as pd


__status__ = PrintingStatus()


def fit(
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
) -> None:
    """Fit spectra data using SpectraFit.

    This command performs spectral fitting on the provided data file using the
    parameters specified in the input configuration file.
    """
    # Convert column to proper format
    if column is None:
        column = ["0", "1"]
    else:
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
    _run_fitting_workflow(args=args_dict)


def _run_fitting_workflow(args: dict[str, Any]) -> None:
    """Run the interactive fitting workflow.

    Args:
        args: The input file arguments as a dictionary.
    """
    __status__.welcome()
    while True:
        __status__.start()

        # Process arguments with input file
        processed_args = _extract_args_from_input(args)

        df_result, processed_args = _fitting_routine(args=processed_args)
        PlotSpectra(df=df_result, args=processed_args)()
        SaveResult(df=df_result, args=processed_args)()

        __status__.end()

        again = typer.confirm("Would you like to fit again?", default=False)
        if not again:
            __status__.thanks()
            __status__.credits()
            return


def _extract_args_from_input(args: dict[str, Any]) -> dict[str, Any]:
    """Extract and merge command line arguments with input file settings.

    Args:
        args: The command line arguments.

    Raises:
        KeyError: Missing key `minimizer` in `parameters`.
        KeyError: Missing key `optimizer` in `parameters`.

    Returns:
        The merged arguments dictionary.
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


def _fitting_routine(args: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the fitting algorithm.

    Args:
        args: The input file arguments as a dictionary.

    Returns:
        A tuple of DataFrame and dictionary containing fit results.
    """
    df: pd.DataFrame = load_data(args)
    df, args = PreProcessing(df=df, args=args)()
    minimizer, result = SolverModels(df=df, args=args)()
    df, args = PostProcessing(df=df, args=args, minimizer=minimizer, result=result)()
    PrintingResults(args=args, minimizer=minimizer, result=result)()

    return df, args
