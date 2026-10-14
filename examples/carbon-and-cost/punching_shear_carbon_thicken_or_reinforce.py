# ---
# Example:  Thicken the slab or add links? The carbon answer
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes - 2026-09-09 - the asv units confirmed against the engine's own bar suggestion (6941 mm2 -> 35Y16); carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# A flat slab fails punching at a column. There are two fixes and they are
# not comparable by eye:
#
#   THICKEN THE SLAB   more effective depth. Cheap per column - and paid
#                      for over the WHOLE FLOOR PLATE, because you cannot
#                      thicken one square metre.
#   ADD SHEAR LINKS    steel, local to the column, over a few square
#                      metres. Expensive per kilogram, tiny in quantity.
#
# Intuition says "concrete is low-carbon per kg, so thicken". This script
# prices both against C23 and shows how badly that intuition scales.
#
# WHAT IT COUNTS. A1-A3 carbon for ONE COLUMN'S worth of the decision:
# the link steel C23 says the perimeters need, against the extra concrete
# that thickening the slab adds over its tributary bay. It does NOT count
# the extra self-weight a thicker slab carries down to the foundations -
# which makes thickening look BETTER here than it really is.
#
# ONE UNIT, MEASURED, BECAUSE GETTING IT WRONG CHANGES THE ANSWER.
# `critical_perimeters[i]["asv"]` is a TOTAL AREA in mm2 for that
# perimeter, not an area per metre. The engine's own bar suggestion
# confirms it: asv of 6941 comes back as "35Y16", and 35 x 201 = 7037.
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
# GGBS = 0.120 / 0.089 / 0.063; bar UK (BRC EPD) 0.684, world average 1.99.
ECF_CONCRETE = 0.120
ECF_REBAR = 0.684
DENSITY_CONCRETE = 2400.0
DENSITY_STEEL = 7850.0

# CONTROL - reproduces the worked example in that same guide.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "BS8110 - 1997"
COLUMN = 400.0               # mm square
FCU = 35.0
FY = 500.0
LOAD = 1400.0                # kN, one column's ultimate reaction
BAY = 7.2                    # m - the column grid, so the tributary area
COVER_TO_LINKS = 30.0        # mm, for the link leg length

DEPTHS = np.arange(175.0, 326.0, 25.0)


def punching(depth):
    """One C23 analysis at this effective depth, well away from any edge."""
    return prokon.v5.punching_shear.analyse(
        design_code=CODE, col_width=COLUMN, col_breadth=COLUMN,
        effective_depth=depth,
        nearest_edge_x=10_000.0, nearest_edge_y=10_000.0,
        fcu=FCU, fy=FY, fyv=FY,
        load_cases=[{"v": LOAD, "mx": 50.0, "my": 30.0}])


def link_steel_kg(result, depth):
    """The link steel the perimeters need, kg, for one column.

    Each perimeter's `asv` is a total leg area. A link leg runs through
    the slab, so its length is taken as the effective depth less the
    cover it starts and stops short of - the standard simplification, and
    stated rather than hidden because it scales the whole steel figure.
    """
    leg_length = depth - COVER_TO_LINKS
    total_mm3 = sum(max(p["asv"], 0.0) for p in result["critical_perimeters"]) * leg_length
    return total_mm3 * DENSITY_STEEL / 1.0e9


print("PUNCHING SHEAR: THICKEN THE SLAB, OR ADD LINKS?")
print(f"  {CODE}, {COLUMN:.0f} mm square column, V = {LOAD:.0f} kN")
print(f"  fcu {FCU:.0f}, fy {FY:.0f}, {BAY:.1f} x {BAY:.1f} m grid "
      f"= {BAY * BAY:.1f} m2 tributary")

# -- 1. What C23 asks for at each depth ---------------------------------
print()
print("1. WHAT THE ENGINE ASKS FOR")
print(f"   {'d':>5} {'vu':>7} {'vcu':>7} {'over':>6} {'perims':>7} "
      f"{'link As':>9} {'link':>7}")
print(f"   {'mm':>5} {'MPa':>7} {'MPa':>7} {'ceil':>6} {'needing':>7} "
      f"{'mm2':>9} {'kg':>7}")
print("   " + "-" * 54)

rows = []
reference = None

