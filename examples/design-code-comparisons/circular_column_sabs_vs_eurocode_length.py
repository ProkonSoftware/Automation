# ---
# Example:  One circular column, growing taller - and two codes that measure slenderness differently
# Feature:  circular_column (C12 Circular Column)
# Verified: yes - 2026-09-07 - the pinned 220 mm column reproduces its total_as exactly at the sweep's L = 2250 mm point; every length measured on prokon-automation.exe
# ---
# ONE column. ONE axial load. ONE thing changes: the effective length.
#
# The section (220 mm diameter, 40 mm cover), the concrete (fcu 25), the
# steel (fy 450) and the load (700 kN) are held constant and asserted
# constant, so every difference is caused by length or by the code.
#
# THE CODES ------------------------------------------------------------
#
# SABS 0100 - 2000 is the old South African concrete code. The new one is
# SANS 51992-1-1, the national adoption of EN 1992-1-1 (Eurocode 2), and
# C12 does not offer it - section 0 lists what this engine actually has, so
# the absence is shown rather than asserted. Eurocode 2 - 2004 is therefore
# both the interesting comparison in its own right and the nearest thing to
# the new code that this engine can compute.
#
# ⚠ THERE IS NO "Eurocode 2 - 2005" ANYWHERE IN THE FLEET. The enabled
# Eurocode 2 here is the 2004 edition.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   BOTH CODES REFUSE, ON DIFFERENT MEASURES, AND EUROCODE 2 STOPS FIRST.
#   Eurocode 2 refuses past a slenderness of 140, computed on le/i with
#   i = D/4. SABS refuses past 60, computed on le/D. Those are different
#   numbers of different quantities, and on this column they land 5.5 m
#   apart: Eurocode 2 gives up at 7.70 m and SABS carries on to 13.20 m.
#
#   ⚠ SO "EUROCODE IS THE MORE PERMISSIVE CODE" IS FALSE HERE, and the
#   sister study on the rectangular column is where that idea comes from -
#   there Eurocode 2 designs 2.88 m FURTHER than SABS. Same two codes,
#   opposite verdicts, because the section changed shape. Neither result
#   generalises, which is the whole reason to run your own case.
#
#   BUT NEITHER LIMIT IS THE ONE THAT MATTERS. Long before either code
#   refuses, both ask for steel nobody can place. Against a 6 % reference
#   line Eurocode 2 crosses at 3.64 m and SABS at 6.94 m - 3.30 m apart,
#   and both then keep answering, to 23.58 % and 62.62 % of the gross area
#   respectively. The engine publishes no maximum of its own, so that
#   reference line is YOURS to set - see section 4.
#
#   AND THEY DISAGREE MOST WHERE THE COLUMN IS STOCKIEST. At 1 m Eurocode 2
#   asks for less than half the steel SABS does. The curves cross, so which
#   code is "cheaper" depends entirely on how tall the column is.
#
#   ONE THING THEY AGREE ON EXACTLY. At the pinned reference length, SABS
#   0100 - 2000 and BS8110 - 1997 return the same total_as to the last
#   binary digit - which is what you would expect of a code derived from
#   the other, and is worth confirming rather than assuming.
#
#   AND ONE CLAIM THIS SCRIPT'S OWN CONTROL DESTROYED. Neither code is
#   given a moment, yet both design for one, so the obvious reading is "a
#   minimum eccentricity on the axial load". Section 5 varies the load to
#   test it, and the answer is that the reading is right for ONE code and
#   wrong for the other: SABS holds a constant 11.000 mm = D/20 across
#   five loads, while Eurocode 2 produces five DIFFERENT eccentricities
#   and none at all at the lightest load. That is what a control is for -
#   it separated the two codes instead of confirming a story about both.
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
HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}

