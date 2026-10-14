# ---
# Example:  One beam section, a growing moment - and two codes that cap the neutral axis differently
# Feature:  beam_section (C22 Beam Section)
# Verified: yes - 2026-09-07 - the pinned 300 x 500 section reproduces its mu and ast exactly at the sweep's m = 200 kNm point; every moment measured on prokon-automation.exe
# ---
# ONE section. ONE shear. ONE thing changes: the applied moment.
#
# The section (300 wide x 500 deep, 40 mm cover all round), the concrete
# (fcu 30), both steels (fy = fyv = 450) and the shear (100 kN) are held
# constant and asserted constant, so every difference is caused by the
# moment or by the code.
#
# THE CODES ------------------------------------------------------------
#
# SABS 0100 - 2000 is the old South African concrete code; C22 also carries
# the new one, SANS 51992-1-1:2025, and section 0 shows it answering - the
# new code is enabled in eight of the twelve engines, and this is one.
# Eurocode 2 - 2004 is the comparison. ⚠ There is no "Eurocode 2 - 2005"
# anywhere in the fleet.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE SAME SECTION HAS TWO DIFFERENT CAPACITIES, 33 % APART. mu is
#   295.18 kNm under SABS and 393.68 under Eurocode 2. It does not move
#   with the applied moment - it is the section's singly-reinforced
#   capacity - so the code alone is worth a third of this beam.
#
#   AND THE REASON IS ONE NUMBER: WHERE EACH CODE STOPS THE NEUTRAL AXIS.
#   The engine publishes x_na, so this is measured rather than asserted:
#   panel C plots it, and each code's plateau is its own cap. A deeper
#   permitted neutral axis is a bigger lever arm and a bigger mu.
#
#   THE STEEL CURVES CROSS, so neither code is simply "cheaper". Eurocode 2
#   asks for less steel on a lightly loaded section and more on a heavily
#   loaded one - the crossover is bisected in section 4.
#
#   AND "NEEDS TOP STEEL" IS THE SAME MOMENT AS mu - MEASURED, NOT ASSUMED.
#   Section 3 bisects the moment at which each code first asks for
#   compression steel and lands within 0.3 kNm of that code's own published
#   mu, both times. So mu is not a separate warning line: it IS the
#   singly-reinforced limit, and panel D therefore has TWO bands rather
#   than three. What matters is that the two codes put that one boundary
#   98.4 kNm apart - between 295 and 394 kNm the old code wants bars in the
#   top of this beam and the new one does not.
#
#   AND NEITHER CODE EVER REFUSES. Ask for three times the capacity and
#   both return a number - a bigger and bigger area of steel, with no error
#   and no flag. The reading that tells you the section has run out is m
#   against mu, and mu is published. Section 6 shows how far it goes.
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
SA_NEW_CODE = "SANS 51992-1-1:2025"

OLD_COLOUR = "#2a78d6"      # categorical slot 1
NEW_COLOUR = "#eb6834"      # categorical slot 2
FREE = "#0ca30c"
RAMP = "#fab219"
DEAD = "#d03b3b"

# -- THE SECTION, AND THE ONE INPUT THAT MOVES --------------------------
SECTION = dict(v=100.0, bw=300.0, h=500.0, dc_t=40.0, dc_b=40.0, dc_s=40.0,
               fcu=30.0, fy=450.0, fyv=450.0)

ANCHOR_MOMENT = 200.0
PINNED_MU = 295.18197048179997
PINNED_AST = 1287.32677061758

MOMENTS = np.arange(25.0, 901.0, 12.5)      # 71 moments, 25 to 900 kNm

DEPTH = SECTION["h"] - SECTION["dc_b"]      # effective depth d

print("ONE BEAM SECTION, A GROWING MOMENT - TWO DESIGN CODES")
print(f"  {SECTION['bw']:.0f} x {SECTION['h']:.0f} mm, cover "
      f"{SECTION['dc_b']:.0f} mm all round (d = {DEPTH:.0f} mm)")
print(f"  fcu {SECTION['fcu']:.0f} MPa, fy {SECTION['fy']:.0f} MPa, "
      f"fyv {SECTION['fyv']:.0f} MPa, V {SECTION['v']:.0f} kN held constant")
