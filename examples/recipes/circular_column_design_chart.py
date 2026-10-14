# ---
# Example:  A design chart for the office wall - diameter against load
# Feature:  circular_column (C12 Circular Column)
# Verified: yes - 2026-09-02 - the reference column reproduces its pinned total_as; every chart point measured on prokon-automation.exe
# ---
# A design chart is the fastest tool in an engineer's hands: you look at
# it, you read off a size, you move on. Charts used to be printed in code
# handbooks for a handful of standard cases. This recipe draws one for the
# case YOU have.
#
# Two panels:
#   LEFT   steel percentage against axial load, one line per diameter
#   RIGHT  the smallest diameter that keeps steel under a chosen limit
#
# ⚠ AND THE CHART CARRIES ITS OWN PROVENANCE. The code, the concrete, the
# steel, the effective length and the engine version are printed on the
# figure. A design chart without those on it is a picture, and somebody
# will read it off the wall in two years for a different project.
#
# Uses matplotlib, bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
COVER = 45.0
EFFECTIVE = 3000.0        # mm
MOMENT = 60.0             # kNm, the moment the chart is drawn for
STEEL_LIMIT = 4.0         # %

DIAMETERS = (300.0, 350.0, 400.0, 450.0, 500.0, 600.0, 700.0, 800.0)
LOADS = tuple(200.0 + 200.0 * step for step in range(20))    # 200 to 4000

print("A DESIGN CHART FOR A CIRCULAR COLUMN")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm")
print(f"  effective length {EFFECTIVE:.0f} mm, M = {MOMENT:.0f} kNm, "
      f"steel limit {STEEL_LIMIT:.0f} %")

# ── The anchor, and the engine's own identity for the caption ──────────
envelope = prokon.v5.circular_column.analyse(
    design_code="BS8110 - 1997", diameter=220.0, cover=40.0,
    fcu=25.0, fy=450.0, lex=2250.0, ley=2250.0, deltas=1.0,
    load_cases=[{"n": 700.0}])
