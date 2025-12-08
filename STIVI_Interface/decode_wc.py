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


# pylint:disable=too-many-locals, too-many-branches
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
    output = config["DecodeWC"]["output"]
    exp = config["DecodeWC"]["exp"]
    run = config["DecodeWC"]["run"]
    flat: bool = config["DecodeWC"]["flat"]

    # safeties
    if isinstance(my_input, list) and isinstance(output, list):
        if len(my_input) != len(output):
            Logger(
                "Input and output must be of same size if they are lists!",
                "FATAL",
            )
    if output != "auto":
        if not (
            isinstance(my_input, type(output)) and isinstance(output, type(my_input))
        ):
            Logger(
                "Local input and output must be of same type if output is not 'auto'!",
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

    name_stivi_reco_dir: str = config["STIVI"]["Reconstruction_dir"]

    # go to STIVI Reconstruction directory
    cd_stivi: str = f"cd {name_stivi_reco_dir}"
    if debug:
        Logger(f"Command to go to STIVI Reconstruction directory: {cd_stivi}", "INFO")

    # enforce list if my_input (hence neither output) is a list
    if not isinstance(my_input, list):
        my_input = [my_input]
    n_input: int = len(my_input)
    if not isinstance(output, list):
        output = [output] * n_input
    if not isinstance(exp, list):
        exp = [exp] * n_input
    if not isinstance(run, list):
        run = [run] * n_input
    if not isinstance(flat, list):
        flat = [flat] * n_input

    cmd_decode_wc = ""

    for i, (in_, out_, exp_, run_, flat_) in enumerate(
        zip(my_input, output, exp, run, flat)
    ):
        cmd_decode_wc += f"DecodeWC -in {in_} -out {out_} -exp {exp_} -run {run_}"
        if flat_:
            cmd_decode_wc += " -flat"

        if i < n_input - 1:
            cmd_decode_wc += " && "

    if debug:
        Logger(f"Command to DecodeWC: {cmd_decode_wc}", "INFO")

    cmd: str = cd_stivi + " && " + cmd_decode_wc

    if config["command"]["print"]:
        Logger(f"Full command: {cmd}", "INFO")
    if config["command"]["run"]:
        system(cmd)


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    DEBUG: bool = False
    main(args.name_config_file, DEBUG)
