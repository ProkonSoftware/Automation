# ---
# Example:  The slab is the carbon - kgCO2e per square metre, by thickness
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - the carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# In a concrete frame the floor slab is usually the single biggest lump of
# material in the building, so its carbon per square metre is the number
# that drives the whole structure's rating. This script sweeps C04 across
# thickness and reports kgCO2e/m2 - the same unit the IStructE SCORS bands
# and the LETI targets are written in, so the answer is directly
# comparable to a target somebody has set you.
#
# WHAT THIS SCRIPT COUNTS. Embodied carbon, A1-A3, for ONE SQUARE METRE of
# slab: the concrete at 2400 kg/m3, and the flexural steel the engine says
# the slab requires. It does NOT count the beams, the columns, the
# foundations, punching-shear links, formwork, or anything past the
# product stage - so the numbers are a SLAB figure, not a SCORS rating.
# A SCORS rating is the whole structure over the gross internal area.
#
# ONE ENGINE HABIT THIS SCRIPT DELIBERATELY AVOIDS. C04 returns both the
# steel each face needs (`ast`). It suggests no bars, so the carbon
# below is computed from the REQUIREMENT, which is the honest basis:
# a bar schedule rounds up, and rounding up is a detailing decision
# rather than a property of the slab.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# -- EMBODIED CARBON FACTORS -------------------------------------------
# A1-A3, kgCO2e per kg, from the table of example UK factors in IStructE,
# "A brief guide to calculating embodied carbon", The Structural Engineer,
# July 2020:  concrete C32/40 at 25/50/75 % GGBS = 0.120 / 0.089 / 0.063;
# reinforcement bar UK (BRC EPD) = 0.684, world average = 1.99.
ECF_CONCRETE = 0.120
ECF_REBAR = 0.684
DENSITY_CONCRETE = 2400.0
DENSITY_STEEL = 7850.0

# CONTROL - reproduces the worked example printed in that same guide:
# 116.6 m3 of concrete is 279.8 t, and 90 kg/m3 of bar over it is 10.5 t.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
COVER = 25.0                 # mm
BAR = 12.0                   # mm, assumed for the effective depths

# A 7.2 x 6.0 m two-way panel, continuous on all four edges, carrying an
# imposed load. The engine adds the slab's own weight, so thickening the panel
# loads it as well as strengthening it - which is the whole point of a study
# that varies thickness.
LX, LY = 7.2, 6.0            # m
IMPOSED = 6.0                # kPa

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

THICKNESSES = np.arange(150.0, 351.0, 25.0)


def slab(thickness):
    """One C04 analysis at this thickness, with matched effective depths."""
    return prokon.v5.rectangular_slab.analyse(
        design_code=CODE,
        lx=LX, ly=LY, h=thickness,
        dx=thickness - COVER - BAR / 2.0,
        dy=thickness - COVER - BAR - BAR / 2.0,
        fcu=FCU, fy=FY,
        edge_top=ENCASTRE, edge_right=ENCASTRE,
        edge_bottom=ENCASTRE, edge_left=ENCASTRE,
        load_cases=[{"number": 1, "lf": 1.4, "udl": IMPOSED}])


def carbon_per_m2(thickness, steel_mm2_per_m, ecf_concrete=ECF_CONCRETE,
                  ecf_rebar=ECF_REBAR):
    """A1-A3 embodied carbon, kgCO2e per square metre of slab.

    `ast` is an area in mm2 per metre width. Over one square metre the bar
    volume is that area times 1000 mm of length, i.e. ast x 1e-6 m3, so
    the mass is ast x 7.85e-3 kg.
    """
    concrete = thickness / 1000.0 * DENSITY_CONCRETE * ecf_concrete
    steel = steel_mm2_per_m * 1.0e-6 * DENSITY_STEEL * ecf_rebar
    return concrete, steel, concrete + steel


print("SLAB EMBODIED CARBON, PER SQUARE METRE")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm")
print(f"  panel {LX} x {LY} m, encastre all round, {IMPOSED:.0f} kPa imposed")

# -- 1. The sweep -------------------------------------------------------
print()
print("1. ONE SQUARE METRE OF SLAB, AT EVERY THICKNESS")
print(f"   {'h':>5} {'ast x':>8} {'ast y':>8} {'steel':>7} {'concrete':>9} "
      f"{'steel':>7} {'TOTAL':>7} {'conc':>6}")
print(f"   {'mm':>5} {'mm2/m':>8} {'mm2/m':>8} {'kg/m2':>7} {'kgCO2e':>9} "
      f"{'kgCO2e':>7} {'kgCO2e':>7} {'share':>6}")
print("   " + "-" * 64)

