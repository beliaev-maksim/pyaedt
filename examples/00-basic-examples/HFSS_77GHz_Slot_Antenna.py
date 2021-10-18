"""
Slot antenna example
------------------------
This example shows how to create a parametric slot antenna and
create the setup.
"""

import os
from pyaedt import Hfss
import tempfile
from pyaedt.generic.general_methods import generate_unique_name
from copy import copy
###############################################################################
# Launch AEDT and define some path and file name information.
# ~~~~~~~~~~~~~~~~~~~~~~~
# This examples runs in 2021.2 student version.

tmpfold = tempfile.gettempdir()
design_name = "slot_ant"
proj_name = os.path.join(tmpfold, generate_unique_name("slot") + ".aedt")

###############################################################################
# Launch HFSS
# ~~~~~~~~~~~~~~~~~~~~~~~
# The :class:`pyaedt.Hfss` class initializes AEDT and inserts an HFSS project.

hfss = Hfss(projectname=proj_name,
            designname=design_name,
            student_version=True)
###############################################################################
# Define parameters
# ~~~~~~~~~~~~~~~
# Units are set to "um".
# Other parameters will be added to the HFSS design using the dictionary
# ``params``

units = "um"
hfss.modeler.model_units = units
params = {"slot_length": 980, "slot_width": 100, "feed_length": 600,
          "x_size": 2000, "y_size": 2000, "t_oxide": 10, "w_trace": 10,
          "feed_offset": 0, "feed_extend": 200, "t_metal": 2,
          "via_offset": 20}

###############################################################################
# Define via radius
# ~~~~~~~~~~~~~~~~~~~~~~
# The via radius will be fixed and is not a parameter in the HFSS
# design.
via_radius = "4um"  # This is not parameterized in HFSS.

###############################################################################
# Pass parameters to HFSS
# ~~~~~~~~~~~~~~~~~~~~~~
# Parameter values and names are assigned in the HFSS
# design.

for k, v in params.items():
    hfss[k] = str(v) + units
###############################################################################
# Draw the layers.
# ~~~~~~~~~~~~~~~

stackup_origin = ["-x_size/2", "-y_size/2", "0"]
plane_xy_size = ["x_size", "y_size"]
layer_definitions = [{"thickness": "t_metal", "material": "copper", "name": "bottom"},
                     {"thickness": "t_oxide", "material": "si02", "name": "oxide"},
                     {"thickness": "t_metal", "material": "copper", "name": "top"}]
layers = []
o = stackup_origin
for n, l in enumerate(layer_definitions):
    o[2] += "+" + l["thickness"]  # Update height in z-dimension for box origin.
    box_size = copy(plane_xy_size)
    box_size.append(l["thickness"])  # Append thickness to xy size of layer box.
    layers.append(hfss.modeler.primitives.create_box(o, box_size,
                                                     name=l["name"],
                                                     matname=l["material"])
    )

bottom_plane = hfss.modeler.primitives.create_rectangle(0, plane_origin,
                                                        plane_xy,
                                                        name="bottom_plane",
                                                        matname="copper")
bottom_plane.color = "Orange"
bottom_plane.transparency = 0.35
bottom_plane.thicken_sheet("-t_metal")

top_plane = bottom_plane.duplicate_along_line([0, 0, "t_oxide + t_metal"], name="top_plane")[0]

slot = hfss.modeler.primitives.create_box(["-slot_length/2", "-slot_width/2", "t_oxide/2"],
                                          ["slot_length", "slot_width", "t_metal"],
                                          name="slot")
top_plane = top_plane - slot  # Boolean subtract
top_plane.transparency = 0.8

###############################################################################
# Place 4 vias around the slot connecting top and bottom layers.
# ~~~~~~~~~~~~~~~
via_base_position = ["slot_length/2 + via_offset", "slot_width/2 + via_offset", "-t_oxide/2"]
via1 = hfss.modeler.primitives.create_cylinder(cs_axis="Z",
                                              position=via_base_position,
                                              radius=via_radius, height="t_oxide",
                                              name="via1", matname="copper")
