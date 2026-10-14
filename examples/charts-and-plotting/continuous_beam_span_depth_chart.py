# ---
# Example:  The span/depth chart every engineer wants - drawn from real deflections
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes - 2026-09-04 - the pinned two-span beam reproduces its steel/deflection/crack quadruple; every one of the 180 beams measured on prokon-automation.exe
# ---
# "Continuous beam? Span over twenty-six." Every code carries a span/depth
# rule like it, and every engineer uses it to pick a first depth. It is a
# deemed-to-satisfy shortcut, and the honest question about a shortcut is
# how far off it is.
#
# This script answers that by computing the real thing. It sweeps ten
# spans against eighteen depths - 180 three-span beams - reads the
# LONG-TERM deflection each one actually develops, and contours the
# span/deflection ratio. The 250 contour on that map is the true minimum
# depth for a span/250 limit, and the code's straight line is drawn on top
# of it for comparison.
#
# Then it draws the beam the chart picks: bending moment envelope, shear
# envelope, steel demand and the deflected shape, all to scale, all off
# the same result the chart was built from.
#
# ⚠ THE RULE OF THUMB AND THE COMPUTED ANSWER DO NOT AGREE, and on this
# floor the rule is THIN on every span measured - by 158 mm at 5 m and
# 362 mm at 14 m. That is not "the code is wrong": BS8110's basic ratio is
# meant to be multiplied by a tension-steel modification factor, and this
# comparison deliberately uses it the way it is used in practice for a
# first size, unmodified. The point is that the shortcut you sketch with
# is not on the safe side here, so it is worth measuring once on your own
# loading rather than inheriting it.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# -- SAVE THE PNG, AND SHOW IT IN SPYDER --------------------------------
# Spyder runs matplotlib on its own backend - "inline" puts the figure in
# the Plots pane, "automatic" opens a window - so plt.show() displays the
# chart right where you are working. A headless run (a batch job, or this
# documentation's own sweep) runs the Agg backend, where show() can only
# warn. So ASK the backend, and write the PNG either way.
#
# There is deliberately NO matplotlib.use("Agg") here. That call forces
# the headless backend, and a script that forces it can never draw into
# Spyder's Plots pane - which is where you actually want to see it.
HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can."""
    path = Path(filename).resolve()
    figure.savefig(path, dpi=150, facecolor="white")
    size = path.stat().st_size
    print("\nWritten: {0}".format(path))
    print("  {0:,} bytes  ({1})".format(
        size, "a real image" if size > 20_000 else "SUSPICIOUSLY SMALL"))
    if str(matplotlib.get_backend()).lower() in HEADLESS:
        plt.close(figure)
        print("  backend is headless - the PNG is the whole output")
    else:
        plt.show()          # Spyder: straight into the Plots pane
        print("  and shown on the {0} backend".format(
            matplotlib.get_backend()))


# -- The floor ----------------------------------------------------------
CODE = "BS8110 - 1997"
WEB = 300.0               # mm
FYV = 250.0
COVER_TOP = 35.0          # to bar centres [mm]
COVER_BOTTOM = 40.0
DEAD = 25.0               # kN/m, unfactored
LIVE = 15.0               # kN/m, unfactored
DEFLECTION_LIMIT = 250.0  # span / this
RULE_OF_THUMB = 26.0      # BS8110 table 3.9, continuous, basic

SPANS = np.arange(5.0, 14.1, 1.0)             # 10 m
DEPTHS = np.arange(350.0, 1201.0, 50.0)       # 18 mm

print("THE SPAN/DEPTH CHART, DRAWN FROM REAL DEFLECTIONS")
print(f"  {CODE}, three equal spans, {WEB:.0f} mm web")
print(f"  {DEAD:.0f} kN/m dead + {LIVE:.0f} kN/m live, unfactored")
print(f"  deflection limit span/{DEFLECTION_LIMIT:.0f}, "
      f"code rule of thumb span/{RULE_OF_THUMB:.0f}")
print(f"  grid: {len(SPANS)} spans x {len(DEPTHS)} depths "
      f"= {len(SPANS) * len(DEPTHS)} engine calls")

# -- The anchor ---------------------------------------------------------
# The C01 suite's own two-span beam, checked against the desktop calcsheet.
PINNED = (805.0209555473922, 1235.4393480298781, 12.446682698091044,
          0.11738993516717798)
envelope = prokon.v5.continuous_beam.analyse(
    design_code=CODE,
    sections=[{"n": 1, "bw": 300, "d": 500}],
    segments=[{"span": 1, "length": 6, "sec_left": 1},
              {"span": 2, "length": 6, "sec_left": 1}],
    supports=[{"n": 1}, {"n": 2}, {"n": 3}],
    loads=[{"case": "Dead", "span": 1, "w_left": 20},
           {"case": "Dead", "span": 2, "w_left": 20},
           {"case": "Live", "span": 1, "w_left": 10},
           {"case": "Live", "span": 2, "w_left": 10}],
    fyv=250.0, cover_top=30.0, cover_bot=40.0,
    live_permanent_percent=25.0, creep_coefficient=2.0,
    shrinkage_strain=300e-6)
anchor = envelope["result"]
measured = (anchor["spans"][0]["max_bottom_steel"],
            anchor["spans"][0]["max_top_steel"],
            anchor["max_deflection"], anchor["max_crack_width"])
print("\n  anchor: the pinned two-span 300 x 500 reference beam")
for name, value, pin in zip(("As bottom", "As top   ", "deflection",
                             "crack    "), measured, PINNED):
    print(f"    {name} {value!r:24} pinned {pin!r}")
print(f"    -> {'EXACT on all four' if measured == PINNED else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def beam(span, depth):
    """A three-span beam. Returns the whole result, or None if refused."""
    try:
        return prokon.v5.continuous_beam.analyse(
            design_code=CODE,
            sections=[{"n": 1, "bw": WEB, "d": depth}],
            segments=[{"span": number, "length": span, "sec_left": 1}
                      for number in (1, 2, 3)],
            supports=[{"n": number} for number in (1, 2, 3, 4)],
            loads=[{"case": "Dead", "span": number, "w_left": DEAD}
                   for number in (1, 2, 3)]
                  + [{"case": "Live", "span": number, "w_left": LIVE}
                     for number in (1, 2, 3)],
            fyv=FYV, cover_top=COVER_TOP, cover_bot=COVER_BOTTOM,
            live_permanent_percent=25.0, creep_coefficient=2.0,
            shrinkage_strain=300e-6)["result"]
    except prokon.v5.ProkonError:
        return None


# -- Sweep --------------------------------------------------------------
ratio = np.full((len(DEPTHS), len(SPANS)), np.nan)     # span / deflection
steel = np.full_like(ratio, np.nan)                    # kg per metre
crack = np.full_like(ratio, np.nan)

for column, span in enumerate(SPANS):
    for row, depth in enumerate(DEPTHS):
        result = beam(float(span), float(depth))
        if result is None:
            continue
        deflection = result["max_deflection"]
        if deflection <= 0:
            continue
        ratio[row, column] = span * 1000.0 / deflection
        crack[row, column] = result["max_crack_width"]
        # Longitudinal steel only, and only the worst per span - enough to
        # rank depths against each other, not a bar schedule.
        worst = max(max(one["max_bottom_steel"], one["max_top_steel"])
                    for one in result["spans"])
        steel[row, column] = worst * 1000.0 / 1e9 * 7850.0

answered = int(np.count_nonzero(~np.isnan(ratio)))
print(f"\nSWEPT   {answered} beams answered of "
      f"{len(SPANS) * len(DEPTHS)}")


def depth_needed(column):
    """Smallest depth on the grid meeting the deflection limit, or None."""
    for row, depth in enumerate(DEPTHS):
        value = ratio[row, column]
        if not np.isnan(value) and value >= DEFLECTION_LIMIT:
            return float(depth)
    return None


# -- The rule of thumb against the computed answer ----------------------
print("\nTHE RULE OF THUMB AGAINST THE COMPUTED DEPTH")
print(f"   {'span':>6} {'span/' + format(RULE_OF_THUMB, '.0f'):>10} "
      f"{'computed':>10} {'difference':>12}   verdict")
unconservative = 0
conservative = 0
for column, span in enumerate(SPANS):
    thumb = span * 1000.0 / RULE_OF_THUMB
    computed = depth_needed(column)
    if computed is None:
        print(f"   {span:>6.0f} {thumb:>10.0f} "
              f"{'over 1200':>10} {'-':>12}   no depth on the grid works")
        continue
    difference = computed - thumb
    if difference > 0:
        unconservative += 1
        verdict = "the rule is THIN"
    else:
        conservative += 1
        verdict = "the rule is generous"
    print(f"   {span:>6.0f} {thumb:>10.0f} {computed:>10.0f} "
          f"{difference:>+11.0f} mm   {verdict}")

print(f"   -> the rule reads thin on {unconservative} spans and generous on "
      f"{conservative}.")
if conservative == 0:
    print("      Thin on EVERY span here - so on this floor the shortcut is")
    print("      not on the safe side, and the error grows with the span.")
else:
    print("      It misses in BOTH directions, which is worse than being")
    print("      simply conservative: you cannot correct it with a margin.")
print("      This is not the code being wrong. BS8110's basic ratio is")
print("      meant to be multiplied by a tension-steel modification")
print("      factor, and this comparison uses it the way it is used in")
print(f"      practice for a first size - unmodified, for {DEAD:.0f} + "
      f"{LIVE:.0f} kN/m on a")
print(f"      {WEB:.0f} mm web it has never seen. Measure it once, on your "
      f"own floor.")

# -- What actually governs, depth by depth ------------------------------
# Deflection is the usual answer; it is not the only one. Crack width is
# checked alongside it so the chart cannot quietly hide a second limit.
CRACK_LIMIT = 0.3
crack_governs = int(np.count_nonzero(crack > CRACK_LIMIT))
print(f"\n   crack width over {CRACK_LIMIT} mm on "
      f"{crack_governs} of {answered} beams "
      f"(worst {np.nanmax(crack):.3f} mm)")

# -- The beam the chart picks -------------------------------------------
DESIGN_SPAN = 9.0
design_column = list(SPANS).index(DESIGN_SPAN)
design_depth = depth_needed(design_column)
design = beam(DESIGN_SPAN, design_depth)
print(f"\nTHE BEAM THE CHART PICKS   3 x {DESIGN_SPAN:.0f} m at "
      f"{WEB:.0f} x {design_depth:.0f} mm")
print(f"   max sagging {design['max_sagging_moment']:8.1f} kNm")
print(f"   max hogging {design['max_hogging_moment']:8.1f} kNm")
print(f"   max shear   {design['max_shear']:8.1f} kN")
print(f"   deflection  {design['max_deflection']:8.2f} mm "
      f"= span/{DESIGN_SPAN * 1000 / design['max_deflection']:.0f}")
print(f"   crack width {design['max_crack_width']:8.3f} mm")
for one in design["spans"]:
    print(f"   span {one['span_number']}: As bot "
          f"{one['max_bottom_steel']:6.0f}   As top "
          f"{one['max_top_steel']:6.0f} mm2   Asv/sv "
          f"{one['max_shear_steel']:.3f} mm2/mm")

# -- The figure ---------------------------------------------------------
figure = plt.figure(figsize=(15.5, 10), layout="constrained")
figure.patch.set_facecolor("white")
grid = figure.add_gridspec(3, 2, width_ratios=(1.15, 1))
mesh_s, mesh_d = np.meshgrid(SPANS, DEPTHS)

# 1. The chart.
chart = figure.add_subplot(grid[0:2, 0])
# The ratio spans more than an order of magnitude, so the FILL is on a
# log scale - but the ticks are labelled with the ratio itself, because
# "span/250" is what an engineer reads and "2.4" is not.
readable = [100, 150, 250, 400, 700, 1200]
shade = chart.contourf(mesh_s, mesh_d, np.log10(ratio), levels=24,
                       cmap="RdYlGn")
bar = figure.colorbar(shade, ax=chart, ticks=np.log10(readable))
bar.ax.set_yticklabels([f"span/{value}" for value in readable])
bar.set_label("long-term deflection, as span / deflection")

lines = chart.contour(mesh_s, mesh_d, ratio,
                      levels=[100, 150, 250, 400, 700, 1200],
                      colors="0.2", linewidths=0.9)
chart.clabel(lines, fmt="span/%.0f", fontsize=8)

limit = chart.contour(mesh_s, mesh_d, ratio, levels=[DEFLECTION_LIMIT],
                      colors="black", linewidths=2.8)
chart.clabel(limit, fmt={DEFLECTION_LIMIT:
                         f"span/{DEFLECTION_LIMIT:.0f} - the real limit"},
             fontsize=9)

chart.plot(SPANS, SPANS * 1000.0 / RULE_OF_THUMB, color="blue",
           linewidth=2.4, linestyle="--",
           label=f"code rule of thumb, span/{RULE_OF_THUMB:.0f}")
picked = [(SPANS[c], depth_needed(c)) for c in range(len(SPANS))
          if depth_needed(c) is not None]
chart.step([s for s, _ in picked], [d for _, d in picked], where="mid",
           color="black", linewidth=2.0,
           label="smallest depth on the grid that passes")
chart.plot(DESIGN_SPAN, design_depth, marker="*", markersize=20,
           color="white", markeredgecolor="black", zorder=6)
chart.set_xlabel("span (m), three equal spans")
chart.set_ylabel("overall depth (mm)")
chart.set_title("Deflection over the whole (span, depth) plane\n"
                "the blue dashes are the code shortcut; the black line is "
                "what the engine computes", fontsize=10)
chart.legend(loc="upper left", fontsize=8)

# 2. Steel content, as the price of the choice.
weight = figure.add_subplot(grid[2, 0])
for column, span in enumerate(SPANS):
    if span % 3 != 0:
        continue
    line = steel[:, column]
    mask = ~np.isnan(line)
    weight.plot(DEPTHS[mask], line[mask], linewidth=1.6,
                label=f"{span:.0f} m")
    needed = depth_needed(column)
    if needed is not None:
        row = list(DEPTHS).index(needed)
        weight.plot(needed, line[row], marker="o", markersize=7,
                    color="black", zorder=5)
weight.set_xlabel("overall depth (mm)")
weight.set_ylabel("worst steel (kg/m)")
weight.set_title("Steel falls as depth rises - the dots are the depth the\n"
                 "deflection limit forces", fontsize=10)
weight.legend(title="span", fontsize=8, title_fontsize=8, ncol=3)
weight.grid(True, linewidth=0.3, color="0.85")

# 3-5. The chosen beam, drawn the way a calcsheet draws it.
env = design["envelopes"]
x = np.array(env["position"])
support_x = [x[design["spans"][0]["first_position"] - 1]] + [
    x[one["last_position"] - 1] for one in design["spans"]]

moment = figure.add_subplot(grid[0, 1])
moment.fill_between(x, env["moment_negative"], env["moment_positive"],
                    color="#4c78a8", alpha=0.35)
moment.plot(x, env["moment_positive"], color="#1f4e79", linewidth=1.2)
moment.plot(x, env["moment_negative"], color="#1f4e79", linewidth=1.2)
moment.plot(x, env["moment_capacity_bottom"], color="#b03030",
            linewidth=1.0, linestyle="--", label="capacity provided")
moment.plot(x, env["moment_capacity_top"], color="#b03030", linewidth=1.0,
            linestyle="--")
moment.axhline(0, color="black", linewidth=0.8)
for position in support_x:
    moment.axvline(position, color="0.6", linewidth=0.8, linestyle=":")
moment.invert_yaxis()          # sagging drawn downwards, as engineers do
moment.set_ylabel("moment (kNm)")
moment.set_title(f"The beam the chart picks: 3 x {DESIGN_SPAN:.0f} m, "
                 f"{WEB:.0f} x {design_depth:.0f} mm", fontsize=10)
moment.legend(fontsize=8)
moment.grid(True, linewidth=0.3, color="0.9")

shear = figure.add_subplot(grid[1, 1], sharex=moment)
shear.fill_between(x, env["shear_negative"], env["shear_positive"],
                   color="#59a14f", alpha=0.35)
shear.plot(x, env["shear_positive"], color="#2d6a26", linewidth=1.2)
shear.plot(x, env["shear_negative"], color="#2d6a26", linewidth=1.2)
shear.axhline(0, color="black", linewidth=0.8)
for position in support_x:
    shear.axvline(position, color="0.6", linewidth=0.8, linestyle=":")
shear.set_ylabel("shear (kN)")
shear.grid(True, linewidth=0.3, color="0.9")

shape = figure.add_subplot(grid[2, 1], sharex=moment)
shape.plot(x, env["deflection_total"], color="#8b3ea8", linewidth=1.8,
           label="long-term total")
shape.plot(x, env["deflection_long_term"], color="#8b3ea8", linewidth=0.9,
           linestyle="--", label="long-term, no shrinkage")
shape.axhline(DESIGN_SPAN * 1000.0 / DEFLECTION_LIMIT, color="red",
              linestyle="--", linewidth=1.2,
              label=f"span/{DEFLECTION_LIMIT:.0f}")
shape.axhline(0, color="black", linewidth=0.8)
for position in support_x:
    shape.axvline(position, color="0.6", linewidth=0.8, linestyle=":")
shape.invert_yaxis()           # downward deflection drawn downwards
shape.set_xlabel("position along the beam (m)")
shape.set_ylabel("deflection (mm)")
shape.legend(fontsize=8)
shape.grid(True, linewidth=0.3, color="0.9")

figure.suptitle(
    f"Continuous beam span/depth chart - {CODE}\n"
    f"three equal spans, {WEB:.0f} mm web, {DEAD:.0f} kN/m dead + "
    f"{LIVE:.0f} kN/m live, creep 2.0, shrinkage 300 microstrain, "
    f"25 % of live permanent  |  engine {envelope['module_version']}",
    fontsize=10)
deliver(figure, "continuous_beam_span_depth_chart.png")
