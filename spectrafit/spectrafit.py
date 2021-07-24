#!/usr/bin/env python3.6
import argparse

import matplotlib.pylab as plt
import numpy as np
import pandas as pd
from lmfit import Minimizer, Parameters, conf_interval, minimize, report_fit
from lmfit.printfuncs import *
from matplotlib.ticker import AutoMinorLocator
from matplotlib.widgets import Cursor
from scipy.special import erf, erfc
from scipy.special import gamma as gamfcn
from scipy.special import gammaln, wofz
from tqdm import tqdm

log2 = np.log(2)
s2pi = np.sqrt(2 * np.pi)
spi = np.sqrt(np.pi)
s2 = np.sqrt(2.0)
sig2fwhM = 2.0 * np.sqrt(2.0 * log2)

description = "Fast Fitting Program for ascii txt files."
# with open('/Users/hahn/bin/Readme.txt', 'r') as content_file:
#    description = content_file.read()
def main():
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "infile", type=argparse.FileType("r"), help="txt-textfile for plotting, please"
    )
    parser.add_argument(
        "outfile",
        nargs="?",
        default="Results",
        help="txt-textfile for fit parameter export, please",
    )
    # parser.add_argument("outfile_1",nargs='?',default='Export_Data.txt', help="txt-textfile for data export, please")
    parser.add_argument(
        "-ov",
        action="store_true",
        default=False,
        help="Oversampling the spectra by using factor of 5",
    )
    parser.add_argument(
        "-disp",
        action="store_true",
        default=False,
        help="Hole or splitted Table on the Screen (default = hole)",
    )
    parser.add_argument("-e0", type=float, default=None, help="Starting energy in eV")
    parser.add_argument("-e1", type=float, default=None, help="Ending energy in eV")
    parser.add_argument(
        "-s", type=int, default=0, help="Number of smooth points for lmfit"
    )
    # parser.add_argument("-b",type=float,default=0.,help="Constant baseline subtraction")
    parser.add_argument("-sh", type=float, default=0.0, help="Constant energy shift")
    parser.add_argument("-c", type=int, default=1, help="Number of y-row")
    # parser.parse_args(['input.txt', 'output.txt'])
    args = parser.parse_args()

    data = np.genfromtxt(args.infile, dtype=float)
    data = np.nan_to_num(data)

    while True:
        again = input("Would you like to fit ...? Enter y/n: ").lower()
        if again == "n":
            print("Thanks for using ...!")
            return
        elif again == "y":
            print("Lets start fitting ...")
            # try:
            guess = pd.read_csv("guess.parm", sep=";\s+", engine="python", comment="#")
            copy_guess("guess.parm", args.outfile + ".parm")
            # guess = np.genfromtxt('guess.parm',dtype=str)
            # print "Input guess is:"
            # print "En\tA\tG\tL miE miA miG miL maEn maA maG maL"
            params = init(guess)
            if args.e0 != args.e1:
                x0, x1 = np.argmin(np.abs(data[:, 0] - args.e0)), np.argmin(
                    np.abs(data[:, 0] - args.e1)
                )
                x, y = data[x0:x1, 0] - args.sh, data[x0:x1, args.c]  # - args.b
            else:
                x, y = data[:, 0] - args.sh, data[:, args.c]  # - args.b
            y = smooth(y, args.s)
            x, y = oversampling(x, y, args.ov)
            minner = Minimizer(model, params, fcn_args=(x, y), iter_cb=20000)
            kws = {"options": {"maxiter": 2000}}
            # try:
            result = minner.minimize()

            # except ValueError:
            #    print "Input error in guess.parm"
            final = y + result.residual
            # print result.init_fit
            # report_fit(result)

            plot(x, y, final, result, args)
            # except IOError:
            #    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            #    print "!!!!No Inputfile guess.parm for Fits!!!!"
            #    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            #
            #    pass

        else:
            print('You should enter either "y" or "n".')


