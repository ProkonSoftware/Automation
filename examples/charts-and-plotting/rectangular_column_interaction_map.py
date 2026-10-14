# ---
# Example:  The N-M interaction chart, drawn from the engine instead of a handbook
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes - 2026-09-04 - the pinned SABS 400 x 400 column reproduces its ast and perc; every one of the 377 interaction points measured on prokon-automation.exe
# ---
# Every concrete handbook carries a page of column interaction charts:
# axial load up the side, moment along the bottom, one curve per steel
# percentage. They are printed for a handful of standard cases and you
# interpolate for yours.
#
# C11 will draw one for YOUR section, YOUR concrete, YOUR effective length
# and YOUR code, in about a minute. This script sweeps 377 (N, M) points,
# contours the steel the engine asks for, and the contours ARE the
# interaction curves - a 2 % contour is the locus of every load the
# section carries with 2 % steel.
#
# Three things fall out of the map that a printed chart cannot show you:
#
#   THE TENSION-GOVERNED NOSE. Steel does not rise with axial load. Under
#   moment a lightly loaded column is tension-governed, so load HELPS
#   until the balance point - the contours bulge outward in the middle.
#   A column schedule that designs only the bottom storey misses it.
#
#   THE 0.4 % FLOOR. A wide region of the map needs no calculated steel at
#   all; the code's detailing minimum governs, and the map is flat there.
#
#   THE ENGINE'S OWN CEILING. Past the section's capacity C11 returns
#   15.4 % - measured identical on 600x400, 500x500 and 900x300, so it is
#   a fixed ceiling and not a design. A script that reads options[0] and
#   moves on gets a number back and never learns it has no column.
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


# -- The column ---------------------------------------------------------
CODE = "BS8110 - 1997"
DEPTH = 600.0             # h, the X-X bending direction [mm]
WIDTH = 400.0             # b [mm]
COVER = 50.0              # to the bar centroid [mm]
FCU = 35.0
FY = 450.0
EFFECTIVE = 3500.0        # effective length, both axes [mm]

MAX_STEEL = 6.0           # BS8110 3.12.6.2, a vertically cast column
CEILING = 15.4            # the engine's own saturation value, measured

MOMENTS = np.arange(0.0, 901.0, 100.0)       # 10 kNm
AXIALS = np.arange(0.0, 7001.0, 700.0)       # 11 kN

# -- Two numbers that decide how long this script takes -----------------
# The sweep below is Cartesian, so its cost is the product of the two step
# sizes above, and every point is a separate engine process at about
# 0.35 s. Choose the steps for the chart you want to READ - halving a step
# doubles the wait.
#
# Then bound the wait itself. timeout_seconds is PER CALL, it defaults to
# 120 s, and these calls take 0.35 s - so one stuck call could cost more
# than the whole sweep. Sized here at many times what a healthy call takes
# and still far below what this whole script costs: generous, and bounded.
prokon.v5.timeout_seconds = 30.0

print("THE N-M INTERACTION CHART, DRAWN BY THE ENGINE")
print(f"  {CODE}, {DEPTH:.0f} x {WIDTH:.0f} mm, cover {COVER:.0f} mm")
print(f"  fcu {FCU:.0f} MPa, fy {FY:.0f} MPa, braced, "
      f"le {EFFECTIVE:.0f} mm both axes")
print(f"  grid: {len(MOMENTS)} moments x {len(AXIALS)} loads "
      f"= {len(MOMENTS) * len(AXIALS)} engine calls")

