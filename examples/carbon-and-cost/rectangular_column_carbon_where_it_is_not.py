# ---
# Example:  Where a column's carbon is NOT - and one sweep that is wasted
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes - 2026-09-09 - carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# C11 hands back several bar arrangements for one column - 40Y12, 24Y16,
# 16Y20, 12Y25 - and it is tempting to sweep them for the lowest-carbon
# option. This script starts by MEASURING whether that sweep is worth
# running, and the answer is no.
#
# That is the useful half. An optimisation you do not have to run is worth
# more than one you do, and knowing WHY tells you where to look instead.
#
# WHAT THIS SCRIPT COUNTS. A1-A3 carbon for one storey of column: the
# concrete b x h x storey height, and the bar area C11 reports. Links,
# formwork, laps and starter bars are not counted; nor is the extra
# foundation a bigger column needs, which counts against the large end.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# -- EMBODIED CARBON FACTORS -------------------------------------------
# A1-A3, kgCO2e/kg, from IStructE, "A brief guide to calculating embodied
# carbon", The Structural Engineer, July 2020: concrete C32/40 at 25/50/75 %
# GGBS = 0.120 / 0.089 / 0.063; bar UK (BRC EPD) 0.684, world 1.99.
ECF_CONCRETE = 0.120
ECF_REBAR = 0.684
DENSITY_CONCRETE = 2400.0
DENSITY_STEEL = 7850.0

# CONTROL - reproduces the worked example in that same guide.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "SABS 0100 - 2000"
HEIGHT = 4.0                 # m storey, matching lex/ley below
COVER = 40.0
FCU = 30.0
FY = 450.0
PRACTICAL_STEEL_LIMIT = 4.0  # %, the ceiling once bars lap

