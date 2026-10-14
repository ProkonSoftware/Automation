# ---
# Example:  The feasible region of a pad footing - four checks, one cost map
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes - 2026-09-04 - the golden 2.5 x 2.5 x 0.6 m footing reproduces its pinned sls.pm and vcx; every footing in the map measured on prokon-automation.exe
# ---
# A pad footing has two dimensions to choose - how wide, how deep - and
# four checks fighting over them:
#
#   BEARING       wants it WIDE
#   ONE-WAY SHEAR wants it DEEP
#   PUNCHING      wants it DEEP
#   OVERTURNING   wants it WIDE and HEAVY
#
# Any two of them can be satisfied by walking in one direction, and that
# is why footing sizing by hand tends to circle. Plotted, it stops being
# a circle: each check is a curve on the (plan, depth) plane, the four
# curves cut out a feasible region, and the cheapest footing sits on its
# boundary - usually on a corner where two checks meet exactly.
#
# ⚠ AND TWO OF THE CHECKS CAN SILENTLY NOT RUN. When the critical section
# or the punching perimeter falls outside the footing, C15 publishes
# vp = vcp = 0 and vx = 0 - and "0 <= 0" reads as a pass. Measured on this
# grid: it happens on a large fraction of the deep footings. The script
# tests vcp > 0 and vx > 0 FIRST and paints those cells as "not checked"
# rather than green.
#
# The last panel is free: the bearing pressure C15 reports does not depend
# on the allowable you told it, so one sweep can be re-read against six
# different allowable pressures without a single extra engine call.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

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


# -- The footing --------------------------------------------------------
CODE = "BS8110 - 1997"
COLUMN = 0.45             # m square
COVER_SOIL = 0.5          # m of soil over the footing
FCU = 30.0
FY = 450.0
SERVICE_LOAD = 1400.0     # kN
HORIZONTAL = 60.0         # kN
MOMENT = 50.0             # kNm
LOAD_FACTOR = 1.4
ALLOWABLE = 200.0         # kPa, the design value
ALLOWABLES = (120.0, 150.0, 200.0, 300.0, 450.0, 700.0)

SF_OVERTURNING = 2.0
SF_SLIDING = 1.5

RATE_CONCRETE = 1750.0    # per m3
RATE_EXCAVATION = 190.0   # per m3 dug and backfilled
RATE_STEEL = 24.0         # per kg
RATE_FORMWORK = 210.0     # per m2 of side shutter
DENSITY_STEEL = 7850.0

PLANS = np.arange(1.5, 4.51, 0.25)        # 13 m
DEPTHS = np.arange(0.30, 1.21, 0.10)      # 10 m

# -- Two numbers that decide how long this script takes -----------------
# The sweep below is Cartesian, so its cost is the product of the two step
# sizes above, and every point is a separate engine process at about
# 0.4 s. Choose the steps for the chart you want to READ - halving a step
# doubles the wait.
#
# Then bound the wait itself. timeout_seconds is PER CALL, it defaults to
# 120 s, and these calls take 0.4 s - so one stuck call could cost more
# than the whole sweep. Sized here at many times what a healthy call takes
# and still far below what this whole script costs: generous, and bounded.
prokon.v5.timeout_seconds = 30.0

print("THE FEASIBLE REGION OF A PAD FOOTING")
print(f"  {CODE}, {COLUMN * 1000:.0f} mm square column, "
      f"{COVER_SOIL:.1f} m of cover soil")
print(f"  service load {SERVICE_LOAD:.0f} kN, H {HORIZONTAL:.0f} kN, "
      f"M {MOMENT:.0f} kNm, load factor {LOAD_FACTOR}")
print(f"  allowable bearing {ALLOWABLE:.0f} kPa")
print(f"  grid: {len(PLANS)} plan sizes x {len(DEPTHS)} depths "
      f"= {len(PLANS) * len(DEPTHS)} engine calls")

# -- The anchor ---------------------------------------------------------
PINNED_PM = 133.98908218356328
PINNED_VCX = 0.3568429018580138
envelope = prokon.v5.pad_footing.analyse(
    design_code=CODE, a=2.5, b=2.5, yf=0.6, z=0.5,
    c1=0.4, d1=0.4, e1=0.0, f1=0.0, fcu=30.0, fy=450.0,
    allowable_bearing_pressure=200.0,
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
    bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
    bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
    load_cases=[{"name": "LC1", "pa1": 600.0, "hx1": 30.0,
                 "mx1": 20.0, "lf1": 1.4}])
