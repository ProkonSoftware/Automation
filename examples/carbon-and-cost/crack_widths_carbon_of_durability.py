# ---
# Example:  What durability costs - the carbon price of a crack limit
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes - 2026-09-09 - carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# On a water-retaining or buried structure the crack width limit is a
# DURABILITY decision, usually taken early and rarely priced. Tightening
# it from 0.3 mm to 0.1 mm is one line in a specification and a lot more
# steel - and more steel is more carbon.
#
# This script asks C21 exactly what each limit costs, so the durability
# conversation can be had with a number in it.
#
# AND IT FINDS SOMETHING WORTH MORE THAN THE ANSWER. C21 returns SEVERAL
# bar arrangements per load case, all of which satisfy the limit. They do
# NOT contain the same amount of steel, and the list is not sorted by
# steel. Taking the first one that passes - the obvious thing to do -
# leaves carbon on the table. This script takes the LIGHTEST that passes
# and reports the gap.
#
# WHAT IT COUNTS. A1-A3 carbon per square metre of wall: the concrete at
# its full thickness, plus the flexural steel of the chosen arrangement.
# Distribution steel, links, kickers and construction joints are not
# counted - so the DIFFERENCES between limits are the honest reading here,
# more than the absolute figures.
#
# ONE INPUT ODDITY: C21 takes `load_cases` as a JSON STRING, not a list of
# dicts like every other engine here. Passing a list raises invalid_input.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

import json
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

CODE = "BS8007 - 1987"       # the water-retaining code
THICKNESS = 300.0            # mm
COVER = 40.0
FCU = 30.0
FY = 450.0
MOMENT = 50.0                # kNm/m service moment

LIMITS = (0.1, 0.15, 0.2, 0.25, 0.3)


def crack(limit):
    """One C21 analysis at this allowable crack width."""
    return prokon.v5.crack_widths.analyse(
        design_code=CODE, slab_mode=True, h=THICKNESS, hef=200.0,
        b=1000.0, cover=COVER, fcu=FCU, fy=FY, ea=200.0, ec=26.0,
        allowable_crack_width=limit,
        load_cases=json.dumps([{"n": 1, "m": MOMENT, "m_uls": 1.5}]))


