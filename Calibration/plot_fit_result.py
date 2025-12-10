"""
file: plot_fit_result.py
brief: Script to produce a plot of a fit.py result
usage: python3 plot_fit_result.py cfg.yml
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import sys
import ROOT as r

try:
    from yaml import load, FullLoader
except ModuleNotFoundError:
    print("Module 'pyyaml' is not installed. Please install it to run this script.")

try:
    from argparse import ArgumentParser
except ModuleNotFoundError:
    print("Module 'argparse' is not installed. Please install it to run this script.")

try:
    sys.path.append("../Utils/")
    from utils import configure_canvas, enforce_list
except ModuleNotFoundError:
    print(
        "Module 'utils' is not in the '../Utils/' directory. Add it to run this script."
    )

try:
    sys.path.append("../Utils/")
    from logger import Logger
except ModuleNotFoundError:
    print(
        "Module 'logger' is not in the '../Utils/' directory. Add it to run this script."
    )

try:
    sys.path.append("../Utils/")
    from style_formatter import set_global_style, set_object_style
except ModuleNotFoundError:
    print(
        "Module 'style_formatter' is not in the '../Utils/' directory. Add it to run this script."
    )


# pylint:disable=too-many-statements, too-many-locals
def main(name_config_file: str) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file
    """

    padleftmargin = 0.12

    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    name_infile: str = config["input"]["file"]
    data: list[str] = enforce_list(config["input"]["data"])
    label: list[str] = enforce_list(config["plot"]["label"])
    name_outfile: list[str] = enforce_list(config["output"]["file"])
    extension: list[str] = enforce_list(config["output"]["extension"])

    # safety
    if not len(data) == len(label) == len(name_outfile):
        Logger(
            "'input/data', 'plot/label' and 'output/file' must be of same size!",
            "FATAL",
        )

    exp: str = config["plot"]["info"]["exp"]
    campaign: str = config["plot"]["info"]["campaign"]
    particle_beam: str = config["plot"]["info"]["beam"]["particle"]
    energy_beam: str = config["plot"]["info"]["beam"]["energy"]
    run_number: str = str(config["plot"]["info"]["run"])

    infile: r.TFile = r.TFile.Open(name_infile)

    for i, (dat, lab, name_ofile) in enumerate(zip(data, label, name_outfile)):

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

        pars, unc_pars = [], []
        for ibin in range(4, 7):
            pars.append(h_fitres.GetBinContent(ibin))
            unc_pars.append(h_fitres.GetBinError(ibin))

        title = f";{lab}; Entries;"
        xmin = h_fitres.GetBinContent(7)
        ymin = h_data.GetMinimum()
        xmax = h_fitres.GetBinContent(8)
        ymax = 1.05 * h_data.GetMaximum()

        c = configure_canvas(f"c{i}", xmin, ymin, xmax, ymax, title)

        func: r.TF1 = r.TF1("func", "gaus", xmin, xmax)
        func.SetParameters(*pars)

        set_object_style(h_data, color=r.kBlack, linewidth=2)
        set_object_style(func, color=r.kAzure + 2, linewidth=2)
        func.Draw("same")
        h_data.Draw("esame")

        # add a legend
        leg = r.TLegend(padleftmargin + 0.55, 0.8, 0.9, 0.9)
        leg.SetTextSize(0.035)
        leg.SetFillStyle(0)
        leg.AddEntry(h_data, "Data", "p")
        leg.AddEntry(func, "Gaussian", "l")
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

        # save plot
        for ext in extension:
            c.SaveAs(name_ofile + "." + ext)

    infile.Close()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    main(args.name_config_file)
