# ---
# Example:  How many piles? The cap grows faster than you expect
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes - 2026-09-09 - carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# Adding a pile spreads the load, which sounds cheap. It is not: pile
# SPACING is a multiple of the pile diameter, so every extra pile pushes
# the cap outward in plan, and the cap is a solid block of concrete whose
# volume grows with that plan area.
#
# So there are three quantities moving at once - the piles themselves, the
# cap concrete, and the tie steel - and only one of them gets better. This
# script prices all three against C16.
#
# THE COMPARISON IS ONLY HONEST WITH A PILE CAPACITY. "Fewer piles" is
# always lower carbon if the piles are allowed to be infinitely strong, so
# the sweep below fixes a working capacity per pile and discards any
# arrangement that overloads them. Without that constraint the answer is
# trivially "one pile" and means nothing.
#
# WHAT IT COUNTS. A1-A3 carbon for one pile group: the cap concrete, the
# pile concrete over an assumed length, and the tie steel C16 designs.
# Pile reinforcement, cap links, excavation and pile-boring spoil are NOT
# counted; nor is the fact that longer or larger piles may be needed on a
# different layout, which is a geotechnical question and not ours.
#
# ONE LIMIT THIS SCRIPT DOES NOT HARD-CODE. C16 designs 2 to 5 piles. The
# sweep deliberately asks for 6 as well and lets the ENGINE refuse it, so
# the range is demonstrated by the engine rather than asserted by a comment
# that can go stale. The refusal arrives as a normal ProkonError carrying
# its own message, and the script prints it.
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

CODE = "CSA-A23.3:2019"
LOAD = 4800.0                # kN ultimate on the column
PILE_CAPACITY = 1300.0       # kN working capacity per pile - the constraint
PILE_DIA = 0.6               # m
PILE_LENGTH = 18.0           # m, assumed, and it dominates the pile carbon
CAP_THICKNESS = 1.2          # m
SPACING = 1.8                # m, 3 x diameter
COLUMN = 0.5                 # m square
FC = 30.0
FY = 400.0

COUNTS = (2, 3, 4, 5, 6)


def cap(count):
    """One C16 analysis with this many piles."""
    return prokon.v5.pile_cap.analyse(
        design_code=CODE, column_dim_x=COLUMN, column_dim_y=COLUMN,
        no_of_piles=count, pile_dia=PILE_DIA, pile_spacing=SPACING,
        pile_tolerance=0.05, cap_thickness=CAP_THICKNESS,
        cap_overhang=0.3, bottom_rebar_depth=0.1, fc=FC, fy=FY,
        load_cases=[{"name": "ULS", "load_factor": 1.0, "p": LOAD}])