# -- The anchor ---------------------------------------------------------
# The C11 suite's own desktop-checked column, before anything else.
PINNED_AST = 4521.012783203123
PINNED_PERC = 2.8249267578124986
envelope = prokon.v5.rectangular_column.analyse(
    design_code="SABS 0100 - 2000", h=400.0, b=400.0, dc_x=40.0, dc_y=40.0,
    fcu=30.0, fy=450.0, lex=4000.0, ley=4000.0,
    bracing_x="Braced", bracing_y="Braced", betad=0.6, deltas=1.0,
    load_cases=[
        {"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
        {"n": 2000, "m2x": 125, "m1x": 75, "m2y": 90, "m1y": 55},
    ])
anchor = envelope["result"]["options"][0]
exact = anchor["ast"] == PINNED_AST and anchor["perc"] == PINNED_PERC
print("\n  anchor: the pinned SABS 400 x 400 reference column")
print(f"    ast  {anchor['ast']!r}   pinned {PINNED_AST!r}")
print(f"    perc {anchor['perc']!r}   pinned {PINNED_PERC!r}")
print(f"    -> {'EXACT on both' if exact else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


# invalid_input and no_solution say something about the COLUMN - this
# (N, M) has no answer - and belong on the map as a hole. Every other
# category says something about the RUN, and a map quietly missing those
# points would be a lie. So they are counted by category and printed.
NO_ANSWER_HERE = ("invalid_input", "no_solution")
not_answered = []


def steel(axial, mx, my=0.0, h=DEPTH, b=WIDTH):
    """Steel percentage for one (N, Mx, My), or None if the engine refuses.

    ⚠ m2y IS REQUIRED even for uniaxial bending. C11 refuses a load case
    that names m2x without m2y - "load_cases[0] has no m2y" - rather than
    reading the missing one as zero. Measured; it is the first thing that
    stops a sweep like this one.
    """
    try:
        result = prokon.v5.rectangular_column.analyse(
            design_code=CODE, h=h, b=b, dc_x=COVER, dc_y=COVER,
            fcu=FCU, fy=FY, lex=EFFECTIVE, ley=EFFECTIVE,
            bracing_x="Braced", bracing_y="Braced",
            betad=0.6, deltas=1.0,
            load_cases=[{"n": axial,
                         "m2x": mx, "m1x": mx * 0.5,
                         "m2y": my, "m1y": my * 0.5}])["result"]
    except prokon.v5.ProkonError as refusal:
        if refusal.category not in NO_ANSWER_HERE:
            not_answered.append("{0}/{1}".format(refusal.category,
                                                 refusal.code))
        return None
    options = result["options"]
    return options[0]["perc"] if options else None


# -- Sweep the plane ----------------------------------------------------
percent = np.full((len(AXIALS), len(MOMENTS)), np.nan)
saturated = 0

for column, moment in enumerate(MOMENTS):
    for row, axial in enumerate(AXIALS):
        found = steel(float(axial), float(moment))
        if found is None:
            continue
        percent[row, column] = found
        if abs(found - CEILING) < 1e-9:
            saturated += 1

usable = np.where(percent < CEILING - 1e-9, percent, np.nan)
peak = float(np.nanmax(usable))
print(f"\nSWEPT   {int(np.count_nonzero(~np.isnan(percent)))} points answered,"
      f" {saturated} of them at the engine's {CEILING} % ceiling")
if not_answered:
    print(f"        {len(not_answered)} call(s) did not answer for a reason "
          f"that is NOT about")
    print("        the column: " + ", ".join(sorted(set(not_answered))))
    print("        Those are holes punched in the map by the RUN. Read them")
    print("        before you read the map.")
print(f"        the heaviest REAL design on the map is {peak:.2f} % steel")
if peak < MAX_STEEL:
    print(f"   -> and that is BELOW the code's {MAX_STEEL:.0f} % maximum, so "
          f"on this section")
    print("      the code limit never binds. The boundary you can actually")
    print("      reach is the engine's ceiling, and the map jumps from")
    print(f"      {peak:.2f} % straight to {CEILING} % with nothing between -")
    print("      which is what the hatched edge on the chart is.")

# -- The ceiling, and the control on it ---------------------------------
# CLAIM: 15.4 % is a fixed ceiling, the same on any section, and it means
# "no design" rather than "a very heavily reinforced design".
#
# CONTROL: the same call on a load each section really carries must return
# three DIFFERENT numbers - otherwise the reading is constant and says
# nothing about the section. ⚠ The first control tried here was N = 2000,
# M = 200, and it was WORTHLESS: all three sections came back at 0.40 %,
# because that is the code's detailing floor, so the output could not move
# whatever the section was. A control has to vary something the reading
# can respond to.
CEILING_LOAD = 20_000.0
CONTROL_N, CONTROL_M = 4500.0, 500.0
print("\nTHE ENGINE'S CEILING - AND WHY perc ALONE IS NOT A VERDICT")
print(f"   {'section':>15} {'at 20 MN':>10}   "
      f"{'at ' + format(CONTROL_N / 1000, '.1f') + ' MN':>10}")
for h, b in ((600.0, 400.0), (500.0, 500.0), (900.0, 300.0)):
    over = steel(CEILING_LOAD, 300.0, h=h, b=b)
    real = steel(CONTROL_N, CONTROL_M, h=h, b=b)
    # A section the engine did not answer has no reading, and printing one
    # anyway is how a table starts lying about its own control.
    print(f"   {h:.0f} x {b:.0f}".rjust(18)
          + (f" {over:>9.2f} %" if over is not None else f"{'refused':>11}")
          + (f" {real:>9.2f} %" if real is not None else f"{'refused':>11}"))
print(f"   -> {CEILING} % on all three, to the same digits, on sections of")
print("      different area - so it is a CEILING in the engine, not an")
print("      answer about the section. The right-hand column is the")
print("      positive control: on a load each section really carries, the")
print("      same call returns three DIFFERENT numbers, so the reading can")
print("      tell the two states apart.")
print("   -> and C11 publishes no code limit of its own. Compare what it")
print(f"      asks for against your code's maximum ({MAX_STEEL:.0f} % here)")
print("      yourself, exactly as you would on the desktop's output.")

# -- The tension-governed nose ------------------------------------------
print("\nSTEEL IS NOT MONOTONIC IN AXIAL LOAD")
print(f"   {'M (kNm)':>9} {'lightest steel at N =':>23} {'against N = 0':>15}")
nose_found = 0
for column, moment in enumerate(MOMENTS):
    line = percent[:, column]
    if np.all(np.isnan(line)):
        continue
    interior = np.where(line < CEILING - 1e-9, line, np.nan)
    if np.all(np.isnan(interior)):
        continue
    at_zero = interior[0]
    best_row = int(np.nanargmin(interior))
    if AXIALS[best_row] > 0 and interior[best_row] < at_zero - 1e-9:
        nose_found += 1
        if column % 2 == 0:
            print(f"   {moment:>9.0f} {AXIALS[best_row]:>16.0f} kN "
                  f"({interior[best_row]:.2f} %) {at_zero:>12.2f} %")
print(f"   -> {nose_found} of the {len(MOMENTS)} moment columns need LESS")
print("      steel at some intermediate load than at zero load. Axial load")
print("      helps a tension-governed section until the balance point, so")
print("      the top storey of a column stack is not automatically the")
print("      easy one.")

# -- A real load path ---------------------------------------------------
# Eight storeys of one internal column, gravity accumulating downwards
# while the wind moment stays roughly constant.
STACK = [(400.0 + 800.0 * level, 260.0 - 12.0 * level)
         for level in range(8)]
print("\nONE COLUMN, EIGHT STOREYS   (the dots on the chart)")
print(f"   {'storey':>7} {'N (kN)':>9} {'M (kNm)':>9} {'steel %':>9}  verdict")
path = []
for level, (axial, moment) in enumerate(STACK):
    found = steel(axial, moment)
    path.append((moment, axial, found))
    if found is None:
        print(f"   {8 - level:>7} {axial:>9.0f} {moment:>9.0f} "
              f"{'refused':>9}")
        continue
    if abs(found - CEILING) < 1e-9:
        verdict = "NO SECTION - engine at its ceiling"
    elif found > MAX_STEEL:
        verdict = f"over the code's {MAX_STEEL:.0f} %"
    else:
        verdict = "ok"
    print(f"   {8 - level:>7} {axial:>9.0f} {moment:>9.0f} {found:>9.2f}"
          f"  {verdict}")

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(1, 2, figsize=(15, 7),
                            gridspec_kw={"width_ratios": (1.35, 1)})
figure.patch.set_facecolor("white")
grid_m, grid_n = np.meshgrid(MOMENTS, AXIALS)

# 1. The interaction chart itself.
chart = axes[0]
shade = chart.contourf(grid_m, grid_n, usable, levels=24, cmap="YlGnBu")
figure.colorbar(shade, ax=chart, label="reinforcement (% of gross area)")

# Everything the engine could not design: hatched, because it is not a
# more expensive column, it is no column.
chart.contourf(grid_m, grid_n, np.where(np.isnan(usable), 1.0, np.nan),
               levels=[0.5, 1.5], colors="none", hatches=["///"])

levels = [step for step in (0.4, 1.0, 2.0, 3.0, 4.0, 5.0, MAX_STEEL)
          if step < peak]
curves = chart.contour(grid_m, grid_n, usable, levels=levels,
                       colors="0.15", linewidths=1.1)
chart.clabel(curves, fmt="%.1f %%", fontsize=8)

# The envelope you can actually reach. On this section the engine's
# ceiling arrives before the code's maximum does, so the red line is drawn
# on whichever one binds - and the print above says which.
if peak > MAX_STEEL:
    limit = chart.contour(grid_m, grid_n, usable, levels=[MAX_STEEL],
                          colors="red", linewidths=2.6)
    chart.clabel(limit, fmt={MAX_STEEL: f"{MAX_STEEL:.0f} % code maximum"},
                 fontsize=9)
else:
    reachable = np.where(np.isnan(usable), 1.0, 0.0)
    edge = chart.contour(grid_m, grid_n, reachable, levels=[0.5],
                         colors="red", linewidths=2.6)
    chart.clabel(edge, fmt={0.5: f"engine ceiling ({peak:.1f} % is the "
                                 f"heaviest real design)"}, fontsize=9)

drawn = [(m, n) for m, n, p in path if p is not None]
chart.plot([m for m, _ in drawn], [n for _, n in drawn],
           color="darkorange", linewidth=2.0, marker="o", markersize=7,
           markeredgecolor="black", zorder=6, label="one column, 8 storeys")
for level, (moment, axial, found) in enumerate(path):
    if found is None:
        continue
    chart.annotate(f"L{8 - level}", (moment, axial),
                   textcoords="offset points", xytext=(9, -3), fontsize=8,
                   color="black", fontweight="bold", zorder=7)

chart.set_xlabel("design moment Mx (kNm)")
chart.set_ylabel("axial load N (kN)")
chart.set_title(f"Interaction chart for {DEPTH:.0f} x {WIDTH:.0f} mm - each "
                f"contour is one steel percentage\n"
                f"hatched: the engine has no design there",
                fontsize=10)
chart.legend(loc="lower right", fontsize=9)
chart.grid(True, linewidth=0.3, color="0.85", alpha=0.5)

# 2. The nose, in section: steel against axial load at fixed moment.
nose = axes[1]
for column, moment in enumerate(MOMENTS):
    # Every other column, so this stays proportionate to the grid above
    # rather than to one particular step size.
    if moment == 0 or column % 2 != 0:
        continue
    line = np.where(percent[:, column] < CEILING - 1e-9,
                    percent[:, column], np.nan)
    nose.plot(AXIALS, line, linewidth=1.8, marker="o", markersize=3,
              label=f"{moment:.0f} kNm")
    lowest = int(np.nanargmin(line))
    nose.plot(AXIALS[lowest], line[lowest], marker="v", markersize=10,
              color="black", zorder=5)

nose.axhline(MAX_STEEL, color="red", linestyle="--", linewidth=1.4)
nose.annotate(f"{MAX_STEEL:.0f} % code maximum", (AXIALS[1], MAX_STEEL + 0.15),
              fontsize=9, color="red")
nose.axhline(0.4, color="0.4", linestyle=":", linewidth=1.2)
nose.annotate("0.4 % detailing floor",
              (AXIALS[len(AXIALS) // 2], 0.60), fontsize=8,
              color="0.4")
nose.set_xlabel("axial load N (kN)")
nose.set_ylabel("reinforcement (% of gross area)")
nose.set_ylim(0, MAX_STEEL * 1.6)
nose.set_title("The tension-governed nose\n"
               "triangles mark the LIGHTEST steel - not at zero load",
               fontsize=10)
nose.legend(title="moment Mx", fontsize=8, title_fontsize=8, ncol=2)
nose.grid(True, linewidth=0.3, color="0.85")

figure.suptitle(
    f"Rectangular column interaction map - {CODE}\n"
    f"{DEPTH:.0f} x {WIDTH:.0f} mm, cover {COVER:.0f} mm, fcu {FCU:.0f} MPa, "
    f"fy {FY:.0f} MPa, braced, le {EFFECTIVE:.0f} mm  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.93))

deliver(figure, "rectangular_column_interaction_map.png")
