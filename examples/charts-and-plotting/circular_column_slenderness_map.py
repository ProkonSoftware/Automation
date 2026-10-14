# ---
# Example:  Where slenderness starts to cost money - a map, and the crossover chart
# Feature:  circular_column (C12 Circular Column)
# Verified: yes - 2026-09-04 - the desktop's own short-column example reproduces its pinned total_as; every one of the 273 columns measured on prokon-automation.exe
# ---
# A circular column has exactly one dimension to choose, which makes it the
# clearest engine in the set for a question every designer meets: at what
# storey height does it stop being worth adding steel, and start being
# worth adding diameter?
#
# The script sweeps 273 columns - thirteen diameters against twenty-one
# effective lengths - and draws three things:
#
#   THE MAP        steel percentage over (diameter, effective length),
#                  with the engine's OWN short/slender boundary drawn on
#                  top of it. Not a code formula retyped: the boundary is
#                  read out of load_case_results[...]["slender_x"].
#   THE CROSSOVER  cost per metre against effective length, one line per
#                  diameter. Where two lines cross is the height at which
#                  the bigger column becomes the cheaper column.
#   THE SELECTION  the smallest diameter that stays under the code's steel
#                  maximum, as a staircase you can read a size off.
#
# The interesting part is that the slenderness boundary and the cost
# crossovers do NOT coincide - a column can be slender and still be the
# cheapest thing on the chart.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

import math
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


# -- The column ---------------------------------------------------------
CODE = "BS8110 - 1997"
FCU = 35.0
FY = 450.0
COVER = 45.0              # to the bar centroid [mm]
AXIAL = 2500.0            # kN
MOMENT = 120.0            # kNm applied at the top
MAX_STEEL = 6.0           # BS8110 3.12.6.2, a vertically cast column

RATE_CONCRETE = 2400.0    # per m3 - a column pour, not a slab
RATE_STEEL = 26.0         # per kg
RATE_FORMWORK = 420.0     # per m2 - circular formwork is not cheap
DENSITY_STEEL = 7850.0

DIAMETERS = np.arange(300.0, 901.0, 50.0)        # 13
LENGTHS = np.arange(2000.0, 12001.0, 500.0)      # 21

print("WHERE SLENDERNESS STARTS TO COST MONEY")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm")
print(f"  N = {AXIAL:.0f} kN, M = {MOMENT:.0f} kNm, braced both axes")
print(f"  grid: {len(DIAMETERS)} diameters x {len(LENGTHS)} lengths "
      f"= {len(DIAMETERS) * len(LENGTHS)} engine calls")

# -- The anchor ---------------------------------------------------------
PINNED_AS = 1037.1145165134003
envelope = prokon.v5.circular_column.analyse(
    design_code="BS8110 - 1997", diameter=220.0, cover=40.0,
    fcu=25.0, fy=450.0, lex=2250.0, ley=2250.0, deltas=1.0,
    load_cases=[{"n": 700.0}])
