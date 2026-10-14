# ---
# Example:  One pad footing, growing wider - where the code matters and where the soil has already decided
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes - 2026-09-07 - the golden 2.5 x 2.5 x 0.6 m footing reproduces its pinned sls pressure, uls pressure and vcx exactly at the sweep's 2.5 m point; every size measured on prokon-automation.exe
# ---
# ONE footing. ONE column. ONE load case. ONE thing changes: the plan size,
# kept square.
#
# The depth (0.6 m), the soil cover (0.5 m), the column (0.4 x 0.4 m,
# concentric), the concrete (fcu 30), the steel (fy 450), the detailed bars
# and the load are held constant and asserted constant - so every
# difference is caused by the plan size or by the code.
#
# THE CODES ------------------------------------------------------------
#
# SABS 0100 - 2000 against Eurocode 2 - 2004. C15 also carries the new
# South African code, SANS 51992-1-1:2025, and section 0 shows it
# answering. ⚠ There is no "Eurocode 2 - 2005" anywhere in the fleet.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE BEARING PRESSURE IS THE SAME UNDER BOTH CODES, AT EVERY SIZE. Like
#   the retaining wall's stability, this is a soil problem: the concrete
#   code cannot touch it. Section 3 checks it digit by digit AND runs the
#   steel through the same comparison as a control, so "identical" is a
#   finding rather than a broken test.
#
#   SO THE CODE ONLY MOVES TWO THINGS: the flexural steel, and the shear
#   capacity of the concrete. And the second one is the interesting one -
#   Eurocode 2 allows 39 % more shear stress on this footing, and it does
#   not vary with the plan size at all, because it is a property of the
#   depth and the concrete.
#
#   AND YET BOTH CODES ALLOW EXACTLY THE SAME SMALLEST FOOTING: 2.013 m
#   square, measured and bisected to 5 mm. That is the result worth having,
#   and it is a NEGATIVE one. Panel C puts every check on one dimensionless
#   axis - demand divided by what that check allows, so 1.0 is the limit
#   whatever the units - and on this footing BEARING is the check that
#   crosses 1.0 first, by a distance: shear and punching never get above
#   0.55 anywhere in the range. So the 39 % shear difference is real,
#   published, and completely irrelevant to the answer. Change the depth or
#   the concrete and it would start to matter; here it cannot.
#
#   ⚠ AND THE PUNCHING CHECK IS NOT REPORTED AT EVERY SIZE. vcp comes back
#   as exactly 0 at 18 sizes under the old code and 28 under the new one.
#   Dividing by it raises ZeroDivisionError - which is how this was found -
#   and treating the 0 as a capacity would be worse: the utilisation would
#   read as infinite and the check would look catastrophically failed when
#   it was simply not reported. Section 4 counts the gaps out loud.
#
#   AND THE ENGINE NEVER REFUSES A FOOTING THAT IS FAR TOO SMALL. At 1.20 m
#   square this footing is 2.86 times over its allowable bearing pressure,
#   and the result still comes back with steel areas and no error. The
#   pressures are published; compare them against what you allowed.
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
SHARED_COLOUR = "#1baf7a"   # categorical slot 3 - the soil check both share
FREE = "#0ca30c"
RAMP = "#fab219"
DEAD = "#d03b3b"

# -- THE FOOTING, AND THE ONE INPUT THAT MOVES --------------------------
FOOTING = dict(yf=0.6, z=0.5, c1=0.4, d1=0.4, e1=0.0, f1=0.0,
               fcu=30.0, fy=450.0, allowable_bearing_pressure=200.0,
               bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
               bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
               bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
               bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
               load_cases=[{"name": "LC1", "pa1": 600.0, "hx1": 30.0,
                            "mx1": 20.0, "lf1": 1.4}])
ALLOWED_BEARING = FOOTING["allowable_bearing_pressure"]

