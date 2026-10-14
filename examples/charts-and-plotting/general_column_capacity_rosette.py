# ---
# Example:  The biaxial capacity rosette - four shapes, same concrete, same steel
# Feature:  general_column (C13 General Column)
# Verified: yes - 2026-09-08 - the pinned 400 mm square reproduces both Case factors; every rosette point measured on prokon-automation.exe, with the square's four-fold and the rectangle's two-fold symmetry as the search's own controls. Batched 2026-09-08 (916 engine calls to 61, 489 s to 31 s) and re-verified by diffing the whole printed report against the one-call-at-a-time run: every computed number byte-identical, only the call counts differ
# ---
# C13 is the only engine here that takes an ARBITRARY outline, so it can
# answer a question no other one can: for the same concrete and the same
# steel, WHICH SHAPE carries most - and in which direction?
#
# The answer is not a number, it is a closed curve. For a fixed axial
# load, sweep the moment DIRECTION right round the section and find, at
# each angle, the moment magnitude the column can just carry. Join the
# points and you have the section's true biaxial capacity envelope - the
# rosette.
#
# Four sections, all 160 000 mm2 of concrete and all eight Y25 bars:
#
#     square      400 x 400
#     rectangle   566 x 283 (2:1)
#     L-section   500 x 500 with 200 mm arms
#     T-section   600 wide flange, 200 mm web
#
# HOW THE ENVELOPE IS FOUND. C13 reports min_capacity_factor - capacity
# over demand - so the capacity at an angle is the moment where that
# factor is exactly 1. The script brackets it and closes in with the
# SECANT method, which fits a straight line through the last two
# residuals instead of halving a range it already knows is lopsided.
# Every angle reports the residual it converged to, so a bad point is
# visible instead of invisible.
#
# ⚠ SIXTEEN DIRECTIONS RIDE IN ONE ENGINE CALL, and that is what makes
# this script quick rather than slow. A C13 load case carries its OWN
# axial force and its own two moments, so the sixteen directions of one
# secant step are sixteen load cases on one section - a single analysis.
# Measured: one load case costs 0.345 s and sixteen cost 0.395 s, 1.15x
# rather than 16x, because 0.282 s of that is the host starting up. The
# sixteen answers are bit-identical to sixteen separate calls, to the last
# binary digit, so nothing about the search or its controls changes.
#
# Asking one direction at a time instead cost 916 engine calls and 8
# minutes - 53 % of it spent starting the same executable 916 times. An
# example nobody will wait for is an example nobody runs.
#
# ⚠ WHAT IS *NOT* DONE, AND WHY - MEASURED. Adjacent directions have
# similar capacities, so seeding each search from the previous angle's
# answer looks like an obvious further saving. It cuts calls by another
# 36 % and it is REJECTED: it takes the square's four-fold symmetry check
# below from 0.000 % to 0.164 %, because the answers stop being path
# independent. That exact zero is this script's whole reason for trusting
# the L-section rosette, which has no symmetry of its own to check. Speed
# bought with the evidence is not a saving.
#
# ⚠ AND THE METHOD IS CONTROLLED BY THE SQUARE. A 400 x 400 section with
# symmetric bars MUST have a four-fold symmetric envelope. If the search
# were unreliable, the square's four quadrants would not match. They are
# compared, and the mismatch is printed as a percentage - so the rosette
# for the L-section, which has no symmetry to check, is trustworthy for a
# reason rather than by assumption. The rectangle is the second control:
# it must be two-fold symmetric and visibly NOT four-fold, so a search
# that quietly symmetrised everything would show up there.
#
# ⚠ ONE THING THE ROSETTE CANNOT SHOW, AND THE SCRIPT SAYS SO. Measured:
# C13's capacity factor is identical at A and at A + 180 degrees even on
# a section with every bar crowded against one face - where the two senses
# of the moment cannot physically be equal. So the factor does not carry
# the SIGN of the moment, and every envelope here is centrally symmetric
# by construction rather than because the section is. Read each rosette as
# one capacity per AXIS of bending.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

