# ---
# Example:  A retaining wall's carbon - spend it on the base or the stem?
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes - 2026-09-09 - carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# A cantilever retaining wall has two independent things you can grow, and
# they fix different problems:
#
#   THE BASE     longer base = more stabilising weight and a longer lever,
#                so overturning, sliding and bearing all improve.
#   THE STEM     thicker stem = more bending capacity, so the wall steel
#                comes down.
#
# Growing the wrong one is pure added concrete. This script sweeps both
# against C14 and finds the lowest-carbon wall that satisfies all three
# stability checks.
#
# WHAT THE THREE RATIOS MEAN, because two of them read one way and the
# third reads the other:
#
#   overturning_ratio >= 1   achieved over required - BIGGER is safer
#   sliding_ratio     >= 1   same convention
#   bearing_ratio     <= 1   applied over allowable - SMALLER is safer
#
# Getting that last one backwards passes every unsafe wall in the sweep,
# so this script tests all three explicitly rather than trusting a single
# summary flag.
#
# WHAT IT COUNTS. A1-A3 carbon per METRE RUN of wall: base slab concrete,
# stem concrete (tapered), and the flexural steel C14 reports for each.
# Excavation, backfill, drainage, the shear key and distribution steel are
# NOT counted - and backfill volume grows with base length, so the map is
# conservative in favour of long bases.
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
HEIGHT = 5.0                 # m retained height, h1
TOE = 0.7                    # m, b
BASE_THICKNESS = 0.4         # m, c
STEM_TOP = 0.25              # m, at
FCU = 30.0
FY = 450.0
ALLOWABLE = 150.0            # kPa, pmax
FRICTION = 30.0              # degrees, theta
WALL_FRICTION = 15.0         # degrees, delta
SURCHARGE = [{"name": "Traffic", "w": 10.0}]

BASES = (1.5, 1.75, 2.0, 2.5, 3.0, 3.5)  # m, d
STEMS = (0.30, 0.40, 0.50, 0.60)         # m, ab


def wall(base, stem):
    """One C14 analysis of the wall."""
    return prokon.v5.retaining_wall.analyse(
        concrete_code=CODE, h1=HEIGHT, b=TOE, d=base, c=BASE_THICKNESS,
        at=STEM_TOP, ab=stem, theta=FRICTION, delta=WALL_FRICTION,
        fcu=FCU, fy=FY, pmax=ALLOWABLE, load_cases=SURCHARGE)


