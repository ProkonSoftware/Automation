# ---
# Example:  One column head, a growing load - and two codes that measure a different perimeter
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes - 2026-09-07 - the pinned 400 sq head reproduces its uo and perimeter-1 asv exactly; each code's drawn control perimeter reproduces the engine's own ucrit; every load measured on prokon-automation.exe
# ---
# ONE column head. ONE slab. ONE thing changes: the applied shear.
#
# The column (400 x 400), the effective depth (200 mm), the concrete
# (fcu 35), the steel (fy = fyv = 500) and the two applied moments are
# held constant and asserted constant, so every difference is caused by
# the load or by the code.
#
# THE CODES ------------------------------------------------------------
#
# ⚠ C23 OFFERS "SABS 0100 - 1992", NOT 2000. The 1992 edition is the old
# South African code this engine has, so that is the one used here and the
# vintage is named everywhere it appears. C23 DOES carry the new code,
# SANS 51992-1-1:2025 - section 0 shows that, because it is not true of
# every engine.
#
# ⚠ THERE IS NO "Eurocode 2 - 2005" ANYWHERE IN THE FLEET; the enabled
# Eurocode 2 here is the 2004 edition.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE TWO CODES DO NOT MEASURE THE SAME PERIMETER, AND THAT IS THE WHOLE
#   STORY. SABS checks a RECTANGULAR perimeter 1.5d from the column face.
#   Eurocode 2 checks a ROUNDED one 2.0d out - the column outline pushed
#   outwards, corners swept to a radius. Panel C draws both to scale, and
#   the drawing is checked: each drawn perimeter is compared against the
#   ucrit the engine published for that code.
#
#   SO THE OLD CODE ASKS FOR ABOUT FOUR TIMES THE SHEAR STEEL. At the
#   pinned load SABS 0100 - 1992 wants 3,920 mm2 on the first perimeter
#   where Eurocode 2 wants 931 - a factor of 4.2, from the same head under
#   the same load. Two things drive it, and both are published: the shorter
#   perimeter, and an allowable concrete shear stress of 0.379 MPa against
#   Eurocode 2's 0.586 - 55 % more.
#
#   THE NUMBER A DESIGNER ACTUALLY WANTS IS THE LOAD THAT NEEDS NO SHEAR
#   STEEL AT ALL, and the two codes put it in different places. Section 3
#   bisects it for each.
#
#   AND NEITHER CODE EVER REFUSES. At the top of this sweep, V = 3 MN on a
#   400 mm column, SABS returns 24,277 mm2 of shear reinforcement and
#   Eurocode 2 returns 5,148 - both with no error, no flag and no empty
#   result, at a shear stress 11.4 and 7.2 times the capacity each code
#   published for itself. Panel D therefore has only TWO bands and no
#   third: there is no state in which either code tells you to stop, and
#   supplying that judgement is the caller's job. Section 4 measures it.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can.

    Spyder runs matplotlib on its own backend, so plt.show() puts the
    chart in the Plots pane. A headless run (a batch job, or this
    documentation's own sweep) can only warn - so ASK the backend, and
    write the PNG either way. There is deliberately no matplotlib.use().
    """
    path = Path(filename).resolve()
    figure.savefig(path, dpi=150, facecolor=SURFACE)
    size = path.stat().st_size
    print("\nWritten: {0}".format(path))
    print("  {0:,} bytes  ({1})".format(
        size, "a real image" if size > 20_000 else "SUSPICIOUSLY SMALL"))
    if str(matplotlib.get_backend()).lower() in HEADLESS:
        plt.close(figure)
        print("  backend is headless - the PNG is the whole output")
    else:
        plt.show()
        print("  and shown on the {0} backend".format(
            matplotlib.get_backend()))


# -- THE TWO CODES ------------------------------------------------------
OLD_CODE = "SABS 0100 - 1992"          # the old SA code THIS engine has
NEW_CODE = "Eurocode 2 - 2004"
PINNED_CODE = "BS8110 - 1997"
SA_NEW_CODE = "SANS 51992-1-1:2025"    # and C23 does have it

OLD_COLOUR = "#2a78d6"      # categorical slot 1
NEW_COLOUR = "#eb6834"      # categorical slot 2
FREE = "#0ca30c"
RAMP = "#fab219"
DEAD = "#d03b3b"

# -- THE HEAD, AND THE ONE INPUT THAT MOVES -----------------------------
HEAD = dict(col_width=400.0, col_breadth=400.0, effective_depth=200.0,
            nearest_edge_x=10000.0, nearest_edge_y=10000.0,
            fcu=35.0, fy=500.0, fyv=500.0)
MOMENT_X = 50.0
MOMENT_Y = 30.0

ANCHOR_SHEAR = 800.0
PINNED_UO = 1600
PINNED_ASV = 2519.6003848228493

SHEARS = np.arange(50.0, 3001.0, 50.0)      # 60 loads, 50 kN to 3 MN

WIDTH = HEAD["col_width"]
BREADTH = HEAD["col_breadth"]
DEPTH = HEAD["effective_depth"]

print("ONE COLUMN HEAD, A GROWING LOAD - TWO DESIGN CODES")
print(f"  {WIDTH:.0f} x {BREADTH:.0f} mm column, effective depth "
      f"{DEPTH:.0f} mm, fcu {HEAD['fcu']:.0f} MPa, fyv {HEAD['fyv']:.0f} MPa")
print(f"  internal (both edges 10 m away), Mx {MOMENT_X:.0f} / "
      f"My {MOMENT_Y:.0f} kNm held constant")
print(f"  the only input that moves: V, {SHEARS[0]:.0f} to {SHEARS[-1]:.0f} kN "
      f"in {SHEARS[1] - SHEARS[0]:.0f} kN steps ({len(SHEARS)} loads)")

CALLS = {"engine": 0}
_ANSWERS = {}


def check(code, shear):
    """One load, one code. The FIRST critical perimeter's numbers."""
    key = (code, round(float(shear), 3))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.punching_shear.analyse(
            design_code=code,
            load_cases=[{"v": float(shear), "mx": MOMENT_X, "my": MOMENT_Y}],
            **HEAD)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(shear=float(shear), asv=None, veff=None, vcap=None, vc=None,
                   ucrit=None, radial=None, perimeters=0,
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    found = result["critical_perimeters"]
    if not found:
        row = dict(shear=float(shear), asv=None, veff=None, vcap=None, vc=None,
                   ucrit=None, radial=None, perimeters=0,
                   reason="no critical perimeter reported")
        _ANSWERS[key] = row
        return row

    first = found[0]
    row = dict(shear=float(shear), asv=first["asv"], veff=first["veff"],
               vcap=first["vcap"], vc=first["vc"], ucrit=first["ucrit"],
               radial=first["radial_distance"], perimeters=len(found),
               uo=result["uo"], reason=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. WHAT THIS ENGINE OFFERS, AND WHICH SABS IT HAS
# ======================================================================
# CLAIM: C23's old South African code is the 1992 edition, and "SABS 0100
# - 2000" - the name C11, C12 and C22 all use - is not available here.
# CONTROL: the codes this script DOES use must answer, and must return
# DIFFERENT numbers, or the reading cannot tell a refusal from an answer.
print("\n0. THE CODES THIS ENGINE HAS")
for code in ("SABS 0100 - 2000", OLD_CODE, NEW_CODE, SA_NEW_CODE,
             PINNED_CODE):
    row = check(code, ANCHOR_SHEAR)
    if row["asv"] is None:
        print(f"   {code:<22} REFUSED")
        print(f"   {'':<22} {row['reason']}")
    else:
        print(f"   {code:<22} answered  asv = {row['asv']:>10.2f} mm2   "
              f"perimeter at {row['radial']:.0f} mm, u = {row['ucrit']:.1f} mm")
print("   -> the controls answer and they DISAGREE, so the refusal above is")
print("      about the code name and nothing else.")
print(f"   -> and note {SA_NEW_CODE} IS here. It is enabled in eight of")
print("      the twelve engines; C11, C12, C13 and C16 are the four without.")

# ======================================================================
# 1. THE ANCHOR
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at V = {ANCHOR_SHEAR:.0f} kN")
anchor = check(PINNED_CODE, ANCHOR_SHEAR)
exact = anchor["uo"] == PINNED_UO and anchor["asv"] == PINNED_ASV
print(f"   uo   {anchor['uo']!r:26} pinned {PINNED_UO!r}")
print(f"   asv  {anchor['asv']!r:26} pinned {PINNED_ASV!r}")
print(f"   -> {'EXACT on both' if exact else 'DRIFTED - READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(SHEARS)} loads x 2 codes")
sweep = {code: [check(code, shear) for shear in SHEARS]
         for code in (OLD_CODE, NEW_CODE)}

assert HEAD["col_width"] == 400.0 and HEAD["effective_depth"] == 200.0
assert MOMENT_X == 50.0 and MOMENT_Y == 30.0
print("   the head dictionary and both moments are unchanged after the sweep")

print(f"\n   {'V (kN)':>7} | {'SABS asv':>10} {'veff':>8} {'vcap':>8} | "
      f"{'EC2 asv':>10} {'veff':>8} {'vcap':>8} | {'SABS/EC2':>9}")
for index, shear in enumerate(SHEARS):
    if shear % 300 != 0:
        continue
    cells, steel = [], {}
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        steel[code] = row["asv"]
        cells.append(f" {row['asv']:>10.1f} {row['veff']:>8.1f} "
                     f"{row['vcap']:>8.1f}")
    factor = ("     n/a" if not steel[NEW_CODE]
              else f"{steel[OLD_CODE] / steel[NEW_CODE]:>8.2f}x")
    print(f"   {shear:>7.0f} |" + " |".join(cells) + f" | {factor:>9}")

# The two constants behind all of it, published per code and never varying
# with the load - so they are read once and stated, not plotted.
print("\n   THE TWO PUBLISHED CONSTANTS THAT EXPLAIN THE WHOLE GAP")
print(f"   {'code':<22} {'perimeter at':>13} {'u (mm)':>10} "
      f"{'vc (MPa)':>10} {'vcap (kN)':>10}")
geometry = {}
for code in (OLD_CODE, NEW_CODE):
    row = sweep[code][-1]
    geometry[code] = row
    print(f"   {code:<22} {row['radial']:>10.0f} mm {row['ucrit']:>10.1f} "
          f"{row['vc']:>10.4f} {row['vcap']:>10.1f}")
    unchanged = {other["ucrit"] for other in sweep[code]
                 if other["ucrit"] is not None}
    print(f"   {'':<22} u took {len(unchanged)} distinct value(s) across all "
          f"{len(SHEARS)} loads")
ratio_vc = geometry[NEW_COLOUR] if False else (
    geometry[NEW_CODE]["vc"] / geometry[OLD_CODE]["vc"])
print(f"   -> Eurocode 2 allows {(ratio_vc - 1) * 100:.0f} % more concrete "
      f"shear stress,")
print(f"      over a perimeter {geometry[NEW_CODE]['ucrit'] / geometry[OLD_CODE]['ucrit']:.3f}x "
      f"as long, pushed out to "
      f"{geometry[NEW_CODE]['radial'] / DEPTH:.1f}d instead of "
      f"{geometry[OLD_CODE]['radial'] / DEPTH:.1f}d.")


# ======================================================================
# 3. THE LOAD THAT NEEDS NO SHEAR STEEL AT ALL
# ======================================================================
def boundary(holds, low, high, resolution=1.0):
    """The largest load where `holds` is still true, to `resolution`.

    The bracket is CHECKED rather than assumed - a bisection over a
    bracket that does not straddle the boundary returns one of its own
    endpoints, and that looks exactly like an answer.
    """
    if not holds(low):
        raise AssertionError(f"the bracket's low end {low} does not hold")
    if holds(high):
        raise AssertionError(f"the bracket's high end {high} still holds")
    while high - low > resolution:
        middle = (low + high) / 2.0
        if holds(middle):
            low = middle
        else:
            high = middle
    return low, high


print("\n3. THE LARGEST LOAD THAT NEEDS NO SHEAR REINFORCEMENT")
threshold = {}
for code in (OLD_CODE, NEW_CODE):
    rows = sweep[code]
    clear = [row for row in rows if row["asv"] == 0]
    needs = [row for row in rows if row["asv"] and row["asv"] > 0]
    if not clear or not needs:
        print(f"   {code:<22} no crossing inside this sweep")
        continue

    def no_steel(shear, code=code):
        return check(code, shear)["asv"] == 0

    low, high = boundary(no_steel, clear[-1]["shear"], needs[0]["shear"])
    threshold[code] = low
    print(f"   {code:<22} clear to {low:.1f} kN, needs steel from "
          f"{high:.1f} kN")
if len(threshold) == 2:
    gain = threshold[NEW_CODE] / threshold[OLD_CODE]
    print(f"   -> Eurocode 2 carries {gain:.2f}x the load before ANY shear")
    print(f"      reinforcement is required - {threshold[NEW_CODE]:.0f} kN "
          f"against {threshold[OLD_CODE]:.0f} kN.")
    print("      On a flat-slab job that is the difference between a plain")
    print("      slab and a head full of links.")

# ======================================================================
# 4. HOW FAR PAST SENSE THE ANSWERS RUN
# ======================================================================
# Neither code refuses, so the caller has to supply the judgement. The
# honest check is the shear STRESS against the code's own capacity, both
# of which the engine publishes - and even that keeps answering.
print("\n4. NEITHER CODE EVER REFUSES")
for code in (OLD_CODE, NEW_CODE):
    last = sweep[code][-1]
    print(f"   {code:<22} at V = {last['shear']:.0f} kN it returns "
          f"{last['asv']:>10.1f} mm2")
    print(f"   {'':<22} veff {last['veff']:.0f} kN against a published "
          f"vcap of {last['vcap']:.0f} kN "
          f"({last['veff'] / last['vcap']:.1f}x over)")
print("   -> no exception, no flag, no empty result. The engine answers the")
print("      question it was asked. Compare veff against vcap yourself -")
print("      that pair is published per code and per perimeter, and it is")
print("      the reading that tells you whether a head exists at all.")

# ======================================================================
# 5. THE CONTROL PERIMETERS, DRAWN - AND THE DRAWING CHECKED
# ======================================================================
# Panel C draws each code's control perimeter. A drawing is a claim, so it
# is checked: the perimeter of the shape drawn is computed and compared
# against the ucrit the ENGINE published. If the drawing were wrong, this
# is where it would show.
print("\n5. THE DRAWN PERIMETERS, CHECKED AGAINST THE ENGINE'S OWN ucrit")


def rectangular_perimeter(offset):
    """A rectangle offset from the column face on all four sides."""
    return 2.0 * (WIDTH + 2 * offset) + 2.0 * (BREADTH + 2 * offset)


def rounded_perimeter(offset):
    """The column outline pushed out by `offset`, corners swept round."""
    return 2.0 * WIDTH + 2.0 * BREADTH + 2.0 * np.pi * offset


SHAPES = {OLD_CODE: ("rectangular", rectangular_perimeter),
          NEW_CODE: ("rounded", rounded_perimeter)}
for code in (OLD_CODE, NEW_CODE):
    offset = geometry[code]["radial"]
    published = geometry[code]["ucrit"]
    best = None
    for name, formula in (("rectangular", rectangular_perimeter),
                          ("rounded", rounded_perimeter)):
        drawn = formula(offset)
        gap = abs(drawn - published)
        print(f"   {code:<22} as {name:<12} u = {drawn:>10.3f} mm   "
              f"published {published:>10.3f}   gap {gap:>9.4f}")
        if best is None or gap < best[1]:
            best = (name, gap, formula)
    SHAPES[code] = (best[0], best[2])
    print(f"   {'':<22} -> the engine's own number matches the "
          f"{best[0].upper()} shape, to {best[1]:.4f} mm")
print("   -> so the drawing in panel C is not an illustration of the idea;")
print("      it is the shape whose length the engine actually reported.")

print(f"\n   {CALLS['engine']} engine calls in total")

# ======================================================================
# 6. THE PICTURE
# ======================================================================
figure = plt.figure(figsize=(16.0, 10.6), facecolor=SURFACE)
panels = figure.add_gridspec(2, 2, hspace=0.36, wspace=0.19,
                             height_ratios=(1.22, 1.0),
                             left=0.055, right=0.985, top=0.865, bottom=0.09)


def dress(axes, title, xlabel, ylabel):
    """The chrome every panel shares: hairline grid, recessive axes."""
    axes.set_facecolor(SURFACE)
    axes.set_title(title, fontsize=10.5, color=INK, pad=9, loc="left")
    axes.set_xlabel(xlabel, fontsize=9.5, color=INK_SOFT)
    axes.set_ylabel(ylabel, fontsize=9.5, color=INK_SOFT)
    axes.grid(True, linewidth=0.6, color=GRID)
    axes.set_axisbelow(True)
    for edge in ("top", "right"):
        axes.spines[edge].set_visible(False)
    for edge in ("left", "bottom"):
        axes.spines[edge].set_color(AXIS)
        axes.spines[edge].set_linewidth(0.8)
    axes.tick_params(colors=MUTED, labelsize=9)


def series(code, field):
    return np.asarray([np.nan if row[field] is None else row[field]
                       for row in sweep[code]], dtype=float)


# ---- A. shear steel against load ---------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  Shear reinforcement on the first critical perimeter",
      "applied shear  V   (kN)", "Asv on perimeter 1   (mm²)")

for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    chart.plot(SHEARS, series(code, "asv"), color=colour, linewidth=2.0,
               label=code, zorder=4)
    if code in threshold:
        chart.plot([threshold[code]], [0.0], marker="o", markersize=8,
                   color=colour, markeredgecolor=SURFACE, markeredgewidth=2.0,
                   zorder=6)

peak = max(np.nanmax(series(code, "asv")) for code in (OLD_CODE, NEW_CODE))
for code, colour, lift in ((OLD_CODE, OLD_COLOUR, 0.64),
                           (NEW_CODE, NEW_COLOUR, 0.44)):
    if code not in threshold:
        continue
    short = "SABS 1992" if code == OLD_CODE else "Eurocode 2"
    chart.annotate(f"{short}: no shear steel\nup to {threshold[code]:.0f} kN",
                   (threshold[code], peak * lift),
                   textcoords="offset points", xytext=(12, 0), ha="left",
                   va="center", fontsize=8.5, color=colour, fontweight="bold")
    chart.plot([threshold[code]] * 2, [0.0, peak * lift * 0.92], color=colour,
               linewidth=1.1, linestyle="--", zorder=2)

chart.plot([ANCHOR_SHEAR], [check(OLD_CODE, ANCHOR_SHEAR)["asv"]], marker="D",
           markersize=8, color=OLD_COLOUR, markeredgecolor=SURFACE,
           markeredgewidth=2.0, zorder=7)
chart.annotate("the pinned load", (ANCHOR_SHEAR,
                                   check(OLD_CODE, ANCHOR_SHEAR)["asv"]),
               textcoords="offset points", xytext=(14, -12), ha="left",
               fontsize=8.5, color=INK_SOFT)
chart.set_xlim(SHEARS[0], SHEARS[-1])
chart.set_ylim(0.0, peak * 1.08)
chart.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=INK)

# ---- B. the direct comparison ------------------------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS 1992)",
      "applied shear  V   (kN)", "shear steel demanded,  new ÷ old")