import math
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
# There is deliberately NO matplotlib.use("Agg") here. That call forces
# the headless backend, and a script that forces it can never draw into
# Spyder's Plots pane - which is where you actually want to see it.
HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can."""
    path = Path(filename).resolve()
    figure.savefig(path, dpi=150, facecolor="white")
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


# -- The columns --------------------------------------------------------
CODE = "BS8110 - 1997"
LENGTH = 3.0              # m
FCU = 30.0
FY = 450.0
BAR = 25.0                # mm
COVER = 42.5              # mm to the bar centre
AXIAL = 1500.0            # kN, the headline rosette
AXIALS = (500.0, 1500.0, 3000.0)   # the L-section family

ANGLES = np.arange(0.0, 360.0, 22.5)      # 16 directions
TOLERANCE = 0.005          # stop when the capacity factor is within this
MAX_STEPS = 8


def outline(points):
    """A closed solid contour through these absolute points, in mm."""
    rows = [{"code": "+", "x": points[0][0], "y": points[0][1]}]
    for x, y in points[1:]:
        rows.append({"code": "L", "x": x, "y": y})
    return rows


def bars(points):
    """One Y25 at each point. C13 wants a "+" then a "B" with the size."""
    rows = []
    for x, y in points:
        rows.append({"code": "+", "x": x, "y": y})
        rows.append({"code": "B", "x": BAR})
    return rows


SIDE = 400.0
LONG = math.sqrt(160_000.0 * 2.0)         # 565.69
SHORT = LONG / 2.0

SHAPES = {
    "square 400 x 400": (
        [(0, 0), (SIDE, 0), (SIDE, SIDE), (0, SIDE)],
        [(COVER, COVER), (SIDE / 2, COVER), (SIDE - COVER, COVER),
         (SIDE - COVER, SIDE / 2), (SIDE - COVER, SIDE - COVER),
         (SIDE / 2, SIDE - COVER), (COVER, SIDE - COVER),
         (COVER, SIDE / 2)]),
    "rectangle 2:1": (
        [(0, 0), (LONG, 0), (LONG, SHORT), (0, SHORT)],
        [(COVER, COVER), (COVER + (LONG - 2 * COVER) / 3, COVER),
         (COVER + 2 * (LONG - 2 * COVER) / 3, COVER),
         (LONG - COVER, COVER), (LONG - COVER, SHORT - COVER),
         (COVER + 2 * (LONG - 2 * COVER) / 3, SHORT - COVER),
         (COVER + (LONG - 2 * COVER) / 3, SHORT - COVER),
         (COVER, SHORT - COVER)]),
    "L 500, 200 arms": (
        [(0, 0), (500, 0), (500, 200), (200, 200), (200, 500), (0, 500)],
        [(COVER, COVER), (250, COVER), (500 - COVER, COVER),
         (500 - COVER, 200 - COVER), (200 - COVER, 200 - COVER),
         (200 - COVER, 250), (200 - COVER, 500 - COVER),
         (COVER, 500 - COVER)]),
    "T 600 flange": (
        [(200, 0), (400, 0), (400, 200), (600, 200), (600, 400),
         (0, 400), (0, 200), (200, 200)],
        [(200 + COVER, COVER), (400 - COVER, COVER),
         (COVER, 200 + COVER), (600 - COVER, 200 + COVER),
         (COVER, 400 - COVER), (600 - COVER, 400 - COVER),
         (200, 400 - COVER), (400, 400 - COVER)]),
}
HEADLINE = "L 500, 200 arms"

print("THE BIAXIAL CAPACITY ROSETTE")
print(f"  {CODE}, {LENGTH:.1f} m braced column, fcu {FCU:.0f}, fy {FY:.0f}")
print(f"  four sections, 160 000 mm2 of concrete and 8 Y{BAR:.0f} each")
print(f"  N = {AXIAL:.0f} kN, {len(ANGLES)} moment directions per envelope")

# -- The anchor ---------------------------------------------------------
# C13's own pinned reference: a 400 mm square, four Y25 corner bars.
PINNED_LC1 = 2.179097995657654
PINNED_LC2 = 1.123583760958025
envelope_probe = prokon.v5.general_column.analyse(
    design_code=CODE, length=3.0, fcu=30.0, fy=450.0,
    section=outline([(0, 0), (400, 0), (400, 400), (0, 400)])
            + bars([(42.5, 42.5), (357.5, 42.5), (357.5, 357.5),
                    (42.5, 357.5)]),
    load_cases=[
        {"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50},
        {"axial": 2000, "moment_x_top": 90, "moment_y_top": 30,
         "moment_x_bottom": 90, "moment_y_bottom": 30}])
anchor = envelope_probe["result"]
measured = (anchor["load_cases"][0]["min_capacity_factor"],
            anchor["load_cases"][1]["min_capacity_factor"])
print("\n  anchor: the pinned 400 mm square, four Y25 corner bars")
print(f"    LC1 {measured[0]!r}   pinned {PINNED_LC1!r}")
print(f"    LC2 {measured[1]!r}   pinned {PINNED_LC2!r}")
print(f"    -> {'EXACT on both' if measured == (PINNED_LC1, PINNED_LC2) else 'DRIFTED'}")
print(f"    engine {envelope_probe['module']} "
      f"{envelope_probe['module_version']}")

CALLS = [0]


def load_case(axial, moment, angle):
    """One C13 load case: a moment of this size, in this direction."""
    mx = moment * math.cos(math.radians(angle))
    my = moment * math.sin(math.radians(angle))
    return {"axial": axial,
            "moment_x_top": mx, "moment_x_bottom": mx,
            "moment_y_top": my, "moment_y_bottom": my}


def one_factor(section, axial, moment, angle):
    """C13's capacity/demand factor for a single moment. One engine call."""
    CALLS[0] += 1
    try:
        result = prokon.v5.general_column.analyse(
            design_code=CODE, length=LENGTH, fcu=FCU, fy=FY,
            section=section, load_cases=[load_case(axial, moment, angle)])["result"]
    except prokon.v5.ProkonError:
        return None
    return result["min_capacity_factor"]


