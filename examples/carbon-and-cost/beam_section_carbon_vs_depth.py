# ---
# Example:  The lowest-carbon beam - and why the depth is not the lever
# Feature:  beam_section (C22 Beam Section)
# Verified: yes - 2026-09-09 - the pinned 300 x 500 reference reproduces mu = 295.18197048179997; carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# A deeper beam needs less steel and more concrete. A shallower beam needs
# more steel and less concrete. Somewhere between them is the section with
# the least embodied carbon - and this script sweeps C22 to find it.
#
# The answer is worth having. What the sweep shows on the way there is
# worth more, and it is not what the question implies.
#
# WHAT THIS SCRIPT COUNTS. Embodied carbon, A1-A3 (the product stage:
# extraction, transport to plant, manufacture), for ONE METRE of beam:
#
#   concrete   bw x h x 1 m, at 2400 kg/m3
#   tension steel   the engine's required `ast`, over 1 m
#   link steel      the engine's governing Asv/Sv, over 1 m
#
# It does NOT count formwork, transport to site (A4), construction (A5),
# laps, curtailment, or anything past the product stage. Those are real
# and they are somebody's else's number; this is the part the ENGINE's
# output can support, and saying so is the honest scope.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# -- EMBODIED CARBON FACTORS -------------------------------------------
# A1-A3 embodied carbon factors, kgCO2e per kg, from the table of example
# UK factors in IStructE, "A brief guide to calculating embodied carbon",
# The Structural Engineer, July 2020:
#
#   concrete, in situ, unreinforced   C30/37 UK avg ready-mix   0.103
#                                     C32/40  25% GGBS          0.120
#                                     C32/40  50% GGBS          0.089
#                                     C32/40  75% GGBS          0.063
#                                     C40/50  25% GGBS          0.138
#                                     C40/50  50% GGBS          0.102
#                                     C40/50  75% GGBS          0.072
#   reinforcement bar                 UK, BRC EPD               0.684
#                                     world average             1.99
#
# Change these two numbers and the whole answer moves. That is the point
# of section 4 below.
ECF_CONCRETE = 0.120            # kgCO2e/kg - C32/40, 25% GGBS
ECF_REBAR = 0.684               # kgCO2e/kg - UK bar, BRC EPD
DENSITY_CONCRETE = 2400.0       # kg/m3
DENSITY_STEEL = 7850.0          # kg/m3

# CONTROL - this arithmetic reproduces the worked example printed in that
# same guide: 116.6 m3 of concrete is 279.8 t, and 90 kg/m3 of bar over
# that volume is 10.5 t. If either line ever fails, a density moved.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "BS8110 - 1997"
MOMENT = 200.0                  # kNm
SHEAR = 100.0                   # kN
WIDTH = 300.0                   # mm
COVER = 40.0                    # mm
FCU = 30.0
FY = 450.0

DEPTHS = np.arange(400.0, 1101.0, 50.0)


def section(depth):
    """One C22 analysis at this depth."""
    return prokon.v5.beam_section.analyse(
        design_code=CODE, m=MOMENT, v=SHEAR, bw=WIDTH, h=depth,
        dc_t=COVER, dc_b=COVER, dc_s=COVER,
        fcu=FCU, fy=FY, fyv=FY)


def link_perimeter(depth):
    """One closed link's centre-line length, mm."""
    return 2.0 * (WIDTH - 2.0 * COVER) + 2.0 * (depth - 2.0 * COVER)


def steel_kg_per_m(result, depth):
    """Tension bar + link steel, kg per metre of beam.

    Two units the engine does NOT spell out, and both were measured:

      `ast`  is an AREA in mm2.
      `asv`  is Asv/Sv - link leg area per mm along the beam, mm2/mm.
             `reinforcement.shear_links[0]` confirms it: "2Y8@300" is
             reported as 0.3351, and 2 x 50.265 / 300 = 0.3351.

    A closed 2-leg link has HALF that area in its single perimeter, so the
    link volume per metre is asv/2 x 1000 x perimeter. Hand check, 2Y8@300
    on a 300 x 500 with 40 cover: 3.33 links/m x 1280 mm x 50.27 mm2 =
    214 400 mm3, and 0.3351/2 x 1000 x 1280 = 214 464 mm3.
    """
    tension_mm3 = result["ast"] * 1000.0
    links_mm3 = max(result["asv"], result["asvn"]) / 2.0 * 1000.0 * link_perimeter(depth)
    return (tension_mm3 + links_mm3) * DENSITY_STEEL / 1.0e9


