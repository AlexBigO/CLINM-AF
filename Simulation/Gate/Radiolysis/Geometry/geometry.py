"""
file: geometry.py
brief: Module
note:
author: Alexandre BIGOT, alexandre.bigot@iphc.cnrs.fr
"""

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

# small distance (useful when subtracting volumes)
EPS = 0.001 * MM

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
WHITE = [1, 1, 1, 1]
TRANSPARENT = [1, 1, 1, 0]
C_TANK = [1, 1, 1, 0.3]
C_WATER = [0, 0.7, 1, 1] # [0.05, 0.53, 0.8, 1]
C_RACK = [0.5, 0.5, 0.5, 1]

# dimensions of a tank
WIDTH_TANK = 1 * MM
X_WIDTH_TANK = 12 * MM
Y_HEIGHT_TANK = 4 * CM
Z_WIDTH_TANK = 12 * MM
Y_HEIGHT_WATER = 15 * MM

# space between separator and tank
D_SEP_TANK = 0.5 * MM / 2.

N_TANKS_IN_ONE_COL = 6

MATERIAL_RACK = "G4_Galactic"

# # method 1: with daughter volumes
# def build_tank(sim: gate.Simulation, id: str):
#     """
#     Helper function to build a tank
#     """

#     tank = sim.add_volume("Box", name=f"Cuve{id}")
#     tank.mother = NAME_WORLD
#     tank.size = [X_WIDTH_TANK, Y_HEIGHT_TANK, Z_WIDTH_TANK]
#     tank.translation = [20 * CM, 20 * CM, 20 * CM]
#     tank.material = "PMMARadiolysis"
#     tank.color = C_TANK

#     water_inside_tank = sim.add_volume("Box", name=f"WaterInsideCuve{id}")
#     water_inside_tank.mother = f"Cuve{id}"
#     water_inside_tank.material = "G4_WATER"
#     water_inside_tank.size[IDX] = tank.size[IDX] - 2 * WIDTH_TANK
#     water_inside_tank.size[IDZ] = tank.size[IDZ] - 2 * WIDTH_TANK
#     water_inside_tank.size[IDY] = Y_HEIGHT_WATER # tank.size[IDY] - WIDTH_TANK
#     water_inside_tank.translation[IDY] = WIDTH_TANK - 0.5 * Y_HEIGHT_TANK + 0.5 * Y_HEIGHT_WATER
#     water_inside_tank.color = C_WATER

#     void_inside_tank = sim.add_volume("Box", name=f"VoidInsideCuve{id}")
#     void_inside_tank.mother = f"Cuve{id}"
#     void_inside_tank.material = "G4_Galactic"
#     void_inside_tank.size[IDX] = tank.size[IDX] - 2 * WIDTH_TANK
#     void_inside_tank.size[IDZ] = tank.size[IDZ] - 2 * WIDTH_TANK
#     void_inside_tank.size[IDY] = Y_HEIGHT_TANK - Y_HEIGHT_WATER - WIDTH_TANK
#     void_inside_tank.translation[IDY] = 0.5 * WIDTH_TANK + 0.5 * Y_HEIGHT_TANK - 0.5 * (Y_HEIGHT_TANK - Y_HEIGHT_WATER)
#     void_inside_tank.color = TRANSPARENT

#     return tank, water_inside_tank

def __get_tank_tmpl():
    """
    Helper function to get a template of a tank
    """
    tank = gate.geometry.volumes.BoxVolume(name="CuveTmpl_000")
    tank.mother = NAME_WORLD
    tank.size = [X_WIDTH_TANK, Y_HEIGHT_TANK, Z_WIDTH_TANK]
    tank.translation = [20 * CM, 20 * CM, 20 * CM]

    return tank

# method 2: subtract volumes
def build_tank(sim: gate.Simulation, id: str):
    """
    Helper function to build a tank
    """
    tank_tmpl = gate.geometry.volumes.BoxVolume(name=f"CuveTemplate{id}")
    tank_tmpl.mother = NAME_WORLD
    tank_tmpl.size = [X_WIDTH_TANK, Y_HEIGHT_TANK, Z_WIDTH_TANK]
    tank_tmpl.translation = [20 * CM, 20 * CM, 20 * CM]
    tank_tmpl.material = "PMMARadiolysis"
    tank_tmpl.color = RED #C_TANK

    # void_inside_tank = sim.add_volume("Box", name=f"VoidInsideCuve{id}")
    void_inside_tank = gate.geometry.volumes.BoxVolume(name=f"VoidInsideCuve{id}")
    # void_inside_tank.mother = f"Cuve{id}"
    void_inside_tank.material = "G4_Galactic"
    # translation_void = tank.translation.copy()
    translation_void = [0, 0, 0]
    void_inside_tank.size[IDX] = tank_tmpl.size[IDX] - 2 * WIDTH_TANK
    void_inside_tank.size[IDZ] = tank_tmpl.size[IDZ] - 2 * WIDTH_TANK
    void_inside_tank.size[IDY] = Y_HEIGHT_TANK - WIDTH_TANK
    translation_void[IDY] += WIDTH_TANK / 2.

    tank = gate.geometry.volumes.subtract_volumes(
        tank_tmpl,
        void_inside_tank,
        translation=translation_void)
    tank.name = f"CuveTemplate{id}"
    tank.material = "PMMARadiolysis"
    tank.color = C_TANK

    return tank