def oversampling(x, y, mode):
    if mode:
        xvals = np.linspace(min(x), max(x), 5 * len(x))
        yinterp = np.interp(xvals, x, y)
    else:
        xvals = x
        yinterp = y

    return xvals, yinterp


def copy_guess(inp, out):
    with open(inp, "r") as f:
        lines = f.readlines()
        lines = [l for l in lines]
        with open(out, "w+") as f1:
            f1.writelines(lines)


def smooth(y, box_pts):
    if box_pts == 0:
        return y

    box = np.ones(box_pts) / box_pts
    return np.convolve(y, box, mode="same")


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

        if "pvoigt" in mode:
            if "cen" in mode:
                cen = result.params[mode]
            if "amp" in mode:
                amp = result.params[mode]
            if "fwg" in mode:
                fwg = result.params[mode]
            if "fwl" in mode:
                fwl = result.params[mode]
                val = np.nan_to_num(pvoigt(x, amp, cen, fwg, fwl))
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


"""def printh(file,detail=False):
    if detail:
        print '----- \t\t ----- \t\t ------ \t\t --------- \t\t ---- \t\t ---- \t\t ----- \t\t ----- \t\t --- \t\t ----- \t\t --------'
        print 'Model \t\t Count \t\t Energy \t\t Amplitude \t\t FWHM \t\t FRAC \t\t Gamma \t\t Slope \t\t Cut \t\t Decay \t\t Exponent'
        print '----- \t\t ----- \t\t ------ \t\t --------- \t\t ---- \t\t ---- \t\t ----- \t\t ----- \t\t --- \t\t ----- \t\t --------\n'
        print >>file,'----- \t\t ----- \t\t ------ \t\t --------- \t\t ---- \t\t ---- \t\t ----- \t\t ----- \t\t --- \t\t ----- \t\t --------'
        print >>file,'Model \t\t Count \t\t Energy \t\t Amplitude \t\t FWHM \t\t FRAC \t\t Gamma \t\t Slope \t\t Cut \t\t Decay \t\t Exponent'
        print >>file,'----- \t\t ----- \t\t ------ \t\t --------- \t\t ---- \t\t ---- \t\t ----- \t\t ----- \t\t --- \t\t ----- \t\t --------\n'
    else:
        print 'Model \t\t Count \t\t Energy \t\t Amp \t\t Area \t\t FWHM (GAUSSIAN) \t\t FWHM (LORENTZ) \t\t FWHM (VOIGT) \t\t Fraction \t\t Decay \t\t Power \t\t Slope \t\t Constant \t\t Signum'
        print '----- \t\t ----- \t\t ------ \t\t --- \t\t ---- \t\t --------------- \t\t -------------- \t\t ------------ \t\t -------- \t\t ----- \t\t ----- \t\t ----- \t\t -------- \t\t ------'
        print >>file,'Model \t\t Count \t\t Energy \t\t Amp \t\t Area \t\t FWHM (GAUSSIAN) \t\t FWHM (LORENTZ) \t\t FWHM (VOIGT) \t\t Fraction \t\t Decay \t\t Power \t\t Slope \t\t Constant \t\t Signum'
        print >>file,'----- \t\t ----- \t\t ------ \t\t --- \t\t ---- \t\t --------------- \t\t -------------- \t\t ------------ \t\t -------- \t\t ----- \t\t ----- \t\t ----- \t\t -------- \t\t ------'
        """

