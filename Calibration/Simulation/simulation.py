"""
file: simulation.py
brief:
usage: python3 simulation.py cfg.yml
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

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
        print("Hello world!")
    # import configuration
    config: dict = {}
    with open(name_config_file, "r", encoding="utf-8") as yml_config_file:
        config = load(yml_config_file, FullLoader)

    campaign: str = config["campaign"]
    run: str = str(config["run"])
    energy_source: str = config["source"]["energy"]
    n_source: int = config["source"]["n"]
    dir_output: str = config["output"]["dir"]

    # create simulation object
    sim: gate.Simulation = gate.Simulation()

    # import materials definitions
    sim.volume_manager.add_material_database("./MaterialsCLINM.db")

    # ui
    sim.verbose_level = gate.logger.DEBUG
    sim.running_verbose_level = gate.logger.RUN
    sim.g4_verbose = False
    sim.g4_verbose_level = 1
    sim.visu = False
    sim.visu_type = "qt"  # vrml
    sim.random_engine = "MersenneTwister"
    sim.random_seed = "auto"
    sim.output_dir = dir_output

    # volumes

    dist_plastic1 = 740 * MM
    dist_plastic2 = dist_plastic1 + 33 * MM
    dist_alu = dist_plastic2 + 67 * MM
    dist_teflon = dist_alu + 1 * MM  # 0.8 * MM
    dist_cebr3 = dist_teflon + 26 * MM

    plastic1 = sim.add_volume("Box", name="plastic1")
    plastic1.mother = "world"
    plastic1.material = "G4_PLASTIC_SC_VINYLTOLUENE"
    plastic1.size = [6 * CM, 6 * CM, 2 * MM]
    plastic1.translation = [0, 0, dist_plastic1]

    plastic2 = sim.add_volume("Box", name="plastic2")
    plastic2.mother = "world"
    plastic2.material = "G4_PLASTIC_SC_VINYLTOLUENE"
    plastic2.size = [6 * CM, 6 * CM, 4 * MM]
    plastic2.translation = [0, 0, dist_plastic2]

    alu = sim.add_volume("TubsVolume", name="alu")
    alu.mother = "world"
    alu.material = "Aluminium"
    alu.rmin = 0
    alu.rmax = 51 * MM
    alu.dz = 0.5 * MM
    alu.sphi = 0
    alu.dphi = 360 * DEG
    alu.translation = [0, 0, dist_alu]

    teflon = sim.add_volume("TubsVolume", name="teflon")
    teflon.mother = "world"
    teflon.material = "Teflon"
    teflon.rmin = 0
    teflon.rmax = 51 * MM
    teflon.dz = 0.5 * MM
    teflon.sphi = 0
    teflon.dphi = 360 * DEG
    teflon.translation = [0, 0, dist_teflon]

    cebr3 = sim.add_volume("TubsVolume", name="cebr3")
    cebr3.mother = "world"
    cebr3.material = "CeBr3"
    cebr3.rmin = 0
    cebr3.rmax = 51 * MM
    cebr3.dz = 25.5 * MM
    cebr3.sphi = 0
    cebr3.dphi = 360 * DEG
    cebr3.translation = [0, 0, dist_cebr3]

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

    # actors
    hits_plastic1 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsPlastic1")
    hits_plastic1.attached_to = plastic1
    hits_plastic1.output_filename = f"HitsPlastic1_{campaign}_Run{run}.root"
    hits_plastic1.attributes = [
        "TotalEnergyDeposit",
        "KineticEnergy",
        "RunID",
        "ThreadID",
        "TrackID",
        "EventID",
    ]

    hits_plastic2 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsPlastic2")
    hits_plastic2.attached_to = plastic2
    hits_plastic2.output_filename = f"HitsPlastic2_{campaign}_Run{run}.root"
    hits_plastic2.attributes = [
        "TotalEnergyDeposit",
        "KineticEnergy",
        "RunID",
        "ThreadID",
        "TrackID",
        "EventID",
    ]

    hits_cebr3 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsCeBr3")
    hits_cebr3.attached_to = cebr3
    hits_cebr3.output_filename = f"HitsCeBr3_{campaign}_Run{run}.root"
    hits_cebr3.attributes = [
        "TotalEnergyDeposit",
        "KineticEnergy",
        "RunID",
        "ThreadID",
        "TrackID",
        "EventID",
    ]

    # run simulation
    sim.run()


if __name__ == "__main__":
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    DEBUG: bool = True
    main(args.name_config_file, DEBUG)
