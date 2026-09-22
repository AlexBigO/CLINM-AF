"""
file: analysis.py
brief: Script to analyse data from BeamOnTarget G4 simulation
usage: python3 analysis.py
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import uproot
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import constants

# import ROOT as r

# mass of 1 amu in kg * (speed of light)**2 / 1 eV in Joules
amu_in_ev_manual = (constants.atomic_mass * (constants.c**2)) / constants.eV
amu_mev = 1.0e-6 * amu_in_ev_manual


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
    name_tree: str = "Tracks"
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

    # sels: str = "MotherName == 'C12'" + " and " + "Particle == 'alpha'" + " and  " + "ParentID == 1"
    sels: str = (
        "MotherName == 'C12'" + " and  " + "ParentID == 1" + " and " + "TargetName != 'none'"
    )

    df.query(sels, inplace=True)

    # df.query("Ndaughters < 5", inplace=True)

    print(df)

    # return

    df["Etot_MeV"] = df["Mass_MeV"] + df["Ekin_MeV"]

    # if debug:

    #     df["MyMotherEtot_MeV"] = np.sqrt(df["MotherMass_MeV"] ** 2 + df["MotherMomentum_MeV"] ** 2)

    #     mass_number_mother = 12
    #     df["MyMotherEtotV2_Mev"] = (
    #         mass_number_mother * 931.494028 - 6 * 0.511 + df["MotherEkin_MeV"]
    #     )
    #     # df["MyMotherEtotV2_Mev"] = df["MotherMass_MeV"] + df["MotherEkin_MeV"]

    #     cols = [
    #         "MotherMass_MeV",
    #         "MotherEkin_MeV",
    #         "MotherMomentum_MeV",
    #         "MotherEtot_MeV",
    #         # "MyMotherEtot_MeV",
    #         # "MyMotherEtotV2_Mev",
    #         "Momentum_MeV",
    #         "MotherMomentum_MeV",
    #     ]
    #     print(df[cols])
    #     return

    groups = df.groupby(
        ["EventID", "ParentID", "VertexX_cm", "VertexY_cm", "VertexZ_cm", "Time_ns", "MotherName"]
    )

    ndaughters_dict = {
        "1_alpha": 0,
        "2_alpha": 0,
        "3_alpha": 0,
        "4_alpha": 0,
        "5_alpha": 0,
        "6_alpha": 0,
        "7_alpha": 0,
        "8_alpha": 0,
        "9_alpha": 0,
    }

    n_daughters_list = []

    etot_alpha_per_daughter_ratio = []
    energy_conservation = {"1_alpha": [], "2_alpha": [], "3_alpha": [], "4_alpha": []}

    n_12c_on_12c = 0
    n_12c_on_proton = 0

    for i, (cle, groupe) in enumerate(groups):
        ekin_mother = groupe["MotherEkin_MeV"].iloc[0]
        etot_mother = groupe["MotherEtot_MeV"].iloc[0]
        etot_target = groupe["TargetMass_MeV"].iloc[0]  # target at rest in lab frame
        ndaughters = len(groupe["Particle"])
        # ndaughters_dict[f"{ndaughters}_alpha"] += 1

        # compute the ratio of Etot of one alpha and Etot of 12C divided by number of daughters
        for etot_daughter in groupe["Etot_MeV"].tolist():
            etot_alpha_per_daughter_ratio.append(etot_daughter / (etot_mother / ndaughters))

        mother_name = groupe["MotherName"].iloc[0]
        target_name = groupe["TargetName"].iloc[0]
        daughter_names = groupe["Particle"].tolist()

        # check if reaction is 12C + nuclei -> some alpha + something else
        is_12c_into_alpha_process: bool = mother_name == "C12" and "alpha" in daughter_names
        if not is_12c_into_alpha_process:
            continue

        if target_name == "C12":
            n_12c_on_12c += 1
            continue  # FIXME
        elif target_name == "proton":
            n_12c_on_proton += 1

        str_daugh_names = ""
        for iname, name in enumerate(daughter_names):
            str_daugh_names += f"{name}"
            if iname < len(daughter_names) - 1:
                str_daugh_names += " + "
        str_daugh_etot = ""
        str_daugh_ekin = ""
        str_daugh_mom = ""
        for ietot, (mom, ekin, etot) in enumerate(
            zip(
                groupe["Momentum_MeV"].tolist(),
                groupe["Ekin_MeV"].tolist(),
                groupe["Etot_MeV"].tolist(),
            )
        ):
            str_daugh_mom += f"{mom:.2f}"
            str_daugh_ekin += f"{ekin:.2f}"
            str_daugh_etot += f"{etot:.2f}"
            if ietot < ndaughters - 1:
                str_daugh_mom += " + "
                str_daugh_ekin += " + "
                str_daugh_etot += " + "
        print(f"Group #{i+1}:")
        print(f"\tProcess: {mother_name} + {target_name} -> {str_daugh_names}")
        ekin_daughters = groupe["Ekin_MeV"].sum()
        etot_daughters = groupe["Etot_MeV"].sum()

        if ndaughters <= 4:
            energy_conservation[f"{ndaughters}_alpha"].append(etot_mother - etot_daughters)

        mom_daughters = [mom**2 for mom in groupe["Momentum_MeV"].tolist()]
        mom_daughters = np.sqrt(np.sum(mom_daughters))

        if ndaughters > 1:
            # print(
            #     f"\tMomentum (MeV): {groupe['MotherMomentum_MeV'].iloc[0]:.2f} -> {str_daugh_mom} = {mom_daughters:.2f}"
            # )
            # print(f"\tEkin (MeV): {ekin_mother:.2f} -> {str_daugh_ekin} = {ekin_daughters:.2f}")
            print(
                f"\tEtot (MeV): {etot_mother:.2f} + {etot_target:.2f} -> {str_daugh_etot} = {etot_daughters:.2f}"
            )
        else:
            # print(
            #     f"\tMomentum (MeV): {groupe['MotherMomentum_MeV'].iloc[0]:.2f} -> {mom_daughters:.2f}"
            # )
            # print(f"\tEkin (MeV): {ekin_mother:.2f} -> {str_daugh_ekin} ")
            print(f"\tEnergies (MeV): {etot_mother:.2f} + {etot_target:.2f} -> {str_daugh_etot} ")
        print(f"\tE_initial - E_final (MeV): {etot_mother + etot_target - etot_daughters:.2f}")
        print("\n")

    ntot_daugh = np.sum(list(ndaughters_dict.values()))

    print(f"# 12C + 12C reactions: {n_12c_on_12c}; # 12C + proton reactions: {n_12c_on_proton}")

    # for key, _ in ndaughters_dict.items():
    #     ndaughters_dict[key] /= ntot_daugh
    #     ndaughters_dict[key] = [ndaughters_dict[key]]

    # print(ndaughters_dict)

    # df_ndaugh = pd.DataFrame.from_dict(ndaughters_dict)
    # np_ndaugh = df_ndaugh.to_numpy()[0]

    # bins = np.arange(0.5, 9.5 + 1, 1)

    # print(bins)
    # print(np_ndaugh)

    # # counts, bins = np.histogram(np_ndaugh)
    # plt.hist(bins[:-1], bins, weights=np_ndaugh, color="blue", alpha=0.5)
    # plt.xlabel(r"Number of $\alpha$ daughters")
    # plt.ylabel("Normalised counts")

    # plot etot_alpha_per_daughter_ratio
    plt.figure(figsize=(8, 8), dpi=100)

    # sns.histplot(
    #     etot_alpha_per_daughter_ratio, bins=20, kde=False, stat="count", color="blue", alpha=0.6
    # )
    # plt.xlabel(r"$\dfrac{E (\alpha) }{E(^{12}\mathrm{C}) / n_{\alpha}}$")
    # plt.ylabel("Counts")
    # for key, data in energy_conservation.items():
    #     label = r"$^{12}\mathrm{C} \to $" + key[0] + r" $\alpha$"
    #     sns.histplot(data, bins=20, kde=False, stat="count", alpha=0.6, label=label)
    # plt.xlabel("Energy of mother - Energy of daughters (MeV)")
    # plt.ylabel("Counts")
    # plt.legend()
    # plt.show()


if __name__ == "__main__":
    DEBUG: bool = True
    main(DEBUG)
