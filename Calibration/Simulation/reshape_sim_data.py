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
    if debug:
        print("Hello world!")
    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    # handle input
    name_infile = config["input"]["file"]
    name_trees: str = config["input"]["tree"]["names"]
    name_branches: list[str] = config["input"]["tree"]["branches"]
    # handle df merge
    refs_for_merge: list[str] = config["merge"]["on_branches"]
    suffixes: list[str] = config["merge"]["suffixes"]
    thresholds: list[str] = config["merge"]["thresholds"]
    # handle output
    name_ofile = config["output"]["file"]
    name_otree: str = config["output"]["tree"]["name"]
    branch_of_interest: str = "TotalEnergyDeposit"

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
    df_merged: pd.DataFrame = pd.merge(*dfs, on=refs_for_merge)
    if debug:
        print(f"Merged dataframe: {df_merged}")

    cols_to_keep = []
    for name in list(df_merged.columns):
        if name in refs_for_merge:
            cols_to_keep.append(name)
        elif branch_of_interest in name:
            cols_to_keep.append(name)

    df: pd.DataFrame = df_merged[cols_to_keep]
    if debug:
        print(f"Dataframe with selected columns: {df}")

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


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    DEBUG: bool = True
    main(args.name_config_file, DEBUG)
