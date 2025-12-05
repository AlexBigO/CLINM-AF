"""
file: import_data_from_server.py
brief: Script to import data from a server (e.g. sbgui11)
usage: python3 import_data_from_server config.yml
note: This script requires to be connected to IPHC server
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

from os import system, makedirs
from os.path import isdir

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
    from utils import enforce_trailing_slash, Logger
except ModuleNotFoundError:
    print("Module 'utils' is not in the parent directory. Add it to run this script.")

POSSIBLE_TYPE_OF_CONTENT: list[str] = ["directory", "file"]


def get_address_server(username: str, name_server: str, use_ssh_cm: bool) -> str:
    """
    Helper function to get the address of the server

    Parameters
    ------------------------------------------------
    - username: str
        Username

    - name_server: str
        Name of the remote server (e.g. sbgui11)

    Returns
    ------------------------------------------------
    - :str
        Full address of the remote server
    """
    if use_ssh_cm:
        return username + "@" + name_server
    return username + "@" + name_server + ".in2p3.fr"


def create_ssh_cm(cfg_ssh_cm: dict) -> None:
    """
    Helper function to create a SSH ControlManager entry for the server

    Parameters
    ------------------------------------------------
    - config_ssh_cm: dict
        Dictionary with the configuration of the SSH ControlManager
    """
    name_ssh_config_file: str = cfg_ssh_cm["ssh_config_file"]
    host: str = cfg_ssh_cm["host"]
    user: str = cfg_ssh_cm["user"]
    hostname: str = cfg_ssh_cm["hostname"]

    text_cm: str = "\n"
    text_cm += f"# Access to {hostname} server (via proxy connection to sbgli)\n"
    text_cm += f"Host {host}\n"
    text_cm += f"User {user}\n"
    text_cm += f"Hostname {hostname}\n"
    text_cm += "# use control hub to  use only one ssh channel for all\n"
    text_cm += "# connections, faster and password only on  first connection\n"
    text_cm += "ControlMaster auto\n"
    ssh_dir: str = name_ssh_config_file.rsplit("/", 1)[0]
    text_cm += f"ControlPath {ssh_dir}/%r@%h:%p.control\n"
    text_cm += "ControlPersist 600\n"
    text_cm += "# Forward SSH Key Agent , this allows to log back into home\n"
    text_cm += "# machines using your local private key\n"
    text_cm += "ForwardAgent yes\n"
    text_cm += "PubkeyAuthentication yes\n"
    text_cm += "# X11\nForwardX11 yes\nForwardX11Trusted yes\n"
    text_cm += "# Compression would be  nice\n"
    text_cm += "Compression yes\n"
    text_cm += "# try to  keep the connection aliv\n"
    text_cm += "ServerAliveInterval 60\n"
    text_cm += "# and use this command to  connect\n"
    text_cm += f"ProxyCommand ssh -Y {user}@sbgli.in2p3.fr -W %h:%p"

    # add the ControlManager to the ssh config file
    with open(name_ssh_config_file, "a", encoding="utf-8") as f:
        f.write(" \n")
        f.write(text_cm)

    Logger(
        f"The SSH ControlManager for host {host} was added to the file {name_ssh_config_file}",
        "INFO",
    )


# pylint:disable=too-many-locals, too-many-branches
def main(name_config_file: str) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML configuration file
    """

    Logger("This script requires to be connected to IPHC server!", "WARNING")

    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    # SSH Control Master configuration
    cfg_ssh_cm: dict = config["ssh_control_master"]
    if cfg_ssh_cm["create"]:
        create_ssh_cm(cfg_ssh_cm)

    # elements of local and remote configuration
    cfg_local: dict = config["local"]
    cfg_remote: dict = config["remote"]
    type_of_content: str = cfg_remote["type_of_content"]
    content = config["remote"]["content"]
    content_renaming = cfg_local["content_renaming"]
    use_ssh_cm: bool = cfg_remote["use_ssh_control_master"]

    # safeties
    if content_renaming is not None:
        if not (
            isinstance(content, type(content_renaming))
            and isinstance(content_renaming, type(content))
        ):
            Logger(
                "Local content_renaming and remote content must be of same type!",
                "FATAL",
            )
    if type_of_content not in POSSIBLE_TYPE_OF_CONTENT:
        log = f"The type_of_content {type_of_content} is not among the possible values:"
        log += " 'directory' or 'file'."
        Logger(log, "FATAL")

    # retrieve the rest of the configuration
    username: str = config["remote"]["username"]
    name_server: str = config["remote"]["server"]
    address_server: str = get_address_server(username, name_server, use_ssh_cm)
    dir_local: str = enforce_trailing_slash(cfg_local["dir"]["name"])

    if cfg_local["dir"]["mkdir"]:
        if isdir(dir_local):
            Logger(f"Local directory {dir_local} already exists.", "INFO")
        else:
            Logger(f"Make local directory {dir_local}.", "INFO")
            makedirs(dir_local)

    # enforce list type
    if not isinstance(content, list):
        content = [content]

    # first, create the scp command to copy files from remote
    cmd_copy = "scp "

    if type_of_content == "directory":
        cmd_copy += "-r "

    for entry in content:
        cmd_copy += f"{address_server}:{entry} "

    cmd_copy += dir_local
    cmd_total = cmd_copy

    # then, rename the files if needed
    if content_renaming is not None:
        cmd_rename = str()
        if not isinstance(content_renaming, list):
            content_renaming = [content_renaming]
        for i, (original_name, new_name) in enumerate(zip(content, content_renaming)):
            original_name_wo_path: str = original_name.split("/")[-1]
            cmd_rename += (
                f" mv {dir_local}{original_name_wo_path} {dir_local}{new_name} "
            )
            if i < len(content) - 1:
                cmd_rename += " && "

        cmd_total += " && " + cmd_rename

    if config["command"]["print"]:
        Logger(f"Command line to copy data from remote:\n {cmd_copy}", "INFO")
        if content_renaming is not None:
            Logger(f"Command line to rename local data:\n {cmd_rename}", "INFO")
    if config["command"]["run"]:
        system(cmd_total)


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args: str = parser.parse_args()

    main(args.name_config_file)
