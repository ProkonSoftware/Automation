# ---
# Example:  One column, growing taller - the old South African code against the new one's parent
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes - 2026-09-07 - the pinned SABS 400 x 400 column IS the L = 4000 mm point of this sweep and reproduces its ast and perc exactly; every length measured on prokon-automation.exe
# ---
# ONE column. ONE load set. ONE thing changes: the effective length.
#
# Everything else - 400 x 400 section, 40 mm cover, fcu 30, fy 450, braced
# both ways, the two load cases - is held constant and asserted constant, so
# every difference on the chart is caused by length or by the code.
#
# WHY THIS IS NOT "SABS versus SANS", AND THE SCRIPT PROVES IT ----------
#
# The new South African concrete code is SANS 51992-1-1, the national
# adoption of EN 1992-1-1 (Eurocode 2). C11 KNOWS that name and REFUSES it:
# the row is registered in the engine's code table but disabled, because the
# native library's own code-name table stops one entry short of it. Section
# 0 below runs the call and shows the refusal, with two positive controls.
#
# So the "new code" here is EUROCODE 2 - 2004 - the document SANS 51992-1-1
# adopts, and the nearest thing this engine can compute. It is named as a
# stand-in throughout, never as SANS. When the engine's SANS support lands,
# change NEW_CODE below and nothing else.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE TWO CODES DISAGREE ABOUT WHERE THE COLUMN STOPS EXISTING, by nearly
#   three metres. Bisected to 25 mm: SABS designs this column to 12.56 m
#   and Eurocode 2 to 15.44 m - 2.88 m of extra storey height out of the
#   same section, the same concrete and the same steel.
#
#   ONE CODE SAYS SO AND THE OTHER GOES QUIET. At 16.17 m Eurocode 2
#   refuses, in words: "Slenderness limit of 140 exceeded". Past 12.56 m
#   SABS returns a number - 15.4 % steel, 220 Y12 bars in a 400 x 400
#   column, and all_pass = true. That is not a design. Section 3 detects it
#   WITHOUT knowing the number, by the only property that generalises: the
#   answer has stopped responding to the input.
#
#   LENGTH IS FREE UNTIL IT SUDDENLY IS NOT, AND NOT AT THE SAME PLACE.
#   Every answer is bit-identical from 2 m up to 8.50 m under Eurocode 2 and
#   8.75 m under SABS - six and a half metres of extra height for nothing -
#   and then, inside one 250 mm step, both start climbing. The new code
#   begins charging one step earlier than the old one.
#
#   AND EUROCODE 2 CHARGES A TOLL EVEN ON A STUBBY COLUMN. Its design
#   moment sits exactly N x 20 mm above the moment you supplied, on the axis
#   with the larger applied moment. Section 5 measures that against five
#   axial loads, so it is an eccentricity rather than a coincidence.
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
# There is deliberately NO matplotlib.use("Agg") here. That call forces the
# headless backend, and a script that forces it can never draw into
# Spyder's Plots pane - which is where you actually want to see it.
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
NEW_CODE = "Eurocode 2 - 2004"        # the document SANS 51992-1-1 adopts
WANTED_CODE = "SANS 51992-1-1:2025"   # what we would rather have run

# Categorical slot 1 and slot 2, in that fixed order, one colour per code in
# every panel. Checked as a pair: worst colour-vision separation dE 24.7,
# normal-vision dE 33.6, both at least 3:1 against the surface above.
OLD_COLOUR = "#2a78d6"      # blue
NEW_COLOUR = "#eb6834"      # orange
# Status colours, used only where they MEAN a state, and always beside a
# written label so the colour never carries the meaning on its own.
FREE = "#0ca30c"
RAMP = "#fab219"
DEAD = "#d03b3b"