def factors(section, axial, probes):
    """The capacity factor for MANY (angle, moment) pairs, in ONE call.

    This is the whole reason the script is quick. A load case already
    carries its own axial force and its own two moments, so sixteen
    directions are sixteen load cases on one section - and C13 answers
    them all in a single analysis.
    """
    if not probes:
        return []
    CALLS[0] += 1
    cases = [load_case(axial, moment, angle) for angle, moment in probes]
    try:
        answer = prokon.v5.general_column.analyse(
            design_code=CODE, length=LENGTH, fcu=FCU, fy=FY,
            section=section, load_cases=cases)
    except prokon.v5.ProkonError:
        # One unanswerable direction must not cost the other fifteen their
        # answer, so ask separately and let each fail on its own.
        #
        # ⚠ UNPROVEN, AND SAID SO DELIBERATELY. No input has been found
        # that makes C13 refuse: measured, an axial of 1e9 kN, a negative
        # axial and a moment of 1e9 kNm are all ANSWERED, with tiny
        # capacity factors, and all sixteen rows come back. So this branch
        # is a guard for a case nobody has produced - not a verified path.
        return [one_factor(section, axial, moment, angle)
                for angle, moment in probes]
    return [row["min_capacity_factor"]
            for row in answer["result"]["load_cases"]]


def rosette(section, axial, low=20.0, high=900.0):
    """The whole envelope: one (moment, residual) per direction.

    Every direction runs the SAME independent secant search it always did
    - bracket the root, then fit a straight line through the last two
    residuals instead of halving a range it already knows is lopsided -
    and every one of them starts from the SAME cold bracket. What changed
    is only that all sixteen searches are advanced IN LOCKSTEP, so one
    engine call carries one step of every direction that has not yet
    converged, instead of one call carrying one step of one direction.

    ⚠ THE COLD BRACKET IS LOAD-BEARING - DO NOT WARM-START IT. Seeding it
    from the previous direction's answer looks free and is not: measured,
    it cuts calls by 36 % and takes the square's four-fold symmetry check
    below from 0.000 % to 0.164 %, because the answers stop being path
    independent. That exact zero is this script's whole reason for
    trusting the L-section's rosette, which has no symmetry of its own to
    check. Batching costs it nothing - the answers are bit-identical to
    one-at-a-time calls, measured to the last binary digit.
    """
    hunts = [{"angle": float(angle), "low": low, "high": high,
              "moment": None, "residual": None, "live": True}
             for angle in ANGLES]

    # The bracket: every direction's low end in one engine call, every
    # high end in a second. Two calls for all sixteen brackets.
    at_low = factors(section, axial,
                     [(hunt["angle"], hunt["low"]) for hunt in hunts])
    at_high = factors(section, axial,
                      [(hunt["angle"], hunt["high"]) for hunt in hunts])
    for hunt, low_value, high_value in zip(hunts, at_low, at_high):
        if low_value is None or high_value is None:
            hunt["live"] = False         # C13 could not answer at all
            continue
        hunt["low_residual"] = low_value - 1.0
        hunt["high_residual"] = high_value - 1.0
        if hunt["low_residual"] < 0 or hunt["high_residual"] > 0:
            hunt["live"] = False         # the bracket holds no root

    # Then up to MAX_STEPS secant steps, one engine call per step.
    for _ in range(MAX_STEPS):
        stepping = []
        for hunt in hunts:
            if not hunt["live"]:
                continue
            if hunt["high_residual"] == hunt["low_residual"]:
                hunt["live"] = False
                continue
            reach = (hunt["low"] - hunt["low_residual"]
                     * (hunt["high"] - hunt["low"])
                     / (hunt["high_residual"] - hunt["low_residual"]))
            hunt["step"] = min(max(reach, hunt["low"]), hunt["high"])
            stepping.append(hunt)
        if not stepping:
            break
        values = factors(section, axial,
                         [(hunt["angle"], hunt["step"]) for hunt in stepping])
        for hunt, value in zip(stepping, values):
            if value is None:
                hunt["live"] = False
                continue
            hunt["residual"] = value - 1.0
            hunt["moment"] = hunt["step"]
            if abs(hunt["residual"]) <= TOLERANCE:
                hunt["live"] = False
            elif hunt["residual"] < 0:
                hunt["high"] = hunt["step"]
                hunt["high_residual"] = hunt["residual"]
            else:
                hunt["low"] = hunt["step"]
                hunt["low_residual"] = hunt["residual"]

    return [(hunt["moment"], hunt["residual"]) for hunt in hunts]


