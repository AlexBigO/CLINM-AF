"""
file: test_geometry.py
brief:
usage: python3 test_geometry.py
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

# import sys
from os import system

import numpy as np

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
    import opengate_core as g4
except ModuleNotFoundError:
    print("Module 'opengate' is not installed. Please install it to run this script.")

from geometry import build_tank, build_rack, TRANSPARENT


# units
MM = gate.g4_units.mm
CM = gate.g4_units.cm
M = gate.g4_units.m
DEG = gate.g4_units.deg
MEV = gate.g4_units.MeV


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

# dimensions of a tank
WIDTH_TANK = 1 * MM
X_WIDTH_TANK = 12 * MM
Y_HEIGHT_TANK = 4 * CM
Z_WIDTH_TANK = 12 * MM


def update_source(source, z: int, energy_range: tuple):
    """
    Helper function to update source information
    """
    if z == 1:
        source.particle = "proton"
        source.energy.type = "range"
        source.energy.min_energy = energy_range[0]  # in MeV, not in MeV/u !
        source.energy.max_energy = energy_range[1]  # in MeV, not in MeV/u !
    else:
        source.particle = "ion"
        source.ion.Z = z
        source.ion.A = 2 * z
        source.ion.Q = z
        source.ion.E = 0
        source.energy.type = "range"
        source.energy.min_energy = (
            energy_range[0] * source.ion.A
        )  # in MeV, not in MeV/u !
        source.energy.max_energy = (
            energy_range[1] * source.ion.A
        )  # in MeV, not in MeV/u !


def set_actors(sim: gate.Simulation, name_pos: str, name_vol: str, name_ofile: str):
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
        "ParentID"
    ]

    digi_adder_policy: str = "EnergyWeightedCentroidPosition"

    # first, define HitsCollectionActors
    hits = sim.add_actor("DigitizerHitsCollectionActor", name=f"Hits{name_pos}")
    hits.attached_to = name_vol
    hits.output_filename = name_ofile
    hits.attributes = digi_attributes

    # then, define Adder to get the total energy deposited inside a detector during an event
    hits_adder = sim.add_actor("DigitizerAdderActor", name=f"HitsAdder{name_pos}")
    hits_adder.input_digi_collection = hits.name
    hits_adder.group_volume = name_vol
    hits_adder.output_filename = name_ofile
    hits_adder.policy = digi_adder_policy


def main_nominal(debug: bool) -> None:
    """
    Main function for nominal experiment
    (12C beam on RW3 target + tanks)

    Parameters
    ------------------------------------------------
    - debug: bool
        Switch for debugging
    """
    if debug:
        print("DEBUG mode enabled!")

    vis = g4.G4VisAttributes()
    vis.SetColor(*BLUE)
    vis.SetVisibility(1)

    dir_output: str = "Visual"
    dist_source_target: float = 30 * CM
    energy_beam = 398.8 * MEV  # in MeV/u
    n_source: int = 10  # int(1.e+1)

    # create simulation object
    sim: gate.Simulation = gate.Simulation()

    # import materials definitions
    sim.volume_manager.add_material_database("../../MaterialsCLINM.db")

    # ui
    # sim.verbose_level = gate.logger.RUN  # DEBUG
    # sim.running_verbose_level = gate.logger.RUN
    sim.g4_verbose = False
    sim.g4_verbose_level = 0  # 1
    sim.visu = True
    sim.visu_type = "qt"  # vrml
    sim.random_engine = "MersenneTwister"
    sim.random_seed = "auto"
    sim.output_dir = dir_output

    ui = sim.user_info
    ui.number_of_threads = 1

    # volumes
    world = sim.world
    world.material = "G4_Galactic"
    world.color = TRANSPARENT
    # target
    target = sim.add_volume("Box", name="Target")
    target.mother = NAME_WORLD
    target.size = [6 * CM, 6 * CM, 23 * CM]
    target.translation = [0, 0, -0.5 * target.size[IDZ]]
    target.material = "RW3"
    target.color = [1, 1, 1, 0.2]
    # target.style = "solid"
    # target.g4_vis_attributes(vis)

    # sphere = gate.geometry.volumes.SphereVolume(name="sph")
    # sphere.rmax = 100.0              # mm
    # sphere.material = "G4_AIR"        # material is irrelevant for the Boolean geometry
    # sphere.translation = target.translation.copy()

    # final_vol = gate.geometry.volumes.subtract_volumes(target, sphere)

    # sim.add_volume(final_vol)

    pos_base_rack = [0, -5.5 * MM, 30 * CM]
    water_inside_tanks = build_rack(sim, pos_base_rack)

    # actors
    name_ofile: str = "test.root"
    for key, vol in water_inside_tanks.items():
        set_actors(sim, key, vol.name, name_ofile)

    # source
    source = sim.add_source("GenericSource", name="Source")
    source.particle = "ion"
    z: int = 6
    source.ion.Z = z
    source.ion.A = 2 * z
    source.ion.Q = z
    source.ion.E = 0
    source.energy.mono = (energy_beam) * source.ion.A  # in MeV, not in MeV/u !
    source.position.type = "point"
    source.position.center = [0, 0, 0]
    source.position.translation = [0, 0, -(dist_source_target)] # + target.size[IDZ])]
    source.direction.type = "momentum"
    source.direction.momentum = [0, 0, 1]
    source.n = int(n_source / ui.number_of_threads)

    # physics list
    sim.physics_manager.physics_list_name = "QGSP_INCLXX_HP"

    sim.g4_commands_after_init.append("/vis/geometry/set/forceSolid all")
    # run simulation
    sim.run()



if __name__ == "__main__":
    DEBUG: bool = True
    main_nominal(DEBUG)
