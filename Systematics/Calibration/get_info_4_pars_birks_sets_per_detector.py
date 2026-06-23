"""
file: get_info_4_pars_birks_sets_per_detector.py
brief:
usage: python3 get_info_4_pars_birks_sets_per_detector.py cfg.yml
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
    print("Module 'logger' is not in the '../Utils/' directory. Add it to run this script.")

try:
    sys.path.append("../Utils/")
    from utils import fill_th1, get_h_config, enforce_list
except ModuleNotFoundError:
    print("Module 'utils' is not in the '../Utils/' directory. Add it to run this script.")

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
        edep = x[0] - par[3]
        s = par[0]
        a0 = par[1]
        kb = par[2]

        return (s * edep + a0) / (1 + kb * edep)


def inv_birks_law(a, par):
    """
    Inverse Birks law
    """
    s = par[0]
    a0 = par[1]
    kb = par[2]

    return (a - a0) / (s - a * kb)


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

    # FIXME: add to configuration ? add a 2nd cfg file?
    pars_birks = [2.784, 2.449, 0.015267]

    unc_pars_birks = [0.004, 0.009, 0.00005]

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
            "'input/real/file' and 'input/simulation/file'" " entries must be of same size!",
            "FATAL",
        )
    # TODO add safety for size comparison inside each entry of the dict name_infiles_real
    if not (isinstance(name_hist_fitres_real, str) and isinstance(name_hist_fitres_simu, str)):
        Logger(
            "'histfitres' options must be a single string (not a list)!",
            "FATAL",
        )

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

    # compute sigma
    sigma = 0
    n = 0
    for campaign, name_infiles_campaign in name_infiles_simu.items():
        for mean_real, mean_simu in zip(means_real[campaign], means_simu[campaign]):
            print(mean_real)
            x = mean_simu
            x_estimate = inv_birks_law(mean_real, pars_birks)
            sigma += (x - x_estimate) * (x - x_estimate)
            n += 1
    sigma /= n
    sigma = np.sqrt(sigma)
    print(sigma)

    # We have sigma :)

    sigma_arr = np.array([sigma])
    xmin, xmax = limits_xaxis[0], limits_xaxis[1]
    ymin, ymax = limits_yaxis[0], limits_yaxis[1]
    mydict = {
        "fSigma": sigma_arr,
        "fXmin": np.array([xmin]),
        "fXmax": np.array([xmax]),
        "fYmin": np.array([ymin]),
        "fYmax": np.array([ymax]),
    }
    df = r.RDF.FromNumpy(mydict)
    name_sigma_file: str = "info4ParBirksVariationsPlastic1.root"
    name_otree: str = "treePlastic1"
    df.Snapshot(name_otree, name_sigma_file)

    alpha = 3  # TODO make it configurable

    pars_birks.append(0)

    func_birks_for_plot = r.TF1("func_birks_for_plot", BirksLaw(), *limits_xaxis, 4)
    func_birks_for_plot.SetParNames("S", "A_0", "Kb")
    func_birks_for_plot.SetParameters(*pars_birks)
    func_birks_for_plot.GetXaxis().SetTitle(label_xaxis)
    func_birks_for_plot.GetYaxis().SetTitle(label_yaxis)
    func_birks_for_plot.GetXaxis().SetLimits(*limits_xaxis)
    func_birks_for_plot.GetYaxis().SetRangeUser(*limits_yaxis)
    set_object_style(obj=func_birks_for_plot, linecolor=color_fit, linewidth=2)

    # define upper band
    pars_birks[-1] = alpha * sigma
    func_birks_plusalpha_sigma = r.TF1("func_birks_plusalpha_sigma", BirksLaw(), *limits_xaxis, 4)
    func_birks_plusalpha_sigma.SetParameters(*pars_birks)
    # define lower band
    pars_birks[-1] = -alpha * sigma
    func_birks_minusalpha_sigma = r.TF1("func_birks_minusalpha_sigma", BirksLaw(), *limits_xaxis, 4)
    func_birks_minusalpha_sigma.SetParameters(*pars_birks)

    # reset Edep translation in Birks law
    pars_birks[-1] = 0
    # define variation function
    func_birks_variation = r.TF1("func_birks_variation", BirksLaw(), *limits_xaxis, 4)

    # define alpha per parameter
    alpha_per_par = 1
    alpha_mapping = np.arange(-alpha_per_par, alpha_per_par + 1, 1)
    # remove nominal calibration (where alpha_per_par = 0)
    alpha_mapping = np.delete(alpha_mapping, np.where(alpha_mapping == 0))
    pars_birks_np = np.array(pars_birks[:-1]).reshape(
        3, 1
    )  # reshape to allow the sum of arrays below
    unc_pars_birks_np = np.array(unc_pars_birks)
    pars_values = pars_birks_np + np.array([alpha_mapping * unc for unc in unc_pars_birks_np])

    print(f"Number of triplets evaluated: {np.size(pars_values, axis=1)}\n")

    pars_triplets = []
    for par0_value in pars_values[0]:
        for par1_value in pars_values[1]:
            for par2_value in pars_values[2]:
                pars_triplets.append([par0_value, par1_value, par2_value])

    # pars_birks[0] += 30 * unc_pars_birks[0]
    # func_birks_par0_variations = []
    # func_birks_par0_variations.append(
    #     r.TF1("func_birks_par0_variation_2", BirksLaw(), *limits_xaxis, 4)
    # )
    # func_birks_par0_variations[-1].SetParameters(*pars_birks)

    # possible_par0_variations = []

    id_to_rm_in_pars_triplets = []
    pars_triplets_to_keep = []

    for i, pars_triplet in enumerate(pars_triplets):
        func_birks_variation.SetParameters(*pars_triplet, 0)
        # condition to check that upper alpha-sigma band is above
        # and lower alpha-sigma band is below
        is_inside = False
        for x in np.linspace(*limits_xaxis, 100):
            y_upper_alpha_sigma_band = func_birks_minusalpha_sigma.Eval(x)
            y_lower_alpha_sigma_band = func_birks_plusalpha_sigma.Eval(x)
            y = func_birks_variation.Eval(x)
            is_inside = (y_upper_alpha_sigma_band > y) and (y_lower_alpha_sigma_band < y)
            if not is_inside:
                # print(f"Triplet {pars_triplet} of position {i}")
                id_to_rm_in_pars_triplets.append(i)
                break
        if is_inside:
            pars_triplets_to_keep.append(pars_triplet)
        # if not is_inside:
        #     print("\n")
        #     print(x)
        #     print(y_upper_alpha_sigma_band)
        #     print(y)
        #     print(y_lower_alpha_sigma_band)
        #     print("\n")
        #     break

    print(f"Number of triplets to keep: {len(pars_triplets_to_keep)}\n")

    # TODO find a way to keep only pars triplets passing through the "band condition"

    do_plot = False

    if do_plot:
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

        c = r.TCanvas("c", "", 800, 800)
        func_birks_for_plot.Draw()
        func_birks_plusalpha_sigma.SetLineColor(r.kRed)
        func_birks_plusalpha_sigma.Draw("same")
        func_birks_minusalpha_sigma.SetLineColor(r.kBlue)
        func_birks_minusalpha_sigma.Draw("same")
        # for func in func_birks_par0_variations:
        #     func.Draw("same")
        for i, graph in enumerate(list(graphs_for_plot.values())):
            if i == 0:
                graph.Draw("p")
                continue
            graph.Draw("p")

        c.Update()
        c.Draw()

        input("Enter")


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    main(args.name_config_file)