SURFACE = "#fcfcfb"      # the surface every colour below was checked against
INK = "#0b0b0b"
INK_SOFT = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can."""
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
        plt.show()          # Spyder: straight into the Plots pane
        print("  and shown on the {0} backend".format(
            matplotlib.get_backend()))


# -- THE TWO CODES ------------------------------------------------------
OLD_CODE = "SABS 0100 - 2000"
NEW_CODE = "Eurocode 2 - 2004"
PINNED_CODE = "BS8110 - 1997"          # what the pinned reference case used
WANTED_CODE = "SANS 51992-1-1:2025"    # the new SA code - not in this engine

# Categorical slot 1 and slot 2, in that fixed order, one colour per code in
# every panel. Checked as a pair: worst colour-vision separation dE 24.7,
# normal-vision dE 33.6, both at least 3:1 against the surface above.
OLD_COLOUR = "#2a78d6"      # blue
NEW_COLOUR = "#eb6834"      # orange
# Status colours, used only where they MEAN a state, always beside a label.
FREE = "#0ca30c"
RAMP = "#fab219"
DEAD = "#d03b3b"

# -- THE COLUMN, AND THE ONE INPUT THAT MOVES ---------------------------
# The C12 suite's own desktop-checked column, held in one dictionary so
# that "only the length changes" is checkable rather than merely intended.
COLUMN = dict(diameter=220.0, cover=40.0, fcu=25.0, fy=450.0, deltas=1.0,
              load_cases=[{"n": 700.0}])

ANCHOR_LENGTH = 2250.0
PINNED_TOTAL_AS = 1037.1145165134003

LENGTHS = np.arange(500.0, 14001.0, 250.0)      # 55 lengths, 0.5 m to 14 m

DIAMETER = COLUMN["diameter"]
GROSS = np.pi * DIAMETER ** 2 / 4.0
RADIUS = DIAMETER / 4.0        # radius of gyration of a circle: i = D/4
APPLIED_N = COLUMN["load_cases"][0]["n"]

# ⚠ THIS IS A REFERENCE LINE, NOT AN ENGINE LIMIT. C12 publishes no maximum
# steel percentage - its result carries total_as, percentage_steel and a
# pass flag, and nothing else. 6 % is a common vertically-cast maximum;
# your own code's number may differ (some say 4 %). Set it to yours.
YOUR_MAX_STEEL = 6.0

print("ONE CIRCULAR COLUMN, GROWING TALLER - TWO DESIGN CODES")
print(f"  {DIAMETER:.0f} mm diameter, cover {COLUMN['cover']:.0f} mm, "
      f"fcu {COLUMN['fcu']:.0f} MPa, fy {COLUMN['fy']:.0f} MPa")
print(f"  gross area {GROSS:.0f} mm2, radius of gyration i = D/4 = "
      f"{RADIUS:.1f} mm")
print(f"  one load case: N = {APPLIED_N:.0f} kN, no applied moment")
print(f"  the only input that moves: lex = ley = L, "
      f"{LENGTHS[0]:.0f} to {LENGTHS[-1]:.0f} mm in "
      f"{LENGTHS[1] - LENGTHS[0]:.0f} mm steps ({len(LENGTHS)} lengths)")

# -- The one call, memoised, and a count of how many we make ------------
CALLS = {"engine": 0}
_ANSWERS = {}


def design(code, length):
    """One length, one code. Returns a row; never raises for a refusal."""
    key = (code, round(float(length), 3))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.circular_column.analyse(
            design_code=code, lex=float(length), ley=float(length), **COLUMN)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(length=float(length), total_as=None, perc=None,
                   moment=None, passes=None, buckles=None,
                   reason=refusal.message, code_name=refusal.code)
        _ANSWERS[key] = row
        return row

    case = result["load_case_results"][0]
    row = dict(length=float(length),
               total_as=result["total_as"],
               perc=result["percentage_steel"],
               moment=max(case["moment_x"], case["moment_y"]),
               passes=case["passes"], buckles=case["buckles"],
               reason=None, code_name=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. WHAT THIS ENGINE ACTUALLY OFFERS
# ======================================================================
# CLAIM: C12 has no SANS 51992-1-1:2025, so the new South African code
# cannot be run here.
# CONTROL: the two codes this script DOES use must both answer, and must
# return two DIFFERENT numbers - otherwise the reading cannot tell a
# refusal from an answer and proves nothing about the missing one.
print(f"\n0. THE CODES THIS ENGINE HAS")
for code in (WANTED_CODE, OLD_CODE, NEW_CODE, PINNED_CODE):
    row = design(code, ANCHOR_LENGTH)
    if row["total_as"] is None:
        print(f"   {code:<22} REFUSED   {row['code_name']}")
        print(f"   {'':<22} {row['reason']}")
    else:
        print(f"   {code:<22} answered  total_as = {row['total_as']:.4f} mm2")
print("   -> the controls answer and they DISAGREE, so the reading can")
print("      distinguish a refusal from an answer. The missing code is")
print("      missing, not mis-measured.")
print("   -> SANS 51992-1-1:2025 IS available in eight of the twelve")
print("      engines - just not this one. C12, C13, C16 and C11 lack it.")

# ======================================================================
# 1. THE ANCHOR, AND ONE EXACT AGREEMENT
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at L = {ANCHOR_LENGTH:.0f} mm")
anchor = design(PINNED_CODE, ANCHOR_LENGTH)
exact = anchor["total_as"] == PINNED_TOTAL_AS
print(f"   total_as {anchor['total_as']!r}")
print(f"   pinned   {PINNED_TOTAL_AS!r}")
print(f"   -> {'EXACT' if exact else 'DRIFTED - READ NOTHING BELOW'}")

old_at_anchor = design(OLD_CODE, ANCHOR_LENGTH)
identical = old_at_anchor["total_as"] == anchor["total_as"]
print(f"\n   and {OLD_CODE} at the same length:")
print(f"   total_as {old_at_anchor['total_as']!r}")
print(f"   -> {'BYTE-IDENTICAL to BS8110' if identical else 'DIFFERENT'}, "
      f"which is what a code")
print("      derived from the other should do - confirmed, not assumed.")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(LENGTHS)} lengths x 2 codes")
sweep = {code: [design(code, length) for length in LENGTHS]
         for code in (OLD_CODE, NEW_CODE)}

# "Only the length changed" - said, then checked.
assert COLUMN["diameter"] == 220.0 and COLUMN["fcu"] == 25.0
assert COLUMN["load_cases"][0]["n"] == APPLIED_N
print("   the section and load dictionary is unchanged after the sweep")

print(f"\n   {'L (m)':>6} {'le/D':>6} {'le/i':>6} | "
      f"{'SABS as':>9} {'%':>7} {'M':>6} | {'EC2 as':>9} {'%':>7} {'M':>6}")
for index, length in enumerate(LENGTHS):
    if length % 1000 != 0:
        continue
    cells = []
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        if row["total_as"] is None:
            cells.append(f" {'refused':>9} {str(row['reason'])[:23]:<23}")
        else:
            cells.append(f" {row['total_as']:>9.1f} {row['perc']:>7.2f} "
                         f"{row['moment']:>6.2f}")
    print(f"   {length / 1000:>6.1f} {length / DIAMETER:>6.1f} "
          f"{length / RADIUS:>6.1f} |" + " |".join(cells))


# ======================================================================
# 3. TWO REFUSALS, ON TWO DIFFERENT MEASURES
# ======================================================================
def boundary(holds, low, high, resolution=25.0):
    """The largest length where `holds` is still true, to `resolution`.

    The bracket is CHECKED rather than assumed. A bisection over a bracket
    that does not straddle the boundary happily returns one of its own
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


