#include <ROOT/RDataFrame.hxx>
#include <algorithm>
#include <iostream>
#include <vector>

#include "TCutG.h"
#include "TFile.h"
#include "TString.h"
#include "TTree.h"

enum Pars : std::size_t { kP0 = 0, kP1, kP2, nP };
using triplet = std::array<double, nP>;
using nonuplet = std::array<double, nP * nP>;

TCutG* gCut = nullptr;

nonuplet* parsPtr = nullptr;

double* par0Ptr = nullptr;
double* par1Ptr = nullptr;
double* par2Ptr = nullptr;

// double calibrate(double amp) {
//     // use Birks law
//     double par0 = *par0Ptr;
//     double par1 = *par1Ptr;
//     double par2 = *par2Ptr;
//     return (amp - par1) / (par0 - par2 * amp);
// }
bool cutFunc(double x, double y) { return gCut->IsInside(x, y); }

double calibratePl1(double amp) {
    // use Birks law
    double par0 = (*parsPtr)[kP0];
    double par1 = (*parsPtr)[kP1];
    double par2 = (*parsPtr)[kP2];
    return (amp - par1) / (par0 - par2 * amp);
}

double calibratePl2(double amp) {
    // use Birks law
    double par0 = (*parsPtr)[nP + kP0];
    double par1 = (*parsPtr)[nP + kP1];
    double par2 = (*parsPtr)[nP + kP2];
    return (amp - par1) / (par0 - par2 * amp);
}

double calibrateCebr(double amp) {
    // use Birks law
    double par0 = (*parsPtr)[2 * nP + kP0];
    double par1 = (*parsPtr)[2 * nP + kP1];
    double par2 = (*parsPtr)[2 * nP + kP2];
    return (amp - par1) / (par0 - par2 * amp);
}

void calibrationSystematics() {
    // ROOT::EnableImplicitMT(4);

    // Data file
    TString nameDataFile =
        "/Users/abigot/CLINM/Data/CNAO_0925/"
        "CNAO0925_Run_06_post_processed.root";
    TString nameTreeData = "tree";
    ROOT::RDataFrame dfData(nameTreeData, nameDataFile);
    // // Cut file
    // TString nameCutFile = "";
    // TFile* cutFile = new TFile(nameCutFile, "read");
    // TString nameCut = "cut";
    // TCutG* cut = static_cast<TCutG*>(cutFile->Get(nameCut));
    // gCut = cut;
    // Birks parameters sets file
    TString nameParsBirks4SystematicsFile = "parsBirksSets4Systematics.root";
    TString nameTreeParsBirks = "tree";
    ROOT::RDataFrame dfParsBirks(nameTreeParsBirks,
                                 nameParsBirks4SystematicsFile);

    std::vector<nonuplet> pars = dfParsBirks.Take<nonuplet>("fPars").GetValue();

    uint64_t nParsSets = dfParsBirks.Count().GetValue();

    // std::cout << nParsSets << "\n";

    std::vector<uint64_t> rawYields = {};

    for (uint64_t iParsSet{0}; iParsSet < nParsSets; ++iParsSet) {
        if (iParsSet > 1) continue;
        auto parsSet = pars[iParsSet];
        par0Ptr = &parsSet[0];
        par1Ptr = &parsSet[1];
        par2Ptr = &parsSet[2];

        parsPtr = &parsSet;

        auto dfCut =
            dfData.Define("fEdepPl1Calib", calibratePl1, {"fDeltaEPl1"})
                .Define("fEdepPl2Calib", calibratePl2, {"fDeltaEPl2"})
                .Define("fEdepCebrCalib", calibrateCebr, {"fDeltaECebr"});
        // .Filter(cutFunc, {"fEdepCebrCalib", "fEdepPl2Calib"});

        uint64_t rawYield = dfCut.Count().GetValue();
        rawYields.emplace_back(rawYield);

        dfCut.Display()->Print();
    }

    // for (const auto& par : parsPtr) {
    //     std::cout << par[0] << "\n";
    // }

    // std::vector<double> pars0Plastic1 =
    //     dfParsBirks.Take<double>("fPar0Plastic1").GetValue();

    // for (const auto& par0Plastic1 : pars0Plastic1) {
    // }

    // // apply calibration sets

    // //
    // auto dfCut = df.Filter(cutFunc, {"fDeltaECebr", "fDeltaEPl2"});

    //
}