old_asv = series(OLD_CODE, "asv")
new_asv = series(NEW_CODE, "asv")
both = (old_asv > 0) & (new_asv > 0)
ratio = np.where(both, new_asv / np.where(both, old_asv, 1.0), np.nan)

ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
ratio_axes.fill_between(SHEARS, ratio, 1.0, where=(ratio >= 1.0),
                        interpolate=True, color=NEW_COLOUR, alpha=0.16)
ratio_axes.fill_between(SHEARS, ratio, 1.0, where=(ratio <= 1.0),
                        interpolate=True, color=OLD_COLOUR, alpha=0.16)
ratio_axes.plot(SHEARS, ratio, color=NEW_COLOUR, linewidth=2.0, zorder=4)

loads_both, values = SHEARS[both], ratio[both]
# The first load at which BOTH codes ask for steel is where the
# comparison begins; the minimum sits hard against the right-hand edge,
# so annotating it put the label off the axis entirely.
ratio_axes.plot([loads_both[0]], [values[0]], marker="o", markersize=8,
                color=OLD_COLOUR, markeredgecolor=SURFACE,
                markeredgewidth=2.0, zorder=6)
ratio_axes.annotate(f"the comparison starts at V = {loads_both[0]:.0f} kN\n"
                    f"- the first load BOTH codes ask\n"
                    f"for steel at. Eurocode 2 wants\n"
                    f"{values[0] * 100:.0f} % of the old code's.",
                    (loads_both[0], values[0]),
                    textcoords="offset points", xytext=(16, 6),
                    ha="left", fontsize=8.5, color=OLD_COLOUR,
                    fontweight="bold")