anchor = envelope["result"]
exact = (anchor["max_bearing_pressure_sls"] == PINNED_PM
         and anchor["critical_uls"]["shear"]["vcx"] == PINNED_VCX)
print("\n  anchor: the golden 2.5 x 2.5 x 0.6 m footing under 600 kN")
print(f"    sls pm {anchor['max_bearing_pressure_sls']!r}   "
      f"pinned {PINNED_PM!r}")
print(f"    vcx    {anchor['critical_uls']['shear']['vcx']!r}   "
      f"pinned {PINNED_VCX!r}")
print(f"    -> {'EXACT on both' if exact else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")

CHECKS = ("bearing", "one-way shear", "punching", "overturning", "sliding")


# invalid_input and no_solution say something about the FOOTING - this
# size has no answer - and belong on the map as a hole. Every other
# category says something about the RUN, and a map quietly missing those
# points would be a lie. So they are counted by category and printed.
NO_ANSWER_HERE = ("invalid_input", "no_solution")
not_answered = []


def footing(plan, depth):
    """One footing: the utilisation of every check, and what it costs."""
    try:
        result = prokon.v5.pad_footing.analyse(
            design_code=CODE, a=plan, b=plan, yf=depth, z=COVER_SOIL,
            c1=COLUMN, d1=COLUMN, e1=0.0, f1=0.0,
            fcu=FCU, fy=FY, allowable_bearing_pressure=ALLOWABLE,
            bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
            bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
            bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
            bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
            load_cases=[{"name": "LC", "pa1": SERVICE_LOAD,
                         "hx1": HORIZONTAL, "mx1": MOMENT,
                         "lf1": LOAD_FACTOR}])["result"]
    except prokon.v5.ProkonError as refusal:
        if refusal.category not in NO_ANSWER_HERE:
            not_answered.append("{0}/{1}".format(refusal.category,
                                                 refusal.code))
        return None

    critical = result["critical_uls"]
    shear = critical["shear"]
    sls = critical["sls"]

    # ⚠ A zero here is "the check never ran", not "the check passed".
    # vcp = 0 means the punching perimeter did not fit inside the footing;
    # vx = 0 means the one-way critical section fell outside it. Reporting
    # them as None keeps "not checked" distinct from "0 <= 0".
    one_way = None
    if shear["vcx"] and shear["vx"] and shear["vcy"] and shear["vy"]:
        one_way = max(shear["vx"] / shear["vcx"], shear["vy"] / shear["vcy"])
    punching = None
    if shear["vcp"] and shear["vp"]:
        punching = shear["vp"] / shear["vcp"]

    steel = result["load_cases"][0]["reinforcement"]
    steel_kg = ((steel["as_x"] + steel["as_y"]) * plan * plan
                / 1e6 * DENSITY_STEEL)
    concrete = plan * plan * depth
    excavation = plan * plan * (depth + COVER_SOIL)
    formwork = 4.0 * plan * depth

    return {
        "utilisation": {
            "bearing": result["max_bearing_pressure_sls"] / ALLOWABLE,
            "one-way shear": one_way,
            "punching": punching,
            "overturning": (SF_OVERTURNING / sls["sf_ovt"]
                            if sls["sf_ovt"] else None),
            "sliding": (SF_SLIDING / sls["sf_sliding"]
                        if sls["sf_sliding"] else None),
        },
        "pressure": result["max_bearing_pressure_sls"],
        "cost": (concrete * RATE_CONCRETE + excavation * RATE_EXCAVATION
                 + steel_kg * RATE_STEEL + formwork * RATE_FORMWORK),
        "concrete": concrete * RATE_CONCRETE,
        "excavation": excavation * RATE_EXCAVATION,
        "steel": steel_kg * RATE_STEEL,
        "formwork": formwork * RATE_FORMWORK,
        "steel_kg": steel_kg,
    }


# -- Sweep --------------------------------------------------------------
cost = np.full((len(DEPTHS), len(PLANS)), np.nan)
pressure = np.full_like(cost, np.nan)
worst = np.full_like(cost, np.nan)
governing = np.full_like(cost, np.nan)
unchecked = np.zeros_like(cost)
surfaces = {name: np.full_like(cost, np.nan) for name in CHECKS}
cells = {}
skipped = {"one-way shear": 0, "punching": 0}

