import argparse
import json
import pprint
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import toml
import yaml
from lmfit import Minimizer, Parameters, conf_interval, fit_report, minimize
from matplotlib.ticker import AutoMinorLocator
from matplotlib.widgets import Cursor
from scipy.special import erf, wofz

from spectrafit import __version__


@dataclass(frozen=True)
class Constants:
    log2 = np.log(2.0)
    sq2pi = np.sqrt(2.0 * np.pi)
    sqpi = np.sqrt(np.pi)
    sq2 = np.sqrt(2.0)
    sig2fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0))


pp = pprint.PrettyPrinter(indent=4)


def get_args() -> dict:
    parser = argparse.ArgumentParser(
        description="Fast Fitting Program for ascii txt files."
    )
    parser.add_argument("infile", type=Path, help="Filename of the specta data")
    parser.add_argument(
        "-o",
        "--outfile",
        type=Path,
        help="Filename for the export, default to set to input name.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default="fitting_input.toml",
        help=(
            "Filename for the input parameter, default to set to 'fitting_input.toml'."
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
        ),
    )
    parser.add_argument(
        "-ov",
        "--oversampling",
        action="store_true",
        default=False,
        help="Oversampling the spectra by using factor of 5; default to False.",
    )
    parser.add_argument(
        "-disp",
        action="store_true",
        default=False,
        help="Hole or splitted Table on the Screen; default to 'hole'.",
    )
    parser.add_argument(
        "-e0",
        "--energy_start",
        type=float,
        default=None,
        help="Starting energy in eV; default to start of energy.",
    )
    parser.add_argument(
        "-e1",
        "--energy_stop",
        type=float,
        default=None,
        help="Ending energy in eV; default to end of energy.",
    )
    parser.add_argument(
        "-s",
        "--smooth",
        type=int,
        default=None,
        help="Number of smooth points for lmfit; default to 0.",
    )
    parser.add_argument(
        "-sh",
        "--shift",
        type=float,
        default=None,
        help="Constant applied energy shift; default to 0.0.",
    )
    parser.add_argument(
        "-c",
        "--column",
        nargs=2,
        type=int,
        default=[0, 1],
        help=(
            "Selected columns for the energy- and intensity-values; default to 0 for"
            " energy (x-axis) and 1 for intensity (y-axis)."
        ),
    )
    parser.add_argument(
        "-sep",
        "--seperator",
        type=str,
        default="\t",
        choices=["\t", ",", ";", ":", "|", " ", "s+"],
        help="Redefine the type of seperator; default to '\t'.",
    )
    parser.add_argument(
        "-dec",
        "--decimal",
        type=str,
        default=".",
        choices=[".", ","],
        help="Type of decimal seperator; default to '.'.",
    )
    parser.add_argument(
        "-hd",
        "--header",
        type=int,
        default=None,
        help="Selected the header for the dataframe; default to None.",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Display the current version of `spectrafit`.",
        action="store_true",
    )
    parser.add_argument(
        "-vb",
        "--verbose",
        help="Display the initial configuration parameters as a dictionary.",
        action="store_true",
    )
    return vars(parser.parse_args())


