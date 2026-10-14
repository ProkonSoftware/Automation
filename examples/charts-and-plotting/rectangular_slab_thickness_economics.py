# ---
# Example:  How thick should the slab be? The self-weight loop, drawn
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - the anchor reproduces the desktop calcsheet for its own Default Example (689 / 349 / 1106 / 566); the 143-cell map, the frozen-self-weight control and all 29 codes measured on prokon-automation.exe
# ---
# A slab is the one element where the structure's own weight is most of the
# load, so thickness is not a free variable: make it thicker and you have
# made the load bigger.
#
# ⚠ AND THE ENGINE NOW CLOSES THAT LOOP FOR YOU. C04 analyses the panel and
# adds the slab's own weight to every load case itself, from `density` and
# the thickness. This script used to compute the weight, turn it into a
# moment with a coefficient, and hand the moment over; all of that is gone.
# What is left is the interesting part - what the feedback DOES to the price.
#
# The script does three things:
#
#   THE DESIGN MAP     total steel over the whole (span, thickness) plane,
#                      with the region the engine will not design marked on
#                      it. Pure C04, no assumptions of ours.
#   THE SELF-WEIGHT    for three spans, the floor is priced per square metre
#   LOOP               at every thickness, and the cheapest is found.
#   THE CODE SPREAD    the same panel through all twenty-nine codes, as a
#                      sorted bar chart. Four of them design nothing at all,
#                      and the chart says so rather than plotting a zero as
#                      if it were an answer.
#
# ⚠ ONE CLAIM IN THIS SCRIPT WAS REFUTED BY ITS OWN CONTROL, WHICH IS WHY
# THE CONTROL IS STILL IN IT. The obvious story - "the cost minimum exists
# because of the self-weight feedback" - is wrong. Freeze the weight and the
# minimum is still there, because the plain trade between concrete and steel
# already produces one. What the feedback does is MOVE the economic
# thickness, and the script measures by how much.
#
# The freeze is exact rather than approximate: `self_weight_lf=0` switches
# the engine's own weight off, and the thinnest slab's weight goes back on
# as an ordinary load row. Same load at every thickness, by construction.
#
# ⚠ AND ONE WARNING THIS FILE USED TO CARRY IS NOW GONE. It said a numpy
# scalar was refused where the identical value as a plain float was accepted.
# MEASURED 2026-09-10: np.float64 is accepted and returns the identical
# answer, so the float() wrapping that used to be load-bearing is not. The
# calls below still pass plain floats, because a script that says what it
# means is easier to read - not because the engine insists.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# -- SAVE THE PNG, AND SHOW IT IN SPYDER --------------------------------
# Spyder runs matplotlib on its own backend - "inline" puts the figure in
# the Plots pane, "automatic" opens a window - so plt.show() displays the
# chart right where you are working. A headless run (a batch job, or this
# documentation's own sweep) runs the Agg backend, where show() can only
# warn. So ASK the backend, and write the PNG either way.
#
# There is deliberately NO matplotlib.use("Agg") here. That call forces the
# headless backend, and a script that forces it can never draw into Spyder's
# Plots pane - which is where you actually want to see it.
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


# -- The floor ----------------------------------------------------------
CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
COVER = 25.0              # mm
BAR = 12.0                # mm, assumed for the effective depth

IMPOSED = 4.0             # kPa live
FINISHES = 1.5            # kPa superimposed dead
CONCRETE_DENSITY = 24.0   # kN/m3
LOAD_FACTOR_DEAD = 1.4
LOAD_FACTOR_LIVE = 1.6

RATE_CONCRETE = 1950.0    # per m3
RATE_STEEL = 24.0         # per kg
RATE_SOFFIT = 320.0       # per m2 of soffit formwork
DENSITY_STEEL = 7850.0

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

FACES = ("x_top", "x_bot", "y_top", "y_bot")

THICKNESSES = np.arange(100.0, 401.0, 25.0)      # 13 - deliberately
                                                 # starting thin enough
                                                 # that the long spans
                                                 # fail to design, so the
                                                 # map has a real edge
GRID_SPANS = np.arange(5.0, 10.1, 1.0)           # 6
SPANS = (6.0, 7.5, 9.0)                          # the three drawn in detail

# -- Two numbers that decide how long this script takes -----------------
# The design map below is Cartesian, so its cost is the product of the two
# step sizes above, and every point is a separate engine process at about
# 0.3 s. Choose the steps for the chart you want to READ - halving a step
# doubles the wait.
#
# Then bound the wait itself. timeout_seconds is PER CALL, it defaults to
# 120 s, and these calls take 0.3 s - so one stuck call could cost more
# than the whole sweep. Sized here at many times what a healthy call takes
# and still far below what this whole script costs: generous, and bounded.
prokon.v5.timeout_seconds = 30.0