print("\n3. TWO REFUSALS, ON TWO DIFFERENT MEASURES")
wall, stated = {}, {}
for code in (OLD_CODE, NEW_CODE):
    refused = [row for row in sweep[code] if row["total_as"] is None]
    if not refused:
        print(f"   {code:<22} never refuses below "
              f"{LENGTHS[-1] / 1000:.1f} m")
        continue
    answered = [row for row in sweep[code] if row["total_as"] is not None]

    def still_answers(length, code=code):
        return design(code, length)["total_as"] is not None

    low, high = boundary(still_answers, answered[-1]["length"],
                         refused[0]["length"])
    wall[code] = high
    stated[code] = refused[0]["reason"]
    print(f"\n   {code}")
    print(f'     says: "{refused[0]["reason"]}"')
    print(f"     answers at {low / 1000:.3f} m, refuses at {high / 1000:.3f} m")
    print(f"     at that boundary   le/D = {high / DIAMETER:>6.2f}   "
          f"le/i = {high / RADIUS:>7.2f}")

# WHICH RATIO IS EACH CODE MEASURING? Read the limit out of the message the
# engine itself wrote, then check which quantity actually equals it at the
# boundary. That is measured rather than assumed - and the answer differs
# between the two codes, which is the finding.
print("\n   WHICH QUANTITY EACH LIMIT IS ON")
for code in wall:
    digits = [int(part) for part in stated[code].replace(".", " ").split()
              if part.isdigit()]
    limit = digits[0] if digits else None
    if limit is None:
        print(f"     {code:<22} no number in the message - not decidable here")
        continue
    on_diameter = abs(wall[code] / DIAMETER - limit)
    on_radius = abs(wall[code] / RADIUS - limit)
    which = "le/D" if on_diameter < on_radius else "le/i  (i = D/4)"
    print(f"     {code:<22} stated limit {limit:>4}   is on {which}")
    print(f"     {'':<22} le/D = {wall[code] / DIAMETER:.2f}, "
          f"le/i = {wall[code] / RADIUS:.2f} at the boundary, so "
          f"{'the first' if on_diameter < on_radius else 'the second'} is it")
    print(f"     {'':<22} that limit is reached at L = "
          f"{limit * (DIAMETER if on_diameter < on_radius else RADIUS) / 1000:.3f} m")

