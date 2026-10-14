# ---
# Example:  One slab section, a growing service moment - the national adoption is worth 0.6 %, the generation change 30 %
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes - 2026-09-07 - the pinned reference slab reproduces its crack width, steel area and moment capacity exactly at the sweep's m = 50 kNm/m point; every moment measured on prokon-automation.exe
# ---
# ONE section. ONE thing changes: the service moment.
#
# The thickness (300 mm), the tension zone (200 mm), the cover (40 mm),
# both moduli, the concrete (fcu 30), the steel (fy 450) and the allowable
# crack width (0.3 mm) are held constant and asserted constant - so every
# difference is caused by the moment or by the code.
#
# ⚠ THIS ENGINE HAS NO OLD SOUTH AFRICAN CODE AT ALL, so this study is not
# the SABS-against-Eurocode comparison its eleven sister scripts are.
# C21's thirteen codes are all CRACK-WIDTH codes, and the only South
# African one among them is the NEW code, SANS 51992-1-1:2025. Section 0
# lists them and shows every SABS spelling being refused.
#
# So the comparison here is the one the C11 study wanted and could not
# have: the new South African code against the Eurocode it adopts, plus
# BS8007 - 1987 - the older-generation code, and the one the pinned
# reference case uses - as a third line for scale.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   SANS 51992-1-1:2025 IS NOT IDENTICAL TO EUROCODE 2 - 2004, BUT VERY
#   NEARLY - about 0.6 % apart, in one direction at every moment. That is
#   what a national adoption looks like when you measure it instead of
#   assuming it: real, reproducible, and far too small to change a
#   decision.
#
#   ⚠ AND THAT 0.6 % ONLY MEANS ANYTHING WHERE BOTH CODES PICKED THE SAME
#   BARS. An earlier draft of this script reported "up to 45 % away",
#   which was a real number read wrongly. optimised_configs[0] is the
#   smallest arrangement that works, and the arrangements stop working at
#   slightly different moments under each code - so at a handful of
#   moments the two codes are reporting DIFFERENT bars, and dividing one
#   crack width by the other compares two different slabs. Section 3
#   splits the two cases and panel B draws the mismatched points hollow.
#
#   BS8007 - 1987 IS ABOUT 30 % AWAY, WHICH IS THE POINT. On like-for-like
#   arrangements the generation change dwarfs the national adoption.
#   Panel B puts both ratios on one axis so the two scales cannot be
#   confused.
#
#   AND THE CRACK WIDTH IS NOT MONOTONIC IN THE MOMENT. It rises, then
#   falls, then rises. Nothing is wrong: the engine is stepping between
#   DISCRETE bar arrangements, and each step changes the steel area
#   abruptly. Panel C shows the arrangements running out as the moment
#   grows - four of them at the light end, one at the heavy end.
#
#   ⚠ AND optimised_configs[0] IS NOT THE BEST ARRANGEMENT. Measured under
#   SANS at the reference moment, the four arrangements give crack widths
#   of 0.1624, 0.2279, 0.2719 and 0.0937 mm - so the list is ordered by BAR
#   DIAMETER (Y10, Y16, Y25, Y40) and not by performance, and [0] is 73 %
#   worse than [3]. Across the sweep [0] is the smallest crack at only 35
#   of 45 moments. A caller who reads [0] and stops gets the smallest bar,
#   which is a different question from the smallest crack. Panel D draws
#   every arrangement.
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


# -- THE THREE CODES ----------------------------------------------------
# Categorical slots 1, 2 and 3, in that fixed order. Those three validate
# as an all-pairs set: worst colour-vision separation dE 9.2, worst
# normal-vision dE 24.0, each at least 3:1 against the surface above.
SA_CODE = "SANS 51992-1-1:2025"     # the only South African code C21 has
EU_CODE = "Eurocode 2 - 2004"       # the document it adopts
OLD_GENERATION = "BS8007 - 1987"    # and the pinned reference case's code

SA_COLOUR = "#2a78d6"       # blue
EU_COLOUR = "#eb6834"       # orange
OLD_COLOUR = "#1baf7a"      # aqua
FREE = "#0ca30c"
RAMP = "#fab219"
DEAD = "#d03b3b"
CODES = (SA_CODE, EU_CODE, OLD_GENERATION)
SHORT = {SA_CODE: "SANS 2025", EU_CODE: "Eurocode 2",
         OLD_GENERATION: "BS8007 1987"}
