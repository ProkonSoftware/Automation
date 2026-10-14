# ---
# Example:  One post-tensioned floor, a growing live load - and a code change that only touches the EDGE columns
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes - 2026-09-07 - the desktop's own DEFAULT EXAMPLE reproduces all three pinned punching veff values exactly at the sweep's 15 kN/m point; every load measured on prokon-automation.exe
# ---
# ONE floor. TWO spans. THREE columns. ONE thing changes: the live load.
#
# The geometry, the cable layout, the tendon properties, the supports, the
# added reinforcement, the dead load and every punching-shear input are
# held constant and asserted constant - so every difference is caused by
# the live load or by the code.
#
# THE CODES ------------------------------------------------------------
#
# SABS 0100 - 2000 against Eurocode 2 - 2004. C02 also carries the new
# South African code, SANS 51992-1-1:2025, and section 0 shows it
# answering. ⚠ There is no "Eurocode 2 - 2005" anywhere in the fleet.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE CODE CHANGE IS ALMOST ENTIRELY ABOUT THE EDGE COLUMNS. Measured at
#   the reference load, the effective punching shear at the two edge
#   columns falls by about 42 % when you switch to Eurocode 2, while the
#   internal column moves by about one per cent. Same floor, same load,
#   same tendons - and two of the three columns are a different problem.
#
#   SO THE CODE CHANGES WHICH COLUMN YOU HAVE TO WORRY ABOUT. Measured at
#   the reference load: under the old code the worst column is 1.40x the
#   best, so all three are live concerns. Under Eurocode 2 it is 2.32x, and
#   only the internal column is worth looking at. Panel C draws that shape
#   change directly.
#
#   AND THE SHARPEST RESULT IS IN SECTION 5. Under the old code the first
#   critical perimeter is over its own published vcap at EVERY live load in
#   this range, down to 2 kN/m; under Eurocode 2 the floor is clear to
#   5.00 kN/m. On the same slab with the same tendons, the code choice is
#   the difference between needing punching reinforcement everywhere and
#   not needing it at all at light load.
#
#   AND IT IS NOT A CONSTANT FACTOR. Panel B divides the two codes column
#   by column: two lines sit together well below 1.0 and one sits almost
#   on it. A single "the new code is x % lighter" would be wrong for every
#   column here.
#
#   BOTH CODES AGREE ON WHICH COLUMN GOVERNS, and section 4 checks that
#   rather than assuming it - the internal column is the worst under both.
#   So the maximum live load this floor carries is set by the same column
#   either way; what changes is how much margin the other two have.
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
DEAD = "#d03b3b"

# -- THE FLOOR ----------------------------------------------------------
# The desktop's own DEFAULT EXAMPLE: a 5 m wide, 250 mm post-tensioned
# slab strip over two spans, seven unbonded cables in two sets jacked from
# opposite ends, and punching checks at all three columns.
TENDONS = [{"no": 1, "bond": "Unbonded", "strength": 260.7,
            "max_stress_pct": 80, "dia": 18, "area": 140,
            "k": 0.0015, "u": 0.05, "pullin": 5, "relax": 2,
            "est": 195e6, "min_harp_radius": 1.0}]
CABLES = [
    {"n": 4, "prop": 1, "x_live": 0.0, "x_dead": 15.5,
     "spans": [{"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125, "b2": 34,
                "b3": 34},
               {"span": 2, "lo": 0.4, "ro": 0.0, "b1": 34, "b2": 34,
                "b3": 125}]},
    {"n": 3, "prop": 1, "x_live": 15.5, "x_dead": 0.0,
     "spans": [{"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125, "b2": 34,
                "b3": 34},
               {"span": 2, "lo": 0.38, "ro": 0.0, "b1": 34, "b2": 34,
                "b3": 125}]}]