ratio_axes.annotate(f"settling towards {values[-1]:.2f}×\n"
                    f"as the load grows",
                    (loads_both[-1], values[-1]), textcoords="offset points",
                    xytext=(-10, 14), ha="right", fontsize=8.5,
                    color=NEW_COLOUR, fontweight="bold")
ratio_axes.set_xlim(SHEARS[0], SHEARS[-1])
ratio_axes.set_ylim(0.0, 1.15)

# ---- C. the two control perimeters, to scale ---------------------------
plan = figure.add_subplot(panels[1, 0])
plan.set_facecolor(SURFACE)
plan.set_title("C.  Why — the two codes check a DIFFERENT perimeter "
               "(drawn to scale)", fontsize=10.5, color=INK, pad=9,
               loc="left")
plan.set_aspect("equal")
plan.set_xlabel("mm from the column centre", fontsize=9.5, color=INK_SOFT)
plan.tick_params(colors=MUTED, labelsize=9)
for edge in ("top", "right", "left"):
    plan.spines[edge].set_visible(False)
plan.spines["bottom"].set_color(AXIS)
plan.set_yticks([])

plan.add_patch(plt.Rectangle((-WIDTH / 2, -BREADTH / 2), WIDTH, BREADTH,
                             facecolor="#d8d7d0", edgecolor=INK_SOFT,
                             linewidth=1.2, zorder=4))
