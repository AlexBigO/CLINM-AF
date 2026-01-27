"""
file: fit_utils.py
brief:
usage:
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

from utils import configure_canvas
from format_utils import enforce_list
from style_formatter import set_global_style, set_object_style
import ROOT as r
from numpy import arange

try:
    from math import pi
except ModuleNotFoundError:
    print("Module 'math' is not installed. Please install it to run this script.")


# # pylint: disable=too-few-public-methods
# class Lorentzian:
#     """
#     Class for lorentz fit function
#     """

#     def __call__(self, x, par):
#         x0 = par[1]
#         gamma = par[2]
#         num = par[0] * 2.0 / pi / gamma
#         den = 1 + (x[0] - x0) * (x[0] - x0) / (0.5 * gamma) / (0.5 * gamma)
#         return num / den


def langaufun(x, par):
    # par[0] = Landau MPV
    # par[1] = Landau width
    # par[2] = Gaussian sigma
    # par[3] = normalization

    invsq2pi = 0.3989422804014
    mpshift = -0.22278298

    mpv = par[0] - mpshift * par[1]
    sum_ = 0.0
    np = 100
    sc = 5.0

    xlow = x[0] - sc * par[2]
    xupp = x[0] + sc * par[2]
    step = (xupp - xlow) / np

    for i in range(np):
        xx = xlow + (i + 0.5) * step
        land = r.TMath.Landau(xx, mpv, par[1]) / par[1]
        gaus = r.TMath.Gaus(x[0], xx, par[2])
        sum_ += land * gaus

    return par[3] * step * sum_ * invsq2pi / par[2]


class LanGaus:
    """
    Docstring pour LanGaus
    """

    def __call__(self, x, par):

        # Fit parameters:
        # par[0]=Width (scale) parameter of Landau density
        # par[1]=Most Probable (MP, location) parameter of Landau density
        # par[2]=Total area (integral -inf to inf, normalization constant)
        # par[3]=Width (sigma) of convoluted Gaussian function

        # In the Landau distribution (represented by the CERNLIB approximation),
        # the maximum is located at x=-0.22278298 with the location parameter=0.
        # This shift is corrected within this function, so that the actual
        # maximum is identical to the MP parameter.

        # Numeric constants
        invsq2pi = 0.3989422804014  # (2 pi)^(-1/2)
        mpshift = -0.22278298  # Landau maximum location
        # Control constants
        np = 100  # number of convolution steps
        sc = 5.0  # convolution extends to +-sc Gaussian sigmas

        # Variables
        sum = 0.0

        #   MP shift correction
        mpc = par[1] - mpshift * par[0]

        #    Range of convolution integral
        xlow = x[0] - sc * par[3]
        xupp = x[0] + sc * par[3]

        step = (xupp - xlow) / np

        # Convolution integral of Landau and Gaussian by sum
        for i in range(np):
            xx = xlow + (i - 0.5) * step
            fland = r.TMath.Landau(xx, mpc, par[0]) / par[0]
            sum += fland * r.TMath.Gaus(x[0], xx, par[3])

            xx = xupp - (i - 0.5) * step
            fland = r.TMath.Landau(xx, mpc, par[0]) / par[0]
            sum += fland * r.TMath.Gaus(x[0], xx, par[3])

        return par[2] * step * sum * invsq2pi / par[3]


def lorentzian():
    """
    Class for lorentz fit function
    """
    num = "[0] * 2 / pi / [2]"
    den = "1 + (x - [1])*(x - [1]) / ([2]/2) / ([2]/2)"
    return num + "/ (" + den + ")"


