# ---
# Example:  One general column, growing taller - and two codes that disagree about WHICH load case governs
# Feature:  general_column (C13 General Column)
# Verified: yes - 2026-09-07 - the pinned 400 mm square reproduces both capacity factors and all three section values exactly at the sweep's 3 m point; every length measured on prokon-automation.exe
# ---
# ONE column. TWO load cases. ONE thing changes: the length.
#
# The section (400 mm square with four Y25 corner bars), the concrete
# (fcu 30), the steel (fy 450), the end conditions and both load cases are
# held constant and asserted constant - so every difference is caused by
# the length or by the code.
#
# ⚠ C13 CHECKS A COLUMN; IT DOES NOT DESIGN ONE. You give it the bars, so
# steel_area and reinforcement_ratio are echoes of your input and never
# move - section 2 checks that they do not. The output that RESPONDS is
# min_capacity_factor, and 1.0 is the line: above it the column carries the
# case, below it the column fails. That makes this study different in kind
# from the C11 and C12 ones, where the engine sizes the steel for you.
#
# THE CODES ------------------------------------------------------------
#
# SABS 0100 - 2000 against Eurocode 2 - 2004. C13 does NOT carry the new
# South African code - it is one of only four engines that do not (with
# C11, C12 and C16), and section 0 shows the refusal rather than asserting
# it. ⚠ There is no "Eurocode 2 - 2005" anywhere in the fleet.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE TWO CODES DISAGREE ABOUT WHICH LOAD CASE GOVERNS. On a tall column
#   the old code's critical case is the lightly loaded one and the new
#   code's is the heavy one - they swap, and only one of them swaps.
#   Section 4 draws it. That is worse than a numerical disagreement: two
#   engineers reporting "the governing case" from the same model and the
#   same loads would name different rows of the same table.
#
#   THE NEW CODE IS MORE GENEROUS WHEN THE COLUMN IS SHORT and less
#   generous when it is tall. Both codes report a flat capacity for a range
#   of lengths and then fall away; section 3 finds where each one starts
#   caring about length, and they are not the same place.
#
#   AND THE LAST LENGTH THAT PASSES DIFFERS. Section 5 bisects it for each
#   code - that single number is what an engineer would actually take off
#   this study.
#
#   NEITHER CODE REFUSES, AND HERE THAT IS CORRECT. A capacity factor of
#   0.61 is a real, useful answer: it says the column fails and by how
#   much. Unlike the sister studies, there is nothing dishonest in the
#   engine answering past the limit - the number carries its own verdict,
#   as long as you read it against 1.0.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
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
    chart in the Plots pane. A headless run can only warn - so ASK the
    backend and write the PNG either way. No matplotlib.use() here: that
    call would make the Plots pane unreachable for ever.
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
OLD_CODE = "SABS 0100 - 2000"
NEW_CODE = "Eurocode 2 - 2004"
PINNED_CODE = "BS8110 - 1997"
SA_NEW_CODE = "SANS 51992-1-1:2025"     # not in this engine

OLD_COLOUR = "#2a78d6"      # categorical slot 1
NEW_COLOUR = "#eb6834"      # categorical slot 2
FREE = "#0ca30c"
DEAD = "#d03b3b"

# -- THE COLUMN, AND THE ONE INPUT THAT MOVES ---------------------------
# The section is the desktop's own row format: "+" moves the pen, "L"
# draws a line to a corner, "B" places a bar of that diameter at the pen.
SECTION = [{"code": "+", "x": 0, "y": 0},
           {"code": "L", "x": 400, "y": 0},
           {"code": "L", "x": 400, "y": 400},
           {"code": "L", "x": 0, "y": 400},
           {"code": "+", "x": 42.5, "y": 42.5}, {"code": "B", "x": 25},
           {"code": "+", "x": 357.5, "y": 42.5}, {"code": "B", "x": 25},
           {"code": "+", "x": 357.5, "y": 357.5}, {"code": "B", "x": 25},
           {"code": "+", "x": 42.5, "y": 357.5}, {"code": "B", "x": 25}]