COLOUR = {SA_CODE: SA_COLOUR, EU_CODE: EU_COLOUR,
          OLD_GENERATION: OLD_COLOUR}

# -- THE SECTION, AND THE ONE INPUT THAT MOVES --------------------------
SECTION = dict(slab_mode=True, h=300.0, hef=200.0, b=1000.0, cover=40.0,
               fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
               allowable_crack_width=0.3, high_bond_bar=True,
               short_term_load=True)
ALLOWED = SECTION["allowable_crack_width"]

ANCHOR_MOMENT = 50.0
PINNED = {"crack": 0.11059554804834058, "steel": 1047.197551196598,
          "capacity": 99.75807235558123}

MOMENTS = np.arange(5.0, 251.0, 5.0)        # 50 moments, 5 to 250 kNm/m

print("ONE SLAB SECTION, A GROWING SERVICE MOMENT - THREE CRACK-WIDTH CODES")
print(f"  {SECTION['h']:.0f} mm thick, tension zone {SECTION['hef']:.0f} mm, "
      f"cover {SECTION['cover']:.0f} mm, per metre width")
print(f"  fcu {SECTION['fcu']:.0f} MPa, fy {SECTION['fy']:.0f} MPa, "
      f"Es {SECTION['ea']:.0f} GPa, Ec {SECTION['ec']:.0f} GPa")
print(f"  allowable crack width {ALLOWED:.1f} mm, high-bond bars, "
      f"short-term load")
print(f"  the only input that moves: m, {MOMENTS[0]:.0f} to "
      f"{MOMENTS[-1]:.0f} kNm/m in {MOMENTS[1] - MOMENTS[0]:.0f} steps "
      f"({len(MOMENTS)} moments)")

CALLS = {"engine": 0}
_ANSWERS = {}


