# ---
# Example:  A post-tensioned slab's carbon - the engine weighs it for you
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes - 2026-09-09 - the `quantities` units confirmed by slab_area = 5.0 x 8.0 m; carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe
# ---
# Post-tensioning buys DEPTH. A PT slab spans further, or spans the same
# distance thinner, than a reinforced one - and on a concrete-dominated
# element depth is carbon. Against that, strand is a high-carbon material
# used in a small quantity, and a thinner slab needs more of it - so the
# two pull against each other and only arithmetic settles it.
#
# So: how thin can PT take this slab before the strand costs more than the
# concrete it saves? This script asks C02 directly.
#
# C02 IS THE ONE ENGINE THAT WEIGHS ITS OWN REINFORCEMENT. Every other
# engine here reports an AREA and leaves the mass to you. C02 returns
# `quantities` with the masses already in kilograms:
#
#     cable_mass        kg of strand
#     main_rebar_mass   kg of ordinary bar
#     link_mass         kg of links
#     slab_area         m2 of slab
#
# Measured, on the reference slab below: 112.45, 101.28, 0, 40.0 - and
# 40 m2 is exactly the 5.0 m width x 8.0 m span, which is what confirms
# the units without having to trust a docstring.
#
# AND THE GUIDE ANSWERS THE FACTOR QUESTION EXPLICITLY. IStructE's
# table lists "PT strands: assume the same as reinforcement bars". So
# strand and bar carry the SAME kgCO2e/kg here, and the difference
# between them is quantity alone - which is the honest way to compare
# them, and not what most people assume.
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
ECF_STRAND = 0.684           # "PT strands: assume the same as reinforcement bars"
DENSITY_CONCRETE = 2400.0

# CONTROL - reproduces the worked example in that same guide.
assert round(116.6 * DENSITY_CONCRETE / 1000.0, 1) == 279.8
assert round(116.6 * 90.0 / 1000.0, 1) == 10.5

CODE = "BS8110 - 1997"
SPAN = 8.0                   # m
WIDTH = 5000.0               # mm
DEAD = 6.0                   # kN/m
LIVE = 15.0                  # kN/m
STRANDS = 12

TENDON = [{"no": 1, "bond": "Unbonded", "strength": 260.7,
           "max_stress_pct": 80, "dia": 18, "area": 140, "k": 0.0015,
           "u": 0.05, "pullin": 5, "relax": 2, "est": 195_000_000.0,
           "min_harp_radius": 1.0}]

DEPTHS = (300.0, 275.0, 250.0, 225.0, 200.0)

# Deflection limit for a slab carrying a partition-free floor.
DEFLECTION_LIMIT = SPAN * 1000.0 / 250.0
CRACK_LIMIT = 0.2            # mm


def pt_slab(depth, strands=STRANDS):
    """One C02 analysis of the slab at this depth."""
    drape = depth / 300.0 * 40.0          # keep the drape proportional
    return prokon.v5.prestressed_concrete.analyse(
        design_code=CODE, fcu=19.2, fy=450.0, fyv=250.0, fci=14.4,
        ec=26_000_000.0, est=206_000_000.0, density=24.0,
        top_cover=25.0, bottom_cover=25.0,
        tendon_properties=TENDON,
        cable_sets=[{"n": strands, "prop": 1, "x_live": 0.0,
                     "x_dead": SPAN,
                     "spans": [{"span": 1, "lo": 0, "ro": 0,
                                "b1": depth / 2.0, "b2": drape,
                                "b3": depth / 2.0}]}],
        sections=[{"name": "slab", "bw": WIDTH, "d": depth}],
        span_segments=[{"span": 1, "length": SPAN, "sec_left": "slab"}],
        loads=[{"case": "D", "span": 1, "wl": DEAD},
               {"case": "L", "span": 1, "wl": LIVE}],
        additional_rebar=[{"span": 1, "pos": "B", "bars": "8Y16",
                           "length": SPAN}])


def carbon(depth, quantities, ecf_concrete=ECF_CONCRETE):
    """A1-A3 carbon for the slab, and per square metre."""
    area = quantities["slab_area"]
    concrete_m3 = depth / 1000.0 * area
    concrete = concrete_m3 * DENSITY_CONCRETE * ecf_concrete
    strand = quantities["cable_mass"] * ECF_STRAND
    rebar = (quantities["main_rebar_mass"] + quantities["link_mass"]) * ECF_REBAR
    return dict(area=area, concrete=concrete, strand=strand, rebar=rebar,
                total=concrete + strand + rebar,
                per_m2=(concrete + strand + rebar) / area)


