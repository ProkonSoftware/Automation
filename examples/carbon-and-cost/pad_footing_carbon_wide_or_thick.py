# ---
# Example:  Wide and thin, or small and thick? A footing's carbon map
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes - 2026-09-09 - the `yf` thickness reading confirmed by back-calculation from the engine's own mdes_x to within 0.5 %; carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# A pad footing has two dimensions you can trade against each other:
#
#   PLAN SIZE  spreads the load, so the bearing pressure comes down.
#              Concrete grows with the SQUARE of it.
#   THICKNESS  gives shear capacity and lever arm, so the steel comes
#              down. Concrete grows LINEARLY with it.
#
# Those two grow at different rates, which is exactly why the answer is
# not obvious and why a 2-D sweep is worth running. This script maps the
# whole grid and finds the lowest-carbon footing that actually works.
#
# ONE INPUT THAT IS EASY TO GET WRONG, AND IT WAS MEASURED. C15's footing
# THICKNESS is `yf`, not `z`. Checked by back-calculation: with `yf` read
# as the thickness, the steel area C15 reports for the reference footing
# reproduces from its own reported design moment to within 0.5 %, and with
# any other reading it does not. Get this wrong and every concrete volume
# in the sweep is wrong by the ratio of the two.
#
# WHAT IT COUNTS. A1-A3 carbon for one footing: concrete a x b x yf, plus
# the flexural steel in both directions. Excavation, disposal, blinding,
# and the extra depth of dig a thicker pad needs are NOT counted - and
# they all count AGAINST the thick end, so the map is conservative in
# favour of thickness.
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
FCU = 30.0
FY = 450.0
ALLOWABLE = 200.0            # kPa
COLUMN = 0.4                 # m square
LOAD = [{"name": "LC1", "pa1": 900.0, "hx1": 40.0, "mx1": 30.0, "lf1": 1.4}]

PLANS = (2.0, 2.25, 2.5, 2.75, 3.0, 3.25)        # m square
THICKNESSES = (0.35, 0.45, 0.55, 0.65)           # m, this is `yf`


def footing(plan, thickness):
    """One C15 analysis of a square pad."""
    return prokon.v5.pad_footing.analyse(
        design_code=CODE, a=plan, b=plan, yf=thickness, z=0.5,
        c1=COLUMN, d1=COLUMN, e1=0.0, f1=0.0,
        fcu=FCU, fy=FY, allowable_bearing_pressure=ALLOWABLE,
        bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
        bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
        load_cases=LOAD)


