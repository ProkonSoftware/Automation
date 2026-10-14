# ---
# Example:  One slab panel, a growing load - what the design code changes, and what it does not
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - the identical-moments control asserted in-script on all four faces at two loads; the ten-point load sweep and the h = 150.5 mm designability threshold measured on prokon-automation.exe
# ---
# ONE slab panel. TWO codes. The load grows, and nothing else moves.
#
# The panel (7.5 x 5.0 m, 200 mm), both effective depths (165 and 150 mm),
# the concrete (fcu 30), the steel (fy 450) and the four encastre edges are
# held constant - so every difference below is caused by the load or by the
# code, and by nothing else.
#
# THE CODES ------------------------------------------------------------
#
# ⚠ C04's OLD SOUTH AFRICAN CODE IS "SABS0100 - 1992" - the 1992 edition,
# and note the spelling: no space after SABS, unlike the "SABS 0100 - 2000"
# that C11, C12 and C22 use. Two engines in this fleet spell it that way and
# the string is not interchangeable. C04 also carries the new code,
# SANS 51992-1-1:2025.
#
# ⚠ There is no "Eurocode 2 - 2005" anywhere in the fleet; the enabled
# Eurocode 2 here is the 2004 edition.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE MOMENTS DO NOT DEPEND ON THE CODE, AT ALL. Section 1 asserts it:
#   the same panel under the same load gives BIT-IDENTICAL moments under
#   both codes, on all four faces. The analysis is elasticity and geometry;
#   the code enters afterwards, when the moment is turned into steel. That
#   is worth knowing before you spend an afternoon wondering which code to
#   analyse in.
#
#   THE STEEL DOES, BUT LESS THAN YOU WOULD GUESS, AND NOT EVENLY. Over a
#   fifty-fold range of load, Eurocode 2 asks for between 1.2 % and 4.5 %
#   LESS bottom steel than the old code. The gap is not constant and the
#   curves never cross, so neither code is "the heavy one" by a fixed
#   margin - section 2 draws it.
#
#   AND THEY DISAGREE ABOUT WHAT IS DESIGNABLE AT ALL. Below a slab
#   thickness of about 150.5 mm on this panel, Eurocode 2 returns ZERO
#   steel for both y faces while the old code designs them normally - same
#   moments, same section, one code declines and the other does not.
#   Section 3 bisects that threshold. It is the finding with the sharpest
#   practical edge, because nothing in the result says "declined".
#
# ⚠ AND ONE FINDING THIS FILE USED TO REPORT IS RETRACTED, because the
# engine no longer publishes what it was measured from. It said the two
# codes differ by a 33 % CAPACITY gap - mu.x_bot of 126.60 against 168.84
# kNm/m - matching a beam study to four significant figures. `mu` was a
# property of the old one-metre-strip command, which designed a section
# from a moment you supplied. The panel command analyses a slab and
# publishes moments, steel and deflection; there is no singly-reinforced
# capacity in it to compare. The ratio is not disproved here - it is simply
# no longer measurable on this engine, and a number nobody can re-measure
# does not belong in a verified example.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

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
        plt.show()
        print("  and shown on the {0} backend".format(matplotlib.get_backend()))


OLD = "SABS0100 - 1992"
NEW = "Eurocode 2 - 2004"

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"
FACES = ("x_top", "x_bot", "y_top", "y_bot")

COVER, BAR = 25.0, 12.0

PANEL = dict(lx=7.5, ly=5.0, h=200.0, dx=165.0, dy=150.0,
             fcu=30.0, fy=450.0,
             edge_top=ENCASTRE, edge_right=ENCASTRE,
             edge_bottom=ENCASTRE, edge_left=ENCASTRE)

LOADS = np.array([2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 80.0, 100.0])


def analyse(code, udl, **changes):
    inputs = dict(PANEL)
    inputs.update(changes)
    return prokon.v5.rectangular_slab.analyse(
        design_code=code,
        load_cases=[{"number": 1, "lf": 1.4, "udl": float(udl)}],
        **inputs)["result"]


def declined_faces(result):
    """Faces carrying a moment that came back with no steel."""
    return [face for face in FACES
            if result["ast"][face] == 0.0 and result["moment_max"][face] > 0.0]


print("ONE SLAB PANEL, TWO DESIGN CODES")
print(f"  {PANEL['lx']} x {PANEL['ly']} m, {PANEL['h']:.0f} mm, "
      f"dx {PANEL['dx']:.0f} / dy {PANEL['dy']:.0f}, "
      f"fcu {PANEL['fcu']:.0f}, fy {PANEL['fy']:.0f}, encastre all round")
print(f"  {OLD}  vs  {NEW}")

# ── 1. THE CONTROL: what the code does NOT change ──────────────────────
print("\n1. THE MOMENTS DO NOT DEPEND ON THE CODE")
print(f"   {'udl':>6}  {'face':<7} {'old':>12} {'new':>12}  identical?")

moments_identical = True
for udl in (5.0, 45.0):
    old = analyse(OLD, udl)
    new = analyse(NEW, udl)
    for face in FACES:
        same = old["moment_max"][face] == new["moment_max"][face]
        moments_identical = moments_identical and same
        print(f"   {udl:>6.1f}  {face:<7} {old['moment_max'][face]:>12.6f} "
              f"{new['moment_max'][face]:>12.6f}  {same}")

assert moments_identical, "the codes disagreed about the moments"
print("   -> BIT-IDENTICAL on every face at both loads. The analysis is")
print("      elasticity and geometry; the code enters only when the moment")
print("      is turned into steel. So 'which code should I analyse in?' has")
print("      no answer, because the analysis is not the part the code owns.")