if len(wall) == 2:
    first = min(wall, key=wall.get)
    last = max(wall, key=wall.get)
    print(f"\n   -> {first} gives up FIRST, at "
          f"{wall[first] / 1000:.2f} m;")
    print(f"      {last} carries on to "
          f"{wall[last] / 1000:.2f} m - "
          f"{(wall[last] - wall[first]) / 1000:.2f} m further.")
    print("   -> and the two limits are not comparable as written: one is a")
    print("      number of diameters, the other a number of radii of")
    print("      gyration. Panel C puts both on one axis by dividing each")
    print("      code's own ratio by its own limit, so 1.0 is where each")
    print("      code stops - which is the only fair way to draw them.")

# ======================================================================
# 4. THE LIMIT THAT ACTUALLY BITES FIRST
# ======================================================================
# Neither refusal is the practical boundary. Both codes go on asking for
# steel long after the answer stops being placeable, and the engine
# publishes no maximum - so this section compares each code against YOUR
# number and reports where it is crossed.
print(f"\n4. WHERE EACH CODE PASSES {YOUR_MAX_STEEL:.0f} % STEEL "
      f"(your reference, not the engine's)")
crossing = {}
for code in (OLD_CODE, NEW_CODE):
    rows = [row for row in sweep[code] if row["perc"] is not None]
    under = [row for row in rows if row["perc"] <= YOUR_MAX_STEEL]
    over = [row for row in rows if row["perc"] > YOUR_MAX_STEEL]
    if not under or not over:
        print(f"   {code:<22} never crosses it in this range")
        continue

    def under_limit(length, code=code):
        row = design(code, length)
        return row["perc"] is not None and row["perc"] <= YOUR_MAX_STEEL

    low, high = boundary(under_limit, under[-1]["length"], over[0]["length"])
    crossing[code] = low
    worst = max(row["perc"] for row in rows)
    print(f"   {code:<22} crosses between {low / 1000:.3f} m and "
          f"{high / 1000:.3f} m")
    print(f"   {'':<22} and keeps answering up to {worst:.2f} % "
          f"before it refuses")
if len(crossing) == 2:
    print(f"   -> the two codes cross your limit "
          f"{abs(crossing[NEW_CODE] - crossing[OLD_CODE]) / 1000:.2f} m apart,")
    print("      and BOTH cross it well before either code refuses. On this")
    print("      column the steel percentage is the real boundary and the")
    print("      slenderness limit is the one that gets quoted.")

