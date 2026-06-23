#include <ROOT/RDataFrame.hxx>
#include <algorithm>
#include <iostream>
#include <vector>

#include "TCutG.h"
#include "TFile.h"
#include "TString.h"
#include "TTree.h"

static constexpr bool debug = false;

enum Pars : std::size_t { kP0 = 0, kP1, kP2, nP };
using triplet = std::array<double, nP>;
using nonuplet = std::array<double, nP * nP>;

#define LOG(x) std::cout << x << std::endl

void generateParsBirks4Systematics() {
    std::cout << "Hello world!" << std::endl;

    // ROOT::EnableImplicitMT(4);

    TString nameParsBirks4SystematicsFile = "info4ParBirksVariationsAll.root";

    ROOT::RDataFrame dfPlastic1("treePlastic1", nameParsBirks4SystematicsFile);
    ROOT::RDataFrame dfPlastic2("treePlastic2", nameParsBirks4SystematicsFile);
    ROOT::RDataFrame dfCebr("treeCebr", nameParsBirks4SystematicsFile);

    std::vector<triplet> parsTripletsPlastic1 = {};
    std::vector<triplet> parsTripletsPlastic2 = {};
    std::vector<triplet> parsTripletsCebr = {};

    std::vector<std::string> nameCols = {"fPar0", "fPar1", "fPar2"};

    dfPlastic1.Foreach(
        [&parsTripletsPlastic1](double p0, double p1, double p2) {
            parsTripletsPlastic1.emplace_back(triplet{p0, p1, p2});
        },
        nameCols);

    dfPlastic2.Foreach(
        [&parsTripletsPlastic2](double p0, double p1, double p2) {
            parsTripletsPlastic2.emplace_back(triplet{p0, p1, p2});
        },
        nameCols);

    dfCebr.Foreach(
        [&parsTripletsCebr](double p0, double p1, double p2) {
            parsTripletsCebr.emplace_back(triplet{p0, p1, p2});
        },
        nameCols);

    uint64_t nParsNonuplets = parsTripletsPlastic1.size() *
                              parsTripletsPlastic2.size() *
                              parsTripletsCebr.size();
    std::cout << "Total number of parameters sets: " << nParsNonuplets << "\n";

    std::vector<nonuplet> parsNonuplets = {};
    for (const auto& tripletPlastic1 : parsTripletsPlastic1) {
        for (const auto& tripletPlastic2 : parsTripletsPlastic2) {
            for (const auto& tripletCebr : parsTripletsCebr) {
                // fill vector with nonuplets (a triplet for each detector)
                nonuplet tripletAll = {};
                std::size_t iPosNonuplet = 0;
                for (const auto& parPlastic1 : tripletPlastic1) {
                    tripletAll[iPosNonuplet] = parPlastic1;
                    ++iPosNonuplet;
                }
                for (const auto& parPlastic2 : tripletPlastic2) {
                    tripletAll[iPosNonuplet] = parPlastic2;
                    ++iPosNonuplet;
                }
                for (const auto& parCebr : tripletCebr) {
                    tripletAll[iPosNonuplet] = parCebr;
                    ++iPosNonuplet;
                }

                parsNonuplets.emplace_back(tripletAll);
            }
        }
    }

    if (debug) {
        for (const auto& parNonuplet : parsNonuplets) {
            for (const auto& par : parNonuplet) {
                std::cout << par << "\t";
            }
            std::cout << "\n";
        }
    }

    // ROOT::RDataFrame df(nParsNonuplets);  // an RDF that will generate 100
    // entries (currently empty)
    // int x = -1;
    // auto df2 = df.Define("fPar0Plastic1", []() -> double {
    //                  return ++x;
    //              }).Define("xx", []() -> int { return x * x; });

    ROOT::RDataFrame dfEmpty(nParsNonuplets);
    // auto df = dfEmpty
    //               .Define("fPar0Plastic1",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][kP0];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar1Plastic1",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][kP1];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar2Plastic1",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][kP2];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar0Plastic2",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][nP + kP0];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar1Plastic2",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][nP + kP1];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar2Plastic2",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][nP + kP2];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar0Cebr",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][2 * nP + kP0];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar1Cebr",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][2 * nP + kP1];
    //                       },
    //                       {"rdfentry_"})
    //               .Define("fPar2Cebr",
    //                       [&parsNonuplets](ULong64_t iSet) {
    //                           return parsNonuplets[iSet][2 * nP + kP2];
    //                       },
    //                       {"rdfentry_"});  // dependency on the index column

    auto df = dfEmpty.Define(
        "fPars",
        [&parsNonuplets](ULong64_t iSet) { return parsNonuplets[iSet]; },
        {"rdfentry_"});

    // if (debug)
    df.Display()->Print();

    LOG("Writing output file with all parameters sets...");

    TString nameOfile = "parsBirksSets4Systematics.root";
    df.Snapshot<nonuplet>("tree", nameOfile.Data(), {"fPars"});
}