# ── 2. WHAT THE CODE DOES CHANGE ───────────────────────────────────────
print("\n2. THE STEEL, ACROSS THE LOAD RANGE")
print(f"   {'udl':>6} {'moment x_bot':>13} {'old ast':>10} {'new ast':>10} "
      f"{'new/old':>9}")

old_steel, new_steel, ratios = [], [], []
for udl in LOADS:
    old = analyse(OLD, udl)
    new = analyse(NEW, udl)

    assert not declined_faces(old) and not declined_faces(new), (
        f"a face was declined at {udl} kPa - the sweep is off the designable "
        f"range and section 2 would be comparing a zero to a number")

    old_a = old["ast"]["x_bot"]
    new_a = new["ast"]["x_bot"]
    old_steel.append(old_a)
    new_steel.append(new_a)
    ratios.append(new_a / old_a)

    print(f"   {udl:>6.1f} {old['moment_max']['x_bot']:>13.4f} "
          f"{old_a:>10.2f} {new_a:>10.2f} {new_a / old_a:>9.4f}")

crossed = min(ratios) < 1.0 < max(ratios)
print(f"\n   ratio runs {min(ratios):.4f} to {max(ratios):.4f}")
print(f"   the curves cross: {crossed}")
print(f"   -> Eurocode 2 asks for {100 * (1 - max(ratios)):.1f} % to "
      f"{100 * (1 - min(ratios)):.1f} % LESS bottom steel here, and the gap")
print("      is NOT constant - it narrows as the load grows and then widens")
print("      again. A single 'Eurocode is x % lighter' factor would be wrong")
print("      at both ends of this range.")

# ── 3. THE DISAGREEMENT THAT MATTERS ───────────────────────────────────
# Same moments, same section - and one code designs a face the other will
# not. Nothing in the result says "declined": the steel is simply zero.
print("\n3. AND THEY DISAGREE ABOUT WHAT IS DESIGNABLE")
print(f"   the same panel at 5 kPa, thinned down")
print(f"   {'h':>6}  {OLD:<28} {NEW:<28}")


def declined_at(code, thickness):
    dx = thickness - COVER - BAR / 2.0
    result = analyse(code, 5.0, h=thickness, dx=dx, dy=dx - BAR)
    return declined_faces(result)


for thickness in (130.0, 140.0, 150.0, 160.0, 180.0, 200.0):
    a = declined_at(OLD, thickness)
    b = declined_at(NEW, thickness)
    print(f"   {thickness:>6.0f}  {(','.join(a) or 'designs all four'):<28} "
          f"{(','.join(b) or 'designs all four'):<28}")

low, high = 130.0, 200.0
for _ in range(30):
    middle = 0.5 * (low + high)
    if declined_at(NEW, middle):
        low = middle
    else:
        high = middle

print(f"\n   {NEW} starts designing all four faces at "
      f"h = {high:.3f} mm")
print(f"   {OLD} designs all four at every thickness in that range.")
print("   -> below that line one code returns zero steel for the two y faces")
print("      and the other returns real areas, from the SAME moments. The")
print("      result carries no flag: `ast` is simply 0.0. Any script that")
print("      sweeps geometry has to test `ast == 0 and moment_max > 0`, and")
print("      a study that switches codes has to test it on BOTH.")

# ── The figure ─────────────────────────────────────────────────────────
figure = plt.figure(figsize=(13.5, 5.4))
figure.patch.set_facecolor("white")
grid = figure.add_gridspec(1, 2, wspace=0.26)

steel_chart = figure.add_subplot(grid[0, 0])
steel_chart.plot(LOADS, old_steel, marker="o", markersize=4, linewidth=2.0,
                 color="#b03030", label=OLD)
steel_chart.plot(LOADS, new_steel, marker="s", markersize=4, linewidth=2.0,
                 color="#4c78a8", label=NEW)
steel_chart.set_xlabel("uniform load (kPa, unfactored)")
steel_chart.set_ylabel("bottom steel in x (mm2/m)")
steel_chart.set_title("The same panel, the same moments,\ntwo codes",
                      fontsize=10)
steel_chart.legend(fontsize=8)
steel_chart.grid(True, linewidth=0.3, color="0.85")

ratio_chart = figure.add_subplot(grid[0, 1])
ratio_chart.plot(LOADS, ratios, marker="o", markersize=4, linewidth=2.0,
                 color="#333333")
ratio_chart.axhline(1.0, color="red", linewidth=1.2, linestyle="--")
ratio_chart.annotate("equal steel", (LOADS[-1], 1.0),
                     textcoords="offset points", xytext=(-58, 6),
                     fontsize=8, color="red")
ratio_chart.set_xlabel("uniform load (kPa, unfactored)")
ratio_chart.set_ylabel("Eurocode 2 steel / old code steel")
ratio_chart.set_title("The gap is not a constant factor\n"
                      "and the curves never cross", fontsize=10)
ratio_chart.grid(True, linewidth=0.3, color="0.85")

figure.suptitle(
    f"{OLD} vs {NEW} - {PANEL['lx']} x {PANEL['ly']} m panel, "
    f"{PANEL['h']:.0f} mm, fcu {PANEL['fcu']:.0f}, fy {PANEL['fy']:.0f}",
    fontsize=10)
figure.subplots_adjust(left=0.07, right=0.97, top=0.83, bottom=0.13)

deliver(figure, "rectangular_slab_sabs_vs_eurocode.png")