def carbon_kg_per_m(concrete_m3, steel_kg):
    """A1-A3 embodied carbon, kgCO2e per metre of beam."""
    return (concrete_m3 * DENSITY_CONCRETE * ECF_CONCRETE
            + steel_kg * ECF_REBAR)



# -- PINNED CONTROL ----------------------------------------------------
# Before sweeping anything, check the engine is the one this example was
# written against. The 300 x 500 reference section under M = 200 kNm is
# the fleet's pinned value: mu = 295.18197048179997 kNm. If this assert
# ever fires, the engine changed and every number below is suspect.
_pinned = prokon.v5.beam_section.analyse(
    design_code=CODE, m=MOMENT, v=SHEAR, bw=WIDTH, h=500.0,
    dc_t=COVER, dc_b=COVER, dc_s=COVER, fcu=FCU, fy=FY, fyv=FY)
assert _pinned["result"]["mu"] == 295.18197048179997, _pinned["result"]["mu"]

print("THE LOWEST-CARBON BEAM")
print(f"  pinned control: the 300 x 500 reference reproduces "
      f"mu = {_pinned['result']['mu']} kNm")
print(f"  M = {MOMENT:.0f} kNm, V = {SHEAR:.0f} kN, bw = {WIDTH:.0f} mm, "
      f"{CODE}")
print(f"  fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm")
print(f"  carbon factors: concrete {ECF_CONCRETE} kgCO2e/kg, "
      f"bar {ECF_REBAR} kgCO2e/kg")

# -- 1. The sweep -------------------------------------------------------
print()
print("1. ONE METRE OF BEAM, AT EVERY DEPTH")
print(f"   {'h':>6} {'ast':>8} {'links':>8} {'conc':>8} {'steel':>7} "
      f"{'kgCO2e':>8} {'of which':>9}")
print(f"   {'mm':>6} {'mm2':>8} {'mm2/mm':>8} {'m3/m':>8} {'kg/m':>7} "
      f"{'per m':>8} {'concrete':>9}")
print("   " + "-" * 62)

rows = []
reference = None

for depth in DEPTHS:
    envelope = section(depth)
    result = envelope["result"]

    if reference is None:
        reference = envelope

    # An inadequate section is still a SUCCESS on this engine - it designs
    # whatever it is asked. So the adequacy test is ours to make.
    #
    # NOTE THE KEY. It is the single string "shear.ok", with a dot IN THE
    # NAME - not a nested dict. result["shear"]["ok"] raises KeyError.
    # "torsion.solved" and "torsion.vrd_max" are spelled the same way.
    adequate = result["mu"] >= MOMENT and result["shear.ok"]

    concrete_m3 = WIDTH * depth / 1.0e6
    steel_kg = steel_kg_per_m(result, depth)
    total = carbon_kg_per_m(concrete_m3, steel_kg)
    concrete_share = concrete_m3 * DENSITY_CONCRETE * ECF_CONCRETE / total

    rows.append(dict(h=depth, ast=result["ast"], asv=max(result["asv"], result["asvn"]),
                     concrete=concrete_m3, steel=steel_kg, carbon=total,
                     share=concrete_share, adequate=adequate))

    print(f"   {depth:>6.0f} {result['ast']:>8.0f} {max(result['asv'], result['asvn']):>8.4f} "
          f"{concrete_m3:>8.4f} {steel_kg:>7.1f} {total:>8.1f} "
          f"{concrete_share:>8.0%}" + ("" if adequate else "   INADEQUATE"))

usable = [row for row in rows if row["adequate"]]
best = min(usable, key=lambda row: row["carbon"])
worst = max(usable, key=lambda row: row["carbon"])

print(f"   -> {len(usable)} of {len(rows)} depths carry the moment.")
print(f"   -> LOWEST CARBON at h = {best['h']:.0f} mm: "
      f"{best['carbon']:.1f} kgCO2e per metre.")
print(f"      The worst adequate depth, h = {worst['h']:.0f}, costs "
      f"{worst['carbon']:.1f} - a factor of "
      f"{worst['carbon'] / best['carbon']:.2f}.")