def put_water_in_tank(sim, tank, id):
    """
    Helper method to put water in tank
    """
    water_inside_tank = sim.add_volume("Box", name=f"WaterInsideCuve{id}")
    water_inside_tank.mother = NAME_WORLD
    water_inside_tank.material = "G4_WATER"
    water_inside_tank.size[IDX] = X_WIDTH_TANK - 2 * WIDTH_TANK
    water_inside_tank.size[IDZ] = Z_WIDTH_TANK - 2 * WIDTH_TANK
    water_inside_tank.size[IDY] = Y_HEIGHT_WATER # tank.size[IDY] - WIDTH_TANK
    translation_water = tank.translation.copy()
    translation_water[IDY] += (WIDTH_TANK - 0.5 * Y_HEIGHT_TANK + 0.5 * Y_HEIGHT_WATER)
    water_inside_tank.translation = translation_water
    water_inside_tank.color = C_WATER


def build_base(sim: gate.Simulation):
    """
    Helper function to build the base of the rack
    """
    base = sim.add_volume("Box", name=f"RackBase")
    base.mother = NAME_WORLD
    base.material = MATERIAL_RACK
    # FIXME find actual value of height (along Y axis)
    base.size = [110 * MM, 6 * MM, 130 * MM]
    base.translation = [0,0,0]
    base.color = C_RACK

    return base


def place_on_top_of_base(base, obj):
    """
    Helper function to place an object on top of the base
    """
    translation = base.translation.copy()
    translation[IDY] += (base.size[IDY] + obj.size[IDY]) / 2.

    return translation

def get_top_of_base_pos(pos_base, size_base, size_obj):
    """
    Helper function to place an object on top of the base
    """
    translation = pos_base.copy()
    translation[IDY] += (size_base[IDY] + size_obj[IDY]) / 2.

    return translation

# def get_base_edge_pos(base, obj, id: str=""):
#     """
#     Helper function to translate an object to the left edge of the base
#     """
#     translation = get_top_of_base_pos(base.translation, base.size, obj.size)
#     translate_to_edge = (base.size[IDX] - obj.size[IDX]) / 2.
#     if "Left" in obj.name or id == "Left":
#         translation[IDX] += translate_to_edge
#     else:
#         translation[IDX] -= translate_to_edge
#     return translation

def get_base_edge_pos(pos_base, size_base, size_obj, id: str=""):
    """
    Helper function to translate an object to the left edge of the base
    """
    translation = get_top_of_base_pos(pos_base, size_base, size_obj)
    translate_to_edge = (size_base[IDX] - size_obj[IDX]) / 2.
    if id == "Left":
        translation[IDX] += translate_to_edge
    else:
        translation[IDX] -= translate_to_edge
    return translation

# def get_a1(base, obj):
#     """
#     Helper function to move object to A1
#     """
#     # a1 = get_base_edge_pos(base, obj, "Left")
#     a1 = get_base_edge_pos(pos_base, size_base, size_obj, "Left")
#     a1[IDX] -= (10 * MM + D_SEP_TANK)
#     a1[IDZ] -= (base.size[IDZ] - obj.size[IDZ]) / 2.
#     a1[IDZ] += 2 * MM

#     return a1

def get_a1(pos_base, size_base, size_obj):
    """
    Helper function to move object to A1
    """
    a1 = get_base_edge_pos(pos_base, size_base, size_obj, "Left")
    a1[IDX] -= (10 * MM + D_SEP_TANK)
    a1[IDZ] -= (size_base[IDZ] - size_obj[IDZ]) / 2.
    a1[IDZ] += 2 * MM

    return a1

# # method 1: with daughter void volume
# def build_border(sim: gate.Simulation, id: str):
#     """
#     Helper function to build a vertical border
#     """
#     border = sim.add_volume("Box", name=f"RackVerticalBorder{id}")
#     border.mother = NAME_WORLD
#     border.material = MATERIAL_RACK
#     # do not care about the little "hole" in the middle top as beam does not pass here
#     border.size = [5 * MM, 56 * MM, 130 * MM]
#     border.color = C_RACK

