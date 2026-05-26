"""
file: run_simulation_jobs.py
brief:
usage: python3 run_simulation_jobs.py cfg.yml njobs -id
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

from os import system, chmod, stat as os_stat
from stat import S_IXUSR

try:
    from argparse import ArgumentParser
except ModuleNotFoundError:
    print("Module 'argparse' is not installed. Please install it to run this script.")

try:
    from yaml import load, FullLoader
except ModuleNotFoundError:
    print("Module 'pyyaml' is not installed. Please install it to run this script.")


SPACE = " "


# pylint:disable=too-many-locals,too-many-statements, too-many-branches
def main(name_config_file: str, njobs: int, id_start_job: int = 1, debug: bool = False) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file

    - id_file: str
        ID of output file (if parallel computing)

    - id_start_job: int
        ID of output file (if parallel computing)

    - debug: bool
        Switch for debugging
    """
    if debug:
        print("Hello world!")

    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    # source
    config_source: dict = config["source"]
    # target
    has_target: bool = config["target"]["exists"]
    if has_target:
        material_target = config["target"]["material"]
    # campaign and run
    campaign: str = config["campaign"]
    run = config["run"]
    # for log file
    dir_output: str = config["output"]["dir"]
    prefix_log_file: str = dir_output + "/"
    if has_target:
        prefix_log_file += f"log_{campaign}_Run{run}_{config_source['particle']}_on_{material_target}_MC_"
    else:
        prefix_log_file += (
            f"log_{campaign}_Run{run}_{config_source['particle']}_wo_target_MC_"
        )

    executor: str = "python3"
    name_simulation_script: str = "simulation.py"

    # get lists of job IDs and log files
    id_jobs = []
    name_log_files = []
    for ijob in range(id_start_job, id_start_job + njobs + 1):
        if ijob >= 10:
            id_job = f"{ijob}"
        else:
            id_job = f"0{ijob}"
        id_jobs.append(id_job)
        name_log_files.append(prefix_log_file + id_job + ".txt")

    cmd_bash = "#!/bin/bash\n\n"
    for _, (id_job, name_log_file) in enumerate(zip(id_jobs, name_log_files)):
        cmd_bash += (
            "/usr/bin/time -o "
            + name_log_file
            + SPACE
            + executor
            + SPACE
            + name_simulation_script
            + SPACE
            + name_config_file
            + SPACE
            + "-id"
            + SPACE
            + id_job
            + SPACE
            + ">&"
            + SPACE
            + name_log_file
            + SPACE
            + "&"
            + "\n"
        )

    # create shell script file
    name_shell_script: str = (
        f"run_jobs_{campaign}_Run{run}_{config_source['particle']}.sh"
    )
    with open(name_shell_script, "w", encoding="utf-8") as f:
        f.write(cmd_bash)
    # make shell script executable
    stat_shell_script = os_stat(name_shell_script)
    chmod(name_shell_script, stat_shell_script.st_mode | S_IXUSR)

    # print command
    if debug:
        print(cmd_bash)
    # run shell script
    else:
        cmd_run_bash = "./" + name_shell_script
        system(cmd_run_bash)


if __name__ == "__main__":
    DEBUG: bool = False
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    parser.add_argument(
        "njobs", type=int, default=1, help="Number of jobs to run in parallel"
    )
    parser.add_argument(
        "--id_start_job",
        "-id",
        type=int, default=1, help="ID of the starting job"
    )
    args = parser.parse_args()
    main(args.name_config_file, args.njobs, args.id_start, DEBUG)