PINNED_AS = 1037.1145165134003
measured = envelope["result"]["total_as"]
print(f"\n  anchor: the desktop's own short-column example")
print(f"    total_as {measured!r}   pinned {PINNED_AS!r}")
print(f"    -> {'EXACT' if measured == PINNED_AS else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def column(diameter, load):
    """(percentage, all_pass) or (None, reason)."""
    try:
        result = prokon.v5.circular_column.analyse(
            design_code=CODE, diameter=diameter, cover=COVER,
            fcu=FCU, fy=FY, lex=EFFECTIVE, ley=EFFECTIVE,
            bracing_x="Braced", bracing_y="Braced", deltas=1.0,
            load_cases=[{"n": load, "m1x": MOMENT}])["result"]
    except prokon.v5.ProkonError as refusal:
        return None, refusal.message.encode("ascii", "replace").decode()
    return result["percentage_steel"], result["all_pass"]


# ── Gather the chart data ──────────────────────────────────────────────
print(f"\nSTEEL PERCENTAGE   rows are diameters, columns are axial load kN")
print(f"{'dia':>5}" + "".join(f"{load:>7.0f}" for load in LOADS[::3]))

curves = {}
for diameter in DIAMETERS:
    percentages = []
    for load in LOADS:
        percentage, passed = column(diameter, load)
        percentages.append(percentage if passed else None)
    curves[diameter] = percentages
    cells = []
    for percentage in percentages[::3]:
        cells.append("-" if percentage is None else f"{percentage:.2f}")
    print(f"{diameter:>5.0f}" + "".join(f"{cell:>7}" for cell in cells))

# The smallest diameter that stays under the limit, per load.
smallest = []
for index, load in enumerate(LOADS):
    choice = None
    for diameter in DIAMETERS:
        percentage = curves[diameter][index]
        if percentage is not None and percentage <= STEEL_LIMIT:
            choice = diameter
            break
    smallest.append(choice)

print(f"\nSMALLEST DIAMETER UNDER {STEEL_LIMIT:.0f} % STEEL")
print(f"   {'N (kN)':>8} {'diameter':>9} {'steel %':>8}")
for index, load in enumerate(LOADS):
    diameter = smallest[index]
    if diameter is None:
        print(f"   {load:>8.0f} {'none':>9} {'-':>8}")
        continue
    print(f"   {load:>8.0f} {diameter:>9.0f} "
          f"{curves[diameter][index]:>8.2f}")

# ── Draw it ─────────────────────────────────────────────────────────────
figure, (left, right) = plt.subplots(1, 2, figsize=(13, 6))

for diameter in DIAMETERS:
    xs = [load for load, percentage in zip(LOADS, curves[diameter])
          if percentage is not None]
    ys = [percentage for percentage in curves[diameter]
          if percentage is not None]
    if xs:
        left.plot(xs, ys, marker="o", markersize=3, linewidth=1.4,
                  label=f"{diameter:.0f} mm")

left.axhline(STEEL_LIMIT, color="0.3", linestyle="--", linewidth=1.2)
left.annotate(f"{STEEL_LIMIT:.0f} % limit", (LOADS[1], STEEL_LIMIT + 0.15),
              fontsize=9, color="0.3")
left.set_xlabel("axial load N (kN)")
left.set_ylabel("reinforcement (% of gross area)")
left.set_title(f"Steel against load, M = {MOMENT:.0f} kNm", fontsize=10)
left.set_ylim(0, min(16.0, STEEL_LIMIT * 3))
left.grid(True, linewidth=0.3, color="0.85")
left.legend(title="diameter", fontsize=8, title_fontsize=8, ncol=2)

chosen_x = [load for load, diameter in zip(LOADS, smallest) if diameter]
chosen_y = [diameter for diameter in smallest if diameter]
right.step(chosen_x, chosen_y, where="post", linewidth=2.0, color="0.2")
right.plot(chosen_x, chosen_y, "o", markersize=4, color="0.2")
right.set_xlabel("axial load N (kN)")
right.set_ylabel("smallest workable diameter (mm)")
right.set_title(f"Smallest diameter under {STEEL_LIMIT:.0f} % steel",
                fontsize=10)
right.grid(True, linewidth=0.3, color="0.85")
right.set_yticks(list(DIAMETERS))

# THE PROVENANCE. Anyone reading this off a wall needs it.
figure.suptitle(
    f"Circular column design chart - {CODE}\n"
    f"fcu {FCU:.0f} MPa, fy {FY:.0f} MPa, cover {COVER:.0f} mm, "
    f"le {EFFECTIVE:.0f} mm braced, M {MOMENT:.0f} kNm  |  "
    f"engine {envelope['module_version'][:24]}",
    fontsize=10)
figure.tight_layout()

output = Path("circular_column_chart.png")
figure.savefig(output, dpi=140)
plt.close(figure)

size = output.stat().st_size
print(f"\nWritten: {output.resolve()}")
print(f"  {size} bytes, "
      f"{'a real image' if size > 20_000 else 'SUSPICIOUSLY SMALL'}")

# ── And the thing a chart hides ────────────────────────────────────────
# Every curve above has a lower end that turns UP as the load falls,
# because a lightly loaded column carrying a moment is tension-governed.
# A chart read left to right looks monotonic; it is not.
print(f"\nWHAT THE CHART HIDES")
for diameter in DIAMETERS:
    percentages = [(load, percentage)
                   for load, percentage in zip(LOADS, curves[diameter])
                   if percentage is not None]
    if len(percentages) < 3:
        continue
    minimum = min(percentages, key=lambda pair: pair[1])
    if minimum[0] > percentages[0][0]:
        print(f"   {diameter:.0f} mm: lightest steel is at N = "
              f"{minimum[0]:.0f} kN ({minimum[1]:.2f} %), NOT at the")
        print(f"      lowest load - {percentages[0][0]:.0f} kN needs "
              f"{percentages[0][1]:.2f} %")
print("   -> a lightly loaded column carrying a moment is TENSION-governed,")
print("      so axial load HELPS until the balance point. Reading a chart")
print("      from the heaviest load down is how that gets missed.")
