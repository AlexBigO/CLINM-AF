"""
file: fit_with_gauss.py
brief: Script to fit amplitude and/or charge distributions of scintillators
usage: python3 fit_with_gauss.py cfg.yml
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
    from numpy import mean as npmean
    from numpy import std as npstd
except ModuleNotFoundError:
    print("Module 'uproot' is not installed. Please install it to run this script.")


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
    from utils import fill_th1, get_h_config, configure_canvas
except ModuleNotFoundError:
    print(
        "Module 'utils' is not in the '../Utils/' directory. Add it to run this script."
    )

try:
    sys.path.append("../Utils/")
    from fit_utils import lorentzian, plot_fit, LanGaus, langaufun
except ModuleNotFoundError:
    print(
        "Module 'fit_utils' is not in the '../Utils/' directory. Add it to run this script."
    )

try:
    sys.path.append("../Utils/")
    from style_formatter import set_global_style, set_object_style
except ModuleNotFoundError:
    print(
        "Module 'style_formatter' is not in the '../Utils/' directory. Add it to run this script."
    )

IDX_TO_TEST = (
    None  # index of the distribution list to select when testing individual fits
)

NAME_PARS_GAUSS = ["mu_gauss", "sigma_gauss", "norm"]
LABELS_HFIT_RES_GAUSS: list[str] = [
    "FitStatus",
    "Chi2OverNdf",
    "Xmin",
    "Xmax",
    "x_{MPV}",
    "#sigma_{MPV}",
    # "#rho_{#sigma_{l}, #sigma_{g}}",
] + NAME_PARS_GAUSS

# NAME_PARS = ["MPV_landau", "sigma_landau", "mu_gauss", "sigma_gauss", "norm"]
# LABELS_HFIT_RES: list[str] = [
#     "FitStatus",
#     "Chi2OverNdf",
#     "Xmin",
#     "Xmax",
#     "x_{MPV}",
#     "#sigma_{MPV}",
#     "#rho_{#sigma_{l}, #sigma_{g}}",
# ] + NAME_PARS


def propagate_unc(sigma1: float, sigma2: float, rho12: float) -> float:
    """
    Helper function to propagate uncertainties

    Parameters
    ------------------------------------------------
    - sigma1: float
        Uncertainty on variable 1

    - sigma2: float
        Uncertainty on variable 2

    - rho12: float
        Correlation factor of sigma1 and sigma2

    Returns
    ------------------------------------------------
    - sigma: float
        Propagated uncertainty
    """

    return np.sqrt(sigma1**2 + sigma2**2 + 2 * rho12 * sigma1 * sigma2)


# pylint:disable=too-many-locals,too-many-branches,too-many-statements
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

    # handle input
    name_infile = config["input"]["file"]
    name_tree: str = config["input"]["tree"]["name"]
    name_branches: list[str] = config["input"]["tree"]["branches"]
    init_pars_fit = config["fit"]["pars"]
    ranges_fit = config["fit"]["range"]
    h_configs = []
    histogram_cfg = config["histogram_config"]
    histogram_cfg["range"] = ranges_fit

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
    name_outfile: str = config["output"]["file"]
    name_pdf_outfile: str = name_outfile.replace(".root", str()) + ".pdf"
    outfile: r.TFile = r.TFile(name_outfile, "recreate")
    for hist in hists:
        hist.Write()

    hfit_results = []
    hfit_correlations = []

    exp: str = config["output"]["plot"]["info"]["exp"]
    campaign: str = config["output"]["plot"]["info"]["campaign"]
    particle_beam: str = config["output"]["plot"]["info"]["beam"]["particle"]
    energy_beam: str = config["output"]["plot"]["info"]["beam"]["energy"]
    run_number: str = str(config["output"]["plot"]["info"]["run"])

    # add a fitting procedure
    for i, (
        hist,
        name_branch,
        name_data,
        nbin,
        range_fit,
        init_par0,
        init_par1,
        init_par2,
        ymin_canvas,
        ymax_canvas,
    ) in enumerate(
        zip(
            hists,
            name_branches,
            histogram_cfg["name"],
            histogram_cfg["nbin"],
            ranges_fit,
            init_pars_fit[NAME_PARS_GAUSS[0]],
            init_pars_fit[NAME_PARS_GAUSS[1]],
            init_pars_fit[NAME_PARS_GAUSS[2]],
            config["output"]["plot"]["ymin"],
            config["output"]["plot"]["ymax"],
        )
    ):

        if i != IDX_TO_TEST and IDX_TO_TEST is not None:
            continue

        if "Charge" in name_branch:
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

        Logger(f"Start fit of {name_branch}\n", "INFO")

        data = df[name_branch].to_numpy()

        x = r.RooRealVar(name_branch, f"x{i}", *range_fit)

        x.setBins(nbin)

        frame = x.frame()

        dataset = r.RooDataSet.from_numpy({name_branch: data}, [x])

        # Construct gauss(t,mg,sg)
        mg = r.RooRealVar(NAME_PARS_GAUSS[0], NAME_PARS_GAUSS[0], *init_par0)
        sg = r.RooRealVar(NAME_PARS_GAUSS[1], NAME_PARS_GAUSS[1], *init_par1)
        gauss = r.RooGaussian("gauss", "gauss", x, mg, sg)

        # add norm
        norm = r.RooRealVar(NAME_PARS_GAUSS[2], NAME_PARS_GAUSS[2], *init_par2)

        model = r.RooAddPdf("model", "model", [gauss], [norm])

        fit_res = model.fitTo(
            dataset, r.RooFit.NumCPU(10), Save=True
        )  # , Range="fit_range"        )

        hfit_correlation = fit_res.correlationHist()
        hfit_correlation.SetName(f"hFitCorrelation{name_data}")
        hfit_correlations.append(hfit_correlation)

        func_model = model.asTF(r.RooArgList(x))
        # get most probable value (MPV)
        x_mpv: float = func_model.GetMaximumX()
        # compute uncertainty on MPV by doing some weighted sum in quadrature
        s_mpv = fit_res.floatParsFinal().find("mu_gauss").getAsymErrorHi()

        ##########
        # Plot
        xmin = range_fit[0]
        xmax = range_fit[1]
        ymin = 0
        if ymin_canvas != "auto":
            ymin = ymin_canvas

        ymax = 1.05 * hist.GetMaximum()
        if ymax_canvas != "auto":
            ymax = ymax_canvas
        title = f";{config['output']['plot']['label'][i]}; Entries;"
        c = configure_canvas(f"c_{i}", xmin, ymin, xmax, ymax, title)
        c.Update()
        c.Draw()
        # c = r.TCanvas(f"c_{i}", "My TCanvas", 600, 600)
        dataset.plotOn(frame, MarkerStyle=r.kFullCircle)
        model.plotOn(frame, LineColor=r.kAzure + 4, LineWidth=2, MoveToBack=True)
        frame.Draw("same")
        ##########

        # Use fit result
        hfit_res = r.TH1D(
            f"hFitRes{name_data}",
            "",
            len(LABELS_HFIT_RES_GAUSS),
            0,
            len(LABELS_HFIT_RES_GAUSS) - 1,
        )
        my_res = [fit_res.status(), frame.chiSquare(), *range_fit, x_mpv, s_mpv]

        errors = [
            0,  # no error on fit status
            0,  # no error on chi2
            0,  # no error on xmin
            0,  # no error on xmax
            0,  # no error on x_mpv
            0,  # no error on s_mpv
        ]

        for name_par in NAME_PARS_GAUSS:
            my_res.append(fit_res.floatParsFinal().find(name_par).getValV())
            errors.append(fit_res.floatParsFinal().find(name_par).getAsymErrorHi())

        for ilabel, (label, res, error) in enumerate(
            zip(LABELS_HFIT_RES_GAUSS, my_res, errors)
        ):
            ibin = ilabel + 1
            hfit_res.GetXaxis().SetBinLabel(ibin, label)
            hfit_res.SetBinContent(ibin, res)
            hfit_res.SetBinError(ibin, error)

        hfit_results.append(hfit_res)

        # add a legend
        if "Charge" in name_branch:
            leg = r.TLegend(padleftmargin + 0.45, 0.8, 0.87, 0.9)
        elif "Amplitude" in name_branch:
            leg = r.TLegend(padleftmargin + 0.53, 0.8, 0.87, 0.9)
        else:
            leg = r.TLegend(padleftmargin + 0.62, 0.8, 0.95, 0.9)
        leg.SetTextSize(0.035)
        leg.SetFillStyle(0)
        leg.AddEntry(dataset, "Data", "p")
        leg.AddEntry(model, "Gauss", "l")

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
            padleftmargin + 0.55 if "Amplitude" in name_branch else padleftmargin + 0.5
        )
        if "EnergyDeposit" in name_branch:
            xlatex_fitpars = padleftmargin + 0.56
        ylatex_fitpars_max = 0.75
        latex_fitpars.SetNDC()
        latex_fitpars.SetTextSize(0.03)
        latex_fitpars.SetTextAlign(13)  # align at top
        latex_fitpars.SetTextFont(42)
        latex_fitpars.DrawLatex(
            xlatex_fitpars, ylatex_fitpars_max, f"#chi^{{2}} / ndf = {my_res[1]:.2f}"
        )
        # latex_fitpars.DrawLatex(
        #     xlatex_fitpars,
        #     ylatex_fitpars_max - 0.05,
        #     f"m_{{l}} = {my_res[5]:.3f} #pm {errors[5]:.3f}",
        # )
        # latex_fitpars.DrawLatex(
        #     xlatex_fitpars,
        #     ylatex_fitpars_max - 0.05,
        #     f"#sigma_{{l}} = {my_res[8]:.3f} #pm {errors[8]:.3f}",
        # )
        # # latex_fitpars.DrawLatex(
        # #     xlatex_fitpars,
        # #     ylatex_fitpars_max - 0.15,
        # #     f"m_{{g}} = {my_res[7]:.3f} #pm {errors[7]:.3f}",
        # # )
        # latex_fitpars.DrawLatex(
        #     xlatex_fitpars,
        #     ylatex_fitpars_max - 0.10,
        #     f"#sigma_{{g}} = {my_res[10]:.3f} #pm {errors[10]:.3f}",
        # )
        # latex_fitpars.DrawLatex(
        #     xlatex_fitpars,
        #     ylatex_fitpars_max - 0.15,
        #     f"#rho_{{ #sigma_{{l}} #sigma_{{ g }} }} = {my_res[6]:.3f}",
        # )
        latex_fitpars.DrawLatex(
            xlatex_fitpars,
            ylatex_fitpars_max - 0.05,
            f"MPV = {my_res[4]:.4f} #pm {my_res[5]:.4f}",
        )

        c.Update()
        c.Draw()
        c.Write()

        if i == IDX_TO_TEST and IDX_TO_TEST is not None:
            c.Print(name_pdf_outfile)
            continue

        if len(name_branches) == 1:
            c.Print(name_pdf_outfile)
        else:
            if i == 0:
                c.Print(f"{name_pdf_outfile}(")
            elif i == len(name_branches) - 1:
                c.Print(f"{name_pdf_outfile})")
            else:
                c.Print(name_pdf_outfile)

    # save in output file
    for hfit_res, hfit_correlation in zip(hfit_results, hfit_correlations):
        hfit_res.Write()
        hfit_correlation.Write()
    outfile.Close()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    main(args.name_config_file)
