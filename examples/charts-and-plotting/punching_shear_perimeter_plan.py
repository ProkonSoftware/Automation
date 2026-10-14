# ---
# Example:  The column head, drawn to scale - five perimeters and three levers
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes - 2026-09-04 - the pinned 400 sq head reproduces its uo and perimeter-1 Asv; every head measured on prokon-automation.exe, and every drawn perimeter checked against the engine's own ucrit
# ---
# Punching shear is the one check that is genuinely easier to see than to
# read. It happens on five concentric perimeters at 0.75d spacing, each
# one carrying a different force against a different capacity, and a table
# of five rows does not tell you where on the floor the links go.
#
# So this script draws the head. The perimeters are drawn TO SCALE from
# the engine's own radial_distance, each one shaded by how hard it is
# working, and the rings that need reinforcement are marked.
#
# ⚠ AND THE DRAWING IS CHECKED, NOT ASSUMED. Before anything is plotted,
# the script tests the rectangle it is about to draw against the engine's
# own ucrit for every perimeter. If the engine used a different shape -
# rounded corners, say - the drawing would be a lie and the check says so.
#
# The other three panels are the design decisions that follow:
#
#   THE MAP       total link steel over (column size, slab depth), with
#                 the FACE-CHECK ceiling drawn on it. That ceiling is the
#                 one boundary with no reinforcement remedy.
#   THE RINGS     link steel required, perimeter by perimeter - which is
#                 NOT a decreasing sequence, and the script says by how
#                 much it rises again.
#   THE REMEDIES  three levers on a failing head, driven side by side on
#                 the same slab - and only two of them touch the face
#                 check at all. Measured: adding flexural steel leaves
#                 vu/vcu at 1.631 across its whole range, unchanged to
#                 three decimals, while it cuts the link steel by half.
#                 The other two levers move it, which is the control that
#                 makes the first result mean something.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

import prokon.v5