def read_input_file(fname: Path) -> dict:
    """Read the input file.

    Read the input file as `toml`, `json`, or `yaml` files
    and return as a dictionary.

    Args:
        fname (Path): Name of the input file.

    Raises:
        TypeError: If the input file is not supported.

    Returns:
        dict: Table of the input file to a dictionary.
    """
    if fname.suffix == ".toml":
        with open(fname, "r") as f:
            return toml.load(fname)
    elif fname.suffix == ".json":
        with open(fname, "r") as f:
            return json.load(f)
    elif fname.suffix == ".yaml":
        with open(fname, "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    else:
        raise TypeError(
            f"Input file {fname} has not supported file format."
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
        )


def command_line_runner(args: dict = None) -> None:

    if not args:
        args = extracted_from_command_line_runner()
    if args["version"]:
        print(f"Currently used verison is: {__version__}")
        return
    if args["verbose"]:
        print("Input Parameter:\n")
        pp.pprint(args)
    try:
        df = pd.read_csv(
            args["infile"],
            sep=args["seperator"],
            header=args["header"],
            usecols=args["column"],
            dtype=np.float64,
            decimal=args["decimal"],
        )
        df_stats = df.describe(percentiles=np.arange(0.1, 1, 0.1)).to_dict()
        df_original = df.to_dict()
    except ValueError as exc:
        print(f"Error: {exc} -> Dataframe contains non numeric data!")
        return
    if args["verbose"]:
        print("\nStatistic:\n")
        pp.pprint(df_stats)

    while True:
        again = input("Would you like to fit ...? Enter y/n: ").lower()
        if again == "n":
            print("Thanks for using ...!")
            return
        elif again == "y":
            print("Lets start fitting ...")
            fitting_routine(df=df, args=args)
        else:
            print('You should enter either "y" or "n".')


def extracted_from_command_line_runner() -> dict:
    result = get_args()
    _args = read_input_file(result["input"])
    if "settings" in _args.keys():
        for key in _args["settings"].keys():
            result[key] = _args["settings"][key]
    if "description" in _args["fitting"].keys():
        result["description"] = _args["fitting"]["description"]
    if "parameters" in _args["fitting"].keys():
        if "minimizer" in _args["fitting"]["parameters"].keys():
            result["minimizer"] = _args["fitting"]["parameters"]["minimizer"]
        if "optimizer" in _args["fitting"]["parameters"].keys():
            result["optimizer"] = _args["fitting"]["parameters"]["optimizer"]
    if "peaks" in _args["fitting"].keys():
        result["peaks"] = _args["fitting"]["peaks"]

    return result


def fitting_routine(df: pd.DataFrame, args: dict) -> None:

    # try:

    df = energy_range(df=df, args=args)
    df = energy_shift(df=df, args=args)
    df = oversampling(df=df, args=args)
    df = intensity_smooth(df=df, args=args)

    params = get_parameters(args=args)
    minner = Minimizer(
        model,
        params,
        fcn_args=(df[args["column"][0]].values, df[args["column"][1]].values),
        **args["minimizer"],
    )
    #
    # try:
    result = minner.minimize(**args["optimizer"])
    # print(result.params.dumps())
    print(
        result.nfev,
        result.nvarys,
        result.nfree,
        result.residual,
        result.ndata,
        result.chisqr,
        result.redchi,
        result.aic,
        result.bic,
        result.var_names,
        # result.covar,
        result.init_vals,
        result.call_kws,
    )

    # print(result.errorbars)

    # print(dict(vars(result)))
    # except ValueError:
    #    print "Input error in guess.parm"
    # final = y + result.residual
    # print result.init_fit
    # report_fit(result)
    # plot(x, y, final, result, args)
    # except IOError:
    #    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    #    print "!!!!No Inputfile guess.parm for Fits!!!!"
    #    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    #
    #    pass


def get_parameters(args: dict) -> dict:
    """[summary]

    Args:
        args (dict): [description]

    Returns:
        dict: [description]
    """
    params = Parameters()

    for key_1, value_1 in args["peaks"].items():
        for key_2, value_2 in value_1.items():
            for key_3, value_3 in value_2.items():
                params.add(f"{key_2}_{key_3}_{key_1}", **value_3)
    return params


def model(params: dict, x: np.array, data):
    """[summary]

    Args:
        params (dict): [description]
        x (np.array): [description]
        data ([type]): [description]

    Returns:
        [type]: [description]
    """
    val = 0.0
    for mode in params:
        mode = mode.lower()
        if mode.split("_")[0] in [
            "gaussian",
            "lorentzian",
            "voigt",
            "pseudovoigt",
            "exponential",
            "linear",
            "constant",
            "erf",
            "atan",
            "log",
        ]:
            pass
        else:
            raise SystemExit(f"{mode} is not supported")
    for mode in params:
        mode = mode.lower()
        if "gaussian" in mode:
            if "center" in mode:
                center = params[mode]
            if "amplitude" in mode:
                amplitude = params[mode]
            if "fwhm_gaussian" in mode:
                fwhm_gaussian = params[mode]
                val += gaussian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_gaussian,
                )
        if "lorentzian" in mode:
            if "center" in mode:
                center = params[mode]
            if "amplitude" in mode:
                amplitude = params[mode]
            if "fwhm_lorentzian" in mode:
                fwhm_lorentzian = params[mode]
                val += lorentzian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_lorentzian,
                )
        if "voigt" in mode:
            if "center" in mode:
                center = params[mode]
            if "fwhm" in mode:
                fwhm = params[mode]
            if "gamma" in mode:
                gamma = params[mode]
                val += voigt(
                    x=x,
                    center=center,
                    fwhm=fwhm,
                    gamma=gamma,
                )
        if "pseudovoigt" in mode:
            if "center" in mode:
                center = params[mode]
            if "amplitude" in mode:
                amplitude = params[mode]
            if "fwhm_gaussian" in mode:
                fwhm_gaussian = params[mode]
            if "fwhm_lorentzian" in mode:
                fwhm_lorentzian = params[mode]
                val += pseudovoigt(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm_g=fwhm_gaussian,
                    fwhm_l=fwhm_lorentzian,
                )
        if "exponential" in mode:
            if "amplitude" in mode:
                amplitude = params[mode]
            if "decay" in mode:
                decay = params[mode]
            if "intercept" in mode:
                intercept = params[mode]
                val += exponential(
                    x=x,
                    amplitude=amplitude,
                    decay=decay,
                    intercept=intercept,
                )
        if "power" in mode:
            if "amplitude" in mode:
                amplitude = params[mode]
            if "exponent" in mode:
                exponent = params[mode]
            if "intercept" in mode:
                intercept = params[mode]
                val += powerlaw(
                    x=x,
                    amplitude=amplitude,
                    exponent=exponent,
                    intercept=intercept,
                )
        if "linear" in mode:
            if "slope" in mode:
                slope = params[mode]
            if "intercept" in mode:
                intercept = params[mode]
                val += linear(x=x, slope=slope, intercept=intercept)
        if "constant" in mode and "amplitude" in mode:
            amplitude = params[mode]
            val += constant(x=x, amplitude=amplitude)
        if "erf" in mode:
            if "center" in mode:
                center = params[mode]
            if "sigma" in mode:
                sigma = params[mode]
            if "amplitude" in mode:
                amplitude = params[mode]
                val += step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    form="erf",
                )
        if "atan" in mode:
            if "center" in mode:
                center = params[mode]
            if "sigma" in mode:
                sigma = params[mode]
            if "amplitude" in mode:
                amplitude = params[mode]
                val += step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    form="atan",
                )
        if "log" in mode:
            if "center" in mode:
                center = params[mode]
            if "sigma" in mode:
                sigma = params[mode]
            if "amplitude" in mode:
                amplitude = params[mode]
                val += step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    form="logistic",
                )
    return val - data


