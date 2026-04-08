/// fit.cpp
/// author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
/// brief
#include <RooAbsDataHelper.h>
#include <yaml-cpp/yaml.h>

#include <ROOT/RDataFrame.hxx>
#include <iostream>
#include <string>
#include <vector>

#include "ConfigHandler.h"
#include "RooAbsArg.h"
#include "RooAbsData.h"
#include "RooAddPdf.h"
#include "RooFFTConvPdf.h"
#include "RooFitResult.h"
#include "RooGaussian.h"
#include "RooLandau.h"
#include "RooPlot.h"
#include "RooRealVar.h"
#include "TApplication.h"
#include "TF1.h"
#include "TFile.h"
#include "TH1D.h"
#include "TString.h"
#include "TTree.h"

enum InitFitPars : uint8_t { kStart = 0, kMin, kMax, nInitFitPars };

const std::vector<TString> NAME_PARS = {"MPV_landau", "sigma_landau",
                                        "mu_gauss", "sigma_gauss", "norm"};
const std::vector<TString> LABELS_HFIT_RES = {
    "FitStatus", "Chi2OverNdf",  "Xmin",       "Xmax",
    "x_{MPV}",   "#sigma_{MPV}", "MPV_landau", "sigma_landau",
    "mu_gauss",  "sigma_gauss",  "norm"};