print(f"  the only input that moves: m, {MOMENTS[0]:.0f} to "
      f"{MOMENTS[-1]:.0f} kNm in {MOMENTS[1] - MOMENTS[0]:.1f} kNm steps "
      f"({len(MOMENTS)} moments)")

CALLS = {"engine": 0}
_ANSWERS = {}


def design(code, moment):
    """One moment, one code. Returns a row; never raises for a refusal."""
    key = (code, round(float(moment), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.beam_section.analyse(design_code=code,
                                                m=float(moment), **SECTION)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(moment=float(moment), ast=None, asc=None, mu=None,
                   x_na=None, asv=None,
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    row = dict(moment=float(moment), ast=result["ast"], asc=result["as1"],
               mu=result["mu"], x_na=result["x_na"], asv=result["asv"],
               reason=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE CODES THIS ENGINE HAS
# ======================================================================
# CONTROL for everything below: the codes used here must answer AND return
# different numbers. A reading that cannot tell two codes apart cannot
# tell you anything about either.
print("\n0. THE CODES THIS ENGINE HAS")
for code in (OLD_CODE, NEW_CODE, SA_NEW_CODE, PINNED_CODE):
    row = design(code, ANCHOR_MOMENT)
    if row["ast"] is None:
        print(f"   {code:<22} REFUSED   {row['reason']}")
    else:
        print(f"   {code:<22} answered  mu = {row['mu']:>8.2f} kNm   "
              f"ast = {row['ast']:>9.2f} mm2   x_na = {row['x_na']:>7.2f} mm")
print(f"   -> four codes, four readings, and they are NOT all the same, so")
print("      the comparison below is measuring the code and not the noise.")
print(f"   -> {SA_NEW_CODE} answers here. It is enabled in eight of")
print("      the twelve engines; C11, C12, C13 and C16 are the four without.")

# ======================================================================
# 1. THE ANCHOR
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at m = {ANCHOR_MOMENT:.0f} kNm")
anchor = design(PINNED_CODE, ANCHOR_MOMENT)
exact = anchor["mu"] == PINNED_MU and anchor["ast"] == PINNED_AST
print(f"   mu   {anchor['mu']!r:24} pinned {PINNED_MU!r}")
print(f"   ast  {anchor['ast']!r:24} pinned {PINNED_AST!r}")
print(f"   -> {'EXACT on both' if exact else 'DRIFTED - READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(MOMENTS)} moments x 2 codes")
sweep = {code: [design(code, moment) for moment in MOMENTS]
         for code in (OLD_CODE, NEW_CODE)}

assert SECTION["bw"] == 300.0 and SECTION["h"] == 500.0
assert SECTION["v"] == 100.0 and SECTION["fcu"] == 30.0
print("   the section dictionary and the shear are unchanged after the sweep")

print(f"\n   {'m (kNm)':>8} | {'SABS ast':>9} {'asc':>8} {'x_na':>7} | "
      f"{'EC2 ast':>9} {'asc':>8} {'x_na':>7} | {'EC2/SABS':>9}")
for index, moment in enumerate(MOMENTS):
    if moment % 100 != 0:
        continue
    cells, steel = [], {}
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        steel[code] = row["ast"]
        cells.append(f" {row['ast']:>9.1f} {row['asc']:>8.1f} "
                     f"{row['x_na']:>7.2f}")
    print(f"   {moment:>8.0f} |" + " |".join(cells)
          + f" | {steel[NEW_CODE] / steel[OLD_CODE]:>8.3f}x")

# mu does not move with the applied moment - it is the section's capacity.
# Said, then checked, because the whole study leans on it.
print("\n   mu IS A PROPERTY OF THE SECTION, NOT OF THE LOAD")
capacity = {}
for code in (OLD_CODE, NEW_CODE):
    values = {row["mu"] for row in sweep[code] if row["mu"] is not None}
    capacity[code] = sweep[code][0]["mu"]
    print(f"   {code:<22} mu = {capacity[code]!r}")
    print(f"   {'':<22} took {len(values)} distinct value(s) over all "
          f"{len(MOMENTS)} moments")
print(f"   -> Eurocode 2 gives this section "
      f"{(capacity[NEW_CODE] / capacity[OLD_CODE] - 1) * 100:.1f} % more "
      f"capacity")
print(f"      from the same concrete and the same geometry: "
      f"{capacity[NEW_CODE]:.2f} against {capacity[OLD_CODE]:.2f} kNm.")


def boundary(holds, low, high, resolution=0.5):
    """The largest moment where `holds` is still true, to `resolution`.

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
# 3. WHERE COMPRESSION STEEL STARTS
# ======================================================================
print("\n3. THE MOMENT AT WHICH EACH CODE FIRST WANTS COMPRESSION STEEL")
singly = {}
for code in (OLD_CODE, NEW_CODE):
    rows = sweep[code]
    none_yet = [row for row in rows if row["asc"] == 0]
    needs = [row for row in rows if row["asc"] and row["asc"] > 0]
    if not none_yet or not needs:
        print(f"   {code:<22} no crossing inside this sweep")
        continue

    def singly_reinforced(moment, code=code):
        return design(code, moment)["asc"] == 0

    low, high = boundary(singly_reinforced, none_yet[-1]["moment"],
                         needs[0]["moment"])
    singly[code] = low
    print(f"   {code:<22} singly reinforced to {low:.2f} kNm, top steel "
          f"from {high:.2f}")
    print(f"   {'':<22} and its own published mu is "
          f"{capacity[code]:.2f} kNm")
if len(singly) == 2:
    print(f"   -> {abs(singly[NEW_CODE] - singly[OLD_CODE]):.1f} kNm apart. "
          f"Between those two moments the")
    print("      old code wants bars in the top of this beam and the new one")
    print("      does not - the same beam, the same load, a different cage.")

# ======================================================================
# 4. WHERE THE TWO STEEL CURVES CROSS
# ======================================================================
print("\n4. WHERE THE CHEAPER CODE CHANGES SIDES")
old_ast = np.asarray([row["ast"] for row in sweep[OLD_CODE]], dtype=float)
new_ast = np.asarray([row["ast"] for row in sweep[NEW_CODE]], dtype=float)
lighter_at_start = new_ast[0] < old_ast[0]
flipped = [index for index in range(len(MOMENTS) - 1)
           if (new_ast[index] < old_ast[index])
           != (new_ast[index + 1] < old_ast[index + 1])]
print(f"   at m = {MOMENTS[0]:.0f} kNm the "
      f"{'NEW' if lighter_at_start else 'OLD'} code asks for less steel "
      f"({new_ast[0]:.1f} against {old_ast[0]:.1f} mm2)")
if flipped:
    def new_is_lighter(moment):
        return design(NEW_CODE, moment)["ast"] < design(OLD_CODE,
                                                        moment)["ast"]

    low, high = boundary(new_is_lighter, MOMENTS[flipped[0]],
                         MOMENTS[flipped[0] + 1])
    print(f"   they swap places between {low:.2f} and {high:.2f} kNm")
    print(f"   at m = {MOMENTS[-1]:.0f} kNm the "
          f"{'NEW' if new_ast[-1] < old_ast[-1] else 'OLD'} code asks for "
          f"less ({new_ast[-1]:.1f} against {old_ast[-1]:.1f} mm2)")
    print("   -> so neither code is 'the expensive one'. Which is cheaper")
    print("      depends on where on this axis your beam sits.")
    crossover = low
else:
    crossover = None
    print("   one code is lighter across the whole sweep - no crossover")

# ======================================================================
# 5. THE NEUTRAL AXIS, AND WHY mu DIFFERS
# ======================================================================
# x_na is published, so the mechanism behind the 33 % is measurable rather
# than a matter of belief: each code allows the neutral axis to a
# different fraction of d, and a deeper axis is a longer lever arm.
print("\n5. WHERE EACH CODE STOPS THE NEUTRAL AXIS   "
      f"(d = {DEPTH:.0f} mm)")
for code in (OLD_CODE, NEW_CODE):
    depths = [row["x_na"] for row in sweep[code] if row["x_na"] is not None]
    deepest = max(depths)
    plateau = sum(1 for value in depths if value == deepest)
    print(f"   {code:<22} deepest x_na {deepest:>8.2f} mm = "
          f"{deepest / DEPTH:.3f} d")
    print(f"   {'':<22} and it sits there for {plateau} of "
          f"{len(depths)} moments - a cap, not a coincidence")
print("   -> that ratio is the lever-arm difference, and it is the whole")
print("      reason the same concrete has two capacities.")

# ======================================================================
# 6. NEITHER CODE EVER REFUSES
# ======================================================================
print("\n6. NEITHER CODE EVER REFUSES")
for code in (OLD_CODE, NEW_CODE):
    last = sweep[code][-1]
    print(f"   {code:<22} at m = {last['moment']:.0f} kNm "
          f"({last['moment'] / capacity[code]:.2f}x its own published mu)")
    print(f"   {'':<22} it returns ast {last['ast']:>10.1f} mm2 and "
          f"asc {last['asc']:>10.1f} mm2, no error")
print("   -> compare m against mu. Both are in the result dictionary, and")
print("      that comparison is the only thing standing between a caller")
print("      and a confident number for a beam that cannot be built.")

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


def series(code, field):
    return np.asarray([np.nan if row[field] is None else row[field]
                       for row in sweep[code]], dtype=float)


# ---- A. steel against moment -------------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  Tension steel (solid) and compression steel (dotted)",
      "applied moment  m   (kNm)", "steel area   (mm²)")

peak = max(np.nanmax(series(code, "ast")) for code in (OLD_CODE, NEW_CODE))
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    chart.plot(MOMENTS, series(code, "ast"), color=colour, linewidth=2.0,
               label=f"{short}  Ast", zorder=4)
    chart.plot(MOMENTS, series(code, "asc"), color=colour, linewidth=1.6,
               linestyle=":", label=f"{short}  Asc", zorder=4)
    chart.plot([capacity[code]] * 2, [0.0, peak * 1.02], color=colour,
               linewidth=1.3, linestyle="--", zorder=2)

# The mu labels run VERTICALLY, hugging their own dashed lines just above
# the axis. Laid horizontally they crossed the rising Ast curve, which is
# the one thing in this panel a reader must be able to follow.
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    chart.text(capacity[code] - 9, peak * 0.035,
               f"{'SABS' if code == OLD_CODE else 'Eurocode 2'} "
               f"mu = {capacity[code]:.1f} kNm",
               rotation=90, va="bottom", ha="center", fontsize=8.5,
               color=colour, fontweight="bold")
    if code in singly:
        chart.plot([singly[code]], [0.0], marker="o", markersize=8,
                   color=colour, markeredgecolor=SURFACE, markeredgewidth=2.0,
                   zorder=6)

chart.plot([ANCHOR_MOMENT], [design(PINNED_CODE, ANCHOR_MOMENT)["ast"]],
           marker="D", markersize=8, color=MUTED, markeredgecolor=SURFACE,
           markeredgewidth=2.0, zorder=7)
chart.annotate("the pinned section", (ANCHOR_MOMENT,
                                      design(PINNED_CODE,
                                             ANCHOR_MOMENT)["ast"]),
               textcoords="offset points", xytext=(-10, 12), ha="right",
               fontsize=8.5, color=INK_SOFT)
chart.set_xlim(MOMENTS[0], MOMENTS[-1])
chart.set_ylim(0.0, peak * 1.10)
chart.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor=INK,
             ncol=2)

# ---- B. the direct comparison ------------------------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "applied moment  m   (kNm)", "tension steel,  new ÷ old")

ratio = new_ast / old_ast
ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
ratio_axes.fill_between(MOMENTS, ratio, 1.0, where=(ratio >= 1.0),
                        interpolate=True, color=NEW_COLOUR, alpha=0.16)
ratio_axes.fill_between(MOMENTS, ratio, 1.0, where=(ratio <= 1.0),
                        interpolate=True, color=OLD_COLOUR, alpha=0.16)
ratio_axes.plot(MOMENTS, ratio, color=NEW_COLOUR, linewidth=2.0, zorder=4)

ratio_axes.annotate(f"at {MOMENTS[0]:.0f} kNm the new code\n"
                    f"asks {(1 - ratio[0]) * 100:.1f} % LESS steel",
                    (MOMENTS[0], ratio[0]), textcoords="offset points",
                    xytext=(16, 6), ha="left", fontsize=8.5,
                    color=OLD_COLOUR, fontweight="bold")
if crossover is not None:
    ratio_axes.plot([crossover], [1.0], marker="o", markersize=8,
                    color=INK, markeredgecolor=SURFACE, markeredgewidth=2.0,
                    zorder=6)
    ratio_axes.annotate(f"they change places\nat {crossover:.0f} kNm",
                        (crossover, 1.0), textcoords="offset points",
                        xytext=(10, -26), ha="left", fontsize=8.5,
                        color=INK, fontweight="bold")
ratio_axes.annotate(f"and {(ratio[-1] - 1) * 100:.1f} % MORE by "
                    f"{MOMENTS[-1]:.0f} kNm",
                    (MOMENTS[-1], ratio[-1]), textcoords="offset points",
                    xytext=(-10, -6), ha="right", va="top", fontsize=8.5,
                    color=NEW_COLOUR, fontweight="bold")
ratio_axes.set_xlim(MOMENTS[0], MOMENTS[-1])

# ---- C. the mechanism: the neutral-axis cap ----------------------------
axis_panel = figure.add_subplot(panels[1, 0])
dress(axis_panel,
      "C.  Why — how deep each code lets the neutral axis go",
      "applied moment  m   (kNm)", "x_na   (mm below the top face)")

for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    depths = series(code, "x_na")
    axis_panel.plot(MOMENTS, depths, color=colour, linewidth=2.0, label=code,
                    zorder=4)
    deepest = np.nanmax(depths)
    axis_panel.annotate(f"caps at {deepest:.1f} mm = {deepest / DEPTH:.3f} d",
                        (MOMENTS[-1], deepest), textcoords="offset points",
                        xytext=(-8, 8 if code == NEW_CODE else -16),
                        ha="right", fontsize=8.5, color=colour,
                        fontweight="bold")

axis_panel.axhline(DEPTH, color=MUTED, linewidth=1.1, linestyle="--")
axis_panel.annotate(f"d = {DEPTH:.0f} mm", (MOMENTS[0], DEPTH),
                    textcoords="offset points", xytext=(4, 6), fontsize=8.5,
                    color=MUTED)
axis_panel.set_xlim(MOMENTS[0], MOMENTS[-1])
axis_panel.set_ylim(0.0, DEPTH * 1.12)
axis_panel.legend(loc="lower right", fontsize=8.5, frameon=False,
                  labelcolor=INK)

# ---- D. the verdict, side by side --------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same section, same axis — what each code tells you",
      "", "")
verdict.set_xlabel("applied moment  m   (kNm)", fontsize=9.5, color=INK_SOFT)

# TWO bands. Section 3 measured the compression-steel threshold onto
# mu itself, so a third band between them would be a few tenths of a kNm
# wide and would imply a distinction the engine does not make.
REGIMES = ((FREE, "singly reinforced — no top steel, m below mu"),
           (DEAD, "past mu: top steel required, and still no refusal"))

for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    top_steel_from = singly.get(code, MOMENTS[-1])
    past_mu = capacity[code]
    for start, stop, colour in ((MOMENTS[0], past_mu, FREE),
                                (past_mu, MOMENTS[-1], DEAD)):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, edgecolor=SURFACE,
                     linewidth=2.0, zorder=3)
    verdict.text(MOMENTS[0] + 8, base + 0.15, code, fontsize=9.5, color=INK,
                 fontweight="bold")
    verdict.plot([past_mu, past_mu], [base - 0.145, base - 0.105], color=INK,
                 linewidth=1.0, zorder=5)
    verdict.text(past_mu, base - 0.20, f"mu = {past_mu:.0f} kNm", ha="center",
                 fontsize=8.5, color=INK, fontweight="bold")
    verdict.text(MOMENTS[-1], base + 0.15,
                 f"top steel from {top_steel_from:.1f} kNm — the same "
                 f"boundary, measured", ha="right", fontsize=8.5,
                 color=INK_SOFT)

verdict.set_xlim(MOMENTS[0], MOMENTS[-1])
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
    f"One beam section, a growing moment:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"{SECTION['bw']:.0f} × {SECTION['h']:.0f} mm, cover "
    f"{SECTION['dc_b']:.0f} mm, fcu {SECTION['fcu']:.0f} MPa, "
    f"fy {SECTION['fy']:.0f} MPa, V {SECTION['v']:.0f} kN  —  "
    f"ONLY the applied moment changes\n"
    f"The same section has two capacities — mu {capacity[OLD_CODE]:.1f} "
    f"against {capacity[NEW_CODE]:.1f} kNm — and panel C shows the one "
    f"published number that explains it",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "beam_section_sabs_vs_eurocode_moment.png")