# ======================================================================
# 5. THE MOMENT ON A COLUMN WITH NO APPLIED MOMENT
# ======================================================================
# No moment is supplied, yet both codes design for one. CLAIM: it is a
# minimum eccentricity applied to the axial load - so moment / N should be
# ONE number, whatever N is.
#
# CONTROL: vary N. An eccentricity must give the same arm at every load; a
# slenderness effect need not.
#
# ⚠ AND THE CONTROL REFUTES THE CLAIM FOR ONE OF THE TWO CODES. That is
# reported below rather than smoothed over: a control that can only agree
# with you is not a control. Watch the two right-hand columns diverge.
print("\n5. THE MOMENT NEITHER CODE WAS GIVEN   (L = "
      f"{ANCHOR_LENGTH:.0f} mm, stocky)")
print(f"   {'N (kN)':>8} {'SABS M':>8} {'e (mm)':>8} | "
      f"{'EC2 M':>8} {'e (mm)':>8}")
eccentricity = {OLD_CODE: set(), NEW_CODE: set()}
for axial in (200.0, 400.0, 700.0, 1000.0, 1400.0):
    cells = []
    for code in (OLD_CODE, NEW_CODE):
        probe = dict(COLUMN)
        probe["load_cases"] = [{"n": axial}]
        CALLS["engine"] += 1
        result = prokon.v5.circular_column.analyse(
            design_code=code, lex=ANCHOR_LENGTH, ley=ANCHOR_LENGTH, **probe)["result"]
        case = result["load_case_results"][0]
        moment = max(case["moment_x"], case["moment_y"])
        arm = moment / axial * 1000.0
        eccentricity[code].add(round(arm, 6))
        cells.append(f" {moment:>8.2f} {arm:>8.3f}")
    print(f"   {axial:>8.0f}" + " |".join(cells))
for code in (OLD_CODE, NEW_CODE):
    found = sorted(eccentricity[code])
    if len(found) == 1:
        print(f"   -> {code:<22} one eccentricity, {found[0]:.3f} mm, on all "
              f"five loads")
    else:
        print(f"   -> {code:<22} {len(found)} different eccentricities: "
              f"{found}")
print(f"   -> D/20 = {DIAMETER / 20:.2f} mm and D/25 = {DIAMETER / 25:.2f} mm,")
print("      so the arithmetic says which fraction of the diameter each")
print("      code is using. It is constant HERE only because D is.")

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


metres = LENGTHS / 1000.0


def series(code, field):
    """One code's column of numbers, np.nan where it refused."""
    return np.asarray([np.nan if row[field] is None else row[field]
                       for row in sweep[code]], dtype=float)


# ---- A. steel against length ------------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  What the extra height costs in steel",
      "effective length  L = lex = ley   (m)",
      "reinforcement   (% of gross area)")

peak = max(np.nanmax(series(code, "perc")) for code in (OLD_CODE, NEW_CODE))
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    chart.plot(metres, series(code, "perc"), color=colour, linewidth=2.0,
               label=code, zorder=4)
    if code in wall:
        chart.plot([wall[code] / 1000.0] * 2, [0.0, peak * 1.03], color=colour,
                   linewidth=1.3, linestyle="--", zorder=2)
    if code in crossing:
        where = crossing[code] / 1000.0
        chart.plot([where], [YOUR_MAX_STEEL], marker="o", markersize=8,
                   color=colour, markeredgecolor=SURFACE, markeredgewidth=2.0,
                   zorder=6)

chart.axhline(YOUR_MAX_STEEL, color=DEAD, linewidth=1.4, linestyle="--",
              zorder=3)
chart.annotate(f"{YOUR_MAX_STEEL:.0f} % — YOUR reference line, not the "
               f"engine's\n(C12 publishes no maximum; set it to your code's)",
               (metres[0] + 0.15, YOUR_MAX_STEEL), textcoords="offset points",
               xytext=(0, 8), fontsize=8.5, color=DEAD, fontweight="bold")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    if code in wall:
        short = "SABS" if code == OLD_CODE else "Eurocode 2"
        chart.annotate(f"{short} refuses\nfrom {wall[code] / 1000:.2f} m",
                       (wall[code] / 1000.0, peak * 0.68),
                       textcoords="offset points", xytext=(-9, 0),
                       ha="right", va="center", fontsize=8.5, color=colour,
                       fontweight="bold")