# -- 2. There is no interior minimum, and that is the finding ----------
print()
print("2. THERE IS NO VALLEY. CARBON FALLS ALL THE WAY TO THE BOUNDARY")
shallowest = min(usable, key=lambda row: row["h"])
monotonic = all(later["carbon"] > earlier["carbon"] for earlier, later
                in zip(sorted(usable, key=lambda row: row["h"]),
                       sorted(usable, key=lambda row: row["h"])[1:]))
print(f"   carbon rises with depth at every step: {monotonic}")
print(f"   best depth {best['h']:.0f} mm IS the shallowest adequate one "
      f"({shallowest['h']:.0f} mm): {best['h'] == shallowest['h']}")
print(f"   at the best depth   concrete is {best['share']:.0%} of the carbon")
print(f"   at the worst depth  concrete is {worst['share']:.0%}")
print("   -> the steel saved by going deeper NEVER pays for the concrete")
print("      it costs. So the curve has no floor to sit in: it just falls")
print("      until the section stops working. The optimiser's answer is")
print("      always 'the shallowest thing that passes'.")
print("   -> which is the opposite of the instinct that a deeper beam is")
print("      the efficient one. Deeper is efficient in STEEL. Steel is")
print("      not where the carbon is.")

# -- 3. So the constraint, not the optimum, is the answer ---------------
print()
print("3. THE THING THAT ACTUALLY PICKS THE DEPTH IS A LIMIT STATE")
within = [row for row in usable if row["carbon"] <= 1.05 * best["carbon"]]
band = ", ".join("{0:.0f}".format(row["h"]) for row in within)
print(f"   depths within 5 % of the best: {len(within)}  ({band} mm)")
print("   -> a band of one. There is no flat floor to exploit, so nothing")
print("      here lets you trade depth for free.")
print(f"   -> and note WHERE the minimum sits: {best['h']:.0f} mm is one")
print(f"      grid step above the depth that fails ({DEPTHS[0]:.0f} mm).")
print("      A carbon optimum that lands hard against a capacity boundary")
print("      has no margin left for the checks THIS ENGINE DOES NOT DO -")
print("      deflection and vibration above all. C22 sizes a section; it")
print("      does not tell you the 450 will pass a span/depth check.")
print("   -> so read this sweep as 'carbon pushes shallow, serviceability")
print("      pushes deep, and the answer is where they meet' - not as a")
print("      recommendation to build the 450.")

# -- 4. The lever that needs no change to the geometry ------------------
# The specification changes the factor, and the factor multiplies
# everything. This is the IStructE hierarchy's "specify low impact" step.
print()
print("4. THE LEVER THAT COSTS NO DEPTH AT ALL: THE MIX")
MIXES = (("C32/40, 25% GGBS", 0.120),
         ("C32/40, 50% GGBS", 0.089),
         ("C32/40, 75% GGBS", 0.063))
print(f"   {'mix':<20} {'kgCO2e/kg':>10} {'best beam':>10} {'saving':>8}")
baseline = None
for label, factor in MIXES:
    carbon = (best["concrete"] * DENSITY_CONCRETE * factor
              + best["steel"] * ECF_REBAR)
    baseline = carbon if baseline is None else baseline
    print(f"   {label:<20} {factor:>10.3f} {carbon:>10.1f} "
          f"{1.0 - carbon / baseline:>7.0%}")

mix_saving = 1.0 - (best["concrete"] * DENSITY_CONCRETE * 0.063
                    + best["steel"] * ECF_REBAR) / best["carbon"]
print(f"   -> {mix_saving:.0%} off, on ANY depth, with no change to the")
print("      section, the bars, the formwork or the drawing geometry.")

# The useful way to compare two levers in different units: convert one
# into the other. How much DEPTH does the better mix buy, at equal carbon?
on_low_carbon_mix = [(row["h"], row["concrete"] * DENSITY_CONCRETE * 0.063
                      + row["steel"] * ECF_REBAR) for row in usable]
affordable = [h for h, carbon in on_low_carbon_mix if carbon <= best["carbon"]]

print("   -> and the comparison that matters, since depth is NOT free.")
print(f"      The 450 mm beam on 25% GGBS costs {best['carbon']:.1f} kgCO2e/m.")
print(f"      On 75% GGBS, the SAME budget buys any depth up to "
      f"{max(affordable):.0f} mm.")