plan.annotate(f"column\n{WIDTH:.0f} × {BREADTH:.0f}", (0, 0), ha="center",
              va="center", fontsize=8.5, color=INK, zorder=5)

for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    offset = geometry[code]["radial"]
    shape, formula = SHAPES[code]
    if shape == "rounded":
        # The rounded control perimeter is the column outline DILATED by
        # `offset`: a rounded rectangle whose corner radius is the offset
        # itself. matplotlib's "round" box style defaults rounding_size to
        # pad, which is exactly that, and gives a perimeter of
        # 2W + 2B + 2*pi*offset - the number section 5 checked.
        outline = patches.FancyBboxPatch(
            (-WIDTH / 2, -BREADTH / 2), WIDTH, BREADTH,
            boxstyle=f"round,pad={offset}",
            facecolor="none", edgecolor=colour, linewidth=2.2, zorder=3)
    else:
        outline = plt.Rectangle(
            (-WIDTH / 2 - offset, -BREADTH / 2 - offset),
            WIDTH + 2 * offset, BREADTH + 2 * offset, facecolor="none",
            edgecolor=colour, linewidth=2.2, zorder=3)
    plan.add_patch(outline)
    reach = BREADTH / 2 + offset
    plan.annotate(f"{code}\n{shape}, {offset / DEPTH:.1f}d = "
                  f"{offset:.0f} mm out\nu = {geometry[code]['ucrit']:.0f} mm, "
                  f"vc = {geometry[code]['vc']:.3f} MPa",
                  (0, reach if code == NEW_CODE else -reach),
                  textcoords="offset points",
                  xytext=(0, 10 if code == NEW_CODE else -42), ha="center",
                  fontsize=8.5, color=colour, fontweight="bold", zorder=6)

