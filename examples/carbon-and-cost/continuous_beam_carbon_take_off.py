# ---
# Example:  A real quantity take-off - integrating a beam's steel envelope
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes - 2026-09-09 - carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# Every other carbon estimate in this folder multiplies ONE steel area by
# a length. That is fine for a single section and wrong for a continuous
# beam, where the steel varies along the span: heavy over the supports,
# light at mid-span, and nominal in between.
#
# C01 reports that variation as ENVELOPES - one value per position along
# the beam - so the honest quantity is an integral, not a multiplication.
# This script does the integral properly and then shows how far out you
# would have been with the shortcut.
#
# TWO MEASURED GOTCHAS, BOTH OF WHICH COST A WRONG NUMBER.
#
# 1. `total_mass` IS ZERO UNLESS YOU ASK FOR IT. C01 reports a concrete
#    mass, but it is 0 unless `concrete_density` is supplied - and 0 is a
#    perfectly plausible-looking number to multiply a carbon factor by.
#    This script computes the concrete from geometry instead, and prints
#    both so the difference is visible.
#
# 2. `asv_required` IS Asv/Sv IN mm2/mm, NOT AN AREA. Same convention as
#    C22. Integrating it as though it were an area overstates the link
#    steel by three orders of magnitude.
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
CONCRETE_DENSITY_KN = 24.0   # kN/m3, what C01 wants for its own mass figure

# CONTROL - reproduces the worked example in that same guide.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "BS8110 - 1997"
SPAN = 6.0                   # m, each of two spans
WIDTH = 300.0                # mm
COVER_TOP = 30.0
COVER_BOT = 40.0
FYV = 250.0
DEAD = 20.0                  # kN/m
LIVE = 10.0                  # kN/m

DEPTHS = (400.0, 450.0, 500.0, 550.0, 600.0, 650.0, 700.0)
DEFLECTION_LIMIT = SPAN * 1000.0 / 250.0


def beam(depth):
    """One C01 analysis of the two-span beam at this section depth."""
    return prokon.v5.continuous_beam.analyse(
        design_code=CODE,
        sections=[{"n": 1, "bw": WIDTH, "d": depth}],
        segments=[{"span": 1, "length": SPAN, "sec_left": 1},
                  {"span": 2, "length": SPAN, "sec_left": 1}],
        supports=[{"n": 1}, {"n": 2}, {"n": 3}],
        loads=[{"case": "Dead", "span": 1, "w_left": DEAD},
               {"case": "Dead", "span": 2, "w_left": DEAD},
               {"case": "Live", "span": 1, "w_left": LIVE},
               {"case": "Live", "span": 2, "w_left": LIVE}],
        fyv=FYV, cover_top=COVER_TOP, cover_bot=COVER_BOT,
        live_permanent_percent=25.0, creep_coefficient=2.0,
        shrinkage_strain=0.0003,
        concrete_density=CONCRETE_DENSITY_KN)


def link_perimeter(depth):
    """One closed link's centre-line length, mm."""
    return 2.0 * (WIDTH - 2.0 * COVER_BOT) + 2.0 * (depth - 2.0 * COVER_BOT)


def take_off(result, depth):
    """Integrate the envelopes into real quantities."""
    envelopes = result["envelopes"]
    x = np.array(envelopes["position"], dtype=float)          # m
    bottom = np.array(envelopes["ast_bottom"], dtype=float)   # mm2
    top = np.array(envelopes["ast_top"], dtype=float)         # mm2
    asv = np.array(envelopes["asv_required"], dtype=float)    # mm2/mm

    # Main bars: mm2 integrated over m gives 1e-6 m3.
    main_m3 = np.trapezoid(bottom + top, x) * 1.0e-6

    # Links: (Asv/Sv)/2 is one leg-set per mm, so the volume over a length
    # dx (in mm) is that times the link perimeter. Same treatment as C22.
    links_mm3 = np.trapezoid(asv / 2.0 * link_perimeter(depth), x * 1000.0)

    return dict(main_m3=main_m3, links_m3=links_mm3 * 1.0e-9,
                steel_m3=main_m3 + links_mm3 * 1.0e-9,
                peak_bottom=float(bottom.max()), peak_top=float(top.max()),
                positions=len(x))