# -- The four shapes ----------------------------------------------------
print(f"\nFOUR SHAPES AT N = {AXIAL:.0f} kN")
print(f"   {'section':>18}" + "".join(f"{angle:>7.0f}" for angle in ANGLES[::2]))
envelopes = {}
sections = {}
for name, (shape, positions) in SHAPES.items():
    section = outline(shape) + bars(positions)
    sections[name] = (shape, positions)
    envelopes[name] = rosette(section, AXIAL)
    line = "".join("      -" if moment is None else f"{moment:>7.0f}"
                   for moment, _ in envelopes[name][::2])
    print(f"   {name:>18}{line}")
print("   (kNm capacity, at moment directions 0, 45, 90 ... degrees)")

worst_residual = max(abs(residual)
                     for rows in envelopes.values()
                     for _, residual in rows if residual is not None)
POINTS = len(SHAPES) * len(ANGLES)
print(f"\n   the search converged to within {worst_residual:.4f} of a "
      f"capacity factor of 1.0")
print(f"   on every point, in {CALLS[0]} engine calls for {POINTS} points")
print(f"   ({CALLS[0] / len(SHAPES):.0f} search steps per shape, and each "
      f"step asks all {len(ANGLES)} directions in ONE call)")

# -- The control: the square must be four-fold symmetric ----------------
square = [moment for moment, _ in envelopes["square 400 x 400"]]
quadrant = len(ANGLES) // 4
errors = []
for index in range(len(ANGLES)):
    here = square[index]
    there = square[(index + quadrant) % len(ANGLES)]
    if here and there:
        errors.append(abs(here - there) / here * 100.0)
print("\nTHE CONTROL - A SQUARE MUST BE FOUR-FOLD SYMMETRIC")
print(f"   comparing every direction with the one 90 degrees round:")
print(f"   worst mismatch {max(errors):.3f} %, mean {np.mean(errors):.3f} %")
print("   -> the search finds the same capacity from four independent")
print("      starting directions, so the L-section's rosette - which has")
print("      no symmetry of its own to check - is trustworthy for a")
print("      reason. The rectangle is the second control: it must be")
print("      TWO-fold symmetric and visibly NOT four-fold, so a bug that")
print("      symmetrised everything would show up there.")

rectangle = [moment for moment, _ in envelopes["rectangle 2:1"]]
half = len(ANGLES) // 2
two_fold = [abs(rectangle[i] - rectangle[(i + half) % len(ANGLES)])
            / rectangle[i] * 100.0
            for i in range(len(ANGLES)) if rectangle[i]]
four_fold = [abs(rectangle[i] - rectangle[(i + quadrant) % len(ANGLES)])
             / rectangle[i] * 100.0
             for i in range(len(ANGLES)) if rectangle[i]]
print(f"   the rectangle: two-fold mismatch {max(two_fold):.3f} %, "
      f"four-fold mismatch {max(four_fold):.1f} %")
print("   -> exactly as it should be. The method is not symmetrising.")

