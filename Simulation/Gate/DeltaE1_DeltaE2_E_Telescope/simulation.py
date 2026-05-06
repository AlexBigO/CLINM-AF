"""
file: simulation.py
brief: Script for GATE simulation of DeltaE1-DeltaE2-E telescope with target
usage: python3 simulation.py cfg.yml
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

import sys

try:
    import numpy as np
except ModuleNotFoundError:
    print("Module 'numpy' is not installed. Please install it to run this script.")

try:
    from scipy.spatial.transform import Rotation
except ModuleNotFoundError:
    print("Module 'scipy' is not installed. Please install it to run this script.")

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

try:
    sys.path.append("../../../Utils/")
    from logger import Logger
except ModuleNotFoundError:
    print(
        "Module 'logger' is not in the '../../../Utils/' directory. Add it to run this script."
    )

# units
MM = gate.g4_units.mm
CM = gate.g4_units.cm
M = gate.g4_units.m
DEG = gate.g4_units.deg
MEV = gate.g4_units.MeV

# telescope elements
NAMES_EL_TELESCOPE = [
    "BlackTapeBeforePl1",
    "Plastic1",
    "BlackTapeAfterPl1",
    "BlackTapeBeforePl2",
    "Plastic2",
    "BlackTapeAfterPl2",
    "WindowCebr",
]

# volume types
TYPE_BOX = "Box"
TYPE_TUBS = "Tubs"

# ids for 3D coordinates
IDX = 0
IDY = 1
IDZ = 2

# default name for the world volume
NAME_WORLD = "world"

# colors
RED = [1, 0, 0, 1]
GREEN = [0, 1, 0, 1]
BLUE = [0, 0, 1, 1]
CYAN = [0, 1, 1, 1]
YELLOW = [1, 1, 0, 1]


def apply_rotation(obj, axis: str, angle) -> None:
    """
    Helper method to apply rotation to an object

    Parameters
    ------------------------------------------------
    - obj:
        The gate object that shall rotate

    - axis: str
        Name of the rotation axis: 'x', 'y' or 'z'

    - angle: float
        Rotation angle
    """
    obj.rotation = Rotation.from_euler(axis, angle, degrees=False).as_matrix()


def turn_around_yaxis(obj, angle: float) -> None:
    """
    Helper method to turn an object arount world y axis

    Parameters
    ------------------------------------------------
    - obj:
        The gate object that shall rotate

    - angle: float
        Rotation angle
    """
    radius = obj.translation[IDZ]
    x = radius * np.sin(angle)
    y = 0
    z = radius * np.cos(angle)
    translation = [x, y, z]

    # apply orbital translation around y axis of the target (at the origin of the world)
    obj.translation = translation
    # apply rotation around y axis of the object
    apply_rotation(obj, "y", angle)


def set_source(
    sim: gate.Simulation, cfg_source: dict, dist_source_target: float, nthreads: int
) -> None:
    """
    Helper method to define the source

    Parameters
    ------------------------------------------------
    - sim: gate.Simulation
        The gate simulation object

    - cfg_source: dict
        Configuration for the source imported from the YAML file

    - dist_source_target: float
        Distance between source and target (edge-to-edge)

    - nthreads: int
        Number of threads for multithreading purposes
    """
    source = sim.add_source("GenericSource", name="Source")
    name_particle: str = cfg_source["particle"]
    # default config with proton
    z: int = 1
    source.particle = "proton"
    # check if another ion is selected
    if name_particle == "helium":
        z = 2
    elif name_particle == "lithium":
        z = 3
    elif name_particle == "bore":
        z = 5
    elif name_particle == "carbon":
        z = 6
    if z != 1:
        source.particle = "ion"
        source.ion.Z = z
        source.ion.A = 2 * z
        source.ion.Q = z
        source.ion.E = 0
    source.energy.type = "gauss"
    energy_source: float = cfg_source["energy_spectrum"]["mean"]
    if z == 1:
        source.energy.mono = energy_source * MEV
    else:
        source.energy.mono = (
            energy_source * MEV
        ) * source.ion.A  # in MeV, not in MeV/u !
    source.energy.sigma_gauss = cfg_source["energy_spectrum"]["sigma"] * MEV
    source.position.center = [0, 0, 0]
    source.position.translation = [0, 0, -dist_source_target]
    source.direction.type = "momentum"
    source.direction.momentum = [0, 0, 1]
    source.n = int(cfg_source["n"] / nthreads)


def set_actors(sim: gate.Simulation, name_ofile: str):
    """
    Helper method to set the actors of the simulation

    Parameters
    ------------------------------------------------
    - sim: gate.Simulation
        The gate simulation object

    - name_ofile: str
        Name of the output (.root) file
    """

    # common parameters
    digi_attributes: list = [
        "TotalEnergyDeposit",
        "KineticEnergy",
        "RunID",
        "ThreadID",
        "TrackID",
        "EventID",
        "PostPosition",
        "PreStepUniqueVolumeID",
        "GlobalTime",
        "ParticleName",
        "PDGCode",
    ]

    digi_adder_policy: str = "EnergyWeightedCentroidPosition"

    # first, define HitsCollectionActors
    hits_plastic1 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsPlastic1")
    hits_plastic1.attached_to = "Plastic1"
    hits_plastic1.output_filename = name_ofile
    hits_plastic1.attributes = digi_attributes

    hits_plastic2 = sim.add_actor("DigitizerHitsCollectionActor", name="HitsPlastic2")
    hits_plastic2.attached_to = "Plastic2"
    hits_plastic2.output_filename = name_ofile
    hits_plastic2.attributes = digi_attributes

    hits_cebr = sim.add_actor("DigitizerHitsCollectionActor", name="HitsCebr")
    hits_cebr.attached_to = "Cebr"
    hits_cebr.output_filename = name_ofile
    hits_cebr.attributes = digi_attributes

    # then, define Adder to get the total energy deposited inside a detector during an event
    hits_adder_plastic1 = sim.add_actor("DigitizerAdderActor", name="HitsAdderPlastic1")
    hits_adder_plastic1.input_digi_collection = "HitsPlastic1"
    hits_adder_plastic1.group_volume = "Plastic1"
    hits_adder_plastic1.output_filename = name_ofile
    hits_adder_plastic1.policy = digi_adder_policy

    hits_adder_plastic2 = sim.add_actor("DigitizerAdderActor", name="HitsAdderPlastic2")
    hits_adder_plastic2.input_digi_collection = "HitsPlastic2"
    hits_adder_plastic2.group_volume = "Plastic2"
    hits_adder_plastic2.output_filename = name_ofile
    hits_adder_plastic2.policy = digi_adder_policy

    hits_adder_cebr = sim.add_actor("DigitizerAdderActor", name="HitsAdderCebr")
    hits_adder_cebr.input_digi_collection = "HitsCebr"
    hits_adder_cebr.group_volume = "Cebr"
    hits_adder_cebr.output_filename = name_ofile
    hits_adder_cebr.policy = digi_adder_policy


# pylint:disable=too-many-locals,too-many-statements, too-many-branches
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

    # visu
    activate_visu: bool = config["visu"]["activate"]
    type_visu: str = config["visu"]["type"]
    # multithreading
    nthreads: int | None = config["multithreading"]["nthreads"]
    # physics list
    physics_list: str = config["physics_list"]
    # source
    config_source: dict = config["source"]
    # target
    has_target: bool = config["target"]["exists"]

    if has_target:
        material_target = config["target"]["material"]
        size_target = [s * CM for s in config["target"]["size"]]
    # distances
    dist_source_target: float | None = None
    dist_target_pl1: float | None = None
    if has_target:
        dist_source_target = config["distances"]["source_target"] * CM
        dist_target_pl1 = config["distances"]["target_plastic1"] * CM
    dist_pl1_pl2: float = config["distances"]["plastic1_plastic2"] * CM
    dist_pl2_cebr: float = config["distances"]["plastic2_cebr"] * CM
    # telescope
    angle_telescope = config["telescope"]["angle"]
    if angle_telescope is not None:
        angle_telescope *= DEG
    # campaign and run
    campaign: str = config["campaign"]
    run = config["run"]
    # output
    dir_output: str = config["output"]["dir"]
    name_ofile = f"{campaign}_Run{run}_{config_source['particle']}_wo_target_MC.root"
    if has_target:
        name_ofile = f"{campaign}_Run{run}_{config_source['particle']}_on_{material_target}_MC.root"

    # create simulation object
    sim: gate.Simulation = gate.Simulation()

    # import materials definitions
    sim.volume_manager.add_material_database("./data/MaterialsCLINM.db")

    # ui
    sim.verbose_level = gate.logger.DEBUG
    sim.running_verbose_level = gate.logger.RUN
    sim.g4_verbose = False
    sim.g4_verbose_level = 0  # 1
    sim.visu = activate_visu
    sim.visu_type = type_visu
    sim.random_engine = "MersenneTwister"
    sim.random_seed = "auto"
    sim.output_dir = dir_output

    if nthreads is None:
        nthreads = int(1)
    else:
        ui = sim.user_info
        ui.number_of_threads = nthreads

    # names
    names: dict = {
        NAME_WORLD: None,
    }

    if has_target:
        names.update({"Target": "Target"})

    names.update(
        {
            "BlackTapeBeforePl1": "BlackTapeBeforePl1",
            "Plastic1": "Plastic1",
            "BlackTapeAfterPl1": "BlackTapeAfterPl1",
            "BlackTapeBeforePl2": "BlackTapeBeforePl2",
            "Plastic2": "Plastic2",
            "BlackTapeAfterPl2": "BlackTapeAfterPl2",
            "WindowCebr": "WindowCebr",
            "ReflCebr": "ReflCebr",
            "Cebr": "Cebr",
        }
    )

    # sizes
    sizes: dict = {
        NAME_WORLD: [3 * M, 3 * M, 6 * M],
    }
    if has_target:
        sizes.update({"Target": size_target})
    sizes.update(
        {
            "BlackTapeBeforePl1": [6 * CM, 6 * CM, 0.2 * MM],
            "Plastic1": [6 * CM, 6 * CM, 2 * MM],
            "BlackTapeAfterPl1": [6 * CM, 6 * CM, 0.2 * MM],
            "BlackTapeBeforePl2": [6 * CM, 6 * CM, 0.2 * MM],
            "Plastic2": [6 * CM, 6 * CM, 4 * MM],
            "BlackTapeAfterPl2": [6 * CM, 6 * CM, 0.2 * MM],
            "WindowCebr": [0, 51 * MM, 52.4 * MM],  # Dmin, Dmax, H for Tubs
            "ReflCebr": [0, 50.8 * MM, 52 * MM],  # Dmin, Dmax, H for Tubs
            "Cebr": [0, 50.6 * MM, 51 * MM],  # Dmin, Dmax, H for Tubs
        }
    )
    # define reference frame of each volume (for positions only!)
    # it does not affect the mother
    ref_frames: dict = {
        NAME_WORLD: None,
    }
    if has_target:
        ref_frames.update(
            {
                "Target": NAME_WORLD,
                "BlackTapeBeforePl1": "Target",
            }
        )
    else:
        ref_frames.update({"BlackTapeBeforePl1": NAME_WORLD})

    ref_frames.update(
        {
            "Plastic1": "BlackTapeBeforePl1",
            "BlackTapeAfterPl1": "Plastic1",
            "BlackTapeBeforePl2": "BlackTapeAfterPl1",
            "Plastic2": "BlackTapeBeforePl2",
            "BlackTapeAfterPl2": "Plastic2",
            "WindowCebr": "BlackTapeAfterPl2",
            "ReflCebr": "WindowCebr",
            "Cebr": "ReflCebr",
        }
    )

    # positions
    # CAREFUL: the distances filled are edge-to-edge, this will require a correction later on
    positions: dict = {
        NAME_WORLD: [0, 0, 0],
    }

    if has_target:
        positions.update(
            {
                "Target": [0, 0, 0.5 * sizes["Target"][IDZ]],
                "BlackTapeBeforePl1": [0, 0, dist_target_pl1],  # in Target frame
            }
        )
    else:
        positions.update(
            {"BlackTapeBeforePl1": [0, 0, 0.5 * sizes["BlackTapeBeforePl1"][IDZ]]}
        )  # in world frame

    positions.update(
        {
            "Plastic1": [0, 0, 0],  # in BlackTapeBeforePl1 frame
            "BlackTapeAfterPl1": [0, 0, 0],  # in Plastic1 frame
            "BlackTapeBeforePl2": [0, 0, dist_pl1_pl2],  # in BlackTapeAfterPl1 frame
            "Plastic2": [0, 0, 0],  # in BlackTapeBeforePl2 frame
            "BlackTapeAfterPl2": [0, 0, 0],  # in Plastic2 frame
            "WindowCebr": [0, 0, dist_pl2_cebr],  # in BlackTapeAfterPl2 frame
            "ReflCebr": [0, 0, 0],  # in WindowCebr frame
            "Cebr": [0, 0, 0],  # in ReflCebr frame
        }
    )

    mothers: dict = {
        NAME_WORLD: None,
    }
    if has_target:
        mothers.update({"Target": NAME_WORLD})
    mothers.update(
        {
            "BlackTapeBeforePl1": NAME_WORLD,
            "Plastic1": NAME_WORLD,
            "BlackTapeAfterPl1": NAME_WORLD,
            "BlackTapeBeforePl2": NAME_WORLD,
            "Plastic2": NAME_WORLD,
            "BlackTapeAfterPl2": NAME_WORLD,
            "WindowCebr": NAME_WORLD,
            "ReflCebr": "WindowCebr",
            "Cebr": "ReflCebr",
        }
    )

    colors: dict = {
        NAME_WORLD: None,
    }
    if has_target:
        colors.update({"Target": RED})
    colors.update(
        {
            "BlackTapeBeforePl1": GREEN,
            "Plastic1": BLUE,
            "BlackTapeAfterPl1": YELLOW,
            "BlackTapeBeforePl2": GREEN,
            "Plastic2": BLUE,
            "BlackTapeAfterPl2": YELLOW,
            "WindowCebr": None,
            "ReflCebr": None,
            "Cebr": None,
        }
    )

    # correct distance in world frame
    for (key, ref), (_, mother) in zip(ref_frames.items(), mothers.items()):
        if mother is None or mother != NAME_WORLD:
            continue

        # from ref frame to world frame
        for idx in range(3):
            positions[key][idx] += positions[ref][idx]
            # distance from edge to edge and not center to center
            if idx == IDZ:
                positions[key][idx] += 0.5 * sizes[key][IDZ]
                if has_target and key != "Target":
                    positions[key][idx] += 0.5 * sizes[ref][IDZ]
                if not has_target and key != "BlackTapeBeforePl1":
                    positions[key][idx] += 0.5 * sizes[ref][IDZ]

    # materials
    materials: dict = {
        NAME_WORLD: "G4_Galactic",  # approximation to void
    }
    if has_target:
        materials.update({"Target": material_target})
    materials.update(
        {
            "BlackTapeBeforePl1": "G4_POLYVINYL_CHLORIDE",
            "Plastic1": "G4_PLASTIC_SC_VINYLTOLUENE",
            "BlackTapeAfterPl1": "G4_POLYVINYL_CHLORIDE",
            "BlackTapeBeforePl2": "G4_POLYVINYL_CHLORIDE",
            "Plastic2": "G4_PLASTIC_SC_VINYLTOLUENE",
            "BlackTapeAfterPl2": "G4_POLYVINYL_CHLORIDE",
            "WindowCebr": "G4_Al",
            "ReflCebr": "G4_TEFLON",
            "Cebr": "CeBr3",
        }
    )

    # volume types
    type_vols: dict = {
        NAME_WORLD: TYPE_BOX,
    }
    if has_target:
        type_vols.update({"Target": TYPE_BOX})
    type_vols.update(
        {
            "BlackTapeBeforePl1": TYPE_BOX,
            "Plastic1": TYPE_BOX,
            "BlackTapeAfterPl1": TYPE_BOX,
            "BlackTapeBeforePl2": TYPE_BOX,
            "Plastic2": TYPE_BOX,
            "BlackTapeAfterPl2": TYPE_BOX,
            "WindowCebr": TYPE_TUBS,
            "ReflCebr": TYPE_TUBS,
            "Cebr": TYPE_TUBS,
        }
    )

    vols: dict = {}

    for (
        (key, name),
        (_, size),
        (_, position),
        (_, type_vol),
        (_, mat),
        (_, ref),
        (_, mother),
        (_, color),
    ) in zip(
        names.items(),
        sizes.items(),
        positions.items(),
        type_vols.items(),
        materials.items(),
        ref_frames.items(),
        mothers.items(),
        colors.items(),
    ):
        if key == NAME_WORLD:
            vols[key] = sim.world
            vols[key].size = size
        elif type_vol == TYPE_BOX:
            vols[key] = sim.add_volume("Box", name=name)
            vols[key].size = size
        elif type_vol == TYPE_TUBS:
            vols[key] = sim.add_volume("TubsVolume", name=name)
            vols[key].rmin = size[IDX] / 2.0
            vols[key].rmax = size[IDY] / 2.0
            vols[key].dz = size[IDZ] / 2.0
            vols[key].sphi = 0
            vols[key].dphi = 360 * DEG

        vols[key].translation = position
        vols[key].material = mat

        if mother is not None:
            vols[key].mother = mother

        if color is not None:
            vols[key].color = color

    # rotate telescope
    if angle_telescope is not None:
        for name in NAMES_EL_TELESCOPE:
            turn_around_yaxis(vols[name], angle_telescope)

    # physics list
    sim.physics_manager.physics_list_name = physics_list

    # source
    if has_target:
        set_source(sim, config_source, dist_source_target, nthreads)
    else:
        dist_source_pl1: float | None = config["distances"]["source_plastic1"] * CM
        if dist_source_pl1 is None:
            Logger("'source_plastic1' distance must be not null if no target!", "FATAL")
        set_source(sim, config_source, dist_source_pl1, nthreads)

    # actors
    set_actors(sim, name_ofile)

    # run simulation
    sim.run()


if __name__ == "__main__":
    DEBUG: bool = False
    parser = ArgumentParser(description="Arguments")
    parser.add_argument("name_config_file", metavar="text", default="config.yaml")
    args = parser.parse_args()
    main(args.name_config_file, DEBUG)