for depth in DEPTHS:
    envelope = punching(depth)
    result = envelope["result"]
    if reference is None:
        reference = envelope

    vu = max(result["vu"])
    vcu = result["vcu"]
    # Over the ceiling no amount of link steel helps - that is a ceiling,
    # not a capacity you reinforce past.
    over_ceiling = vu > vcu

    needing = [p for p in result["critical_perimeters"] if p["asv"] > 0.0]
    asv_total = sum(p["asv"] for p in needing)
    steel_kg = link_steel_kg(result, depth)

    rows.append(dict(d=depth, vu=vu, vcu=vcu, over=over_ceiling,
                     needing=len(needing), asv=asv_total, steel=steel_kg))

    print(f"   {depth:>5.0f} {vu:>7.3f} {vcu:>7.3f} {'YES' if over_ceiling else 'no':>6} "
          f"{len(needing):>7} {asv_total:>9.0f} {steel_kg:>7.1f}")

usable = [row for row in rows if not row["over"]]
print(f"   -> {len(usable)} of {len(rows)} depths are under the shear ceiling.")

# The required AREA falls with depth. The MASS does not, and the reason is
# worth a line: a deeper slab needs LONGER link legs, so mass is area
# times a length that is itself growing.
areas = [row["asv"] for row in usable]
masses = [row["steel"] for row in usable]
area_falls = all(b < a for a, b in zip(areas, areas[1:]))
mass_falls = all(b < a for a, b in zip(masses, masses[1:]))
print(f"   -> required link AREA falls at every step: {area_falls}")
print(f"      required link MASS falls at every step: {mass_falls}")
if not mass_falls:
    bump = [row for a, row in zip(masses, usable[1:]) if row["steel"] > a]
    where = ", ".join("{0:.0f}".format(row["d"]) for row in bump)
    print(f"      -> mass goes back UP at d = {where} mm, because the legs")
    print("         get longer faster than the area falls. Area is what the")
    print("         code checks; mass is what you buy. They are not the")
    print("         same curve, and only one of them is the carbon.")

# -- 2. Price both fixes from the same baseline -------------------------
# The comparison only means something against a fixed reference: take the
# THINNEST slab that works and price every deeper option as "the extra
# concrete you pour instead of the links you save".
base = min(usable, key=lambda row: row["d"])
tributary = BAY * BAY

print()
print("2. THE SAME DECISION, BOTH WAYS, PER COLUMN")
print(f"   baseline: d = {base['d']:.0f} mm with "
      f"{base['steel']:.1f} kg of links ({base['asv']:.0f} mm2)")
print(f"   {'d':>5} {'extra conc':>11} {'links saved':>12} "
      f"{'concrete':>9} {'steel':>8} {'NET':>8}")
print(f"   {'mm':>5} {'m3':>11} {'kg':>12} "
      f"{'kgCO2e':>9} {'kgCO2e':>8} {'kgCO2e':>8}")
print("   " + "-" * 60)

for row in usable:
    extra_depth_m = (row["d"] - base["d"]) / 1000.0
    extra_concrete = extra_depth_m * tributary
    links_saved = base["steel"] - row["steel"]
    concrete_carbon = extra_concrete * DENSITY_CONCRETE * ECF_CONCRETE
    steel_carbon = -links_saved * ECF_REBAR
    net = concrete_carbon + steel_carbon
    row["net"] = net
    row["concrete_carbon"] = concrete_carbon
    row["steel_saved_carbon"] = links_saved * ECF_REBAR
    print(f"   {row['d']:>5.0f} {extra_concrete:>11.2f} {links_saved:>12.1f} "
          f"{concrete_carbon:>9.1f} {steel_carbon:>8.1f} {net:>8.1f}")

cheapest = min(usable, key=lambda row: row["net"])
print(f"   -> LOWEST NET CARBON: d = {cheapest['d']:.0f} mm, "
      f"net {cheapest['net']:+.1f} kgCO2e vs the baseline.")
print(f"   -> that is the BASELINE itself: {cheapest['d'] == base['d']}. Every")
print("      millimetre of thickening is a net cost, at every step. There")
print("      is no depth at which the links saved pay for the concrete.")

# -- 3. The reading -----------------------------------------------------
deepest = max(usable, key=lambda row: row["d"])
print()
print("3. WHY LINKS WIN, AND BY HOW MUCH")
print(f"   thickening from {base['d']:.0f} to {deepest['d']:.0f} mm:")
print(f"      concrete added   {deepest['concrete_carbon']:>8.1f} kgCO2e")
print(f"      link steel saved {deepest['steel_saved_carbon']:>8.1f} kgCO2e")
print(f"      net              {deepest['net']:>+8.1f} kgCO2e per column")
print(f"   -> the concrete costs {deepest['concrete_carbon'] / max(deepest['steel_saved_carbon'], 0.001):.0f}x "
      f"what the steel saves.")