# The panel is a bay of that span by a bay and a half, continuous all round.
ASPECT = 1.5

print("HOW THICK SHOULD THE SLAB BE?")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm, "
      f"Y{BAR:.0f} bars")
print(f"  {IMPOSED:.1f} kPa imposed + {FINISHES:.1f} kPa finishes; the ENGINE "
      f"adds the slab's own weight")
print(f"  grid: {len(THICKNESSES)} thicknesses x {len(GRID_SPANS)} spans "
      f"= {len(THICKNESSES) * len(GRID_SPANS)} engine calls, plus "
      f"{len(SPANS) * len(THICKNESSES)} for the frozen control and 29 for "
      f"the codes")


# -- The anchor ---------------------------------------------------------
# The desktop program's own Default Example, so this sweep starts from a
# panel whose answer is published rather than one only this script has seen.
CALCSHEET = {"x_top": 689, "x_bot": 349, "y_top": 1106, "y_bot": 566}

envelope = prokon.v5.rectangular_slab.analyse(
    design_code=CODE, lx=13.81, ly=8.21, h=250.0, dx=200.0, dy=220.0,
    fcu=25.0, fy=450.0,
    edge_top=ENCASTRE, edge_right=ENCASTRE, edge_bottom=ENCASTRE,
    edge_left="FixedAgainstVerticalDisplacement",
    load_cases=[
        {"number": 1, "lf": 1.4, "udl": 2.0,
         "p": 4.0, "x": 4.19, "y": 6.45,
         "l": 4.1, "x1": 2.44, "y1": 4.05, "x2": 10.03, "y2": 6.65},
        {"lf": 1.6, "udl": 2.0,
         "p": 4.0, "x": 10.06, "y": 2.99,
         "l": 2.0, "x1": 2.59, "y1": 2.62, "x2": 9.99, "y2": 4.61},
        {"number": 2, "lf": 1.4, "udl": 1.0, "p": 12.0, "x": 3.28, "y": 6.6},
    ],
    envelope="1,2")