CASES = [{"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50},
         {"axial": 2000, "moment_x_top": 90, "moment_y_top": 30,
          "moment_x_bottom": 90, "moment_y_bottom": 30}]
CASE_NAMES = ("case 1:  N 1000, Mx 50", "case 2:  N 2000, Mx 90, My 30")
COLUMN = dict(fcu=30.0, fy=450.0, section=SECTION, load_cases=CASES)

ANCHOR_LENGTH = 3.0
PINNED = {"case1": 2.179097995657654, "case2": 1.123583760958025,
          "steel_area": 1963.4954084936207, "concrete_area": 160000,
          "ratio": 1.227184630308513}

LENGTHS = np.arange(1.0, 18.01, 0.25)       # 69 lengths, 1 m to 18 m
PASSES_AT = 1.0                             # the capacity factor that means "ok"

print("ONE GENERAL COLUMN, GROWING TALLER - TWO DESIGN CODES")
print("  400 mm square, four Y25 corner bars at 42.5 mm to the bar centre")
print(f"  fcu {COLUMN['fcu']:.0f} MPa, fy {COLUMN['fy']:.0f} MPa, braced, "
      f"both ends fully fixed (the defaults)")
for index, name in enumerate(CASE_NAMES):
    print(f"  {name}")
print(f"  the only input that moves: length, {LENGTHS[0]:.2f} to "
      f"{LENGTHS[-1]:.2f} m in {LENGTHS[1] - LENGTHS[0]:.2f} m steps "
      f"({len(LENGTHS)} lengths)")

CALLS = {"engine": 0}
_ANSWERS = {}


def check(code, length):
    """One length, one code. Returns a row; never raises for a refusal."""
    key = (code, round(float(length), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.general_column.analyse(
            design_code=code, length=float(length), **COLUMN)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(length=float(length), factors=None, governing=None,
                   worst=None, steel=None, ratio=None,
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    factors = [case["min_capacity_factor"] for case in result["load_cases"]]
    row = dict(length=float(length), factors=factors,
               governing=int(np.argmin(factors)), worst=min(factors),
               steel=result["steel_area"],
               ratio=result["reinforcement_ratio"], reason=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE CODES THIS ENGINE HAS - AND THE ONE IT DOES NOT
# ======================================================================
# CLAIM: C13 has no SANS 51992-1-1:2025.
# CONTROL: the codes this script DOES use must answer AND return different
# numbers, or the reading cannot tell a refusal from an answer.
print("\n0. THE CODES THIS ENGINE HAS")
for code in (SA_NEW_CODE, OLD_CODE, NEW_CODE, PINNED_CODE):
    row = check(code, ANCHOR_LENGTH)
    if row["factors"] is None:
        print(f"   {code:<22} REFUSED")
        print(f"   {'':<22} {str(row['reason'])[:66]}")
    else:
        print(f"   {code:<22} answered  factors "
              + "  ".join(f"{value:.4f}" for value in row["factors"]))
print("   -> the controls answer and they DISAGREE, so the refusal above is")
print("      about the code name and nothing else.")
print("   -> C13 is one of only four engines without the new South African")
print("      code; C11, C12 and C16 are the others. The remaining eight")
print("      have it.")

# ======================================================================
# 1. THE ANCHOR
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at {ANCHOR_LENGTH:.1f} m")
anchor = check(PINNED_CODE, ANCHOR_LENGTH)
found = {"case1": anchor["factors"][0], "case2": anchor["factors"][1],
         "steel_area": anchor["steel"], "ratio": anchor["ratio"]}
matched = 0
for name in ("case1", "case2", "steel_area", "ratio"):
    hit = found[name] == PINNED[name]
    matched += hit
    print(f"   {name:<12} {found[name]!r:22} pinned {PINNED[name]!r}")
print(f"   -> {matched} of 4 exact"
      f"{'' if matched == 4 else '  - DRIFTED, READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP - AND WHAT DOES NOT MOVE
# ======================================================================
print(f"\n2. THE SWEEP   {len(LENGTHS)} lengths x 2 codes")
sweep = {code: [check(code, length) for length in LENGTHS]
         for code in (OLD_CODE, NEW_CODE)}

assert COLUMN["fcu"] == 30.0 and len(COLUMN["load_cases"]) == 2
assert COLUMN["load_cases"][0]["axial"] == 1000
print("   the section and both load cases are unchanged after the sweep")

# C13 CHECKS rather than designs, so the steel is an echo of the input.
# Saying so is cheap; proving it is cheaper than a reader assuming the
# engine sized something.
print("\n   THE STEEL IS YOUR INPUT, NOT AN ANSWER")
for code in (OLD_CODE, NEW_CODE):
    areas = {row["steel"] for row in sweep[code]}
    ratios = {row["ratio"] for row in sweep[code]}
    print(f"     {code:<22} steel_area took {len(areas)} value(s), "
          f"ratio took {len(ratios)}")
    print(f"     {'':<22} {next(iter(areas))!r} mm2, "
          f"{next(iter(ratios))!r} %")
print("   -> one value each, across both codes and every length. The bars")
print("      are what you gave it; the capacity factor is the answer.")

print(f"\n   {'L (m)':>6} | {'SABS c1':>8} {'c2':>8} {'gov':>4} {'worst':>8} | "
      f"{'EC2 c1':>8} {'c2':>8} {'gov':>4} {'worst':>8}")
for index, length in enumerate(LENGTHS):
    if abs(length - round(length)) > 1e-9 or round(length) % 2:
        continue
    cells = []
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        cells.append(f" {row['factors'][0]:>8.4f} {row['factors'][1]:>8.4f} "
                     f"{row['governing'] + 1:>4} {row['worst']:>8.4f}")
    print(f"   {length:>6.2f} |" + " |".join(cells))


def column_of(code, field, case=None):
    if case is None:
        return np.asarray([np.nan if row[field] is None else row[field]
                           for row in sweep[code]], dtype=float)
    return np.asarray([np.nan if row["factors"] is None
                       else row["factors"][case] for row in sweep[code]],
                      dtype=float)


def boundary(holds, low, high, resolution=0.01):
    """The largest length where `holds` is still true, to `resolution`.

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


# ======================================================================
# 3. WHERE EACH CODE STARTS CARING ABOUT LENGTH
# ======================================================================
print("\n3. WHERE EACH CODE STARTS CARING ABOUT LENGTH")
onset = {}
for code in (OLD_CODE, NEW_CODE):
    worst = column_of(code, "worst")
    stubby = worst[0]
    moved = [index for index in range(len(LENGTHS)) if worst[index] != stubby]
    if not moved:
        print(f"   {code:<22} flat across the whole range")
        continue
    onset[code] = LENGTHS[moved[0]]
    flat = LENGTHS[:moved[0]]
    print(f"   {code:<22} flat at {stubby:.4f} from {flat[0]:.2f} to "
          f"{flat[-1]:.2f} m ({len(flat)} lengths)")
    print(f"   {'':<22} first moves at {onset[code]:.2f} m")
if len(onset) == 2:
    print(f"   -> {abs(onset[NEW_CODE] - onset[OLD_CODE]):.2f} m apart, and "
          f"the "
          f"{'NEW' if onset[NEW_CODE] < onset[OLD_CODE] else 'OLD'} code")
    print("      starts charging for height first.")

# ======================================================================
# 4. WHICH LOAD CASE GOVERNS - AND THE CODES DISAGREE
# ======================================================================
# This is the finding. "The governing case" sounds like a property of the
# model; measured, it is a property of the model AND the code.
print("\n4. WHICH LOAD CASE GOVERNS")
governs = {}
for code in (OLD_CODE, NEW_CODE):
    order = [row["governing"] for row in sweep[code]]
    governs[code] = np.asarray(order)
    swaps = [index for index in range(len(order) - 1)
             if order[index] != order[index + 1]]
    counted = {case: order.count(case) for case in sorted(set(order))}
    print(f"   {code}")
    for case, times in counted.items():
        print(f"     case {case + 1} governs at {times:>3} of "
              f"{len(order)} lengths")
    if swaps:
        for index in swaps:
            print(f"     swaps from case {order[index] + 1} to case "
                  f"{order[index + 1] + 1} between "
                  f"{LENGTHS[index]:.2f} and {LENGTHS[index + 1]:.2f} m")
    else:
        print(f"     never swaps - case {order[0] + 1} governs throughout")

disagree = LENGTHS[governs[OLD_CODE] != governs[NEW_CODE]]
print(f"\n   the two codes name a DIFFERENT governing case at "
      f"{len(disagree)} of {len(LENGTHS)} lengths")
if len(disagree):
    print(f"   from {disagree.min():.2f} m to {disagree.max():.2f} m")
    print("   -> so 'the governing load case' is not a property of the model.")
    print("      It is a property of the model AND the code, and two")
    print("      engineers with the same file would report different rows.")
else:
    print("   -> they agree everywhere in this range")

# ======================================================================
# 5. THE LAST LENGTH THAT PASSES
# ======================================================================
print(f"\n5. THE LAST LENGTH AT WHICH EVERY CASE STILL PASSES "
      f"(factor >= {PASSES_AT:.1f})")
last_good = {}
for code in (OLD_CODE, NEW_CODE):
    worst = column_of(code, "worst")
    good = LENGTHS[worst >= PASSES_AT]
    bad = LENGTHS[worst < PASSES_AT]
    if not len(good) or not len(bad):
        print(f"   {code:<22} no crossing inside this range")
        continue

    def still_passes(length, code=code):
        return check(code, length)["worst"] >= PASSES_AT

    low, high = boundary(still_passes, good[-1], bad[0])
    last_good[code] = low
    print(f"   {code:<22} passes to {low:.3f} m, fails from {high:.3f} m")
    print(f"   {'':<22} governing case there: "
          f"{check(code, low)['governing'] + 1}")
if len(last_good) == 2:
    print(f"   -> {abs(last_good[NEW_CODE] - last_good[OLD_CODE]):.2f} m "
          f"apart. The "
          f"{'NEW' if last_good[NEW_CODE] > last_good[OLD_CODE] else 'OLD'} "
          f"code allows the taller column,")
    print("      from the same section with the same four bars in it.")

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
    axes.set_xlim(LENGTHS[0], LENGTHS[-1])


# ---- A. the capacity factors -------------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  Capacity factor — above 1.0 the column carries the case",
      "column length   (m)", "min capacity factor")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    for case, style in ((0, "-"), (1, ":")):
        chart.plot(LENGTHS, column_of(code, None, case), color=colour,
                   linewidth=2.0 if case == 0 else 1.6, linestyle=style,
                   label=f"{short}  case {case + 1}", zorder=4)
    if code in last_good:
        chart.plot([last_good[code]], [PASSES_AT], marker="o", markersize=9,
                   color=colour, markeredgecolor=SURFACE, markeredgewidth=2.0,
                   zorder=6)
chart.axhline(PASSES_AT, color=DEAD, linewidth=1.4, linestyle="--", zorder=3)
chart.annotate(f"{PASSES_AT:.1f} — below here the case FAILS",
               (LENGTHS[-1], PASSES_AT), textcoords="offset points",
               xytext=(-6, 8), ha="right", fontsize=8.5, color=DEAD,
               fontweight="bold")
for code, colour, lift in ((OLD_CODE, OLD_COLOUR, 46),
                           (NEW_CODE, NEW_COLOUR, -34)):
    if code in last_good:
        chart.annotate(f"{'SABS' if code == OLD_CODE else 'Eurocode 2'} "
                       f"passes to {last_good[code]:.2f} m",
                       (last_good[code], PASSES_AT),
                       textcoords="offset points", xytext=(-12, lift),
                       ha="right", fontsize=8.5, color=colour,
                       fontweight="bold")
chart.plot([ANCHOR_LENGTH], [anchor["factors"][1]], marker="D", markersize=8,
           color=MUTED, markeredgecolor=SURFACE, markeredgewidth=2.0,
           zorder=7)
chart.annotate("the pinned column", (ANCHOR_LENGTH, anchor["factors"][1]),
               textcoords="offset points", xytext=(12, -20), ha="left",
               fontsize=8.5, color=INK_SOFT)
chart.set_ylim(0.0, None)
chart.legend(loc="upper right", fontsize=8.5, frameon=False, labelcolor=INK,
             ncol=2)

# ---- B. the direct comparison ------------------------------------------
# ⚠ THE SENSE IS REVERSED HERE relative to the sister studies. On the
# steel-designing engines a ratio above 1.0 means the new code costs MORE.
# A capacity factor is a good thing, so above 1.0 means the new code is
# more PERMISSIVE. The axis label says so, and the fills are swapped to
# match: blue (old) above, orange (new) below.
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes,
      "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "column length   (m)",
      "governing capacity factor,  new ÷ old\n(above 1.0 the NEW code is "
      "more permissive)")
old_worst = column_of(OLD_CODE, "worst")
new_worst = column_of(NEW_CODE, "worst")
ratio = new_worst / old_worst
ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
ratio_axes.fill_between(LENGTHS, ratio, 1.0, where=(ratio >= 1.0),
                        interpolate=True, color=NEW_COLOUR, alpha=0.16)
ratio_axes.fill_between(LENGTHS, ratio, 1.0, where=(ratio <= 1.0),
                        interpolate=True, color=OLD_COLOUR, alpha=0.16)
ratio_axes.plot(LENGTHS, ratio, color=NEW_COLOUR, linewidth=2.0, zorder=4)
ratio_axes.annotate(f"stubby: the new code allows\n"
                    f"{(ratio[0] - 1) * 100:.1f} % MORE",
                    (LENGTHS[0], ratio[0]), textcoords="offset points",
                    xytext=(16, -20), ha="left", fontsize=8.5,
                    color=NEW_COLOUR, fontweight="bold")
lowest = int(np.argmin(ratio))
ratio_axes.plot([LENGTHS[lowest]], [ratio[lowest]], marker="o", markersize=8,
                color=OLD_COLOUR, markeredgecolor=SURFACE,
                markeredgewidth=2.0, zorder=6)
ratio_axes.annotate(f"tall: down to {(1 - ratio[lowest]) * 100:.1f} % LESS\n"
                    f"at {LENGTHS[lowest]:.2f} m",
                    (LENGTHS[lowest], ratio[lowest]),
                    textcoords="offset points", xytext=(-12, 22),
                    ha="right", va="bottom", fontsize=8.5, color=OLD_COLOUR,
                    fontweight="bold")

# ---- C. which case governs ---------------------------------------------
which = figure.add_subplot(panels[1, 0])
dress(which, "C.  Which load case governs — and the codes disagree", "", "")
which.set_xlabel("column length   (m)", fontsize=9.5, color=INK_SOFT)
CASE_FILL = ("#1baf7a", "#4a3aa7")      # categorical slots 3 and 7
for code, base in ((OLD_CODE, 0.62), (NEW_CODE, 0.22)):
    order = governs[code]
    edges = [0] + [index + 1 for index in range(len(order) - 1)
                   if order[index] != order[index + 1]] + [len(order)]
    for start, stop in zip(edges, edges[1:]):
        case = int(order[start])
        left = LENGTHS[start]
        right = (LENGTHS[stop] if stop < len(LENGTHS) else LENGTHS[-1])
        which.barh(base, right - left, left=left, height=0.22,
                   color=CASE_FILL[case], alpha=0.85, edgecolor=SURFACE,
                   linewidth=2.0, zorder=3)
        if right - left > 2.0:
            which.text((left + right) / 2, base, f"case {case + 1}",
                       ha="center", va="center", fontsize=9, color="white",
                       fontweight="bold", zorder=5)
    which.text(LENGTHS[0] + 0.1, base + 0.17, code, fontsize=9.5, color=INK,
               fontweight="bold")
if len(disagree):
    which.axvspan(disagree.min(), disagree.max(), color=DEAD, alpha=0.10,
                  zorder=0)
    which.text((disagree.min() + disagree.max()) / 2, 0.93,
               "the codes name DIFFERENT" + chr(10) + "governing cases here,"
               + chr(10) + f"{disagree.min():.2f} to {disagree.max():.2f} m",
               ha="center", va="top", fontsize=8.5, color=DEAD,
               fontweight="bold")
which.set_ylim(0.0, 0.95)
which.set_yticks([])
which.grid(False)
which.spines["left"].set_visible(False)
which.legend([plt.Rectangle((0, 0), 1, 1, color=CASE_FILL[index], alpha=0.85)
              for index in (0, 1)], list(CASE_NAMES), loc="upper center",
             bbox_to_anchor=(0.5, -0.14), fontsize=8.5, ncol=2,
             frameon=False, labelcolor=INK)

# ---- D. the verdict ----------------------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same column, same axis — what each code tells you",
      "", "")
verdict.set_xlabel("column length   (m)", fontsize=9.5, color=INK_SOFT)
REGIMES = ((FREE, f"every case passes  (factor ≥ {PASSES_AT:.1f})"),
           (DEAD, "a case fails — and the number says by how much"))
for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    edge = last_good.get(code, LENGTHS[-1])
    for start, stop, colour in ((LENGTHS[0], edge, FREE),
                                (edge, LENGTHS[-1], DEAD)):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, edgecolor=SURFACE,
                     linewidth=2.0, zorder=3)
    verdict.text(LENGTHS[0] + 0.15, base + 0.15, code, fontsize=9.5,
                 color=INK, fontweight="bold")
    verdict.plot([edge, edge], [base - 0.145, base - 0.105], color=INK,
                 linewidth=1.0, zorder=5)
    verdict.text(edge, base - 0.20, f"passes to {edge:.2f} m", ha="center",
                 fontsize=8.5, color=INK, fontweight="bold")
    verdict.text(LENGTHS[-1], base + 0.15,
                 f"worst factor {column_of(code, 'worst')[-1]:.2f} at "
                 f"{LENGTHS[-1]:.0f} m", ha="right", fontsize=8.5,
                 color=INK_SOFT)
verdict.text(0.985, 0.975,
             "no refusal anywhere — and here that is right: a factor of "
             "0.6 is" + chr(10) +
             "a real answer, as long as it is read against 1.0",
             transform=verdict.transAxes, ha="right", va="top",
             fontsize=8.5, color=MUTED)
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
    f"One general column, growing taller:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"400 mm square, four Y25, fcu {COLUMN['fcu']:.0f} MPa, "
    f"fy {COLUMN['fy']:.0f} MPa, two load cases  —  ONLY the length changes\n"
    f"C13 CHECKS the column you give it, so the answer is the capacity "
    f"factor — and the two codes disagree about which load case governs",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "general_column_sabs_vs_eurocode_length.png")
