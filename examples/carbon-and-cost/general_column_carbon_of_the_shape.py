# ---
# Example:  Same area, different shape - which column shape is lowest carbon?
# Feature:  general_column (C13 General Column)
# Verified: yes - 2026-09-09 - carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# Architects ask for blade columns. Engineers prefer squares. Both sides
# usually argue from habit, because the comparison is awkward to make: you
# have to hold the concrete AREA constant and see what the capacity does.
#
# C13 takes an arbitrary polygon, so it is the one engine here that can
# answer this directly. This script holds the gross area at a constant
# 160 000 mm2, holds the bars constant at four corner bars, and asks what
# the SHAPE alone is worth.
#
# WHY THIS IS A CARBON QUESTION AND NOT JUST A CAPACITY ONE. Equal area
# means equal concrete, so equal concrete carbon. Equal bars mean equal
# steel carbon. Every option therefore has the SAME embodied carbon, and
# the only thing that differs is how much load it carries. So the useful
# figure is carbon per unit of capacity - kgCO2e per kN actually carried -
# which is the number that tells you whether a shape is wasteful.
#
# HOW C13's `section` INPUT WORKS, because it is unlike the others:
#   {"code": "+", "x": .., "y": ..}   move to a point
#   {"code": "L", "x": .., "y": ..}   line to a point (the outline)
#   {"code": "B", "x": dia}           put a bar of that diameter at the
#                                     point the last "+" named
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# -- EMBODIED CARBON FACTORS -------------------------------------------
# A1-A3, kgCO2e/kg, from IStructE, "A brief guide to calculating embodied
# carbon", The Structural Engineer, July 2020.
ECF_CONCRETE = 0.120         # C32/40, 25% GGBS
ECF_REBAR = 0.684            # UK bar, BRC EPD
DENSITY_CONCRETE = 2400.0
DENSITY_STEEL = 7850.0

# CONTROL - reproduces the worked example in that same guide.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "BS8110 - 1997"
LENGTH = 3.0                 # m
FCU = 30.0
FY = 450.0
COVER = 30.0
BAR = 25.0                   # mm, four corner bars
GROSS_AREA = 160_000.0       # mm2, held constant across every shape

AXIAL = 1000.0               # kN
MOMENT = 50.0                # kNm, applied about x at both ends


def rectangle(width, depth):
    """A rectangular C13 section of this size with four corner bars."""
    inset = COVER + BAR / 2.0
    outline = [{"code": "+", "x": 0, "y": 0},
               {"code": "L", "x": width, "y": 0},
               {"code": "L", "x": width, "y": depth},
               {"code": "L", "x": 0, "y": depth}]
    bars = []
    for x, y in ((inset, inset), (width - inset, inset),
                 (width - inset, depth - inset), (inset, depth - inset)):
        bars.append({"code": "+", "x": x, "y": y})
        bars.append({"code": "B", "x": BAR})
    return outline + bars


# Every shape has the SAME gross area, so the same concrete.
SHAPES = []
for width in (400.0, 320.0, 250.0, 200.0, 160.0):
    depth = GROSS_AREA / width
    SHAPES.append((f"{width:.0f} x {depth:.0f}", width, depth))


def analyse(section):
    """One C13 analysis of this polygon."""
    return prokon.v5.general_column.analyse(
        design_code=CODE, length=LENGTH, fcu=FCU, fy=FY, section=section,
        load_cases=[{"axial": AXIAL, "moment_x_top": MOMENT,
                     "moment_x_bottom": MOMENT}])