"""def printf(file,x,y,model,index,0,0,0,0,0,0,0,0,0,0,0):
    index = '\t\t'+str(index)

    area = np.trapz(y,x)
    #print(cen.__dict__)
    #print str(np.round(cen._val,4)) +' +/- ' + str(cen.stderr)
    if not (fwg  is None) and not (fwl  is None):
        f, n             = pv_cof(fwg._val,fwl._val)
        f_error, n_error = pv_cof(fwg.stderr,fwl.stderr)

        fwh = str(np.round(f,4)) +' +/- ' + str(np.round(f_error,4))
        gam = str(np.round(n,4)) +' +/- ' + str(np.round(n_error,4))
    elif not (fwh  is None) and not (gam  is None):
        fwh = str(np.round(fwh._val,4)) +' +/- ' + str(np.round(fwh.stderr,4))
        gam = str(np.round(gam._val,4)) +' +/- ' + str(np.round(gam.stderr,4))
    if not (cen  is None): cen = str(np.round(cen._val,4)) +' +/- ' + str(np.round(cen.stderr,4))
    if not (amp  is None): amp = str(np.round(amp._val,4)) +' +/- ' + str(np.round(amp.stderr,4))
    if not (fwg  is None): fwg = str(np.round(fwg._val,4)) +' +/- ' + str(np.round(fwg.stderr,4))
    if not (fwl  is None): fwl = str(np.round(fwl._val,4)) +' +/- ' + str(np.round(fwl.stderr,4))
    if not (dec  is None): dec = str(np.round(dec._val,4)) +' +/- ' + str(np.round(dec.stderr,4))
    if not (exp  is None): exp = str(np.round(exp._val,4)) +' +/- ' + str(np.round(exp.stderr,4))
    if not (slp  is None): slp = str(np.round(slp._val,4)) +' +/- ' + str(np.round(slp.stderr,4))
    if not (con  is None): con = str(np.round(con._val,4)) +' +/- ' + str(np.round(con.stderr,4))
    if not (sig  is None): sig = str(np.round(sig._val,4)) +' +/- ' + str(np.round(sig.stderr,4))

    #f = np.power(fwhm_g**5 +2.69269*fwhm_g**4*fwhm_l+2.42843*fwhm_g**3*fwhm_l**2+
    #             4.47163*fwhm_g**2*fwhm_l**3+0.07842*fwhm_g*fwhm_l**4+fwhm_l**5,0.25)
    #
    #if detail:
    #    print  model,     index,      eng         ,amp          ,sig       ,fra     ,gam        ,slp      ,cut     ,dec       ,exp
    sp = '\t\t'



    print  model,index,sp,cen,sp,amp,sp,area,sp,fwg,sp,fwl,sp,fwh,sp,gam,sp,dec,sp,exp,sp,slp,sp,con,sp,sig
    print  >>file,model,sp,index,sp,cen,sp,amp,sp,area,sp,fwg,sp,fwl,sp,fwh,sp,gam,sp,dec,sp,exp,sp,slp,sp,con,sp,sig"""


"""
def high_res(x,final,result,filename):
    x = np.linspace(min(x),max(x),2000)
    out = []
    y = 0.
    for i,index in enumerate(range(0,len(result.params),4)):
        amp   = result.params['amp_'+str(i)].value
        x0    = result.params['x0_'+str(i)].value
        fwhmG = result.params['fwhmG_'+str(i)].value
        fwhmL = result.params['fwhmL_'+str(i)].value
        tmp_y = amp* psVoigt( x, x0, fwhmG, fwhmL)
        out.append(tmp_y)
        y += tmp_y
    export =  filename[0].split('.')[0]+'.dat'
    out.append(x)
    out.append(y)
    np.savetxt(export,np.transpose(out),delimiter='\t')
"""
"""
def psVoigt( x, x0, fwhmG, fwhmL):

    #PSVOIGT This is a psuedo voigt function
    #   This is programmed according to wikipidia and they cite:
    #   Ida, T and Ando, M and Toraya, H (2000).
    #"Extended pseudo-Voigt function for approximating the Voigt profile".
    #Journal of Applied Crystallography 33 (6): 1311-1316.



    f = np.power(fwhmG**5 +2.69269*fwhmG**4*fwhmL+2.42843*fwhmG**3*fwhmL**2+
                 4.47163*fwhmG**2*fwhmL**3+0.07842*fwhmG*fwhmL**4+fwhmL**5,0.25)
    n = 1.36603*(fwhmL/f) - 0.47719*(fwhmL/f)**2 +0.11116*(fwhmL/f)**3
    return n* fn_lorentz(x,x0,fwhmL)+ (1-n)*fn_gauss(x,x0,fwhmG)
def fn_gauss(x,x0,fwhmG):
    c2 = np.power(fwhmG/(2*np.sqrt(2*np.log(2))),2)
    return  1.*np.exp(-0.5*(x - x0)**2/c2)
def fn_lorentz(x,x0,fwhmL):
    return  1/np.pi*0.5*fwhmL/(np.power((x-x0),2)+np.power((0.5*fwhmL),2))
"""