def energy_range(df: pd.DataFrame, args: dict) -> pd.DataFrame:
    """
    Select the energy range for fitting.
    """

    _e0 = args["energy_start"]
    _e1 = args["energy_stop"]

    if _e0 and _e1:
        return df[(df[args["column"][0]] >= _e0) & (df[args["column"][0]] <= _e1)]
    elif _e0:
        return df[df[args["column"][0]] >= _e0]
    elif _e1:
        return df[df[args["column"][0]] <= _e1]
    return df


def energy_shift(df: pd.DataFrame, args: dict) -> pd.DataFrame:
    """
    Shift the energy axis by a given value.
    """
    if args["shift"]:
        df[args["column"][0]] = df[args["column"][0]] - args["shift"]
        return df
    return df


def oversampling(df: pd.DataFrame, args: dict) -> pd.DataFrame:
    if args["oversampling"]:
        x_values = np.linspace(
            df[args["column"][0]].min(), df[args["column"][0]].max(x), 5 * df.shape[0]
        )
        return pd.DataFrame(
            {
                args["column"][0]: x_values,
                args["column"][1]: np.interp(
                    x_values, df[args["column"][0]].values, df[args["column"][1]].values
                ),
            }
        )
    return df


def intensity_smooth(df: pd.DataFrame, args: dict) -> pd.DataFrame:

    if args["smooth"]:
        box = np.ones(args["smooth"]) / args["smooth"]
        df[args["column"][1]] = np.convolve(
            df[args["column"][1]].values, box, mode="same"
        )
        return df
    return df