#     # add the little "hole" at the middle top
#     void_box = sim.add_volume("Box", name=f"RackVerticalBorder{id}VoidBox")
#     void_box.mother = border.name
#     void_box.color = [0,0,0,1] # [*C_RACK[:3], 0.2]
#     void_box.size = [5 * MM, 5* MM, 15 * MM]
#     translation_void_box = void_box.translation.copy()
#     translation_void_box[IDY] += (border.size[IDY] - void_box.size[IDY]) / 2.
#     void_box.translation = translation_void_box

#     return border

# method 2: with subtracted volume
def build_border(sim: gate.Simulation, id: str):
    """
    Helper function to build a vertical border
    """
    # border template
    border_tmpl = gate.geometry.volumes.BoxVolume(name=f"RackVerticalBorderTemplate{id}")
    border_tmpl.mother = NAME_WORLD
    border_tmpl.size = [5 * MM, 56 * MM, 130 * MM]

    # add the little "hole" at the middle top
    void_box = gate.geometry.volumes.BoxVolume(name=f"RackVerticalBorder{id}VoidBox")
    void_box.mother = NAME_WORLD
    # FIXME here I need to add EPS
    void_box.size = [5 * MM + EPS, 5* MM, 15 * MM]
    translation_void_box = [0, 0, 0]
    translation_void_box[IDY] += (border_tmpl.size[IDY] - void_box.size[IDY]) / 2.
    void_box.translation = translation_void_box

    # border_with_hole
    border_with_hole = gate.geometry.volumes.subtract_volumes(
        border_tmpl,
        void_box,
        translation=translation_void_box)
    border_with_hole.name = f"RackVerticalBorder{id}"
    border_with_hole.material = MATERIAL_RACK
    border_with_hole.color = C_RACK

    return border_tmpl, border_with_hole


def place_border(base, border_tmpl, border) -> None:
    """
    Helper function to place border on base
    """

    pos = "Left"
    if "Right" in border.name:
        pos = "Right"

    translation = get_base_edge_pos(base.translation, base.size, border_tmpl.size, pos)

    if "Left" in border.name:
        translation[IDX] -= 5 * MM
    else:
        translation[IDX] += 5 * MM

    border.translation = translation


def build_separator(sim: gate.Simulation, id: int):
    """
    Helper function to build separator
    """
    separator = sim.add_volume("Box", name=f"RackSeparator{id}")
    separator.mother = NAME_WORLD
    separator.material = MATERIAL_RACK
    separator.size = [3 * MM, 12 * MM, 130 * MM]
    separator.color = C_RACK

    return separator

def place_separator(base, separator, id: int):
    """
    Helper function to place separator
    """
    translation = get_base_edge_pos(base.translation, base.size, separator.size, "Left")
    # put right next to the left border
    translation[IDX] -= 10 * MM 

    translation[IDX] -= ((X_WIDTH_TANK + 2 * D_SEP_TANK)* id + separator.size[IDX] * (id - 1))

    separator.translation = translation

# # method 1: with daughter void volume
# def build_rod(sim: gate.Simulation, id: str):
#     """
#     Helper function to build separator
#     """
#     rod = sim.add_volume("Box", name=f"RackRod{id}")
#     rod.mother = NAME_WORLD
#     rod.material = MATERIAL_RACK
#     rod.size = [90 * MM, 15 * MM, 2 * MM]
#     rod.color = C_RACK

#     nholes = 6

#     pos_left_hole = rod.translation.copy()
#     xpos_left_rod_edge = rod.size[IDX] / 2.
#     pos_left_hole[IDX] += xpos_left_rod_edge
#     pos_left_hole[IDX] -= (X_WIDTH_TANK + 2 * D_SEP_TANK) / 2.
#     pos_left_hole[IDY] -= 2.5 * MM
#     x_step = 3 * MM + X_WIDTH_TANK + 2 * D_SEP_TANK
#     for ihole in range(nholes):
#         hole = sim.add_volume("TubsVolume", name=f"RackRod{id}Hole{ihole}")
#         hole.mother = f"RackRod{id}"
#         hole.rmin = 0
#         hole.rmax = 1 * MM
#         hole.dz = 1 * MM
#         hole.material = "G4_Galactic"
#         hole.color = WHITE
#         translation_hole = pos_left_hole.copy()
#         translation_hole[IDX] -= x_step * ihole
#         # if ihole > 0:
#         #     translation_hole[IDX] -= 3 * MM
#         hole.translation = translation_hole