# -- SAVE THE PNG, AND SHOW IT IN SPYDER --------------------------------
# Spyder runs matplotlib on its own backend - "inline" puts the figure in
# the Plots pane, "automatic" opens a window - so plt.show() displays the
# chart right where you are working. A headless run (a batch job, or this
# documentation's own sweep) runs the Agg backend, where show() can only
# warn. So ASK the backend, and write the PNG either way.
#
# There is deliberately NO matplotlib.use("Agg") here. That call forces
# the headless backend, and a script that forces it can never draw into
# Spyder's Plots pane - which is where you actually want to see it.
HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can."""
    path = Path(filename).resolve()
    figure.savefig(path, dpi=150, facecolor="white")
    size = path.stat().st_size
    print("\nWritten: {0}".format(path))
    print("  {0:,} bytes  ({1})".format(
        size, "a real image" if size > 20_000 else "SUSPICIOUSLY SMALL"))
    if str(matplotlib.get_backend()).lower() in HEADLESS:
        plt.close(figure)
        print("  backend is headless - the PNG is the whole output")
    else:
        plt.show()          # Spyder: straight into the Plots pane
        print("  and shown on the {0} backend".format(
            matplotlib.get_backend()))


# -- The head -----------------------------------------------------------
CODE = "BS8110 - 1997"
FCU = 35.0
FY = 500.0
FYV = 500.0
BAY = 7.5                 # m square bay
SLAB = 275.0              # mm overall
COVER = 35.0              # mm to the top bar centre
DEPTH = SLAB - COVER      # effective depth
COLUMN = 400.0            # mm square
LOAD = 22.0               # kPa ultimate
SHEAR = LOAD * BAY * BAY  # kN on the head
TRANSFER_X = 60.0         # kNm
TRANSFER_Y = 40.0         # kNm
INTERNAL = 15_000.0       # mm to the nearest edge - genuinely internal

COLUMNS = np.arange(250.0, 851.0, 75.0)        # 9 mm
DEPTHS = np.arange(140.0, 401.0, 25.0)         # 11 mm

# -- Two numbers that decide how long this script takes -----------------
# The map below is a Cartesian sweep, so its cost is the product of the
# two step sizes above, and every point is a separate engine process at
# about 0.3 s. Choose the steps for the chart you want to READ - halving
# a step doubles the wait, and this map is already finer than the eye
# resolves.
#
# Then bound the wait itself. timeout_seconds is PER CALL, it defaults to
# 120 s, and these calls take 0.3 s - so one stuck call could cost more
# than the whole sweep. Sized here at many times what a healthy call takes
# and still far below what this whole script costs: generous, and bounded.
prokon.v5.timeout_seconds = 30.0

print("THE COLUMN HEAD, DRAWN TO SCALE")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, fyv {FYV:.0f}")
print(f"  {BAY:.1f} m bay at {LOAD:.0f} kPa -> V = {SHEAR:.0f} kN, "
      f"Mx {TRANSFER_X:.0f}, My {TRANSFER_Y:.0f} kNm")
print(f"  reference head {COLUMN:.0f} mm square in a {SLAB:.0f} mm slab "
      f"(de {DEPTH:.0f} mm)")
print(f"  grid: {len(COLUMNS)} column sizes x {len(DEPTHS)} depths "
      f"= {len(COLUMNS) * len(DEPTHS)} engine calls")

# -- The anchor ---------------------------------------------------------
PINNED_UO = 1600
PINNED_ASV = 2519.6003848228493
envelope = prokon.v5.punching_shear.analyse(
    design_code=CODE, col_width=400.0, col_breadth=400.0,
    effective_depth=200.0, nearest_edge_x=10_000.0,
    nearest_edge_y=10_000.0, fcu=35.0, fy=500.0, fyv=500.0,
    load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}])
anchor = envelope["result"]
exact = (anchor["uo"] == PINNED_UO
         and anchor["critical_perimeters"][0]["asv"] == PINNED_ASV)
print("\n  anchor: the pinned 400 sq head, de 200, V = 800 kN")
print(f"    uo  {anchor['uo']!r}   pinned {PINNED_UO!r}")
print(f"    perimeter-1 Asv {anchor['critical_perimeters'][0]['asv']!r}")
print(f"    pinned          {PINNED_ASV!r}")
print(f"    -> {'EXACT on both' if exact else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def steel_across(width, depth, perimeter, ratio=1.0):
    """Top steel over the width the perimeter reaches, mm2."""
    reach = width + 2 * 1.5 * perimeter * depth
    return ratio * 1200.0 * min(reach, BAY * 1000.0) / 1000.0


# invalid_input and no_solution say something about the HEAD - this
# geometry has no answer - and belong on the map as a hole. Every other
# category says something about the RUN, and a map quietly missing those
# points would be a lie. So they are counted by category and printed.
NO_ANSWER_HERE = ("invalid_input", "no_solution")
not_answered = []


def head(col_width=COLUMN, col_breadth=None, depth=DEPTH, shear=SHEAR,
         edge_x=INTERNAL, edge_y=INTERNAL, ratio=1.0):
    """One column head. Returns the whole result, or None if refused."""
    if col_breadth is None:
        col_breadth = col_width
    try:
        return prokon.v5.punching_shear.analyse(
            design_code=CODE, col_width=col_width, col_breadth=col_breadth,
            effective_depth=depth, nearest_edge_x=edge_x,
            nearest_edge_y=edge_y, fcu=FCU, fy=FY, fyv=FYV,
            asx_1=steel_across(col_width, depth, 1, ratio),
            asx_2=steel_across(col_width, depth, 2, ratio),
            asx_3=steel_across(col_width, depth, 3, ratio),
            asx_4=steel_across(col_width, depth, 4, ratio),
            asy_1=steel_across(col_breadth, depth, 1, ratio * 0.9),
            asy_2=steel_across(col_breadth, depth, 2, ratio * 0.9),
            asy_3=steel_across(col_breadth, depth, 3, ratio * 0.9),
            asy_4=steel_across(col_breadth, depth, 4, ratio * 0.9),
            load_cases=[{"v": shear, "mx": TRANSFER_X, "my": TRANSFER_Y}])["result"]
    except prokon.v5.ProkonError as refusal:
        if refusal.category not in NO_ANSWER_HERE:
            not_answered.append("{0}/{1}".format(refusal.category,
                                                 refusal.code))
        return None


def face(result):
    """(applied face stress, the code's ceiling, does it pass)."""
    stress = result["vu"][result["critical_load_case_index"]]
    return stress, result["vcu"], stress <= result["vcu"]


reference = head()
# Nothing below can be drawn without it, so say so plainly rather than
# reaching into a None and blaming the script for the engine's answer.
if reference is None:
    raise SystemExit(
        "the reference head was not answered, so there is no plan to draw"
        + (": " + ", ".join(sorted(set(not_answered))) if not_answered
           else " - the engine refused this geometry"))
face_stress, ceiling, face_ok = face(reference)
print(f"\nTHE REFERENCE HEAD")
print(f"   column face   uo = {reference['uo']:.0f} mm, "
      f"vu = {face_stress:.4f} MPa against vcu = {ceiling:.4f} MPa"
      f"  ->  {'OK' if face_ok else 'OVERSTRESSED - no remedy in links'}")
print(f"   {'ring':>5} {'r (mm)':>8} {'ucrit':>8} {'Veff (kN)':>10} "
      f"{'Vcap (kN)':>10} {'Asv (mm2)':>10}")
for ring in reference["critical_perimeters"]:
    print(f"   {ring['perimeter']:>5} {ring['radial_distance']:>8.0f} "
          f"{ring['ucrit']:>8.0f} {ring['veff']:>10.1f} "
          f"{ring['vcap']:>10.1f} {ring['asv']:>10.1f}")

# -- Is the perimeter really a rectangle? --------------------------------
# CLAIM: each critical perimeter is the rectangle offset r from the column
# face, so ucrit = 2((w + 2r) + (b + 2r)). The drawing depends on it.
# CONTROL: a rounded-corner perimeter of the same offset has a DIFFERENT
# length, and it is computed here too - so the test can fail. If both
# formulas gave the same number the check would prove nothing.
print("\nIS THE PERIMETER A RECTANGLE? (the drawing depends on the answer)")
print(f"   {'ring':>5} {'engine ucrit':>13} {'rectangle':>11} "
      f"{'rounded corners':>16}")
rectangular = True
for ring in reference["critical_perimeters"]:
    radius = ring["radial_distance"]
    boxed = 2.0 * ((COLUMN + 2 * radius) + (COLUMN + 2 * radius))
    rounded = boxed - 8.0 * radius + 2.0 * np.pi * radius
    if abs(boxed - ring["ucrit"]) > 1e-6:
        rectangular = False
    print(f"   {ring['perimeter']:>5} {ring['ucrit']:>13.1f} "
          f"{boxed:>11.1f} {rounded:>16.1f}")
print(f"   -> {'RECTANGULAR on every ring, so the plan below is the real'
              ' shape' if rectangular else 'NOT rectangular - the drawing '
              'below is only indicative'}")
print("      (the rounded-corner column is the control: it differs by "
      "hundreds")
print("      of mm, so a match with the rectangle is a real match)")

# -- The rings do not simply get easier ---------------------------------
asv_values = [ring["asv"] for ring in reference["critical_perimeters"]]
print("\nTHE LINK STEEL DOES NOT FALL RING BY RING")
print("   Asv by ring: " + "  ".join(f"{value:.0f}" for value in asv_values))
rises = [(index, asv_values[index - 1], asv_values[index])
         for index in range(1, len(asv_values))
         if asv_values[index] > asv_values[index - 1] > 0]
free = [index + 1 for index, value in enumerate(asv_values) if value == 0]
if rises:
    index, before, after = rises[0]
    print(f"   -> it RISES from ring {index} to ring {index + 1}: "
          f"{before:.0f} -> {after:.0f} mm2, {after / before:.2f}x.")
    print("      The perimeter grows faster than the shear falls, so the")
    print("      steel per ring goes back up before it goes away.")
if free:
    print(f"   -> rings {', '.join(str(number) for number in free)} need "
          f"nothing at all.")
if rises and free:
    print("      Together those two mean the sequence is not something you")
    print("      can walk outward from the column and stop at the first")
    print("      light ring: on this head that would stop at ring "
          f"{rises[0][0]} and")
    print(f"      miss ring {rises[0][0] + 1}, which needs more than it.")

# -- The map ------------------------------------------------------------
total_asv = np.full((len(DEPTHS), len(COLUMNS)), np.nan)
face_use = np.full_like(total_asv, np.nan)
rings_needed = np.full_like(total_asv, np.nan)

for column_index, width in enumerate(COLUMNS):
    for row, depth in enumerate(DEPTHS):
        result = head(col_width=float(width), depth=float(depth))
        if result is None:
            continue
        stress, limit, _ = face(result)
        face_use[row, column_index] = stress / limit
        total_asv[row, column_index] = sum(
            ring["asv"] for ring in result["critical_perimeters"])
        rings_needed[row, column_index] = sum(
            1 for ring in result["critical_perimeters"] if ring["asv"] > 0)

answered = int(np.count_nonzero(~np.isnan(total_asv)))
over_face = int(np.count_nonzero(face_use > 1.0))
no_links = int(np.count_nonzero(total_asv == 0.0))
print(f"\nTHE MAP   {answered} heads answered")
if not_answered:
    print(f"   {len(not_answered)} call(s) did not answer for a reason that "
          f"is NOT about")
    print("      the geometry: " + ", ".join(sorted(set(not_answered))))
    print("      Those are holes punched in the map by the RUN. Read them")
    print("      before you read the map.")
print(f"   {over_face} fail the FACE check - no amount of link steel helps")
print(f"   {no_links} need no links at all")
print("   -> the face check is a ceiling on the stress at the column face,")
print("      not a capacity you reinforce past. It is the one boundary on")
print("      the map that has to be crossed by growing the column or the")
print("      slab.")

# -- The four remedies --------------------------------------------------
print("\nTHE THREE LEVERS, ON THE SAME FAILING HEAD")
SLIM_COLUMN = 300.0
SLIM_DEPTH = 190.0
HEAVY = 30.0 * BAY * BAY
problem = head(col_width=SLIM_COLUMN, depth=SLIM_DEPTH, shear=HEAVY)
print(f"   the problem: {SLIM_COLUMN:.0f} mm column, de {SLIM_DEPTH:.0f} mm,"
      f" V = {HEAVY:.0f} kN")
if problem is None:
    print("     NOT ANSWERED - the levers below still run, but there is no")
    print("     baseline face ratio to measure them against")
else:
    problem_stress, problem_limit, problem_ok = face(problem)
    print(f"     face vu {problem_stress:.3f} / vcu {problem_limit:.3f} = "
          f"{problem_stress / problem_limit:.2f}"
          f"  ->  {'OK' if problem_ok else 'FACE FAILS'}")

remedies = {}
remedies["thicken the slab"] = [
    (extra, head(col_width=SLIM_COLUMN, depth=SLIM_DEPTH + extra,
                 shear=HEAVY))
    for extra in range(0, 121, 20)]
remedies["enlarge the column"] = [
    (extra, head(col_width=SLIM_COLUMN + extra, depth=SLIM_DEPTH,
                 shear=HEAVY))
    for extra in range(0, 481, 80)]
remedies["more flexural steel"] = [
    (extra, head(col_width=SLIM_COLUMN, depth=SLIM_DEPTH, shear=HEAVY,
                 ratio=1.0 + extra / 100.0))
    for extra in range(0, 241, 40)]

print(f"   {'remedy':>22} {'change':>8} {'face vu/vcu':>12} "
      f"{'total Asv':>11}")
for name, rows in remedies.items():
    for change, result in rows:
        if result is None:
            continue
        stress, limit, _ = face(result)
        total = sum(ring["asv"] for ring in result["critical_perimeters"])
        print(f"   {name:>22} {change:>8.0f} {stress / limit:>12.3f} "
              f"{total:>11.0f}")

fixes_face = [name for name, rows in remedies.items()
              if any(result is not None and face(result)[2]
                     for _, result in rows)]
print(f"   -> {len(fixes_face)} of the {len(remedies)} levers can fix the "
      f"FACE check: "
      f"{', '.join(fixes_face) if fixes_face else 'none'}.")
flat = [name for name, rows in remedies.items()
        if len({round(face(result)[0] / face(result)[1], 4)
                for _, result in rows if result is not None}) == 1]
for name in flat:
    print(f"      '{name}' leaves the face ratio UNCHANGED over its whole")
    print("      range - it raises the concrete's shear capacity on the")
    print("      outer perimeters and does nothing to the stress at the")
    print("      column face, which depends only on the load and the")
    print("      column perimeter.")
print("      The other levers DO move that ratio, which is the control:")
print("      the reading is alive, so a flat line is a result.")

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(2, 2, figsize=(15, 11))
figure.patch.set_facecolor("white")

# 1. The plan.
plan = axes[0][0]
rings = reference["critical_perimeters"]
worst_use = max(ring["veff"] / ring["vcap"] for ring in rings)
palette = plt.cm.YlOrRd

for ring in reversed(rings):
    radius = ring["radial_distance"]
    use = ring["veff"] / ring["vcap"]
    plan.add_patch(Rectangle(
        (-(COLUMN / 2 + radius), -(COLUMN / 2 + radius)),
        COLUMN + 2 * radius, COLUMN + 2 * radius,
        facecolor=palette(min(use / max(worst_use, 1.0), 1.0)),
        edgecolor="0.25", linewidth=1.2, alpha=0.85, zorder=1))
    plan.annotate(f"{ring['perimeter']}: {use:.2f}x"
                  + ("  LINKS" if ring["asv"] > 0 else ""),
                  (0, COLUMN / 2 + radius), ha="center", va="bottom",
                  fontsize=8, zorder=4)

plan.add_patch(Rectangle((-COLUMN / 2, -COLUMN / 2), COLUMN, COLUMN,
                         facecolor="0.35", edgecolor="black",
                         linewidth=1.6, zorder=3))
plan.annotate(f"{COLUMN:.0f} sq", (0, 0), ha="center", va="center",
              color="white", fontsize=9, fontweight="bold", zorder=4)

reach = COLUMN / 2 + rings[-1]["radial_distance"] + 120
plan.set_xlim(-reach, reach)
plan.set_ylim(-reach, reach)
plan.set_aspect("equal")
plan.set_xlabel("mm from the column centre")
plan.set_ylabel("mm from the column centre")
plan.set_title("The five critical perimeters, to scale\n"
               "shaded by Veff/Vcap - the label says which rings need links",
               fontsize=10)

# 2. The map.
chart = axes[0][1]
mesh_c, mesh_d = np.meshgrid(COLUMNS, DEPTHS)
shade = chart.contourf(mesh_c, mesh_d, total_asv, levels=20, cmap="PuRd")
figure.colorbar(shade, ax=chart, label="total link steel over five rings "
                                       "(mm2)")
zero = chart.contour(mesh_c, mesh_d, total_asv, levels=[1.0],
                     colors="green", linewidths=2.4)
chart.clabel(zero, fmt={1.0: "no links needed above here"}, fontsize=8)
ceiling_line = chart.contour(mesh_c, mesh_d, face_use, levels=[1.0],
                             colors="black", linewidths=2.8)
chart.clabel(ceiling_line, fmt={1.0: "FACE CEILING - no remedy in links"},
             fontsize=8)
chart.contourf(mesh_c, mesh_d, np.where(face_use > 1.0, 1.0, np.nan),
               levels=[0.5, 1.5], colors="none", hatches=["xx"])
chart.plot(COLUMN, DEPTH, marker="*", markersize=20, color="white",
           markeredgecolor="black", zorder=5)
chart.set_xlabel("column size, square (mm)")
chart.set_ylabel("effective slab depth de (mm)")
chart.set_title(f"Link steel over the whole head, V = {SHEAR:.0f} kN\n"
                "the star is the reference head", fontsize=10)

# 3. Ring by ring, reference against a thickened slab.
bars = axes[1][0]
thicker = head(depth=DEPTH + 50.0)
positions = np.arange(len(rings))
bars.bar(positions - 0.19, [ring["asv"] for ring in rings], width=0.38,
         color="#b03030", label=f"de {DEPTH:.0f} mm")
if thicker is not None:
    bars.bar(positions + 0.19,
             [ring["asv"] for ring in thicker["critical_perimeters"]],
             width=0.38, color="#4c78a8", label=f"de {DEPTH + 50:.0f} mm")
bars.set_xticks(positions)
bars.set_xticklabels([f"ring {ring['perimeter']}\nr = "
                      f"{ring['radial_distance']:.0f} mm" for ring in rings],
                     fontsize=8)
bars.set_ylabel("link steel required Asv (mm2)")
bars.set_title("Ring by ring - and it does not fall monotonically",
               fontsize=10)
bars.legend(fontsize=8)
bars.grid(True, axis="y", linewidth=0.3, color="0.85")

# 4. The remedies.
cure = axes[1][1]
styles = {"thicken the slab": ("#4c78a8", "extra depth (mm)"),
          "enlarge the column": ("#59a14f", "extra column size (mm)"),
          "more flexural steel": ("#e0a030", "extra top steel (%)")}
for name, rows in remedies.items():
    if name not in styles:
        continue
    colour, _ = styles[name]
    xs = [change for change, result in rows if result is not None]
    ys = [face(result)[0] / face(result)[1]
          for _, result in rows if result is not None]
    if xs:
        # Normalised so three different levers share one axis.
        span = max(xs) or 1.0
        cure.plot([x / span * 100.0 for x in xs], ys, marker="o",
                  markersize=6, linewidth=2.0, color=colour,
                  label=f"{name} (0 to {max(xs):.0f})")
cure.axhline(1.0, color="black", linestyle="--", linewidth=1.8)
cure.annotate("face ceiling", (2, 1.02), fontsize=9)
cure.set_xlabel("how far the remedy is taken (% of its full range)")
cure.set_ylabel("face stress vu / vcu")
cure.set_title("Only two of the three levers touch the face check\n"
               f"({SLIM_COLUMN:.0f} mm column, de {SLIM_DEPTH:.0f} mm, "
               f"V = {HEAVY:.0f} kN)", fontsize=10)
cure.legend(fontsize=8)
cure.grid(True, linewidth=0.3, color="0.85")

figure.suptitle(
    f"Punching shear at a column head - {CODE}\n"
    f"{BAY:.1f} m bay at {LOAD:.0f} kPa, V = {SHEAR:.0f} kN, "
    f"Mx {TRANSFER_X:.0f} / My {TRANSFER_Y:.0f} kNm, fcu {FCU:.0f} MPa, "
    f"fyv {FYV:.0f} MPa, internal column  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "punching_shear_perimeter_plan.png")