def plot(x, y, final, result, args):
    filename = args.outfile
    # try:
    fig, ax = plt.subplots()
    out = [x, y, final, y - final]
    # tmp = open(filename+'_Export.txt','w+')

    df = panda_h()
    print("--------------")
    print("|Fit-Results:|")
    print("--------------")
    # printh(tmp)

    index = 1
    for i, mode in enumerate(result.params):
        mode = mode.lower()
        if "gaus" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
            if "fwg" in mode:
                fwg = result.params[mode]
                val = np.nan_to_num(gaussian(x, amp, cen, fwg))
                plt.plot(x, val, color="C9", ls=":")
                out.append(val)
                # Exporting
                model = "Gaussian"
                res = np.array([val, x])

                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=cen,
                    amp=amp,
                    fwg=fwg,
                    fwl=None,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=None,
                    slp=None,
                    con=None,
                    sig=None,
                )
                index += 1
                # printf(tmp,x, val,'Gaussian',index,cen,amp,fwg,0,0,0,0,0,0,0,0)

        if "lorz" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
            if "fwl" in mode:
                fwl = result.params[mode]
                val = np.nan_to_num(lorentzian(x, amp, cen, fwl))
                plt.plot(x, val, color="C9", ls=":")
                out.append(val)
                # Exporting
                model = "Lorentzian"
                res = np.array([val, x])

                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=cen,
                    amp=amp,
                    fwg=None,
                    fwl=fwl,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=None,
                    slp=None,
                    con=None,
                    sig=None,
                )
                index += 1
                # printf(tmp,x, val,'Lorentzian',index,cen,amp,0,fwl,0,0,0,0,0,0,0)

        if "voigt" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "fwh" in mode:
                fwh = result.params[mode]
            if "gam" in mode:
                gam = result.params[mode]
                val = np.nan_to_num(voigt(x, cen, fwh, gam))
                plt.plot(x, val, color="C9", ls=":")
                out.append(val)
                # Exporting
                model = "Voigt"
                res = np.array([val, x])
                df = panda_e(
                    df,
                    model,
                    res,
                    cen=cen,
                    amp=None,
                    fwg=None,
                    fwl=None,
                    fwh=fwh,
                    gam=gam,
                    dec=None,
                    exp=None,
                    slp=None,
                    con=None,
                    sig=None,
                )
                index += 1
                # printf(tmp,x, val,'Voigt',index,cen,amp,0,0,fwh=fwh,gam=gamma,0,0,0,0,0)

        if "pseudovoigt" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
            if "fwg" in mode:
                fwg = result.params[mode]
            if "fwl" in mode:
                fwl = result.params[mode]
                val = np.nan_to_num(pseudovoigt(x, amp, cen, fwg, fwl))
                plt.plot(x, val, color="C9", ls=":")
                out.append(val)
                # Exporting
                model = "Pseudo-Voigt"
                res = np.array([val, x])
                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=cen,
                    amp=amp,
                    fwg=fwg,
                    fwl=fwl,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=None,
                    slp=None,
                    con=None,
                    sig=None,
                )
                index += 1
                # printf(tmp,x, val,'PS-Voigt',index,cen,amp,fwg,fwl,0,0,0,0,0,0,0)

        if "expo" in mode:
            if "dec" in mode:
                dec = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
            if "con" in mode:
                con = result.params[mode]

                val = np.nan_to_num(exponential(x, amp, dec, con))
                plt.plot(x, val, color="C3", ls="-.")
                out.append(val)
                # Exporting
                model = "Exponential"
                res = np.array([val, x])
                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=None,
                    amp=amp,
                    fwg=None,
                    fwl=None,
                    fwh=None,
                    gam=None,
                    dec=dec,
                    exp=None,
                    slp=None,
                    con=con,
                    sig=None,
                )
                index += 1
                # printf(tmp,x, val,'Exponential',index,0,amp,0,0,0,0,dec=dec,0,0,con,0)

        if "powr" in mode:
            if "ord" in mode:
                exp = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
            if "con" in mode:
                con = result.params[mode]

                val = np.nan_to_num(powerlaw(x, amp, exp, con))
                plt.plot(x, val, color="C3", ls="-.")
                out.append(val)
                # Exporting
                model = "Power"
                res = np.array([val, x])

                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=None,
                    amp=amp,
                    fwg=None,
                    fwl=None,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=exp,
                    slp=None,
                    con=con,
                    sig=None,
                )
                # printf(tmp,x, val,'Power',index,0,amp,0,0,0,0,0,exp=exp,0,con,0)

        if "linr" in mode:
            if "slp" in mode:
                slp = result.params[mode]
            if "con" in mode:
                con = result.params[mode]
                val = np.nan_to_num(linear(x, slp, con))
                plt.plot(x, val, color="C3", ls="-.")
                out.append(val)
                # Exporting
                model = "Linear"
                res = np.array([val, x])
                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=None,
                    amp=None,
                    fwg=None,
                    fwl=None,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=None,
                    slp=slp,
                    con=con,
                    sig=None,
                )
                index += 1
                # printf(tmp,x, val,'Linear',index,0,0,0,0,0,0,0,0,slp,con,0)

        if "cons" in mode and "con" in mode:
            con = result.params[mode]
            val = np.nan_to_num(const(x, con))
            plt.plot(x, val, color="C3", ls="-.")
            out.append(val)
            # Exporting
            model = "Constant"
            res = np.array([val, x])
            df = panda_e(
                df,
                model,
                index,
                res,
                cen=None,
                amp=None,
                fwg=None,
                fwl=None,
                fwh=None,
                gam=None,
                dec=None,
                exp=None,
                slp=None,
                con=con,
                sig=None,
            )
            index += 1
            # printf(tmp,x, val,'Constant',index,0,0,0,0,0,0,0,0,0,con,0)

        # elif 'stpl' in mode:
        #    if 'cen' in mode: cen  = params[mode]
        #    elif 'sig' in mode:
        #        sig   = params[mode]
        #        val += np.nan_to_num(step(x, cen, sig, form='linear'))
        if "erf" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "sig" in mode:
                sig = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]

                val = np.nan_to_num(step(x, amp, cen, sig, form="erf"))
                plt.plot(x, val, color="C6", ls="--")
                out.append(val)
                # Exporting
                model = "Error-Step"
                res = np.array([val, x])
                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=cen,
                    amp=amp,
                    fwg=None,
                    fwl=None,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=None,
                    slp=None,
                    con=None,
                    sig=sig,
                )
                index += 1
                # printf(tmp,x, val,'Error-Fnc',index,cen,amp,0,0,0,0,0,0,0,0,sig=sig)

        if "atan" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "sig" in mode:
                sig = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
                val = np.nan_to_num(step(x, amp, cen, sig, form="atan"))
                plt.plot(x, val, color="C6", ls="--")
                out.append(val)
                # Exporting
                model = "ATangH-Step"
                res = np.array([val, x])
                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=cen,
                    amp=amp,
                    fwg=None,
                    fwl=None,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=None,
                    slp=None,
                    con=None,
                    sig=sig,
                )
                index += 1
                # printf(tmp,x, val,'ATangH-Fnc',index,cen,amp,0,0,0,0,0,0,0,0,sig=sig)

        if "log" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "sig" in mode:
                sig = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
                val = np.nan_to_num(step(x, amp, cen, sig, form="atan"))
                plt.plot(x, val, color="C6", ls="--")
                out.append(val)
                # Exporting
                model = "Log-Step"
                res = np.array([val, x])

                df = panda_e(
                    df,
                    model,
                    index,
                    res,
                    cen=cen,
                    amp=amp,
                    fwg=None,
                    fwl=None,
                    fwh=None,
                    gam=None,
                    dec=None,
                    exp=None,
                    slp=None,
                    con=None,
                    sig=sig,
                )
                index += 1
                # printf(tmp,x, val,'Log-Fnc',index,cen,amp,0,0,0,0,0,0,0,0,sig=sig)

    pd.set_option(
        "expand_frame_repr", args.disp, "display.float_format", lambda x: "%.3f" % x
    )
    # dates = pd.date_range('1/1/2000', periods=7)

    print(df)
    excle(filename + "_Export.xlsx", df)
    # majorLocator = MultipleLocator(20)
    # majorFormatter = FormatStrFormatter('%d')
    # minorLocator = MultipleLocator(5)

    # fig, ax = plt.subplots()

    # ax.xaxis.set_major_locator(majorLocator)
    # ax.xaxis.set_major_formatter(majorFormatter)

    # for the minor ticks, use no labels; default NullFormatter

    ax.xaxis.set_minor_locator(AutoMinorLocator())

    plt.plot(x, y, color="C7", marker="+")
    plt.plot(x, final, color="C1", ls="-.")
    plt.tick_params(which="both", width=2)
    plt.tick_params(which="major", length=7)
    plt.tick_params(which="minor", length=4, color="0.75")
    fig.savefig(filename + "_Fit.pdf", format="pdf")
    cursor = Cursor(ax, useblit=True, color="C0", linewidth=1)
    plt.show()
    # tmp.close()
    np.savetxt(filename + "_Fit.txt", np.transpose(out), delimiter="\t")
    # high_res(x,final,result,filename)
    # except:
    #    pass