# pylint:disable=too-many-statements, too-many-locals
def plot_fit(config: dict) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file
    """

    padleftmargin = 0.12

    name_infile: str = config["output"]["file"]
    data: list[str] = enforce_list(config["histogram_config"]["name"])
    label: list[str] = enforce_list(config["output"]["plot"]["label"])
    funcs_fit: list[str] = enforce_list(config["fit"]["func"])
    name_outfile = name_infile.replace(".root", str()) + ".pdf"
    # extension: list[str] = enforce_list(config["output"]["extension"])

    exp: str = config["output"]["plot"]["info"]["exp"]
    campaign: str = config["output"]["plot"]["info"]["campaign"]
    particle_beam: str = config["output"]["plot"]["info"]["beam"]["particle"]
    energy_beam: str = config["output"]["plot"]["info"]["beam"]["energy"]
    run_number: str = str(config["output"]["plot"]["info"]["run"])

    infile: r.TFile = r.TFile.Open(name_infile)

    for i, (dat, lab, func_fit) in enumerate(zip(data, label, funcs_fit)):

        if "Charge" in dat:
            padrightmargin = 0.09
        else:
            padrightmargin = 0.035  # default value
        set_global_style(
            padleftmargin=padleftmargin,
            padrightmargin=padrightmargin,
            padbottommargin=0.12,
            padtopmargin=0.05,
            titlesize=0.045,
            labelsize=0.04,
            maxdigits=3,
        )

        h_data: r.TH1F = infile.Get(dat)
        h_fitres: r.TH1F = infile.Get(f"hFitRes{dat}")

        chi2 = h_fitres.GetBinContent(2)
        ndf = h_fitres.GetBinContent(3)
        chi2_ndf = float(chi2) / ndf

        eq_func: str = str()
        npars: int = 3
        if func_fit == "gaus":
            eq_func = "gaus"
            npars = 3
        elif func_fit == "lorentz":
            eq_func = lorentzian()
            npars = 3
        elif func_fit == "crystalball":
            eq_func = "crystalball"
            npars = 5

        pars, unc_pars = [], []
        for ibin in range(6, 6 + npars):
            pars.append(h_fitres.GetBinContent(ibin))
            unc_pars.append(h_fitres.GetBinError(ibin))

        xmin = h_fitres.GetBinContent(4)
        xmax = h_fitres.GetBinContent(5)
        func: r.TF1 = r.TF1("func", eq_func, xmin, xmax)
        func.SetParameters(*pars)

        ymin = h_data.GetMinimum()
        ymax = 1.05 * max(func.GetMaximum(), h_data.GetMaximum())
        title = f";{lab}; Entries;"
        c = configure_canvas(f"canvas{i}", xmin, ymin, xmax, ymax, title)

        set_object_style(h_data, color=r.kBlack, linewidth=2)
        set_object_style(func, color=r.kAzure + 2, linewidth=2)
        func.Draw("same")
        h_data.Draw("esame")

        # add a legend
        leg = r.TLegend(padleftmargin + 0.55, 0.8, 0.9, 0.9)
        leg.SetTextSize(0.035)
        leg.SetFillStyle(0)
        leg.AddEntry(h_data, "Data", "p")
        if func_fit == "gaus":
            leg.AddEntry(func, "Gaussian", "l")
        elif func_fit == "lorentz":
            leg.AddEntry(func, "Lorentzian", "l")
        elif func_fit == "crystalball":
            leg.AddEntry(func, "CrystallBall", "l")
        leg.Draw()

        # add information in TLatex
        latex_clinm = r.TLatex()
        xlatex_clinm = padleftmargin + 0.03  # 0.18
        ylatex_clinm = 0.92
        latex_clinm.SetNDC()
        latex_clinm.SetTextSize(0.04)
        latex_clinm.SetTextAlign(13)  # align at top
        latex_clinm.SetTextFont(42)
        latex_clinm.DrawLatex(xlatex_clinm, ylatex_clinm, exp)

        latex_info = r.TLatex()
        xlatex_info = padleftmargin + 0.03
        ylatex_info_max = 0.92 - 0.06
        latex_info.SetNDC()
        latex_info.SetTextSize(0.03)
        latex_info.SetTextAlign(13)  # align at top
        latex_info.SetTextFont(42)
        latex_info.DrawLatex(xlatex_info, ylatex_info_max, campaign)
        latex_info.DrawLatex(
            xlatex_info, ylatex_info_max - 0.05, f"{particle_beam} @ {energy_beam}"
        )
        latex_info.DrawLatex(xlatex_info, ylatex_info_max - 0.1, f"Run {run_number}")

        latex_fitpars = r.TLatex()
        xlatex_fitpars = (
            padleftmargin + 0.55 if "Amplitude" in dat else padleftmargin + 0.5
        )
        ylatex_fitpars_max = 0.75
        latex_fitpars.SetNDC()
        latex_fitpars.SetTextSize(0.03)
        latex_fitpars.SetTextAlign(13)  # align at top
        latex_fitpars.SetTextFont(42)
        latex_fitpars.DrawLatex(
            xlatex_fitpars, ylatex_fitpars_max, f"#chi^{{2}} / ndf = {chi2_ndf:.2f}"
        )
        latex_fitpars.DrawLatex(
            xlatex_fitpars,
            ylatex_fitpars_max - 0.05,
            f"#mu = {pars[1]:.3f} #pm {unc_pars[1]:.3f}",
        )
        latex_fitpars.DrawLatex(
            xlatex_fitpars,
            ylatex_fitpars_max - 0.1,
            f"#sigma = {pars[2]:.3f} #pm {unc_pars[2]:.3f}",
        )

        c.Update()
        c.Draw()

        if i == 0:
            c.Print(f"{name_outfile}(")
        elif i == len(data) - 1:
            c.Print(f"{name_outfile})")
        else:
            c.Print(name_outfile)

    infile.Close()