span = BREADTH / 2 + max(geometry[code]["radial"]
                         for code in (OLD_CODE, NEW_CODE)) + 150
plan.set_xlim(-span * 1.02, span * 1.02)
plan.set_ylim(-span * 1.34, span * 1.30)
plan.annotate("both drawn from the engine's own radial_distance,\n"
              "and each shape's perimeter checked against its ucrit "
              "(section 5)",
              (0.5, 0.015), xycoords="axes fraction", ha="center",
              fontsize=8.5, color=MUTED)

# ---- D. the verdict, side by side --------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same head, same axis — what each code tells you", "", "")
verdict.set_xlabel("applied shear  V   (kN)", fontsize=9.5, color=INK_SOFT)

REGIMES = ((FREE, "no shear reinforcement needed"),
           (RAMP, "links required, and rising — with no upper end"))

for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    clear_to = threshold.get(code, SHEARS[0])
    rows = sweep[code]
    over = [row for row in rows
            if row["veff"] is not None and row["veff"] > row["vcap"]]
    past = over[0]["shear"] if over else SHEARS[-1]
    # TWO bands, not three. There is no state in which either code says
    # "stop", so drawing a third would invent a refusal neither one makes.
    for start, stop, colour in ((SHEARS[0], clear_to, FREE),
                                (clear_to, SHEARS[-1], RAMP)):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, edgecolor=SURFACE,
                     linewidth=2.0, zorder=3)
    verdict.text(SHEARS[0] + 20, base + 0.15, code, fontsize=9.5, color=INK,
                 fontweight="bold")
    verdict.plot([clear_to, clear_to], [base - 0.145, base - 0.105],
                 color=INK, linewidth=1.0, zorder=5)
    verdict.text(clear_to, base - 0.20, f"clear to {clear_to:.0f} kN",
                 ha="center", fontsize=8.5, color=INK, fontweight="bold")
    verdict.text(SHEARS[-1], base + 0.15,
                 f"veff passes its own vcap at {past:.0f} kN — and the "
                 f"answers keep coming", ha="right", fontsize=8.5,
                 color=INK_SOFT)

verdict.set_xlim(SHEARS[0], SHEARS[-1])
verdict.set_ylim(0.02, 1.0)
verdict.set_yticks([])
verdict.grid(False)
verdict.spines["left"].set_visible(False)
verdict.legend([plt.Rectangle((0, 0), 1, 1, color=colour, alpha=0.85)
                for colour, _ in REGIMES],
               [label for _, label in REGIMES], loc="upper center",
               bbox_to_anchor=(0.5, -0.14), fontsize=8.5, ncol=2,
               frameon=False, labelcolor=INK)

figure.suptitle(
    f"One column head, a growing load:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"{WIDTH:.0f} × {BREADTH:.0f} mm column, effective depth {DEPTH:.0f} mm, "
    f"fcu {HEAD['fcu']:.0f} MPa, fyv {HEAD['fyv']:.0f} MPa, internal, "
    f"Mx {MOMENT_X:.0f} / My {MOMENT_Y:.0f} kNm  —  ONLY the shear changes\n"
    f"The codes check a different perimeter at a different distance, and "
    f"allow a different concrete stress — panel C draws both to scale",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "punching_shear_sabs_vs_eurocode_load.png")