def panda_h():
    f_array = np.array([], dtype=np.float)
    s_array = np.array([], dtype=np.str)
    return pd.DataFrame(
        {
            "Model": s_array,
            "Energy": f_array,
            "stderr Energy": f_array,
            "Amp": f_array,
            "stderr Amp": f_array,
            "Area": f_array,  #'stderr Area': f_array,
            "FWHM (GAUSSIAN)": f_array,
            "stderr FWHM (GAUSSIAN)": f_array,
            "FWHM (LORENTZ)": f_array,
            "stderr FWHM (LORENTZ)": f_array,
            "FWHM (VOIGT)": f_array,
            "stderr FWHM (VOIGT)": f_array,
            "Fraction": f_array,
            "stderr Fraction": f_array,
            "Decay": f_array,
            "stderr Decay": f_array,
            "Power": f_array,
            "stderr Power": f_array,
            "Slope": f_array,
            "stderr Slope": f_array,
            "Constant": f_array,
            "stderr Constant": f_array,
            "Signum": f_array,
            "stderr Signum": f_array,
        }
    )


def panda_e(
    file,
    model,
    index,
    data,
    cen=None,
    amp=None,
    fwg=None,
    fwl=None,
    fwh=None,
    gam=None,
    dec=None,
    exp=None,
    slp=None,
    con=None,
    sig=None,
):
    area = np.trapz(data[0], data[1])

    if cen is None:
        cen_fit, cen_error = np.array([0.0]), np.array([0.0])
    else:
        cen_fit, cen_error = np.round(cen._val, 8), np.array([0.0])
    if amp is None:
        amp_fit, amp_error = np.array([0.0]), np.array([0.0])
    else:
        amp_fit, amp_error = np.round(amp._val, 8), np.array([0.0])
    if fwg is None:
        fwg_fit, fwg_error = np.array([0.0]), np.array([0.0])
    else:
        fwg_fit, fwg_error = np.round(fwg._val, 8), np.array([0.0])
    if fwl is None:
        fwl_fit, fwl_error = np.array([0.0]), np.array([0.0])
    else:
        fwl_fit, fwl_error = np.round(fwl._val, 8), np.array([0.0])
    if fwh is None:
        fwh_fit, fwh_error = np.array([0.0]), np.array([0.0])
    else:
        fwh_fit, fwh_error = np.round(fwh._val, 8), np.array([0.0])
    if gam is None:
        gam_fit, gam_error = np.array([0.0]), np.array([0.0])
    else:
        gam_fit, gam_error = np.round(gam._val, 8), np.array([0.0])
    if dec is None:
        dec_fit, dec_error = np.array([0.0]), np.array([0.0])
    else:
        dec_fit, dec_error = np.round(dec._val, 8), np.array([0.0])
    if exp is None:
        exp_fit, exp_error = np.array([0.0]), np.array([0.0])
    else:
        exp_fit, exp_error = np.round(exp._val, 8), np.array([0.0])
    if slp is None:
        slp_fit, slp_error = np.array([0.0]), np.array([0.0])
    else:
        slp_fit, slp_error = np.round(slp._val, 8), np.array([0.0])
    if con is None:
        con_fit, con_error = np.array([0.0]), np.array([0.0])
    else:
        con_fit, con_error = np.round(con._val, 8), np.array([0.0])
    if sig is None:
        sig_fit, sig_error = np.array([0.0]), np.array([0.0])
    else:
        sig_fit, sig_error = np.round(sig._val, 8), np.array([0.0])
    # if not (cen  is None): cen_fit, cen_error  = np.round(cen._val,8) , np.round(cen.stderr,8)
    # if not (amp  is None): amp_fit, amp_error  = np.round(amp._val,8) , np.round(amp.stderr,8)
    # if not (fwg  is None): fwg_fit, fwg_error  = np.round(fwg._val,8) , np.round(fwg.stderr,8)
    # if not (fwl  is None): fwl_fit, fwl_error  = np.round(fwl._val,8) , np.round(fwl.stderr,8)
    # if not (fwh  is None): fwh_fit, fwh_error  = np.round(fwh._val,8) , np.round(fwh.stderr,8)
    # if not (gam  is None): gam_fit, gam_error  = np.round(gam._val,8) , np.round(gam.stderr,8)
    # if not (dec  is None): dec_fit, dec_error  = np.round(dec._val,8) , np.round(dec.stderr,8)
    # if not (exp  is None): exp_fit, exp_error  = np.round(exp._val,8) , np.round(exp.stderr,8)
    # if not (slp  is None): slp_fit, slp_error  = np.round(slp._val,8) , np.round(slp.stderr,8)
    # if not (con  is None): con_fit, con_error  = np.round(con._val,8) , np.round(con.stderr,8)
    # if not (sig  is None): sig_fit, sig_error  = np.round(sig._val,8) , np.round(sig.stderr,8)

    tmp = pd.DataFrame(
        {
            "Model": model,
            "Energy": cen_fit,
            "stderr Energy": cen_error,
            "Amp": amp_fit,
            "stderr Amp": amp_error,
            "Area": np.round(area, 8),  #'stderr Area': f_array,
            "FWHM (GAUSSIAN)": fwg_fit,
            "stderr FWHM (GAUSSIAN)": fwg_error,
            "FWHM (LORENTZ)": fwl_fit,
            "stderr FWHM (LORENTZ)": fwl_error,
            "FWHM (VOIGT)": fwh_fit,
            "stderr FWHM (VOIGT)": fwh_error,
            "Fraction": gam_fit,
            "stderr Fraction": gam_error,
            "Decay": dec_fit,
            "stderr Decay": dec_error,
            "Power": exp_fit,
            "stderr Power": exp_error,
            "Slope": slp_fit,
            "stderr Slope": slp_error,
            "Constant": con_fit,
            "stderr Constant": con_error,
            "Signum": sig_fit,
            "stderr Signum": sig_error,
        },
        index=[index],
    )

    # merged = file.append(tmp)
    # cols = list(file) + list(tmp)
    # merged.columns = cols

    index = [
        "Model",
        "Energy",
        "stderr Energy",
        "Amp",
        "stderr Amp",
        "Area",  #'stderr Area': f_
        "FWHM (GAUSSIAN)",
        "stderr FWHM (GAUSSIAN)",
        "FWHM (LORENTZ)",
        "stderr FWHM (LORENTZ)",
        "FWHM (VOIGT)",
        "stderr FWHM (VOIGT)",
        "Fraction",
        "stderr Fraction",
        "Decay",
        "stderr Decay",
        "Power",
        "stderr Power",
        "Slope",
        "stderr Slope",
        "Constant",
        "stderr Constant",
        "Signum",
        "stderr Signum",
    ]

    file = file.append(tmp)

    return file[index]