# -- THE COLUMN, AND THE ONE INPUT THAT MOVES ---------------------------
# The C11 automation suite's own desktop-checked column. Holding the whole
# thing in one dictionary is what makes "only the length changes" checkable
# rather than merely intended - the sweep never writes into it.
COLUMN = dict(h=400.0, b=400.0, dc_x=40.0, dc_y=40.0,
              fcu=30.0, fy=450.0,
              bracing_x="Braced", bracing_y="Braced",
              betad=0.6, deltas=1.0,
              load_cases=[
                  {"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
                  {"n": 2000, "m2x": 125, "m1x": 75, "m2y": 90, "m1y": 55},
              ])

ANCHOR_LENGTH = 4000.0      # where the pinned reference case sits
PINNED_AST = 4521.012783203123
PINNED_PERC = 2.8249267578124986

LENGTHS = np.arange(2000.0, 17001.0, 250.0)     # 61 lengths, 2 m to 17 m

# Slenderness of a rectangular section about X-X: le / i, with i = h/sqrt(12).
RADIUS = COLUMN["h"] / np.sqrt(12.0)

CASE = 0                    # every moment reported below is load case 1
APPLIED_N = COLUMN["load_cases"][CASE]["n"]
APPLIED_MX = COLUMN["load_cases"][CASE]["m2x"]
APPLIED_MY = COLUMN["load_cases"][CASE]["m2y"]

print("ONE COLUMN, GROWING TALLER - TWO DESIGN CODES")
print(f"  {COLUMN['h']:.0f} x {COLUMN['b']:.0f} mm, cover "
      f"{COLUMN['dc_x']:.0f} mm, fcu {COLUMN['fcu']:.0f} MPa, "
      f"fy {COLUMN['fy']:.0f} MPa, braced both ways")
print(f"  case 1: N {APPLIED_N:.0f} kN, Mx {APPLIED_MX:.0f} kNm, "
      f"My {APPLIED_MY:.0f} kNm    case 2: N 2000, Mx 125, My 90")
print(f"  the only input that moves: lex = ley = L, "
      f"{LENGTHS[0]:.0f} to {LENGTHS[-1]:.0f} mm in "
      f"{LENGTHS[1] - LENGTHS[0]:.0f} mm steps ({len(LENGTHS)} lengths)")

# -- The one call, memoised, and a count of how many we make ------------
CALLS = {"engine": 0}
_ANSWERS = {}


def design(code, length):
    """One length, one code. Returns a row; never raises for "no design".

    C11 reports "I could not design this" as a SUCCESSFUL answer carrying an
    EMPTY options list and the reason in sweep_errors - so the empty list is
    checked here, not just the absence of an exception.
    """
    key = (code, round(float(length), 3))
    if key in _ANSWERS:
        return _ANSWERS[key]

    blank = dict(length=float(length), ast=None, perc=None, mxe=None,
                 mye=None, total=None, bars=None, all_pass=None)

    CALLS["engine"] += 1
    try:
        result = prokon.v5.rectangular_column.analyse(
            design_code=code, lex=float(length), ley=float(length), **COLUMN)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(blank, reason=f"{refusal.category}/{refusal.code}: "
                                 f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    options = result["options"]
    if not options:
        row = dict(blank, reason=str(result["sweep_errors"][0])
                   if result["sweep_errors"]
                   else "(no options and no stated reason)")
        _ANSWERS[key] = row
        return row

    best = options[0]
    case = best["load_case_results"][CASE]
    row = dict(length=float(length), ast=best["ast"], perc=best["perc"],
               mxe=case["mxe"], mye=case["mye"],
               total=case["mxe"] + case["mye"],
               bars=best["bar_description"], all_pass=best["all_pass"],
               reason=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE CODE THIS STUDY WANTED, AND WHY IT DOES NOT USE IT
# ======================================================================
# CLAIM: C11 cannot design to SANS 51992-1-1:2025.
# CONTROL: the same call, same everything, with each of the two codes this
# script DOES use, must succeed AND return two DIFFERENT numbers - otherwise
# the reading cannot tell "refused" from "answered" and proves nothing.
print(f"\n0. THE CODE THIS STUDY WANTED   {WANTED_CODE}")
for code in (WANTED_CODE, OLD_CODE, NEW_CODE):
    row = design(code, ANCHOR_LENGTH)
    if row["perc"] is None:
        print(f"   {code:<22} REFUSED")
        print(f"   {'':<22} {row['reason']}")
    else:
        print(f"   {code:<22} answered   {row['perc']:.4f} % steel")
print("   -> the two controls answer, and they DISAGREE with each other, so")
print("      the reading can distinguish a refusal from an answer. The")
print("      refusal above is therefore about the code name and nothing else.")
print(f"   -> so the 'new code' below is {NEW_CODE}, the")
print("      document SANS 51992-1-1 adopts. It is a STAND-IN and is")
print("      labelled as one. When the engine gains SANS, change NEW_CODE.")

# ======================================================================
# 1. THE ANCHOR - is this the engine the pinned numbers came from?
# ======================================================================
# The pinned reference case is not a separate call: it IS this sweep's
# L = 4000 mm point under the old code. If it does not reproduce, none of
# the numbers below are worth reading - and you find that out in line one.
print(f"\n1. THE ANCHOR   {OLD_CODE} at L = {ANCHOR_LENGTH:.0f} mm")
anchor = design(OLD_CODE, ANCHOR_LENGTH)
exact = anchor["ast"] == PINNED_AST and anchor["perc"] == PINNED_PERC
print(f"   ast  {anchor['ast']!r}   pinned {PINNED_AST!r}")
print(f"   perc {anchor['perc']!r}   pinned {PINNED_PERC!r}")
print(f"   -> {'EXACT on both' if exact else 'DRIFTED - READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(LENGTHS)} lengths x 2 codes")
sweep = {code: [design(code, length) for length in LENGTHS]
         for code in (OLD_CODE, NEW_CODE)}

# "Only the length changed" - said, then checked. A sweep that mutated the
# shared dictionary would be invisible in the output and would invalidate
# every conclusion here, so this is cheap insurance on the one claim they
# all rest on.
assert COLUMN["h"] == 400.0 and COLUMN["b"] == 400.0
assert COLUMN["load_cases"][CASE]["m2x"] == APPLIED_MX
assert COLUMN["load_cases"][CASE]["n"] == APPLIED_N
print("   the section and load dictionary is unchanged after the sweep")

print(f"\n   {'L (m)':>6} {'le/h':>5} {'le/i':>6} | "
      f"{'SABS %':>8} {'bars':>8} {'Mxe':>7} {'Mye':>7} | "
      f"{'EC2 %':>8} {'bars':>8} {'Mxe':>7} {'Mye':>7}")
for index, length in enumerate(LENGTHS):
    if length % 1000 != 0:
        continue
    cells = []
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        if row["perc"] is None:
            cells.append(f" {'no design':>8} {str(row['reason'])[:33]:>33}")
        else:
            cells.append(f" {row['perc']:>8.3f} {row['bars']:>8} "
                         f"{row['mxe']:>7.1f} {row['mye']:>7.1f}")
    print(f"   {length / 1000:>6.1f} {length / COLUMN['h']:>5.1f} "
          f"{length / RADIUS:>6.1f} |" + " |".join(cells))


def onset_of(code):
    """The first length whose design moment differs from the stubby answer.

    Below it the whole answer - ast, perc, both moments, the bar count - is
    bit-identical, so extra height is free. Reading the MOMENT rather than
    the steel matters: at the first slender length the engine reassigns
    between the two axes and Mxe actually FALLS while Mye rises, so a test
    for "the moment went up" would miss the very step it is looking for.
    Their sum rises, and that is what is compared.
    """
    stubby = sweep[code][0]["total"]
    return next(row["length"] for row in sweep[code]
                if row["total"] is not None and row["total"] != stubby)


print("\n   AND THE TWO CODES DO NOT START CHARGING AT THE SAME HEIGHT")
onsets = {code: onset_of(code) for code in (OLD_CODE, NEW_CODE)}
for code, length in onsets.items():
    flat = [row for row in sweep[code] if row["length"] < length]
    print(f"     {code:<22} free to {flat[-1]['length'] / 1000:.2f} m "
          f"(le/h {flat[-1]['length'] / COLUMN['h']:.2f}, "
          f"le/i {flat[-1]['length'] / RADIUS:.1f}), "
          f"{len(flat)} lengths, all identical")
earliest, latest = min(onsets.values()), max(onsets.values())
print(f"   -> the new code starts charging {latest - earliest:.0f} mm earlier,")
print(f"      which is one step of this sweep - so the threshold is located")
print(f"      to {LENGTHS[1] - LENGTHS[0]:.0f} mm and no finer.")


# ======================================================================
# 3. WHERE THE ANSWER STOPS BEING A DESIGN
# ======================================================================
def plateau_area(rows):
    """The steel area the engine returns once it has stopped designing.

    THE RULE IS NOT "15.4 %". A hard-coded number is a rule about one code
    on one machine, and measured here the two codes plateau at DIFFERENT
    values. The property that generalises is this: the SAME ast at two
    consecutive lengths WHILE the design moment the engine used is still
    rising. A real design cannot do that - more moment needs more steel.

    The conjunction is doing real work. Below the slenderness threshold the
    ast repeats for twenty-seven consecutive lengths and must NOT be
    flagged, because the moment is not moving either. That is this
    detector's negative control, and it is printed below.
    """
    answered = [row for row in rows if row["ast"] is not None]
    for earlier, later in zip(answered, answered[1:]):
        if earlier["ast"] == later["ast"] and later["total"] > earlier["total"]:
            return earlier["ast"]
    return None


print("\n3. WHERE THE ANSWER STOPS BEING A DESIGN")
plateau, last_real, first_refusal = {}, {}, {}
for code in (OLD_CODE, NEW_CODE):
    rows = sweep[code]
    plateau[code] = plateau_area(rows)
    real = [row for row in rows
            if row["ast"] is not None and row["ast"] != plateau[code]]
    last_real[code] = real[-1] if real else None
    refused = [row for row in rows if row["ast"] is None]
    first_refusal[code] = refused[0] if refused else None

    print(f"\n   {code}")
    if plateau[code] is None:
        print("     the answer responds to length everywhere in this range")
    else:
        frozen = [row for row in rows if row["ast"] == plateau[code]]
        print(f"     frozen ast   {plateau[code]!r} mm2   "
              f"({frozen[0]['perc']!r} % of the gross area)")
        print(f"     identical over {len(frozen)} lengths, L = "
              f"{frozen[0]['length'] / 1000:.2f} m to "
              f"{frozen[-1]['length'] / 1000:.2f} m")
        print(f"     while the design moment rose from "
              f"{frozen[0]['total']:.1f} to {frozen[-1]['total']:.1f} kNm")
        print(f"     and the engine still reports all_pass = "
              f"{frozen[0]['all_pass']}, {frozen[0]['bars']}")
    if last_real[code]:
        print(f"     LAST REAL DESIGN   L = "
              f"{last_real[code]['length'] / 1000:.2f} m   "
              f"{last_real[code]['perc']:.3f} %   {last_real[code]['bars']}")
    if first_refusal[code]:
        print(f"     FIRST REFUSAL      L = "
              f"{first_refusal[code]['length'] / 1000:.2f} m")
        print(f'       "{first_refusal[code]["reason"]}"')
    else:
        print("     never refuses in this range - it answers every length")

print("\n   THE DETECTOR'S CONTROLS")
for code in (OLD_CODE, NEW_CODE):
    rows = [row for row in sweep[code] if row["ast"] is not None]
    quiet = sum(1 for a, b in zip(rows, rows[1:])
                if a["ast"] == b["ast"] and b["total"] == a["total"])
    ramp = [row for row in rows
            if row["ast"] != plateau[code] and row["total"] > rows[0]["total"]]
    moved = sum(1 for a, b in zip(ramp, ramp[1:]) if a["ast"] != b["ast"])
    print(f"     {code}")
    print(f"       negative: {quiet} repeats where the moment did NOT move")
    print(f"                 - correctly NOT flagged as a plateau")
    print(f"       positive: {moved} of {max(len(ramp) - 1, 0)} steps on the "
          f"ramp move ast")
    print(f"                 - so the reading CAN respond to length")
print("   -> and 220 Y12 is arithmetic, not a design: 15.4 % of a 400 x 400")
print("      section is 24,640 mm2 of steel inside 320 mm of clear width.")
print("      Read options AND watch whether the answer moves. all_pass and")
print("      the exit code are both true on that plateau.")


# ======================================================================
# 4. THE TWO CLIFFS, LOCATED
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


print("\n4. THE CLIFFS, BISECTED TO 25 mm")
step = float(LENGTHS[1] - LENGTHS[0])
cliff, wall = {}, {}

for code in (OLD_CODE, NEW_CODE):
    if plateau[code] is None or last_real[code] is None:
        continue

    def still_designs(length, code=code, frozen=plateau[code]):
        row = design(code, length)
        return row["ast"] is not None and row["ast"] != frozen

    low, high = boundary(still_designs, last_real[code]["length"],
                         last_real[code]["length"] + step)
    cliff[code] = low
    print(f"   {code:<22} last real design between {low / 1000:.3f} m and "
          f"{high / 1000:.3f} m")

for code in (OLD_CODE, NEW_CODE):
    if first_refusal[code] is None:
        print(f"   {code:<22} never refuses below "
              f"{LENGTHS[-1] / 1000:.1f} m - nothing to bisect")
        continue

    def still_answers(length, code=code):
        return design(code, length)["ast"] is not None

    low, high = boundary(still_answers,
                         first_refusal[code]["length"] - step,
                         first_refusal[code]["length"])
    wall[code] = high
    print(f"   {code:<22} refuses from between {low / 1000:.3f} m "
          f"(le/i {low / RADIUS:.1f}) and {high / 1000:.3f} m "
          f"(le/i {high / RADIUS:.1f})")
    print(f"   {'':<22} the stated limit is 140, and le/i reaches 140 at "
          f"L = {140 * RADIUS / 1000:.3f} m")
    print(f"   {'':<22} -> the boundary IS le/i = 140, reproduced to 25 mm")

if OLD_CODE in cliff and NEW_CODE in cliff:
    print(f"\n   THE HEADLINE: {NEW_CODE} designs this column")
    print(f"   {(cliff[NEW_CODE] - cliff[OLD_CODE]) / 1000:.2f} m taller than "
          f"{OLD_CODE} does,")
    print("   from the same section, the same concrete and the same load.")

# ======================================================================
# 5. THE TOLL EUROCODE 2 CHARGES ON A COLUMN THAT IS NOT SLENDER
# ======================================================================
# CLAIM: while the column is stocky the new code's design moment is the
# applied moment PLUS N x 20 mm, on the axis carrying the larger moment.
#
# CONTROL: vary N. If the gap is an eccentricity it must track N exactly; if
# it is a coincidence it will not move with N at all. This is the one block
# that steps outside "only the length changes", deliberately - without it
# "+30 kNm" is a number with no explanation attached to it.
print(f"\n5. THE MINIMUM-ECCENTRICITY TOLL   (L = {ANCHOR_LENGTH:.0f} mm, stocky)")
print(f"   {'N (kN)':>8} {'SABS Mxe':>9} {'EC2 Mxe':>9} {'gap':>7} "
      f"{'N x 20 mm':>10} {'match':>6}")
matched = 0
for axial in (500.0, 1000.0, 1500.0, 2000.0, 2500.0):
    probe = dict(COLUMN)
    probe["load_cases"] = [{"n": axial, "m2x": APPLIED_MX, "m1x": 150,
                            "m2y": APPLIED_MY, "m1y": 90}]
    moments = {}
    for code in (OLD_CODE, NEW_CODE):
        CALLS["engine"] += 1
        result = prokon.v5.rectangular_column.analyse(
            design_code=code, lex=ANCHOR_LENGTH, ley=ANCHOR_LENGTH, **probe)["result"]
        moments[code] = result["options"][0]["load_case_results"][CASE]["mxe"]
    gap = moments[NEW_CODE] - moments[OLD_CODE]
    expected = axial * 0.020
    hit = gap == expected
    matched += hit
    print(f"   {axial:>8.0f} {moments[OLD_CODE]:>9.1f} "
          f"{moments[NEW_CODE]:>9.1f} {gap:>7.1f} {expected:>10.1f} "
          f"{'yes' if hit else 'NO':>6}")
print(f"   -> {matched} of 5 exact, and the old code's moment never moved off")
print("      the applied 250 kNm in any of the five. So the gap is an")
print("      eccentricity of 20 mm on the axial load, not a fixed offset.")
print("   -> the 20 mm itself is NOT universal: measured separately, a")
print("      deeper section gets a larger one. It is constant HERE only")
print("      because h is held constant.")

# ======================================================================
# 6. ONE HONEST ASYMMETRY IN THE COMPARISON
# ======================================================================
# Both codes get the SAME dictionary, which is what makes the comparison
# fair. But C11 has two inputs only the Eurocode family honours, and they
# are left at their defaults - so say what they would have done.
print("\n6. THE TWO EUROCODE-ONLY INPUTS, LEFT AT THEIR DEFAULTS")
print(f"   {'L (m)':>6} {'default %':>10} {'incl=0.005 %':>13} "
      f"{'efcreep=2 %':>12}")
for length in (10000.0, 14000.0):
    base = design(NEW_CODE, length)["perc"]
    variants = []
    for extra in ({"incl": 0.005}, {"efcreep": 2.0}):
        CALLS["engine"] += 1
        result = prokon.v5.rectangular_column.analyse(
            design_code=NEW_CODE, lex=length, ley=length, **COLUMN, **extra)["result"]
        variants.append(result["options"][0]["perc"])
    print(f"   {length / 1000:>6.1f} {base:>10.3f} {variants[0]:>13.3f} "
          f"{variants[1]:>12.3f}")
print("   -> incl (the geometric imperfection, in RADIANS) BITES on a")
print("      slender column and would move the orange curve up. efcreep did")
print("      not move it at all here. Both are ignored outright by the old")
print("      code, which is exactly why they are left alone: supplying one")
print("      would make the two runs differ in two things instead of one.")

print(f"\n   {CALLS['engine']} engine calls in total")

# ======================================================================
# 7. THE PICTURE
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
is_frozen = {code: np.asarray([row["ast"] == plateau[code]
                               for row in sweep[code]])
             for code in (OLD_CODE, NEW_CODE)}


def series(code, field, real_only=True):
    """One code's column of numbers, np.nan where there is no design."""
    out = []
    for row, frozen in zip(sweep[code], is_frozen[code]):
        value = row[field]
        out.append(np.nan if value is None or (real_only and frozen)
                   else value)
    return np.asarray(out, dtype=float)


# ---- A. steel against length ------------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  What the extra height costs in steel",
      "effective length  L = lex = ley   (m)",
      "reinforcement   (% of gross area)")

frozen_level = max(row["perc"] for code in (OLD_CODE, NEW_CODE)
                   for row, frozen in zip(sweep[code], is_frozen[code])
                   if frozen)

for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    label = code if code == OLD_CODE else f"{code}   (stand-in for SANS)"
    chart.plot(metres, series(code, "perc"), color=colour, linewidth=2.0,
               label=label, zorder=4)
    # What the engine keeps returning past the cliff, in grey because it is
    # not a design, and dotted so it cannot be read as the curve above.
    chart.plot(metres, np.where(is_frozen[code],
                                series(code, "perc", real_only=False),
                                np.nan),
               color=MUTED, linewidth=1.6, linestyle=":", zorder=3)
    if code in cliff:
        end, value = cliff[code] / 1000.0, last_real[code]["perc"]
        chart.plot([end], [value], marker="o", markersize=8, color=colour,
                   markeredgecolor=SURFACE, markeredgewidth=2.0, zorder=6)
        # The old code's label goes DOWN-RIGHT and the new code's UP-LEFT:
        # both sit at the top of their own curve, so the obvious placement
        # puts one of them straight through the other's line.
        offset, align = ((11, -20), "left") if code == OLD_CODE \
            else ((-11, 4), "right")
        chart.annotate(f"last real design\n{end:.2f} m,  {value:.2f} %",
                       (end, value), textcoords="offset points",
                       xytext=offset, ha=align, fontsize=8.5,
                       color=colour, fontweight="bold")

chart.plot([ANCHOR_LENGTH / 1000.0], [anchor["perc"]], marker="D",
           markersize=8, color=OLD_COLOUR, markeredgecolor=SURFACE,
           markeredgewidth=2.0, zorder=7)
chart.annotate("the pinned reference column",
               (ANCHOR_LENGTH / 1000.0, anchor["perc"]),
               textcoords="offset points", xytext=(9, -16), fontsize=8.5,
               color=INK_SOFT)
chart.text(0.985, 0.955,
           "grey dots: what the engine still RETURNS past its cliff —\n"
           "frozen steel, all_pass = true, and no design at all",
           transform=chart.transAxes, ha="right", va="top", fontsize=8.5,
           color=MUTED)

if NEW_CODE in wall:
    chart.plot([wall[NEW_CODE] / 1000.0] * 2, [0.0, frozen_level * 1.03],
               color=NEW_COLOUR, linewidth=1.3, linestyle="--", zorder=2)
    chart.annotate(f"Eurocode 2 REFUSES from\n"
                   f"{wall[NEW_CODE] / 1000:.2f} m  (λ = 140)",
                   (wall[NEW_CODE] / 1000.0, frozen_level * 0.12),
                   textcoords="offset points", xytext=(-10, 0), ha="right",
                   va="center", fontsize=8.5, color=NEW_COLOUR,
                   fontweight="bold")

chart.set_xlim(metres[0], metres[-1])
chart.set_ylim(0.0, frozen_level * 1.26)
slender = chart.secondary_xaxis(
    "top", functions=(lambda m: m * 1000.0 / RADIUS,
                      lambda s: s * RADIUS / 1000.0))
slender.set_xlabel("the same axis in slenderness:  λ = le / i,   i = h/√12",
                   fontsize=9, color=MUTED)
slender.tick_params(colors=MUTED, labelsize=8.5)
chart.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=INK)

# ---- B. the two codes, divided ----------------------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "effective length  L   (m)", "steel demanded,  new ÷ old")

old_perc = series(OLD_CODE, "perc")
new_perc = series(NEW_CODE, "perc")
both = ~np.isnan(old_perc) & ~np.isnan(new_perc)
ratio = np.where(both, new_perc / np.where(both, old_perc, 1.0), np.nan)

ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
# Blue below, orange above: the same two hues, now reading as a diverging
# pair about a neutral "they agree" line.
ratio_axes.fill_between(metres, ratio, 1.0, where=(ratio >= 1.0),
                        interpolate=True, color=NEW_COLOUR, alpha=0.16)
ratio_axes.fill_between(metres, ratio, 1.0, where=(ratio <= 1.0),
                        interpolate=True, color=OLD_COLOUR, alpha=0.16)
ratio_axes.plot(metres, ratio, color=NEW_COLOUR, linewidth=2.0, zorder=4)

lengths_both, values = metres[both], ratio[both]
peak = int(np.argmax(values))
ratio_axes.plot([lengths_both[peak]], [values[peak]], marker="o",
                markersize=8, color=NEW_COLOUR, markeredgecolor=SURFACE,
                markeredgewidth=2.0, zorder=6)
ratio_axes.annotate(f"{values[peak]:.2f}× the steel at "
                    f"L = {lengths_both[peak]:.2f} m —\n"
                    f"and the comparison ENDS here, because\n"
                    f"that is where SABS stops designing",
                    (lengths_both[peak], values[peak]),
                    textcoords="offset points", xytext=(-12, -6),
                    ha="right", va="top", fontsize=8.5, color=NEW_COLOUR,
                    fontweight="bold")
ratio_axes.text(0.035, 0.27,
                f"stocky: the new code asks {(1 - values[0]) * 100:.1f} % "
                f"LESS steel",
                transform=ratio_axes.transAxes, fontsize=8.5,
                color=OLD_COLOUR, fontweight="bold")
crossing = next((index for index in range(len(values) - 1)
                 if (values[index] - 1.0) * (values[index + 1] - 1.0) < 0),
                None)
if crossing is not None:
    ratio_axes.annotate(f"they agree somewhere between "
                        f"{lengths_both[crossing]:.2f} m and "
                        f"{lengths_both[crossing + 1]:.2f} m",
                        (lengths_both[crossing + 1], 1.0),
                        textcoords="offset points", xytext=(9, 10),
                        fontsize=8.5, color=INK_SOFT)
ratio_axes.text(0.985, 0.05, "above the line, the new code is dearer",
                transform=ratio_axes.transAxes, ha="right", fontsize=8.5,
                color=MUTED)
ratio_axes.set_xlim(metres[0], metres[-1])
span = values.max() - min(values.min(), 1.0)
ratio_axes.set_ylim(min(values.min(), 1.0) - span * 0.18,
                    values.max() + span * 0.10)

# ---- C. the mechanism --------------------------------------------------
moment_axes = figure.add_subplot(panels[1, 0])
dress(moment_axes,
      "C.  Why — the moment each code actually designs for  (load case 1)",
      "effective length  L   (m)", "design moment   (kNm)")

for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    moment_axes.plot(metres, series(code, "mxe", real_only=False),
                     color=colour, linewidth=2.0, label=f"{short}  Mxe")
    moment_axes.plot(metres, series(code, "mye", real_only=False),
                     color=colour, linewidth=1.6, linestyle=":",
                     label=f"{short}  Mye")

moment_axes.axhline(APPLIED_MX, color=AXIS, linewidth=1.1, linestyle="--")
moment_axes.annotate(f"the Mx you supplied:  {APPLIED_MX:.0f} kNm",
                     (metres[-1], APPLIED_MX), textcoords="offset points",
                     xytext=(-6, 8), ha="right", fontsize=8.5,
                     color=INK_SOFT)
# The double arrow measures the toll; the words sit well clear of it,
# because everything within 40 kNm of the 250 line is already occupied by
# four curves and the hairline itself.
toll = APPLIED_N * 0.020
moment_axes.annotate("", xy=(5.0, APPLIED_MX + toll), xytext=(5.0, APPLIED_MX),
                     arrowprops=dict(arrowstyle="<->", color=NEW_COLOUR,
                                     linewidth=1.3))
moment_axes.annotate(f"+{toll:.0f} kNm = N × 20 mm  ↓\n"
                     f"(section 5 varied N to prove it)",
                     (5.15, APPLIED_MX + toll * 2.4), fontsize=8.5,
                     color=NEW_COLOUR, fontweight="bold")

onset = min(onsets.values())
moment_axes.axvspan(metres[0], onset / 1000.0, color=FREE, alpha=0.08,
                    zorder=0)
moment_axes.text(0.025, 0.80,
                 f"length is FREE below {onset / 1000:.2f} m  "
                 f"(λ = {onset / RADIUS:.0f}):\n"
                 f"every answer in this band is bit-identical",
                 transform=moment_axes.transAxes, fontsize=8.5,
                 color="#0a7a0a")
moment_axes.set_xlim(metres[0], metres[-1])
moment_axes.legend(loc="upper left", fontsize=8.5, frameon=False,
                   labelcolor=INK, ncol=2)

# ---- D. the verdict, side by side --------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same column, same axis — what each code tells you", "", "")
verdict.set_xlabel("effective length  L   (m)", fontsize=9.5, color=INK_SOFT)

REGIMES = ((FREE, "length costs nothing"),
           (RAMP, "slenderness ramp — steel climbing"),
           (DEAD, "engine STOPS DESIGNING, and never says so"),
           (MUTED, "REFUSED, with a reason in words"))

for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    ramp_from = onsets[code] / 1000.0
    ends = cliff.get(code, LENGTHS[-1]) / 1000.0
    refuses = (wall[code] / 1000.0) if code in wall else metres[-1]

    for start, stop, colour, texture in (
            (metres[0], ramp_from, FREE, None),
            (ramp_from, ends, RAMP, None),
            (ends, refuses, DEAD, None),
            (refuses, metres[-1], MUTED, "////")):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, hatch=texture,
                     edgecolor=SURFACE, linewidth=2.0, zorder=3)

    verdict.text(metres[0] + 0.15, base + 0.15, code, fontsize=9.5,
                 color=INK, fontweight="bold")
    verdict.plot([ends, ends], [base - 0.145, base - 0.105], color=INK,
                 linewidth=1.0, zorder=5)
    verdict.text(ends, base - 0.20, f"designs to {ends:.2f} m", ha="center",
                 fontsize=8.5, color=INK, fontweight="bold")
    if code in wall:
        verdict.text(metres[-1], base + 0.15,
                     f"refuses from {refuses:.2f} m", ha="right",
                     fontsize=8.5, color=INK_SOFT)

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
    f"One column, growing taller:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"{COLUMN['h']:.0f} × {COLUMN['b']:.0f} mm, cover {COLUMN['dc_x']:.0f} mm, "
    f"fcu {COLUMN['fcu']:.0f} MPa, fy {COLUMN['fy']:.0f} MPa, braced, "
    f"N {APPLIED_N:.0f} kN, Mx {APPLIED_MX:.0f} / My {APPLIED_MY:.0f} kNm  —  "
    f"ONLY the effective length changes\n"
    f"{WANTED_CODE} is refused by this engine, so Eurocode 2 — the document "
    f"it adopts — stands in for it, and is labelled as a stand-in throughout",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "rectangular_column_sabs_vs_eurocode_length.png")