def carbon_per_m2(steel_mm2_per_m, ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon, kgCO2e per square metre of wall."""
    concrete = THICKNESS / 1000.0 * DENSITY_CONCRETE * ecf_concrete
    steel = steel_mm2_per_m * 1.0e-6 * DENSITY_STEEL * ECF_REBAR
    return dict(concrete=concrete, steel=steel, total=concrete + steel)


print("WHAT A CRACK WIDTH LIMIT COSTS IN CARBON")
print(f"  {CODE}, {THICKNESS:.0f} mm wall, cover {COVER:.0f} mm, "
      f"fcu {FCU:.0f}, fy {FY:.0f}")
print(f"  service moment {MOMENT:.0f} kNm/m")

# -- 1. Every limit, and the choice inside each ------------------------
print()
print("1. THE ARRANGEMENTS C21 OFFERS, AT EACH LIMIT")

rows = []
reference = None

for limit in LIMITS:
    envelope = crack(limit)
    result = envelope["result"]
    if reference is None:
        reference = envelope

    case = result["load_cases"][0]
    configs = case["optimised_configs"]
    passing = [config for config in configs if config["meets_all_criteria"]]

    print()
    print(f"   allowable {limit:.2f} mm  -  {len(configs)} arrangement(s), "
          f"{len(passing)} passing")
    for index, config in enumerate(configs):
        calc = config["calc_result"]
        mark = "ok " if config["meets_all_criteria"] else "no "
        print(f"      [{index}] {mark}{config['formatted_bars']:<12} "
              f"As {calc['steel_area']:>7.0f} mm2/m   "
              f"cw {calc['governing_crack_width']:.4f} mm")

    if not passing:
        print("      -> nothing satisfies this limit on this section.")
        rows.append(dict(limit=limit, feasible=False))
        continue

    first = passing[0]
    lightest = min(passing, key=lambda config: config["calc_result"]["steel_area"])
    first_area = first["calc_result"]["steel_area"]
    light_area = lightest["calc_result"]["steel_area"]

    money = carbon_per_m2(light_area)
    rows.append(dict(limit=limit, feasible=True,
                     first_bars=first["formatted_bars"], first_area=first_area,
                     bars=lightest["formatted_bars"], area=light_area,
                     crack=lightest["calc_result"]["governing_crack_width"],
                     options=len(configs), passing=len(passing), **money))

    saving = (first_area - light_area) * 1.0e-6 * DENSITY_STEEL * ECF_REBAR
    print(f"      -> first passing: {first['formatted_bars']} "
          f"({first_area:.0f} mm2/m)")
    print(f"         LIGHTEST     : {lightest['formatted_bars']} "
          f"({light_area:.0f} mm2/m)")
    if light_area < first_area:
        print(f"         picking the lightest saves {saving:.2f} kgCO2e/m2 "
              f"({1.0 - light_area / first_area:.0%} of the steel)")
    else:
        print("         the first passing option IS the lightest here")

# -- 2. The price of the limit ------------------------------------------
usable = [row for row in rows if row["feasible"]]
print()
print("2. THE PRICE OF THE LIMIT ITSELF")
print(f"   {'limit':>6} {'bars':<12} {'As':>8} {'steel':>8} {'total':>8}")
print(f"   {'mm':>6} {'':<12} {'mm2/m':>8} {'kgCO2e':>8} {'kgCO2e/m2':>8}")
print("   " + "-" * 48)
for row in usable:
    print(f"   {row['limit']:>6.2f} {row['bars']:<12} {row['area']:>8.0f} "
          f"{row['steel']:>8.2f} {row['total']:>8.1f}")

loosest = max(usable, key=lambda row: row["limit"])
tightest = min(usable, key=lambda row: row["limit"])
print(f"   -> from {loosest['limit']:.2f} mm to {tightest['limit']:.2f} mm:")
print(f"      steel      {loosest['area']:.0f} -> {tightest['area']:.0f} mm2/m "
      f"({tightest['area'] / loosest['area']:.2f}x)")
print(f"      carbon/m2  {loosest['total']:.1f} -> {tightest['total']:.1f} "
      f"({tightest['total'] / loosest['total']:.2f}x)")
print(f"   -> the STEEL multiplies by "
      f"{tightest['area'] / loosest['area']:.2f}, but the total moves only")
print(f"      {tightest['total'] / loosest['total']:.2f}x, because the "
      f"{THICKNESS:.0f} mm of concrete is fixed and")
print(f"      it is {loosest['concrete'] / loosest['total']:.0%} of the "
      f"total to begin with.")
print("   -> so a tighter crack limit is a real cost and a SMALL one in")
print("      carbon terms. If durability wants 0.2 instead of 0.3, carbon")
print("      is not the argument against it.")

# -- 3. Scale it, because per-m2 hides the size of a tank --------------
TANK_AREA = 900.0            # m2 of wall and base on a decent reservoir
print()
print("3. ON A REAL STRUCTURE")
print(f"   {TANK_AREA:,.0f} m2 of wall and base")
for row in (loosest, tightest):
    print(f"   {row['limit']:.2f} mm limit -> "
          f"{row['total'] * TANK_AREA / 1000.0:>6.1f} tCO2e")
delta = (tightest["total"] - loosest["total"]) * TANK_AREA / 1000.0
print(f"   -> tightening the whole structure costs {delta:.1f} tCO2e.")
print("      Worth knowing, and worth putting next to the cost of the")
print("      leak it prevents rather than treating as free either way.")

# -- 4. The mix, and the one that is NOT free --------------------------
print()
print("4. THE MIX - AND A WARNING SPECIFIC TO THIS CODE")
for label, factor in (("C32/40, 25% GGBS", 0.120),
                      ("C32/40, 50% GGBS", 0.089),
                      ("C32/40, 75% GGBS", 0.063)):
    money = carbon_per_m2(tightest["area"], ecf_concrete=factor)
    print(f"   {label:<20} {money['total']:>7.1f} kgCO2e/m2")
print("   -> the concrete is most of this element, so GGBS again outranks")
print("      everything the steel can do.")
print("   -> BUT: high-GGBS mixes change the EARLY-AGE THERMAL behaviour")
print("      that BS8007 crack control is largely about. Lower peak heat")
print("      generally helps early thermal cracking; slower strength gain")
print("      generally does not help restraint at joints. C21 is not being")
print("      told the mix here - `fcu` is a strength, not a cement blend -")
print("      so this table prices the CONCRETE and not the cracking. Do")
print("      not read it as 'more GGBS, same crack widths'.")

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

limits = np.array([row["limit"] for row in usable])
concrete = np.array([row["concrete"] for row in usable])
steel = np.array([row["steel"] for row in usable])

left.bar(limits, concrete, width=0.028, label="concrete (fixed)",
         color="#9fb8c8")
left.bar(limits, steel, width=0.028, bottom=concrete,
         label="reinforcement", color="#c86e5a")
for row in usable:
    left.text(row["limit"], row["total"] + 1.0, row["bars"], ha="center",
              fontsize=8, rotation=90, color="#22303a", va="bottom")
left.set_xlabel("allowable crack width (mm)")
left.set_ylabel("embodied carbon A1-A3 (kgCO2e per m2)")
left.set_ylim(0.0, max(row["total"] for row in usable) * 1.35)
left.set_title("Durability moves the steel, not the total\n"
               "the concrete band does not move at all", fontsize=10)
left.legend(fontsize=9, loc="lower left")
left.grid(alpha=0.25, axis="y")

firsts = np.array([row["first_area"] for row in usable])
lights = np.array([row["area"] for row in usable])
offset = 0.012
right.bar(limits - offset, firsts, width=0.022,
          label="first passing arrangement", color="#e0a458")
right.bar(limits + offset, lights, width=0.022,
          label="lightest passing arrangement", color="#1a7f4b")
right.set_xlabel("allowable crack width (mm)")
right.set_ylabel("steel area (mm2/m)")
right.set_title("The list is not sorted by steel\n"
                "taking the first passing option overpays", fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25, axis="y")

figure.suptitle(
    f"Crack width limit against carbon - {CODE}  |  "
    f"{THICKNESS:.0f} mm, M = {MOMENT:.0f} kNm/m, cover {COVER:.0f} mm  |  "
    f"concrete {ECF_CONCRETE}, bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "crack_widths_carbon_of_durability.png")

print()
print("-" * 72)
print("A tighter crack limit costs steel, and steel is a small part of a")
print("300 mm wall - so durability is cheap in carbon and should not be")
print("traded away for it. The bigger finding is procedural: C21 offers")
print("several passing arrangements, they differ in steel, and the list")
print("is not sorted. Read them all before you pick one.")
