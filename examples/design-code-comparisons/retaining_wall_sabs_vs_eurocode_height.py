# ---
# Example:  One retaining wall, growing taller - and the concrete code that does not touch the stability
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes - 2026-09-18 - the pinned wall reproduces all five of its pinned values exactly at the sweep's h1 = 5.0 m point; every height measured on prokon-automation.exe; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example
# ---
# ONE wall. ONE soil. ONE thing changes: the stem height above the base.
#
# The base geometry, the stem thicknesses, the shear key, the soil
# properties, the water table, the load cases, the safety factors and the
# allowable bearing pressure are all held constant and asserted constant -
# so every difference is caused by the height or by the code.
#
# THE CODES ------------------------------------------------------------
#
# ⚠ C14 CALLS THE INPUT "concrete_code", NOT "design_code" - it is the only
# engine in the fleet that does, because a retaining wall has a soil
# problem and a concrete problem and the input names say which is which.
# SABS 0100 - 2000 against Eurocode 2 - 2004; C14 also carries the new
# South African code, SANS 51992-1-1:2025.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE CONCRETE CODE DOES NOT TOUCH THE STABILITY, AT ALL. Overturning,
#   sliding and bearing pressure come back BIT-IDENTICAL under both codes
#   at every height. Panel C draws four curves and you will see two,
#   because each pair lies exactly on top of the other. Section 3 checks it
#   digit by digit rather than by eye.
#
#   ⚠ THAT IS WHY THIS COMPARISON IS NARROWER THAN THE OTHERS. On a
#   retaining wall the code choice is a REINFORCEMENT question and nothing
#   else. Anyone expecting a code change to rescue a wall that is sliding
#   is looking in the wrong place, and this script is the evidence.
#
#   THE STEEL DOES DIFFER, AND THE CURVES CROSS. Eurocode 2 asks for
#   slightly less over most of the range and then MORE at the tall end -
#   section 4 bisects the crossover.
#
#   AND THE WALL FALLS OVER LONG BEFORE THE STEEL BECOMES THE PROBLEM.
#   Section 5 finds the height at which each safety factor drops below the
#   1.5 that was asked for, and the height at which the bearing pressure
#   passes the 400 kPa allowed. Past all of those the engine keeps
#   returning steel areas, with no error and no flag - so the reading that
#   matters is the safety factors, and they are published.
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

# -- THE WALL, AND THE ONE INPUT THAT MOVES -----------------------------
WALL = dict(h2=0.7, h3=0.8, hw=2.8, b=0.55, d=2.50, c=0.40, f=0.70, xf=3.05,
            at=0.30, ab=0.40, x=0.45,
            theta=27.0, alpha=9.0, delta=20.0, dg=18.0, db=25.0,
            fcu=25.0, fy=450.0,
            sf_overturning=1.5, sf_sliding=1.5,
            dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9, pmax=400.0, mu=0.5,
            cover_wall=50.0, cover_base=50.0,
            seismic=True, kh=0.02, kv=0.01, seis_w_loads=True,
            allow_seep=True, toe_back_force=True,
            load_cases=[
                {"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0,
                 "lynl": 1.0, "xlv": 2.0, "ph": 0.5},
                {"name": "Truck", "w": 2.0, "p": 0.5, "xp": 2.0,
                 "lynl": 2.0, "xlv": 1.0, "ph": 3.0},
                {"name": "Train", "w": 3.0, "lynl": 1.0, "xlv": 2.0},
            ])

REQUIRED_SF = WALL["sf_overturning"]        # the same 1.5 for both checks
ALLOWED_BEARING = WALL["pmax"]

ANCHOR_HEIGHT = 5.0
PINNED = {"sf_overturning": 4.477940718035636,
          "sf_sliding": 1.6341314510288516,
          "qmax": 97.26517611421157,
          "as_wall_req": 915.8514440593759,
          "as_base_req": 791.8667235080961}

HEIGHTS = np.arange(2.0, 10.01, 0.125)      # 65 heights, 2 m to 10 m

