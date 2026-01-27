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
    if len(name_infiles_real) != len(name_infiles_simu):
        Logger(
            "'input/real/file' and 'input/simulation/file'"
            " entries must be of same size!",
            "FATAL",
        )
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

    campaigns = list(name_infiles_real.keys())

    means_real = {}
    sigmas_real = {}
    means_simu = {}
    sigmas_simu = {}

    for campaign, name_infiles_campaign in name_infiles_real.items():
        means_real[campaign] = []
        sigmas_real[campaign] = []
        for name_infile_real in name_infiles_campaign:
            infile_real: r.TFile = r.TFile.Open(name_infile_real)
            hist_real: r.TH1 = infile_real.Get(name_hist_fitres_real)
            means_real[campaign].append(hist_real.GetBinContent(number_mean_bin))
            sigmas_real[campaign].append(hist_real.GetBinContent(number_sigma_bin))
            infile_real.Close()

    for campaign, name_infiles_campaign in name_infiles_simu.items():
        means_simu[campaign] = []
        sigmas_simu[campaign] = []
        for name_infile_simu in name_infiles_campaign:
            infile_simu: r.TFile = r.TFile.Open(name_infile_simu)
            hist_simu: r.TH1 = infile_simu.Get(name_hist_fitres_simu)
            means_simu[campaign].append(hist_simu.GetBinContent(number_mean_bin))
            sigmas_simu[campaign].append(hist_simu.GetBinContent(number_sigma_bin))
            infile_simu.Close()

    # for name_infile_real in name_infiles_real:
    #     infile_real: r.TFile = r.TFile.Open(name_infile_real)
    #     hist_real: r.TH1 = infile_real.Get(name_hist_fitres_real)
    #     means_real.append(hist_real.GetBinContent(number_mean_bin))
    #     sigmas_real.append(hist_real.GetBinContent(number_sigma_bin))
    #     # sigmas_real.append(0.01 * means_real[-1]) # FIXME TEST
    #     infile_real.Close()

    # for name_infile_simu in name_infiles_simu:
    #     infile_simu: r.TFile = r.TFile.Open(name_infile_simu)
    #     hist_simu: r.TH1 = infile_simu.Get(name_hist_fitres_simu)
    #     means_simu.append(hist_simu.GetBinContent(number_mean_bin))
    #     sigmas_simu.append(hist_simu.GetBinContent(number_sigma_bin))
    #     infile_simu.Close()

    # create TGraphErrors for fit
    x, unc_x = [], []
    y, unc_y = [], []
    for campaign in campaigns:
        x.extend(means_simu[campaign])
        unc_x.extend(sigmas_simu[campaign])
        y.extend(means_real[campaign])
        unc_y.extend(sigmas_real[campaign])

    range_fit = [min(x), max(x)]
    x = np.array(x)
    unc_x = np.array(unc_x)
    y = np.array(y)
    unc_y = np.array(unc_y)
    graph_for_fit = r.TGraphErrors(len(x), x, y, unc_x, unc_y)
    graph_for_fit.SetName(f"{name_graph}")
    # create TGraphErrors for plot
    x, unc_x = {}, {}
    y, unc_y = {}, {}
    graphs_for_plot = {}
    for campaign in campaigns:
        x[campaign] = np.array(means_simu[campaign])
        unc_x[campaign] = np.array(sigmas_simu[campaign])
        y[campaign] = np.array(means_real[campaign])
        unc_y[campaign] = np.array(sigmas_real[campaign])
        graphs_for_plot[campaign] = r.TGraphErrors(
            len(x[campaign]), x[campaign], y[campaign], unc_x[campaign], unc_y[campaign]
        )

    for campaign, graph in graphs_for_plot.items():
        graph.SetName(f"{name_graph}_{campaign}")
        graph.GetXaxis().SetTitle(label_xaxis)
        graph.GetYaxis().SetTitle(label_yaxis)
        graph.GetXaxis().SetLimits(*limits_xaxis)
        graph.GetYaxis().SetRangeUser(*limits_yaxis)
        set_object_style(
            obj=graph,
            color=color_graph[campaign],
            markerstyle=markerstyle_graph[campaign],
        )

    # configure fit
    # func_birks = r.TF1("func_birks", BirksLaw(), *range_fit, 3)
    # func_birks.SetParNames("S", "A_0", "Kb")
    # range_fit = config["fit"]["range"]
    func_birks = r.TF1("func_birks", BirksLaw(), *range_fit, 3)
    func_birks.SetParNames("S", "A_0", "Kb")
    # kb = 0.126 / 2  # 0.008 / 1.02 / 2
    # func_birks.FixParameter(2, kb)
    # set_object_style(obj=func_birks, linecolor=color_fit, linewidth=2)

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
    fit_res = graph_for_fit.Fit("func_birks", "S")  # , "RS")
    hfit_res = r.TH1D(
        f"hFitRes{graph_for_fit.GetName()}",
        "",
        len(labels_hfit_res),
        0,
        len(labels_hfit_res) - 1,
    )

    my_res = [
        fit_res.Status(),
        fit_res.Chi2(),
        fit_res.Ndf(),
        fit_res.Parameter(0),
        fit_res.Parameter(1),
        fit_res.Parameter(2),
        *range_fit,
    ]
    errors = [
        0,  # no error on fit status
        0,  # no error on chi2
        0,  # no error on ndf
        fit_res.ParError(0),
        fit_res.ParError(1),
        fit_res.ParError(2),
        0,  # no error on xmin
        0,  # no error on xmax
    ]
    for ilabel, (label, res, error) in enumerate(zip(labels_hfit_res, my_res, errors)):
        ibin = ilabel + 1
        hfit_res.GetXaxis().SetBinLabel(ibin, label)
        hfit_res.SetBinContent(ibin, res)
        hfit_res.SetBinError(ibin, error)

    c = r.TCanvas("c", "", 800, 800)

    func_birks_for_plot = r.TF1("func_birks_for_plot", BirksLaw(), *limits_xaxis, 3)
    func_birks_for_plot.SetParNames("S", "A_0", "Kb")
    func_birks_for_plot.SetParameters(
        fit_res.Parameter(0), fit_res.Parameter(1), fit_res.Parameter(2)
    )
    func_birks_for_plot.GetXaxis().SetTitle(label_xaxis)
    func_birks_for_plot.GetYaxis().SetTitle(label_yaxis)
    func_birks_for_plot.GetXaxis().SetLimits(*limits_xaxis)
    func_birks_for_plot.GetYaxis().SetRangeUser(*limits_yaxis)
    set_object_style(obj=func_birks_for_plot, linecolor=color_fit, linewidth=2)

    # set_object_style(obj=f_birks, linecolor=color_fit[campaign])
    func_birks_for_plot.Draw()

    for i, graph in enumerate(list(graphs_for_plot.values())):
        if i == 0:
            graph.Draw("p")
            continue
        graph.Draw("p")

    leg = r.TLegend(padleftmargin + 0.05, 0.75, 0.3, 0.90)
    leg.SetTextSize(0.035)
    leg.SetFillStyle(0)
    for campaign, label in config["graph"]["legend"].items():
        leg.AddEntry(graphs_for_plot[campaign], label, "p")
    leg.Draw()

    latex_fitpars = r.TLatex()
    xlatex_fitpars = xmin_tlatex  # padleftmargin + 0.45
    ylatex_fitpars_max = ymax_tlatex  # 0.9
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
        f"#color[{color_fit}]{{S = {my_res[3]:.3f} #pm {errors[3]:.3f} {unit}.MeV^{{-1}}}}",
    )
    latex_fitpars.DrawLatex(
        xlatex_fitpars,
        ylatex_fitpars_max - 0.05,
        f"#color[{color_fit}]{{A_{{0}} = {my_res[4]:.3f} #pm {errors[4]:.3f} MeV}}",
    )
    latex_fitpars.DrawLatex(
        xlatex_fitpars,
        ylatex_fitpars_max - 0.1,
        f"#color[{color_fit}]{{K_{{B}} = {my_res[5]:.6f} #pm {errors[5]:.6f} MeV^{{-1}}}}",
    )

    c.Update()
    c.Draw()

    input("Enter")

    # configure output with fit results
    name_outfile: str = config["output"]["file"]
    name_pdf_outfile: str = name_outfile.replace(".root", str()) + ".pdf"
    outfile: r.TFile = r.TFile(name_outfile, "recreate")

    for _, graph in graphs_for_plot.items():
        graph.Write()
    graph_for_fit.Write()
    # c.Write()
    hfit_res.Write()

    c.Print(name_pdf_outfile)

    outfile.Close()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    main(args.name_config_file)