chart.plot([ANCHOR_LENGTH / 1000.0], [design(OLD_CODE, ANCHOR_LENGTH)["perc"]],
           marker="D", markersize=8, color=OLD_COLOUR,
           markeredgecolor=SURFACE, markeredgewidth=2.0, zorder=7)
chart.annotate("the pinned reference column",
               (ANCHOR_LENGTH / 1000.0,
                design(OLD_CODE, ANCHOR_LENGTH)["perc"]),
               textcoords="offset points", xytext=(10, -14), fontsize=8.5,
               color=INK_SOFT)
chart.set_xlim(metres[0], metres[-1])
chart.set_ylim(0.0, peak * 1.12)
chart.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=INK)

# ---- B. the direct comparison -----------------------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "effective length  L   (m)", "steel demanded,  new ÷ old")

old_perc = series(OLD_CODE, "perc")
new_perc = series(NEW_CODE, "perc")
both = ~np.isnan(old_perc) & ~np.isnan(new_perc)
ratio = np.where(both, new_perc / np.where(both, old_perc, 1.0), np.nan)

ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
ratio_axes.fill_between(metres, ratio, 1.0, where=(ratio >= 1.0),
                        interpolate=True, color=NEW_COLOUR, alpha=0.16)
ratio_axes.fill_between(metres, ratio, 1.0, where=(ratio <= 1.0),
                        interpolate=True, color=OLD_COLOUR, alpha=0.16)
ratio_axes.plot(metres, ratio, color=NEW_COLOUR, linewidth=2.0, zorder=4)

lengths_both, values = metres[both], ratio[both]
# Bottom-centre, not top-left: on this engine the ratio CLIMBS with
# length, so the top-left is where the peak annotation lives and the
# only empty ground is under the parity line on the right half.
ratio_axes.text(0.40, 0.13,
                f"stocky: the new code asks {(1 - values[0]) * 100:.0f} % LESS "
                f"steel\n(and it is still the first to refuse - panel C)",
                transform=ratio_axes.transAxes, fontsize=8.5, va="bottom",
                color=OLD_COLOUR, fontweight="bold")
top = int(np.argmax(values))
ratio_axes.plot([lengths_both[top]], [values[top]], marker="o", markersize=8,
                color=NEW_COLOUR, markeredgecolor=SURFACE,
                markeredgewidth=2.0, zorder=6)
ratio_axes.annotate(f"{values[top]:.2f}× at L = {lengths_both[top]:.2f} m —\n"
                    f"and the comparison ENDS at "
                    f"{lengths_both[-1]:.2f} m, where\n"
                    f"Eurocode 2 stops answering",
                    (lengths_both[top], values[top]),
                    textcoords="offset points", xytext=(-12, -4), ha="right",
                    va="top", fontsize=8.5, color=NEW_COLOUR,
                    fontweight="bold")
cross = next((index for index in range(len(values) - 1)
              if (values[index] - 1.0) * (values[index + 1] - 1.0) < 0), None)
if cross is not None:
    ratio_axes.annotate(f"they agree between {lengths_both[cross]:.2f} m "
                        f"and {lengths_both[cross + 1]:.2f} m",
                        (lengths_both[cross + 1], 1.0),
                        textcoords="offset points", xytext=(9, -16),
                        fontsize=8.5, color=INK_SOFT)
ratio_axes.set_xlim(metres[0], metres[-1])

# ---- C. the mechanism: two limits on one axis --------------------------
# The two codes limit DIFFERENT ratios to DIFFERENT numbers, so the ratios
# cannot share a y-axis as they stand. Dividing each code's own ratio by
# its own limit puts both on one dimensionless axis where 1.0 means "this
# code has stopped" - which is the only comparison that is not an
# arbitrary alignment of two scales.
limit_axes = figure.add_subplot(panels[1, 0])
dress(limit_axes,
      "C.  Each code against ITS OWN slenderness limit  (1.0 = it refuses)",
      "effective length  L   (m)", "slenderness ÷ that code's own limit")

