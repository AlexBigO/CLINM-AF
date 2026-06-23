"""
file: pid_systematics.py
brief: Draft script to get systematics on PID
usage: python3 pid_systematics.py
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

# FIXME I cannot manage to make it work (use TCutG with RDataFrame filter) :/

import uproot
import pandas as pd
import ROOT as r

mycut = r.TCutG()


@r.Numba.Declare(["double", "double"], "bool")
def cut_func(x, y):
    return 1  # mycut.IsInside(x, y)


@r.Numba.Declare(["double"], "bool")
def test_func(x):
    return True  # mycut.IsInside(x,y)


def get_rdf_from_rootfile(
    name_root_file: str, name_tree: str, name_branches: None | list[str], debug: bool
) -> r.RDataFrame:
    """
    Helper function to convert a TTree inside a .root file into a RDataFrame
    """

    return r.RDataFrame(name_tree, name_root_file)

    file = r.TFile(name_root_file, "read")
    tree = file.Get(name_tree)

    df = r.RDataFrame(tree)

    # df_cut = df.Filter()

    # file.Close()

    return df

    # auto dfCut = df.Filter(cutFunc, {"fDeltaECebr", "fDeltaEPl2"});

    # with uproot.open(name_root_file) as file:
    #     tree = file[name_tree]
    #     arrays = tree.arrays(name_branches, library="np")
    #     df = pd.DataFrame(arrays)
    #     nevents = len(df)
    #     if debug:
    #         print(arrays)
    #         print("\n")
    #         print(df)
    #         print(f"nevents = {nevents}\n")
    # return df


def get_tcutgs_from_rootfile(name_root_file: str):
    """
    ...
    """
    file = r.TFile(name_root_file, "read")

    cuts = []
    keys = file.GetListOfKeys()
    name_cuts = [key.GetName() for key in keys]

    for name_cut in name_cuts:
        cuts.append(file.Get(name_cut))

    file.Close()

    return cuts


def main(debug: bool) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - debug: bool
        Switch for debugging
    """
    if debug:
        print("Hello world!")

    # r.EnableImplicitMT(4)

    # open real data file
    name_infile_data: str = "/Users/abigot/CLINM/Data/CNAO_0925/CNAO0925_Run_06_post_processed.root"
    name_tree = "tree"
    name_branches = None
    df_data: r.RDataFrame = r.RDataFrame(
        name_tree, name_infile_data
    )  # get_rdf_from_rootfile(name_infile_data, name_tree, name_branches, debug=False)

    # open TCutG file
    name_file_cuts: str = "cutsDelta.root"
    cuts = get_tcutgs_from_rootfile(name_file_cuts)

    for icut, cut in enumerate(cuts):
        if icut > 0:
            continue

        mycut = cut

        # df_cut = df_data.Filter("Numba::cut_func(fDeltaECebr, fDeltaEPl2, cut)") # FIXME does not work
        df_cut = df_data.Filter("Numba::test_func", "fDeltaECebr")

    # apply each cut and retrieve the  number of entries


if __name__ == "__main__":
    DEBUG: bool = True
    main(DEBUG)