ANCHOR_SIZE = 2.5
PINNED = {"sls": 133.98908218356328, "uls": 182.9047150569886,
          "vcx": 0.3568429018580138}

SIZES = np.arange(1.20, 4.51, 0.05)         # 67 sizes, 1.2 m to 4.5 m square

print("ONE PAD FOOTING, GROWING WIDER - TWO DESIGN CODES")
print(f"  {FOOTING['yf']:.2f} m deep, {FOOTING['z']:.2f} m of cover over it, "
      f"{FOOTING['c1']:.2f} x {FOOTING['d1']:.2f} m column, concentric")
print(f"  fcu {FOOTING['fcu']:.0f} MPa, fy {FOOTING['fy']:.0f} MPa, "
      f"allowable bearing {ALLOWED_BEARING:.0f} kPa")
print(f"  one load case: {FOOTING['load_cases'][0]['pa1']:.0f} kN axial, "
      f"{FOOTING['load_cases'][0]['hx1']:.0f} kN horizontal, "
      f"{FOOTING['load_cases'][0]['mx1']:.0f} kNm, factor "
      f"{FOOTING['load_cases'][0]['lf1']:.1f}")
print(f"  the only input that moves: a = b, {SIZES[0]:.2f} to "
      f"{SIZES[-1]:.2f} m in {SIZES[1] - SIZES[0]:.2f} m steps "
      f"({len(SIZES)} sizes)")

CALLS = {"engine": 0}
_ANSWERS = {}
STEEL = ("as_x", "as_y")
SHEAR = ("vx", "vcx", "vy", "vcy", "vp", "vcp")