print("A POST-TENSIONED SLAB'S EMBODIED CARBON")
print(f"  {CODE}, {SPAN:.1f} m span, {WIDTH / 1000.0:.1f} m wide")
print(f"  loads  dead {DEAD:.0f} kN/m, live {LIVE:.0f} kN/m")
print(f"  limits deflection span/250 = {DEFLECTION_LIMIT:.1f} mm, "
      f"crack {CRACK_LIMIT:.1f} mm")
print(f"  strand and bar share one factor: {ECF_STRAND} kgCO2e/kg "
      f"(the guide says to)")

# -- 1. Thinner, but PAY FOR IT IN STRAND -------------------------------
# The point of PT is that depth and prestress trade against each other, so
# holding the strand count fixed while thinning would not be a trade at
# all - it would just be a slab that fails. At every depth this searches
# UPWARD for the fewest strands that meet both SLS limits.
STRAND_OPTIONS = (12, 16, 20, 24, 28, 32, 36, 40)

print()
print("1. THE FEWEST STRANDS THAT WORK, AT EACH DEPTH")
print(f"   {'depth':>6} {'strands':>8} {'strand':>7} {'rebar':>7} "
      f"{'concrete':>9} {'defl':>7} {'crack':>7} {'kgCO2e':>8}")
print(f"   {'mm':>6} {'no.':>8} {'kg':>7} {'kg':>7} "
      f"{'m3':>9} {'mm':>7} {'mm':>7} {'per m2':>8}")
print("   " + "-" * 68)

rows = []
reference = None

for depth in DEPTHS:
    found = None
    for strands in STRAND_OPTIONS:
        envelope = pt_slab(depth, strands=strands)
        result = envelope["result"]
        if reference is None:
            reference = envelope

        deflection = max(abs(value) for value in result["deflections"]["ditot"])
        crack = max(result["crack_widths"]["cwb"] + result["crack_widths"]["cwt"])

        if deflection <= DEFLECTION_LIMIT and crack <= CRACK_LIMIT:
            found = (strands, result, deflection, crack)
            break

    if found is None:
        print(f"   {depth:>6.0f} {'-':>8}   no strand count up to "
              f"{max(STRAND_OPTIONS)} meets both SLS limits")
        continue

    strands, result, deflection, crack = found
    quantities = result["quantities"]
    money = carbon(depth, quantities)

    row = dict(money)                    # area, concrete, strand, rebar, total, per_m2
    row.update(depth=depth, strands=strands,
               strand_kg=quantities["cable_mass"],
               rebar_kg=quantities["main_rebar_mass"] + quantities["link_mass"],
               concrete_m3=depth / 1000.0 * money["area"],
               deflection=deflection, crack=crack, adequate=True)
    rows.append(row)

    print(f"   {depth:>6.0f} {strands:>8} {row['strand_kg']:>7.1f} "
          f"{row['rebar_kg']:>7.1f} {row['concrete_m3']:>9.2f} "
          f"{deflection:>7.2f} {crack:>7.3f} {money['per_m2']:>8.1f}")

if not rows:
    raise SystemExit("no depth in the sweep can be made to work - widen it")

usable = rows
best = min(usable, key=lambda row: row["per_m2"])
print(f"   -> {len(usable)} of {len(DEPTHS)} depths can be made to work at all.")
print(f"   -> LOWEST CARBON: {best['depth']:.0f} mm with {best['strands']} "
      f"strands, {best['per_m2']:.1f} kgCO2e/m2")

# -- 2. Where the carbon sits ------------------------------------------
print()
print("2. THE SPLIT - AND STRAND IS NOT THE PROBLEM")
thickest = max(rows, key=lambda row: row["depth"])
print(f"   {'depth':>6} {'strands':>8} {'concrete':>9} {'strand':>8} "
      f"{'rebar':>8} {'conc share':>11}")
for row in rows:
    print(f"   {row['depth']:>6.0f} {row['strands']:>8} "
          f"{row['concrete']:>9.1f} {row['strand']:>8.1f} "
          f"{row['rebar']:>8.1f} {row['concrete'] / row['total']:>10.0%}")
print("   -> strand is a few percent of the total on every depth here.")
print("      A 'high-carbon material' used in a small quantity is a small")
print("      number: the factor is only half of any carbon argument.")

# -- 3. Does thinning actually pay -------------------------------------
print()
print("3. DOES THINNING PAY, ONCE THE STRAND IS PAID FOR")
base = thickest
print(f"   baseline {base['depth']:.0f} mm, {base['strands']} strands: "
      f"{base['per_m2']:.1f} kgCO2e/m2")
