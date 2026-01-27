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

    # volumes

    z_plastic1 = 740 * MM
    z_plastic2 = z_plastic1 + 33 * MM
    # z_alu = z_plastic2 + 67 * MM
    # z_teflon = z_alu + 1 * MM  # 0.8 * MM
    # z_cebr3 = z_teflon + 26 * MM

    plastic1 = sim.add_volume("Box", name="plastic1")
    plastic1.mother = "world"
    plastic1.material = "G4_PLASTIC_SC_VINYLTOLUENE"
    plastic1.size = [6 * CM, 6 * CM, 2 * MM]
    plastic1.translation = [0, 0, z_plastic1]

    plastic2 = sim.add_volume("Box", name="plastic2")
    plastic2.mother = "world"
    plastic2.material = "G4_PLASTIC_SC_VINYLTOLUENE"
    plastic2.size = [6 * CM, 6 * CM, 4 * MM]
    plastic2.translation = [0, 0, z_plastic2]

    # alu = sim.add_volume("TubsVolume", name="alu")
    # alu.mother = "world"
    # alu.material = "Aluminium"
    # alu.rmin = 0
    # alu.rmax = 51 * MM
    # alu.dz = 0.5 * MM
    # alu.sphi = 0
    # alu.dphi = 360 * DEG
    # alu.translation = [0, 0, z_alu]

    # teflon = sim.add_volume("TubsVolume", name="teflon")
    # teflon.mother = "world"
    # teflon.material = "Teflon"
    # teflon.rmin = 0
    # teflon.rmax = 51 * MM
    # teflon.dz = 0.5 * MM
    # teflon.sphi = 0
    # teflon.dphi = 360 * DEG
    # teflon.translation = [0, 0, z_teflon]

    # we do not need CeBr3 here as we only want to calibrate the plastic detectors
    # cebr3 = sim.add_volume("TubsVolume", name="cebr3")
    # cebr3.mother = "world"
    # cebr3.material = "CeBr3"
    # cebr3.rmin = 0
    # cebr3.rmax = 51 * MM
    # cebr3.dz = 25.5 * MM
    # cebr3.sphi = 0
    # cebr3.dphi = 360 * DEG
    # cebr3.translation = [0, 0, z_cebr3]

    # physics list
    sim.physics_manager.physics_list_name = "QGSP_INCLXX_HP"

    # source
    source = sim.add_source("GenericSource", name="CNAO")
    source.particle = "ion"
    source.ion.Z = 6
    source.ion.A = 12
    source.ion.Q = 6
    source.ion.E = 0
    source.energy.mono = (energy_source * MEV) * source.ion.A  # in MeV, not in MeV/u !
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

    # try with attachment to both of the scintillators
    # hits_plastics = sim.add_actor("DigitizerHitsCollectionActor", name="HitsPlastics")
    # hits_plastics.attached_to = [plastic1.name, plastic2.name]
    # name_ofile_pls = f"HitsPlastics_{campaign}_Run{run}.root"
    # hits_plastics.output_filename = name_ofile_pls
    # hits_plastics.attributes = [
    #     "TotalEnergyDeposit",
    #     "KineticEnergy",
    #     "RunID",
    #     "ThreadID",
    #     "TrackID",
    #     "EventID",
    #     # below info is needed for DigitizerAdderActor
    #     "PostPosition",
    #     "PreStepUniqueVolumeID",
    #     "GlobalTime",
    # ]

    # hits_adder_plastics = sim.add_actor("DigitizerAdderActor", name="HitsAdderPlastics")
    # hits_adder_plastics.input_digi_collection = "HitsPlastics"
    # # hits_adder_plastics.group_volume = plastic2.name  # FIXME this does not seem to accept a list
    # hits_adder_plastics.output_filename = name_ofile_plastics
    # hits_adder_plastics.policy = "EnergyWeightedCentroidPosition"

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

    # TODO remove this paragraph ; merge output files
    # name_ofile = f"{dir_output}/Hits_{campaign}_Run{run}.root"
    # cmd_merge = (
    #     f"hadd {name_ofile} {dir_output}/{name_ofile_pl1} {dir_output}/{name_ofile_pl2}"
    # )
    # print(f"Merging output files into {name_ofile}: ")
    # system(cmd_merge)


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    DEBUG: bool = True
    main(args.name_config_file, DEBUG)