def design(code, size):
    """One plan size, one code. Returns a row; never raises for a refusal."""
    key = (code, round(float(size), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    blank = dict(size=float(size), sls=None, uls=None)
    blank.update({name: None for name in STEEL + SHEAR})
    try:
        result = prokon.v5.pad_footing.analyse(
            design_code=code, a=float(size), b=float(size), **FOOTING)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(blank, reason=f"{refusal.category}/{refusal.code}: "
                                 f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    case = result["load_cases"][0]
    row = dict(size=float(size),
               sls=result["max_bearing_pressure_sls"],
               uls=result["max_bearing_pressure"], reason=None)
    row.update({name: case["reinforcement"][name] for name in STEEL})
    row.update({name: case["shear"][name] for name in SHEAR})
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE CODES THIS ENGINE HAS
# ======================================================================
# CONTROL for the whole study: the codes must answer AND disagree
# somewhere. A reading that cannot separate them says nothing about either.
print("\n0. THE CODES THIS ENGINE HAS")
for code in (OLD_CODE, NEW_CODE, SA_NEW_CODE, PINNED_CODE):
    row = design(code, ANCHOR_SIZE)
    if row["as_x"] is None:
        print(f"   {code:<22} REFUSED   {row['reason']}")
    else:
        print(f"   {code:<22} answered  as_x {row['as_x']:>8.2f}  "
              f"vcx {row['vcx']:>7.4f}  sls {row['sls']:>8.3f}")
print("   -> they answer, and the steel and shear readings differ while the")
print("      pressure does not. That split is the whole study.")
print(f"   -> {SA_NEW_CODE} answers here; it is enabled in eight of")
print("      the twelve engines (C11, C12, C13 and C16 are the four without).")

# ======================================================================
# 1. THE ANCHOR
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at {ANCHOR_SIZE:.2f} m square")
anchor = design(PINNED_CODE, ANCHOR_SIZE)
found = {"sls": anchor["sls"], "uls": anchor["uls"], "vcx": anchor["vcx"]}
matched = 0
for name in ("sls", "uls", "vcx"):
    hit = found[name] == PINNED[name]
    matched += hit
    print(f"   {name:<5} {found[name]!r:22} pinned {PINNED[name]!r}")
print(f"   -> {matched} of 3 exact"
      f"{'' if matched == 3 else '  - DRIFTED, READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(SIZES)} sizes x 2 codes")
sweep = {code: [design(code, size) for size in SIZES]
         for code in (OLD_CODE, NEW_CODE)}

assert FOOTING["yf"] == 0.6 and FOOTING["fcu"] == 30.0
assert FOOTING["load_cases"][0]["pa1"] == 600.0
assert FOOTING["allowable_bearing_pressure"] == 200.0
print("   the footing dictionary and the load case are unchanged")

print(f"\n   {'a=b (m)':>8} {'sls kPa':>9} {'uls kPa':>9} | "
      f"{'SABS as_x':>10} {'vx':>7} {'vcx':>7} | "
      f"{'EC2 as_x':>10} {'vx':>7} {'vcx':>7}")
for index, size in enumerate(SIZES):
    if abs(size * 100 % 50) > 1e-6:
        continue
    old, new = sweep[OLD_CODE][index], sweep[NEW_CODE][index]
    print(f"   {size:>8.2f} {old['sls']:>9.2f} {old['uls']:>9.2f} | "
          f"{old['as_x']:>10.1f} {old['vx']:>7.4f} {old['vcx']:>7.4f} | "
          f"{new['as_x']:>10.1f} {new['vx']:>7.4f} {new['vcx']:>7.4f}")


def column_of(code, field):
    return np.asarray([np.nan if row[field] is None else row[field]
                       for row in sweep[code]], dtype=float)


# ======================================================================
# 3. WHAT THE CODE TOUCHES, AND WHAT THE SOIL HAS ALREADY DECIDED
# ======================================================================
# ⚠ "These two lists are identical" is also what a broken comparison
# reports, so the STEEL goes through the same comparison as a control. If
# everything comes back identical, the comparison is broken, not the soil.
print("\n3. WHICH READINGS THE CONCRETE CODE ACTUALLY MOVES")
print(f"   {'reading':<10} {'identical at':>14} {'of':>5}  verdict")
for name in ("sls", "uls", "as_x", "as_y", "vx", "vcx", "vp", "vcp"):
    old, new = column_of(OLD_CODE, name), column_of(NEW_CODE, name)
    same = int(np.sum(old == new))
    tag = "IDENTICAL everywhere" if same == len(SIZES) else "DIFFERS"
    print(f"   {name:<10} {same:>14} {len(SIZES):>5}  {tag}")
pressure_same = all(np.all(column_of(OLD_CODE, name)
                           == column_of(NEW_CODE, name))
                    for name in ("sls", "uls"))
steel_differs = any(np.any(column_of(OLD_CODE, name)
                           != column_of(NEW_CODE, name)) for name in STEEL)
print(f"\n   bearing pressure identical : {pressure_same}")
print(f"   steel differs              : {steel_differs}   <- the control")
if pressure_same and steel_differs:
    print("   -> so the comparison CAN see a difference, and it finds none in")
    print("      the pressure. Choosing a different concrete code will not")
    print("      make an overloaded soil acceptable.")

# The shear capacity is a property of the depth and the concrete, so it
# should not move with the plan size at all. Said, then checked.
print("\n   AND THE SHEAR CAPACITY DOES NOT DEPEND ON THE PLAN SIZE")
capacity = {}
for code in (OLD_CODE, NEW_CODE):
    values = {row["vcx"] for row in sweep[code]}
    capacity[code] = sweep[code][0]["vcx"]
    print(f"     {code:<22} vcx took {len(values)} value(s): "
          f"{capacity[code]!r}")
print(f"   -> Eurocode 2 allows "
      f"{(capacity[NEW_CODE] / capacity[OLD_CODE] - 1) * 100:.0f} % more "
      f"shear stress on the same concrete at the same depth.")
print("   -> and note from the table above that the shear DEMAND (vx)")
print("      differs between the codes as well, not only the capacity: the")
print("      critical section is not in the same place. So the two shear")
print("      curves in panel C are not scaled copies of one another.")


def boundary(holds, low, high, resolution=0.005):
    """The largest size where `holds` is still true, to `resolution`.

    Used here with a FAILING predicate, because a footing gets better as it
    grows: the answer is "the largest size that still fails", and the
    smallest acceptable size is one step above it.

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


# ======================================================================
# 4. THE SMALLEST FOOTING EACH CHECK ALLOWS
# ======================================================================
print("\n4. THE SMALLEST FOOTING EACH CHECK ALLOWS")
smallest = {}


def worst_utilisation(code, size):
    """Every check on one scale: demand divided by what it allows.

    ⚠ THE PUNCHING CAPACITY IS NOT REPORTED AT EVERY SIZE. Measured, vcp
    comes back as exactly 0 over part of this range, so the ratio is
    unavailable rather than zero or infinite - it is returned as NaN and
    section 4 counts how often that happens. Dividing anyway raises
    ZeroDivisionError, which is how this was found; treating 0 as a
    capacity would have been worse, because the utilisation would have
    read as infinite and the check would look catastrophically failed
    when it simply was not reported.
    """
    row = design(code, size)
    return {"bearing": row["sls"] / ALLOWED_BEARING,
            "shear x": (row["vx"] / row["vcx"] if row["vcx"]
                        else float("nan")),
            "punching": (row["vp"] / row["vcp"] if row["vcp"]
                         else float("nan"))}


for label in ("bearing", "shear x", "punching"):
    print(f"   {label}")
    for code in (OLD_CODE, NEW_CODE):
        values = np.asarray([worst_utilisation(code, size)[label]
                             for size in SIZES])
        missing = int(np.sum(np.isnan(values)))
        if missing:
            print(f"     {code:<22} NOT REPORTED at {missing} of "
                  f"{len(SIZES)} sizes (the capacity comes back as 0)")
        bad = SIZES[values > 1.0]
        good = SIZES[(values <= 1.0) & ~np.isnan(values)]
        if not len(bad):
            print(f"     {code:<22} satisfied at every size in this range")
            smallest.setdefault(label, {})[code] = SIZES[0]
            continue
        if not len(good):
            print(f"     {code:<22} never satisfied in this range")
            continue

        def fails(size, code=code, label=label):
            value = worst_utilisation(code, size)[label]
            # An unreported check cannot fail. NaN > 1.0 is already False,
            # but saying so beats relying on it.
            return False if value != value else value > 1.0

        low, high = boundary(fails, bad[-1], good[0])
        smallest.setdefault(label, {})[code] = high
        print(f"     {code:<22} fails to {low:.3f} m, satisfied from "
              f"{high:.3f} m square")

print("\n   AND SO THE SMALLEST FOOTING THAT SATISFIES EVERYTHING:")
minimum = {}
for code in (OLD_CODE, NEW_CODE):
    needed = {label: sizes[code] for label, sizes in smallest.items()
              if code in sizes}
    if not needed:
        continue
    governing = max(needed, key=needed.get)
    minimum[code] = (needed[governing], governing)
    print(f"     {code:<22} {needed[governing]:.3f} m square, governed by "
          f"{governing.upper()}")
if len(minimum) == 2:
    gap = abs(minimum[NEW_CODE][0] - minimum[OLD_CODE][0])
    if gap < 1e-9:
        print(f"   -> the SAME size, because BEARING governs for both - and")
        print("      bearing is the check the concrete code cannot touch.")
        print("      Change the depth or the concrete and the codes would")
        print("      part company; on this footing they cannot.")
    else:
        print(f"   -> {gap:.3f} m apart, because the governing check differs.")

# ======================================================================
# 5. THE ENGINE NEVER REFUSES A FOOTING THAT IS FAR TOO SMALL
# ======================================================================
print("\n5. THE SMALLEST FOOTING IN THE SWEEP")
for code in (OLD_CODE, NEW_CODE):
    first = sweep[code][0]
    print(f"   {code:<22} at {first['size']:.2f} m square: "
          f"sls {first['sls']:.1f} kPa against {ALLOWED_BEARING:.0f} allowed "
          f"({first['sls'] / ALLOWED_BEARING:.2f}x)")
    print(f"   {'':<22} and it still returns as_x {first['as_x']:.1f} mm2, "
          f"no error")
print("   -> the pressures are published. Compare them against the")
print("      allowable you supplied; the engine will not do it for you.")

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
    axes.set_xlim(SIZES[0], SIZES[-1])


# ---- A. the steel ------------------------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  The flexural steel — one of only two things the code moves",
      "plan size  a = b   (m square)", "steel required   (mm²)")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    chart.plot(SIZES, column_of(code, "as_x"), color=colour, linewidth=2.0,
               label=f"{short}  as_x")
    chart.plot(SIZES, column_of(code, "as_y"), color=colour, linewidth=1.6,
               linestyle=":", label=f"{short}  as_y")
if minimum:
    edge = max(value for value, _ in minimum.values())
    chart.axvspan(SIZES[0], edge, color=DEAD, alpha=0.09, zorder=0)
    chart.text(0.985, 0.06,
               f"shaded: no code allows a footing this small — the binding "
               f"check is" + chr(10) +
               f"{minimum[OLD_CODE][1].upper()}, and every steel area in "
               f"there is for a footing you cannot use",
               transform=chart.transAxes, ha="right", va="bottom",
               fontsize=8.5, color=DEAD, fontweight="bold")
chart.plot([ANCHOR_SIZE], [anchor["as_x"]], marker="D", markersize=8,
           color=MUTED, markeredgecolor=SURFACE, markeredgewidth=2.0,
           zorder=7)
chart.annotate("the golden footing", (ANCHOR_SIZE, anchor["as_x"]),
               textcoords="offset points", xytext=(12, 8), ha="left",
               fontsize=8.5, color=INK_SOFT)
chart.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor=INK,
             ncol=2)

# ---- B. the direct comparison ------------------------------------------
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "plan size  a = b   (m square)", "steel demanded,  new ÷ old")
ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
share_x = column_of(NEW_CODE, "as_x") / column_of(OLD_CODE, "as_x")
share_y = column_of(NEW_CODE, "as_y") / column_of(OLD_CODE, "as_y")
ratio_axes.fill_between(SIZES, share_x, 1.0, where=(share_x >= 1.0),
                        interpolate=True, color=NEW_COLOUR, alpha=0.16)
ratio_axes.fill_between(SIZES, share_x, 1.0, where=(share_x <= 1.0),
                        interpolate=True, color=OLD_COLOUR, alpha=0.16)
ratio_axes.plot(SIZES, share_x, color=NEW_COLOUR, linewidth=2.0,
                label="as_x", zorder=4)
ratio_axes.plot(SIZES, share_y, color=NEW_COLOUR, linewidth=1.6,
                linestyle=":", label="as_y", zorder=4)
ratio_axes.annotate(f"at {SIZES[0]:.2f} m the new code asks\n"
                    f"{abs(share_x[0] - 1) * 100:.1f} % "
                    f"{'MORE' if share_x[0] > 1 else 'LESS'}",
                    (SIZES[0], share_x[0]), textcoords="offset points",
                    xytext=(16, 8), ha="left", fontsize=8.5,
                    color=NEW_COLOUR if share_x[0] > 1 else OLD_COLOUR,
                    fontweight="bold")
ratio_axes.annotate(f"and {abs(share_x[-1] - 1) * 100:.1f} % "
                    f"{'MORE' if share_x[-1] > 1 else 'LESS'} "
                    f"at {SIZES[-1]:.2f} m",
                    (SIZES[-1], share_x[-1]), textcoords="offset points",
                    xytext=(-10, -8), ha="right", va="top", fontsize=8.5,
                    color=NEW_COLOUR if share_x[-1] > 1 else OLD_COLOUR,
                    fontweight="bold")
ratio_axes.legend(loc="upper right", fontsize=8.5, frameon=False,
                  labelcolor=INK)

# ---- C. every check on one dimensionless axis --------------------------
# Bearing is in kPa and the shear checks are in MPa, so they cannot share a
# y-axis as they stand. Dividing each by what IT allows puts all of them on
# one scale where 1.0 means "this check is exactly satisfied" - the only
# alignment that is not arbitrary.
checks = figure.add_subplot(panels[1, 0])
dress(checks, "C.  Every check on one axis — demand ÷ what that check allows",
      "plan size  a = b   (m square)", "utilisation   (1.0 = at the limit)")
bearing = np.asarray([worst_utilisation(OLD_CODE, size)["bearing"]
                      for size in SIZES])
checks.plot(SIZES, bearing, color=SHARED_COLOUR, linewidth=2.6,
            label="bearing — SHARED by both codes", zorder=4)
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    for label, style in (("shear x", "-"), ("punching", ":")):
        values = np.asarray([worst_utilisation(code, size)[label]
                             for size in SIZES])
        checks.plot(SIZES, values, color=colour, linewidth=1.8,
                    linestyle=style, label=f"{short}  {label}", zorder=3)
checks.axhline(1.0, color=DEAD, linewidth=1.4, linestyle="--", zorder=2)
checks.annotate("1.0 — the limit", (SIZES[-1], 1.0),
                textcoords="offset points", xytext=(-6, 8), ha="right",
                fontsize=8.5, color=DEAD, fontweight="bold")
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    if code in minimum:
        where, governing = minimum[code]
        checks.plot([where], [1.0], marker="o", markersize=9, color=colour,
                    markeredgecolor=SURFACE, markeredgewidth=2.0, zorder=6)
checks.set_ylim(0.0, min(3.0, float(np.nanmax(bearing)) * 1.15))
checks.legend(loc="upper right", fontsize=8.5, frameon=False,
              labelcolor=INK, ncol=2)

# ---- D. the verdict ----------------------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same footing, same axis — the smallest each code allows",
      "", "")
verdict.set_xlabel("plan size  a = b   (m square)", fontsize=9.5,
                   color=INK_SOFT)
REGIMES = ((DEAD, "a check is over its limit — unbuildable"),
           (FREE, "every check satisfied"))
for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    if code not in minimum:
        continue
    edge, governing = minimum[code]
    for start, stop, colour in ((SIZES[0], edge, DEAD),
                                (edge, SIZES[-1], FREE)):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, edgecolor=SURFACE,
                     linewidth=2.0, zorder=3)
    verdict.text(SIZES[0] + 0.04, base + 0.15, code, fontsize=9.5, color=INK,
                 fontweight="bold")
    verdict.plot([edge, edge], [base - 0.145, base - 0.105], color=INK,
                 linewidth=1.0, zorder=5)
    verdict.text(edge, base - 0.20,
                 f"{edge:.2f} m — governed by {governing}", ha="center",
                 fontsize=8.5, color=INK, fontweight="bold")
verdict.text(0.985, 0.975,
             "both boundaries are set by BEARING here, and bearing is the "
             "one" + chr(10) +
             "check the concrete code cannot move — so they coincide",
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
    f"One pad footing, growing wider:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"{FOOTING['yf']:.2f} m deep, {FOOTING['c1']:.2f} m column, "
    f"fcu {FOOTING['fcu']:.0f} MPa, "
    f"{FOOTING['load_cases'][0]['pa1']:.0f} kN, allowable bearing "
    f"{ALLOWED_BEARING:.0f} kPa  —  ONLY the plan size changes\n"
    f"The concrete code moves the steel and the shear capacity; the "
    f"bearing pressure is a soil problem and comes back identical",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "pad_footing_sabs_vs_eurocode_size.png")