/// @brief Main function to perform the fit
/// @param argc
/// @param argv
int main(int argc, char** argv) {
    static constexpr bool debug = true;
    static constexpr bool batchMode = true;

    std::string nameCfgFile =
        "/Users/abigot/CLINM-AF/Calibration/ConfigFiles/FitRealData/"
        "config_fit_CNAO0425_Run2_Config1.yml";
    if (argc == 1) {
        std::cout << "Using default configuration file!\n";
    } else if (argc == 2) {
        nameCfgFile = static_cast<std::string>(argv[1]);
    } else {
        std::cout << "ERROR\n";
        return 1;
    }

    ConfigInput cfgInput = loadConfig<ConfigInput>(nameCfgFile);
    ConfigHistogram cfgHistogram = loadConfig<ConfigHistogram>(nameCfgFile);
    ConfigFit cfgFit = loadConfig<ConfigFit>(nameCfgFile);
    ConfigOutput cfgOutput = loadConfig<ConfigOutput>(nameCfgFile);

    // handle input
    const TString nameInfile = cfgInput.nameFile;
    const TString nameTree = cfgInput.nameTree;
    const auto nameBranches = cfgInput.nameBranches;
    // histogram config
    const auto nameHistos = cfgHistogram.names;
    const auto nbins = cfgHistogram.nbins;
    // fit
    const auto ranges = cfgFit.ranges;
    // fit pars
    const auto mpvsLandau = cfgFit.mpvsLandau;
    const auto sigmasLandau = cfgFit.sigmasLandau;
    const auto musGauss = cfgFit.musGauss;
    const auto sigmasGauss = cfgFit.sigmasGauss;
    const auto norms = cfgFit.norms;
    // output
    TString nameOutfile = "test_output.root";  // cfgOutput.nameFile;

    // Config for fit
    if (debug) {
        std::cout << "Ranges:\n";
        for (const auto& range : ranges) {
            std::cout << range[0] << " , " << range[1] << "\n";
        }
    }

    // for visualisation while using CMake
    std::unique_ptr<TApplication> app =
        std::make_unique<TApplication>("app", &argc, argv);

    if (debug) {
        std::cout << "nameInfile = " << nameInfile << "\n";
        std::cout << "nameTree = " << nameTree << "\n";
    }

    TFile* infile = new TFile(nameInfile.Data(), "read");

    TTree* tree = (TTree*)infile->Get<TTree>(nameTree.Data());

    std::vector<TH1D> hists;
    std::vector<TH1D> hFitResults;

    for (size_t iBranch = 0; iBranch < nameBranches.size(); ++iBranch) {
        if (iBranch > 0) {
            continue;
        }
        const auto nameBranch = nameBranches[iBranch];
        const auto nameData = nameHistos[iBranch];
        const auto nbin = nbins[iBranch];
        const auto rangeFit = ranges[iBranch];
        const auto initMpvLandau = mpvsLandau[iBranch];
        const auto initSigmaLandau = sigmasLandau[iBranch];
        const auto initMuGauss = musGauss[iBranch];
        const auto initSigmaGauss = sigmasGauss[iBranch];
        const auto initNorm = norms[iBranch];
        // const auto ymin = ymins[iBranch];
        // const auto ymax = ymaxs[iBranch];

        // Get dataframe
        ROOT::RDataFrame df(nameTree, infile, {nameBranch.Data()});

        // save histogram
        TString title("");
        title.Form(";%s; Entries;", nameData.Data());
        auto histTmp =
            df.Histo1D({nameData, title, nbin, rangeFit[0], rangeFit[1]},
                       nameBranch)
                ->Clone();
        auto hist = static_cast<TH1D*>(histTmp);
        hist->SetDirectory(0);
        hists.emplace_back(*hist);

        // start defining RooFit variables
        TString nameX("");
        nameX.Form("x%zu", iBranch);
        if (debug) std::cout << "nameX = " << nameX << "\n";
        RooRealVar x(nameBranch, nameX, rangeFit[0], rangeFit[1]);
        // Set #bins to be used for FFT sampling to 10000
        x.setBins(10000, "cache");
        x.setBins(nbin);

        auto frame = x.frame();

        TString nameDataset("");
        nameDataset.Form("dataset%zu", iBranch);
        auto dataset = df.Book<double>(
            RooDataSetHelper(nameDataset,         // Name
                             "Title of dataset",  // Title
                             RooArgSet(x)         // Variables in this dataset
                             ),
            {nameBranch.Data()}  // Column names in RDataFrame.
        );

        // construct landau
        TString nameMlVar("");
        nameMlVar.Form("MPV_landau%zu", iBranch);
        RooRealVar ml(nameMlVar, "MPV_landau", initMpvLandau[kStart],
                      initMpvLandau[kMin], initMpvLandau[kMax]);
        TString nameSlVar("");
        nameSlVar.Form("sigma_landau%zu", iBranch);
        RooRealVar sl(nameSlVar, "sigma_landau", initSigmaLandau[kStart],
                      initSigmaLandau[kMin], initSigmaLandau[kMax]);
        TString nameLandau("");
        nameLandau.Form("landau%zu", iBranch);
        RooLandau landau(nameLandau, "landau", x, ml, sl);

        // construct gauss
        TString nameMgVar("");
        nameMgVar.Form("mu_gauss%zu", iBranch);
        RooRealVar mg(nameMgVar, "mu_gauss", initMuGauss[kStart],
                      initMuGauss[kMin], initMuGauss[kMax]);
        mg.setConstant(true);  // fix mu Gauss
        TString nameSgVar("");
        nameSgVar.Form("sigma_gauss%zu", iBranch);
        RooRealVar sg(nameSgVar, "mu_gauss", initSigmaGauss[kStart],
                      initSigmaGauss[kMin], initSigmaGauss[kMax]);
        TString nameGauss("");
        nameGauss.Form("gauss%zu", iBranch);
        RooGaussian gauss(nameGauss, "gauss", x, mg, sg);

        // construct landau (x) gauss
        TString nameLxg("");
        nameLxg.Form("lxg%zu", iBranch);
        RooFFTConvPdf lxg(nameLxg, "landau (X) gauss", x, landau, gauss);
        // add norm
        TString nameNormVar("");
        nameNormVar.Form("norm%zu", iBranch);
        RooRealVar normVar(nameNormVar, "norm", initNorm[kStart],
                           initNorm[kMin], initNorm[kMax]);
        TString nameModel("");
        nameModel.Form("model%zu", iBranch);
        RooAddPdf model(nameModel, "model", {lxg}, {normVar});

        // fit
        auto fitres = model.fitTo(*dataset, RooFit::NumCPU(3), RooFit::Save());

        // plot
        dataset->plotOn(frame, RooFit::MarkerStyle(kFullCircle));
        model.plotOn(frame, RooFit::LineColor(kAzure + 4), RooFit::LineWidth(2),
                     RooFit::MoveToBack());
        frame->Draw();

        // ...

        auto funcModel = model.asTF(x);
        double xMpv = funcModel->GetMaximumX();
        if (debug) {
            std::cout << "\n\n\n\n\n\n";
            std::cout << "x MPV = " << xMpv << "\n";
        }
        auto mlVarFitted =
            (RooRealVar*)fitres->floatParsFinal().find(nameMlVar.Data());
        double sMpv = mlVarFitted->getAsymErrorHi();

        // histogram with fit results
        TString nameHFitRes("");
        nameHFitRes.Form("hFitRes%s", nameData.Data());
        auto hFitResult = TH1D(nameHFitRes, "", LABELS_HFIT_RES.size(), 0,
                               LABELS_HFIT_RES.size() - 1);
        std::vector<double> myRes = {static_cast<double>(fitres->status()),
                                     frame->chiSquare(),
                                     rangeFit[0],
                                     rangeFit[1],
                                     xMpv,
                                     sMpv};

        std::vector<double> errors = {0, 0, 0, 0, 0, 0};

        for (const auto& nameParOriginal : NAME_PARS) {
            if (nameParOriginal == "mu_gauss") {  // mu Gauss is fixed
                myRes.emplace_back(0);
                continue;
            }
            TString namePar("");
            namePar.Form("%s%zu", nameParOriginal.Data(), iBranch);
            auto parFitted =
                (RooRealVar*)fitres->floatParsFinal().find(namePar.Data());
            myRes.emplace_back(parFitted->getValV());
            errors.emplace_back(parFitted->getAsymErrorHi());
        }

        for (size_t iLabel = 0; iLabel < myRes.size(); iLabel++) {
            int ibin = iLabel + 1;
            hFitResult.GetXaxis()->SetBinLabel(ibin, LABELS_HFIT_RES[iLabel]);
            hFitResult.SetBinContent(ibin, myRes[iLabel]);
            hFitResult.SetBinError(ibin, errors[iLabel]);
        }

        if (debug) {
            std::cout << "\n\nFit result: " << hFitResult.GetBinContent(1)
                      << "\n\n";
        }

        hFitResults.emplace_back(hFitResult);
    }

    infile->Close();

    TFile* outfile = new TFile(nameOutfile.Data(), "recreate");
    for (auto& hist : hists) {
        hist.Write();
    }
    for (auto& hFitResult : hFitResults) {
        hFitResult.Write();
    }

    outfile->Close();

    // std::string nameBranch = "pl0ntu.fPlAmplitude";
    // // ROOT::RDataFrame dfInitial(*tree);
    // ROOT::RDataFrame df(nameTree.Data(), infile, {nameBranch.data()});

    // const bool useRooFit = false;

    // const int nbins = 100;

    // // using Root(!)Fit
    // if (!useRooFit) {
    //     auto histTmp =
    //         df.Histo1D({"fDeltaEPl1", "", nbins, 40., 120.},
    //         nameBranch.data())
    //             ->Clone();
    //     auto hist = static_cast<TH1D*>(histTmp);
    //     hist->Draw();
    // }

    // // using RooFit
    // if (useRooFit) {
    //     RooRealVar x("x", "x", 40., 120.);
    //     x.setBins(nbins);

    //     auto dataset = df.Book<double>(
    //         RooDataSetHelper("dataset",           // Name
    //                          "Title of dataset",  // Title
    //                          RooArgSet(x)         // Variables in this
    //                          dataset
    //                          ),
    //         {nameBranch.data()}  // Column names in RDataFrame.
    //     );
    // }

    if (!batchMode) {
        app->Run();
    }

    return 0;
}