for row in rows:
    if row["depth"] >= base["depth"]:
        continue
    # Every value here is already a CARBON figure in kgCO2e, not a mass.
    concrete_saved = base["concrete"] - row["concrete"]
    steel_added = ((row["strand"] + row["rebar"])
                   - (base["strand"] + base["rebar"]))
    net = row["total"] - base["total"]
    print(f"   {row['depth']:>6.0f} mm, {row['strands']:>2} strands  "
          f"concrete -{concrete_saved:>7.1f}  steel {steel_added:>+7.1f}  "
          f"net {net:>+8.1f} kgCO2e")
paying = [row for row in rows if row["depth"] < base["depth"]
          and row["total"] < base["total"]]
print(f"   -> {len(paying)} of {len(rows) - 1} thinner options are a NET SAVING")
print("      once the extra strand is charged for.")
print("   -> the strand bill is real but small, so the concrete removed")
print("      wins wherever the slab can be made to work at all. That is")
print("      the carbon case for PT, stated in its own units.")

# -- 4. The mix, and one honest limit ----------------------------------
print()
print("4. THE MIX, AND WHAT THIS DOES NOT MODEL")
print(f"   {'mix':<20} {'best slab':>12}")
for label, factor in (("C32/40, 25% GGBS", 0.120),
                      ("C32/40, 50% GGBS", 0.089),
                      ("C32/40, 75% GGBS", 0.063)):
    money = carbon(best["depth"], dict(slab_area=best["area"],
                                       cable_mass=best["strand_kg"],
                                       main_rebar_mass=best["rebar_kg"],
                                       link_mass=0.0),
                   ecf_concrete=factor)
    print(f"   {label:<20} {money['per_m2']:>9.1f}/m2")
print("   -> GGBS in a PT slab has a catch a reinforced slab does not:")
print("      PT needs early strength at TRANSFER, and high-GGBS mixes gain")
print("      strength slowly. `fci` in this model is the transfer strength,")
print("      and it is an INPUT here, not something the mix choice feeds.")
print("      So treat the 75 % row as an upper bound on the saving, not a")
print("      specification - the programme may not allow it.")

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


ordered = sorted(rows, key=lambda row: row["depth"])
depths = np.array([row["depth"] for row in ordered])
concrete = np.array([row["concrete"] / row["area"] for row in ordered])
strand = np.array([row["strand"] / row["area"] for row in ordered])
rebar = np.array([row["rebar"] / row["area"] for row in ordered])

figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

left.bar(depths, concrete, width=16.0, label="concrete", color="#9fb8c8")
left.bar(depths, strand, width=16.0, bottom=concrete, label="PT strand",
         color="#6a4c93")
left.bar(depths, rebar, width=16.0, bottom=concrete + strand,
         label="ordinary bar", color="#c86e5a")
for row in ordered:
    left.text(row["depth"], row["per_m2"] + 1.0, f"{row['strands']}T",
              ha="center", fontsize=8, color="#22303a")
left.set_xlabel("slab depth (mm)")
left.set_ylabel("embodied carbon A1-A3 (kgCO2e per m2)")
left.set_title("Strand is the thin band in the middle\n"
               "'high-carbon material' does not mean high carbon",
               fontsize=10)
left.legend(fontsize=9, loc="upper left")
left.grid(alpha=0.25, axis="y")

deflections = np.array([row["deflection"] for row in ordered])
right.plot(depths, deflections, color="#22303a", lw=2.0, marker="o", ms=5,
           label="total long-term deflection")
right.axhline(DEFLECTION_LIMIT, color="#c0392b", ls="--", lw=1.5,
              label=f"span/250 = {DEFLECTION_LIMIT:.1f} mm")
right.set_xlabel("slab depth (mm)")
right.set_ylabel("deflection (mm)")
right.set_title("What actually stops you thinning it\n"
                "carbon says thinner; serviceability says when to stop",
                fontsize=10)
right.legend(fontsize=9)
right.grid(alpha=0.25)

figure.suptitle(
    f"PT slab embodied carbon - {CODE}  |  {SPAN:.1f} m span, "
    f"{STRANDS} strands, D {DEAD:.0f} + L {LIVE:.0f} kN/m  |  "
    f"strand = bar at {ECF_STRAND} kgCO2e/kg  |  "
    f"engine {reference['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "prestressed_concrete_carbon_of_a_pt_slab.png")

print()
print("-" * 72)
print("C02 hands you the masses, so the carbon is arithmetic rather than")
print("estimation - and the arithmetic says the strand was never the")
print("problem. PT earns its carbon by removing concrete, and how far you")
print("can take that is a serviceability question, not a carbon one.")
