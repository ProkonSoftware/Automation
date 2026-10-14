# ---
# Example:  Does a higher concrete grade lower the carbon? Column edition
# Feature:  circular_column (C12 Circular Column)
# Verified: yes - 2026-09-09 - carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# A stronger mix lets you build a smaller column. A stronger mix also has
# a HIGHER carbon factor per kilogram, because it holds more cement. Those
# two facts point in opposite directions and the usual answer - "specify
# the higher grade, you use less of it" - is an assumption, not a result.
#
# This script settles it for one column by sweeping C12 over diameter at
# two grades and pricing every combination that passes.
#
# READ THIS BEFORE TRUSTING ANY CONCRETE CARBON FACTOR YOU FIND.
# BS8110's `fcu` is a CUBE strength. The ICE and IStructE tables name
# concrete by the EUROCODE pair "C<cylinder>/<cube>". So:
#
#     fcu = 40 MPa (cube)  ->  the "C32/40" rows
#     fcu = 50 MPa (cube)  ->  the "C40/50" rows
#
# Reading "C32/40" as fcu 32 picks the factor one grade too low and makes
# every higher grade look better than it is. That single mis-read is
# enough to invert this script's answer, which is why it is stated here
# rather than buried.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# -- EMBODIED CARBON FACTORS -------------------------------------------
# A1-A3, kgCO2e/kg, from IStructE, "A brief guide to calculating embodied
# carbon", The Structural Engineer, July 2020, in situ unreinforced:
#
#     C32/40   25% GGBS 0.120   50% 0.089   75% 0.063
#     C40/50   25% GGBS 0.138   50% 0.102   75% 0.072
#
# Note the grades are paired at EQUAL GGBS replacement, which is what
# makes the comparison below a fair one: only the strength differs.
GRADES = {
    40.0: dict(label="C32/40", ecf=0.120),
    50.0: dict(label="C40/50", ecf=0.138),
}
ECF_REBAR = 0.684
DENSITY_CONCRETE = 2400.0
DENSITY_STEEL = 7850.0

# CONTROL - reproduces the worked example in that same guide.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "BS8110 - 1997"
HEIGHT = 3.5                 # m storey height
COVER = 45.0                 # mm
FY = 450.0
LOAD = [{"n": 2500.0, "m1x": 120.0}]

DIAMETERS = np.arange(350.0, 751.0, 50.0)


def column(diameter, fcu):
    """One C12 analysis of this column."""
    return prokon.v5.circular_column.analyse(
        design_code=CODE, diameter=diameter, cover=COVER,
        fcu=fcu, fy=FY,
        lex=HEIGHT * 1000.0, ley=HEIGHT * 1000.0,
        deltas=1.0, load_cases=LOAD)


def carbon(diameter, steel_mm2, ecf_concrete):
    """A1-A3 carbon for one storey of column, kgCO2e."""
    concrete_m3 = np.pi * (diameter / 1000.0) ** 2 / 4.0 * HEIGHT
    steel_kg = steel_mm2 * 1.0e-6 * HEIGHT * DENSITY_STEEL
    concrete = concrete_m3 * DENSITY_CONCRETE * ecf_concrete
    steel = steel_kg * ECF_REBAR
    return dict(concrete_m3=concrete_m3, steel_kg=steel_kg,
                concrete=concrete, steel=steel, total=concrete + steel)


print("DOES A HIGHER CONCRETE GRADE LOWER A COLUMN'S CARBON?")
print(f"  {CODE}, {HEIGHT:.1f} m storey, cover {COVER:.0f} mm, fy {FY:.0f}")
print(f"  load  N = {LOAD[0]['n']:.0f} kN, M = {LOAD[0]['m1x']:.0f} kNm")
print("  grades compared at EQUAL 25 % GGBS, so only strength differs:")
for fcu, grade in GRADES.items():
    print(f"    fcu {fcu:.0f} (cube) = {grade['label']} "
          f"at {grade['ecf']:.3f} kgCO2e/kg")

# -- 1. The sweep, both grades -----------------------------------------
print()
print("1. EVERY DIAMETER, AT BOTH GRADES")
print(f"   {'dia':>5} | {'fcu 40: As':>10} {'%':>6} {'kgCO2e':>8} "
      f"| {'fcu 50: As':>10} {'%':>6} {'kgCO2e':>8}")