for column, plan in enumerate(PLANS):
    for row, depth in enumerate(DEPTHS):
        found = footing(float(plan), float(depth))
        if found is None:
            continue
        cells[(float(plan), float(depth))] = found
        cost[row, column] = found["cost"]
        pressure[row, column] = found["pressure"]
        for name in CHECKS:
            value = found["utilisation"][name]
            if value is None:
                if name in skipped:
                    skipped[name] += 1
                continue
            surfaces[name][row, column] = value
        real = {name: value
                for name, value in found["utilisation"].items()
                if value is not None}
        if len(real) < len(CHECKS):
            unchecked[row, column] = 1.0
        if real:
            top = max(real, key=real.get)
            worst[row, column] = real[top]
            governing[row, column] = CHECKS.index(top)

answered = int(np.count_nonzero(~np.isnan(cost)))
print(f"\nSWEPT   {answered} footings answered")
if not_answered:
    print(f"   {len(not_answered)} call(s) did not answer for a reason that "
          f"is NOT about")
    print("      the footing: " + ", ".join(sorted(set(not_answered))))
    print("      Those are holes punched in the map by the RUN. Read them")
    print("      before you read the map.")
print("\nTHE CHECKS THAT DID NOT RUN")
for name, count in skipped.items():
    print(f"   {name:>14}: not checked on {count} of {answered} footings")
print("   -> every one of those publishes a ZERO, and a script comparing")
print("      demand against capacity reads 0 <= 0 and calls it a pass.")
print("      Test the CAPACITY for zero before you divide by it.")

# -- The feasible region and the cheapest footing on it -----------------
feasible = (worst <= 1.0) & (unchecked == 0.0)
count = int(np.count_nonzero(feasible))
print(f"\nFEASIBLE   {count} of {answered} footings pass every check that "
      f"ran,")
print(f"           with none of the five skipped")

masked = np.where(feasible, cost, np.nan)
best_index = np.unravel_index(np.nanargmin(masked), masked.shape)
best_plan = float(PLANS[best_index[1]])
best_depth = float(DEPTHS[best_index[0]])
best = cells[(best_plan, best_depth)]
print(f"\nCHEAPEST FEASIBLE   {best_plan:.2f} x {best_plan:.2f} x "
      f"{best_depth:.2f} m at {best['cost']:.0f}")
print(f"   concrete {best['concrete']:7.0f}   excavation "
      f"{best['excavation']:7.0f}   steel {best['steel']:7.0f}   "
      f"formwork {best['formwork']:7.0f}")
print(f"   {'check':>14} {'utilisation':>12}")
for name in CHECKS:
    value = best["utilisation"][name]
    print(f"   {name:>14} "
          + (f"{'not checked':>12}" if value is None else f"{value:>12.3f}")
          + ("   <- governs" if value is not None
             and value == max(v for v in best["utilisation"].values()
                              if v is not None) else ""))
print("   -> the optimum sits ON the boundary, with one check at almost")
print("      exactly 1.0. That is what an optimum looks like: any cheaper")
print("      footing has already failed something.")

# -- The allowable pressure, re-read for free ---------------------------
# C15 derives NOTHING from allowable_bearing_pressure - the comparison is
# the caller's, every time - so the same sweep answers six ground
# conditions without another engine call.
#
# CONTROL: if the reported pressure DID depend on the allowable, this
# re-read would be wrong. So one cell is re-run with a different allowable
# and the two pressures compared with ==.
probe = footing(2.5, 0.6)
try:
    alternate = prokon.v5.pad_footing.analyse(
    design_code=CODE, a=2.5, b=2.5, yf=0.6, z=COVER_SOIL,
    c1=COLUMN, d1=COLUMN, e1=0.0, f1=0.0, fcu=FCU, fy=FY,
    allowable_bearing_pressure=ALLOWABLE * 3.0,
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
    bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
    bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
        load_cases=[{"name": "LC", "pa1": SERVICE_LOAD, "hx1": HORIZONTAL,
                     "mx1": MOMENT, "lf1": LOAD_FACTOR}])["result"]
except prokon.v5.ProkonError as refusal:
    alternate = None
    not_answered.append("{0}/{1}".format(refusal.category, refusal.code))
print(f"\nRE-READING THE SWEEP AGAINST SIX GROUND CONDITIONS")
# The control needs BOTH footings. Saying "sound" on the strength of a
# comparison that did not happen is the one thing this section must not do.
if probe is None or alternate is None:
    print("   control: NOT RUN - one of the two footings was not answered,")
    print("     so the re-read below is UNVERIFIED on this run:")
    print("     " + ", ".join(sorted(set(not_answered))))
