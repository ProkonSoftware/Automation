# ---
# Example:  Rectangular slab - your first panel
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - this is the desktop program's OWN Default Example; all four ast values and all four moments reproduce the ENVELOPE MAXIMUM row of its calcsheet, saved in Slab.exe 5.3.3.0
# ---
# Analyse a whole slab PANEL from Python. You give it the geometry, how the
# four edges are held, and the loads; it meshes the panel, solves it, and
# hands back the moments it found and the steel they need.
#
# You do NOT give it moments. That is the difference between this engine and
# a section designer: it works out the moments itself, everywhere on the
# panel, and reports the worst of them.
#
# The panel below is the one that opens when you start the desktop program:
# its Default Example, transcribed input for input. Every number this script
# prints can be checked against that program's calcsheet.

import prokon.v5

result = prokon.v5.rectangular_slab.analyse(
    design_code="BS8110 - 1997",   # spelled exactly as the desktop names it
    lx=13.81,                      # panel size in x [m]
    ly=8.21,                       # panel size in y [m]
    h=250.0,                       # overall slab thickness [mm]

    # The EFFECTIVE depths: from the compression face down to the centre of
    # each direction's bars. They differ because the two layers cannot occupy
    # the same place - one mat sits on top of the other.
    dx=200.0,
    dy=220.0,

    fcu=25.0,                      # concrete strength [MPa]
    fy=450.0,                      # reinforcement yield strength [MPa]

    # How each edge is held. Three of these are "encastre" - held against both
    # vertical movement and rotation, which is what a panel continuous with
    # the slab around it looks like. The left edge is held against vertical
    # movement ONLY, so it can rotate: a simple support, a wall it merely sits
    # on. That asymmetry is why the answers below are not symmetric either.
    edge_top="FixedAgainstVerticalDisplacementAndRotation",
    edge_right="FixedAgainstVerticalDisplacementAndRotation",
    edge_bottom="FixedAgainstVerticalDisplacementAndRotation",
    edge_left="FixedAgainstVerticalDisplacement",

    # THE LOAD TABLE, and the one thing worth reading twice: each element is
    # one ROW, not one load case. A row that omits "number" CONTINUES the case
    # above it - which is how a single load case carries two different load
    # factors, as case 1 does here (1.4 and 1.6).
    #
    # Every row may carry a UDL over the whole panel, a point load "p" at
    # (x, y), and a line load "l" from (x1, y1) to (x2, y2) - all at once.
    load_cases=[
        {"number": 1, "lf": 1.4, "udl": 2.0,
         "p": 4.0, "x": 4.19, "y": 6.45,
         "l": 4.1, "x1": 2.44, "y1": 4.05, "x2": 10.03, "y2": 6.65},
        {"lf": 1.6, "udl": 2.0,
         "p": 4.0, "x": 10.06, "y": 2.99,
         "l": 2.0, "x1": 2.59, "y1": 2.62, "x2": 9.99, "y2": 4.61},
        {"number": 2, "lf": 1.4, "udl": 1.0,
         "p": 12.0, "x": 3.28, "y": 6.6},
    ],

    # Which cases the moment envelope covers, in the desktop's own notation.
    # Omit it and only case 1 is enveloped, which would quietly ignore case 2.
    envelope="1,2",

    # The engine adds the slab's own weight to every case; these are the
    # figures it uses. Shown because they are defaults you can change, not
    # because you must supply them.
    density=24.0,          # kN/m3
    self_weight_lf=1.4,    # load factor on the self weight
    poisson=0.2,
    creep_factor=2.0,      # long-term deflection only
)["result"]

# Four faces, because a slab spans two ways and can hog or sag in each.
# x_top and y_top are the HOGGING faces - steel in the top, over the supports;
# x_bot and y_bot the SAGGING ones - steel in the bottom, at midspan. Keeping
# them separate means a crossed direction is visible rather than plausible.
print("Required tension steel [mm2/m]")
for face in ("x_top", "x_bot", "y_top", "y_bot"):
    print(f"  {face:>6} = {result['ast'][face]:8.1f}")
# desktop calcsheet: 689 | 349 | 1106 | 566

print("\nDesign moments [kNm/m]")
for face in ("x_top", "x_bot", "y_top", "y_bot"):
    print(f"  {face:>6} = {result['moment_max'][face]:8.2f}")
# desktop calcsheet: 50.6 | 25.9 | 86.8 | 46.3

# The panel's worst downward movement, short and long term. The long-term
# figure includes creep, which is why it is the larger of the two and the one
# a span/250 check is made against.
limit = 8210.0 / 250.0
print(f"\nDeflection   short term {result['deflection']['short_term_max']:6.2f} mm"
      f"   long term {result['deflection']['long_term_max']:6.2f} mm")
print(f"             against span/250 = {limit:.1f} mm  ->  "
      f"{'OK' if result['deflection']['long_term_max'] <= limit else 'TOO FLEXIBLE'}")

# ---------------------------------------------------------------------
# WHERE THOSE EIGHT NUMBERS CAME FROM
#
# The engine solves the panel on a mesh and reports what it found at every
# node. The values above are the ENVELOPE over that mesh - the worst anywhere
# on the panel - so they are a summary of the table, not a separate answer.
print(f"\nMesh: {result['mesh']['nodes']} nodes, "
      f"{result['mesh']['load_cases']} load case(s)")

worst = max(node["ast"]["y_top"] for node in result["nodes"])
print(f"  worst y_top over all nodes = {worst:8.1f} mm2/m"
      f"   (summary says {result['ast']['y_top']:8.1f})")

# The node table is where you go when "how much steel" is not enough and you
# need to know WHERE it is needed.
peak = max(result["nodes"], key=lambda node: node["ast"]["y_top"])
print(f"  and it is at x = {peak['x']:.3f} m, y = {peak['y']:.3f} m"
      f"  - the middle of the top edge")

# Every node is a plain dictionary, so the whole table goes straight into
# pandas if you want to contour it, or into a CSV:
#
#     import pandas
#     frame = pandas.DataFrame([
#         {"x": n["x"], "y": n["y"], **n["ast"]} for n in result["nodes"]
#     ])
