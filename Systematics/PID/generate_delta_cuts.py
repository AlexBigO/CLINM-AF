"""
file: generate_delta_cuts.py
brief: Simple script to generate "delta cuts" for PID
a "delta cut" being a variation of a nominal cut
usage: python3 generate_delta_cuts.py
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import sys
import uproot
import pandas as pd
import numpy as np

import ROOT as r

IDX = 0
IDY = 1


def get_unit_vector(point_a, point_b) -> list[float]:
    """
    Helper function to get unit vector AB
    """
    xa, ya = point_a[IDX], point_a[IDY]
    xb, yb = point_b[IDX], point_b[IDY]

    xab = xb - xa
    yab = yb - ya

    norm = np.sqrt(xab * xab + yab * yab)
    xab /= norm
    yab /= norm

    return [xab, yab]


def get_delta_vec(vec1, vec2, delta):
    """
    Helper function to get "delta" "vector
    normalised (vec1 - vec2) * delta
    """
    x = vec1[IDX] - vec2[IDX]
    y = vec1[IDY] - vec2[IDY]
    norm = delta / np.sqrt(x * x + y * y)

    return [x * norm, y * norm]


def get_cut_delta(cut: r.TCutG, delta: float) -> r.TCutG:
    """
    Helper function to generate contracted or dilated cut region
    """
    # clone input cut
    cut_delta = cut.Clone()
    name: str = cut.GetName()
    if delta is None or delta == 1:
        cut_delta.SetName(f"{name}_nominal")
    else:
        cut_delta.SetName(f"{name}_delta_{int(1000*delta):03d}")
    print(cut_delta.GetName())
    cut_delta.SetVarX(cut.GetVarX())  # safety
    cut_delta.SetVarY(cut.GetVarY())  # safety

    n: int = cut.GetN()
    xs_cut_nominal = cut.GetX()
    ys_cut_nominal = cut.GetY()
    # compute centroid
    xc = np.sum(xs_cut_nominal) / float(n)
    yc = np.sum(ys_cut_nominal) / float(n)
    # initialise points of the new cut
    xs_cut_delta = [xc] * n
    ys_cut_delta = [yc] * n
    # define points of the new cut
    for i, (x, y) in enumerate(zip(xs_cut_nominal, ys_cut_nominal)):
        xs_cut_delta[i] += delta * (x - xc)
        ys_cut_delta[i] += delta * (y - yc)
        cut_delta.SetPoint(i, xs_cut_delta[i], ys_cut_delta[i])

    return cut_delta


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

    name_cutfile = "../../Analysis/CNAO_0925/Run06/cut_C.root"
    name_cut = "cut_C"
    cutfile = r.TFile(name_cutfile, "READ")
    cut_nominal = cutfile.Get(name_cut)

    n = int(cut_nominal.GetN())
    xs_cut_nominal = cut_nominal.GetX()
    ys_cut_nominal = cut_nominal.GetY()
    # compute centroid
    xc = np.sum(xs_cut_nominal) / float(n)
    yc = np.sum(ys_cut_nominal) / float(n)

    if debug:
        print(f"xc = {xc} \t yc = {yc}")

    # # test delta vector method
    # delta = 1
    # xs_cut_delta = [x for x in xs_cut_nominal]
    # ys_cut_delta = [y for y in ys_cut_nominal]
    # for i in range(n):
    #     # test on first triplet
    #     if i == 1:
    #         continue
    #     if i > 3:
    #         continue
    #     point1 = [xs_cut_nominal[i-1], ys_cut_nominal[i-1]]
    #     point2 = [xs_cut_nominal[i], ys_cut_nominal[i]]
    #     point3 = [xs_cut_nominal[i+1], ys_cut_nominal[i+1]]
    #     vec12 = get_unit_vector(point1, point2)
    #     vec23 = get_unit_vector(point2, point3)
    #     vec_delta = get_delta_vec(vec12, vec23, delta)
    #     xs_cut_delta[i] += vec_delta[IDX]
    #     ys_cut_delta[i] += vec_delta[IDY]
    #     # new_point = np.array(point2) + np.array(vec_delta)

    # if debug:
    #     print(f"vec_delta = {vec_delta}")

    # # cut_delta = cut_nominal.Clone()
    # cut_delta = r.TCutG("aha", 2)
    # cut_delta.SetName("cut_delta")
    # cut_delta.SetLineColor(r.kRed)
    # for i in range(1, 3):
    #     cut_delta.SetPoint(i, xs_cut_delta[i], ys_cut_delta[i])
    # cut_delta.SetPoint(2, xs_cut_delta[0], ys_cut_delta[0])

    cuts_delta = []
    deltas = np.arange(0.90, 1.10, 0.001)

    for delta in deltas:
        cuts_delta.append(get_cut_delta(cut_nominal, delta=delta))

    # cut_narrow = get_cut_delta(cut_nominal, delta=0.80)
    # cut_narrow.SetLineColor(r.kRed)

    # cut_wide = get_cut_delta(cut_nominal, delta=1.10)
    # cut_wide.SetLineColor(r.kBlue)

    c = r.TCanvas("c", "", 1000, 800)
    cut_nominal.SetLineColor(r.kRed)
    cut_nominal.SetLineWidth(3)
    cut_nominal.Draw()
    # cut_delta.Draw("same")
    for cut_delta in cuts_delta:
        cut_delta.Draw("same")
    # cut_narrow.Draw("same")
    # cut_wide.Draw("same")
    c.Update()
    c.Draw()
    input("Press enter")

    name_ofile: str = "cutsDelta.root"
    ofile = r.TFile(name_ofile, "recreate")
    for cut_delta in cuts_delta:
        cut_delta.Write()
    # cut_narrow.Write()
    # cut_wide.Write()
    ofile.Close()


if __name__ == "__main__":
    DEBUG: bool = True
    main(DEBUG)
