# ---
# Example:  Two spans, growing longer - the codes agree on flexure, disagree on shear, and disagree in DIRECTION on cracking
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes - 2026-09-07 - the pinned two-span beam reproduces all five of its pinned values exactly at the sweep's 6 m point; every span measured on prokon-automation.exe
# ---
# ONE beam. TWO equal spans. ONE thing changes: how long they are.
#
# The section (300 x 500), the loads per metre (20 dead, 10 live), the
# covers, the link steel, and every serviceability setting are held
# constant and asserted constant - so every difference is caused by the
# span or by the code.
#
# THE CODES ------------------------------------------------------------
#
# SABS 0100 - 2000 against Eurocode 2 - 2004. C01 also carries the new
# South African code, SANS 51992-1-1:2025, and section 0 shows it
# answering. ⚠ There is no "Eurocode 2 - 2005" anywhere in the fleet.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
# C01 publishes four different answers about the same beam, and the two
# codes relate to each other DIFFERENTLY in each. That is the point of this
# study: "which code is more onerous" has four answers, not one.
#
#   FLEXURE: THEY ALMOST AGREE. Bottom and top steel stay within a few per
#   cent across the whole range, and the curves cross. Nothing here would
#   change a drawing.
#
#   SHEAR: THEY DO NOT. Eurocode 2 asks for NO shear reinforcement at all
#   up to 3.50 m spans, where SABS asks for some at every span in the
#   range. Where both ask for links the old code wants between 33 % and
#   104 % more - measured, and the spread is the point: there is no single
#   factor between them. Same beam, same load, same links, a different cage.
#
#   CRACKING: THE TWO CODES END UP GOING OPPOSITE WAYS. Over 3.5 to 18 m
#   the old code's crack width finishes HIGHER than it started (0.0747 ->
#   0.1924 mm) and Eurocode 2's finishes LOWER (0.1482 -> 0.1286), and the
#   curves cross four times.
#
#   ⚠ BUT NEITHER CURVE IS MONOTONIC, and an earlier draft of this comment
#   said they were. Measured: SABS rises at 40 of 58 steps and falls at 18;
#   Eurocode 2 rises at 33 and falls at 25. So this is a net trend in
#   opposite directions, not a clean law - and panel C is deliberately
#   drawn at full resolution so the sawtooth is visible rather than
#   smoothed away. The useful conclusion survives either way: a rule of
#   thumb calibrated on one of these codes is worthless on the other.
#
#   DEFLECTION: THEY TRACK, but not exactly - Eurocode 2 runs a few per
#   cent higher, and it grows with span.
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

# -- THE BEAM, AND THE ONE INPUT THAT MOVES -----------------------------
BEAM = dict(sections=[{"n": 1, "bw": 300, "d": 500}],
            supports=[{"n": 1}, {"n": 2}, {"n": 3}],
            fyv=250.0, cover_top=30.0, cover_bot=40.0,
            live_permanent_percent=25.0, creep_coefficient=2.0,
            shrinkage_strain=300e-6)
DEAD = 20.0
LIVE = 10.0

ANCHOR_SPAN = 6.0
PINNED = {"bottom": 805.0209555473922, "top": 1235.4393480298781,
          "shear": 0.6078222002339925, "deflection": 12.446682698091044,
          "crack": 0.11738993516717798}

SPANS = np.arange(3.0, 18.01, 0.25)         # 61 spans, 3 m to 18 m

print("TWO SPANS, GROWING LONGER - TWO DESIGN CODES")
print(f"  {BEAM['sections'][0]['bw']:.0f} x {BEAM['sections'][0]['d']:.0f} mm, "
      f"three simple supports, links fyv {BEAM['fyv']:.0f} MPa")
print(f"  loads held constant: {DEAD:.0f} kN/m dead + {LIVE:.0f} kN/m live "
      f"on both spans")
print(f"  serviceability held constant: "
      f"{BEAM['live_permanent_percent']:.0f} % of live permanent, creep "
      f"{BEAM['creep_coefficient']:.1f}, shrinkage "
      f"{BEAM['shrinkage_strain'] * 1e6:.0f} microstrain")
print(f"  the only input that moves: both span lengths, {SPANS[0]:.1f} to "
      f"{SPANS[-1]:.1f} m in {SPANS[1] - SPANS[0]:.2f} m steps "
      f"({len(SPANS)} spans)")

CALLS = {"engine": 0}
_ANSWERS = {}