else:
    same = probe["pressure"] == alternate["max_bearing_pressure_sls"]
    print(f"   control: the same footing with the allowable tripled reports")
    print(f"     {probe['pressure']!r} against "
          f"{alternate['max_bearing_pressure_sls']!r}")
    print(f"     -> {'IDENTICAL, so the re-read below is sound' if same else 'DIFFERENT - the re-read below would be WRONG'}")

print(f"\n   {'allowable':>10} {'cheapest footing':>20} {'cost':>9} "
      f"{'governing check':>16}")
sizing = []
for allowable in ALLOWABLES:
    bearing = pressure / allowable
    others = np.fmax.reduce([surfaces[name] for name in CHECKS[1:]])
    combined = np.fmax(bearing, np.nan_to_num(others, nan=0.0))
    ok = (combined <= 1.0) & (unchecked == 0.0) & ~np.isnan(cost)
    if not np.any(ok):
        print(f"   {allowable:>10.0f} {'nothing on the grid':>20}")
        continue
    trial = np.where(ok, cost, np.nan)
    where = np.unravel_index(np.nanargmin(trial), trial.shape)
    plan = float(PLANS[where[1]])
    depth = float(DEPTHS[where[0]])
    found = cells[(plan, depth)]
    utilisations = dict(found["utilisation"])
    utilisations["bearing"] = found["pressure"] / allowable
    real = {name: value for name, value in utilisations.items()
            if value is not None}
    top = max(real, key=real.get)
    sizing.append((allowable, plan, depth, float(trial[where]), top))
    print(f"   {allowable:>10.0f} {plan:>8.2f} x {depth:<9.2f} "
          f"{trial[where]:>9.0f} {top:>16}")

# ⚠ Read the table before summarising it. The governing check does not
# switch over once and stay switched - it ALTERNATES, because improving
# the ground lets the footing shrink, and a smaller footing changes which
# concrete check is worst. What DOES settle is the size.
if sizing:
    # Walk back from the best ground while the SIZE is unchanged. A plain
    # equality filter over the whole list would also pick up an earlier
    # row that happened to match, and "it stops changing from here" would
    # then be false.
    settled = [sizing[-1]]
    for row in reversed(sizing[:-1]):
        if (row[1], row[2]) != (sizing[-1][1], sizing[-1][2]):
            break
        settled.insert(0, row)
    checks_used = {row[4] for row in sizing}
    print(f"   -> {len(checks_used)} different checks govern across the six "
          f"ground conditions,")
    print("      and they alternate rather than switching over once: a")
    print("      better allowable lets the footing shrink, and a smaller")
    print("      footing changes which concrete check is worst.")
    if len(settled) > 1:
        print(f"   -> what DOES settle is the size. From "
              f"{settled[0][0]:.0f} kPa upward the cheapest footing is")
        print(f"      {settled[0][1]:.2f} x {settled[0][2]:.2f} m at "
              f"{settled[0][3]:.0f} and stops changing - so better ground")
        print("      buys nothing beyond that point, and paying for it is")
        print("      paying for nothing.")

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(2, 2, figsize=(15, 10.5))
figure.patch.set_facecolor("white")
mesh_p, mesh_d = np.meshgrid(PLANS, DEPTHS)

# 1. The cost map with every constraint drawn on it.
chart = axes[0][0]
shade = chart.contourf(mesh_p, mesh_d, np.where(feasible, cost, np.nan),
                       levels=20, cmap="YlGnBu")
figure.colorbar(shade, ax=chart, label="cost of the footing")
chart.contourf(mesh_p, mesh_d, np.where(feasible, np.nan, 1.0),
               levels=[0.5, 1.5], colors=["0.88"])
chart.contourf(mesh_p, mesh_d, np.where(unchecked > 0, 1.0, np.nan),
               levels=[0.5, 1.5], colors="none", hatches=["\\\\"])

palette = {"bearing": "#d62728", "one-way shear": "#1f77b4",
           "punching": "#9467bd", "overturning": "#2ca02c",
           "sliding": "#ff7f0e"}
for name in CHECKS:
    surface = surfaces[name]
    if np.all(np.isnan(surface)) or np.nanmin(surface) > 1.0 \
            or np.nanmax(surface) < 1.0:
        continue
    line = chart.contour(mesh_p, mesh_d, surface, levels=[1.0],
                         colors=palette[name], linewidths=2.2)
    chart.clabel(line, fmt={1.0: name}, fontsize=8)

chart.plot(best_plan, best_depth, marker="*", markersize=22, color="white",
           markeredgecolor="black", zorder=6)