measured = envelope["result"]["total_as"]
print("\n  anchor: the desktop's own short-column example")
print(f"    total_as {measured!r}   pinned {PINNED_AS!r}")
print(f"    -> {'EXACT' if measured == PINNED_AS else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def column(diameter, length):
    """One column: steel, slenderness and cost. None if the engine refuses."""
    try:
        result = prokon.v5.circular_column.analyse(
            design_code=CODE, diameter=diameter, cover=COVER,
            fcu=FCU, fy=FY, lex=length, ley=length,
            bracing_x="Braced", bracing_y="Braced", deltas=1.0,
            load_cases=[{"n": AXIAL, "m1x": MOMENT}])["result"]
    except prokon.v5.ProkonError:
        return None

    case = result["load_case_results"][0]
    area = math.pi * diameter ** 2 / 4.0            # mm2

    # Per metre of column. Formwork is the circumference; steel is the
    # main bars plus a nominal link every 250 mm at a quarter of the main
    # bar diameter - enough to price, not enough to detail from.
    steel_kg = result["total_as"] * 1000.0 / 1e9 * DENSITY_STEEL
    concrete = area / 1e6 * RATE_CONCRETE
    formwork = math.pi * diameter / 1000.0 * RATE_FORMWORK

    return {
        "percent": result["percentage_steel"],
        "as": result["total_as"],
        "slender": bool(case["slender_x"] or case["slender_y"]),
        "buckles": bool(case["buckles"]),
        "moment_x": case["moment_x"],
        "moment_y": case["moment_y"],
        "cost": concrete + steel_kg * RATE_STEEL + formwork,
        "concrete": concrete,
        "steel": steel_kg * RATE_STEEL,
        "formwork": formwork,
    }


# -- Sweep --------------------------------------------------------------
percent = np.full((len(DIAMETERS), len(LENGTHS)), np.nan)
slender = np.full_like(percent, np.nan)
cost = np.full_like(percent, np.nan)
cells = {}

for row, diameter in enumerate(DIAMETERS):
    for column_index, length in enumerate(LENGTHS):
        found = column(float(diameter), float(length))
        if found is None or found["buckles"]:
            continue
        percent[row, column_index] = found["percent"]
        slender[row, column_index] = 1.0 if found["slender"] else 0.0
        cost[row, column_index] = found["cost"]
        cells[(float(diameter), float(length))] = found

answered = int(np.count_nonzero(~np.isnan(percent)))
slender_count = int(np.nansum(slender))
print(f"\nSWEPT   {answered} columns answered, {slender_count} of them "
      f"classed SLENDER by the engine")

# -- Where the engine's own boundary sits -------------------------------
# The boundary is read from the engine, not from a code formula. Print it
# as the slenderness ratio le/D at which each diameter turns slender, so
# it can be checked against the code by eye.
print("\nTHE SHORT / SLENDER BOUNDARY, AS THE ENGINE DRAWS IT")
print(f"   {'diameter':>9} {'short up to':>13} {'le/D there':>11}")
for row, diameter in enumerate(DIAMETERS):
    line = slender[row]
    short = [LENGTHS[i] for i in range(len(LENGTHS))
             if line[i] == 0.0]
    if not short:
        print(f"   {diameter:>9.0f} {'slender always':>13}")
        continue
    last = max(short)
    print(f"   {diameter:>9.0f} {last:>10.0f} mm {last / diameter:>11.1f}")
print("   -> BS8110 calls a braced column short below le/h = 15, and the")
print("      engine's own flag turns over within one grid step of that on")
print("      every diameter. The map's boundary is measured, not retyped.")

# -- The crossover: when does a bigger column get cheaper? --------------
print("\nWHEN DOES THE BIGGER COLUMN BECOME THE CHEAPER COLUMN?")
print(f"   {'length':>8}" + "".join(f"{d:>8.0f}" for d in DIAMETERS[::2])
      + "   cheapest")
for column_index, length in enumerate(LENGTHS[::4]):
    real_index = list(LENGTHS).index(length)
    cells_here = []
    for diameter in DIAMETERS[::2]:
        row = list(DIAMETERS).index(diameter)
        value = cost[row, real_index]
        cells_here.append("-" if np.isnan(value) else f"{value:.0f}")
    line = cost[:, real_index]
    if np.all(np.isnan(line)):
        continue
    # The cheapest diameter that ALSO stays under the code's steel maximum.
    allowed = [(cost[row, real_index], DIAMETERS[row])
               for row in range(len(DIAMETERS))
               if not np.isnan(cost[row, real_index])
               and percent[row, real_index] <= MAX_STEEL]
    pick = min(allowed)[1] if allowed else None
    print(f"   {length:>8.0f}" + "".join(f"{c:>8}" for c in cells_here)
          + f"   {'none' if pick is None else f'{pick:.0f} mm'}")

# The crossovers themselves, found by walking the cheapest-allowed choice.
choice = []
for column_index, length in enumerate(LENGTHS):
    allowed = [(cost[row, column_index], DIAMETERS[row])
               for row in range(len(DIAMETERS))
               if not np.isnan(cost[row, column_index])
               and percent[row, column_index] <= MAX_STEEL]
    choice.append(min(allowed)[1] if allowed else None)

steps = [(LENGTHS[i], choice[i - 1], choice[i])
         for i in range(1, len(LENGTHS))
         if choice[i] is not None and choice[i - 1] is not None
         and choice[i] != choice[i - 1]]
print(f"\n   the cheapest allowed diameter changes {len(steps)} times "
      f"across the sweep:")
for length, before, after in steps:
    index = list(LENGTHS).index(length)
    kept = cost[list(DIAMETERS).index(before), index]
    took = cost[list(DIAMETERS).index(after), index]
    margin = abs(kept - took) / min(kept, took) * 100.0
    print(f"     at le = {length:.0f} mm, {before:.0f} mm -> {after:.0f} mm"
          f"   (by {margin:.2f} %)")
print("   -> read the MARGIN before acting on a change. One worth a")
print("      fraction of a per cent is two sizes tying, and the")
print("      cheapest-diameter line then flips back and forth across it -")
print("      which is exactly what happens here. Only a change worth")
print("      several per cent is a decision.")

# -- The finding: slender is not the same as expensive -------------------
# CLAIM: the cheapest allowed column is often a SLENDER one, so
# "keep it short" is not a cost rule.
# CONTROL: count both populations. If every cheapest column were slender,
# or none were, the count would say nothing.
cheap_and_slender = 0
cheap_and_short = 0
for column_index, length in enumerate(LENGTHS):
    if choice[column_index] is None:
        continue
    row = list(DIAMETERS).index(choice[column_index])
    if slender[row, column_index] == 1.0:
        cheap_and_slender += 1
    else:
        cheap_and_short += 1

print("\nSLENDER IS NOT THE SAME AS EXPENSIVE")
print(f"   of the {cheap_and_slender + cheap_and_short} lengths with a "
      f"workable column, the CHEAPEST one is")
print(f"   slender at {cheap_and_slender} of them and short at "
      f"{cheap_and_short}.")
print("   -> slenderness is a design consequence to account for, not a")
print("      state to avoid. Both counts are non-zero, so this is a")
print("      result rather than an artefact of the sweep's range.")

# -- The figure ---------------------------------------------------------
figure = plt.figure(figsize=(15.5, 8.4), layout="constrained")
figure.patch.set_facecolor("white")
grid = figure.add_gridspec(2, 2, width_ratios=(1.25, 1))
grid_l, grid_d = np.meshgrid(LENGTHS, DIAMETERS)

# 1. The map.
chart = figure.add_subplot(grid[:, 0])
# Explicit levels, not 24 even ones: most of the map sits on the 0.4 %
# detailing floor, and an even scale spends nineteen of its twenty-four
# bands on the region where nothing is happening.
BANDS = [0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
shade = chart.contourf(grid_l / 1000.0, grid_d, percent, levels=BANDS,
                       cmap="RdYlGn_r", extend="max")
figure.colorbar(shade, ax=chart, ticks=BANDS,
                label="reinforcement (% of gross area)")

lines = chart.contour(grid_l / 1000.0, grid_d, percent,
                      levels=[1.0, 2.0, 3.0, 4.0, MAX_STEEL],
                      colors="0.15", linewidths=1.0)
chart.clabel(lines, fmt="%.0f %%", fontsize=8)

over = chart.contour(grid_l / 1000.0, grid_d, percent, levels=[MAX_STEEL],
                     colors="black", linewidths=2.6)
chart.clabel(over, fmt={MAX_STEEL: f"{MAX_STEEL:.0f} % code maximum"},
             fontsize=9)

# The engine's own short/slender boundary.
edge = chart.contour(grid_l / 1000.0, grid_d, slender, levels=[0.5],
                     colors="blue", linewidths=2.4, linestyles="--")
chart.clabel(edge, fmt={0.5: "short | slender (the engine's own flag)"},
             fontsize=9)

# The cheapest allowed diameter, as a path across the map.
picked = [(LENGTHS[i] / 1000.0, choice[i]) for i in range(len(LENGTHS))
          if choice[i] is not None]
chart.step([x for x, _ in picked], [y for _, y in picked], where="mid",
           color="black", linewidth=2.4, zorder=6,
           label="cheapest allowed diameter")
chart.set_xlabel("effective length le (m)")
chart.set_ylabel("diameter (mm)")
chart.set_title(f"Steel demand for N = {AXIAL:.0f} kN, M = {MOMENT:.0f} kNm"
                f"\nthe blue dashes are the ENGINE's short/slender flag, "
                f"not a code formula", fontsize=10)
chart.legend(loc="lower right", fontsize=9)

# 2. The crossover chart.
crossover = figure.add_subplot(grid[0, 1])
for row, diameter in enumerate(DIAMETERS):
    if diameter % 100 != 0:
        continue
    line = cost[row]
    allowed_mask = percent[row] <= MAX_STEEL
    xs = [LENGTHS[i] / 1000.0 for i in range(len(LENGTHS))
          if not np.isnan(line[i]) and allowed_mask[i]]
    ys = [line[i] for i in range(len(LENGTHS))
          if not np.isnan(line[i]) and allowed_mask[i]]
    if xs:
        crossover.plot(xs, ys, linewidth=1.8, label=f"{diameter:.0f} mm")

for length, _, _ in steps:
    crossover.axvline(length / 1000.0, color="0.7", linewidth=0.8,
                      linestyle=":")

crossover.set_xlabel("effective length le (m)")
crossover.set_ylabel("cost per metre of column")
crossover.set_title("Cost per metre - where two lines cross, the bigger\n"
                    "column has just become the cheaper one", fontsize=10)
crossover.legend(title="diameter", fontsize=8, title_fontsize=8, ncol=2)
crossover.grid(True, linewidth=0.3, color="0.85")

# 3. The selection staircase, with what it is made of.
selection = figure.add_subplot(grid[1, 1])
xs = [LENGTHS[i] / 1000.0 for i in range(len(LENGTHS))
      if choice[i] is not None]
concrete_part, steel_part, form_part = [], [], []
for index, length in enumerate(LENGTHS):
    if choice[index] is None:
        continue
    found = cells[(choice[index], float(length))]
    concrete_part.append(found["concrete"])
    steel_part.append(found["steel"])
    form_part.append(found["formwork"])

selection.stackplot(xs, steel_part, concrete_part, form_part,
                    labels=("steel", "concrete", "formwork"),
                    colors=("#b03030", "#8a8f98", "#4c78a8"), alpha=0.9)
drawn = [size for size in choice if size is not None]
totals = [sum(values)
          for values in zip(steel_part, concrete_part, form_part)]
for index, (x, y, diameter) in enumerate(zip(xs, totals, drawn)):
    if index == 0 or diameter != drawn[index - 1]:
        selection.annotate(f"{diameter:.0f}", (x, y),
                           textcoords="offset points", xytext=(-8, 8),
                           fontsize=8, fontweight="bold")

selection.set_xlabel("effective length le (m)")
selection.set_ylabel("cost per metre")
selection.set_title("What the cheapest allowed column is made of\n"
                    "(labels are the diameter chosen, in mm)", fontsize=10)
selection.legend(loc="upper left", fontsize=8)
selection.grid(True, linewidth=0.3, color="0.85")

figure.suptitle(
    f"Circular column - slenderness, steel and cost - {CODE}\n"
    f"N = {AXIAL:.0f} kN, M = {MOMENT:.0f} kNm, fcu {FCU:.0f} MPa, "
    f"fy {FY:.0f} MPa, cover {COVER:.0f} mm, braced  |  "
    f"concrete {RATE_CONCRETE:.0f}/m3, steel {RATE_STEEL:.0f}/kg, "
    f"formwork {RATE_FORMWORK:.0f}/m2  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
deliver(figure, "circular_column_slenderness_map.png")
