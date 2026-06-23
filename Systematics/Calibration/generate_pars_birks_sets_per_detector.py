"""
file: generate_pars_birks_sets_per_detector.py
brief:
usage: python3 generate_pars_birks_sets_per_detector.py
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

from sys import exit as sys_exit

import pandas as pd
import uproot
import numpy as np
import ROOT as r


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


def get_df_pars_triplets(
    pars_birks, unc_pars_birks, name_infile, name_tree, do_rdf=True, debug=False
):
    """Helper function to get RDataFrame for parameters triplets

    Args:
        pars_birks (_type_): _description_
        unc_pars_birks (_type_): _description_
        name_infile (_type_): _description_
        name_tree (_type_): _description_
        do_rdf (bool, optional): _description_. Defaults to True.
        debug (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """

    name_branches = ["fSigma", "fXmin", "fXmax", "fYmin", "fYmax"]

    with uproot.open(name_infile) as f:
        tree = f[name_tree]
        arrays = tree.arrays(name_branches, library="np")

    sigma = arrays["fSigma"][0]
    limits_xaxis = [arrays["fXmin"][0], arrays["fXmax"][0]]
    limits_yaxis = [arrays["fYmin"][0], arrays["fYmax"][0]]

    if debug:
        print(f"sigma = {sigma}")

    alpha = 1  # TODO make it configurable
    alpha_per_par = 1

    pars_birks.append(0)

    # FIXME
    label_xaxis: str = "Edep (MeV)"
    label_yaxis: str = "Amplitude (mV)"

    func_birks_for_plot = r.TF1("func_birks_for_plot", BirksLaw(), *limits_xaxis, 4)
    func_birks_for_plot.SetParNames("S", "A_0", "Kb", "Xtranslation")
    func_birks_for_plot.SetParameters(*pars_birks)
    func_birks_for_plot.GetXaxis().SetTitle(label_xaxis)
    func_birks_for_plot.GetYaxis().SetTitle(label_yaxis)
    func_birks_for_plot.GetXaxis().SetLimits(*limits_xaxis)
    func_birks_for_plot.GetYaxis().SetRangeUser(*limits_yaxis)

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
    alpha_mapping = np.arange(-alpha_per_par, alpha_per_par + 1, 1)
    # remove nominal calibration (where alpha_per_par = 0)
    alpha_mapping = np.delete(alpha_mapping, np.where(alpha_mapping == 0))
    pars_birks_np = np.array(pars_birks[:-1]).reshape(
        3, 1
    )  # reshape to allow the sum of arrays below
    unc_pars_birks_np = np.array(unc_pars_birks)
    pars_values = pars_birks_np + np.array([alpha_mapping * unc for unc in unc_pars_birks_np])

    if debug:
        print(f"Number of triplets evaluated: {np.size(pars_values, axis=1)}\n")
        print(f"Parameters values: {pars_values}")

    pars_triplets = []
    for par0_value in pars_values[0]:
        for par1_value in pars_values[1]:
            for par2_value in pars_values[2]:
                pars_triplets.append([par0_value, par1_value, par2_value])

    pars_triplets_to_keep = []

    for _, pars_triplet in enumerate(pars_triplets):
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
                break
        if is_inside:
            pars_triplets_to_keep.append(pars_triplet)

    # return pars_triplets_to_keep

    if debug:
        print(f"Number of possible combinations: {np.size(pars_values, axis=1)**3}")
        print(f"Number of triplets to keep: {len(pars_triplets_to_keep)}\n")

    df = pd.DataFrame(pars_triplets_to_keep, columns=["fPar0", "fPar1", "fPar2"])
    if debug:
        print(f"Parameters triplets in the band:\n {df}")

    if not do_rdf:
        return df

    return r.RDF.FromPandas(df)


def write_rdf(rdf, name_file, name_tree, option: str = "RECREATE") -> None:
    """Helpet function to write RDataFrame to a file

    Args:
        rdf (_type_): _description_
        name_file (_type_): _description_
        name_tree (_type_): _description_
        option (str, optional): _description_. Defaults to "RECREATE".
    """
    # safety
    if option not in ["RECREATE", "UPDATE"]:
        print("Wrong 'option' in write_rdf!")
        sys_exit(1)

    snapshot_options = r.RDF.RSnapshotOptions()
    snapshot_options.fMode = option

    rdf.Snapshot(name_tree, name_file, "", snapshot_options)


def main(debug: bool) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - debug: bool
        Switch for debugging
    """
    if debug:
        print("Debug mode activated!")

    pars_birks_all: dict = {
        "Plastic1": [2.784, 2.449, 0.015267],
        "Plastic2": [2.784, 2.449, 0.015267],  # FIXME
        "Cebr": [2.784, 2.449, 0.015267],  # FIXME
    }

    unc_pars_birks_all: dict = {
        "Plastic1": [0.004, 0.009, 0.00005],
        "Plastic2": [0.004, 0.009, 0.00005],  # FIXME
        "Cebr": [0.004, 0.009, 0.00005],  # FIXME
    }

    name_infiles: dict = {
        "Plastic1": "info4ParBirksVariationsPlastic1.root",
        "Plastic2": "info4ParBirksVariationsPlastic1.root",  # FIXME
        "Cebr": "info4ParBirksVariationsPlastic1.root",  # FIXME
    }

    name_trees: dict = {
        "Plastic1": "treePlastic1",
        "Plastic2": "treePlastic1",  # FIXME
        "CeBr": "treePlastic1",  # FIXME
    }

    rdfs = {}

    # arrays = {}

    # for (det, pars_birks), (_, unc_pars_birks), (_, name_infile), (_, name_tree) in zip(
    #     pars_birks_all.items(), unc_pars_birks_all.items(), name_infiles.items(), name_trees.items()
    # ):
    #     arrays[det] = get_df_pars_triplets(
    #         pars_birks, unc_pars_birks, name_infile, name_tree, do_rdf=True, debug=True
    #     )

    # size = 1
    # for key, arr in arrays.items():
    #     size *= len(arr)
    # print(f"Total number of combinatorics: {size}")

    # # loop over all detectors parameters
    # arrays_all = []
    # for pars_triplet_plastic1 in arrays["Plastic1"]:
    #     for pars_triplet_plastic2 in arrays["Plastic2"]:
    #         for pars_triplet_cebr in arrays["Cebr"]:
    #             arrays_all.append(pars_triplet_plastic1 + pars_triplet_plastic2 + pars_triplet_cebr)

    # df = pd.DataFrame(np.array(arrays_all))

    # print(df.head())

    for (det, pars_birks), (_, unc_pars_birks), (_, name_infile), (_, name_tree) in zip(
        pars_birks_all.items(), unc_pars_birks_all.items(), name_infiles.items(), name_trees.items()
    ):
        rdf = get_df_pars_triplets(
            pars_birks, unc_pars_birks, name_infile, name_tree, do_rdf=True, debug=True
        )
        rdfs[det] = rdf

    name_ofile = "info4ParBirksVariationsAll.root"

    for i, (det, rdf) in enumerate(rdfs.items()):
        option = "RECREATE"
        if i > 0:
            option = "UPDATE"
        write_rdf(rdf, name_ofile, f"tree{det}", option)


if __name__ == "__main__":
    DEBUG: bool = True
    main(DEBUG)
