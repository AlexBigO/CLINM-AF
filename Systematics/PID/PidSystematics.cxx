/// \file
/// \brief

#include <ROOT/RDataFrame.hxx>
#include <algorithm>
#include <iostream>
#include <vector>

#include "TCutG.h"
#include "TFile.h"
#include "TString.h"
#include "TTree.h"

#define LOG(x) std::cout << x << std::endl

TCutG* gCut = nullptr;

bool cutFunc(double x, double y) { return gCut->IsInside(x, y); }

std::vector<TCutG*> getTCutGsFromRootFile(TString nameFile) {
    TFile* file = new TFile(nameFile, "read");
    std::vector<TCutG*> cuts = {};
    auto keys = file->GetListOfKeys();

    for (const auto& key : *keys) {
        LOG(key->GetName());
        TString nameCut = TString(key->GetName());
        // TCutG* cut = static_cast<TCutG*>(file->Get(nameCut));
        cuts.emplace_back(static_cast<TCutG*>(file->Get(nameCut)));
    }

    file->Close();
    return cuts;
}

double get_mean(const std::vector<double>& v) {
    double mean{0};
    for (const auto& x : v) {
        mean += x;
    }
    mean /= v.size();
    return mean;
}

double get_rmse(const std::vector<double>& v) {
    double mean = get_mean(v);
    double rmse{0};
    for (const auto& x : v) {
        rmse += (x - mean) * (x - mean);
    }
    rmse /= v.size();
    rmse = std::sqrt(rmse);
    return rmse;
}

/// @brief
void PidSystematics() {
    ROOT::EnableImplicitMT(4);

    // Input config
    TString nameDataFile =
        "/Users/abigot/CLINM/Data/CNAO_0925/"
        "CNAO0925_Run_06_post_processed.root";
    TString nameTree = "tree";
    // Read input
    TFile* infile = new TFile(nameDataFile, "read");
    TTree* tree = (TTree*)infile->Get<TTree>(nameTree);
    ROOT::RDataFrame df(*tree);

    // open TCutG file
    TString nameCutFile = "cutsDelta.root";
    auto cuts = getTCutGsFromRootFile(nameCutFile);

    std::vector<double> rawYields = {};

    uint8_t iCutNominal{0};

    uint8_t iCut{0};
    for (const auto& cut : cuts) {
        // if (iCut > 0) continue;
        gCut = cut;
        auto dfCut = df.Filter(cutFunc, {"fDeltaECebr", "fDeltaEPl2"});
        uint64_t rawYield = dfCut.Count().GetValue();
        rawYields.emplace_back(rawYield);
        // Retrieve ID of the nominal cut
        if (static_cast<std::string>(cut->GetName()).find("nominal") !=
            std::string::npos) {
            iCutNominal = iCut;
        }
        ++iCut;
    }

    // QA
    for (const auto& rawYield : rawYields) {
        LOG(rawYield);
    }

    auto [minRawYieldIt, maxRawYieldIt] =
        std::minmax_element(rawYields.begin(), rawYields.end());

    auto minRawYield = *minRawYieldIt;
    auto maxRawYield = *maxRawYieldIt;

    // int nbins = 50;
    // TH1D* h = new TH1D("h", "", nbins, minRawYield, maxRawYield);
    // for (const auto& rawYield : rawYields) {
    //     h->Fill(rawYield);
    // }
    // h->Draw();

    LOG("\n");

    double rmse = get_rmse(rawYields);
    LOG(rmse);
    LOG("\n");
    LOG((int)iCutNominal);
    LOG(rawYields[iCutNominal]);

    double relRmse = rmse / rawYields[iCutNominal];
    LOG(relRmse);
}