def pv_cof(fwhm_g, fwhm_l):
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
    return f, n


def gaussian(x, amplitude=1.0, center=0.0, fwhm=1.0):
    """Return a 1-dimensional Gaussian function.

    gaussian(x, amplitude, center, sigma) =
        (amplitude/(s2pi*sigma)) * exp(-(1.0*x-center)**2 / (2*sigma**2))

    """
    sigma = fwhm / sig2fwhM
    return (amplitude / (s2pi * sigma)) * np.exp(
        -((1.0 * x - center) ** 2) / (2 * sigma ** 2)
    )


def lorentzian(x, amplitude=1.0, center=0.0, fwhm=1.0):
    """Return a 1-dimensional Lorentzian function.

    lorentzian(x, amplitude, center, sigma) =
        (amplitude/(1 + ((1.0*x-center)/sigma)**2)) / (pi*sigma)

    """
    sigma = fwhm / 2.0
    return (amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (np.pi * sigma)


def voigt(x, center=0.0, fwhm=1.0, gamma=None):
    """Return a 1-dimensional Voigt function.

    voigt(x, amplitude, center, sigma, gamma) =
        amplitude*wofz(z).real / (sigma*s2pi)

    see http://en.wikipedia.org/wiki/Voigt_profile

    """
    sigma = fwhm / 3.60131
    if gamma is None:
        gamma = sigma
    z = (x - center + 1j * gamma) / (sigma * s2)
    return wofz(z).real / (sigma * s2pi)


# def pvoigt(x, amplitude=1.0, center=0.0, sigma=1.0, fraction=0.5):
#    """Return a 1-dimensional pseudo-Voigt function.
#
#    pvoigt(x, amplitude, center, sigma, fraction) =
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


def pvoigt(x, amplitude, center, fwhm_g, fwhm_l):

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


def exponential(x, amplitude=1, decay=1, intercept=0.0):
    """Return an exponential function.

    x -> amplitude * exp(-x/decay)

    """
    return amplitude * np.exp(-x / decay) + intercept


def powerlaw(x, amplitude=1, exponent=1.0, intercept=0.0):
    """Return the powerlaw function.

    x -> amplitude * x**exponent

    """

    return amplitude * np.power(x, exponent) + intercept


def linear(x, slope=1.0, intercept=0.0):
    """Return a linear function.

    x -> slope * x + intercept

    """
    return slope * x + intercept


def const(x, c):
    """Return a cosntant function.

    x -> constant

    """
    return np.linspace(c, c, len(x))


def step(x, amplitude=1.0, center=0.0, sigma=1.0, form="linear"):
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
    elif form in ("atan", "arctan"):
        out = 0.5 + np.arctan(out) / np.pi
    else:
        out[where(out < 0)] = 0.0
        out[where(out > 1)] = 1.0
    return amplitude * out


def model(params, x, data):
    """
    Here is the model function, where all
    init params will read and add to the model

    """
    val = 0.0
    for i, mode in enumerate(params):
        mode = mode.lower()
        if "gaus" in mode:
            if "cen" in mode:
                cen = params[mode]
            if "amp" in mode:
                amp = params[mode]
            if "fwg" in mode:
                fwg = params[mode]
                val += np.nan_to_num(gaussian(x, amp, cen, fwg))
        if "lorz" in mode:
            if "cen" in mode:
                cen = params[mode]
            if "amp" in mode:
                amp = params[mode]
            if "fwl" in mode:
                fwl = params[mode]
                val += np.nan_to_num(lorentzian(x, amp, cen, fwl))
        if "voigt" in mode:
            if "cen" in mode:
                cen = params[mode]
            if "fwh" in mode:
                fwh = params[mode]
            # elif 'amp' in mode: amp   = params[mode]
            if "gam" in mode:
                gamma = params[mode]
                val += np.nan_to_num(voigt(x, cen, fwh, gamma))
        if "pvoigt" in mode:
            if "cen" in mode:
                cen = params[mode]
            if "amp" in mode:
                amp = params[mode]
            if "fwg" in mode:
                fwg = params[mode]
            if "fwl" in mode:
                fwl = params[mode]
                val += np.nan_to_num(pvoigt(x, amp, cen, fwg, fwl))
        if "expo" in mode:
            if "dec" in mode:
                decay = params[mode]
            if "amp" in mode:
                amp = params[mode]
            if "con" in mode:
                inter = params[mode]
                val += np.nan_to_num(exponential(x, amp, decay, inter))
        if "powr" in mode:
            if "ord" in mode:
                expo = params[mode]
            if "con" in mode:
                inter = params[mode]
                val += np.nan_to_num(powerlaw(x, amp, expo, inter))
        if "linr" in mode:
            if "slp" in mode:
                slope = params[mode]
            if "con" in mode:
                inter = params[mode]
                val += np.nan_to_num(linear(x, slope, inter))
        if "cons" in mode and "con" in mode:
            c = params[mode]
            val += np.nan_to_num(const(x, c))
        # elif 'stpl' in mode:
        #    if 'cen' in mode: cen  = params[mode]
        #    elif 'sig' in mode:
        #        sig   = params[mode]
        #        val += np.nan_to_num(step(x, cen, sig, form='linear'))
        if "erf" in mode:
            if "cen" in mode:
                cen = params[mode]
            if "sig" in mode:
                sig = params[mode]
            if "amp" in mode:
                amp = params[mode]
                val += np.nan_to_num(step(x, amp, cen, sig, form="erf"))
        if "atan" in mode:
            if "cen" in mode:
                cen = params[mode]
            if "sig" in mode:
                sig = params[mode]
            if "amp" in mode:
                amp = params[mode]
                val += np.nan_to_num(step(x, amp, cen, sig, form="atan"))
        if "log" in mode:
            if "cen" in mode:
                cen = params[mode]
            if "sig" in mode:
                sig = params[mode]
            if "amp" in mode:
                amp = params[mode]
                val += np.nan_to_num(step(x, amp, cen, sig, form="atan"))
    return val - data


def init(guess):
    params = Parameters()
    func = []
    len_row = len(guess.axes[0])
    len_col = len(guess.axes[1])
    # index = 0

    Name = np.array(guess.get("Name"))
    Value = np.array(guess.get("Value"))
    Vary = np.array(guess.get("Vary"))
    Min = np.array(guess.get("Min"))
    Max = np.array(guess.get("Max"))
    Expr = np.array(guess.get("Expr"))

    func = [i.lower() for i in np.array(guess.get("Type"))]

    for i, mode in enumerate(func):
        if Expr[i].lower() == "none":
            Expr[i] = None
        if (np.isnan(Min[i]) == True) and (np.isnan(Max[i]) != True):
            params.add(
                Name[i] + "_" + mode,
                value=Value[i],
                vary=Vary[i],
                min=None,
                max=Max[i],
                expr=Expr[i],
            )
        elif (np.isnan(Min[i]) != True) and (np.isnan(Max[i]) == True):
            params.add(
                Name[i] + "_" + mode,
                value=Value[i],
                vary=Vary[i],
                min=Min[i],
                max=None,
                expr=Expr[i],
            )
        elif (np.isnan(Min[i]) == True) and (np.isnan(Max[i]) == True):
            params.add(
                Name[i] + "_" + mode,
                value=Value[i],
                vary=Vary[i],
                min=None,
                max=None,
                expr=Expr[i],
            )
        else:
            params.add(
                Name[i] + "_" + mode,
                value=Value[i],
                vary=Vary[i],
                min=Min[i],
                max=Max[i],
                expr=Expr[i],
            )

    # TypeError
    return params


if __name__ == "__main__":
    main()