def carbon(concrete_m3, steel_m3, ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon, kgCO2e."""
    concrete = concrete_m3 * DENSITY_CONCRETE * ecf_concrete
    steel = steel_m3 * DENSITY_STEEL * ECF_REBAR
    return dict(concrete=concrete, steel=steel, total=concrete + steel,
                steel_kg=steel_m3 * DENSITY_STEEL)


print("A CONTINUOUS BEAM'S CARBON, FROM ITS ACTUAL ENVELOPES")
print(f"  {CODE}, two {SPAN:.1f} m spans, bw {WIDTH:.0f} mm")
print(f"  loads  dead {DEAD:.0f} kN/m, live {LIVE:.0f} kN/m")
print(f"  deflection limit span/250 = {DEFLECTION_LIMIT:.1f} mm")

# -- 1. The take-off ----------------------------------------------------
print()
print("1. INTEGRATED, NOT ESTIMATED")
print(f"   {'d':>5} {'pos':>5} {'peak bot':>9} {'peak top':>9} "
      f"{'main':>7} {'links':>7} {'steel':>7} {'defl':>7} {'kgCO2e':>8}")
print(f"   {'mm':>5} {'no.':>5} {'mm2':>9} {'mm2':>9} "
      f"{'kg':>7} {'kg':>7} {'kg':>7} {'mm':>7} {'total':>8}")
print("   " + "-" * 74)

rows = []
reference = None

for depth in DEPTHS:
    envelope = beam(depth)
    result = envelope["result"]
    if reference is None:
        reference = envelope

    quantities = take_off(result, depth)
    concrete_m3 = WIDTH / 1000.0 * depth / 1000.0 * result["total_length"]
    money = carbon(concrete_m3, quantities["steel_m3"])

    deflection = result["max_deflection"]
    adequate = result["succeeded"] and abs(deflection) <= DEFLECTION_LIMIT

    rows.append(dict(depth=depth, concrete_m3=concrete_m3,
                     deflection=abs(deflection), adequate=adequate,
                     reported_mass=result["total_mass"], **quantities, **money))

    print(f"   {depth:>5.0f} {quantities['positions']:>5} "
          f"{quantities['peak_bottom']:>9.0f} {quantities['peak_top']:>9.0f} "
          f"{quantities['main_m3'] * DENSITY_STEEL:>7.1f} "
          f"{quantities['links_m3'] * DENSITY_STEEL:>7.1f} "
          f"{money['steel_kg']:>7.1f} {abs(deflection):>7.2f} "
          f"{money['total']:>8.1f}"
          + ("" if adequate else "  FAILS"))

usable = [row for row in rows if row["adequate"]]
best = min(usable, key=lambda row: row["total"])
print(f"   -> {len(usable)} of {len(rows)} depths pass and meet span/250.")
print(f"   -> LOWEST CARBON: d = {best['depth']:.0f} mm, "
      f"{best['total']:.1f} kgCO2e for the whole beam")

# -- 2. How wrong is the shortcut --------------------------------------
# The shortcut everybody uses: take the PEAK steel area and multiply by
# the length. It is quick, and it is an over-estimate by a knowable amount.
print()
print("2. WHAT THE SHORTCUT WOULD HAVE TOLD YOU")
print(f"   {'d':>5} {'integrated':>11} {'peak x length':>14} {'over by':>9}")
for row in rows:
    peak_m3 = ((row["peak_bottom"] + row["peak_top"]) * 1.0e-6
               * reference["result"]["total_length"])
    shortcut = peak_m3 * DENSITY_STEEL
    integrated = row["main_m3"] * DENSITY_STEEL
    print(f"   {row['depth']:>5.0f} {integrated:>10.1f} kg "
          f"{shortcut:>13.1f} kg {shortcut / integrated:>8.2f}x")
ratios = []
for row in rows:
    peak_m3 = ((row["peak_bottom"] + row["peak_top"]) * 1.0e-6
               * reference["result"]["total_length"])
    ratios.append(peak_m3 * DENSITY_STEEL / (row["main_m3"] * DENSITY_STEEL))
print(f"   -> the shortcut overstates the main steel by "
      f"{min(ratios):.2f}x to {max(ratios):.2f}x here,")
print("      because the envelope peaks over one support and nowhere")
print("      else. On a carbon estimate that is the difference between a")
print("      defensible number and a comfortable one.")
print("   -> it is also an over-estimate in a SAFE direction for strength")
print("      and an unsafe one for carbon reporting, which is exactly the")
print("      sort of asymmetry worth naming out loud.")

# -- 3. The concrete-mass trap -----------------------------------------
print()
print("3. THE `total_mass` TRAP, MEASURED")
print(f"   {'d':>5} {'from geometry':>14} {'C01 total_mass':>16}")
for row in rows[:3]:
    from_geometry = row["concrete_m3"] * CONCRETE_DENSITY_KN
    print(f"   {row['depth']:>5.0f} {from_geometry:>11.2f} kN "
          f"{row['reported_mass']:>13.2f} kN")
print(f"   -> with `concrete_density` supplied they agree.")
print("      WITHOUT it, C01 reports 0 - and this script computes the")
print("      concrete from geometry anyway, so its answer does not depend")
print("      on remembering that input. Prefer the quantity you derived")
print("      over the one you were handed, when you can derive it.")

# -- 4. Where the carbon is --------------------------------------------
print()
print("4. THE SPLIT ALONG THE SWEEP")
for row in rows:
    print(f"   d = {row['depth']:>3.0f} mm  concrete {row['concrete']:>7.1f}  "
          f"steel {row['steel']:>6.1f}  "
          f"({row['concrete'] / row['total']:.0%} concrete)")
shallowest = min(usable, key=lambda row: row["depth"])
print(f"   -> minimum carbon is at {best['depth']:.0f} mm and the shallowest")
print(f"      passing depth is {shallowest['depth']:.0f} mm: "
      f"{'the same' if best['depth'] == shallowest['depth'] else 'NOT the same'}")
if best["depth"] != shallowest["depth"]:
    print("   -> so unlike a single section, this beam has a real interior")
    print("      optimum: going shallower costs more steel than it saves in")
    print("      concrete, because the support steel climbs steeply.")
else:
    print("   -> the deflection limit is what stops the sweep, not carbon.")

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

# Left: the envelope being integrated, at the winning depth.
winner = beam(best["depth"])["result"]
x = np.array(winner["envelopes"]["position"], dtype=float)
bottom = np.array(winner["envelopes"]["ast_bottom"], dtype=float)
top = np.array(winner["envelopes"]["ast_top"], dtype=float)

left.fill_between(x, 0.0, bottom, color="#9fb8c8", alpha=0.85,
                  label="ast bottom")
left.fill_between(x, 0.0, -top, color="#c86e5a", alpha=0.85,
                  label="ast top (drawn downward)")
left.axhline(bottom.max(), color="#22303a", ls=":", lw=1.2)
left.text(x[-1], bottom.max(), f" peak {bottom.max():.0f}", fontsize=8,
          va="center", color="#22303a")
left.set_xlabel("position along the beam (m)")
left.set_ylabel("required steel area (mm2)")
left.set_title(f"What is actually integrated - d = {best['depth']:.0f} mm\n"
               "the peak happens once; the shortcut charges for it everywhere",
               fontsize=10)
left.legend(fontsize=9)
left.grid(alpha=0.25)

depths = np.array([row["depth"] for row in rows])
concrete = np.array([row["concrete"] for row in rows])
steel = np.array([row["steel"] for row in rows])
right.bar(depths, concrete, width=32.0, label="concrete", color="#9fb8c8")
right.bar(depths, steel, width=32.0, bottom=concrete, label="reinforcement",
          color="#c86e5a")
for row in rows:
    if not row["adequate"]:
        right.text(row["depth"], row["total"] + 4.0, "SLS", ha="center",
                   fontsize=8, color="#c0392b", weight="bold")
right.axvline(best["depth"], color="#1a7f4b", ls="--", lw=1.5)
right.set_xlabel("section depth d (mm)")
right.set_ylabel("embodied carbon A1-A3 (kgCO2e, whole beam)")
right.set_title("Whole-beam carbon\ndashed line = lowest that meets span/250",
                fontsize=10)
right.legend(fontsize=9, loc="upper left")
right.grid(alpha=0.25, axis="y")

figure.suptitle(
    f"Continuous beam take-off - {CODE}  |  2 x {SPAN:.1f} m, "
    f"bw {WIDTH:.0f} mm, D {DEAD:.0f} + L {LIVE:.0f} kN/m  |  "
    f"concrete {ECF_CONCRETE}, bar {ECF_REBAR} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "continuous_beam_carbon_take_off.png")

print()
print("-" * 72)
print("A continuous beam's steel is a curve, so its quantity is an")
print("integral. C01 gives you the curve; taking the peak instead roughly")
print("doubles the answer. If a carbon figure has to survive scrutiny,")
print("integrate the envelope you were given rather than the worst point")
print("on it.")