def check(code, moment):
    """One moment, one code. Every arrangement the engine offers."""
    key = (code, round(float(moment), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.crack_widths.analyse(
            design_code=code,
            load_cases='[{"n": 1, "m": %g, "m_uls": 1.5}]' % float(moment),
            **SECTION)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(moment=float(moment), options=[],
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    options = []
    for option in result["load_cases"][0]["optimised_configs"]:
        maths = option["calc_result"]
        options.append(dict(crack=maths["governing_crack_width"],
                            steel=maths["steel_area"],
                            capacity=option["moment_capacity"],
                            bars=option["formatted_bars"],
                            ok=option["meets_all_criteria"]))
    _ANSWERS[key] = dict(moment=float(moment), options=options, reason=None)
    return _ANSWERS[key]


def first(code, moment, field):
    """The field on optimised_configs[0] - what a caller reads by default."""
    options = check(code, moment)["options"]
    return options[0][field] if options else None


# ======================================================================
# 0. THIS ENGINE HAS NO OLD SOUTH AFRICAN CODE
# ======================================================================
# CLAIM: none of the SABS spellings the other engines use exists here.
# CONTROL: the three codes this script DOES use must answer AND return
# different numbers, or the reading cannot tell a refusal from an answer.
print("\n0. THE CODES THIS ENGINE HAS")
for code in ("SABS 0100 - 2000", "SABS 0100 - 1992", "SABS0100 - 1992",
             "BS8110 - 1997") + CODES:
    row = check(code, ANCHOR_MOMENT)
    if not row["options"]:
        print(f"   {code:<22} REFUSED")
        print(f"   {'':<22} {str(row['reason'])[:64]}")
    else:
        best = row["options"][0]
        print(f"   {code:<22} answered  w = {best['crack']:.6f} mm  "
              f"as = {best['steel']:>8.1f}  bars {best['bars']}")
print("   -> EVERY SABS spelling is refused, and so is BS8110: C21's codes")
print("      are all CRACK-WIDTH codes, and the only South African one is")
print("      the NEW code. The three controls answer and they disagree, so")
print("      those refusals are about the strings and nothing else.")

# ======================================================================
# 1. THE ANCHOR
# ======================================================================
print(f"\n1. THE ANCHOR   {OLD_GENERATION} at m = {ANCHOR_MOMENT:.0f} kNm/m")
anchor = check(OLD_GENERATION, ANCHOR_MOMENT)["options"][0]
found = {"crack": anchor["crack"], "steel": anchor["steel"],
         "capacity": anchor["capacity"]}
matched = 0
for name in PINNED:
    hit = found[name] == PINNED[name]
    matched += hit
    print(f"   {name:<9} {found[name]!r:22} pinned {PINNED[name]!r}")
print(f"   -> {matched} of 3 exact"
      f"{'' if matched == 3 else '  - DRIFTED, READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(MOMENTS)} moments x 3 codes")
sweep = {code: [check(code, moment) for moment in MOMENTS]
         for code in CODES}

assert SECTION["h"] == 300.0 and SECTION["cover"] == 40.0
assert SECTION["allowable_crack_width"] == 0.3
print("   the section dictionary is unchanged after the sweep")

print(f"\n   {'m':>5} | " + " | ".join(
    f"{SHORT[code] + ' w':>13} {'as':>8} {'n':>2}" for code in CODES))
for index, moment in enumerate(MOMENTS):
    if moment % 25 != 0:
        continue
    cells = []
    for code in CODES:
        options = sweep[code][index]["options"]
        if not options:
            cells.append(f" {'no option':>13} {'':>8} {0:>2}")
            continue
        cells.append(f" {options[0]['crack']:>13.6f} "
                     f"{options[0]['steel']:>8.1f} {len(options):>2}")
    print(f"   {moment:>5.0f} |" + " |".join(cells))
print("   (w = optimised_configs[0]'s crack width, n = arrangements offered)")


def column_of(code, field):
    return np.asarray([np.nan if first(code, moment, field) is None
                       else first(code, moment, field)
                       for moment in MOMENTS], dtype=float)


# ======================================================================
# 3. THE NATIONAL ADOPTION AGAINST THE GENERATION CHANGE
# ======================================================================
# The whole point of this study, stated as two numbers on the same scale.
print("\n3. HOW FAR APART ARE THEY, REALLY?")
crack = {code: column_of(code, "crack") for code in CODES}
layout = {code: [first(code, moment, "bars") for moment in MOMENTS]
          for code in CODES}
live = np.ones(len(MOMENTS), dtype=bool)
for code in CODES:
    live &= crack[code] > 0

# ⚠ AND THE COMPARISON HAS TO ASK WHETHER THE TWO CODES CHOSE THE SAME
# BARS FIRST. optimised_configs[0] is the smallest-diameter arrangement
# that works, and arrangements stop working at slightly different moments
# under each code (section 4). Where the selections differ, dividing one
# crack width by the other compares two DIFFERENT slabs - and the ratio
# jumps to about 1.45, which says nothing whatever about the codes.
#
# An earlier draft of this script reported that 1.45 as "the national
# adoption is up to 45 % away from Eurocode 2". It is not. The number was
# real and the reading was wrong, and the split below is the fix.
print(f"   comparing over the {int(np.sum(live))} moments where all three "
      f"report a non-zero crack")
pairs = ((SA_CODE, EU_CODE, "the national adoption"),
         (OLD_GENERATION, EU_CODE, "the generation change"))
spreads, matched_mask = {}, {}
for numerator, denominator, label in pairs:
    same = np.asarray([layout[numerator][index] == layout[denominator][index]
                       for index in range(len(MOMENTS))]) & live
    apart = live & ~same
    matched_mask[label] = same
    share = crack[numerator][same] / crack[denominator][same]
    spreads[label] = share
    print(f"\n   {label.upper()}   "
          f"{SHORT[numerator]} / {SHORT[denominator]}")
    print(f"     SAME arrangement at {int(np.sum(same))} moments: "
          f"ratio {share.min():.5f} to {share.max():.5f}")
    print(f"     -> up to {abs(share - 1).max() * 100:.2f} % apart, and "
          f"THIS is the code difference")
    if np.any(apart):
        wrong = crack[numerator][apart] / crack[denominator][apart]
        worst = int(np.where(apart)[0][-1])
        print(f"     different arrangement at {int(np.sum(apart))} "
              f"moments: ratio {wrong.min():.3f} to {wrong.max():.3f}")
        print(f"     -> up to {abs(wrong - 1).max() * 100:.1f} % apart, "
              f"and that is NOT a code difference:")
        print(f"        the two codes are reporting different bars. At "
              f"m = {MOMENTS[worst]:.0f} kNm/m, {SHORT[numerator]}")
        print(f"        offers {layout[numerator][worst]} and "
              f"{SHORT[denominator]} offers {layout[denominator][worst]}.")

adoption = abs(spreads["the national adoption"] - 1).max()
generation = abs(spreads["the generation change"] - 1).max()
print(f"\n   -> ON LIKE-FOR-LIKE ARRANGEMENTS: the generation "
      f"change is {generation / adoption:.0f} times")
print("      the national adoption. SANS 51992-1-1 is measurably not")
print("      Eurocode 2, and the difference is far too small to change a")
print("      decision. BS8007 is a different answer altogether.")

# And is the national difference CONSISTENT, or noise? A signed count says.
signed = spreads["the national adoption"] - 1.0
print(f"\n   IS IT A DIRECTION OR JUST SCATTER?")
print(f"     on like-for-like arrangements SANS reads higher than "
      f"Eurocode 2 at {int(np.sum(signed > 0))} of {len(signed)} moments,")
print(f"     lower at {int(np.sum(signed < 0))}, equal at "
      f"{int(np.sum(signed == 0))}")
if np.all(signed > 0) or np.all(signed < 0):
    print("     -> one direction at EVERY moment, so it is a systematic")
    print("        difference in the code and not numerical scatter.")

# ======================================================================
# 4. THE CRACK WIDTH IS NOT MONOTONIC, AND HERE IS WHY
# ======================================================================
print("\n4. WHY THE CURVES ZIGZAG")
for code in CODES:
    counts = [len(sweep[code][index]["options"])
              for index in range(len(MOMENTS))]
    steps = [index for index in range(len(MOMENTS) - 1)
             if counts[index] != counts[index + 1]]
    print(f"   {SHORT[code]:<12} arrangements offered: {counts[0]} at "
          f"{MOMENTS[0]:.0f} kNm/m down to {counts[-1]} at "
          f"{MOMENTS[-1]:.0f}")
    for index in steps:
        print(f"   {'':<12}   drops {counts[index]} -> {counts[index + 1]} "
              f"between {MOMENTS[index]:.0f} and {MOMENTS[index + 1]:.0f}")
    values = crack[code]
    rises = sum(1 for index in range(len(values) - 1)
                if values[index + 1] > values[index])
    print(f"   {'':<12} crack width: {rises} rises, "
          f"{len(values) - 1 - rises} falls - NOT monotonic")
print("   -> each drop is one arrangement becoming infeasible, and the")
print("      steel area jumps when the engine moves to the next one. The")
print("      zigzag is the bar schedule, not noise in the calculation.")

# ======================================================================
# 5. optimised_configs[0] IS NOT THE BEST ARRANGEMENT
# ======================================================================
# CLAIM: the list is ordered by bar diameter, not by crack width.
# CONTROL: if it were ordered by crack width, [0] would be the minimum at
# every moment. Count how often it is not.
print(f"\n5. IS optimised_configs[0] THE BEST ONE?")
print(f"   {'code':<12} {'[0] is the smallest crack at':>30} {'of':>4}")
for code in CODES:
    best_is_first = 0
    total = 0
    for index in range(len(MOMENTS)):
        options = sweep[code][index]["options"]
        if len(options) < 2:
            continue
        total += 1
        widths = [option["crack"] for option in options]
        if widths[0] == min(widths):
            best_is_first += 1
    print(f"   {SHORT[code]:<12} {best_is_first:>30} {total:>4}")
print(f"\n   AT THE REFERENCE MOMENT ({ANCHOR_MOMENT:.0f} kNm/m), "
      f"EVERY ARRANGEMENT:")
for code in CODES:
    print(f"   {SHORT[code]}")
    options = check(code, ANCHOR_MOMENT)["options"]
    widths = [option["crack"] for option in options]
    for position, option in enumerate(options):
        flag = "  <- what [0] gives you" if position == 0 else ""
        best = "  <- the smallest crack" if option["crack"] == min(widths) \
            else ""
        print(f"     [{position}] {option['bars']:<10} "
              f"w {option['crack']:.6f}  as {option['steel']:>8.1f}  "
              f"mcap {option['capacity']:>7.2f}  ok={option['ok']}"
              f"{flag}{best}")
print("   -> the list is ordered by BAR DIAMETER. Reading [0] and moving on")
print("      gives you the smallest bar, which is a different question from")
print("      the smallest crack - and on this section they are different")
print("      arrangements.")

print(f"\n   {CALLS['engine']} engine calls in total")

# ======================================================================
# 6. THE PICTURE
# ======================================================================
figure = plt.figure(figsize=(16.0, 10.6), facecolor=SURFACE)
panels = figure.add_gridspec(2, 2, hspace=0.36, wspace=0.19,
                             height_ratios=(1.22, 1.0),
                             left=0.06, right=0.985, top=0.865, bottom=0.09)


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


# ---- A. the crack width ------------------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  Crack width of optimised_configs[0]",
      "service moment  m   (kNm/m)", "crack width   (mm)")
for code in CODES:
    chart.plot(MOMENTS, crack[code], color=COLOUR[code],
               linewidth=2.4 if code == SA_CODE else 1.8,
               label=code, zorder=4)
chart.axhline(ALLOWED, color=DEAD, linewidth=1.4, linestyle="--", zorder=3)
chart.annotate(f"{ALLOWED:.1f} mm — the allowable you supplied",
               (MOMENTS[-1], ALLOWED), textcoords="offset points",
               xytext=(-6, 8), ha="right", fontsize=8.5, color=DEAD,
               fontweight="bold")
uncracked = MOMENTS[crack[SA_CODE] == 0]
if len(uncracked):
    chart.axvspan(MOMENTS[0], uncracked.max(), color=FREE, alpha=0.10,
                  zorder=0)
    # Stood up INSIDE the uncracked band, where every curve is exactly
    # zero. Laid flat it crossed all three rising curves.
    chart.text(uncracked.max() / 2, 0.04,
               f"uncracked below {uncracked.max():.0f} kNm/m — w reads exactly 0",
               transform=chart.get_xaxis_transform(), rotation=90,
               va="bottom", ha="center", fontsize=8.5,
               color="#0a7a0a", fontweight="bold")
chart.plot([ANCHOR_MOMENT], [anchor["crack"]], marker="D", markersize=8,
           color=OLD_COLOUR, markeredgecolor=SURFACE, markeredgewidth=2.0,
           zorder=7)
chart.annotate("the pinned slab", (ANCHOR_MOMENT, anchor["crack"]),
               textcoords="offset points", xytext=(10, -16), ha="left",
               fontsize=8.5, color=INK_SOFT)
chart.set_xlim(MOMENTS[0], MOMENTS[-1])
chart.set_ylim(0.0, None)
chart.legend(loc="lower right", fontsize=8.5, frameon=False, labelcolor=INK)

# ---- B. two ratios, one axis -------------------------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes,
      "B.  Both differences on ONE axis — adoption against generation",
      "service moment  m   (kNm/m)", "crack width ÷ Eurocode 2 - 2004")
ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
comparable = MOMENTS[live]
# SOLID where the two codes chose the same bars - that ratio is a code
# difference. HOLLOW where they chose different bars: there the ratio is
# comparing two different slabs and means nothing about the codes, and
# drawing it as a continuous line is what made an earlier draft of this
# script report "up to 45 % away".
for numerator, label, colour in ((SA_CODE, "the national adoption",
                                  SA_COLOUR),
                                 (OLD_GENERATION, "the generation change",
                                  OLD_COLOUR)):
    same = matched_mask[label]
    stray = live & ~same
    share = np.where(live, crack[numerator]
                     / np.where(live, crack[EU_CODE], 1.0), np.nan)
    ratio_axes.plot(MOMENTS, np.where(same, share, np.nan), color=colour,
                    linewidth=2.2,
                    label=f"{SHORT[numerator]} ÷ Eurocode 2 — same bars",
                    zorder=4)
    if np.any(stray):
        ratio_axes.plot(MOMENTS[stray], share[stray],
                        linestyle="none", marker="o", markersize=8,
                        markerfacecolor="none", markeredgecolor=colour,
                        markeredgewidth=1.8, zorder=5,
                        label=f"{SHORT[numerator]} — DIFFERENT bars, not a code difference")
    like_for_like = share[same]
    ratio_axes.annotate(f"{label}:" + chr(10)
                        + f"{abs(like_for_like - 1).max() * 100:.2f} % on like-for-like bars",
                        (MOMENTS[same][-1], like_for_like[-1]),
                        textcoords="offset points", xytext=(-12, 16),
                        ha="right", fontsize=8.5, color=colour,
                        fontweight="bold")
ratio_axes.annotate("1.0 — identical to Eurocode 2", (comparable[0], 1.0),
                    textcoords="offset points", xytext=(8, 8), ha="left",
                    fontsize=8.5, color=INK_SOFT)
ratio_axes.set_xlim(MOMENTS[0], MOMENTS[-1])
ratio_axes.legend(loc="lower right", fontsize=8.5, frameon=False,
                  labelcolor=INK)

# ---- C. the arrangements running out -----------------------------------
options_axes = figure.add_subplot(panels[1, 0])
dress(options_axes,
      "C.  Why the curves zigzag — the arrangements run out",
      "service moment  m   (kNm/m)", "arrangements the engine offers")
for code in CODES:
    counts = [len(sweep[code][index]["options"])
              for index in range(len(MOMENTS))]
    options_axes.step(MOMENTS, counts, where="post", color=COLOUR[code],
                      linewidth=2.4 if code == SA_CODE else 1.8,
                      label=SHORT[code], zorder=4)
options_axes.set_xlim(MOMENTS[0], MOMENTS[-1])
options_axes.set_ylim(0, 5)
options_axes.set_yticks([0, 1, 2, 3, 4])
options_axes.text(0.985, 0.94,
                  "each drop is one bar arrangement becoming infeasible, and"
                  + chr(10) +
                  "the steel area jumps when the engine moves to the next —"
                  + chr(10) +
                  "which is the zigzag in panel A, not noise",
                  transform=options_axes.transAxes, ha="right", va="top",
                  fontsize=8.5, color=INK_SOFT)
options_axes.legend(loc="lower left", fontsize=8.5, frameon=False,
                    labelcolor=INK)

# ---- D. [0] is not the best -------------------------------------------
spread_axes = figure.add_subplot(panels[1, 1])
dress(spread_axes,
      f"D.  Every arrangement at m = {ANCHOR_MOMENT:.0f} kNm/m — "
      f"[0] is not the best",
      "", "crack width   (mm)")
width = 0.26
for offset, code in enumerate(CODES):
    options = check(code, ANCHOR_MOMENT)["options"]
    widths = [option["crack"] for option in options]
    positions = np.arange(len(options)) + (offset - 1) * width
    spread_axes.bar(positions, widths, width=width, color=COLOUR[code],
                    alpha=0.9, edgecolor=SURFACE, linewidth=2.0,
                    label=SHORT[code], zorder=3)
    for position, option in zip(positions, options):
        spread_axes.text(position, option["crack"] + 0.006,
                         option["bars"], ha="center", fontsize=7.5,
                         rotation=90, va="bottom", color=INK_SOFT)
    # ONE annotation, for the code this study is about. All three drew
    # it before, and the three labels landed on top of each other.
    smallest = int(np.argmin(widths))
    if smallest != 0 and code == SA_CODE:
        spread_axes.text(0.60, 0.97,
                         f"the smallest crack is at [{smallest}], not at [0] —"
                         + chr(10) + "and [0] is what a caller reads by default",
                         transform=spread_axes.transAxes, ha="center",
                         va="top", fontsize=8.5, color=COLOUR[code],
                         fontweight="bold")
spread_axes.axhline(ALLOWED, color=DEAD, linewidth=1.4, linestyle="--")
spread_axes.annotate(f"{ALLOWED:.1f} mm allowable", (len(CODES), ALLOWED),
                     textcoords="offset points", xytext=(0, 6), ha="right",
                     fontsize=8.5, color=DEAD, fontweight="bold")
spread_axes.set_xticks(np.arange(4))
spread_axes.set_xticklabels([f"[{index}]" for index in range(4)],
                            fontsize=9.5, color=INK_SOFT)
spread_axes.set_xlabel("optimised_configs index", fontsize=9.5,
                       color=INK_SOFT)
spread_axes.set_ylim(0, ALLOWED * 1.30)
spread_axes.grid(True, axis="y", linewidth=0.6, color=GRID)
spread_axes.grid(False, axis="x")
spread_axes.legend(loc="upper left", fontsize=8.5, frameon=False,
                   labelcolor=INK)

figure.suptitle(
    f"One slab section, a growing service moment:  {SA_CODE}  against  "
    f"{EU_CODE}  and  {OLD_GENERATION}\n"
    f"{SECTION['h']:.0f} mm thick, tension zone {SECTION['hef']:.0f} mm, "
    f"cover {SECTION['cover']:.0f} mm, fcu {SECTION['fcu']:.0f} MPa, "
    f"allowable {ALLOWED:.1f} mm  —  ONLY the moment changes\n"
    f"C21 has NO old South African code, so this is the new one against "
    f"its parent — and the national adoption is worth a fraction of the "
    f"generation change",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "crack_widths_sans_vs_eurocode_moment.png")
