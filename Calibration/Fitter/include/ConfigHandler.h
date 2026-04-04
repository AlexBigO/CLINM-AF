/// ConfigHandler.h
/// \brief File to define handlers for YAML config file importation

#ifndef CONFIGHANDLER_H
#define CONFIGHANDLER_H

#include <yaml-cpp/yaml.h>

#include <array>
#include <iostream>
#include <string>
#include <vector>

#include "TString.h"

// dummy value
static constexpr double dummyDouble = -999.;

/// @brief Function to load any user-defined config
/// @tparam T
/// @param path
/// @return
template <typename T>
T loadConfig(const std::string& path) {
    return YAML::LoadFile(path).as<T>();
}

struct ConfigInput {
    TString nameFile;
    TString nameTree;
    std::vector<TString> nameBranches{};
};

struct ConfigHistogram {
    std::vector<TString> names{};
    std::vector<int> nbins{};
};

struct ConfigFit {
    std::vector<std::array<double, 2>> ranges{};
    // in pars
    std::vector<std::array<double, 3>> mpvsLandau{};
    std::vector<std::array<double, 3>> sigmasLandau{};
    std::vector<std::array<double, 3>> musGauss{};
    std::vector<std::array<double, 3>> sigmasGauss{};
    std::vector<std::array<double, 3>> norms{};
};

struct ConfigOutput {
    TString nameFile;
    // in plot
    std::vector<std::string> labels{};
    std::vector<double> ymins{};
    std::vector<double> ymaxs{};
    // in plot-info
    std::string exp;
    std::string campaign;
    std::string run;
    // in plot-info-beam
    std::string particle;
    std::string energy;
};

namespace YAML {

// override convert method

template <>
struct convert<ConfigOutput> {
    static bool decode(const Node& node, ConfigOutput& rhs) {
        const Node mynode = node["output"];
        rhs.nameFile = static_cast<TString>(mynode["file"].as<std::string>());

        const Node nodePlot = node["output"]["plot"];
        rhs.labels = nodePlot["label"].as<std::vector<std::string>>();

        // safety for 'auto' option in ymin
        const auto str_ymins = nodePlot["ymin"].as<std::vector<std::string>>();
        bool yminIsAuto = false;
        for (const auto& str_ymin : str_ymins) {
            if (str_ymin == "auto") {
                yminIsAuto = true;
                break;
            }
        }
        if (yminIsAuto) {
            // put dummy values
            for (size_t i = 0; i < str_ymins.size(); ++i) {
                rhs.ymins.emplace_back(dummyDouble);
            }
        } else {
            rhs.ymins = nodePlot["ymin"].as<std::vector<double>>();
        }
        // safety for 'auto' option in ymax
        const auto str_ymaxs = nodePlot["ymax"].as<std::vector<std::string>>();
        bool ymaxIsAuto = false;
        for (const auto& str_ymax : str_ymaxs) {
            if (str_ymax == "auto") {
                ymaxIsAuto = true;
                break;
            }
        }
        if (ymaxIsAuto) {
            // put dummy values
            for (size_t i = 0; i < str_ymaxs.size(); ++i) {
                rhs.ymaxs.emplace_back(dummyDouble);
            }
        } else {
            rhs.ymaxs = nodePlot["ymax"].as<std::vector<double>>();
        }

        const Node nodePlotInfo = node["output"]["plot"]["info"];
        rhs.exp = static_cast<TString>(nodePlotInfo["exp"].as<std::string>());
        rhs.campaign =
            static_cast<TString>(nodePlotInfo["campaign"].as<std::string>());
        rhs.run = static_cast<TString>(nodePlotInfo["run"].as<std::string>());

        const Node nodePlotInfoBeam = node["output"]["plot"]["info"]["beam"];
        rhs.particle = static_cast<TString>(
            nodePlotInfoBeam["particle"].as<std::string>());
        rhs.energy =
            static_cast<TString>(nodePlotInfoBeam["energy"].as<std::string>());
        return true;
    }
};

template <>
struct convert<ConfigFit> {
    static bool decode(const Node& node, ConfigFit& rhs) {
        const Node mynode = node["fit"];
        rhs.ranges = mynode["range"].as<std::vector<std::array<double, 2>>>();
        const Node nodePars = node["fit"]["pars"];
        // safeties for 'auto' option
        const auto str_mpvsLandau =
            nodePars["MPV_landau"]
                .as<std::vector<std::array<std::string, 3>>>();
        for (const auto& str_mpvLandau : str_mpvsLandau) {
            if (str_mpvLandau[0] == "auto") {
                std::cout << "ERROR: option 'auto' (in MPV_landau) not "
                             "possible with fit.cpp!\n";
                exit(1);
            }
        }
        const auto str_sigmasLandau =
            nodePars["sigma_landau"]
                .as<std::vector<std::array<std::string, 3>>>();
        for (const auto& str_sigmaLandau : str_sigmasLandau) {
            if (str_sigmaLandau[0] == "auto") {
                std::cout << "ERROR: option 'auto' (in sigma_landau) not "
                             "possible with fit.cpp!\n";
                exit(1);
            }
        }
        // get the 'pars' config
        rhs.mpvsLandau =
            nodePars["MPV_landau"].as<std::vector<std::array<double, 3>>>();
        rhs.sigmasLandau =
            nodePars["sigma_landau"].as<std::vector<std::array<double, 3>>>();
        rhs.musGauss =
            nodePars["mu_gauss"].as<std::vector<std::array<double, 3>>>();
        rhs.sigmasGauss =
            nodePars["sigma_gauss"].as<std::vector<std::array<double, 3>>>();
        rhs.norms = nodePars["norm"].as<std::vector<std::array<double, 3>>>();

        return true;
    }
};

template <>
struct convert<ConfigInput> {
    static bool decode(const Node& node, ConfigInput& rhs) {
        const Node mynode = node["input"];
        rhs.nameFile = static_cast<TString>(mynode["file"].as<std::string>());
        rhs.nameTree =
            static_cast<TString>(mynode["tree"]["name"].as<std::string>());
        const auto tmpNameBranches =
            mynode["tree"]["branches"].as<std::vector<std::string>>();
        for (const auto& name : tmpNameBranches) {
            rhs.nameBranches.emplace_back(static_cast<TString>(name));
        }

        return true;
    }
};

template <>
struct convert<ConfigHistogram> {
    static bool decode(const Node& node, ConfigHistogram& rhs) {
        const Node mynode = node["histogram_config"];
        const auto tmpNames = mynode["name"].as<std::vector<std::string>>();
        for (const auto& name : tmpNames) {
            rhs.names.emplace_back(static_cast<TString>(name));
        }
        const auto tmpNbins = mynode["nbin"].as<std::vector<int>>();
        for (const auto& nbin : tmpNbins) {
            rhs.nbins.emplace_back(nbin);
        }

        return true;
    }
};

}  // namespace YAML

#endif  // CONFIGHANDLER_H