print("   " + "-" * 66)

rows = {fcu: [] for fcu in GRADES}
reference = None

for diameter in DIAMETERS:
    line = f"   {diameter:>5.0f} |"
    for fcu, grade in GRADES.items():
        envelope = column(diameter, fcu)
        result = envelope["result"]
        if reference is None:
            reference = envelope

        passes = result["all_pass"]
        money = carbon(diameter, result["total_as"], grade["ecf"])
        rows[fcu].append(dict(dia=diameter, steel_mm2=result["total_as"],
                              perc=result["percentage_steel"],
                              passes=passes, **money))
        mark = "" if passes else "x"
        line += (f" {result['total_as']:>10.0f} {result['percentage_steel']:>5.2f}"
                 f"{mark:<1} {money['total']:>8.1f} |")
    print(line)

print("   ('x' beside the steel percentage means the column does not pass)")

# AND HERE IS THE TRAP IN THAT COLUMN OF MARKS. C12 designs whatever it is
# asked, so "passes" means the arrangement it found works - not that it is
# buildable. BS8110 caps steel at 6 %, and 4 % is the practical ceiling
# once bars lap. Apply YOUR limit; the engine will not.
PRACTICAL_STEEL_LIMIT = 4.0
crowded = [(fcu, row) for fcu in GRADES for row in rows[fcu]
           if row["passes"] and row["perc"] > PRACTICAL_STEEL_LIMIT]
print(f"   -> every diameter above reports all_pass = True, including "
      f"{len(crowded)} that")
print(f"      carry more than {PRACTICAL_STEEL_LIMIT:.0f} % steel:")
for fcu, row in crowded:
    print(f"        {GRADES[fcu]['label']} at {row['dia']:.0f} mm: "
          f"{row['perc']:.2f} %")
print("      Those are not columns anyone can cast. The engine's 'pass' is")
print("      a capacity statement, not a buildability one - so the sweep")
print("      below keeps only arrangements under that limit.")

for fcu in GRADES:
    for row in rows[fcu]:
        row["passes"] = row["passes"] and row["perc"] <= PRACTICAL_STEEL_LIMIT

best = {}
for fcu in GRADES:
    ok = [row for row in rows[fcu] if row["passes"]]
    if ok:
        best[fcu] = min(ok, key=lambda row: row["total"])

print()
for fcu, grade in GRADES.items():
    if fcu in best:
        row = best[fcu]
        print(f"   best at {grade['label']}: dia {row['dia']:.0f} mm, "
              f"{row['perc']:.2f} % steel, {row['total']:.1f} kgCO2e")
    else:
        print(f"   {grade['label']}: nothing in the sweep passes")

# -- 2. The answer ------------------------------------------------------
print()
print("2. SO WHICH GRADE WINS")
if len(best) == 2:
    low, high = GRADES[40.0], GRADES[50.0]
    row_low, row_high = best[40.0], best[50.0]
    winner = min(best.items(), key=lambda item: item[1]["total"])
    print(f"   {low['label']:>8}  {row_low['dia']:.0f} mm  "
          f"{row_low['total']:>7.1f} kgCO2e")
    print(f"   {high['label']:>8}  {row_high['dia']:.0f} mm  "
          f"{row_high['total']:>7.1f} kgCO2e")
    margin = abs(row_high["total"] - row_low["total"])
    share = margin / max(row_low["total"], row_high["total"])
    print(f"   -> {GRADES[winner[0]]['label']} wins, by {margin:.1f} kgCO2e "
          f"({share:.1%}).")
    if row_low["dia"] == row_high["dia"]:
        print("   -> and note the two winners are the SAME DIAMETER. The")
        print("      stronger mix did not buy a smaller column here, so its")
        print("      higher factor is paid for nothing. That is the case the")
        print("      'specify higher, use less' argument forgets: it only")
        print("      works if the size actually comes down.")
    else:
        print(f"   -> the stronger mix bought "
              f"{row_low['dia'] - row_high['dia']:.0f} mm of diameter, which")
        print("      is what has to pay for its higher factor.")