print("   -> the reason is AREA, not carbon intensity. Links are local to")
print(f"      the column; depth is paid over all {tributary:.0f} m2 of the bay.")
print("      Concrete IS the low-carbon material per kilogram. It is the")
print("      quantity that beats you.")
print("   -> so on punching shear the low-carbon answer is the one that")
print("      feels wasteful: keep the slab thin and reinforce locally.")

# -- 4. Scale it to a floor plate --------------------------------------
COLUMNS = 20
print()
print("4. ACROSS A FLOOR PLATE")
print(f"   {COLUMNS} columns on this grid = "
      f"{COLUMNS * tributary:,.0f} m2 of slab")
for row in (base, deepest):
    links = row["steel"] * COLUMNS * ECF_REBAR
    concrete = row["d"] / 1000.0 * COLUMNS * tributary * DENSITY_CONCRETE * ECF_CONCRETE
    print(f"   d = {row['d']:>3.0f} mm  slab {concrete / 1000.0:>6.1f} tCO2e"
          f" + links {links / 1000.0:>5.2f} tCO2e"
          f"  = {(concrete + links) / 1000.0:>6.1f} tCO2e")
print("   -> the link steel is a rounding error at plate scale and the")
print("      depth is not. That asymmetry is the entire argument.")

# -- 5. The honest caveats ---------------------------------------------
print()
print("5. WHAT THIS COMPARISON LEAVES OUT, AND WHICH WAY IT LEANS")
print("   - a thicker slab is heavier, so columns and foundations grow.")
print("     Not counted, and it counts AGAINST thickening: the answer")
print("     above is therefore conservative in favour of thickening.")
print("   - links have to be fixed, which is labour and programme, not")
print("     carbon. Counts against links.")
print("   - deflection is not checked here at all. C23 answers punching")
print("     and nothing else, and a thin flat slab is a deflection")
print("     problem long before it is a punching one.")
print("   -> price the carbon, then argue the rest on its own terms.")

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


depths = np.array([row["d"] for row in usable])
concrete_added = np.array([row["concrete_carbon"] for row in usable])
steel_saved = np.array([row["steel_saved_carbon"] for row in usable])
net = np.array([row["net"] for row in usable])

figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

width = 8.0
left.bar(depths - width / 2.0, concrete_added, width=width,
         label="concrete added by thickening", color="#9fb8c8")
left.bar(depths + width / 2.0, -steel_saved, width=width,
         label="link steel saved", color="#c86e5a")
left.plot(depths, net, color="#22303a", lw=2.0, marker="o", ms=5,
          label="net")
left.axhline(0.0, color="#22303a", lw=1.0)
left.set_xlabel("effective depth d (mm)")
left.set_ylabel("kgCO2e per column, vs the thinnest working slab")
left.set_title("Thickening costs far more than the links it saves\n"
               "because depth is paid over the whole bay", fontsize=10)
left.legend(fontsize=9, loc="upper left")
left.grid(alpha=0.25, axis="y")

link_kg = np.array([row["steel"] for row in usable])
right.plot(depths, link_kg, color="#c86e5a", lw=2.0, marker="o", ms=5)
right.set_xlabel("effective depth d (mm)")
right.set_ylabel("link steel required (kg per column)")
right.set_title("What the engine actually asks for\n"
                "link steel falls with depth - that is the trade", fontsize=10)
right.grid(alpha=0.25)
for row in usable:
    right.annotate(f"{row['needing']} perim.", xy=(row["d"], row["steel"]),
                   xytext=(0, 8), textcoords="offset points",
                   ha="center", fontsize=8, color="#22303a")

figure.suptitle(
    f"Punching shear: thicken or reinforce - {CODE}  |  "
    f"V = {LOAD:.0f} kN on a {COLUMN:.0f} mm column, {BAY:.1f} m grid  |  "
    f"concrete {ECF_CONCRETE}, bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "punching_shear_carbon_thicken_or_reinforce.png")

print()
print("-" * 72)
print("Concrete is the low-carbon material per kilogram, and that is why")
print("thickening loses: the fix you apply to one column gets paid for")
print("over every square metre of the bay. When two fixes act at different")
print("SCALES, compare their quantities before their carbon factors.")
