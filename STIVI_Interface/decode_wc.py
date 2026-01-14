"""
file: decode_wc.py
brief: Script to run DecodeWC action of STIVI
usage: python3 decode_wc.py cfg.yml
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

from os import system
import sys

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
    from logger import Logger
except ModuleNotFoundError:
    print(
        "Module 'logger' is not in the '../Utils/' directory. Add it to run this script."
    )


# pylint:disable=too-many-locals, too-many-branches, too-many-statements
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

    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    my_input = config["DecodeWC"]["input"]
    name_output = config["DecodeWC"]["output"]["name"]
    use_stivi_merge: bool = config["DecodeWC"]["use_stivi_merge"]
    merge_output: bool = config["DecodeWC"]["output"]["merge"]["activate"]
    rm_tmp_file: bool = config["DecodeWC"]["output"]["merge"]["rm_tmp_file"]
    exp = config["DecodeWC"]["exp"]
    run = config["DecodeWC"]["run"]
    flat: bool = config["DecodeWC"]["flat"]
    extra_option = config["DecodeWC"]["extra_option"]

    # safeties
    if isinstance(my_input, list) and isinstance(name_output, list):
        if len(my_input) != len(name_output):
            Logger(
                "Input and output must be of same size if they are lists!",
                "FATAL",
            )
    if name_output != "auto" and not merge_output and not use_stivi_merge:
        if not (
            isinstance(my_input, type(name_output))
            and isinstance(name_output, type(my_input))
        ):
            Logger(
                "Local input and output must be of same type if output is not 'auto' "
                "and ('merge' is not activated or 'use_stivi_merge' is not activated)!",
                "FATAL",
            )
    if name_output == "auto" and merge_output:
        Logger(
            "Option 'output/name' cannot be 'auto' if 'merge' is activated!",
            "FATAL",
        )
    if not isinstance(flat, list) and not isinstance(flat, bool):
        Logger("The option 'flat' must be a boolean or a list of booleans!", "FATAL")
    if isinstance(flat, list):
        for flat_ in flat:
            if not isinstance(flat_, bool):
                Logger(
                    "The option 'flat' must be a boolean or a list of booleans!",
                    "FATAL",
                )

    if rm_tmp_file and not merge_output:
        Logger(
            "Option 'rm_tmp_file' enabled but 'merge' not activated "
            "so no temporary files will be produced",
            "WARNING",
        )

    name_stivi_reco_dir: str = config["STIVI"]["Reconstruction_dir"]

    # go to STIVI Reconstruction directory
    cd_stivi: str = f"cd {name_stivi_reco_dir}"
    if debug:
        Logger(f"Command to go to STIVI Reconstruction directory: {cd_stivi}", "DEBUG")

    # enforce list if my_input (hence neither output) is a list
    if not isinstance(my_input, list):
        my_input = [my_input]
    n_input: int = len(my_input)
    if not isinstance(exp, list):
        exp = [exp] * n_input
    if not isinstance(run, list):
        run = [run] * n_input
    if not isinstance(flat, list):
        flat = [flat] * n_input
    if merge_output:
        name_output = [f"tmp_{name.split('/')[-1]}.root" for name in my_input]
    else:
        if not isinstance(name_output, list):
            name_output = [name_output] * n_input

    cmd_decode_wc = ""

    for i, (in_, out_, exp_, run_, flat_) in enumerate(
        zip(my_input, name_output, exp, run, flat)
    ):
        cmd_decode_wc += f"DecodeWC -in {in_} -out {out_} -exp {exp_} -run {run_}"
        if flat_:
            cmd_decode_wc += " -flat"
        if extra_option is not None:
            cmd_decode_wc += " " + extra_option

        if i < n_input - 1:
            cmd_decode_wc += " && "

    if debug:
        Logger(f"Command to DecodeWC: {cmd_decode_wc}", "DEBUG")

    # STIVI adds '_FlatTree' before '.root' when flat option enabled
    # so we need to take it into account for the merge and rm commands
    if flat:
        name_output = [
            name.replace(".root", str()) + "_FlatTree.root"
            for name in name_output.copy()
        ]

    cmd_merge = ""
    if merge_output:
        cmd_merge += f"hadd {config['DecodeWC']['output']['name']} "
        for name in name_output:
            cmd_merge += f"{name} "

    cmd_rm: str = ""
    if merge_output and rm_tmp_file:
        cmd_rm = "rm " + str(" ").join(name_output)

    cmd: str = cd_stivi + " && " + cmd_decode_wc
    if merge_output:
        cmd += " && " + cmd_merge
        if rm_tmp_file:
            cmd += " && " + cmd_rm
    else:
        cmd_rename = str()
        for i, name in enumerate(name_output):
            cmd_rename += f"mv {name} {name.replace('_FlatTree', str())}"
            if i < n_input - 1:
                cmd_rename += " && "
        cmd += " && " + cmd_rename

    if config["command"]["print"]:
        Logger(
            f"Enter this command line to DecodeWC with selected configuration:\n\n{cmd}",
            "INFO",
        )
    if config["command"]["run"]:
        system(cmd)


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    DEBUG: bool = False
    main(args.name_config_file, DEBUG)