def excle(filename, file):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    # writer = pd.ExcelWriter(filename, engine="xlsxwriter")

    # Convert the dataframe to an XlsxWriter Excel object.
    file.to_excel(filename, sheet_name="Fit-Results")

    # Close the Pandas Excel writer and output the Excel file.
    # writer.save()


def pv_cof(fwhm_g: float, fwhm_l: float) -> Tuple[float, float]:
    """
    Calculating the effectiv fwhm of the pseudo voigt profile and the fraction coefficient for n
    """
    f = np.power(
        fwhm_g ** 5
        + 2.69269 * fwhm_g ** 4 * fwhm_l
        + 2.42843 * fwhm_g ** 3 * fwhm_l ** 2
        + 4.47163 * fwhm_g ** 2 * fwhm_l ** 3
        + 0.07842 * fwhm_g * fwhm_l ** 4
        + fwhm_l ** 5,
        0.25,
    )
    n = (
        1.36603 * (fwhm_l / f)
        - 0.47719 * (fwhm_l / f) ** 2
        + 0.11116 * (fwhm_l / f) ** 3
    )
    return (f, n)


def gaussian(
    x: np.array, amplitude: float = 1.0, center: float = 0.0, fwhm: float = 1.0
) -> np.array:
    """Return a 1-dimensional Gaussian function.

    gaussian(x, amplitude, center, sigma) =
        (amplitude/(sq2pi*sigma)) * exp(-(1.0*x-center)**2 / (2*sigma**2))

    """
    sigma = fwhm / Constants.sig2fwhm
    return (amplitude / (Constants.sq2pi * sigma)) * np.exp(
        -((1.0 * x - center) ** 2) / (2 * sigma ** 2)
    )


