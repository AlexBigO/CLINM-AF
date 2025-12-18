"""
file: format_utils.py
brief:
usage:
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""


def enforce_trailing_slash(path):
    """
    Helper method to enforce '/' at the and of directory name

    Parameters
    ------------------------------------------------
    - path: str
        Some path

    Returns
    ------------------------------------------------
    - path: str
        Path with a trailing slash at the end if it was not there yet
    """

    if path is not None and path[-1] != "/":
        path += "/"

    return path


def enforce_list(x) -> list[str]:
    """
    Helper method to enforce list type

    Parameters
    ----------
    - x: a string or a list of string

    Returns
    ----------
    - x_list if x was not a list, x itself otherwise
    """

    if not isinstance(x, list):
        if isinstance(x, str):
            # handle possible whitespaces in config file entry
            x_list = x.split(",")
            for i, element in enumerate(x_list):
                x_list[i] = element.strip()  # remove possible whitespaces
            return x_list
        return [x]

    return x