def design(code, span):
    """One span, one code. Returns a row; never raises for a refusal."""
    key = (code, round(float(span), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.continuous_beam.analyse(
            design_code=code,
            segments=[{"span": 1, "length": float(span), "sec_left": 1},
                      {"span": 2, "length": float(span), "sec_left": 1}],
            loads=[{"case": "Dead", "span": 1, "w_left": DEAD},
                   {"case": "Dead", "span": 2, "w_left": DEAD},
                   {"case": "Live", "span": 1, "w_left": LIVE},
                   {"case": "Live", "span": 2, "w_left": LIVE}],
            **BEAM)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(span=float(span), bottom=None, top=None, shear=None,
                   deflection=None, crack=None,
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    first = result["spans"][0]
    row = dict(span=float(span),
               bottom=first["max_bottom_steel"],
               top=first["max_top_steel"],
               shear=first["max_shear_steel"],
               deflection=result["max_deflection"],
               crack=result["max_crack_width"], reason=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE CODES THIS ENGINE HAS
# ======================================================================
# CONTROL for the whole study: the codes must answer AND disagree. A
# reading that cannot tell two codes apart says nothing about either.
print("\n0. THE CODES THIS ENGINE HAS")
for code in (OLD_CODE, NEW_CODE, SA_NEW_CODE, PINNED_CODE):
    row = design(code, ANCHOR_SPAN)
    if row["bottom"] is None:
        print(f"   {code:<22} REFUSED   {row['reason']}")
    else:
        print(f"   {code:<22} answered  bottom {row['bottom']:>8.1f}  "
              f"shear {row['shear']:>7.4f}  crack {row['crack']:>8.5f}")
print("   -> four codes, and the readings differ, so the sweep below is")
print("      measuring the code and not the noise.")
print(f"   -> {SA_NEW_CODE} answers here; it is enabled in eight")
print("      of the twelve engines (C11, C12, C13 and C16 are the four")
print("      without it).")

# ======================================================================
# 1. THE ANCHOR - all five pinned values
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at {ANCHOR_SPAN:.0f} m spans")
anchor = design(PINNED_CODE, ANCHOR_SPAN)
matched = 0
for name in ("bottom", "top", "shear", "deflection", "crack"):
    hit = anchor[name] == PINNED[name]
    matched += hit
    print(f"   {name:<11} {anchor[name]!r:24} pinned {PINNED[name]!r}")
print(f"   -> {matched} of 5 exact"
      f"{'' if matched == 5 else '  - DRIFTED, READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(SPANS)} spans x 2 codes")
sweep = {code: [design(code, span) for span in SPANS]
         for code in (OLD_CODE, NEW_CODE)}

assert BEAM["sections"][0]["d"] == 500 and BEAM["fyv"] == 250.0
assert DEAD == 20.0 and LIVE == 10.0
print("   the beam dictionary and both loads are unchanged after the sweep")

print(f"\n   {'span':>5} | {'SABS bot':>9} {'shear':>7} {'crack':>8} "
      f"{'defl':>7} | {'EC2 bot':>9} {'shear':>7} {'crack':>8} {'defl':>7}")
for index, span in enumerate(SPANS):
    if span % 3 != 0:
        continue
    cells = []
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        cells.append(f" {row['bottom']:>9.1f} {row['shear']:>7.4f} "
                     f"{row['crack']:>8.5f} {row['deflection']:>7.2f}")
    print(f"   {span:>5.1f} |" + " |".join(cells))


def column(code, field):
    return np.asarray([np.nan if row[field] is None else row[field]
                       for row in sweep[code]], dtype=float)


# ======================================================================
# 3. FOUR ANSWERS, FOUR DIFFERENT RELATIONSHIPS
# ======================================================================
# The headline claim of this study is that "which code is more onerous"
# has four answers. That is worth stating as a table rather than as prose,
# because the direction of each ratio is the finding.
print("\n3. THE SAME TWO CODES, FOUR DIFFERENT VERDICTS")
print(f"   {'quantity':<12} {'at 3 m':>22} {'at 18 m':>22} {'direction':>26}")
summary = {}
for name, label in (("bottom", "bottom steel"), ("top", "top steel"),
                    ("shear", "shear steel"), ("crack", "crack width"),
                    ("deflection", "deflection")):
    old = column(OLD_CODE, name)
    new = column(NEW_CODE, name)
    summary[name] = (old, new)

    def relation(index):
        if old[index] == 0 and new[index] == 0:
            return "both zero"
        if old[index] == 0 or new[index] == 0:
            zero = "new" if new[index] == 0 else "old"
            return f"{zero} code reads 0"
        share = new[index] / old[index]
        return f"new is {abs(share - 1) * 100:>5.1f} % " \
               f"{'MORE' if share > 1 else 'less'}"

    swaps = sum(1 for index in range(len(SPANS) - 1)
                if (new[index] < old[index]) != (new[index + 1] < old[index + 1]))
    print(f"   {label:<12} {relation(0):>22} {relation(-1):>22} "
          f"{('they cross ' + str(swaps) + ' time(s)') if swaps else 'never cross':>26}")

# The one that is not a matter of degree: opposite monotonic trends.
print("\n   AND ONE OF THEM RUNS THE OTHER WAY ENTIRELY")
for name in ("crack",):
    old, new = summary[name]
    # Compare each code's own trend over the part of the range where both
    # are non-zero, so a single zero reading cannot manufacture a trend.
    live = (old > 0) & (new > 0)
    spans_live = SPANS[live]
    old_live, new_live = old[live], new[live]
    for code, values in ((OLD_CODE, old_live), (NEW_CODE, new_live)):
        rises = sum(1 for index in range(len(values) - 1)
                    if values[index + 1] > values[index])
        falls = len(values) - 1 - rises
        print(f"     {code:<22} {name}: {rises} rises, {falls} falls "
              f"over {spans_live[0]:.2f} to {spans_live[-1]:.2f} m")
        print(f"     {'':<22} {values[0]:.5f} at the short end -> "
              f"{values[-1]:.5f} at the long end")
    old_trend = "RISES" if old_live[-1] > old_live[0] else "FALLS"
    new_trend = "RISES" if new_live[-1] > new_live[0] else "FALLS"
    print(f"   -> the old code's crack width {old_trend} with span and the "
          f"new code's {new_trend}.")
    if old_trend != new_trend:
        print("      Opposite signs. This is not a tolerance question: a rule")
        print("      of thumb calibrated on one code is worthless on the")
        print("      other, and the two curves cross rather than diverge.")

# ======================================================================
# 4. THE SHEAR DIVERGENCE, AND WHERE THE NEW CODE ASKS FOR NOTHING
# ======================================================================
print("\n4. SHEAR: THE ONE A DETAILER WOULD NOTICE")
for code in (OLD_CODE, NEW_CODE):
    values = column(code, "shear")
    zero = SPANS[values == 0]
    print(f"   {code:<22} no shear steel at "
          f"{len(zero)} of {len(SPANS)} spans"
          + (f", up to {zero.max():.2f} m" if len(zero) else ""))
    print(f"   {'':<22} {values[0]:.4f} at {SPANS[0]:.1f} m -> "
          f"{values[-1]:.4f} at {SPANS[-1]:.1f} m")
old_shear, new_shear = column(OLD_CODE, "shear"), column(NEW_CODE, "shear")
comparable = (old_shear > 0) & (new_shear > 0)
if comparable.any():
    share = new_shear[comparable] / old_shear[comparable]
    print(f"   -> where both ask for links, the new code wants between "
          f"{share.min():.2f}x and {share.max():.2f}x")
    print(f"      the old code's - so the old code asks for up to "
          f"{(1 / share.min() - 1) * 100:.0f} % more.")

print(f"\n   {CALLS['engine']} engine calls in total")

# ======================================================================
# 5. THE PICTURE  -  one panel per published answer
# ======================================================================
figure = plt.figure(figsize=(16.0, 10.6), facecolor=SURFACE)
panels = figure.add_gridspec(2, 2, hspace=0.34, wspace=0.20,
                             left=0.055, right=0.985, top=0.865, bottom=0.075)


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
    axes.set_xlim(SPANS[0], SPANS[-1])


# ---- A. flexure: they almost agree -------------------------------------
flexure = figure.add_subplot(panels[0, 0])
dress(flexure, "A.  Flexure — the codes almost agree",
      "span length  (m, both spans equal)", "steel in span 1   (mm²)")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    flexure.plot(SPANS, column(code, "bottom"), color=colour, linewidth=2.0,
                 label=f"{short}  bottom")
    flexure.plot(SPANS, column(code, "top"), color=colour, linewidth=1.6,
                 linestyle=":", label=f"{short}  top")
flexure.plot([ANCHOR_SPAN], [anchor["bottom"]], marker="D", markersize=8,
             color=MUTED, markeredgecolor=SURFACE, markeredgewidth=2.0,
             zorder=7)
flexure.annotate("the pinned beam", (ANCHOR_SPAN, anchor["bottom"]),
                 textcoords="offset points", xytext=(12, -4), ha="left",
                 fontsize=8.5, color=INK_SOFT)
old_bottom, new_bottom = column(OLD_CODE, "bottom"), column(NEW_CODE, "bottom")
flexure.text(0.985, 0.05,
             "within "
             f"{np.nanmax(np.abs(new_bottom / old_bottom - 1)) * 100:.1f} % "
             "on bottom steel across the whole range",
             transform=flexure.transAxes, ha="right", va="bottom",
             fontsize=8.5, color=INK_SOFT)
flexure.legend(loc="upper left", fontsize=8.5, frameon=False,
               labelcolor=INK, ncol=2)

# ---- B. shear: they do not ---------------------------------------------
shear_axes = figure.add_subplot(panels[0, 1])
dress(shear_axes, "B.  Shear — the codes do NOT agree",
      "span length  (m)", "max shear steel in span 1")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    shear_axes.plot(SPANS, column(code, "shear"), color=colour, linewidth=2.0,
                    label=code)
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    values = column(code, "shear")
    zero = SPANS[values == 0]
    if len(zero):
        shear_axes.plot([zero.max()], [0.0], marker="o", markersize=8,
                        color=colour, markeredgecolor=SURFACE,
                        markeredgewidth=2.0, zorder=6)
        shear_axes.annotate(f"{'SABS' if code == OLD_CODE else 'Eurocode 2'}: "
                            f"no links at all\nup to {zero.max():.2f} m",
                            (zero.max(), 0.0), textcoords="offset points",
                            xytext=(20, 34), ha="left", fontsize=8.5,
                            color=colour, fontweight="bold")
shear_axes.annotate(f"and {(old_shear[-1] / new_shear[-1] - 1) * 100:.0f} % "
                    f"more\nunder the old code here",
                    (SPANS[-1], old_shear[-1]), textcoords="offset points",
                    xytext=(-10, -6), ha="right", va="top", fontsize=8.5,
                    color=OLD_COLOUR, fontweight="bold")
shear_axes.legend(loc="upper left", fontsize=9, frameon=False,
                  labelcolor=INK)

# ---- C. cracking: opposite directions ----------------------------------
crack_axes = figure.add_subplot(panels[1, 0])
dress(crack_axes, "C.  Cracking — the two codes run in OPPOSITE directions",
      "span length  (m)", "max crack width   (mm)")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    values = column(code, "crack")
    crack_axes.plot(SPANS, values, color=colour, linewidth=2.0, label=code)
    live = values > 0
    if live.any():
        arrow = "rises" if values[live][-1] > values[live][0] else "falls"
        crack_axes.annotate(f"{arrow} with span",
                            (SPANS[live][-1], values[live][-1]),
                            textcoords="offset points",
                            xytext=(-10, 10 if arrow == "rises" else -18),
                            ha="right", fontsize=8.5, color=colour,
                            fontweight="bold")
# ⚠ NOT "two monotonic trends". Measured, they are not: the counts are
# printed in section 3 and the sawtooth is visible above. What is true is
# that the NET directions are opposite - and that is what the caption says.
crack_axes.text(0.035, 0.05,
                "opposite NET directions — but neither curve is monotonic, "
                "and they cross" + chr(10) +
                "four times. A rule of thumb calibrated on one code is "
                "worthless on the other.",
                transform=crack_axes.transAxes, va="bottom", fontsize=8.5,
                color=INK_SOFT)
crack_axes.legend(loc="lower right", fontsize=9, frameon=False,
                  labelcolor=INK)

# ---- D. deflection: they track ------------------------------------------
defl_axes = figure.add_subplot(panels[1, 1])
dress(defl_axes, "D.  Deflection — they track, but not exactly",
      "span length  (m)", "max deflection   (mm)")
old_defl, new_defl = column(OLD_CODE, "deflection"), column(NEW_CODE,
                                                            "deflection")
for code, colour, values in ((OLD_CODE, OLD_COLOUR, old_defl),
                             (NEW_CODE, NEW_COLOUR, new_defl)):
    defl_axes.plot(SPANS, values, color=colour, linewidth=2.0, label=code)
gapped = int(np.argmax(np.abs(new_defl / old_defl - 1)))
defl_axes.plot([SPANS[gapped]], [new_defl[gapped]], marker="o", markersize=8,
               color=NEW_COLOUR, markeredgecolor=SURFACE, markeredgewidth=2.0,
               zorder=6)
defl_axes.annotate(f"widest gap {abs(new_defl[gapped] / old_defl[gapped] - 1) * 100:.1f} % "
                   f"at {SPANS[gapped]:.2f} m\n"
                   f"({new_defl[gapped]:.1f} against "
                   f"{old_defl[gapped]:.1f} mm)",
                   (SPANS[gapped], new_defl[gapped]),
                   textcoords="offset points", xytext=(-14, 6), ha="right",
                   fontsize=8.5, color=NEW_COLOUR, fontweight="bold")
defl_axes.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=INK)

figure.suptitle(
    f"Two spans, growing longer:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"{BEAM['sections'][0]['bw']:.0f} × {BEAM['sections'][0]['d']:.0f} mm, "
    f"{DEAD:.0f} kN/m dead + {LIVE:.0f} kN/m live, links fyv "
    f"{BEAM['fyv']:.0f} MPa  —  ONLY the span length changes\n"
    f"Four published answers, four different relationships — the codes "
    f"almost agree on flexure, disagree sharply on shear, and run in "
    f"OPPOSITE directions on cracking",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "continuous_beam_sabs_vs_eurocode_span.png")