chart.annotate(f"{best_plan:.2f} x {best_depth:.2f} m\n{best['cost']:.0f}",
               (best_plan, best_depth), textcoords="offset points",
               xytext=(12, -4), fontsize=9, fontweight="bold")
chart.set_xlabel("plan size, square (m)")
chart.set_ylabel("footing depth (m)")
chart.set_title("Cost inside the feasible region\n"
                "grey: fails a check    hatched: a check did not run",
                fontsize=10)

# 2. Which check governs, as a categorical map.
which = axes[0][1]
colours = ListedColormap([palette[name] for name in CHECKS])
which.pcolormesh(mesh_p, mesh_d, np.ma.masked_invalid(governing),
                 cmap=colours, vmin=-0.5, vmax=len(CHECKS) - 0.5,
                 shading="nearest")
outline = which.contour(mesh_p, mesh_d, np.where(feasible, 1.0, 0.0),
                        levels=[0.5], colors="black", linewidths=2.4)
which.clabel(outline, fmt={0.5: "feasible"}, fontsize=9)
which.plot(best_plan, best_depth, marker="*", markersize=20, color="white",
           markeredgecolor="black", zorder=6)
which.set_xlabel("plan size, square (m)")
which.set_ylabel("footing depth (m)")
which.set_title("Which of the five checks is worst, everywhere",
                fontsize=10)
which.legend(handles=[Patch(facecolor=palette[name], label=name)
                      for name in CHECKS],
             fontsize=8, loc="upper right", framealpha=0.9)

# 3. What the money buys, along the optimum's depth.
split = axes[1][0]
column_index = list(PLANS).index(best_plan)
depths, concrete_part, dig_part, steel_part, form_part = [], [], [], [], []
for row, depth in enumerate(DEPTHS):
    found = cells.get((best_plan, float(depth)))
    if found is None:
        continue
    depths.append(depth)
    concrete_part.append(found["concrete"])
    dig_part.append(found["excavation"])
    steel_part.append(found["steel"])
    form_part.append(found["formwork"])
split.stackplot(depths, steel_part, concrete_part, dig_part, form_part,
                labels=("steel", "concrete", "excavation", "formwork"),
                colors=("#b03030", "#8a8f98", "#c8a165", "#4c78a8"),
                alpha=0.9)
split.axvline(best_depth, color="black", linestyle="--", linewidth=1.2)
split.annotate("cheapest\nfeasible depth", (best_depth, best["cost"]),
               textcoords="offset points", xytext=(8, 20), fontsize=9)
split.set_xlabel("footing depth (m)")
split.set_ylabel("cost")
split.set_title(f"Where the money goes at {best_plan:.2f} m plan",
                fontsize=10)
split.legend(loc="upper left", fontsize=8)
split.grid(True, linewidth=0.3, color="0.85")

# 4. The ground condition, re-read from the same sweep.
ground = axes[1][1]
if sizing:
    xs = [row[0] for row in sizing]
    plans = [row[1] for row in sizing]
    costs = [row[3] for row in sizing]
    bars = ground.bar([str(int(x)) for x in xs], costs,
                      color=[palette[row[4]] for row in sizing])
    for bar, row in zip(bars, sizing):
        ground.annotate(f"{row[1]:.2f} x {row[2]:.2f} m\n{row[4]}",
                        (bar.get_x() + bar.get_width() / 2,
                         bar.get_height()),
                        ha="center", va="bottom", fontsize=7.5)
    ground.set_ylim(0, max(costs) * 1.28)
ground.set_xlabel("allowable bearing pressure (kPa)")
ground.set_ylabel("cost of the cheapest feasible footing")
ground.set_title("Six ground conditions, one sweep, no extra engine calls\n"
                 "the colour is the check that governs there", fontsize=10)
ground.grid(True, axis="y", linewidth=0.3, color="0.85")

figure.suptitle(
    f"Pad footing feasible region - {CODE}\n"
    f"{COLUMN * 1000:.0f} mm column, P = {SERVICE_LOAD:.0f} kN, "
    f"H = {HORIZONTAL:.0f} kN, M = {MOMENT:.0f} kNm, fcu {FCU:.0f} MPa, "
    f"{COVER_SOIL:.1f} m cover soil  |  "
    f"concrete {RATE_CONCRETE:.0f}/m3, dig {RATE_EXCAVATION:.0f}/m3, "
    f"steel {RATE_STEEL:.0f}/kg  |  engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "pad_footing_feasible_region.png")
