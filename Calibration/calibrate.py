"""
file: calibrate.py
brief: Script to fit amplitude/charge vs deposited energy of scintillator
usage: python3 calibrate.py cfg.yml
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import sys

import numpy as np
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
    import pandas as pd
except ModuleNotFoundError:
    print("Module 'pandas' is not installed. Please install it to run this script.")

try:
    import uproot
except ModuleNotFoundError:
    print("Module 'uproot' is not installed. Please install it to run this script.")

try:
    sys.path.append("../Utils/")
    from logger import Logger
except ModuleNotFoundError:
    print(
        "Module 'logger' is not in the '../Utils/' directory. Add it to run this script."
    )

try:
    sys.path.append("../Utils/")
    from utils import fill_th1, get_h_config, enforce_list
except ModuleNotFoundError:
    print(
        "Module 'utils' is not in the '../Utils/' directory. Add it to run this script."
    )

try:
    sys.path.append("../Utils/")
    from style_formatter import set_global_style, set_object_style
except ModuleNotFoundError:
    print(
        "Module 'style_formatter' is not in the '../Utils/' directory. Add it to run this script."
    )


# pylint:disable=too-few-public-methods
class BirksLaw:
    """
    Class to define Birks law for calibration fit
    """

    def __call__(self, x, par):
        edep = x[0]
        s = par[0]
        a0 = par[1]
        kb = par[2]

        return (s * edep + a0) / (1 + kb * edep)


# pylint:disable=too-many-locals
def main(name_config_file: str) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file
    """
    padleftmargin = 0.12
    set_global_style(
        padleftmargin=padleftmargin,
        # padrightmargin=padrightmargin,
        padbottommargin=0.12,
        padtopmargin=0.05,
        titlesize=0.045,
        labelsize=0.04,
        maxdigits=3,
    )

    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    # handle input
    name_infiles_real: dict = config["input"]["real"]["file"]
    name_hist_fitres_real: str = config["input"]["real"]["hist_fitres"]
    name_infiles_simu: dict = config["input"]["simulation"]["file"]
    name_hist_fitres_simu: str = config["input"]["simulation"]["hist_fitres"]

    number_mean_bin: int = config["input"]["bin_number"]["mean"]
    number_sigma_bin: int = config["input"]["bin_number"]["sigma"]

    # graph options
    name_graph: str = config["graph"]["name"]
    label_xaxis: str = config["graph"]["label"]["xaxis"]
    label_yaxis: str = config["graph"]["label"]["yaxis"]
    limits_xaxis: str = config["graph"]["limits"]["xaxis"]
    limits_yaxis: str = config["graph"]["limits"]["yaxis"]
    color_graph: dict = config["graph"]["color"]
    markerstyle_graph: dict = config["graph"]["markerstyle"]
    # fit options
    color_fit: dict = config["fit"]["color"]

    # TLatex options
    xmin_tlatex: dict = config["tlatex"]["xmin"]
    ymax_tlatex: dict = config["tlatex"]["ymax"]

    # TODO uncomment this safety
    # safety
    # if len(name_infiles_real) != len(name_infiles_simu):
    #     Logger(
    #         "'input/real/file' and 'input/simulation/file'"
    #         " entries must be of same size!",
    #         "FATAL",
    #     )
    # TODO add safety for size comparison inside each entry of the dict name_infiles_real
    if not (
        isinstance(name_hist_fitres_real, str)
        and isinstance(name_hist_fitres_simu, str)
    ):
        Logger(
            "'histfitres' options must be a single string (not a list)!",
            "FATAL",
        )
    # if not (
    #     len(name_hists_fitres_real)
    #     == len(name_hists_fitres_simu)
    #     == len(labels_xaxis)
    #     == len(labels_yaxis)
    # ):
    #     Logger(
    #         "'input/real/hist_fitres', 'input/simulation/hist_fitres' and 'graph/label'"
    #         " entries must be of same size!",
    #         "FATAL",
    #     )

    # means_real = []
    # sigmas_real = []
    # means_simu = []
    # sigmas_simu = []

    ions = list(name_infiles_real.keys())

    # campaigns = list(name_infiles_real.keys())

    means_real = {}
    sigmas_real = {}
    means_simu = {}
    sigmas_simu = {}

    for ion, dict_campaign in name_infiles_real.items():
        means_real[ion] = {}
        sigmas_real[ion] = {}
        for campaign, name_infiles_campaign in dict_campaign.items():
            means_real[ion][campaign] = []
            sigmas_real[ion][campaign] = []
            for name_infile_real in name_infiles_campaign:
                infile_real: r.TFile = r.TFile.Open(name_infile_real)
                hist_real: r.TH1 = infile_real.Get(name_hist_fitres_real)
                means_real[ion][campaign].append(
                    hist_real.GetBinContent(number_mean_bin)
                )
                sigmas_real[ion][campaign].append(
                    hist_real.GetBinContent(number_sigma_bin)
                )
                infile_real.Close()

    for ion, dict_campaign in name_infiles_simu.items():
        means_simu[ion] = {}
        sigmas_simu[ion] = {}
        for campaign, name_infiles_campaign in dict_campaign.items():
            means_simu[ion][campaign] = []
            sigmas_simu[ion][campaign] = []
            for name_infile_simu in name_infiles_campaign:
                infile_simu: r.TFile = r.TFile.Open(name_infile_simu)
                hist_simu: r.TH1 = infile_simu.Get(name_hist_fitres_simu)
                means_simu[ion][campaign].append(
                    hist_simu.GetBinContent(number_mean_bin)
                )
                sigmas_simu[ion][campaign].append(
                    hist_simu.GetBinContent(number_sigma_bin)
                )
                infile_simu.Close()

    # create TGraphErrors for fit
    x, unc_x = {}, {}
    y, unc_y = {}, {}
    graphs_for_fit = {}

    for ion, dict_mean in means_simu.items():
        x[ion] = []
        unc_x[ion] = []
        y[ion] = []
        unc_y[ion] = []
        for campaign, _ in dict_mean.items():
            x[ion].extend(means_simu[ion][campaign])
            unc_x[ion].extend(sigmas_simu[ion][campaign])
            y[ion].extend(means_real[ion][campaign])
            unc_y[ion].extend(sigmas_real[ion][campaign])
        x[ion] = np.array(x[ion])
        unc_x[ion] = np.array(unc_x[ion])
        y[ion] = np.array(y[ion])
        unc_y[ion] = np.array(unc_y[ion])
        graphs_for_fit[ion] = r.TGraphErrors(
            len(x[ion]), x[ion], y[ion], unc_x[ion], unc_y[ion]
        )
        graphs_for_fit[ion].SetName(f"{name_graph}_{ion}")

    # create TGraphErrors for plot
    x, unc_x = {}, {}
    y, unc_y = {}, {}
    graphs_for_plot = {}

    for ion, dict_mean in means_simu.items():
        for campaign, _ in dict_mean.items():
            x[f"{ion}_{campaign}"] = np.array(means_simu[ion][campaign])
            unc_x[f"{ion}_{campaign}"] = np.array(sigmas_simu[ion][campaign])
            y[f"{ion}_{campaign}"] = np.array(means_real[ion][campaign])
            unc_y[f"{ion}_{campaign}"] = np.array(sigmas_real[ion][campaign])
            graphs_for_plot[f"{ion}_{campaign}"] = r.TGraphErrors(
                len(x[f"{ion}_{campaign}"]),
                x[f"{ion}_{campaign}"],
                y[f"{ion}_{campaign}"],
                unc_x[f"{ion}_{campaign}"],
                unc_y[f"{ion}_{campaign}"],
            )

    for ion_campaign, graph in graphs_for_plot.items():
        graph.SetName(f"{name_graph}_{ion_campaign}")
        graph.GetXaxis().SetTitle(label_xaxis)
        graph.GetYaxis().SetTitle(label_yaxis)
        graph.GetXaxis().SetLimits(*limits_xaxis)
        graph.GetYaxis().SetRangeUser(*limits_yaxis)
        split = ion_campaign.split("_")
        ion = split[0]
        campaign = split[1]
        set_object_style(
            obj=graph,
            color=color_graph[ion][campaign],
            markerstyle=markerstyle_graph[ion][campaign],
        )

    # configure fit
    # func_birks = r.TF1("func_birks", BirksLaw(), *range_fit, 3)
    # func_birks.SetParNames("S", "A_0", "Kb")
    range_fit = config["fit"]["range"]
    func_birks: dict = {}
    for ion, fit_range in range_fit.items():
        func_birks[ion] = r.TF1(f"func_birks_{ion}", BirksLaw(), *fit_range, 3)
        func_birks[ion].SetParNames("S", "A_0", "Kb")
        func_birks[ion].FixParameter(2, 0.126 / 2)
        set_object_style(obj=func_birks[ion], linecolor=color_fit[ion], linewidth=2)

    # config of fit result storage
    labels_hfit_res: list[str] = [
        "FitStatus",
        "Chi2",
        "NDF",
        "S",
        "A0",
        "Kb",
        "Xmin",
        "Xmax",
    ]

    fit_res: dict = {}
    hfit_res: dict = {}
    my_res: dict = {}
    errors: dict = {}
    for ion, graph in graphs_for_fit.items():
        fit_res[ion] = graphs_for_fit[ion].Fit(f"func_birks_{ion}", "S")  # , "RS")
        hfit_res[ion] = r.TH1D(
            f"hFitRes{graph.GetName()}",
            "",
            len(labels_hfit_res),
            0,
            len(labels_hfit_res) - 1,
        )

        my_res[ion] = [
            fit_res[ion].Status(),
            fit_res[ion].Chi2(),
            fit_res[ion].Ndf(),
            fit_res[ion].Parameter(0),
            fit_res[ion].Parameter(1),
            fit_res[ion].Parameter(2),
            *range_fit[ion],
        ]
        errors[ion] = [
            0,  # no error on fit status
            0,  # no error on chi2
            0,  # no error on ndf
            fit_res[ion].ParError(0),
            fit_res[ion].ParError(1),
            fit_res[ion].ParError(2),
            0,  # no error on xmin
            0,  # no error on xmax
        ]
        for ilabel, (label, res, error) in enumerate(
            zip(labels_hfit_res, my_res[ion], errors[ion])
        ):
            ibin = ilabel + 1
            hfit_res[ion].GetXaxis().SetBinLabel(ibin, label)
            hfit_res[ion].SetBinContent(ibin, res)
            hfit_res[ion].SetBinError(ibin, error)

    c = r.TCanvas("c", "", 800, 800)

    for i, graph in enumerate(list(graphs_for_plot.values())):
        if i == 0:
            graph.Draw("ap")
            continue
        graph.Draw("p")

    for ion, f_birks in func_birks.items():
        f_birks.SetParameters(
            fit_res[ion].Parameter(0),
            fit_res[ion].Parameter(1),
            fit_res[ion].Parameter(2),
        )
        set_object_style(obj=f_birks, linecolor=color_fit[ion])
        f_birks.Draw("same")

    leg = r.TLegend(padleftmargin + 0.02, 0.75, 0.3, 0.90)
    leg.SetTextSize(0.035)
    leg.SetFillStyle(0)
    for ion, mydict in config["graph"]["legend"].items():
        for campaign, label in mydict.items():
            leg.AddEntry(graphs_for_plot[f"{ion}_{campaign}"], label, "p")
    leg.Draw()

    for (ion, xmin), (_, ymax), (_, color) in zip(
        xmin_tlatex.items(), ymax_tlatex.items(), color_fit.items()
    ):

        latex_fitpars = r.TLatex()
        xlatex_fitpars = xmin  # padleftmargin + 0.45
        ylatex_fitpars_max = ymax  # 0.9
        latex_fitpars.SetNDC()
        latex_fitpars.SetTextSize(0.028)
        latex_fitpars.SetTextAlign(13)  # align at top
        latex_fitpars.SetTextFont(42)
        unit = "mV"
        if "Charge" in label_yaxis:
            unit = "mV.s"
        latex_fitpars.DrawLatex(
            xlatex_fitpars,
            ylatex_fitpars_max,
            f"#color[{color}]{{S = {my_res[ion][3]:.3f} #pm {errors[ion][3]:.3f} {unit}.MeV^{{-1}}}}",
        )
        latex_fitpars.DrawLatex(
            xlatex_fitpars,
            ylatex_fitpars_max - 0.05,
            f"#color[{color}]{{A_{{0}} = {my_res[ion][4]:.3f} #pm {errors[ion][4]:.3f} MeV}}",
        )
        latex_fitpars.DrawLatex(
            xlatex_fitpars,
            ylatex_fitpars_max - 0.1,
            f"#color[{color}]{{K_{{B}} = {my_res[ion][5]:.6f} #pm {errors[ion][5]:.6f} MeV^{{-1}}}}",
        )

    c.Update()
    c.Draw()

    input("Enter")

    # # configure output with fit results
    # name_outfile: str = config["output"]["file"]
    # outfile: r.TFile = r.TFile(name_outfile, "recreate")

    # for _, graph in graphs.items():
    #     graph.Write()
    # # c.Write()
    # for _, hfit in hfit_res.items():
    #     hfit.Write()

    # outfile.Close()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    main(args.name_config_file)