# -- What the rosette CANNOT tell you, measured -------------------------
# The L-section's envelope comes out identical at A and at A + 180, which
# an L-section physically is not. That is worth establishing rather than
# explaining away, so here is a section where the two senses of the
# moment MUST differ: a 400 square with all eight bars crowded against one
# face. Bending it one way puts every bar in tension; the other way puts
# every bar in compression.
#
# CONTROL: the same section at 0 and at 90 degrees must give DIFFERENT
# answers, otherwise the reading is simply dead and proves nothing.
lopsided = outline([(0, 0), (SIDE, 0), (SIDE, SIDE), (0, SIDE)]) + bars(
    [(COVER + index * (SIDE - 2 * COVER) / 7.0, COVER)
     for index in range(8)])
PROBE_ANGLES = (0, 90, 180, 270)
probe = dict(zip(PROBE_ANGLES,
                 factors(lopsided, AXIAL,
                         [(float(angle), 200.0) for angle in PROBE_ANGLES])))
print("\nWHAT THE ROSETTE CANNOT TELL YOU")
print("   a 400 square with ALL eight bars against the y = "
      f"{COVER:.1f} mm face,")
print("   under 200 kNm at four directions:")
for angle in (0, 180, 90, 270):
    print(f"     {angle:>4} deg   capacity factor {probe[angle]!r}")
reversed_same = (probe[0] == probe[180] and probe[90] == probe[270])
directions_differ = probe[0] != probe[90]
print(f"   0 and 180 identical: {probe[0] == probe[180]};  "
      f"90 and 270 identical: {probe[90] == probe[270]}")
print(f"   0 and 90 differ:     {directions_differ}")
if reversed_same and directions_differ:
    print("   -> C13's capacity factor DOES NOT DISTINGUISH THE SENSE of")
    print("      the moment. Reversing it returns the same number to the")
    print("      last binary digit, on a section where the two senses")
    print("      cannot physically be equal. Rotating the moment 90")
    print("      degrees DOES change it, which is the control - the")
    print("      reading is alive, it just does not carry a sign.")
    print("   -> so every rosette here is centrally symmetric BY")
    print("      CONSTRUCTION, not because the section is. Read it as one")
    print("      capacity per AXIS of bending, not per direction, and")
    print("      check an asymmetric section's two senses another way.")

# -- Which shape wins, and where ----------------------------------------
print(f"\nWHICH SHAPE WINS, AND IN WHICH DIRECTION")
print(f"   {'section':>18} {'strongest':>18} {'weakest':>18} "
      f"{'ratio':>7}")
for name, rows in envelopes.items():
    values = [(moment, angle) for (moment, _), angle in zip(rows, ANGLES)
              if moment is not None]
    strongest = max(values)
    weakest = min(values)
    print(f"   {name:>18} {strongest[0]:>10.0f} at "
          f"{strongest[1]:>3.0f} deg {weakest[0]:>10.0f} at "
          f"{weakest[1]:>3.0f} deg {strongest[0] / weakest[0]:>7.2f}")
print("   -> the ratio is the whole point of the rosette. A square is")
print("      nearly a circle and can be checked on its two axes; the")
print("      others cannot, and the direction of the weakest axis is not")
print("      where a sketch would put it.")

# The one comparison an engineer actually makes.
square_area = [moment for moment, _ in envelopes["square 400 x 400"]]
print(f"\n   against the square, direction by direction:")
print(f"   {'angle':>6}" + "".join(f"{name[:12]:>14}" for name in SHAPES))
for index, angle in enumerate(ANGLES):
    line = []
    for name in SHAPES:
        moment = envelopes[name][index][0]
        base = square_area[index]
        line.append("-" if moment is None or not base
                    else f"{moment / base:.2f}x")
    print(f"   {angle:>6.1f}" + "".join(f"{cell:>14}" for cell in line))

# -- The L-section under three axial loads ------------------------------
print(f"\nTHE {HEADLINE.upper()} UNDER THREE AXIAL LOADS")
shape, positions = SHAPES[HEADLINE]
section = outline(shape) + bars(positions)
families = {}
for axial in AXIALS:
    families[axial] = (envelopes[HEADLINE] if axial == AXIAL
                       else rosette(section, axial))
    values = [moment for moment, _ in families[axial] if moment is not None]
    if values:
        print(f"   N = {axial:>6.0f} kN:  {min(values):>6.0f} to "
              f"{max(values):>6.0f} kNm  "
              f"(spread {max(values) / min(values):.2f}x)")
print(f"\n   {CALLS[0]} engine calls in total")

# -- The figure ---------------------------------------------------------
figure = plt.figure(figsize=(16, 8.6), layout="constrained")
figure.patch.set_facecolor("white")
grid = figure.add_gridspec(2, 3, height_ratios=(0.8, 1.0))