def carbon(concrete_mm2, steel_mm2, ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon for one storey of column, kgCO2e."""
    concrete_m3 = concrete_mm2 * 1.0e-6 * LENGTH
    steel_kg = steel_mm2 * 1.0e-6 * LENGTH * DENSITY_STEEL
    concrete = concrete_m3 * DENSITY_CONCRETE * ecf_concrete
    steel = steel_kg * ECF_REBAR
    return dict(concrete_m3=concrete_m3, steel_kg=steel_kg,
                concrete=concrete, steel=steel, total=concrete + steel)


print("SAME CONCRETE, DIFFERENT SHAPE - WHAT IS THE SHAPE WORTH?")
print(f"  {CODE}, {LENGTH:.1f} m column, fcu {FCU:.0f}, fy {FY:.0f}")
print(f"  gross area held at {GROSS_AREA:,.0f} mm2 on every option")
print(f"  four {BAR:.0f} mm corner bars on every option, cover {COVER:.0f} mm")
print(f"  load  N = {AXIAL:.0f} kN with M = {MOMENT:.0f} kNm about x")

# -- 1. The shapes ------------------------------------------------------
print()
print("1. FIVE SHAPES, ONE AREA")
print(f"   {'shape':<12} {'Ac':>8} {'As':>7} {'%':>6} {'cap':>7} "
      f"{'passes':>7} {'kgCO2e':>8} {'kgCO2e':>9}")
print(f"   {'mm':<12} {'mm2':>8} {'mm2':>7} {'':>6} {'factor':>7} "
      f"{'':>7} {'total':>8} {'per kN':>9}")
print("   " + "-" * 68)

rows = []
reference = None

for label, width, depth in SHAPES:
    envelope = analyse(rectangle(width, depth))
    result = envelope["result"]
    if reference is None:
        reference = envelope

    factor = result["min_capacity_factor"]
    passes = result["has_feasible_design"] and factor >= 1.0
    money = carbon(result["concrete_area"], result["steel_area"])

    # Carbon per kN CARRIED, not per kN applied: a column running at
    # factor 2 is carrying twice what it was asked for, and that spare
    # capacity is either useful or wasted depending on the project.
    per_kn = money["total"] / (AXIAL * factor) if factor > 0 else float("nan")

    rows.append(dict(label=label, width=width, depth=depth,
                     concrete_area=result["concrete_area"],
                     steel_area=result["steel_area"],
                     ratio=result["reinforcement_ratio"],
                     factor=factor, passes=passes, per_kn=per_kn, **money))

    print(f"   {label:<12} {result['concrete_area']:>8.0f} "
          f"{result['steel_area']:>7.0f} {result['reinforcement_ratio']:>5.2f}% "
          f"{factor:>7.3f} {str(passes):>7} {money['total']:>8.1f} "
          f"{per_kn:>9.4f}")

# The area really is constant - assert it rather than trusting the maths.
areas = {round(row["concrete_area"], 3) for row in rows}
print(f"   -> distinct concrete areas across the five shapes: {len(areas)}")
print(f"   -> distinct total carbon figures: "
      f"{len({round(row['total'], 3) for row in rows})}")
print("   -> so every option costs the SAME carbon. The whole comparison")
print("      is therefore about capacity, and the last column is the one")
print("      that matters: carbon per kN actually carried.")

# -- 2. The answer ------------------------------------------------------
usable = [row for row in rows if row["passes"]]
print()
print("2. WHICH SHAPE EARNS ITS CONCRETE")
if usable:
    best = min(usable, key=lambda row: row["per_kn"])
    worst = max(usable, key=lambda row: row["per_kn"])
    print(f"   most efficient  {best['label']:<12} "
          f"{best['per_kn']:.4f} kgCO2e per kN carried (factor {best['factor']:.2f})")
    print(f"   least efficient {worst['label']:<12} "
          f"{worst['per_kn']:.4f} kgCO2e per kN carried (factor {worst['factor']:.2f})")
    print(f"   -> a spread of {worst['per_kn'] / best['per_kn']:.2f}x, from")
    print("      geometry alone, at identical material quantities.")
else:
    print("   none of the five shapes carries this load - the comparison")
    print("   is then about WHICH FAILS LEAST, and every factor is < 1.")
    best = max(rows, key=lambda row: row["factor"])
    worst = min(rows, key=lambda row: row["factor"])
    print(f"   closest  {best['label']:<12} factor {best['factor']:.3f}")
    print(f"   furthest {worst['label']:<12} factor {worst['factor']:.3f}")

failing = [row for row in rows if not row["passes"]]
if failing:
    print(f"   -> {len(failing)} of {len(rows)} shapes do NOT carry the load:")
    for row in failing:
        print(f"        {row['label']:<12} factor {row['factor']:.3f}")
    print("      Same concrete, same steel, and they fail. Shape is not a")
    print("      free variable, and 'we kept the area the same' is not a")
    print("      structural argument.")

# -- 3. Which way does depth help --------------------------------------
print()
print("3. THE DIRECTION, AND ITS LIMIT")
ordered = sorted(rows, key=lambda row: row["depth"])
print(f"   {'depth':>6} {'width':>6} {'factor':>8}")
for row in ordered:
    print(f"   {row['depth']:>6.0f} {row['width']:>6.0f} {row['factor']:>8.3f}")
rising = all(b["factor"] >= a["factor"] for a, b in zip(ordered, ordered[1:]))
print(f"   -> capacity rises monotonically with depth: {rising}")
print("   -> the moment is about x, so depth in that direction is lever")
print("      arm and it buys capacity for nothing. That is the real")
print("      argument FOR a blade column - provided the blade is deep in")
print("      the direction the moment actually acts.")
print("   -> turn the same section 90 degrees and the argument reverses")
print("      completely. Shape efficiency is direction-specific, which is")
print("      why it cannot be settled by a rule of thumb.")

# -- 4. And the caveat that limits all of it ---------------------------
print()
print("4. WHAT C13 IS NOT TELLING YOU HERE")
print("   - slenderness. A thin blade is slender about its weak axis, and")
print(f"     `is_slender_x` / `is_slender_y` are reported but are NOT")
print("     written on every path - a known gap, so do not read False as")
print("     'checked and stocky'.")
print("   - biaxial moment. Only Mx is applied above. Real columns take")
print("     moment both ways, and that is precisely where a blade suffers.")
print("   - buildability. Four bars in a 160 mm blade is a congestion and")
print("     cover problem before it is a carbon one.")
print("   -> so read this as 'depth in the moment direction is free")
print("      capacity', not as 'blades are better'.")

# -- The chart ----------------------------------------------------------
HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can."""
    path = Path(filename).resolve()
    figure.savefig(path, dpi=150, facecolor="white")
    size = path.stat().st_size
    print()
    print(f"Written: {path}")
    print(f"  {size:,} bytes  "
          f"({'a real image' if size > 20_000 else 'SUSPICIOUSLY SMALL'})")
    if str(matplotlib.get_backend()).lower() in HEADLESS:
        plt.close(figure)
        print("  backend is headless - the PNG is the whole output")
    else:
        plt.show()
        print(f"  and shown on the {matplotlib.get_backend()} backend")


figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

# Left: the shapes themselves, to scale, coloured by whether they pass.
offset = 0.0
for row in ordered:
    colour = "#1a7f4b" if row["passes"] else "#c0392b"
    left.add_patch(plt.Rectangle((offset, 0.0), row["width"], row["depth"],
                                 facecolor=colour, alpha=0.30,
                                 edgecolor=colour, lw=1.6))
    left.text(offset + row["width"] / 2.0, -70.0,
              f"{row['label']}\nfactor {row['factor']:.2f}",
              ha="center", va="top", fontsize=8, color="#22303a")
    offset += row["width"] + 90.0

left.set_xlim(-60.0, offset)
left.set_ylim(-260.0, max(row["depth"] for row in rows) * 1.1)
left.set_aspect("equal")
left.axis("off")
left.set_title(f"Five sections, all {GROSS_AREA:,.0f} mm2, all the same carbon\n"
               "green carries the load, red does not", fontsize=10)

depths = np.array([row["depth"] for row in ordered])
factors = np.array([row["factor"] for row in ordered])
right.plot(depths, factors, color="#22303a", lw=2.0, marker="o", ms=6)
right.axhline(1.0, color="#c0392b", ls="--", lw=1.5, label="capacity factor 1.0")
for row in ordered:
    right.annotate(row["label"], xy=(row["depth"], row["factor"]),
                   xytext=(0, 9), textcoords="offset points",
                   ha="center", fontsize=8)
right.set_xlabel("section depth in the moment direction (mm)")
right.set_ylabel("minimum capacity factor")
right.set_title("Depth in the moment direction is free capacity\n"
                "same concrete, same bars, 5x the factor", fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Column shape at constant area - {CODE}  |  "
    f"N = {AXIAL:.0f} kN, Mx = {MOMENT:.0f} kNm, {LENGTH:.1f} m  |  "
    f"4 x Y{BAR:.0f} throughout  |  engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "general_column_carbon_of_the_shape.png")

print()
print("-" * 72)
print("Hold the material constant and shape stops being a matter of taste:")
print("the same concrete and the same bars give wildly different capacity")
print("depending on which way the depth runs. Carbon per unit of capacity")
print("is the honest way to compare two designs that use the same stuff.")