#     return rod

# method 2: with subtracted volumes
def build_rod(sim: gate.Simulation, id: str):
    """
    Helper function to build separator
    """
    rod_tmpl = gate.geometry.volumes.BoxVolume(name=f"RackRodTemplate{id}")
    rod_tmpl.mother = NAME_WORLD
    rod_tmpl.size = [90 * MM, 15 * MM, 2 * MM]

    nholes = 6

    pos_left_hole = rod_tmpl.translation.copy()
    xpos_left_rod_edge = rod_tmpl.size[IDX] / 2.
    pos_left_hole[IDX] += xpos_left_rod_edge
    pos_left_hole[IDX] -= (X_WIDTH_TANK + 2 * D_SEP_TANK) / 2.
    pos_left_hole[IDY] -= 2.5 * MM
    x_step = 3 * MM + X_WIDTH_TANK + 2 * D_SEP_TANK

    rod = rod_tmpl

    for ihole in range(nholes):
        hole = gate.geometry.volumes.TubsVolume(name=f"RackRod{id}Hole{ihole}")
        hole.mother = f"RackRod{id}"
        hole.rmin = 0
        hole.rmax = 1 * MM
        # FIXME here I need to add EPS
        hole.dz = 1 * MM + EPS
        hole.material = "G4_Galactic"
        hole.color = WHITE
        translation_hole = pos_left_hole.copy()
        translation_hole[IDX] -= x_step * ihole
        hole.translation = translation_hole

        rod = gate.geometry.volumes.subtract_volumes(
            rod,
            hole,
            translation=translation_hole)
        
    rod.material = MATERIAL_RACK
    rod.color = C_RACK
    rod.name = f"RackRod{id}"

    return rod_tmpl, rod

def place_rod(base, rod_tmpl, rod):
    """
    Helper function to place a rod
    """
    translation = get_top_of_base_pos(base.translation, base.size, rod_tmpl.size)
    translation[IDY] += 30 * MM
    if "Front" in rod.name:
        translation[IDZ] -= (base.size[IDZ] - rod_tmpl.size[IDZ]) / 2.
    else:
        translation[IDZ] += (base.size[IDZ] - rod_tmpl.size[IDZ]) / 2.
    rod.translation = translation


def get_rack_mapping(a1):
    """
    Helper method to generate a map in rack
    The positions will be defined as in chess: A1, A2, ...
    where A -> F are the column ids
    and 1 - > ? are the line ids
    A1 is at the bottom left (view from above)
    """

    mapping = {}

    id_cols = ["A", "B", "C", "D", "E", "F"]
    id_rows = list(range(1, N_TANKS_IN_ONE_COL + 1))

    x_step = 3 * MM + X_WIDTH_TANK + 2 * D_SEP_TANK
    z_step = Z_WIDTH_TANK

    for icol, id_col in enumerate(id_cols):
        for irow, id_row in enumerate(id_rows):
            mapping[f"{id_col}{id_row}"] = a1 + [-icol * x_step, 0,  irow * z_step]

    return mapping


def build_rack(sim: gate.Simulation, pos_base_rack):
    """
    Helper function to build the rack
    """
    base = build_base(sim)
    base.translation = pos_base_rack
    
    a1 = get_a1(base.translation, base.size, [X_WIDTH_TANK, Y_HEIGHT_TANK, Z_WIDTH_TANK])

    tanks = {}
    water_inside_tanks = {}
    mapping = get_rack_mapping(a1)
    for key, pos in mapping.items():
        tanks[key] = build_tank(sim, key)
        tanks[key].translation = pos
        put_water_in_tank(sim, tanks[key], key)
        sim.add_volume(tanks[key])

    # borders
    border_left_tmpl, border_left = build_border(sim, id="Left")
    border_right_tmpl, border_right = build_border(sim, id="Right")
    place_border(base, border_left_tmpl, border_left)
    place_border(base, border_right_tmpl, border_right)
    # add the border volumes to the simulation
    sim.add_volume(border_left)
    sim.add_volume(border_right)

    # separators
    separators = []
    for id in range(1, 6):
        separators.append(build_separator(sim, id))
        place_separator(base, separators[-1], id)

    # rods
    rod_front_tmpl, rod_front = build_rod(sim, "Front")
    rod_back_tmpl, rod_back = build_rod(sim, "Back")
    place_rod(base, rod_front_tmpl, rod_front)
    place_rod(base, rod_back_tmpl, rod_back)

    sim.add_volume(rod_front)
    sim.add_volume(rod_back)

    return water_inside_tanks