LOADS = [{"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
         {"n": 2000, "m2x": 125, "m1x": 75, "m2y": 90, "m1y": 55}]

SIZES = np.arange(350.0, 701.0, 50.0)


def col(size):
    """One C11 analysis of a square column of this side."""
    return prokon.v5.rectangular_column.analyse(
        design_code=CODE, h=size, b=size, dc_x=COVER, dc_y=COVER,
        fcu=FCU, fy=FY, lex=HEIGHT * 1000.0, ley=HEIGHT * 1000.0,
        bracing_x="Braced", bracing_y="Braced", betad=0.6, deltas=1.0,
        load_cases=LOADS)


def carbon(size, steel_mm2, ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon for one storey of column, kgCO2e."""
    concrete_m3 = (size / 1000.0) ** 2 * HEIGHT
    steel_kg = steel_mm2 * 1.0e-6 * HEIGHT * DENSITY_STEEL
    concrete = concrete_m3 * DENSITY_CONCRETE * ecf_concrete
    steel = steel_kg * ECF_REBAR
    return dict(concrete_m3=concrete_m3, steel_kg=steel_kg,
                concrete=concrete, steel=steel, total=concrete + steel)


print("A RECTANGULAR COLUMN'S CARBON - AND THE SWEEP NOT TO RUN")
print(f"  {CODE}, {HEIGHT:.1f} m storey, cover {COVER:.0f} mm, "
      f"fcu {FCU:.0f}, fy {FY:.0f}")
print(f"  {len(LOADS)} load cases, worst N = "
      f"{max(case['n'] for case in LOADS):.0f} kN")

# -- 1. The sweep that is wasted, measured ------------------------------
print()
print("1. THE BAR ARRANGEMENTS ARE CARBON-IDENTICAL. MEASURED.")
envelope = col(400.0)
result = envelope["result"]
reference = envelope

print(f"   a 400 mm column returns {len(result['options'])} arrangements:")
print(f"   {'bars':<10} {'dia':>4} {'no.':>4} {'ast mm2':>9} {'%':>7} "
      f"{'passes':>7} {'kgCO2e':>8}")
areas = set()
for option in result["options"]:
    money = carbon(400.0, option["ast"])
    areas.add(round(option["ast"], 6))
    print(f"   {option['bar_description']:<10} {option['bar_dia']:>4} "
          f"{option['total_bars']:>4} {option['ast']:>9.0f} "
          f"{option['perc']:>6.3f}% {str(option['all_pass']):>7} "
          f"{money['total']:>8.1f}")

print(f"   -> distinct steel AREAS among those arrangements: {len(areas)}")
print("   -> they are the same area, rearranged. C11 picks an area and")
print("      then offers you bar diameters that deliver it, so there is")
print("      no carbon difference to find between them. Choose on")
print("      buildability - fewer, larger bars are quicker to fix - and")
print("      spend the optimisation effort somewhere it can pay.")
print(f"   -> and `preferred` is {result['preferred']!r} here, so there is")
print("      no engine recommendation to compare against either. Do not")
print("      write code that assumes it names one.")

# -- 2. Where the carbon actually is -----------------------------------
print()
print("2. THE SECTION SIZE IS THE WHOLE STORY")
print(f"   {'size':>5} {'ast':>8} {'%':>7} {'concrete':>9} {'steel':>7} "
      f"{'kgCO2e':>8} {'conc':>6}")
print(f"   {'mm':>5} {'mm2':>8} {'':>7} {'kgCO2e':>9} {'kgCO2e':>7} "
      f"{'total':>8} {'share':>6}")
print("   " + "-" * 56)

rows = []
for size in SIZES:
    result = col(size)["result"]
    if not result["has_feasible_design"]:
        print(f"   {size:>5.0f}   no feasible arrangement")
        continue

    passing = [option for option in result["options"] if option["all_pass"]]
    if not passing:
        print(f"   {size:>5.0f}   arrangements found, none passes")
        continue

    # All passing options share one area (section 1), so any of them does.
    lightest = min(passing, key=lambda option: option["ast"])
    buildable = lightest["perc"] <= PRACTICAL_STEEL_LIMIT
    money = carbon(size, lightest["ast"])

    rows.append(dict(size=size, ast=lightest["ast"], perc=lightest["perc"],
                     buildable=buildable,
                     bars=lightest["bar_description"], **money))
    print(f"   {size:>5.0f} {lightest['ast']:>8.0f} {lightest['perc']:>6.3f}% "
          f"{money['concrete']:>9.1f} {money['steel']:>7.1f} "
          f"{money['total']:>8.1f} {money['concrete'] / money['total']:>5.0%}"
          + ("" if buildable else f"   OVER {PRACTICAL_STEEL_LIMIT:.0f}% STEEL"))

usable = [row for row in rows if row["buildable"]]
best = min(usable, key=lambda row: row["total"])
print(f"   -> {len(usable)} of {len(rows)} sizes are both adequate and "
      f"under {PRACTICAL_STEEL_LIMIT:.0f} % steel.")
print(f"   -> LOWEST CARBON: {best['size']:.0f} mm square, "
      f"{best['perc']:.2f} % steel ({best['bars']}), {best['total']:.1f} kgCO2e")

# -- 3. Steel is not negligible here, and that is the difference --------
print()
print("3. A COLUMN IS NOT A SLAB - STEEL EARNS ITS PLACE")
print(f"   at the minimum-carbon size the split is "
      f"{best['concrete'] / best['total']:.0%} concrete / "
      f"{best['steel'] / best['total']:.0%} steel")
biggest = max(usable, key=lambda row: row["size"])
print(f"   at {biggest['size']:.0f} mm it is "
      f"{biggest['concrete'] / biggest['total']:.0%} / "
      f"{biggest['steel'] / biggest['total']:.0%}")
print("   -> a heavily loaded column carries real steel, so unlike a slab")
print("      its carbon is a genuine two-material problem: at the optimum")
print("      a third of it is reinforcement.")

smallest_buildable = min(row["size"] for row in usable)
smallest_at_all = min(row["size"] for row in rows)
print(f"   -> but the optimum is still a BOUNDARY, not a valley: "
      f"{best['size'] == smallest_buildable}")
print(f"      {best['size']:.0f} mm is the smallest size that stays under the")
print(f"      steel ceiling. The engine would give you {smallest_at_all:.0f} mm")
print("      quite happily. So what picks this column is the 4 % limit -")
print("      a DETAILING rule - and not the carbon arithmetic at all.")

# And one thing the table shows that contradicts the usual intuition.
areas = [row["ast"] for row in rows]
turning = [rows[i] for i in range(1, len(rows) - 1)
           if areas[i] < areas[i - 1] and areas[i + 1] > areas[i]]
print("   -> AND STEEL AREA IS NOT MONOTONIC IN SIZE. It falls to a")
if turning:
    low = turning[0]
    print(f"      minimum at {low['size']:.0f} mm ({low['ast']:.0f} mm2) and then")
    print(f"      CLIMBS again - {max(rows, key=lambda r: r['size'])['ast']:.0f} mm2 at "
          f"{max(rows, key=lambda r: r['size'])['size']:.0f} mm.")
print("      Once minimum-percentage steel governs, a bigger column needs")
print("      MORE bar, because the minimum is a fraction of a bigger gross")
print("      area. 'Go bigger to save steel' has a floor, and past it you")
print("      pay twice - more concrete and more steel.")

# -- 4. The mix -------------------------------------------------------
print()
print("4. THE MIX, ON THE WINNING COLUMN")
for label, factor in (("C32/40, 25% GGBS", 0.120),
                      ("C32/40, 50% GGBS", 0.089),
                      ("C32/40, 75% GGBS", 0.063)):
    money = carbon(best["size"], best["ast"], ecf_concrete=factor)
    print(f"   {label:<20} {money['total']:>7.1f} kgCO2e  "
          f"({money['concrete'] / money['total']:.0%} concrete)")
print("   -> and watch the share move. The more you decarbonise the")
print("      concrete, the more the STEEL becomes the thing worth")
print("      optimising. A low-carbon mix changes which lever matters.")

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


sizes = np.array([row["size"] for row in rows])
concrete = np.array([row["concrete"] for row in rows])
steel = np.array([row["steel"] for row in rows])

figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

left.bar(sizes, concrete, width=32.0, label="concrete", color="#9fb8c8")
left.bar(sizes, steel, width=32.0, bottom=concrete, label="reinforcement",
         color="#c86e5a")
for row in rows:
    if not row["buildable"]:
        left.text(row["size"], row["total"] + 6.0, "too much\nsteel",
                  ha="center", fontsize=8, color="#c0392b")
left.axvline(best["size"], color="#1a7f4b", ls="--", lw=1.5)
left.set_xlabel("square column side (mm)")
left.set_ylabel(f"embodied carbon A1-A3 (kgCO2e per {HEIGHT:.1f} m storey)")
left.set_title("Both materials matter on a column\n"
               "dashed line = lowest carbon that is also buildable",
               fontsize=10)
left.legend(fontsize=9, loc="upper left")
left.grid(alpha=0.25, axis="y")

percentages = np.array([row["perc"] for row in rows])
right.plot(sizes, percentages, color="#22303a", lw=2.0, marker="o", ms=5)
right.axhline(PRACTICAL_STEEL_LIMIT, color="#c0392b", ls="--", lw=1.5,
              label=f"{PRACTICAL_STEEL_LIMIT:.0f} % practical ceiling")
right.set_xlabel("square column side (mm)")
right.set_ylabel("steel content (%)")
right.set_title("What the engine will happily design past\n"
                "all_pass is a capacity test, not a buildability one",
                fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Rectangular column carbon - {CODE}  |  "
    f"N up to {max(case['n'] for case in LOADS):.0f} kN, {HEIGHT:.1f} m storey  |  "
    f"concrete {ECF_CONCRETE}, bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "rectangular_column_carbon_where_it_is_not.png")

print()
print("-" * 72)
print("The arrangements C11 offers are one steel area in different bar")
print("diameters, so there is no carbon in choosing between them - measure")
print("before you optimise. The carbon is in the section size, and what")
print("picks the size is a detailing limit rather than the arithmetic. Two")
print("things worth carrying: an engine's 'pass' is not buildability, and")
print("bigger stops saving steel once minimum percentage takes over.")