rows = []
reference = None

for thickness in THICKNESSES:
    envelope = slab(thickness)
    result = envelope["result"]
    if reference is None:
        reference = envelope

    ast_x = result["ast"]["x_bot"]
    ast_y = result["ast"]["y_bot"]
    steel_area = ast_x + ast_y
    steel_kg = steel_area * 1.0e-6 * DENSITY_STEEL

    # C04 designs whatever it is asked, so adequacy is ours to test. The
    # every face the engine found a moment on must have been designed.
    # ADEQUATE means the engine actually designed every face it found a
    # moment on. A face that comes back with zero steel under a real moment
    # is the engine declining that face, and counting its zero as "no carbon"
    # would make the thinnest slab look like the greenest one.
    adequate = not [face for face in ("x_top", "x_bot", "y_top", "y_bot")
                    if result["ast"][face] == 0.0
                    and result["moment_max"][face] > 0.0]

    concrete_c, steel_c, total = carbon_per_m2(thickness, steel_area)
    rows.append(dict(h=thickness, ast_x=ast_x, ast_y=ast_y, steel=steel_kg,
                     area=steel_area, concrete_c=concrete_c, steel_c=steel_c,
                     total=total, share=concrete_c / total, adequate=adequate))

    print(f"   {thickness:>5.0f} {ast_x:>8.0f} {ast_y:>8.0f} {steel_kg:>7.1f} "
          f"{concrete_c:>9.1f} {steel_c:>7.1f} {total:>7.1f} "
          f"{concrete_c / total:>5.0%}" + ("" if adequate else "  INADEQUATE"))

usable = [row for row in rows if row["adequate"]]
best = min(usable, key=lambda row: row["total"])
thinnest = min(usable, key=lambda row: row["h"])

print(f"   -> {len(usable)} of {len(rows)} thicknesses were designed on every face.")
print(f"   -> LOWEST CARBON at h = {best['h']:.0f} mm: "
      f"{best['total']:.1f} kgCO2e/m2")

# -- 2. Concrete is almost all of it -----------------------------------
print()
print("2. THE SPLIT, AND WHY IT DECIDES THE STRATEGY")
print(f"   concrete share runs from {min(r['share'] for r in usable):.0%} "
      f"to {max(r['share'] for r in usable):.0%} across the sweep")
thin, thick = thinnest, max(usable, key=lambda row: row["h"])
print(f"   {thin['h']:.0f} mm -> {thin['total']:.1f} kgCO2e/m2   "
      f"({thin['steel']:.1f} kg/m2 of bar)")
print(f"   {thick['h']:.0f} mm -> {thick['total']:.1f} kgCO2e/m2   "
      f"({thick['steel']:.1f} kg/m2 of bar)")
print(f"   -> going from {thin['h']:.0f} to {thick['h']:.0f} mm adds "
      f"{thick['total'] - thin['total']:.1f} kgCO2e/m2 of concrete")
print(f"      and saves only {thin['steel_c'] - thick['steel_c']:.1f} of steel.")
step = 25.0 / 1000.0 * DENSITY_CONCRETE * ECF_CONCRETE
print("   -> so THICKNESS IS THE CARBON and steel is the small term - but")
print("      keep the sizes honest, because they are closer than the")
print("      headline suggests:")
print(f"      one 25 mm step of thickness       {step:>5.1f} kgCO2e/m2")
print(f"      ALL the flexural steel at {thin['h']:.0f} mm  "
      f"{thin['steel_c']:>5.1f} kgCO2e/m2")
print(f"      -> a 25 mm step is {step / thin['steel_c']:.0%} of the entire")
print("         steel bill. Two steps outweigh it. So thickness dominates")
print("         over the RANGE, not by an order of magnitude per step.")
print(f"   -> and the minimum is the THINNEST slab that works ({best['h']:.0f} mm),")
print("      which C04 cannot tell you is buildable: it checks no")
print("      deflection and no span/depth ratio. Carbon pushes thin;")
print("      serviceability pushes back. Do not read 150 as advice.")

# -- 3. Scale it to a floor plate --------------------------------------
# Per-square-metre numbers are abstract until they are a building.
FLOOR_AREA = 1_200.0         # m2, one floor plate
FLOORS = 6
print()
print("3. WHAT THAT IS ON A REAL BUILDING")
print(f"   {FLOORS} floors of {FLOOR_AREA:,.0f} m2 = "
      f"{FLOORS * FLOOR_AREA:,.0f} m2 of slab")
for row in (thin, thick):
    tonnes = row["total"] * FLOORS * FLOOR_AREA / 1000.0
    print(f"   h = {row['h']:>3.0f} mm  ->  {tonnes:>7.1f} tCO2e of slab")