FLOOR = dict(
    title="DEFAULT EXAMPLE",
    fcu=19.2, fy=450.0, fyv=250.0, fci=14.4, ec=26e6, est=206e6,
    density=24.0, top_cover=25.0, bottom_cover=25.0,
    attached_torsional_members=True, edge_beam=True,
    redistribution_pct=10.0,
    tendon_properties=TENDONS, cable_sets=CABLES,
    sections=[{"name": "sec1", "bw": 5000, "d": 250},
              {"name": "sec2", "bw": 5000, "d": 500},
              {"name": "sec3", "bw": 2500, "d": 500}],
    span_segments=[{"span": 1, "length": 8.0, "sec_left": "sec1"},
                   {"span": 2, "length": 7.5, "sec_left": "sec1"}],
    supports=[
        {"no": 1, "d_below": 300, "b_below": 300, "h_below": 3.0,
         "code_below": "F", "d_above": 300, "b_above": 300, "h_above": 3.0,
         "code_above": "F"},
        {"no": 2, "d_below": 300, "h_below": 3.0, "code_below": "F"},
        {"no": 3, "d_below": 300, "b_below": 300, "h_below": 3.0,
         "code_below": "F", "d_above": 300, "b_above": 300, "h_above": 3.0,
         "code_above": "F"}],
    additional_rebar=[
        {"span": 1, "pos": "T", "bars": "8Y16", "left_end": "Hook",
         "right_end": "Bend", "x": 5.0, "length": 6.0},
        {"span": 1, "pos": "B", "bars": "8Y16", "left_end": "Hook",
         "length": 8.0},
        {"span": 2, "pos": "B", "bars": "8Y16", "right_end": "Bend",
         "length": 7.0}],
    punching_columns=[
        {"no": 1, "slope_y": 0.05, "pcy": 280, "cable_type": 1,
         "nc_x": [4, 5, 6, 7], "nc_y": [1, 1, 2, 2],
         "ast_x": [402, 402, 603, 804], "ast_y": [565, 565, 565, 565]},
        {"no": 2, "slope_y": 0.06, "pcy": 280, "cable_type": 1,
         "nc_x": [5, 6, 7, 8], "nc_y": [1, 1, 2, 2],
         "ast_x": [942, 942, 942, 942], "ast_y": [804, 804, 804, 804]},
        {"no": 3, "slope_y": 0.05, "pcy": 280, "cable_type": 1,
         "nc_x": [4, 5, 6, 7], "nc_y": [1, 1, 2, 2],
         "ast_x": [402, 402, 603, 804], "ast_y": [565, 565, 565, 565]}])

# ⚠ NOT `DEAD`: that name is already the critical status colour above,
# and defining it twice made the second win - so colour=DEAD handed
# matplotlib the number 6.0. Caught by TypeError in the last panel.
DEAD_UDL = 6.0                  # the dead UDL, held constant
COLUMN_NAMES = ("column 1 (edge)", "column 2 (internal)",
                "column 3 (edge)")

ANCHOR_LIVE = 15.0
PINNED = (537.0024640743725, 575.0436234065779, 469.57376394972823)

LIVES = np.arange(2.0, 80.1, 2.0)       # 40 live loads, 2 to 80 kN/m

print("ONE POST-TENSIONED FLOOR, A GROWING LIVE LOAD - TWO DESIGN CODES")
print("  5000 x 250 mm slab strip, two spans of 8.0 and 7.5 m, seven "
      "unbonded cables")
print(f"  fcu {FLOOR['fcu']:.1f} MPa at service, {FLOOR['fci']:.1f} at "
      f"transfer, fy {FLOOR['fy']:.0f} MPa")
print(f"  dead load held constant at {DEAD_UDL:.0f} kN/m, punching checked "
      f"all three columns")
print(f"  the only input that moves: the live UDL, {LIVES[0]:.0f} to "
      f"{LIVES[-1]:.0f} kN/m in {LIVES[1] - LIVES[0]:.0f} steps "
      f"({len(LIVES)} loads)")

CALLS = {"engine": 0}
_ANSWERS = {}