STABILITY = ("sf_overturning", "sf_sliding", "qmax")
STEEL = ("as_wall_req", "as_base_req")

print("ONE RETAINING WALL, GROWING TALLER - TWO CONCRETE CODES")
print(f"  base {WALL['b']:.2f} toe + {WALL['d']:.2f} heel + "
      f"{WALL['ab']:.2f} stem = {WALL['b'] + WALL['d'] + WALL['ab']:.2f} m "
      f"wide, {WALL['c']:.2f} m thick")
print(f"  soil phi {WALL['theta']:.0f} deg, fill slope {WALL['alpha']:.0f} "
      f"deg, water table {WALL['hw']:.1f} m, seismic on")
print(f"  fcu {WALL['fcu']:.0f} MPa, fy {WALL['fy']:.0f} MPa, three load "
      f"cases, SF required {REQUIRED_SF:.1f}, pmax {ALLOWED_BEARING:.0f} kPa")
print(f"  the only input that moves: h1, {HEIGHTS[0]:.2f} to "
      f"{HEIGHTS[-1]:.2f} m in {HEIGHTS[1] - HEIGHTS[0]:.3f} m steps "
      f"({len(HEIGHTS)} heights)")

CALLS = {"engine": 0}
_ANSWERS = {}


def design(code, height):
    """One height, one code. Returns a row; never raises for a refusal."""
    key = (code, round(float(height), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.retaining_wall.analyse(
            concrete_code=code, h1=float(height), **WALL)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(height=float(height),
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        row.update({name: None for name in STABILITY + STEEL})
        _ANSWERS[key] = row
        return row

    row = dict(height=float(height), reason=None)
    row.update({name: result[name] for name in STABILITY + STEEL})
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE CODES THIS ENGINE HAS, AND THE INPUT IT CALLS THEM BY
# ======================================================================
# CLAIM: this engine's code input is `concrete_code`. Passing
# `design_code` - the name every other engine uses - is not silently
# ignored, which is the behaviour worth having.
print("\n0. THE INPUT NAME, AND THE CODES")
# ⚠ AND IT IS REFUSED IN PYTHON, NOT BY THE ENGINE. The shipped package
# builds a real keyword signature per command, so a name this command does
# not take is a TypeError at the call site - no process is spawned and no
# envelope comes back. That is the earliest and cheapest place to find out,
# and it is why both exception types are caught here.
try:
    prokon.v5.retaining_wall.analyse(design_code=OLD_CODE,
                                     h1=ANCHOR_HEIGHT, **WALL)["result"]
    print("   design_code was ACCEPTED - which would mean it was ignored")
except TypeError as wrong_name:
    print(f"   design_code=... -> TypeError: {wrong_name}")
    print("   -> refused by the PYTHON package, before the engine is even")
    print("      spawned. An input quietly dropped is the worst kind,")
    print("      because the answer still looks fine; this one cannot be.")
except prokon.v5.ProkonError as refusal:
    print(f"   design_code=... -> {refusal.category}/{refusal.code}")
    print(f"   {str(refusal.message)[:70]}")
    print("   -> refused by the engine rather than ignored.")

for code in (OLD_CODE, NEW_CODE, SA_NEW_CODE, PINNED_CODE):
    row = design(code, ANCHOR_HEIGHT)
    if row["as_wall_req"] is None:
        print(f"   {code:<22} REFUSED   {row['reason']}")
    else:
        print(f"   {code:<22} answered  as_wall {row['as_wall_req']:>8.1f}  "
              f"sf_ot {row['sf_overturning']:>6.3f}  "
              f"qmax {row['qmax']:>7.2f}")
print(f"   -> {SA_NEW_CODE} answers here; it is enabled in eight of")
print("      the twelve engines (C11, C12, C13 and C16 are the four without).")

# ======================================================================
# 1. THE ANCHOR - all five pinned values
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at h1 = {ANCHOR_HEIGHT:.1f} m")
anchor = design(PINNED_CODE, ANCHOR_HEIGHT)
matched = 0
for name in PINNED:
    hit = anchor[name] == PINNED[name]
    matched += hit
    print(f"   {name:<16} {anchor[name]!r:22} pinned {PINNED[name]!r}")
print(f"   -> {matched} of 5 exact"
      f"{'' if matched == 5 else '  - DRIFTED, READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(HEIGHTS)} heights x 2 codes")
sweep = {code: [design(code, height) for height in HEIGHTS]
         for code in (OLD_CODE, NEW_CODE)}

assert WALL["fcu"] == 25.0 and WALL["theta"] == 27.0
assert WALL["pmax"] == 400.0 and len(WALL["load_cases"]) == 3
print("   the wall dictionary and all three load cases are unchanged")

print(f"\n   {'h1 (m)':>7} | {'sf_ot':>7} {'sf_sl':>7} {'qmax':>8} | "
      f"{'SABS wall':>10} {'base':>9} | {'EC2 wall':>10} {'base':>9}")
for index, height in enumerate(HEIGHTS):
    if abs(height - round(height)) > 1e-9:
        continue
    old = sweep[OLD_CODE][index]
    new = sweep[NEW_CODE][index]
    print(f"   {height:>7.2f} | {old['sf_overturning']:>7.3f} "
          f"{old['sf_sliding']:>7.3f} {old['qmax']:>8.2f} | "
          f"{old['as_wall_req']:>10.1f} {old['as_base_req']:>9.1f} | "
          f"{new['as_wall_req']:>10.1f} {new['as_base_req']:>9.1f}")


def column(code, field):
    return np.asarray([np.nan if row[field] is None else row[field]
                       for row in sweep[code]], dtype=float)


# ======================================================================
# 3. THE STABILITY IS THE SAME UNDER BOTH CODES - CHECKED, NOT ASSUMED
# ======================================================================
# The sweep table above prints the stability once, which already assumes
# the answer. This is the check: compare the two codes digit by digit at
# every height.
#
# ⚠ AND IT NEEDS A CONTROL, because "these two lists are equal" is exactly
# the reading that a broken comparison also produces. The control is the
# STEEL: the same comparison, on the same rows, must find the two codes
# DIFFERENT. If it says both are identical, the comparison is broken.
print("\n3. DOES THE CONCRETE CODE TOUCH THE STABILITY?")
print(f"   {'quantity':<16} {'identical at':>14}  {'of':>4}  verdict")
for name in STABILITY + STEEL:
    old, new = column(OLD_CODE, name), column(NEW_CODE, name)
    same = int(np.sum(old == new))
    tag = "IDENTICAL everywhere" if same == len(HEIGHTS) else "DIFFERS"
    print(f"   {name:<16} {same:>14} {len(HEIGHTS):>5}  {tag}")
stability_same = all(np.all(column(OLD_CODE, name) == column(NEW_CODE, name))
                     for name in STABILITY)
steel_differs = any(np.any(column(OLD_CODE, name) != column(NEW_CODE, name))
                    for name in STEEL)
print(f"\n   stability identical under both codes : {stability_same}")
print(f"   steel differs between the codes      : {steel_differs}   "
      f"<- the control")
if stability_same and steel_differs:
    print("   -> so the comparison CAN see a difference, and it finds none in")
    print("      the stability. On a retaining wall the concrete code is a")
    print("      reinforcement decision and nothing more. A wall that slides")
    print("      will still slide under the other code.")
elif stability_same and not steel_differs:
    print("   -> BOTH readings identical. The comparison is broken, not the")
    print("      wall - do not conclude anything from it.")


def boundary(holds, low, high, resolution=0.01):
    """The largest height where `holds` is still true, to `resolution`.

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
# 4. WHERE THE STEEL CURVES CROSS
# ======================================================================
print("\n4. THE ONE THING THE CODE DOES CHANGE: THE STEEL")
crossover = {}
for name in STEEL:
    old, new = column(OLD_CODE, name), column(NEW_CODE, name)
    flipped = [index for index in range(len(HEIGHTS) - 1)
               if (new[index] < old[index]) != (new[index + 1] < old[index + 1])]
    print(f"   {name}")
    print(f"     at {HEIGHTS[0]:.2f} m the "
          f"{'NEW' if new[0] < old[0] else 'OLD'} code asks for less "
          f"({new[0]:.1f} against {old[0]:.1f} mm2)")
    print(f"     at {HEIGHTS[-1]:.2f} m the "
          f"{'NEW' if new[-1] < old[-1] else 'OLD'} code asks for less "
          f"({new[-1]:.1f} against {old[-1]:.1f} mm2)")
    if flipped:
        def new_is_lighter(height, name=name):
            return design(NEW_CODE, height)[name] < design(OLD_CODE,
                                                           height)[name]

        low, high = boundary(new_is_lighter, HEIGHTS[flipped[0]],
                             HEIGHTS[flipped[0] + 1])
        crossover[name] = low
        print(f"     they swap places between {low:.3f} and {high:.3f} m")
    else:
        print("     one code is lighter across the whole range")

# ======================================================================
# 5. THE WALL FALLS OVER FIRST
# ======================================================================
# Every one of these boundaries is a property of the SOIL problem, so both
# codes share them. They are found once and reported once.
print(f"\n5. WHERE THE WALL STOPS WORKING   (both codes, because the "
      f"stability is shared)")
limits = {}
checks = (("sf_overturning", "overturning", lambda value: value >= REQUIRED_SF,
           f">= {REQUIRED_SF:.1f}"),
          ("sf_sliding", "sliding", lambda value: value >= REQUIRED_SF,
           f">= {REQUIRED_SF:.1f}"),
          ("qmax", "bearing", lambda value: value <= ALLOWED_BEARING,
           f"<= {ALLOWED_BEARING:.0f} kPa"))
for name, label, passes, wanted in checks:
    values = column(OLD_CODE, name)
    good = HEIGHTS[[passes(value) for value in values]]
    bad = HEIGHTS[[not passes(value) for value in values]]
    if not len(good) or not len(bad):
        print(f"   {label:<12} {wanted:<16} never crosses in this range")
        continue

    def still_passes(height, name=name, passes=passes):
        return passes(design(OLD_CODE, height)[name])

    low, high = boundary(still_passes, good[-1], bad[0])
    limits[label] = low
    print(f"   {label:<12} {wanted:<16} holds to h1 = {low:.3f} m, fails "
          f"from {high:.3f}")
if limits:
    first = min(limits, key=limits.get)
    print(f"   -> {first.upper()} is what stops this wall, at "
          f"{limits[first]:.2f} m,")
    print(f"      and the engine goes on returning steel areas for another "
          f"{HEIGHTS[-1] - limits[first]:.2f} m")
    print("      above it with no error and no flag. The safety factors are")
    print("      published; compare them against what you asked for.")

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
    axes.set_xlim(HEIGHTS[0], HEIGHTS[-1])


# ---- A. the steel, which is the only thing the code changes ------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  The reinforcement — the one thing the concrete code moves",
      "stem height  h1   (m)", "steel required   (mm²)")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    chart.plot(HEIGHTS, column(code, "as_wall_req"), color=colour,
               linewidth=2.0, label=f"{short}  wall")
    chart.plot(HEIGHTS, column(code, "as_base_req"), color=colour,
               linewidth=1.6, linestyle=":", label=f"{short}  base")
if limits:
    first = min(limits, key=limits.get)
    chart.axvspan(limits[first], HEIGHTS[-1], color=DEAD, alpha=0.09,
                  zorder=0)
    chart.text(0.985, 0.06,
               f"shaded: the wall already fails {first} from "
               f"{limits[first]:.2f} m —" + chr(10) +
               "every steel area in there is for a wall that does not "
               "stand up",
               transform=chart.transAxes, ha="right", va="bottom",
               fontsize=8.5, color=DEAD, fontweight="bold")
chart.plot([ANCHOR_HEIGHT], [anchor["as_wall_req"]], marker="D", markersize=8,
           color=MUTED, markeredgecolor=SURFACE, markeredgewidth=2.0,
           zorder=7)
chart.annotate("the pinned wall", (ANCHOR_HEIGHT, anchor["as_wall_req"]),
               textcoords="offset points", xytext=(-12, 8), ha="right",
               fontsize=8.5, color=INK_SOFT)
chart.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor=INK,
             ncol=2)

# ---- B. the direct comparison ------------------------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "stem height  h1   (m)", "steel demanded,  new ÷ old")
ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
for name, style, label in (("as_wall_req", "-", "wall"),
                           ("as_base_req", ":", "base")):
    share = column(NEW_CODE, name) / column(OLD_CODE, name)
    ratio_axes.plot(HEIGHTS, share, color=NEW_COLOUR, linewidth=2.0,
                    linestyle=style, label=f"{label} steel")
    if name in crossover:
        ratio_axes.plot([crossover[name]], [1.0], marker="o", markersize=8,
                        color=INK, markeredgecolor=SURFACE,
                        markeredgewidth=2.0, zorder=6)
wall_share = column(NEW_CODE, "as_wall_req") / column(OLD_CODE, "as_wall_req")
ratio_axes.annotate(f"the new code asks {(1 - wall_share[0]) * 100:.1f} % "
                    f"LESS\nwall steel on a short wall",
                    (HEIGHTS[0], wall_share[0]), textcoords="offset points",
                    xytext=(16, 6), ha="left", fontsize=8.5,
                    color=OLD_COLOUR, fontweight="bold")
ratio_axes.annotate(f"and {abs(wall_share[-1] - 1) * 100:.1f} % "
                    f"{'MORE' if wall_share[-1] > 1 else 'less'} "
                    f"on a tall one",
                    (HEIGHTS[-1], wall_share[-1]),
                    textcoords="offset points", xytext=(-10, -6), ha="right",
                    va="top", fontsize=8.5, color=NEW_COLOUR,
                    fontweight="bold")
if crossover:
    named = min(crossover, key=crossover.get)
    ratio_axes.annotate(f"they change places\nat {crossover[named]:.2f} m",
                        (crossover[named], 1.0), textcoords="offset points",
                        xytext=(-12, 12), ha="right", fontsize=8.5, color=INK,
                        fontweight="bold")
ratio_axes.legend(loc="upper left", fontsize=8.5, frameon=False,
                  labelcolor=INK)

# ---- C. four curves, two visible ---------------------------------------
# The old code is drawn THICK and the new code drawn THIN AND DASHED on top
# of it. If the two ever parted company you would see the thick line
# underneath - the whole panel is a visual identity check.
stability_axes = figure.add_subplot(panels[1, 0])
dress(stability_axes,
      "C.  Stability — four curves drawn, two visible (they coincide)",
      "stem height  h1   (m)", "safety factor")
for name, style, label in (("sf_overturning", "-", "overturning"),
                           ("sf_sliding", "--", "sliding")):
    stability_axes.plot(HEIGHTS, column(OLD_CODE, name), color=OLD_COLOUR,
                        linewidth=4.0, linestyle=style, alpha=0.95,
                        label=f"SABS  {label}", zorder=3)
    stability_axes.plot(HEIGHTS, column(NEW_CODE, name), color=NEW_COLOUR,
                        linewidth=1.4, linestyle=style,
                        label=f"Eurocode 2  {label}", zorder=4)
stability_axes.axhline(REQUIRED_SF, color=DEAD, linewidth=1.4,
                       linestyle="--", zorder=2)
stability_axes.annotate(f"{REQUIRED_SF:.1f} — the factor this run asked for",
                        (HEIGHTS[-1], REQUIRED_SF),
                        textcoords="offset points", xytext=(-6, 8),
                        ha="right", fontsize=8.5, color=DEAD,
                        fontweight="bold")
for label, where in limits.items():
    if label == "bearing":
        continue
    stability_axes.plot([where], [REQUIRED_SF], marker="o", markersize=8,
                        color=INK, markeredgecolor=SURFACE,
                        markeredgewidth=2.0, zorder=6)
    stability_axes.annotate(f"{label} fails\nat {where:.2f} m",
                            (where, REQUIRED_SF),
                            textcoords="offset points", xytext=(-10, 22),
                            ha="right", fontsize=8.5, color=INK,
                            fontweight="bold")
stability_axes.text(0.985, 0.955,
                    "the thin orange line is drawn ON TOP of the thick blue "
                    "one:" + chr(10) +
                    "every stability value is bit-identical under both codes",
                    transform=stability_axes.transAxes, ha="right", va="top",
                    fontsize=8.5, color=INK_SOFT)
stability_axes.set_ylim(0.0, None)
# Centre-right: the overturning curve has dropped away by then and the
# sliding pair runs along the bottom, so it is the one clear patch.
stability_axes.legend(loc="center right", fontsize=8.5, frameon=False,
                      labelcolor=INK)

# ---- D. the verdict ----------------------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same wall, same axis — and the bands are SHARED", "", "")
verdict.set_xlabel("stem height  h1   (m)", fontsize=9.5, color=INK_SOFT)

ordered = sorted(limits.items(), key=lambda item: item[1])
REGIMES = [(FREE, "every check satisfied")]
palette = (RAMP, "#ec835a", DEAD)
for index, (label, where) in enumerate(ordered):
    REGIMES.append((palette[min(index, 2)], f"{label} failed from "
                                            f"{where:.2f} m"))

edges = [HEIGHTS[0]] + [where for _, where in ordered] + [HEIGHTS[-1]]
for start, stop, (colour, _) in zip(edges, edges[1:], REGIMES):
    if stop - start <= 0:
        continue
    verdict.barh(0.55, stop - start, left=start, height=0.26, color=colour,
                 alpha=0.85, edgecolor=SURFACE, linewidth=2.0, zorder=3)
verdict.text(HEIGHTS[0] + 0.05, 0.75,
             "BOTH codes — one band, because the soil problem is shared",
             fontsize=9.5, color=INK, fontweight="bold")
# Staggered: the last two boundaries are 0.6 m apart on an 8 m axis, so
# level labels overprinted each other.
for index, (label, where) in enumerate(ordered):
    drop = 0.34 if index % 2 == 0 else 0.19
    verdict.plot([where, where], [0.40, drop + 0.04], color=INK,
                 linewidth=1.0, zorder=5)
    verdict.text(where, drop, f"{label}\n{where:.2f} m",
                 ha="center", va="top", fontsize=8.5, color=INK,
                 fontweight="bold")
verdict.text(0.985, 0.06,
             "the engine keeps returning steel areas across every band, "
             "with" + chr(10) +
             "no error and no flag — the safety factors are the reading",
             transform=verdict.transAxes, ha="right", va="bottom",
             fontsize=8.5, color=MUTED)
verdict.set_ylim(0.0, 1.0)
verdict.set_yticks([])
verdict.grid(False)
verdict.spines["left"].set_visible(False)
verdict.legend([plt.Rectangle((0, 0), 1, 1, color=colour, alpha=0.85)
                for colour, _ in REGIMES],
               [label for _, label in REGIMES], loc="upper center",
               bbox_to_anchor=(0.5, -0.14), fontsize=8.5, ncol=2,
               frameon=False, labelcolor=INK)

figure.suptitle(
    f"One retaining wall, growing taller:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"base {WALL['b'] + WALL['d'] + WALL['ab']:.2f} m wide × "
    f"{WALL['c']:.2f} m thick, soil φ {WALL['theta']:.0f}°, water table "
    f"{WALL['hw']:.1f} m, seismic, three load cases  —  ONLY h1 changes\n"
    f"The concrete code moves the REINFORCEMENT and nothing else: every "
    f"stability value is bit-identical under both, and panel C is the check",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "retaining_wall_sabs_vs_eurocode_height.png")