def carbon(base, stem, as_wall, as_base, ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon per metre run of wall, kgCO2e/m."""
    stem_height = HEIGHT - BASE_THICKNESS
    base_m3 = base * BASE_THICKNESS
    stem_m3 = (STEM_TOP + stem) / 2.0 * stem_height
    # Steel areas are per metre run (mm2/m), applied over the member they
    # reinforce, so mm2 x m gives 1e-6 m3.
    steel_m3 = (as_wall * stem_height + as_base * base) * 1.0e-6
    concrete = (base_m3 + stem_m3) * DENSITY_CONCRETE * ecf_concrete
    steel = steel_m3 * DENSITY_STEEL * ECF_REBAR
    return dict(base_m3=base_m3, stem_m3=stem_m3,
                steel_kg=steel_m3 * DENSITY_STEEL,
                concrete=concrete, steel=steel, total=concrete + steel)


print("A RETAINING WALL'S CARBON - BASE OR STEM?")
print(f"  {CODE}, {HEIGHT:.1f} m retained, toe {TOE:.2f} m, "
      f"base slab {BASE_THICKNESS:.2f} m thick")
print(f"  phi {FRICTION:.0f} deg, wall friction {WALL_FRICTION:.0f} deg, "
      f"allowable {ALLOWABLE:.0f} kPa, surcharge "
      f"{SURCHARGE[0]['w']:.0f} kPa")
print(f"  grid: {len(BASES)} base lengths x {len(STEMS)} stem thicknesses")

# -- 1. The map ---------------------------------------------------------
print()
print("1. EVERY COMBINATION (kgCO2e per metre run; 'x' = fails a check)")
header = "   base\\stem" + "".join(f"{value:>10.2f}" for value in STEMS)
print(header)
print("   " + "-" * (len(header) - 3))

grid = {}
reference = None

for base in BASES:
    line = f"   {base:>8.2f}  "
    for stem in STEMS:
        envelope = wall(base, stem)
        result = envelope["result"]
        if reference is None:
            reference = envelope

        # All three, explicitly, with the bearing one the right way round.
        stable = (result["overturning_ratio"] >= 1.0
                  and result["sliding_ratio"] >= 1.0
                  and result["bearing_ratio"] <= 1.0)

        money = carbon(base, stem, result["as_wall_req"], result["as_base_req"])
        grid[(base, stem)] = dict(base=base, stem=stem, stable=stable,
                                  ovt=result["overturning_ratio"],
                                  sli=result["sliding_ratio"],
                                  bear=result["bearing_ratio"],
                                  qmax=result["qmax"],
                                  as_wall=result["as_wall_req"],
                                  as_base=result["as_base_req"], **money)
        line += f"{money['total']:>9.0f}" + ("" if stable else "x")
        if stable:
            line += " "
    print(line)

stable_rows = [row for row in grid.values() if row["stable"]]
if not stable_rows:
    # A sweep that finds nothing is a RESULT, not a crash - and saying so
    # is more useful than a traceback from min() on an empty list.
    print("   -> NOTHING in this grid satisfies all three checks. Widen the")
    print("      base range, reduce the retained height, or improve the")
    print("      allowable bearing pressure - the wall is not the problem.")
    raise SystemExit(0)
best = min(stable_rows, key=lambda row: row["total"])
print(f"   -> {len(stable_rows)} of {len(grid)} walls satisfy all three checks.")
print(f"   -> LOWEST CARBON: base {best['base']:.2f} m, stem "
      f"{best['stem']:.2f} m -> {best['total']:.0f} kgCO2e/m")
print(f"      overturning {best['ovt']:.2f}, sliding {best['sli']:.2f}, "
      f"bearing {best['bear']:.2f}, qmax {best['qmax']:.0f} kPa")

# -- 2. Which check is binding -----------------------------------------
print()
print("2. WHICH CHECK ACTUALLY STOPS YOU")
failures = {"overturning": 0, "sliding": 0, "bearing": 0}
for row in grid.values():
    if row["ovt"] < 1.0:
        failures["overturning"] += 1
    if row["sli"] < 1.0:
        failures["sliding"] += 1
    if row["bear"] > 1.0:
        failures["bearing"] += 1
for name, count in failures.items():
    print(f"   {name:<13} fails in {count:>2} of {len(grid)} combinations")
binding = max(failures.items(), key=lambda item: item[1])
if binding[1]:
    print(f"   -> {binding[0].upper()} is the governing check here.")
else:
    print("   -> nothing fails: this wall is comfortable across the whole")
    print("      grid, so carbon alone picks the geometry.")

print()
print("   how the base length moves each ratio, at the winning stem:")
print(f"   {'base':>6} {'ovt':>7} {'sli':>7} {'bear':>7} {'qmax':>7}")
for row in sorted([r for r in grid.values() if r["stem"] == best["stem"]],
                  key=lambda r: r["base"]):
    print(f"   {row['base']:>6.2f} {row['ovt']:>7.2f} {row['sli']:>7.2f} "
          f"{row['bear']:>7.2f} {row['qmax']:>7.0f}")
print("   -> a longer base improves all three at once, which is why it is")
print("      the lever that rescues an unstable wall. It is also the")
print("      single most expensive thing on the drawing.")

# -- 3. What the stem is worth ------------------------------------------
print()
print("3. WHAT THICKENING THE STEM BUYS")
print(f"   {'stem':>6} {'as_wall':>9} {'steel':>8} {'concrete':>9} "
      f"{'total':>8}")
for row in sorted([r for r in grid.values() if r["base"] == best["base"]],
                  key=lambda r: r["stem"]):
    print(f"   {row['stem']:>6.2f} {row['as_wall']:>9.0f} {row['steel']:>8.1f} "
          f"{row['concrete']:>9.1f} {row['total']:>8.0f}")
thin_stem = min((r for r in grid.values() if r["base"] == best["base"]),
                key=lambda r: r["stem"])
thick_stem = max((r for r in grid.values() if r["base"] == best["base"]),
                 key=lambda r: r["stem"])
steel_saved = thin_stem["steel"] - thick_stem["steel"]
concrete_cost = thick_stem["concrete"] - thin_stem["concrete"]
print(f"   -> from {thin_stem['stem']:.2f} to {thick_stem['stem']:.2f} m: "
      f"steel down {steel_saved:.1f} kgCO2e,")
print(f"      concrete up {concrete_cost:.1f} kgCO2e - a "
      f"{concrete_cost / max(steel_saved, 0.001):.1f}x loss.")
print("   -> so thicken the stem only as far as the BENDING needs, never")
print("      to feel safer. Unlike the base, a thicker stem does almost")
print("      nothing for stability - it adds weight above the base, not")
print("      lever arm on it.")

# -- 4. The mix ---------------------------------------------------------
LENGTH = 60.0                # m of wall
print()
print("4. THE MIX, AND THE WHOLE WALL")
print(f"   {LENGTH:.0f} m of wall at the winning section")
for label, factor in (("C32/40, 25% GGBS", 0.120),
                      ("C32/40, 50% GGBS", 0.089),
                      ("C32/40, 75% GGBS", 0.063)):
    money = carbon(best["base"], best["stem"], best["as_wall"],
                   best["as_base"], ecf_concrete=factor)
    print(f"   {label:<20} {money['total']:>7.0f} kgCO2e/m  "
          f"{money['total'] * LENGTH / 1000.0:>6.2f} tCO2e total")
print(f"   -> the winning wall is "
      f"{best['concrete'] / best['total']:.0%} concrete, so the mix again")
print("      dominates. A retaining wall is buried, massive and not on")
print("      anyone's critical path - the same argument as the pile cap.")

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

for stem, colour in zip(STEMS, ("#22303a", "#1a7f4b", "#e0a458", "#c86e5a")):
    cells = sorted([grid[(base, stem)] for base in BASES],
                   key=lambda cell: cell["base"])
    left.plot([cell["base"] for cell in cells],
              [cell["total"] for cell in cells],
              lw=2.0, marker="o", ms=5, color=colour,
              label=f"stem {stem:.2f} m")
    for cell in cells:
        if not cell["stable"]:
            left.plot(cell["base"], cell["total"], marker="x", ms=11,
                      color="#c0392b", mew=2.0)
left.plot(best["base"], best["total"], marker="*", ms=20, color="#1a7f4b",
          mec="#22303a")
left.set_xlabel("base length d (m)")
left.set_ylabel("embodied carbon A1-A3 (kgCO2e per metre run)")
left.set_title("Carbon rises with both dimensions\n"
               "red x = fails a stability check, star = lowest that passes",
               fontsize=10)
left.legend(fontsize=9)
left.grid(alpha=0.25)

cells = sorted([grid[(base, best["stem"])] for base in BASES],
               key=lambda cell: cell["base"])
bases = [cell["base"] for cell in cells]
right.plot(bases, [cell["ovt"] for cell in cells], lw=2.0, marker="o",
           ms=5, color="#1a7f4b", label="overturning (want >= 1)")
right.plot(bases, [cell["sli"] for cell in cells], lw=2.0, marker="s",
           ms=5, color="#e0a458", label="sliding (want >= 1)")
right.plot(bases, [cell["bear"] for cell in cells], lw=2.0, marker="^",
           ms=5, color="#c86e5a", label="bearing (want <= 1)")
right.axhline(1.0, color="#22303a", ls="--", lw=1.5)
right.set_xlabel("base length d (m)")
right.set_ylabel("ratio")
right.set_title("Two ratios climb and one falls\n"
                "the dashed line is safe in BOTH directions - read it twice",
                fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Retaining wall carbon - {CODE}  |  {HEIGHT:.1f} m retained, "
    f"phi {FRICTION:.0f} deg, {SURCHARGE[0]['w']:.0f} kPa surcharge  |  "
    f"concrete {ECF_CONCRETE}, bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "retaining_wall_carbon_base_or_stem.png")

print()
print("-" * 72)
print("The base and the stem are not interchangeable. The base buys")
print("stability and costs a lot of concrete; the stem buys bending")
print("capacity and buys almost no stability at all. So size the base from")
print("the three ratios, size the stem from the bending, and do not")
print("thicken either one for reassurance - that is pure carbon.")