def lorentzian(
    x, amplitude: float = 1.0, center: float = 0.0, fwhm: float = 1.0
) -> np.array:
    """Return a 1-dimensional Lorentzian function.

    lorentzian(x, amplitude, center, sigma) =
        (amplitude/(1 + ((1.0*x-center)/sigma)**2)) / (pi*sigma)

    """
    sigma = fwhm / 2.0
    return (amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (np.pi * sigma)


def voigt(
    x: np.array, center: float = 0.0, fwhm: float = 1.0, gamma: float = None
) -> np.array:
    """Return a 1-dimensional Voigt function.

    voigt(x, amplitude, center, sigma, gamma) =
        amplitude*wofz(z).real / (sigma*sq2pi)

    see http://en.wikipedia.org/wiki/Voigt_profile

    """
    sigma = fwhm / 3.60131
    if gamma is None:
        gamma = sigma
    z = (x - center + 1j * gamma) / (sigma * Constants.s2)
    return wofz(z).real / (sigma * Constants.sq2pi)


# def pseudovoigt(x, amplitude=1.0, center=0.0, sigma=1.0, fraction=0.5):
#    """Return a 1-dimensional pseudo-Voigt function.
#
#    pseudovoigt(x, amplitude, center, sigma, fraction) =
#       amplitude*(1-fraction)*gaussion(x, center, sigma_g) +
#       amplitude*fraction*lorentzian(x, center, sigma)
#
#    where sigma_g (the sigma for the Gaussian component) is
#
#        sigma_g = sigma / sqrt(2*log(2)) ~= sigma / 1.17741
#
#    so that the Gaussian and Lorentzian components have the
#    same FWHM of 2*sigma.
#
#    """
#    sigma_g = sigma / np.sqrt(2*log2)
#    return ((1-fraction)*gaussian(x, amplitude, center, sigma_g) +
#            fraction*lorentzian(x, amplitude, center, sigma))


def pseudovoigt(
    x: np.array,
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhm_g: float = 1.0,
    fwhm_l: float = 1.0,
) -> np.array:

    # PSVOIGT This is a psuedo voigt function
    #   This is programmed according to wikipidia and they cite:
    #   Ida, T and Ando, M and Toraya, H (2000).
    # "Extended pseudo-Voigt function for approximating the Voigt profile".
    # Journal of Applied Crystallography 33 (6): 1311-1316.

    # sigma_g = sigma / np.sqrt(2*log2)
    f, n = pv_cof(fwhm_g, fwhm_l)

    # f = np.power(fwhm_g**5 +2.69269*fwhm_g**4*fwhm_l+2.42843*fwhm_g**3*fwhm_l**2+
    #             4.47163*fwhm_g**2*fwhm_l**3+0.07842*fwhm_g*fwhm_l**4+fwhm_l**5,0.25)
    # n = 1.36603*(fwhm_l/f) - 0.47719*(fwhm_l/f)**2 +0.11116*(fwhm_l/f)**3
    return n * lorentzian(x, amplitude, center, fwhm_l) + (1 - n) * gaussian(
        x, amplitude, center, fwhm_g
    )


def exponential(
    x: np.array, amplitude: float = 1.0, decay: float = 1.0, intercept: float = 0.0
) -> np.array:
    """Return an exponential function.

    x -> amplitude * exp(-x/decay)

    """
    return amplitude * np.exp(-x / decay) + intercept


def powerlaw(
    x: np.array, amplitude: float = 1.0, exponent: float = 1.0, intercept: float = 0.0
) -> np.array:
    """Return the powerlaw function.

    x -> amplitude * x**exponent

    """

    return amplitude * np.power(x, exponent) + intercept


def linear(x: np.array, slope: float = 1.0, intercept: float = 0.0) -> np.array:
    """Return a linear function.

    x -> slope * x + intercept

    """
    return slope * x + intercept


def constant(x: np.array, amplitude: float = 1.0) -> np.array:
    """Return a cosntant function.

    x -> constant

    """
    return np.linspace(amplitude, amplitude, len(x))


def step(
    x: np.array,
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    form: str = "linear",
) -> np.array:
    """Return a step function.

    starts at 0.0, ends at amplitude, with half-max at center, and
    rising with form:
      'linear' (default) = amplitude * min(1, max(0, arg))
      'atan', 'arctan'   = amplitude * (0.5 + atan(arg)/pi)
      'erf'              = amplitude * (1 + erf(arg))/2.0
      'logistic'         = amplitude * [1 - 1/(1 + exp(arg))]

    where arg = (x - center)/sigma

    """
    if abs(sigma) < 1.0e-13:
        sigma = 1.0e-13

    out = (x - center) / sigma
    if form == "erf":
        out = 0.5 * (1 + erf(out))
    elif form.startswith("logi"):
        out = 1.0 - 1.0 / (1.0 + np.exp(out))
    elif form in {"atan", "arctan"}:
        out = 0.5 + np.arctan(out) / np.pi
    else:
        out[np.where(out < 0)] = 0.0
        out[np.where(out > 1)] = 1.0
    return amplitude * out


if __name__ == "__main__":
    command_line_runner()