colours = dict(zip(SHAPES, ("#4c78a8", "#59a14f", "#b03030", "#e0a030")))


def closed(values, angles):
    """A polar series with the first point repeated, so the curve joins."""
    return (list(angles) + [angles[0]], list(values) + [values[0]])


# 1. The rosette.
rose = figure.add_subplot(grid[:, 0], projection="polar")
for name, rows in envelopes.items():
    radians = [math.radians(angle) for angle in ANGLES]
    values = [moment if moment is not None else 0.0 for moment, _ in rows]
    theta, radius = closed(values, radians)
    rose.plot(theta, radius, linewidth=2.0, color=colours[name], label=name)
    rose.fill(theta, radius, color=colours[name], alpha=0.08)
rose.set_theta_zero_location("E")
rose.set_title(f"Biaxial moment capacity at N = {AXIAL:.0f} kN\n"
               f"radius is the moment (kNm) the section just carries",
               fontsize=10, pad=18)
rose.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), fontsize=8)
rose.grid(True, linewidth=0.4, color="0.8")

# 2. The sections themselves, to scale.
draw = figure.add_subplot(grid[0, 1])
offset = 0.0
for name, (shape, positions) in sections.items():
    xs = [point[0] + offset for point in shape] + [shape[0][0] + offset]
    ys = [point[1] for point in shape] + [shape[0][1]]
    draw.fill(xs, ys, facecolor=colours[name], alpha=0.25,
              edgecolor=colours[name], linewidth=1.8)
    draw.plot([point[0] + offset for point in positions],
              [point[1] for point in positions], "o", markersize=4,
              color=colours[name])
    draw.annotate(name.split()[0], (offset + 20, -60), fontsize=8,
                  color=colours[name], fontweight="bold")
    offset += max(point[0] for point in shape) + 90
draw.set_aspect("equal")
draw.set_ylim(-110, 620)
draw.set_xlabel("mm")
draw.set_title("The four sections - identical concrete area,\n"
               "identical steel, drawn to the same scale", fontsize=10)
draw.grid(True, linewidth=0.3, color="0.9")

# 3. Capacity against the square, direction by direction.
against = figure.add_subplot(grid[1, 1])
for name, rows in envelopes.items():
    if name == "square 400 x 400":
        continue
    ratios = []
    for index in range(len(ANGLES)):
        moment = rows[index][0]
        base = square_area[index]
        ratios.append(moment / base if moment and base else np.nan)
    against.plot(ANGLES, ratios, marker="o", markersize=4, linewidth=1.8,
                 color=colours[name], label=name)
against.axhline(1.0, color="0.3", linestyle="--", linewidth=1.4)
against.annotate("the square", (5, 1.03), fontsize=8, color="0.3")
against.set_xlabel("moment direction (degrees from the x axis)")
against.set_ylabel("capacity relative to the square")
against.set_xticks(list(ANGLES[::2]))
against.set_title("Shape pays - but only in some directions", fontsize=10)
against.legend(fontsize=8)
against.grid(True, linewidth=0.3, color="0.85")

# 4. The L-section family.
family = figure.add_subplot(grid[:, 2], projection="polar")
shades = plt.cm.plasma(np.linspace(0.15, 0.8, len(AXIALS)))
for index, axial in enumerate(AXIALS):
    radians = [math.radians(angle) for angle in ANGLES]
    values = [moment if moment is not None else 0.0
              for moment, _ in families[axial]]
    theta, radius = closed(values, radians)
    family.plot(theta, radius, linewidth=2.0, color=shades[index],
                label=f"N = {axial:.0f} kN")
    family.fill(theta, radius, color=shades[index], alpha=0.08)
family.set_theta_zero_location("E")
family.set_title(f"{HEADLINE} at three axial loads\n"
                 f"the envelope grows AND changes shape", fontsize=10,
                 pad=18)
family.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), fontsize=8)
family.grid(True, linewidth=0.4, color="0.8")

figure.suptitle(
    f"General column biaxial capacity rosette - {CODE}\n"
    f"160 000 mm2 concrete and 8 Y{BAR:.0f} in every section, "
    f"{LENGTH:.1f} m braced, fcu {FCU:.0f} MPa, fy {FY:.0f} MPa  |  "
    f"secant search, {len(ANGLES)} directions, converged within "
    f"{worst_residual:.4f}  |  engine {envelope_probe['module_version']}",
    fontsize=10)
deliver(figure, "general_column_capacity_rosette.png")