anchor = envelope["result"]["ast"]
print("\n  anchor: the desktop's own Default Example, against its calcsheet")
for face in FACES:
    print(f"    {face:<6} {anchor[face]:10.4f}   calcsheet {CALCSHEET[face]:>5}"
          f"   {'agrees' if round(anchor[face]) == CALCSHEET[face] else 'DIFFERS'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


# invalid_input and no_solution say something about the PANEL - this
# geometry has no answer - and belong on the map as a hole. Every other
# category says something about the RUN, and a map quietly missing those
# points would be a lie. So they are counted by category and printed.
NO_ANSWER_HERE = ("invalid_input", "no_solution")
not_answered = []

# The self-weight loop below asks for panels the design map has already
# priced. Asking an engine the same question twice costs 0.3 s and is a
# second chance to fail, so the answer is kept.
answers = {}


def panel(thickness, span, code=CODE, frozen_weight=None):
    """One panel. Returns the whole result, or None if the engine refused.

    The effective depth follows the thickness: cover plus half a bar in the
    x direction, one bar lower in y, exactly as it would be detailed.

    `frozen_weight` is the CONTROL. Pass a kPa value and the engine's own
    self weight is switched off and that constant put on instead, so the
    load stops depending on the thickness.
    """
    thickness = float(thickness)
    span = float(span)

    asked = (thickness, span, code, frozen_weight)
    if asked in answers:
        return answers[asked]

    dx = thickness - COVER - BAR / 2.0
    dy = thickness - COVER - BAR - BAR / 2.0

    if dy <= thickness / 2.0:
        answers[asked] = None
        return None

    rows = [{"number": 1, "lf": LOAD_FACTOR_DEAD, "udl": FINISHES},
            {"lf": LOAD_FACTOR_LIVE, "udl": IMPOSED}]

    extra = {}
    if frozen_weight is not None:
        rows.append({"lf": LOAD_FACTOR_DEAD, "udl": frozen_weight})
        extra["self_weight_lf"] = 0.0

    try:
        answered = prokon.v5.rectangular_slab.analyse(
            design_code=code,
            lx=span, ly=span * ASPECT,
            h=thickness, dx=dx, dy=dy,
            fcu=FCU, fy=FY,
            edge_top=ENCASTRE, edge_right=ENCASTRE,
            edge_bottom=ENCASTRE, edge_left=ENCASTRE,
            load_cases=rows,
            **extra)["result"]
    except prokon.v5.ProkonError as refusal:
        if refusal.category not in NO_ANSWER_HERE:
            not_answered.append("{0}/{1}".format(refusal.category,
                                                 refusal.code))
        answers[asked] = None
        return None
    else:
        answers[asked] = answered
        return answered


def declined_faces(result):
    """Faces carrying a moment that came back with no steel.

    A zero there is the engine declining to design the face, not a face
    that needs none - and a cost model that summed it would price a slab
    the engine would not build.
    """
    return [face for face in FACES
            if result["ast"][face] == 0.0 and result["moment_max"][face] > 0.0]


def cost_of(thickness, result):
    """Concrete, steel and soffit formwork, per square metre of floor."""
    steel_kg = sum(result["ast"][face] for face in FACES) / 1e6 * DENSITY_STEEL
    concrete = thickness / 1000.0 * RATE_CONCRETE
    return concrete + steel_kg * RATE_STEEL + RATE_SOFFIT, steel_kg, concrete


# -- 1. The design map --------------------------------------------------
steel = np.full((len(THICKNESSES), len(GRID_SPANS)), np.nan)
declined = np.zeros_like(steel)

for row, thickness in enumerate(THICKNESSES):
    for column, span in enumerate(GRID_SPANS):
        result = panel(thickness, span)
        if result is None:
            continue

        bad = declined_faces(result)
        declined[row, column] = 1.0 if bad else 0.0

        if not bad:
            steel[row, column] = sum(result["ast"][face] for face in FACES)

answered = int(np.count_nonzero(~np.isnan(steel)))
refused_cells = int(np.sum(declined))

print(f"\nDESIGN MAP   {answered} panels designed on every face")
print(f"   total steel ranges {np.nanmin(steel):.0f} to "
      f"{np.nanmax(steel):.0f} mm2/m over the four faces")
print(f"   {refused_cells} cell(s) had at least one face the engine declined")
if not_answered:
    print(f"   {len(not_answered)} call(s) did not answer for a reason that "
          f"is NOT about")
    print("      the panel: " + ", ".join(sorted(set(not_answered))))
    print("      Those are holes punched in the map by the RUN. Read them")
    print("      before you read the map.")

# -- 2. The self-weight loop --------------------------------------------
print("\nTHE SELF-WEIGHT LOOP   the engine adds the weight; we price the result")
print(f"   {'h':>5} {'self wt':>9}" + "".join(f"{span:>11.1f} m" for span in SPANS))

curves = {span: {"cost": [], "steel": [], "concrete": [], "formwork": [],
                 "steel_cost": [], "thickness": []}
          for span in SPANS}

for thickness in THICKNESSES:
    self_weight = CONCRETE_DENSITY * thickness / 1000.0
    line = []

    for span in SPANS:
        result = panel(thickness, span)
        if result is None or declined_faces(result):
            line.append("-")
            continue

        cost, steel_kg, concrete = cost_of(thickness, result)
        data = curves[span]
        data["thickness"].append(float(thickness))
        data["cost"].append(cost)
        data["steel"].append(steel_kg)
        data["concrete"].append(concrete)
        data["formwork"].append(RATE_SOFFIT)
        data["steel_cost"].append(steel_kg * RATE_STEEL)
        line.append(f"{cost:.0f}")

    print(f"   {thickness:>5.0f} {self_weight:>7.1f} kPa "
          + "".join(f"{cell:>13}" for cell in line))

print(f"\n   {'span':>6} {'cheapest h':>11} {'cost/m2':>9} {'steel':>9}")
best_of = {}
for span in SPANS:
    data = curves[span]
    if not data["cost"]:
        continue
    index = int(np.argmin(data["cost"]))
    best_of[span] = data["thickness"][index]
    print(f"   {span:>6.1f} {data['thickness'][index]:>10.0f} mm "
          f"{data['cost'][index]:>9.0f} {data['steel'][index]:>7.1f} kg")
print("   -> the minimum is real, and it moves with the span.")

# -- The control, and what it actually showed ---------------------------
# CLAIM AS FIRST WRITTEN: the cost minimum exists BECAUSE of the self-weight
# feedback - freeze the load and the curve would fall forever.
# CONTROL: the same sweep with the engine's own weight switched off and the
# THINNEST slab's weight put on as a constant instead.
#
# ⚠ THE CONTROL REFUTED THE CLAIM, and the retraction is the useful part.
# With the weight frozen the minimum is STILL interior, because the plain
# trade between concrete and steel already produces one: a thicker slab
# always needs less steel and always costs more concrete. So the feedback is
# not what MAKES the minimum. What it does is MOVE it.
print("\n   the control - the same sweep with the self weight FROZEN")
frozen_weight = CONCRETE_DENSITY * float(THICKNESSES[0]) / 1000.0
print(f"     self_weight_lf=0, and {frozen_weight:.2f} kPa put back as a load "
      f"row at every thickness")

shifts = []
for span in SPANS:
    frozen_costs, frozen_thicknesses = [], []

    for thickness in THICKNESSES:
        result = panel(thickness, span, frozen_weight=frozen_weight)
        if result is None or declined_faces(result):
            continue
        cost, _, _ = cost_of(thickness, result)
        frozen_costs.append(cost)
        frozen_thicknesses.append(float(thickness))

    if not frozen_costs or span not in best_of:
        continue

    index = int(np.argmin(frozen_costs))
    frozen_best = frozen_thicknesses[index]
    interior = 0 < index < len(frozen_costs) - 1
    shifts.append(best_of[span] - frozen_best)

    print(f"     {span:.1f} m: cheapest at {frozen_best:.0f} mm, "
          f"{'an INTERIOR minimum' if interior else 'the thinnest that works'}"
          f"   (with the loop: {best_of[span]:.0f} mm)")

if shifts:
    print("     -> the control REFUTES the obvious explanation. A minimum")
    print("        appears with the weight frozen too, so the feedback is not")
    print("        what creates it - the plain trade between concrete and")
    print("        steel already does.")
    print(f"        What the feedback does is MOVE the optimum, by "
          f"{np.mean(shifts):+.0f} mm on")
    print("        average here: a slab that has to carry its own extra")
    print("        weight is charged for being thick twice. That is the")
    print("        number to take away, and it only exists because the")
    print("        control was run.")

# -- 3. The twenty-nine codes -------------------------------------------
CODE_THICKNESS = 250.0
CODE_SPAN = 7.5
print(f"\nTWENTY-NINE CODES   {CODE_THICKNESS:.0f} mm slab, "
      f"{CODE_SPAN:.1f} x {CODE_SPAN * ASPECT:.2f} m panel")

designs = []
silent = []
refused = []

for name in prokon.v5.rectangular_slab.DESIGN_CODE_VALUES:
    result = panel(CODE_THICKNESS, CODE_SPAN, code=name)
    if result is None:
        refused.append(name)
        continue

    # THE RELIABLE DETECTOR for a code with no flexural rules: every face
    # zero while the moments are real. The engine also publishes a warning
    # saying so - see design-studies/rectangular_slab_all_codes.py, which
    # branches on that instead.
    if all(result["ast"][face] == 0.0 for face in FACES):
        silent.append(name)
        continue

    designs.append((name, sum(result["ast"][face] for face in FACES)))

designs.sort(key=lambda row: row[1])
for name, value in designs:
    print(f"   {name:<28} {value:8.1f} mm2/m")
for name in silent:
    print(f"   {name:<28} {'designs nothing (every face zero)':>33}")
for name in refused:
    print(f"   {name:<28} {'refused':>33}")

if designs:
    print(f"   -> {len(designs)} codes design, {len(silent)} design nothing, "
          f"{len(refused)} refuse.")
    print(f"      Across the {len(designs)} that do, the same panel needs "
          f"{designs[0][1]:.0f} to {designs[-1][1]:.0f} mm2/m -")
    print(f"      a {designs[-1][1] / designs[0][1]:.3f}x spread on one panel "
          f"and one load.")

# -- The figure ---------------------------------------------------------
figure = plt.figure(figsize=(15.5, 10))
figure.patch.set_facecolor("white")
grid = figure.add_gridspec(2, 2, hspace=0.32, wspace=0.24)
mesh_span, mesh_h = np.meshgrid(GRID_SPANS, THICKNESSES)

# 1. The design map.
chart = figure.add_subplot(grid[0, 0])
shade = chart.contourf(mesh_span, mesh_h, steel, levels=22, cmap="PuBuGn")
figure.colorbar(shade, ax=chart, label="total steel, four faces (mm2/m)")
lines = chart.contour(mesh_span, mesh_h, steel,
                      levels=[800, 1200, 1600, 2200, 3000],
                      colors="0.2", linewidths=0.9)
chart.clabel(lines, fmt="%.0f", fontsize=7)

if refused_cells:
    chart.contourf(mesh_span, mesh_h, declined, levels=[0.5, 1.5],
                   colors="none", hatches=["////"])
    chart.contour(mesh_span, mesh_h, declined, levels=[0.5],
                  colors="red", linewidths=2.0)

for span in SPANS:
    if span in best_of:
        chart.plot(span, best_of[span], marker="*", markersize=16,
                   color="white", markeredgecolor="black", zorder=6)

chart.set_xlabel("span (m)")
chart.set_ylabel("slab thickness (mm)")
chart.set_title("Steel demand over the (span, thickness) plane\n"
                + ("hatched: at least one face the engine will not "
                   "design; " if refused_cells else "")
                + "stars: the cheapest thickness", fontsize=10)

# 2. The cost curves.
economics = figure.add_subplot(grid[0, 1])
for span in SPANS:
    data = curves[span]
    economics.plot(data["thickness"], data["cost"], linewidth=2.0,
                   marker="o", markersize=4, label=f"{span:.1f} m")
    if span in best_of:
        row = data["thickness"].index(best_of[span])
        economics.plot(best_of[span], data["cost"][row], marker="*",
                       markersize=18, color="white",
                       markeredgecolor="black", zorder=6)
        economics.annotate(f"{best_of[span]:.0f} mm",
                           (best_of[span], data["cost"][row]),
                           textcoords="offset points", xytext=(6, -16),
                           fontsize=8, fontweight="bold")
economics.set_xlabel("slab thickness (mm)")
economics.set_ylabel("cost per square metre of floor")
economics.set_title("Cost with the self-weight loop closed\n"
                    "the minimum is real - but the loop MOVES it, it does "
                    "not create it", fontsize=10)
economics.legend(title="span", fontsize=8, title_fontsize=8)
economics.grid(True, linewidth=0.3, color="0.85")

# 3. What the money is spent on, at the middle span.
middle = SPANS[len(SPANS) // 2]
data = curves[middle]
split = figure.add_subplot(grid[1, 0])
split.stackplot(data["thickness"], data["steel_cost"], data["concrete"],
                data["formwork"],
                labels=("steel", "concrete", "soffit formwork"),
                colors=("#b03030", "#8a8f98", "#4c78a8"), alpha=0.9)
split.plot(data["thickness"], data["cost"], color="black", linewidth=1.8,
           label="total")
if middle in best_of:
    split.axvline(best_of[middle], color="black", linestyle="--",
                  linewidth=1.0)
split.set_xlabel("slab thickness (mm)")
split.set_ylabel("cost per square metre")
split.set_title(f"Where the money goes, {middle:.1f} m span", fontsize=10)
split.legend(loc="upper left", fontsize=8)
split.grid(True, linewidth=0.3, color="0.85")

# 4. The twenty-nine codes.
spread = figure.add_subplot(grid[1, 1])
names = [name for name, _ in designs]
values = [value for _, value in designs]
colours = ["#4c78a8"] * len(values)
if CODE in names:
    colours[names.index(CODE)] = "#b03030"
spread.barh(range(len(values)), values, color=colours)
spread.set_yticks(range(len(values)))
spread.set_yticklabels(names, fontsize=7)
spread.invert_yaxis()
spread.set_xlabel("total steel, four faces (mm2/m)")
spread.set_title(f"The same panel, {len(designs)} codes that design it\n"
                 f"({len(silent)} more return every face zero and design "
                 f"nothing - not plotted)", fontsize=10)
spread.grid(True, axis="x", linewidth=0.3, color="0.85")
for index, value in enumerate(values):
    spread.annotate(f"{value:.0f}", (value, index), xytext=(4, -3),
                    textcoords="offset points", fontsize=6.5, va="center")

figure.suptitle(
    f"Rectangular slab thickness economics - {CODE}\n"
    f"fcu {FCU:.0f} MPa, fy {FY:.0f} MPa, cover {COVER:.0f} mm, "
    f"{IMPOSED:.1f} kPa imposed + {FINISHES:.1f} kPa finishes, "
    f"self weight by the engine  |  "
    f"concrete {RATE_CONCRETE:.0f}/m3, steel {RATE_STEEL:.0f}/kg, "
    f"soffit {RATE_SOFFIT:.0f}/m2  |  engine {envelope['module_version']}",
    fontsize=10)
# NOT tight_layout: it warns on a figure carrying a colorbar, and the
# gridspec above already spaces these four panels.
figure.subplots_adjust(left=0.07, right=0.97, top=0.87, bottom=0.07)

deliver(figure, "rectangular_slab_thickness_economics.png")
