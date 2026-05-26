"""
file: reshape_sim_data.py
brief:
usage: python3 reshape_sim_data.py cfg.yml
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

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

PDG_CODE_PROTON = 2212


def pdg_to_Z(series):
    # Convert to numeric (float) → NaN for non‑numeric entries
    num = pd.to_numeric(series, errors="coerce")
    # Integer arithmetic: // 10_000 discards AAA0, % 1_000 extracts Z
    return ((num.abs() // 10000) % 1000).astype("Int64")

def is_proton(series):
    """
    Return a boolean Series indicating whether each entry equals 2212.
    Handles numeric, float, or string representations.
    """
    # Coerce to numeric first (strings like "2212" become 2212)
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric == PDG_CODE_PROTON

def filter_by_Z(df, Z_target, pdg_columns=None):
    if pdg_columns is None:
        pdg_columns = [c for c in df.columns if c.startswith("PDGCode")]

    per_column_masks = []
    for col in pdg_columns:
        # a) Extract Z for the standard 100ZZZAAA0 format
        Z_series = pdg_to_Z(df[col])

        # b) Proton special case (only relevant when Z_target == 1)
        proton_mask = is_proton(df[col]) if Z_target == 1 else pd.Series(False, index=df.index)

        # c) Combine the two possibilities for THIS column:
        #    - Z matches target, OR
        #    - it's a proton (PDG==2212) when target Z == 1
        col_mask = (Z_series == Z_target) | proton_mask
        per_column_masks.append(col_mask)

    # --------------------------------------------------------------
    # 3) Combine masks across columns (OR or AND)
    # --------------------------------------------------------------
    combined = pd.concat(per_column_masks, axis=1)
    final_mask = combined.all(axis=1)   # keep only if ALL columns match
    return df[final_mask].copy()

def reshape_sim_data(z: int, name_config_file: str, debug: bool) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file

    - debug: bool
        Switch for debugging
    """
    if debug:
        print("Hello world!")
    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    # handle input
    name_infiles = config["input"]["file"]
    if not isinstance(name_infiles, list):
        name_infiles = [name_infiles]
    name_trees: str = config["input"]["tree"]["names"]
    name_branches: list[str] = config["input"]["tree"]["branches"]
    # handle df merge
    refs_for_merge: list[str] = config["merge"]["on_branches"]
    suffixes: list[str] = config["merge"]["suffixes"]
    thresholds: list[str] = config["merge"]["thresholds"]
    # handle output
    name_ofiles = config["output"]["file"]
    if not isinstance(name_ofiles, list):
        name_ofiles = [name_ofiles]
    if z is not None:
        for i_ofile in range(len(name_ofiles)):
            name_ofiles[i_ofile] = name_ofiles[i_ofile].replace(".root", str()) + f"_ZZZ_{z:03d}.root" 
    name_otree: str = config["output"]["tree"]["name"]
    branch_of_interest: str = "TotalEnergyDeposit"

    for name_infile, name_ofile in zip(name_infiles, name_ofiles):

        dfs: list[pd.DataFrame] = []
        for name_tree, suffix in zip(name_trees, suffixes):
            dfs.append(
                uproot.open(name_infile)[name_tree].arrays(name_branches, library="pd")
            )
            new_names: dict = {}
            for name_branch in name_branches:
                if name_branch in refs_for_merge:
                    continue
                new_names[name_branch] = name_branch + suffix
            dfs[-1].rename(columns=new_names, inplace=True)

        # merge dataframes per Run and per Event
        df_merged: pd.DataFrame = dfs[0]
        ndfs: int = len(dfs)
        if ndfs > 2:
            for _ in range(1, ndfs):
                df_merged = pd.merge(dfs[0], dfs[1], on=refs_for_merge)
                dfs.pop(0)
                dfs[0] = df_merged
                # print(dfs)
                # print("\n")
        elif ndfs == 2:
            df_merged = pd.merge(*dfs, on=refs_for_merge)

        if debug:
            print(df_merged)

        # selection on Z
        if z is not None:
            df_merged = filter_by_Z(df_merged, Z_target=z)

        cols_to_keep = []
        for name in list(df_merged.columns):
            if name in refs_for_merge:
                cols_to_keep.append(name)
            elif branch_of_interest in name:
                cols_to_keep.append(name)
            elif "PDGCode" in name:
                cols_to_keep.append(name)

        df: pd.DataFrame = df_merged[cols_to_keep].copy()
        if debug:
            print(f"Dataframe with selected columns: {df}")

        if len(suffixes) == 2:
            df[f"{branch_of_interest}_all"] = df[branch_of_interest + suffixes[0]] + df[branch_of_interest + suffixes[1]]
        elif len(suffixes) == 3:
            df[f"{branch_of_interest}_all"] = df[branch_of_interest + suffixes[0]] + df[branch_of_interest + suffixes[1]] + df[branch_of_interest + suffixes[2]]

        # apply threshold
        sel: str = str()
        for i, (thr, suffix) in enumerate(zip(thresholds, suffixes)):
            sel += branch_of_interest + suffix + f" > {thr}"
            if i < len(suffixes) - 1:
                sel += " and "
        if debug:
            print(f"Selection: {sel}")
        df_coinc: pd.DataFrame = df.query(sel, inplace=False)

        if debug:
            print(f"Size of df: {len(df)}\nSize of df_coinc: {len(df_coinc)}")

        with uproot.recreate(name_ofile) as f:
            f.mktree(name_otree, {col: df_coinc[col].to_numpy() for col in df.columns})


def main(name_config_file: str, debug: bool) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file

    - debug: bool
        Switch for debugging
    """

    # store all information
    reshape_sim_data(None, name_config_file, debug)
    # store information Z-wise
    z_values = [1, 2, 3, 4, 5, 6]
    for z in z_values:
        reshape_sim_data(z, name_config_file, debug)


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    DEBUG: bool = True
    main(args.name_config_file, DEBUG)
