"""
file: fit.py
brief: Script to fit amplitude and/or charge distributions of scintillators
usage: python3 fit.py cfg.yml
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
    from utils import fill_th1, get_h_config
except ModuleNotFoundError:
    print(
        "Module 'utils' is not in the '../Utils/' directory. Add it to run this script."
    )


# pylint:disable=too-many-locals
def main(name_config_file: str) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file
    """

    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    # handle input
    name_infile = config["input"]["file"]
    name_tree: str = config["input"]["tree"]["name"]
    name_branches: list[str] = config["input"]["tree"]["branches"]

    h_configs = []
    histogram_cfg = config["histogram_config"]

    # safeties
    if isinstance(name_branches, list) and isinstance(histogram_cfg["name"], list):
        if len(name_branches) != len(histogram_cfg["name"]):
            Logger(
                "'input/branches' and 'histogram_config/name' must be of same size!",
                "FATAL",
            )

    for i, _ in enumerate(name_branches):
        h_configs.append(get_h_config(histogram_cfg, i))

    # convert input .root file into pandas dataframe
    df: pd.DataFrame = uproot.open(name_infile)[name_tree].arrays(
        name_branches, library="pd"
    )

    hists = []
    for name, h_config in zip(name_branches, h_configs):
        hists.append(fill_th1(df[name], h_config))

    # configure output with fit results
    name_outfile: str = config["output"]["name"]
    outfile: r.TFile = r.TFile(name_outfile, "recreate")
    for hist in hists:
        hist.Write()

    # config of fit result storage
    labels_hfit_res: list[str] = [
        "FitStatus",
        "Chi2",
        "NDF",
        "Constant",
        "Mean",
        "Sigma",
        "Xmin",
        "Xmax",
    ]

    hfit_results = []

    # add a fitting procedure
    for i, (hist, range_fit) in enumerate(zip(hists, config["fit"]["range"])):
        mean: float = hist.GetMean()
        sigma: float = hist.GetStdDev()

        func: r.TF1 = r.TF1("func", "gaus", *range_fit, 3)
        func.SetParameter(1, mean)
        func.SetParameter(2, sigma)

        fit_res = hist.Fit(func, "RS")

        hfit_res = r.TH1D(
            f"hFitRes{hist.GetName()}",
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
        for ilabel, (label, res, error) in enumerate(
            zip(labels_hfit_res, my_res, errors)
        ):
            ibin = ilabel + 1
            hfit_res.GetXaxis().SetBinLabel(ibin, label)
            hfit_res.SetBinContent(ibin, res)
            hfit_res.SetBinError(ibin, error)

        hfit_results.append(hfit_res)

    # save in output file
    for hist in hists:
        name = hist.GetName()
        hist.SetName(f"QA_{name}")
        hist.Write()
    for hfit_res in hfit_results:
        hfit_res.Write()
    outfile.Close()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    main(args.name_config_file)
