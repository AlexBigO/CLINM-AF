"""
file: utils.py
brief:
usage:
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import sys
import ROOT as r
import pandas as pd
import uproot


# pylint: disable=too-few-public-methods
class Logger:
    """
    Class to print in colour
    """

    DEBUG = "\033[96m"
    INFO = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    FATAL = "\33[101m"
    ENDC = "\033[0m"

    def __init__(self, text, level):
        """
        Initialize the class
        Parameters
        ------------------------------------------------
        text: str
            Text to be printed
        level: str
            Level of logger, possible values [DEBUG, INFO, WARNING, ERROR, FATAL, RESULT]
        """
        self._text_ = text
        self._level_ = level

        if level == "DEBUG":
            print(f"{Logger.DEBUG}DEBUG{Logger.ENDC}: {text}")
        elif level == "INFO":
            print(f"{Logger.INFO}INFO{Logger.ENDC}: {text}")
        elif level == "WARNING":
            print(f"{Logger.WARNING}WARNING{Logger.ENDC}: {text}")
        elif level == "ERROR":
            print(f"{Logger.ERROR}ERROR{Logger.ENDC}: {text}")
        elif level == "FATAL":
            print(f"{Logger.FATAL}FATAL{Logger.ENDC}: {text}")
            sys.exit(0)
        elif level == "RESULT":
            print(f"\n\n{text}\n\n")
        else:
            print(text)


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


# pylint: disable=too-many-arguments
def configure_canvas(
    name_canvas, x_min, y_axis_min, x_max, y_axis_max, title, log_y_axis=False
):
    """
    Helper method to configure canvas

    Parameters
    ----------
    - name_canvas: name of the canvas
    - mass_min: lower limit of x axis
    - y_axis_min: lower limit of y axis
    - mass_max: upper limit of x axis
    - y_axis_max: upper limit of y axis
    - title: title of the canvas
    - log_y_axis: switch for log scale along y axis

    Returns
    ----------
    - c: TCanvas instance
    """

    c = r.TCanvas(name_canvas, "", 800, 800)
    c.DrawFrame(x_min, y_axis_min, x_max, y_axis_max, title)
    if log_y_axis:
        c.SetLogy()

    return c


def fill_th1(col, config) -> r.TH1D:
    """
    Helper task to create and fill TH1 histogram

    Parameters
    ------------------------------------------------
    - col:
        dataframe column
    - config:
        config of histogram

    Returns
    ------------------------------------------------
    - hist: r.TH1D
        1D histogram
    """

    hist = r.TH1D(*config)
    for entry in col.to_numpy():
        hist.Fill(entry)

    hist.Sumw2()
    hist.SetDirectory(0)

    return hist


def fill_th2(colx, coly, config) -> r.TH2D:
    """
    Helper task to create and fill TH2 histogram

    ----------
    Parameters
    - colx: dataframe column for x axis
    - coly: dataframe column for y axis
    - config: config of histogram
    """

    hist = r.TH2D(*config)
    for x, y in zip(colx.to_numpy(), coly.to_numpy()):
        hist.Fill(x, y)

    hist.Sumw2()
    return hist


def scan_peaks(content_bins):
    """
    Helper method to scan an E bin and scan the Delta E TTree

    The idea: scan ranges of Delta E to get local minima and maxima
        We start at the lowest value

        Required ingredients:
            - range: min and max for this energy bin
            - then we need to access the Delta E values corresponding to the min and max values OF ENTRIES
    """

    mins, maxs = [], []

    for ibin, content in enumerate(content_bins):
        if ibin == 0:
            mins.append((ibin, content))
            continue
        if ibin == len(content_bins) - 1:
            continue
        if content_bins[ibin - 1] < content and content > content_bins[ibin + 1]:
            maxs.append((ibin, content))
            continue
        if content_bins[ibin - 1] > content and content < content_bins[ibin + 1]:
            mins.append((ibin, content))
            continue

    return mins, maxs


def qa_plot_hist_and_extrema(h, mins, maxs, binning, inrj):
    """
    QA function to plot a histogram and the extrema found to roughly
    estimate both fit ranges and peak positions
    """
    canvas = r.TCanvas(f"QA_{inrj}", "", 800, 600)

    # create histograms for mins and maxs
    title = h.GetName()
    h_config_mins = (f"{title}_mins", "", len(binning) - 1, binning)
    h_config_maxs = (f"{title}_maxs", "", len(binning) - 1, binning)
    h_mins = r.TH1D(*h_config_mins)
    h_maxs = r.TH1D(*h_config_maxs)
    # fill histograms
    for _, (ibin, min) in enumerate(mins):
        h_mins.SetBinContent(ibin + 1, min)
    for _, (ibin, min) in enumerate(maxs):
        h_maxs.SetBinContent(ibin + 1, min)

    # draw options
    h_mins.SetLineColor(r.kBlack)
    h_mins.SetLineColor(r.kRed)
    h_maxs.SetLineColor(r.kMagenta)
    h.Draw("histe")
    h_mins.Draw("same")
    h_maxs.Draw("same")

    canvas.Update()
    # canvas.Draw()
    # input("Enter")
    return canvas


def get_extrema_edges(arr, bin_limits):
    """
    Helper function to retrieve bin informations (edges and center)
    """
    edges = []
    for _, (i, _) in enumerate(arr):
        if i >= len(bin_limits) - 1:
            continue
        lower_edge = bin_limits[i]
        upper_edge = bin_limits[i + 1]
        # center = (lower_edge + upper_edge) / 2
        edges.append((lower_edge, upper_edge))
        # edges.append(lower_edge)
        # edges.append(upper_edge)

    return edges


def get_extrema_centers(arr, bin_limits):
    """
    Helper function to retrieve bin informations (edges and center)
    """
    centers = []
    for _, (i, _) in enumerate(arr):
        if i >= len(bin_limits) - 1:
            continue
        lower_edge = bin_limits[i]
        upper_edge = bin_limits[i + 1]
        center = (lower_edge + upper_edge) / 2
        centers.append(center)

    return centers


def get_pseudo_max(h, binning, thr=7, min_consecutive_zeros=2):
    """
    Helper function to get th
    """
    quasi_empty_bins = []
    nbins = len(binning)
    print(nbins)
    for ibin in range(1, nbins):
        content = h.GetBinContent(ibin)
        # check if content is below threshold
        if content < thr:
            quasi_empty_bins.append(ibin)

    # safety
    if min_consecutive_zeros > len(quasi_empty_bins):
        print("ERROR: ...")
        return
    # get number of consecutive bins with zero
    counter = 0
    first_empty_bin = -1
    for i, bin in enumerate(quasi_empty_bins):
        if i == 0:
            continue
        # we reached the threshold !
        if counter >= min_consecutive_zeros:
            break
        # check if two zeros are consercutive
        if quasi_empty_bins[i - 1] == quasi_empty_bins[i] - 1:
            counter += 1
            if first_empty_bin == -1:
                first_empty_bin = quasi_empty_bins[i - 1]
        else:
            first_empty_bin = -1
    return binning[first_empty_bin]


# def get_bin_info(xaxis, ibin):
#     """
#     Helper function to retrieve bin informations (edges and center)
#     """

#     center = xaxis.GetBinCenter(ibin)
#     lower_limit = xaxis.GetBinLowEdge(ibin)
#     width = xaxis.GetBinWidth(ibin)
#     upper_limit = lower_limit + width

#     return lower_limit, center, upper_limit