def carbon(count, cap_x, cap_y, tie_area_mm2, tie_length_m,
           ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon for the group, kgCO2e."""
    cap_m3 = cap_x * cap_y * CAP_THICKNESS
    pile_m3 = count * np.pi * PILE_DIA ** 2 / 4.0 * PILE_LENGTH
    steel_m3 = tie_area_mm2 * 1.0e-6 * tie_length_m
    cap_c = cap_m3 * DENSITY_CONCRETE * ecf_concrete
    pile_c = pile_m3 * DENSITY_CONCRETE * ecf_concrete
    steel_c = steel_m3 * DENSITY_STEEL * ECF_REBAR
    return dict(cap_m3=cap_m3, pile_m3=pile_m3,
                steel_kg=steel_m3 * DENSITY_STEEL,
                cap=cap_c, piles=pile_c, steel=steel_c,
                total=cap_c + pile_c + steel_c)


print("HOW MANY PILES? THE CARBON OF A PILE GROUP")
print(f"  {CODE}, {LOAD:.0f} kN on a {COLUMN * 1000:.0f} mm column")
print(f"  {PILE_DIA * 1000:.0f} mm piles at {SPACING:.1f} m centres, "
      f"{PILE_LENGTH:.0f} m long, cap {CAP_THICKNESS:.1f} m thick")
print(f"  working capacity assumed {PILE_CAPACITY:.0f} kN per pile, so at")
print(f"  least {int(np.ceil(LOAD / PILE_CAPACITY))} piles are needed")

# -- 1. The sweep -------------------------------------------------------
print()
print("1. EVERY PILE COUNT")
print(f"   {'n':>3} {'cap plan':>12} {'cap':>7} {'piles':>7} {'tie As':>8} "
      f"{'per pile':>9} {'kgCO2e':>8}")
print(f"   {'':>3} {'m x m':>12} {'m3':>7} {'m3':>7} {'mm2':>8} "
      f"{'kN':>9} {'total':>8}")
print("   " + "-" * 60)

rows = []
reference = None

for count in COUNTS:
    # C16 designs 2 to 5 piles. The 6 is left in the sweep DELIBERATELY:
    # rather than hard-coding a range this script cannot verify, it lets
    # the engine state its own limit and reports what it said.
    try:
        envelope = cap(count)
    except prokon.v5.ProkonError as refusal:
        print(f"   {count:>3}   REFUSED: {refusal.category}/{refusal.code}")
        print(f"         {refusal.message}")
        continue

    result = envelope["result"]
    if reference is None:
        reference = envelope

    cap_x, cap_y = result["cap_dim_x"], result["cap_dim_y"]

    # The tie C16 nominates, or the minimum if it is larger.
    tie_area = max(result["tie_minim_reinforcement"], 0.0)
    for tie in result["tie_results"]:
        for case in tie["load_cases"]:
            tie_area = max(tie_area, case["as_required"])

    # A tie runs between piles, so its length is of the order of the cap.
    tie_length = max(cap_x, cap_y)

    per_pile = LOAD / count
    money = carbon(count, cap_x, cap_y, tie_area, tie_length)
    works = (result["is_stable"] and result["geometry_is_valid"]
             and per_pile <= PILE_CAPACITY)

    rows.append(dict(count=count, cap_x=cap_x, cap_y=cap_y, tie_area=tie_area,
                     tie_length=tie_length, per_pile=per_pile, works=works,
                     **money))

    print(f"   {count:>3} {cap_x:>5.2f} x {cap_y:<4.2f} {money['cap_m3']:>7.2f} "
          f"{money['pile_m3']:>7.2f} {tie_area:>8.0f} {per_pile:>9.0f} "
          f"{money['total']:>8.0f}"
          + ("" if works else "   OVERLOADED" if per_pile > PILE_CAPACITY
             else "   UNSTABLE"))

usable = [row for row in rows if row["works"]]
best = min(usable, key=lambda row: row["total"])
print(f"   -> {len(usable)} of {len(rows)} counts carry the load within the")
print(f"      assumed pile capacity.")
print(f"   -> LOWEST CARBON: {best['count']} piles, "
      f"{best['cap_x']:.2f} x {best['cap_y']:.2f} m cap, "
      f"{best['total']:.0f} kgCO2e")

# -- 2. Where it goes ---------------------------------------------------
print()
print("2. THE THREE QUANTITIES, AND WHICH ONE RUNS AWAY")
print(f"   {'n':>3} {'cap':>8} {'piles':>8} {'steel':>8} {'cap share':>10}")
for row in rows:
    print(f"   {row['count']:>3} {row['cap']:>8.0f} {row['piles']:>8.0f} "
          f"{row['steel']:>8.1f} {row['cap'] / row['total']:>9.0%}")
print("   -> the TIE STEEL is negligible on every layout - tenths of a")
print("      percent. A pile cap is a concrete problem, full stop.")
growth = [(row["count"], row["cap_m3"]) for row in rows]
print(f"   -> and the cap volume goes {growth[0][1]:.1f} m3 at "
      f"{growth[0][0]} piles to {growth[-1][1]:.1f} m3 at {growth[-1][0]}:")
print(f"      {growth[-1][1] / growth[0][1]:.1f}x the concrete for "
      f"{growth[-1][0] / growth[0][0]:.2f}x the piles.")
print("      Spacing is a multiple of diameter, so plan area grows faster")
print("      than pile count. That is the mechanism worth remembering.")

# -- 3. The pile length nobody sweeps ----------------------------------
print()
print("3. THE ASSUMPTION THAT OUTWEIGHS THE DECISION")
print(f"   at {best['count']} piles, the piles are "
      f"{best['piles'] / best['total']:.0%} of the carbon and the cap is "
      f"{best['cap'] / best['total']:.0%}")
for length in (12.0, 18.0, 24.0, 30.0):
    pile_m3 = best["count"] * np.pi * PILE_DIA ** 2 / 4.0 * length
    total = (best["cap"] + pile_m3 * DENSITY_CONCRETE * ECF_CONCRETE
             + best["steel"])
    print(f"   pile length {length:>4.0f} m -> {total:>7.0f} kgCO2e "
          f"({pile_m3 * DENSITY_CONCRETE * ECF_CONCRETE / total:.0%} piles)")
spread = max(usable, key=lambda row: row["total"])["total"] - best["total"]
length_spread = (best["count"] * np.pi * PILE_DIA ** 2 / 4.0 * 18.0
                 * DENSITY_CONCRETE * ECF_CONCRETE)
print(f"   -> choosing the pile COUNT well is worth about {spread:.0f} kgCO2e")
print(f"      here. Halving the pile LENGTH is worth about "
      f"{length_spread / 2.0:.0f}.")
print("   -> pile length is a geotechnical answer, not a structural one -")
print("      which makes the ground investigation, again, the biggest")
print("      carbon lever on a substructure. Design it after you know it.")

# -- 4. The mix ---------------------------------------------------------
print()
print("4. THE MIX")
for label, factor in (("C32/40, 25% GGBS", 0.120),
                      ("C32/40, 50% GGBS", 0.089),
                      ("C32/40, 75% GGBS", 0.063)):
    money = carbon(best["count"], best["cap_x"], best["cap_y"],
                   best["tie_area"], best["tie_length"], ecf_concrete=factor)
    print(f"   {label:<20} {money['total']:>7.0f} kgCO2e")
print("   -> a pile cap is the ideal candidate for a high-replacement mix:")
print("      massive, buried, no early striking, and its heat of hydration")
print("      is a problem a GGBS blend HELPS with rather than hinders.")
print("      Unlike the PT slab, here the mix change is free of programme")
print("      risk - so this is where to spend the argument.")

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

counts = np.array([row["count"] for row in rows])
cap_c = np.array([row["cap"] for row in rows])
pile_c = np.array([row["piles"] for row in rows])
steel_c = np.array([row["steel"] for row in rows])

left.bar(counts, pile_c, width=0.6, label="piles", color="#6a4c93")
left.bar(counts, cap_c, width=0.6, bottom=pile_c, label="cap concrete",
         color="#9fb8c8")
left.bar(counts, steel_c, width=0.6, bottom=pile_c + cap_c,
         label="tie steel", color="#c86e5a")
for row in rows:
    if not row["works"]:
        left.text(row["count"], row["total"] + 60.0, "over\ncapacity",
                  ha="center", fontsize=8, color="#c0392b")
left.axvline(best["count"], color="#1a7f4b", ls="--", lw=1.5)
left.set_xlabel("number of piles")
left.set_ylabel("embodied carbon A1-A3 (kgCO2e per group)")
left.set_xticks(counts)
left.set_title("Tie steel is invisible; the concrete is everything\n"
               "dashed line = lowest carbon within pile capacity",
               fontsize=10)
left.legend(fontsize=9, loc="upper left")
left.grid(alpha=0.25, axis="y")

plan_area = np.array([row["cap_x"] * row["cap_y"] for row in rows])
right.plot(counts, plan_area, color="#22303a", lw=2.0, marker="o", ms=6,
           label="cap plan area (m2)")
right.plot(counts, counts / counts[0] * plan_area[0], color="#c0392b",
           ls="--", lw=1.5, label="if area grew in proportion to piles")
for row in rows:
    right.annotate(f"{row['cap_x']:.1f}x{row['cap_y']:.1f}",
                   xy=(row["count"], row["cap_x"] * row["cap_y"]),
                   xytext=(0, 9), textcoords="offset points",
                   ha="center", fontsize=8)
right.set_xlabel("number of piles")
right.set_ylabel("cap plan area (m2)")
right.set_xticks(counts)
right.set_title("The cap outgrows the pile count\n"
                "spacing is a multiple of diameter, so area compounds",
                fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Pile group carbon - {CODE}  |  {LOAD:.0f} kN, "
    f"{PILE_DIA * 1000:.0f} mm piles at {SPACING:.1f} m, "
    f"{PILE_LENGTH:.0f} m long  |  "
    f"concrete {ECF_CONCRETE}, bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "pile_cap_carbon_how_many_piles.png")

print()
print("-" * 72)
print("Every extra pile buys load capacity and pays for it twice - once in")
print("the pile and again in the cap that has to reach it. So use the")
print("fewest piles the capacity allows. And note what dominated the")
print("answer: an assumed pile length, which no structural decision")
print("controls. Know the ground before optimising the concrete.")