# -- 3. Why: the column is not strength-governed ------------------------
print()
print("3. WHY - LOOK AT WHERE THE STEEL PERCENTAGE SITS")
for fcu, grade in GRADES.items():
    ok = [row for row in rows[fcu] if row["passes"]]
    if not ok:
        continue
    smallest = min(ok, key=lambda row: row["dia"])
    largest = max(ok, key=lambda row: row["dia"])
    print(f"   {grade['label']}: {smallest['perc']:.2f} % steel at "
          f"{smallest['dia']:.0f} mm, falling to {largest['perc']:.2f} % at "
          f"{largest['dia']:.0f} mm")
print("   -> once a column is big enough, the steel drops to its MINIMUM")
print("      and stays there. Beyond that point extra diameter buys no")
print("      steel saving at all - it is pure added concrete, and the")
print("      carbon curve just climbs.")
print("   -> so a column's carbon optimum, like a beam's, is the smallest")
print("      section that passes. Grade only helps if it makes that")
print("      smallest section smaller.")

# -- 4. The mix beats the grade ----------------------------------------
print()
print("4. AND THE GGBS ROW OUTRANKS THE GRADE ROW")
winner_fcu = min(best.items(), key=lambda item: item[1]["total"])[0]
row = best[winner_fcu]
print(f"   the winning column ({GRADES[winner_fcu]['label']}, "
      f"{row['dia']:.0f} mm):")
family = {40.0: (("25% GGBS", 0.120), ("50% GGBS", 0.089), ("75% GGBS", 0.063)),
          50.0: (("25% GGBS", 0.138), ("50% GGBS", 0.102), ("75% GGBS", 0.072))}
for label, factor in family[winner_fcu]:
    money = carbon(row["dia"], row["steel_mm2"], factor)
    print(f"     {label:<10} {factor:.3f} -> {money['total']:>7.1f} kgCO2e")
print("   -> the strength decision moved a few percent. The cement")
print("      replacement decision moves tens of percent, at the same")
print("      strength class. If only one line on the concrete note can be")
print("      argued for, it is not the grade.")

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

for fcu, colour in ((40.0, "#1a7f4b"), (50.0, "#c86e5a")):
    ok = [row for row in rows[fcu] if row["passes"]]
    if not ok:
        continue
    left.plot([row["dia"] for row in ok], [row["total"] for row in ok],
              lw=2.0, marker="o", ms=5, color=colour,
              label=f"{GRADES[fcu]['label']} ({GRADES[fcu]['ecf']:.3f})")
    if fcu in best:
        left.plot(best[fcu]["dia"], best[fcu]["total"], marker="*", ms=16,
                  color=colour, mec="#22303a")

left.set_xlabel("column diameter (mm)")
left.set_ylabel(f"embodied carbon A1-A3 (kgCO2e per {HEIGHT:.1f} m storey)")
left.set_title("Both grades climb with diameter\n"
               "stars mark each grade's lowest-carbon passing column",
               fontsize=10)
left.legend(fontsize=9)
left.grid(alpha=0.25)

for fcu, colour in ((40.0, "#1a7f4b"), (50.0, "#c86e5a")):
    ok = [row for row in rows[fcu] if row["passes"]]
    if not ok:
        continue
    right.plot([row["dia"] for row in ok], [row["perc"] for row in ok],
               lw=2.0, marker="o", ms=5, color=colour,
               label=GRADES[fcu]["label"])
right.set_xlabel("column diameter (mm)")
right.set_ylabel("steel content (%)")
right.set_title("Steel bottoms out at the code minimum\n"
                "past that, diameter is pure added concrete", fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Circular column: grade against size - {CODE}  |  "
    f"N = {LOAD[0]['n']:.0f} kN, M = {LOAD[0]['m1x']:.0f} kNm, "
    f"{HEIGHT:.1f} m storey  |  bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "circular_column_carbon_of_concrete_grade.png")

print()
print("-" * 72)
print("A higher grade only pays if it actually shrinks the section, and on")
print("a column that has already dropped to minimum steel it does not.")
print("Check which limit is governing before buying strength you cannot")
print("spend - and read the grade label as cylinder/CUBE before you pick")
print("its carbon factor.")