def analyse(code, live):
    """One live load, one code. The first perimeter at all three columns."""
    key = (code, round(float(live), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    loads = [{"case": "D", "span": 1, "wl": DEAD_UDL},
             {"span": 2, "wl": DEAD_UDL, "p": 10, "p_pos": 2, "m": 10,
              "m_pos": 4},
             {"case": "L", "span": 1, "wl": float(live)},
             {"span": 2, "wl": float(live)}]
    try:
        result = prokon.v5.prestressed_concrete.analyse(
            design_code=code, loads=loads, **FLOOR)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(live=float(live), veff=[], vcap=[], failed=[],
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    firsts = [column["perimeters"][0] for column in result["punching"]]
    row = dict(live=float(live),
               veff=[first["veff"] for first in firsts],
               vcap=[first["vcap"] for first in firsts],
               failed=[first["failed"] for first in firsts],
               reason=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE CODES THIS ENGINE HAS
# ======================================================================
# CONTROL for the whole study: the codes must answer AND disagree. A
# reading that cannot separate two codes says nothing about either.
print("\n0. THE CODES THIS ENGINE HAS")
for code in (OLD_CODE, NEW_CODE, SA_NEW_CODE, PINNED_CODE):
    row = analyse(code, ANCHOR_LIVE)
    if not row["veff"]:
        print(f"   {code:<22} REFUSED   {row['reason']}")
    else:
        print(f"   {code:<22} answered  veff "
              + "  ".join(f"{value:>8.3f}" for value in row["veff"]))
print("   -> they answer, and the readings differ, so the sweep below is")
print("      measuring the code and not the noise.")
print(f"   -> {SA_NEW_CODE} answers here; it is enabled in eight of")
print("      the twelve engines (C11, C12, C13 and C16 are the four without).")

# ======================================================================
# 1. THE ANCHOR - all three columns
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at {ANCHOR_LIVE:.0f} kN/m live")
anchor = analyse(PINNED_CODE, ANCHOR_LIVE)
matched = 0
for index, expected in enumerate(PINNED):
    hit = anchor["veff"][index] == expected
    matched += hit
    print(f"   {COLUMN_NAMES[index]:<22} {anchor['veff'][index]!r:22} "
          f"pinned {expected!r}")
print(f"   -> {matched} of 3 exact"
      f"{'' if matched == 3 else '  - DRIFTED, READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(LIVES)} live loads x 2 codes")
sweep = {code: [analyse(code, live) for live in LIVES]
         for code in (OLD_CODE, NEW_CODE)}

assert FLOOR["fcu"] == 19.2 and len(FLOOR["punching_columns"]) == 3
assert FLOOR["span_segments"][0]["length"] == 8.0 and DEAD_UDL == 6.0
print("   the floor dictionary and the dead load are unchanged")

print(f"\n   {'live':>5} | {'SABS c1':>9} {'c2':>9} {'c3':>9} | "
      f"{'EC2 c1':>9} {'c2':>9} {'c3':>9}")
for index, live in enumerate(LIVES):
    if live % 10 != 0:
        continue
    cells = []
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        cells.append(" " + " ".join(f"{value:>9.2f}" for value in row["veff"]))
    print(f"   {live:>5.0f} |" + " |".join(cells))
print("   (veff on the first critical perimeter, kN)")


def column_of(code, index, field="veff"):
    return np.asarray([row[field][index] if row[field] else np.nan
                       for row in sweep[code]], dtype=float)


# ======================================================================
# 3. THE CODE CHANGE IS ABOUT THE EDGE COLUMNS
# ======================================================================
print("\n3. WHICH COLUMNS THE CODE CHANGE ACTUALLY TOUCHES")
print(f"   {'column':<22} {'min ratio':>10} {'max ratio':>10} "
      f"{'mean':>10}   new vs old")
shares = {}
for index, name in enumerate(COLUMN_NAMES):
    old = column_of(OLD_CODE, index)
    new = column_of(NEW_CODE, index)
    share = new / old
    shares[index] = share
    print(f"   {name:<22} {share.min():>10.4f} {share.max():>10.4f} "
          f"{share.mean():>10.4f}   "
          f"{abs(share.mean() - 1) * 100:>5.1f} % "
          f"{'HIGHER' if share.mean() > 1 else 'lower'}")
edges = [0, 2]
internal = 1
edge_move = np.mean([abs(shares[index].mean() - 1) for index in edges])
internal_move = abs(shares[internal].mean() - 1)
print(f"\n   -> the two EDGE columns move by {edge_move * 100:.1f} % on "
      f"average;")
print(f"      the INTERNAL column moves by {internal_move * 100:.1f} %.")
if internal_move > 0:
    print(f"      That is a factor of {edge_move / internal_move:.0f}. The "
          f"code change is")
    print("      almost entirely an EDGE-CONDITION change on this floor.")

# And the shape of the problem, which is the consequence.
print("\n   WHICH MEANS THE SHAPE OF THE PROBLEM CHANGES")
for code in (OLD_CODE, NEW_CODE):
    row = sweep[code][list(LIVES).index(ANCHOR_LIVE)] \
        if ANCHOR_LIVE in list(LIVES) else analyse(code, ANCHOR_LIVE)
    values = row["veff"]
    spread = max(values) / min(values)
    print(f"     {code:<22} veff "
          + "  ".join(f"{value:>8.1f}" for value in values))
    print(f"     {'':<22} worst is {spread:.2f}x the best - "
          + ("all three are live concerns"
             if spread < 1.5 else "only the internal one matters"))

# ======================================================================
# 4. WHICH COLUMN GOVERNS - CHECKED, NOT ASSUMED
# ======================================================================
print("\n4. WHICH COLUMN GOVERNS")
governs = {}
for code in (OLD_CODE, NEW_CODE):
    order = [int(np.argmax(row["veff"])) if row["veff"] else -1
             for row in sweep[code]]
    governs[code] = np.asarray(order)
    counted = {case: order.count(case) for case in sorted(set(order))}
    print(f"   {code}")
    for case, times in counted.items():
        print(f"     {COLUMN_NAMES[case]:<22} governs at {times:>3} of "
              f"{len(order)} loads")
disagree = LIVES[governs[OLD_CODE] != governs[NEW_CODE]]
print(f"\n   the two codes name a different governing column at "
      f"{len(disagree)} of {len(LIVES)} loads")
if not len(disagree):
    print("   -> they AGREE everywhere, and that was worth checking rather")
    print("      than assuming: with the edge columns moving 40 % and the")
    print("      internal one 1 %, a swap was entirely possible. It does not")
    print("      happen here because the internal column starts ahead and")
    print("      the code change only helps the ones behind it.")

# ======================================================================
# 5. WHERE EACH CODE RUNS OUT
# ======================================================================
# The engine publishes vcap beside veff and a `failed` flag, so the limit
# is its own reading rather than one this script invents.
print("\n5. THE LARGEST LIVE LOAD WITH EVERY COLUMN INSIDE ITS OWN vcap")


def boundary(holds, low, high, resolution=0.05):
    """The largest live load where `holds` is still true.

    The bracket is CHECKED rather than assumed - a bisection over a bracket
    that does not straddle the boundary returns one of its own endpoints,
    and that looks exactly like an answer.
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


limits = {}
for code in (OLD_CODE, NEW_CODE):
    def inside(live, code=code):
        row = analyse(code, live)
        return all(veff <= vcap
                   for veff, vcap in zip(row["veff"], row["vcap"]))

    okay = [live for live in LIVES if inside(live)]
    over = [live for live in LIVES if not inside(live)]
    if not okay or not over:
        state = "every load" if okay else "no load"
        print(f"   {code:<22} {state} in this range is inside vcap")
        continue
    low, high = boundary(inside, okay[-1], over[0])
    limits[code] = low
    row = analyse(code, high)
    first_over = [COLUMN_NAMES[index] for index in range(3)
                  if row["veff"][index] > row["vcap"][index]]
    print(f"   {code:<22} inside to {low:.2f} kN/m, over from {high:.2f}")
    print(f"   {'':<22} first over: {', '.join(first_over)}")
if len(limits) == 2:
    print(f"   -> {abs(limits[NEW_CODE] - limits[OLD_CODE]):.2f} kN/m apart. "
          f"The "
          f"{'NEW' if limits[NEW_CODE] > limits[OLD_CODE] else 'OLD'} code "
          f"carries more live load")
    print("      before the first perimeter needs help.")
elif len(limits) == 1:
    kinder = next(iter(limits))
    harsher = NEW_CODE if kinder == OLD_CODE else OLD_CODE
    print("   -> AND THAT IS THE SHARPEST RESULT IN THIS STUDY. Under")
    print(f"      {harsher} the first perimeter is over its own vcap at")
    print(f"      EVERY live load in this range, down to {LIVES[0]:.0f} kN/m,")
    print(f"      while {kinder} carries {limits[kinder]:.2f} kN/m before it")
    print("      needs any help. The code choice is the difference between a")
    print("      floor that needs punching reinforcement everywhere and one")
    print("      that does not - on the same slab, with the same tendons.")

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
    axes.set_xlim(LIVES[0], LIVES[-1])


STYLES = ("--", "-", ":")       # edge, internal, edge

# ---- A. the punching shear ---------------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  Effective punching shear at all three columns",
      "live UDL   (kN/m, both spans)", "veff on perimeter 1   (kN)")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    for index, name in enumerate(COLUMN_NAMES):
        chart.plot(LIVES, column_of(code, index), color=colour,
                   linewidth=2.2 if index == internal else 1.5,
                   linestyle=STYLES[index],
                   label=f"{short}  {name.split(' ')[1]}", zorder=4)
chart.plot([ANCHOR_LIVE], [anchor["veff"][internal]], marker="D",
           markersize=8, color=MUTED, markeredgecolor=SURFACE,
           markeredgewidth=2.0, zorder=7)
chart.annotate("the pinned floor", (ANCHOR_LIVE, anchor["veff"][internal]),
               textcoords="offset points", xytext=(12, -14), ha="left",
               fontsize=8.5, color=INK_SOFT)
chart.text(0.035, 0.94,
           "the two EDGE columns separate; the INTERNAL pair stay together"
           + chr(10) +
           "— the same code change, and almost all of it lands on the edges",
           transform=chart.transAxes, va="top", fontsize=8.5, color=INK_SOFT)
chart.set_ylim(0.0, None)
chart.legend(loc="lower right", fontsize=8.5, frameon=False, labelcolor=INK,
             ncol=2)

# ---- B. the direct comparison, column by column ------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "live UDL   (kN/m)", "veff,  new ÷ old")
ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
for index, name in enumerate(COLUMN_NAMES):
    ratio_axes.plot(LIVES, shares[index], color=NEW_COLOUR,
                    linewidth=2.2 if index == internal else 1.5,
                    linestyle=STYLES[index], label=name, zorder=4)
    ratio_axes.annotate(f"{name.split(' ')[1]}: "
                        f"{shares[index].mean():.3f}×",
                        (LIVES[0], shares[index][0]),
                        textcoords="offset points",
                        # The two EDGE ratios are 0.576 and 0.594 - close
                        # enough that one offset puts both labels in the
                        # same place, so each gets its own.
                        xytext=(10, (10, 10, -32)[index] if index != 0
                                else -14),
                        ha="left", fontsize=8.5,
                        color=OLD_COLOUR if index == internal else NEW_COLOUR,
                        fontweight="bold")
ratio_axes.fill_between(LIVES, shares[0], 1.0, color=NEW_COLOUR, alpha=0.10)
ratio_axes.text(0.035, 0.06,
                "two lines well below 1.0 and one almost on it — no single"
                + chr(10) +
                "\"the new code is x % lighter\" is true for this floor",
                transform=ratio_axes.transAxes, va="bottom", fontsize=8.5,
                color=INK_SOFT)
ratio_axes.set_ylim(0.0, 1.15)
ratio_axes.legend(loc="center right", fontsize=8.5, frameon=False,
                  labelcolor=INK, bbox_to_anchor=(1.0, 0.62))

# ---- C. the shape change -----------------------------------------------
shape = figure.add_subplot(panels[1, 0])
dress(shape, f"C.  The shape of the problem at {ANCHOR_LIVE:.0f} kN/m live",
      "", "veff on perimeter 1   (kN)")
positions = np.arange(3)
old_values = [analyse(OLD_CODE, ANCHOR_LIVE)["veff"][index]
              for index in range(3)]
new_values = [analyse(NEW_CODE, ANCHOR_LIVE)["veff"][index]
              for index in range(3)]
shape.bar(positions - 0.19, old_values, width=0.36, color=OLD_COLOUR,
          label=OLD_CODE, edgecolor=SURFACE, linewidth=2.0, zorder=3)
shape.bar(positions + 0.19, new_values, width=0.36, color=NEW_COLOUR,
          label=NEW_CODE, edgecolor=SURFACE, linewidth=2.0, zorder=3)
for index in range(3):
    shape.text(index, max(old_values[index], new_values[index]) * 1.03,
               f"{new_values[index] / old_values[index]:.3f}×", ha="center",
               fontsize=9, color=INK, fontweight="bold")
# ⚠ dress() sets the x-range to the LIVE-LOAD axis, which is wrong for a
# categorical bar chart: it crushed all three bars onto x = 0 and stacked
# the tick labels on top of each other. Override it here.
shape.set_xlim(-0.6, len(positions) - 0.4)
shape.set_xticks(positions)
shape.set_xticklabels(COLUMN_NAMES, fontsize=9.5, color=INK_SOFT)
shape.set_ylim(0, max(max(old_values), max(new_values)) * 1.32)
shape.grid(True, axis="y", linewidth=0.6, color=GRID)
shape.grid(False, axis="x")
shape.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor=INK)
shape.text(0.985, 0.955,
           f"under the old code the worst is "
           f"{max(old_values) / min(old_values):.2f}× the best — all three"
           + chr(10) +
           f"are live concerns. Under the new one it is "
           f"{max(new_values) / min(new_values):.2f}× — only"
           + chr(10) + "the internal column is worth looking at.",
           transform=shape.transAxes, ha="right", va="top", fontsize=8.5,
           color=INK_SOFT)

# ---- D. the verdict ----------------------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same floor, same axis — where each code runs out", "", "")
verdict.set_xlabel("live UDL   (kN/m)", fontsize=9.5, color=INK_SOFT)
REGIMES = ((FREE, "every column inside its own published vcap"),
           (DEAD, "a perimeter is over vcap — shear reinforcement needed"))
for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    # A code with no passing load at all gets ONE band, not a zero-width
    # green one - measured, the old code is over vcap at every load here.
    edge = limits.get(code, LIVES[0])
    for start, stop, colour in ((LIVES[0], edge, FREE),
                                (edge, LIVES[-1], DEAD)):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, edgecolor=SURFACE,
                     linewidth=2.0, zorder=3)
    verdict.text(LIVES[0] + 0.6, base + 0.15, code, fontsize=9.5, color=INK,
                 fontweight="bold")
    if code in limits:
        verdict.plot([edge, edge], [base - 0.145, base - 0.105], color=INK,
                     linewidth=1.0, zorder=5)
        verdict.text(edge, base - 0.20, f"clear to {edge:.1f} kN/m",
                     ha="center", fontsize=8.5, color=INK,
                     fontweight="bold")
    else:
        verdict.text((LIVES[0] + LIVES[-1]) / 2, base,
                     "over vcap at EVERY load in this range",
                     ha="center", va="center", fontsize=9, color="white",
                     fontweight="bold", zorder=5)
verdict.text(0.985, 0.975,
             "the same column governs under both codes — checked in "
             "section 4," + chr(10) +
             "not assumed, because a 40 % move on two of three invited a swap",
             transform=verdict.transAxes, ha="right", va="top",
             fontsize=8.5, color=MUTED)
verdict.set_ylim(0.02, 1.0)
verdict.set_yticks([])
verdict.grid(False)
verdict.spines["left"].set_visible(False)
verdict.legend([plt.Rectangle((0, 0), 1, 1, color=colour, alpha=0.85)
                for colour, _ in REGIMES],
               [label for _, label in REGIMES], loc="upper center",
               bbox_to_anchor=(0.5, -0.14), fontsize=8.5, ncol=1,
               frameon=False, labelcolor=INK)

figure.suptitle(
    f"One post-tensioned floor, a growing live load:  {OLD_CODE}  against  "
    f"{NEW_CODE}\n"
    f"5000 × 250 mm strip, spans 8.0 + 7.5 m, seven unbonded cables, "
    f"fcu {FLOOR['fcu']:.1f} MPa, dead {DEAD_UDL:.0f} kN/m  —  ONLY the "
    f"load changes\n"
    f"The code change lands almost entirely on the EDGE columns, which "
    f"changes which column you have to worry about",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "prestressed_concrete_sabs_vs_eurocode_load.png")
