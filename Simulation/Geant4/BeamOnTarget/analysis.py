"""
file: analysis.py
brief: Script to analyse data from BeamOnTarget G4 simulation
usage: python3 analysis.py
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import uproot
import pandas as pd
import ROOT as r


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

    name_infiles: list[str] = [
        "./build/output0_t0.root",
        "./build/output0_t1.root",
        "./build/output0_t2.root",
        "./build/output0_t3.root",
    ]
    name_tree: str = "tree"
    dfs: list[pd.DataFrame] = []

    for name_infile in name_infiles:
        with uproot.open(name_infile) as file:
            tree = file[name_tree]
            arrays = tree.arrays(library="np")
            dfs.append(pd.DataFrame(arrays))

    # print(dfs[0])

    while len(dfs) > 1:
        df_merged = pd.concat([dfs[0], dfs[1]], axis=0, ignore_index=True)
        dfs.pop(1)
        dfs[0] = df_merged

    df = dfs[0]

    # print(df)

    name_particle = "C12"
    ken_pre_target = df.query(
        f"nameDet == 'DetPreTarget' and ParticleName == '{name_particle}'", inplace=False
    )["Ekin_MeV"]
    ken_post_target = (
        df.query(
            f"nameDet == 'DetPostTarget' and ParticleName == '{name_particle}'", inplace=False
        )["Ekin_MeV"]
        / 12.0
    )

    print(
        f"Kinetic energy before target (MeV/u): {ken_pre_target.mean():.4f} +- {ken_pre_target.std():.4f}"
    )
    print("\n")
    print(
        f"Kinetic energy after target (MeV/u): {ken_post_target.mean():.4f} +-  {ken_post_target.std():.4f}"
    )

    h_config = ("aha", "; Energy (MeV); counts", 70, 110, 140)

    hist = r.TH1D(*h_config)
    for entry in ken_post_target.to_numpy():
        hist.Fill(entry)

    hist.Sumw2()
    hist.SetDirectory(0)

    c = r.TCanvas("c", "c", 800, 800)
    hist.Draw("ehist")
    c.Update()
    c.Draw()
    input("Press enter")


if __name__ == "__main__":
    DEBUG: bool = True
    main(DEBUG)