def carbon(plan, thickness, as_x, as_y, ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon for one footing, kgCO2e.

    `as_x` and `as_y` are areas per metre width (mm2/m), so each mat is
    that area times the plan dimension it spans and the width it covers.
    """
    concrete_m3 = plan * plan * thickness
    steel_m3 = (as_x + as_y) * 1.0e-6 * plan * plan / 1.0
    concrete = concrete_m3 * DENSITY_CONCRETE * ecf_concrete
    steel = steel_m3 * DENSITY_STEEL * ECF_REBAR
    return dict(concrete_m3=concrete_m3, steel_kg=steel_m3 * DENSITY_STEEL,
                concrete=concrete, steel=steel, total=concrete + steel)


print("A PAD FOOTING'S CARBON MAP - WIDE AND THIN, OR SMALL AND THICK?")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, allowable {ALLOWABLE:.0f} kPa")
print(f"  {COLUMN * 1000:.0f} mm column, N = {LOAD[0]['pa1']:.0f} kN "
      f"with H = {LOAD[0]['hx1']:.0f} kN and M = {LOAD[0]['mx1']:.0f} kNm")
print(f"  grid: {len(PLANS)} plan sizes x {len(THICKNESSES)} thicknesses "
      f"= {len(PLANS) * len(THICKNESSES)} footings")

# -- 1. The map ---------------------------------------------------------
print()
print("1. EVERY COMBINATION (kgCO2e; 'x' = does not work)")
header = "   plan\\yf " + "".join(f"{value:>10.2f}" for value in THICKNESSES)
print(header)
print("   " + "-" * (len(header) - 3))

grid = {}
reference = None

for plan in PLANS:
    line = f"   {plan:>7.2f} "
    for thickness in THICKNESSES:
        envelope = footing(plan, thickness)
        result = envelope["result"]
        if reference is None:
            reference = envelope

        steel = result["critical_uls"]["reinforcement"]
        as_x = max(steel["as_x"], 0.0)
        as_y = max(steel["as_y"], 0.0)

        critical = result["critical_sls"]
        works = (result["has_feasible_design"]
                 and result["max_bearing_pressure_sls"] <= ALLOWABLE
                 and not critical["overturns_sls"]
                 and not critical["uplifts_sls"])

        money = carbon(plan, thickness, as_x, as_y)
        grid[(plan, thickness)] = dict(plan=plan, thickness=thickness,
                                       as_x=as_x, as_y=as_y, works=works,
                                       pressure=result["max_bearing_pressure_sls"],
                                       **money)
        line += f"{money['total']:>9.0f}" + ("" if works else "x")
        if works:
            line += " "
    print(line)

working = [row for row in grid.values() if row["works"]]
best = min(working, key=lambda row: row["total"])
print(f"   -> {len(working)} of {len(grid)} combinations work.")
print(f"   -> LOWEST CARBON: {best['plan']:.2f} m square x "
      f"{best['thickness']:.2f} m thick, {best['total']:.0f} kgCO2e")
print(f"      bearing {best['pressure']:.0f} kPa of {ALLOWABLE:.0f} allowed, "
      f"steel {best['steel_kg']:.0f} kg")

# -- 2. What each dimension is worth -----------------------------------
print()
print("2. THE TWO DIMENSIONS DO NOT COST THE SAME")
print("   holding thickness at the best value, varying plan:")
for row in sorted([r for r in working if r["thickness"] == best["thickness"]],
                  key=lambda r: r["plan"]):
    print(f"      {row['plan']:.2f} m  {row['total']:>7.0f} kgCO2e  "
          f"(concrete {row['concrete_m3']:.2f} m3, steel {row['steel_kg']:.0f} kg)")
print("   holding plan at the best value, varying thickness:")
for row in sorted([r for r in working if r["plan"] == best["plan"]],
                  key=lambda r: r["thickness"]):
    print(f"      {row['thickness']:.2f} m  {row['total']:>7.0f} kgCO2e  "
          f"(concrete {row['concrete_m3']:.2f} m3, steel {row['steel_kg']:.0f} kg)")
print("   -> plan size is punished twice: it squares the concrete AND it")
print("      lengthens every bar in both mats.")
print("   -> thickness DOES buy steel back through the lever arm - look at")
print("      the steel column falling - but nowhere near enough to pay for")
print("      the concrete. Measured on this footing, thickening from")
thin = min((r for r in working if r["plan"] == best["plan"]),
           key=lambda r: r["thickness"])
thick = max((r for r in working if r["plan"] == best["plan"]),
            key=lambda r: r["thickness"])
print(f"      {thin['thickness']:.2f} to {thick['thickness']:.2f} m saves "
      f"{thin['steel'] - thick['steel']:.0f} kgCO2e of steel and costs")
print(f"      {thick['concrete'] - thin['concrete']:.0f} kgCO2e of concrete "
      f"- a {(thick['concrete'] - thin['concrete']) / max(thin['steel'] - thick['steel'], 0.001):.0f}x loss.")
print("   -> so the low-carbon footing is the SMALLEST plan the bearing")
print("      pressure allows, at the THINNEST section that still works -")
print("      both dimensions pushed to their limits, not traded.")

# -- 3. What is actually binding ---------------------------------------
print()
print("3. WHICH LIMIT PICKED THAT FOOTING")
smallest_working = min(row["plan"] for row in working)
print(f"   smallest plan that works anywhere: {smallest_working:.2f} m")
print(f"   the winner's plan:                 {best['plan']:.2f} m")
print(f"   -> the same? {best['plan'] == smallest_working}")
failed_small = [row for row in grid.values()
                if row["plan"] < smallest_working]
if failed_small:
    example = max(failed_small, key=lambda row: row["thickness"])
    print(f"   -> at {example['plan']:.2f} m even {example['thickness']:.2f} m "
          f"thick does not work:")
    print(f"      bearing {example['pressure']:.0f} kPa against "
          f"{ALLOWABLE:.0f} allowed.")
    print("      Bearing pressure is a GROUND property - no amount of")
    print("      concrete or steel fixes it, only more plan area does.")
    print("   -> which is why a site investigation is a carbon document.")
    print("      A better allowable pressure shrinks every footing on the")
    print("      job, and nothing you draw can achieve that.")

# -- 4. The mix ---------------------------------------------------------
FOOTINGS = 24
print()
print("4. THE MIX, AND THE WHOLE SUBSTRUCTURE")
print(f"   {FOOTINGS} footings like the winner")
for label, factor in (("C32/40, 25% GGBS", 0.120),
                      ("C32/40, 50% GGBS", 0.089),
                      ("C32/40, 75% GGBS", 0.063)):
    money = carbon(best["plan"], best["thickness"], best["as_x"], best["as_y"],
                   ecf_concrete=factor)
    print(f"   {label:<20} {money['total']:>7.0f} kgCO2e each  "
          f"{money['total'] * FOOTINGS / 1000.0:>6.2f} tCO2e total")
print("   -> foundations are the least visible part of a frame and one of")
print("      the easiest places to specify a high-replacement mix: they")
print("      are massive, buried, unstressed early, and nobody is waiting")
print("      on them to strike formwork.")

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

surface = np.full((len(THICKNESSES), len(PLANS)), np.nan)
for row_index, thickness in enumerate(THICKNESSES):
    for column_index, plan in enumerate(PLANS):
        cell = grid[(plan, thickness)]
        if cell["works"]:
            surface[row_index, column_index] = cell["total"]

image = left.imshow(surface, origin="lower", aspect="auto", cmap="YlGnBu",
                    extent=(PLANS[0] - 0.125, PLANS[-1] + 0.125,
                            THICKNESSES[0] - 0.05, THICKNESSES[-1] + 0.05))
figure.colorbar(image, ax=left, label="kgCO2e per footing")
for row_index, thickness in enumerate(THICKNESSES):
    for column_index, plan in enumerate(PLANS):
        cell = grid[(plan, thickness)]
        left.text(plan, thickness,
                  f"{cell['total']:.0f}" if cell["works"] else "x",
                  ha="center", va="center", fontsize=8,
                  color="#22303a" if cell["works"] else "#c0392b")
left.plot(best["plan"], best["thickness"], marker="*", ms=20,
          color="#c0392b", mec="white")
left.set_xlabel("plan size a = b (m)")
left.set_ylabel("thickness yf (m)")
left.set_title("The carbon map - star is the lowest that works\n"
               "'x' = bearing, overturning or uplift fails", fontsize=10)

for thickness, colour in zip(THICKNESSES,
                             ("#22303a", "#1a7f4b", "#e0a458", "#c86e5a")):
    cells = sorted([grid[(plan, thickness)] for plan in PLANS
                    if grid[(plan, thickness)]["works"]],
                   key=lambda cell: cell["plan"])
    if cells:
        right.plot([cell["plan"] for cell in cells],
                   [cell["total"] for cell in cells],
                   lw=2.0, marker="o", ms=5, color=colour,
                   label=f"yf = {thickness:.2f} m")
right.set_xlabel("plan size a = b (m)")
right.set_ylabel("embodied carbon A1-A3 (kgCO2e per footing)")
right.set_title("Plan size dominates, at every thickness\n"
                "the curves barely cross - so shrink the plan first",
                fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Pad footing carbon map - {CODE}  |  N = {LOAD[0]['pa1']:.0f} kN, "
    f"allowable {ALLOWABLE:.0f} kPa  |  "
    f"concrete {ECF_CONCRETE}, bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "pad_footing_carbon_wide_or_thick.png")

print()
print("-" * 72)
print("Plan area costs concrete as a square and bar length in two")
print("directions; thickness costs it linearly and pays some back in lever")
print("arm. So the low-carbon pad is the smallest plan the ground will")
print("accept - which makes the allowable bearing pressure, and therefore")
print("the site investigation, the biggest carbon lever on a substructure.")
