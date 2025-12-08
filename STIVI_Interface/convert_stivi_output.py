"""
file: convert_stivi_output.py
brief: Script to read STIVI output and produce a new .root file(s)
    containing initial information and kinetic energy
usage: python3 convert_stivi_output.py config.yml
notes: we use RDataFrame instead of (uproot + pandas) because it is more robust when there are
    non-standard data types in the file
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import os
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
    sys.path.append("../Utils/")
    from utils import enforce_trailing_slash
except ModuleNotFoundError:
    print(
        "Module 'utils' is not in the '../Utils/' directory. Add it to run this script."
    )

try:
    sys.path.append("../Utils/")
    from logger import Logger
except ModuleNotFoundError:
    print(
        "Module 'logger' is not in the '../Utils/' directory. Add it to run this script."
    )


# pylint: disable = "too-many-locals, too-many-branches, too-many-statements"
def main(name_config_file: str, debug: bool = False) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the configuration file

    - debug: bool
        Switch to activate debugging mode
    """

    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    # handle input
    name_infiles = config["input"]["file"]
    name_tree: str = config["input"]["tree"]["name"]
    name_branches: list[str] = config["input"]["tree"]["DeltaE_branches"]
    name_dnrj_pl1: str = name_branches[0]
    name_dnrj_pl2: str = name_branches[1]
    name_dnrj_cebr: str = name_branches[2]

    # handle output
    dir_output: str = enforce_trailing_slash(config["output"]["dir"])
    auto_format_output: bool = config["output"]["sub_dir"]["activate"]
    name_outfiles = (
        config["output"]["file"]
        if not auto_format_output
        else config["output"]["sub_dir"]["name_file"]
    )
    name_out_tree: str = config["output"]["tree"]["name"]
    name_new_branches: list[str] = config["output"]["tree"]["DeltaE_branches_renaming"]
    # names of new branches containing kinetic energies
    name_ec_pl1: str = config["output"]["tree"]["ec_branches"]["ec_pl1"]
    name_ec_pl2: str = config["output"]["tree"]["ec_branches"]["ec_pl2"]

    # QA config
    do_qa: bool = config["output"]["qa"]["activate"]
    nbins: int = config["output"]["qa"]["nbins"]

    # safeties
    # input files and output files must be of same type if sub_dir not enabled
    if not auto_format_output:
        if not (
            isinstance(name_infiles, type(name_outfiles))
            and isinstance(name_outfiles, type(name_infiles))
        ):
            Logger(
                "The options 'input/file' and 'output/file' must be of same type (str or list[str])"
                + " if sub_dir is not activated!",
                "FATAL",
            )
        if isinstance(name_infiles, list) and len(name_infiles) != len(name_outfiles):
            Logger(
                "There must be the same number of input files and output files"
                + " if 'sub_dir' option is not activated!",
                "FATAL",
            )

    # enforce list type so we can loop over the files
    if not isinstance(name_infiles, list):
        name_infiles = [name_infiles]
    if not isinstance(name_outfiles, list):
        name_outfiles = [name_outfiles] * len(name_infiles)

    # enable multithreaded usage of RDataFrame
    r.EnableImplicitMT(config["RDataFrame"]["EnableImplicitMT"])

    # loop over all the input and output files
    for name_infile, name_outfile in zip(name_infiles, name_outfiles):

        if debug:
            Logger(f"Name of input file: {name_infile}", "DEBUG")
            Logger(f"Name of TTree: {name_tree}", "DEBUG")
            Logger(f"Names of (Delta) E branches: {name_branches}", "DEBUG")

        # auto format output
        if auto_format_output:
            name_infile_wo_path: str = name_infile.split("/")[-1]
            name_infile_wo_suffix: str = name_infile_wo_path.replace(".root", str())
            if "_FlatTree" in name_infile_wo_suffix:
                name_infile_wo_suffix = name_infile_wo_suffix.replace(
                    "_FlatTree", str()
                )
            elif "FlatTree" in name_infile_wo_suffix:
                name_infile_wo_suffix = name_infile_wo_suffix.replace("FlatTree", str())

            # place the output file in dir/sub_dir/
            sub_dir_output: str = dir_output + enforce_trailing_slash(
                name_infile_wo_suffix
            )
            name_outfile = sub_dir_output + name_outfile
        else:
            name_outfile = dir_output + name_outfile

        if debug:
            if auto_format_output:
                Logger(f"Output sub dir: {sub_dir_output}", "DEBUG")
            else:
                Logger(f"Output dir: {dir_output}", "DEBUG")
            Logger(f"Output file: {name_outfile}", "DEBUG")

        # warning if output directory exists, else make it
        if os.path.isdir(dir_output):
            log_dir_output = f"Output directory'{dir_output}'"
            log_dir_output += " already exists,"
            log_dir_output += " overwrites possibly ongoing!\n"
            Logger(log_dir_output, "WARNING")
        else:
            os.makedirs(dir_output)
            print("\n")

        if auto_format_output:
            # warning if output sub directory exists, else make it
            if os.path.isdir(sub_dir_output):
                log_sub_dir_output = f"Output sub directory'{sub_dir_output}'"
                log_sub_dir_output += " already exists,"
                log_sub_dir_output += " overwrites possibly ongoing!\n"
                Logger(log_sub_dir_output, "WARNING")
            else:
                os.makedirs(sub_dir_output)
                print("\n")

        # convert input .root file into RDataFrame
        infile: r.TFile = r.TFile.Open(name_infile)
        tree: r.TTree = infile.Get(name_tree)
        df: r.RDataFrame = r.RDataFrame(tree)

        # TODO add triple coincidence flag in the TTree (from cfg file)

        # compute kinetic energy before Pl1 and Pl2
        df_with_ec = df.Define(
            name_ec_pl2, f"{name_dnrj_cebr} + {name_dnrj_pl2}"
        ).Define(name_ec_pl1, f"{name_dnrj_cebr} + {name_dnrj_pl2} + {name_dnrj_pl1}")

        df_new = (
            df_with_ec.Define(name_new_branches[0], name_dnrj_pl1)
            .Define(name_new_branches[1], name_dnrj_pl2)
            .Define(name_new_branches[2], name_dnrj_cebr)
        )

        # QA histograms
        if do_qa:

            h_names = ["h_cebr_pl2", "h_pl2_pl1", "h_ec_de_pl2", "h_ec_de_pl1"]
            h_titles = [
                "; CeBr_{3} energy (MeV); Plastic 2 energy (MeV)",
                "; Plastic 2 energy (MeV); Plastic 1 energy (MeV)",
                "; E_{c} before Plastic 2 (MeV); #Delta E Plastic 2(MeV)",
                "; E_{c} before Plastic 1 (MeV); #Delta E Plastic 1(MeV)",
            ]

            h_branches_to_plot = [
                (name_dnrj_cebr, name_dnrj_pl2),
                (name_dnrj_pl2, name_dnrj_pl1),
                [name_ec_pl2, name_dnrj_pl2],
                [name_ec_pl1, name_dnrj_pl1],
            ]

            # retrieve mins and maxs of each distribution
            xmins, xmaxs, ymins, ymaxs = [], [], [], []
            for axes in h_branches_to_plot:
                xmins.append(df_new.Min(axes[0]).GetValue())
                xmaxs.append(df_new.Max(axes[0]).GetValue())
                ymins.append(df_new.Min(axes[1]).GetValue())
                ymaxs.append(df_new.Max(axes[1]).GetValue())

            # axes configurations
            h_axes_config = []
            for xmin, xmax, ymin, ymax in zip(xmins, xmaxs, ymins, ymaxs):
                h_axes_config.append((nbins, xmin, xmax, nbins, ymin, ymax))
            # histograms configurations
            h_configs = []
            for name, title, axes_config in zip(h_names, h_titles, h_axes_config):
                h_configs.append((name, title, *axes_config))

            # FIXME I did not find a way to save these in a list
            h1 = df_new.Histo2D(h_configs[0], *h_branches_to_plot[0])
            h2 = df_new.Histo2D(h_configs[1], *h_branches_to_plot[1])
            h3 = df_new.Histo2D(h_configs[2], *h_branches_to_plot[2])
            h4 = df_new.Histo2D(h_configs[3], *h_branches_to_plot[3])

        # save dataframe in output .root file
        if config["output"]["save_nrj_info_only"]:
            saved_branches = [*name_new_branches, name_ec_pl1, name_ec_pl2]
            df_new.Snapshot(name_out_tree, name_outfile, {*saved_branches})
        else:
            df_new.Snapshot(name_out_tree, name_outfile)

        infile.Close()

        if do_qa:
            # add 2d QA plots to the output .root file
            outfile: r.TFile = r.TFile.Open(name_outfile, "UPDATE")
            h1.Write()
            h2.Write()
            h3.Write()
            h4.Write()
            outfile.Close()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args: str = parser.parse_args()
    DEBUG: bool = False
    main(args.name_config_file, DEBUG)