print("      So the mix does not merely shave a percentage - it buys back")
print(f"      {max(affordable) - best['h']:.0f} mm of depth for nothing,")
print("      which is depth you can spend on deflection, on services, or")
print("      on a shallower reinforcement layout. Two levers in different")
print("      units are only comparable once you price one in the other.")

# -- 5. And where the bar comes from ------------------------------------
print()
print("5. AND THE BAR'S ORIGIN IS NOT A ROUNDING ERROR")
for label, factor in (("UK bar (BRC EPD)", 0.684),
                      ("world average", 1.99)):
    carbon = (best["concrete"] * DENSITY_CONCRETE * ECF_CONCRETE
              + best["steel"] * factor)
    print(f"   {label:<20} {factor:>5.3f} kgCO2e/kg -> {carbon:>7.1f} kgCO2e/m")
print("   -> same beam, same drawing, same engine result. The guide notes")
print("      a UAE bar with no recycled content could be nearer 2.1, so")
print("      the SUPPLY CHAIN can outweigh the design. Worth knowing before")
print("      spending a week optimising the section.")

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
concrete_carbon = np.array([row["concrete"] * DENSITY_CONCRETE * ECF_CONCRETE
                            for row in usable])
steel_carbon = np.array([row["steel"] * ECF_REBAR for row in usable])

figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

left.stackplot(heights, concrete_carbon, steel_carbon,
               labels=["concrete", "reinforcement"],
               colors=["#9fb8c8", "#c86e5a"], alpha=0.95)
left.plot(heights, concrete_carbon + steel_carbon, color="#22303a", lw=1.6)
left.axvline(best["h"], color="#1a7f4b", ls="--", lw=1.5)
left.annotate("lowest carbon is the SHALLOWEST\nthat passes - "
              f"{best['h']:.0f} mm, {best['carbon']:.0f} kgCO2e/m",
              xy=(best["h"], best["carbon"]),
              xytext=(best["h"] + 90, best["carbon"] * 1.35),
              arrowprops=dict(arrowstyle="->", color="#1a7f4b"),
              fontsize=9, color="#1a7f4b")
left.axvspan(DEPTHS[0] - 25.0, best["h"] - 25.0, color="#c0392b", alpha=0.12)
left.text(DEPTHS[0] - 15.0, max(concrete_carbon + steel_carbon) * 0.92,
          "fails", fontsize=8, color="#c0392b")
left.set_xlabel("overall depth h (mm)")
left.set_ylabel("embodied carbon A1-A3 (kgCO2e per metre)")
left.set_title("Where the carbon goes - and it only ever falls\n"
               "no interior minimum: the boundary is the answer",
               fontsize=10)
left.legend(loc="upper left", fontsize=9)
left.grid(alpha=0.25)

for label, factor, colour in (("25% GGBS", 0.120, "#c86e5a"),
                              ("50% GGBS", 0.089, "#e0a458"),
                              ("75% GGBS", 0.063, "#1a7f4b")):
    curve = np.array([row["concrete"] * DENSITY_CONCRETE * factor
                      + row["steel"] * ECF_REBAR for row in usable])
    right.plot(heights, curve, lw=1.8, color=colour,
               label=f"C32/40, {label}  ({factor:.3f})")

right.set_xlabel("overall depth h (mm)")
right.set_ylabel("embodied carbon A1-A3 (kgCO2e per metre)")
right.set_title("The mix moves the whole curve\nthe depth only slides along one",
                fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"Beam embodied carbon - {CODE}  |  M = {MOMENT:.0f} kNm, "
    f"V = {SHEAR:.0f} kN, bw = {WIDTH:.0f} mm  |  "
    f"bar {ECF_REBAR} kgCO2e/kg  |  engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "beam_section_carbon_vs_depth.png")

print()
print("-" * 72)
print("The sweep answers the question it was asked, and the answer is a")
print("boundary rather than an optimum: carbon falls until the section")
print("stops working. So the number to take away is not the 450 - it is")
print("that the mix specification buys back the entire depth range, and")
print("that the bar's origin can outweigh the design altogether. Sweep the")
print("geometry if you like. Negotiate the specification either way.")