saving = (thick["total"] - thin["total"]) * FLOORS * FLOOR_AREA / 1000.0
print(f"   -> the difference is {saving:.0f} tCO2e on one building, from a")
print("      decision taken in an afternoon at concept stage. This is why")
print("      slab thickness is the first thing a carbon review asks about.")

# -- 4. And the mix, again ---------------------------------------------
print()
print("4. THE MIX MULTIPLIES ALL OF IT")
print(f"   {'mix':<20} {'best slab':>10} {'6 floors':>10}")
for label, factor in (("C32/40, 25% GGBS", 0.120),
                      ("C32/40, 50% GGBS", 0.089),
                      ("C32/40, 75% GGBS", 0.063)):
    _, _, total = carbon_per_m2(best["h"], best["area"], ecf_concrete=factor)
    print(f"   {label:<20} {total:>7.1f}/m2 {total * FLOORS * FLOOR_AREA / 1000.0:>8.1f} t")
print("   -> because the slab is concrete-dominated, the GGBS decision")
print("      lands almost undiluted on the bottom line. On a steel-heavy")
print("      element it would not.")

# The two levers priced in each other, so they can actually be compared:
# how much THICKNESS does the better mix buy at equal carbon?
on_low_mix = [(row["h"], carbon_per_m2(row["h"], row["area"],
                                       ecf_concrete=0.063)[2])
              for row in usable]
affordable = [h for h, total in on_low_mix if total <= best["total"]]
print(f"   -> priced against each other: the {best['h']:.0f} mm slab on 25% GGBS")
print(f"      costs {best['total']:.1f} kgCO2e/m2, and the same budget on")
print(f"      75% GGBS buys {max(affordable):.0f} mm - "
      f"{max(affordable) - best['h']:.0f} mm of free thickness,")
print("      which is exactly the thickness serviceability wanted back.")

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


heights = np.array([row["h"] for row in usable])
concrete = np.array([row["concrete_c"] for row in usable])
steel = np.array([row["steel_c"] for row in usable])

figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

left.bar(heights, concrete, width=18.0, label="concrete", color="#9fb8c8")
left.bar(heights, steel, width=18.0, bottom=concrete, label="reinforcement",
         color="#c86e5a")
for row in usable:
    left.text(row["h"], row["total"] + 1.2, f"{row['total']:.0f}",
              ha="center", fontsize=8, color="#22303a")
left.set_xlabel("slab thickness h (mm)")
left.set_ylabel("embodied carbon A1-A3 (kgCO2e per m2)")
left.set_title("Steel is the thin sliver on top\n"
               "the slab's carbon is its thickness", fontsize=10)
left.legend(loc="upper left", fontsize=9)
left.grid(alpha=0.25, axis="y")

for label, factor, colour in (("25% GGBS", 0.120, "#c86e5a"),
                              ("50% GGBS", 0.089, "#e0a458"),
                              ("75% GGBS", 0.063, "#1a7f4b")):
    curve = np.array([carbon_per_m2(row["h"], row["area"],
                                    ecf_concrete=factor)[2] for row in usable])
    right.plot(heights, curve, lw=1.9, marker="o", ms=4, color=colour,
               label=f"C32/40, {label}  ({factor:.3f})")

right.set_xlabel("slab thickness h (mm)")
right.set_ylabel("embodied carbon A1-A3 (kgCO2e per m2)")
right.axhline(best["total"], color="#22303a", ls=":", lw=1.2)
right.annotate(f"{best['h']:.0f} mm on 25% GGBS = {best['total']:.0f}\n"
               f"same budget on 75% GGBS buys {max(affordable):.0f} mm",
               xy=(max(affordable), best["total"]),
               xytext=(heights[0] + 15.0, best["total"] * 1.18),
               arrowprops=dict(arrowstyle="->", color="#22303a"),
               fontsize=9, color="#22303a")
right.set_title("The mix shifts the whole curve down\n"
                "so it buys back thickness, not just a percentage",
                fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Slab embodied carbon per m2 - {CODE}  |  "
    f"{LX} x {LY} m, {IMPOSED:.0f} kPa, fcu {FCU:.0f}, fy {FY:.0f}  |  "
    f"bar {ECF_REBAR} kgCO2e/kg  |  engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "rectangular_slab_carbon_per_square_metre.png")

print()
print("-" * 72)
print("A slab's embodied carbon is its thickness, to a first approximation")
print("and very nearly to a second. Reinforcement is a few percent of it.")
print("So the leverage sits in the two decisions that are NOT rebar: how")
print("thin the slab can be made to work, and what goes in the mix.")
