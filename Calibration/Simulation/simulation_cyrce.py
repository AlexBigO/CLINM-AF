"""
file: simulation.py
brief:
usage: python3 simulation.py cfg.yml
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

# import sys
from os import system

try:
    from yaml import load, FullLoader
except ModuleNotFoundError:
    print("Module 'pyyaml' is not installed. Please install it to run this script.")

try:
    from argparse import ArgumentParser
except ModuleNotFoundError:
    print("Module 'argparse' is not installed. Please install it to run this script.")

try:
    import opengate as gate
except ModuleNotFoundError:
    print("Module 'opengate' is not installed. Please install it to run this script.")

# units
MM = gate.g4_units.mm
CM = gate.g4_units.cm
M = gate.g4_units.m
DEG = gate.g4_units.deg
MEV = gate.g4_units.MeV


# pylint:disable=too-many-locals,too-many-statements
def main(name_config_file: str, debug: bool) -> None:
    """
    Main function

    Parameters
    ------------------------------------------------
    - name_config_file: str
        Name of the YAML config file

    - debug: bool
        Switch for debugging
    """
    if debug:
        print("DEBUG mode enabled!")
    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    campaign: str = config["campaign"]
    run = config["run"]
    energy_source: str = config["source"]["energy"]
    n_source: int = config["source"]["n"]
    # widths
    width_wheel: float = config["width"]["wheel"] * MM
    width_collimator: float = config["width"]["collimator"] * MM
    width_plastic1: float = config["width"]["plastic1"] * MM
    width_plastic2: float = config["width"]["plastic2"] * MM
    dir_output: str = config["output"]["dir"]

    # create simulation object
    sim: gate.Simulation = gate.Simulation()

    # import materials definitions
    sim.volume_manager.add_material_database("./MaterialsCLINM.db")

    # ui
    sim.verbose_level = gate.logger.DEBUG
    sim.running_verbose_level = 0  # gate.logger.RUN
    sim.g4_verbose = False
    sim.g4_verbose_level = 1
    sim.visu = False
    sim.visu_type = "qt"  # vrml
    sim.random_engine = "MersenneTwister"
    sim.random_seed = "auto"
    sim.output_dir = dir_output

    # volumes (we take the extremety and not the center as reference)
    z_wheel = 0.5 * width_wheel
    z_collimator = z_wheel + 2 * CM + 0.5 * width_collimator
    z_plastic1 = z_collimator + 9.5 * CM + 0.5 * width_plastic1
    z_plastic2 = z_plastic1 + 7.3 * CM + 0.5 * width_plastic2

    if width_wheel > 0:
        wheel = sim.add_volume("Box", name="wheel")
        wheel.mother = "world"
        wheel.material = "Aluminium"
        wheel.size = [6 * CM, 6 * CM, width_wheel]
        wheel.translation = [0, 0, z_wheel]

    collimator = sim.add_volume("TubsVolume", name="collimator")
    collimator.mother = "world"
    collimator.material = "Aluminium"
    collimator.rmin = 5 * MM
    collimator.rmax = 15 * MM
    collimator.dz = width_collimator
    collimator.sphi = 0
    collimator.dphi = 360 * DEG
    collimator.translation = [0, 0, z_collimator]

    plastic1 = sim.add_volume("Box", name="plastic1")
    plastic1.mother = "world"
    plastic1.material = "G4_PLASTIC_SC_VINYLTOLUENE"
    plastic1.size = [6 * CM, 6 * CM, width_plastic1]
    plastic1.translation = [0, 0, z_plastic1]

    plastic2 = sim.add_volume("Box", name="plastic2")
    plastic2.mother = "world"
    plastic2.material = "G4_PLASTIC_SC_VINYLTOLUENE"
    plastic2.size = [6 * CM, 6 * CM, width_plastic2]
    plastic2.translation = [0, 0, z_plastic2]

    # physics list
    sim.physics_manager.physics_list_name = "QGSP_INCLXX_HP"

    # source
    source = sim.add_source("GenericSource", name="CYRCE")
    source.particle = "proton"
    source.energy.type = "gauss"
    source.energy.mono = energy_source * MEV
    source.energy.sigma_gauss = 0.14 * MEV
    source.position.type = "point"
    source.position.center = [0, 0, 0]
    source.direction.type = "momentum"
    source.direction.momentum = [0, 0, 1]
    source.n = n_source

    name_ofile_plastics = f"{campaign}_Run{run}_MC.root"
    # actors
    # first, define HitsCollectionActors
    hits_plastic1 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsPlastic1")
    hits_plastic1.attached_to = plastic1
    hits_plastic1.output_filename = name_ofile_plastics
    hits_plastic1.attributes = [
        "TotalEnergyDeposit",
        "KineticEnergy",
        "RunID",
        "ThreadID",
        "TrackID",
        "EventID",
        "PostPosition",
        "PreStepUniqueVolumeID",
        "GlobalTime",
    ]

    hits_plastic2 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsPlastic2")
    hits_plastic2.attached_to = plastic2
    hits_plastic2.output_filename = name_ofile_plastics
    hits_plastic2.attributes = [
        "TotalEnergyDeposit",
        "KineticEnergy",
        "RunID",
        "ThreadID",
        "TrackID",
        "EventID",
        "PostPosition",
        "PreStepUniqueVolumeID",
        "GlobalTime",
    ]
    # then, define Adder to get the total energy deposited inside a detector during an event
    hits_adder_plastic1 = sim.add_actor("DigitizerAdderActor", name="HitsAdderPlastic1")
    hits_adder_plastic1.input_digi_collection = "HitsPlastic1"
    hits_adder_plastic1.group_volume = plastic1.name
    hits_adder_plastic1.output_filename = name_ofile_plastics
    hits_adder_plastic1.policy = "EnergyWeightedCentroidPosition"

    hits_adder_plastic2 = sim.add_actor("DigitizerAdderActor", name="HitsAdderPlastic2")
    hits_adder_plastic2.input_digi_collection = "HitsPlastic2"
    hits_adder_plastic2.group_volume = plastic2.name
    hits_adder_plastic2.output_filename = name_ofile_plastics
    hits_adder_plastic2.policy = "EnergyWeightedCentroidPosition"

    # TODO add later on
    # hits_cebr3 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsCeBr3")
    # hits_cebr3.attached_to = cebr3
    # hits_cebr3.output_filename = f"HitsCeBr3_{campaign}_Run{run}.root"
    # hits_cebr3.attributes = [
    #     "TotalEnergyDeposit",
    #     "KineticEnergy",
    #     "RunID",
    #     "ThreadID",
    #     "TrackID",
    #     "EventID",
    # ]

    # run simulation
    sim.run()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    DEBUG: bool = True
    main(args.name_config_file, DEBUG)