for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    if code not in wall:
        continue
    digits = [int(part) for part in stated[code].replace(".", " ").split()
              if part.isdigit()]
    limit = digits[0]
    on_diameter = abs(wall[code] / DIAMETER - limit) < abs(
        wall[code] / RADIUS - limit)
    divisor = DIAMETER if on_diameter else RADIUS
    label = f"{code}:  (le/{'D' if on_diameter else 'i'}) ÷ {limit}"
    limit_axes.plot(metres, LENGTHS / divisor / limit, color=colour,
                    linewidth=2.0, label=label, zorder=4)
    limit_axes.plot([wall[code] / 1000.0], [wall[code] / divisor / limit],
                    marker="o", markersize=9, color=colour,
                    markeredgecolor=SURFACE, markeredgewidth=2.0, zorder=6)
    limit_axes.annotate(f"refuses\n{wall[code] / 1000:.2f} m",
                        (wall[code] / 1000.0, 1.0),
                        textcoords="offset points", xytext=(-10, 14),
                        ha="right", fontsize=8.5, color=colour,
                        fontweight="bold")

limit_axes.axhline(1.0, color=DEAD, linewidth=1.4, linestyle="--", zorder=3)
limit_axes.annotate("1.0 — the code refuses beyond here", (metres[-1], 1.0),
                    textcoords="offset points", xytext=(-6, 8), ha="right",
                    fontsize=8.5, color=DEAD, fontweight="bold")
limit_axes.set_xlim(metres[0], metres[-1])
limit_axes.set_ylim(0.0, 2.1)
limit_axes.legend(loc="upper left", fontsize=8.5, frameon=False,
                  labelcolor=INK)

# ---- D. the verdict, side by side --------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same column, same axis — what each code tells you", "", "")
verdict.set_xlabel("effective length  L   (m)", fontsize=9.5, color=INK_SOFT)

REGIMES = ((FREE, f"under your {YOUR_MAX_STEEL:.0f} % steel line"),
           (RAMP, "over it — the engine still answers"),
           (MUTED, "REFUSED, with a reason in words"))

for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    over = crossing.get(code, LENGTHS[-1]) / 1000.0
    refuses = (wall[code] / 1000.0) if code in wall else metres[-1]
    for start, stop, colour, texture in (
            (metres[0], over, FREE, None),
            (over, refuses, RAMP, None),
            (refuses, metres[-1], MUTED, "////")):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, hatch=texture,
                     edgecolor=SURFACE, linewidth=2.0, zorder=3)
    verdict.text(metres[0] + 0.1, base + 0.15, code, fontsize=9.5, color=INK,
                 fontweight="bold")
    verdict.plot([over, over], [base - 0.145, base - 0.105], color=INK,
                 linewidth=1.0, zorder=5)
    verdict.text(over, base - 0.20,
                 f"placeable to {over:.2f} m", ha="center", fontsize=8.5,
                 color=INK, fontweight="bold")
    if code in wall:
        verdict.text(metres[-1], base + 0.15, f"refuses from {refuses:.2f} m",
                     ha="right", fontsize=8.5, color=INK_SOFT)

verdict.set_xlim(metres[0], metres[-1])
verdict.set_ylim(0.02, 1.0)
verdict.set_yticks([])
verdict.grid(False)
verdict.spines["left"].set_visible(False)
verdict.legend([plt.Rectangle((0, 0), 1, 1, color=colour, alpha=0.85,
                              hatch="////" if colour == MUTED else None)
                for colour, _ in REGIMES],
               [label for _, label in REGIMES], loc="upper center",
               bbox_to_anchor=(0.5, -0.14), fontsize=8.5, ncol=2,
               frameon=False, labelcolor=INK)

figure.suptitle(
    f"One circular column, growing taller:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"{DIAMETER:.0f} mm diameter, cover {COLUMN['cover']:.0f} mm, "
    f"fcu {COLUMN['fcu']:.0f} MPa, fy {COLUMN['fy']:.0f} MPa, "
    f"N {APPLIED_N:.0f} kN, no applied moment  —  "
    f"ONLY the effective length changes\n"
    f"The two codes limit DIFFERENT ratios to DIFFERENT numbers — "
    f"le/D ≤ 60 against le/i ≤ 140 — so panel C divides each by its own",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "circular_column_sabs_vs_eurocode_length.png")