via1.color = "Orange"
via2 = via1.duplicate_and_mirror([0, 0, 0], [1, 0, 0], name="via2")
via3 = via2.duplicate_and_mirror([0, 0, 0], [0, 1, 0], name="via3")
via4 = via1.duplicate_and_mirror([0, 0, 0], [0, 1, 0], name="via4")
###############################################################################
# Draw the feed and unite it with the via.
# ~~~~~~~~~~~~~~~
feed_start_pos = ["feed_offset", "-feed_length", 0]
feed_end_pos = ["feed_offset", "slot_width/2 + feed_extend + 8um", 0]
trace = hfss.modeler.primitives.create_polyline([feed_start_pos, feed_end_pos],
                                                name="trace",
                                                matname="copper",
                                                xsection_type='Rectangle',
                                                xsection_width="w_trace",
                                                xsection_height="t_metal")
feed_short_pos = ["feed_offset", "slot_width/2 + feed_extend", "-t_oxide/2"]
feed_short = hfss.modeler.primitives.create_cylinder(cs_axis="Z",
                                                     position=feed_short_pos,
                                                     radius=via_radius,
                                                     height="t_oxide",
                                                     name="feed_short",
                                                     matname="copper")
trace = trace + feed_short  # Boolean unite
trace.color = "Orange"

###############################################################################
# Draw a wave port.
# ~~~~~~~~~~~~~~~
#
port_rectangle_base = ["feed_offset-w_trace-3*t_oxide", "-feed_length", "-t_oxide/2"]
port_rectangle_size = ["t_oxide", "w_trace + 6*t_oxide"]
port_pec = ["w_trace + 6*t_oxide", "-0.5um", "t_oxide"]

port_face = hfss.modeler.primitives.create_rectangle(2, port_rectangle_base, port_rectangle_size)
port_block = hfss.modeler.primitives.create_box(port_rectangle_base,
                                                port_pec,
                                                name="port_pec",
                                                matname="pec")
port_face.name = "ant_port"
hfss.create_wave_port_from_sheet(port_face, axisdir=hfss.AxisDir.YNeg)
###############################################################################
# Define the automated interpolating sweep.
# ~~~~~~~~~~~~~~~
#
# setup = hfss.create_setup(setupname="AdaptMesh",
#                           setuptype=0)
# setup.props["Sweeps"]["Sweep"]["RangeStart"] = "74GHz"
# setup.props["Sweeps"]["Sweep"]["RangeEnd"] = "80GHz"
# setup.props["Sweeps"]["Sweep"]["RangeStep"] = "0.05GHz"
# setup.props["SaveAnyFields"] = False
# setup.props["Type"] = "Interpolating"
#

###############################################################################
# Define the setup and sweep along with a discrete sweep to
# calculate the field at the center frequency. The discrete sweep
# is deactivated to allow for optimization of feed before
# calculating far-field.
# ~~~~~~~~~~~~~~~
#
setup = hfss.create_setup(setupname="AdaptMesh")
setup.props["Frequency"] = "77GHz"
setup.add_sweep(sweepname="InterpSweep", sweeptype="Interpolating")
setup.add_sweep(sweepname="Discrete", sweeptype="Discrete")

setup.sweeps[0].props["RangeStart"] = "74GHz"
setup.sweeps[0].props["RangeEnd"] = "80GHz"
setup.sweeps[0].props["RangeCount"] = 201
setup.sweeps[0].props["SaveFields"] = False
setup.sweeps[0].props["SaveRadFields"] = False
setup.sweeps[0].update()
setup.sweeps[1].props["RangeStart"] = "77GHz"
setup.sweeps[1].props["RangeCount"] = 1
setup.sweeps[1].props["RangeEnd"] = "77GHz"
setup.sweeps[1].props["IsEnabled"] = False
setup.sweeps[1].update()

hfss.create_open_region(Frequency="77GHz", Boundary="Radiation", ApplyInfiniteGP=True)

###############################################################################
# Create the infinite sphere
# ---------------------------
# A setup with a sweep will be used to run the simulation.
###############################################################################
# Save and Run the Simulation
# ---------------------------
# A setup with a sweep will be used to run the simulation.

hfss.save_project()
hfss.analyze_setup("AdaptMesh")

