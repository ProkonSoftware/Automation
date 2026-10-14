# ---
# Example:  The wall drawn to scale - section, pressures, and the sizing map
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes - 2026-09-18 - the C14 desktop-parity wall reproduces its pinned five; every wall in the sizing map measured on prokon-automation.exe; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example
# ---
# Sizing a retaining wall is choosing two numbers - how far the base sticks
# out in front (the toe) and how far it reaches back under the fill (the
# heel) - against three checks that pull in different directions:
#
#   OVERTURNING   wants a long HEEL, so the weight of soil on it holds
#                 the wall down
#   SLIDING       wants weight anywhere, and a shear key
#   BEARING       wants a WIDE base, and then punishes you for putting
#                 the resultant outside the middle third
#
# This script maps all three over the (toe, heel) plane, draws the
# feasible region they leave, and finds the wall with the least concrete
# inside it. Then it draws that wall - to scale, with the bearing pressure
# under the base and the stem's own bending moment beside it, both read
# out of the engine rather than re-derived.
#
# ⚠ THE BEARING CHECK GOES NEGATIVE IN qmax, NOT qmin. As the heel
# shrinks, the engine's qmax turns NEGATIVE while qmin sits at zero
# throughout - so a script watching qmin for the sign change never sees
# it. The test that works is `qmax > 0 and 0 < bearing_ratio <= 1`, and
# the script counts how many cells that catches which a naive test misses.
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


# -- The wall -----------------------------------------------------------
# Every length is in METRES, angles in degrees, pressures in kPa.
CODE = "BS8110 - 1997"
STEM_HEIGHT = 5.0         # h1, above the base
SOIL_IN_FRONT = 0.7       # h2
BELOW_DREDGE = 0.8        # h3
WATER = 2.8               # hw, 0 for no water table
BASE_THICKNESS = 0.4      # c
KEY_DEPTH = 0.7           # f
STEM_TOP = 0.3            # at
STEM_BASE = 0.4           # ab
BATTER = 0.45             # x
THETA = 27.0              # soil friction angle
ALPHA = 9.0               # fill slope
DELTA = 20.0              # wall/soil friction
SOIL_DENSITY = 18.0       # kN/m3
CONCRETE_DENSITY = 25.0   # kN/m3
FCU = 25.0
FY = 450.0
ALLOWABLE = 400.0         # kPa
COVER = 50.0              # mm

TOES = np.arange(0.20, 1.61, 0.20)        # 8 m
HEELS = np.arange(0.20, 3.61, 0.20)       # 18 m

# The HEEL step is left where it is on purpose, and both of its ends are
# load-bearing: the feasible region lives in the top 0.8 m of that range
# and every cell of the sign trap below lives in the bottom 0.6 m. The TOE
# step is the one with slack in it, so that is the one that was doubled.

# -- Two numbers that decide how long this script takes -----------------
# The sweep below is Cartesian, so its cost is the product of the two step
# sizes above, and every point is a separate engine process at about
# 0.33 s. Choose the steps for the chart you want to READ - halving a step
# doubles the wait.
#
# Then bound the wait itself. timeout_seconds is PER CALL, it defaults to
# 120 s, and these calls take 0.33 s - so one stuck call could cost more
# than the whole sweep. Sized here at many times what a healthy call takes
# and still far below what this whole script costs: generous, and bounded.
prokon.v5.timeout_seconds = 30.0
POINTS = 51               # the stem grid: heights[0..50]

LOAD_CASES = [
    {"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0, "lynl": 1.0,
     "xlv": 2.0, "ph": 0.5},
    {"name": "Truck", "w": 2.0, "p": 0.5, "xp": 2.0, "lynl": 2.0,
     "xlv": 1.0, "ph": 3.0},
    {"name": "Train", "w": 3.0, "lynl": 1.0, "xlv": 2.0},
]

print("THE RETAINING WALL, DRAWN TO SCALE")
print(f"  {CODE}, {STEM_HEIGHT:.1f} m stem, water table at {WATER:.1f} m")
print(f"  theta {THETA:.0f} deg, delta {DELTA:.0f} deg, fill slope "
      f"{ALPHA:.0f} deg, allowable {ALLOWABLE:.0f} kPa")
print(f"  grid: {len(TOES)} toe lengths x {len(HEELS)} heel lengths "
      f"= {len(TOES) * len(HEELS)} engine calls")

# -- The anchor ---------------------------------------------------------
PINNED = (4.477940718035636, 1.6341314510288516, 97.26517611421157,
          915.8514440593759, 791.8667235080961)
envelope = prokon.v5.retaining_wall.analyse(
    concrete_code=CODE, h1=5.0, h2=0.7, h3=0.8, hw=2.8, b=0.55, d=2.50,
    c=0.40, f=0.70, xf=3.05, at=0.30, ab=0.40, x=0.45,
    theta=27.0, alpha=9.0, delta=20.0, dg=18.0, db=25.0,
    fcu=25.0, fy=450.0, sf_overturning=1.5, sf_sliding=1.5,
    dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9, pmax=400.0, mu=0.5,
    cover_wall=50.0, cover_base=50.0,
    seismic=True, kh=0.02, kv=0.01, seis_w_loads=True,
    allow_seep=True, toe_back_force=True,
    load_cases=LOAD_CASES)
anchor = envelope["result"]
measured = (anchor["sf_overturning"], anchor["sf_sliding"], anchor["qmax"],
            anchor["as_wall_req"], anchor["as_base_req"])
print("\n  anchor: the C14 desktop-parity wall")
for name, value, pin in zip(("SF overturning", "SF sliding   ",
                             "qmax         ", "As wall      ",
                             "As base      "), measured, PINNED):
    print(f"    {name} {value!r:22} pinned {pin!r}")
print(f"    -> {'EXACT on all five' if measured == PINNED else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


# invalid_input and no_solution say something about the WALL - this base
# has no answer - and belong on the map as a hole. Every other category
# says something about the RUN, and a map quietly missing those points
# would be a lie. So they are counted by category and printed.
NO_ANSWER_HERE = ("invalid_input", "no_solution")
not_answered = []


def wall(toe, heel, **overrides):
    """One wall. Returns the whole result, or None if the engine refuses."""
    settings = dict(
        concrete_code=CODE, h1=STEM_HEIGHT, h2=SOIL_IN_FRONT,
        h3=BELOW_DREDGE, hw=WATER, b=float(toe), d=float(heel),
        c=BASE_THICKNESS, f=KEY_DEPTH,
        xf=float(heel) + STEM_BASE + float(toe) - 0.4,
        at=STEM_TOP, ab=STEM_BASE, x=BATTER,
        theta=THETA, alpha=ALPHA, delta=DELTA,
        dg=SOIL_DENSITY, db=CONCRETE_DENSITY, fcu=FCU, fy=FY,
        sf_overturning=1.5, sf_sliding=1.5,
        dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9, pmax=ALLOWABLE, mu=0.5,
        cover_wall=COVER, cover_base=COVER,
        allow_seep=True, toe_back_force=True)
    settings.update(overrides)
    try:
        return prokon.v5.retaining_wall.analyse(**settings,
                                             load_cases=LOAD_CASES)["result"]
    except prokon.v5.ProkonError as refusal:
        if refusal.category not in NO_ANSWER_HERE:
            not_answered.append("{0}/{1}".format(refusal.category,
                                                 refusal.code))
        return None


def concrete(toe, heel):
    """Cubic metres of concrete per metre run of wall."""
    base = (toe + heel + STEM_BASE) * BASE_THICKNESS
    stem = (STEM_TOP + STEM_BASE) / 2.0 * (STEM_HEIGHT - BASE_THICKNESS)
    key = KEY_DEPTH * 0.3
    return base + stem + key


# -- Sweep --------------------------------------------------------------
overturning = np.full((len(HEELS), len(TOES)), np.nan)
sliding = np.full_like(overturning, np.nan)
bearing = np.full_like(overturning, np.nan)
qmax_grid = np.full_like(overturning, np.nan)
qmin_grid = np.full_like(overturning, np.nan)
volume = np.full_like(overturning, np.nan)
steel = np.full_like(overturning, np.nan)
refusals = 0

for column, toe in enumerate(TOES):
    for row, heel in enumerate(HEELS):
        result = wall(float(toe), float(heel))
        if result is None:
            refusals += 1
            continue
        # Two of the three ratios read "bigger is better"; bearing does
        # not. They are turned into utilisations so one map can hold all
        # three: above 1.0 fails, whichever check it is.
        over = result["overturning_ratio"]
        slide = result["sliding_ratio"]
        overturning[row, column] = 1.0 / over if over else np.nan
        sliding[row, column] = 1.0 / slide if slide else np.nan
        bearing[row, column] = result["bearing_ratio"]
        qmax_grid[row, column] = result["qmax"]
        qmin_grid[row, column] = result["qmin"]
        volume[row, column] = concrete(float(toe), float(heel))
        steel[row, column] = max(result["as_wall_req"],
                                 result["as_base_req"])

answered = int(np.count_nonzero(~np.isnan(bearing)))
print(f"\nSWEPT   {answered} walls answered, {refusals} refused")
if not_answered:
    print(f"   {len(not_answered)} call(s) did not answer for a reason that "
          f"is NOT about")
    print("      the wall: " + ", ".join(sorted(set(not_answered))))
    print("      Those are holes punched in the map by the RUN. Read them")
    print("      before you read the map.")

# -- The sign trap, counted ---------------------------------------------
# CLAIM: the bearing check fails through a NEGATIVE qmax while qmin stays
# at zero, so watching qmin never catches it.
# CONTROL: count what each test catches. If qmin never moved AND qmax
# never went negative, both counts would be zero and the claim would be
# untestable rather than true.
negative_qmax = int(np.count_nonzero(qmax_grid < 0))
negative_qmin = int(np.count_nonzero(qmin_grid < 0))
moved_qmin = int(np.count_nonzero(qmin_grid > 0))
print("\nTHE SIGN TRAP IN THE BEARING CHECK")
print(f"   cells with qmax < 0 : {negative_qmax}")
print(f"   cells with qmin < 0 : {negative_qmin}")
print(f"   cells with qmin > 0 : {moved_qmin}")
if negative_qmax:
    worst_cell = np.unravel_index(np.nanargmin(qmax_grid), qmax_grid.shape)
    print(f"   the worst: toe {TOES[worst_cell[1]]:.2f} m, heel "
          f"{HEELS[worst_cell[0]]:.2f} m gives qmax "
          f"{qmax_grid[worst_cell]:.2f} kPa with qmin "
          f"{qmin_grid[worst_cell]:.2f}")
if negative_qmax:
    print(f"   -> a test on qmin catches {negative_qmin} of the "
          f"{negative_qmax} bad cells.")
    print("      Use `qmax > 0 and 0 < bearing_ratio <= 1`. The qmin")
    print(f"      column is the control: it moves on {moved_qmin} cells, so "
          f"it is")
    print("      alive - it simply never carries the sign change.")
else:
    print("   -> nothing on this grid drives qmax negative, so this run")
    print("      says nothing about the trap either way. Shrink the heel")
    print("      range until it does before quoting the counts above.")

# -- The feasible region ------------------------------------------------
usable = ((overturning <= 1.0) & (sliding <= 1.0) & (bearing <= 1.0)
          & (qmax_grid > 0))
count = int(np.count_nonzero(usable))
print(f"\nTHE FEASIBLE REGION   {count} of {answered} walls pass all three "
      f"checks")

CHECKS = {"overturning": overturning, "sliding": sliding,
          "bearing": bearing}
governing = np.full_like(overturning, np.nan)
names = list(CHECKS)
for row in range(len(HEELS)):
    for column in range(len(TOES)):
        values = [CHECKS[name][row, column] for name in names]
        if any(np.isnan(value) for value in values):
            continue
        governing[row, column] = int(np.argmax(values))

print(f"   {'check':>14} {'governs on':>11}")
counted = {}
for index, name in enumerate(names):
    counted[name] = int(np.count_nonzero(governing == index))
    print(f"   {name:>14} {counted[name]:>8} cells")
busiest = max(counted, key=counted.get)
if counted[busiest] > 0.8 * sum(counted.values()):
    print(f"   -> the textbook picture is a three-way tug of war. On THIS")
    print(f"      wall it is not: {busiest} is the worst check on")
    print(f"      {counted[busiest]} of the {sum(counted.values())} cells, "
          f"and the other two are")
    print("      nowhere near it over most of the map. That is worth")
    print("      knowing before spending a design meeting on the heel")
    print("      length: the lever that matters here is the one that")
    print("      resists sliding.")

if count:
    priced = np.where(usable, volume, np.nan)
    best = np.unravel_index(np.nanargmin(priced), priced.shape)
    best_toe = float(TOES[best[1]])
    best_heel = float(HEELS[best[0]])
    print(f"\n   least concrete inside it: toe {best_toe:.2f} m, heel "
          f"{best_heel:.2f} m")
    print(f"     {priced[best]:.3f} m3 per metre run, base "
          f"{best_toe + best_heel + STEM_BASE:.2f} m wide")
    print(f"     utilisations: overturning {overturning[best]:.3f}, "
          f"sliding {sliding[best]:.3f}, bearing {bearing[best]:.3f}")
else:
    best_toe, best_heel = 0.55, 2.50
    print("\n   nothing on the grid passes; the drawing below uses the "
          "parity wall")

chosen = wall(best_toe, best_heel)
# Everything from here down - the section, the pressure diagram, the
# sensitivity table - is this one wall, so say plainly that it was not
# answered rather than reaching into a None further on.
if chosen is None:
    raise SystemExit(
        "the wall the map picked was not answered, so there is no section "
        "to draw"
        + (": " + ", ".join(sorted(set(not_answered))) if not_answered
           else " - the engine refused this base"))
print(f"\nTHE WALL THE MAP PICKS   toe {best_toe:.2f} m, heel "
      f"{best_heel:.2f} m")
print(f"   governing load case {chosen['governing_lc']}")
print(f"   SF overturning {chosen['sf_overturning']:.3f}, sliding "
      f"{chosen['sf_sliding']:.3f}")
print(f"   bearing qmax {chosen['qmax']:.2f} / qmin {chosen['qmin']:.2f} kPa"
      f" against {ALLOWABLE:.0f} allowable")
print(f"   stem steel {chosen['as_wall_req']:.0f} mm2/m, base steel "
      f"{chosen['as_base_req']:.0f} mm2/m")
worst_index = max(range(POINTS), key=lambda i: chosen["m_wall"][i])
print(f"   peak stem moment {chosen['m_wall'][worst_index]:.1f} kNm/m at "
      f"{chosen['heights'][worst_index]:.2f} m below the top of the stem")
print(f"   largest stem crack {max(chosen['wall_cw'][:POINTS]):.3f} mm, "
      f"base crack {max(chosen['base_cw'][:POINTS]):.3f} mm")
print(f"   engine crack verdict: "
      f"{'OK' if chosen['crack_ok'] else 'EXCEEDED'}")

# -- What the answer is sensitive to ------------------------------------
print("\nWHAT THE ANSWER IS SENSITIVE TO")
print(f"   {'variable':>16} {'value':>8} {'SF ovt':>8} {'SF slide':>9} "
      f"{'qmax':>8} {'As wall':>9}")
sensitivity = {}
for name, key, values in (
        ("water table (m)", "hw", (0.0, 1.0, 2.0, 2.8, 3.5, 4.2)),
        ("friction (deg)", "theta", (20.0, 24.0, 27.0, 30.0, 34.0, 38.0)),
        ("fill slope (deg)", "alpha", (0.0, 5.0, 9.0, 14.0, 18.0)),
):
    rows = []
    for value in values:
        result = wall(best_toe, best_heel, **{key: float(value)})
        if result is None:
            print(f"   {name:>16} {value:>8.1f} {'refused':>8}")
            continue
        rows.append((value, result["sf_overturning"], result["sf_sliding"],
                     result["qmax"], result["as_wall_req"]))
        print(f"   {name:>16} {value:>8.1f} {rows[-1][1]:>8.3f} "
              f"{rows[-1][2]:>9.3f} {rows[-1][3]:>8.2f} "
              f"{rows[-1][4]:>9.0f}")
    sensitivity[name] = rows

for name, rows in sensitivity.items():
    if len(rows) < 2:
        continue
    slide = [row[2] for row in rows]
    steel_range = [row[4] for row in rows]
    print(f"   {name}: sliding factor {min(slide):.3f} to {max(slide):.3f} "
          f"({max(slide) / min(slide):.2f}x), stem steel "
          f"{min(steel_range):.0f} to {max(steel_range):.0f} mm2/m")

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(2, 2, figsize=(15, 11))
figure.patch.set_facecolor("white")

# 1. The wall, to scale, with the bearing pressure under it.
section = axes[0][0]
base_width = best_toe + best_heel + STEM_BASE
stem_top_y = STEM_HEIGHT
outline_x = [0.0, base_width, base_width, best_toe + STEM_BASE,
             best_toe + STEM_TOP, best_toe, 0.0]
outline_y = [0.0, 0.0, BASE_THICKNESS, BASE_THICKNESS, stem_top_y,
             stem_top_y, BASE_THICKNESS]
section.fill(outline_x, outline_y, facecolor="0.82", edgecolor="0.25",
             linewidth=1.8, zorder=3)
section.fill([best_toe + STEM_BASE - 0.15, best_toe + STEM_BASE + 0.15,
              best_toe + STEM_BASE + 0.15, best_toe + STEM_BASE - 0.15],
             [0.0, 0.0, -KEY_DEPTH, -KEY_DEPTH], facecolor="0.82",
             edgecolor="0.25", linewidth=1.8, zorder=3)

# Retained fill behind the stem, and the soil in front.
fill_top = stem_top_y + best_heel * np.tan(np.radians(ALPHA))
section.fill([best_toe + STEM_BASE, base_width, base_width,
              best_toe + STEM_BASE],
             [BASE_THICKNESS, BASE_THICKNESS, fill_top, stem_top_y],
             facecolor="#c8a165", alpha=0.35, zorder=1)
section.fill([0.0, best_toe, best_toe, 0.0],
             [BASE_THICKNESS, BASE_THICKNESS,
              BASE_THICKNESS + SOIL_IN_FRONT,
              BASE_THICKNESS + SOIL_IN_FRONT],
             facecolor="#c8a165", alpha=0.2, zorder=1)
if WATER > 0:
    section.plot([best_toe + STEM_BASE, base_width], [WATER, WATER],
                 color="#3a7ca5", linewidth=1.6, zorder=4)
    section.annotate("water table", (base_width, WATER),
                     textcoords="offset points", xytext=(-70, 5),
                     fontsize=8, color="#3a7ca5")

# The bearing pressure, drawn as the engine reports it.
scale = 1.2 / max(chosen["qmax"], 1.0)
section.fill([0.0, base_width, base_width, 0.0],
             [0.0, 0.0, -chosen["qmax"] * scale, -chosen["qmin"] * scale],
             facecolor="#b03030", alpha=0.35, edgecolor="#b03030",
             linewidth=1.4, zorder=2)
section.annotate(f"qmax {chosen['qmax']:.1f} kPa",
                 (base_width, -chosen["qmax"] * scale),
                 textcoords="offset points", xytext=(-100, -14),
                 fontsize=8, color="#b03030")
section.annotate(f"qmin {chosen['qmin']:.1f} kPa",
                 (0.0, -chosen["qmin"] * scale),
                 textcoords="offset points", xytext=(-6, -26), fontsize=8,
                 ha="right", color="#b03030")

section.annotate(
    f"SF overturning {chosen['sf_overturning']:.2f}\n"
    f"SF sliding {chosen['sf_sliding']:.2f}\n"
    f"stem steel {chosen['as_wall_req']:.0f} mm2/m\n"
    f"base steel {chosen['as_base_req']:.0f} mm2/m",
    (0.02, 0.97), xycoords="axes fraction", va="top", fontsize=8.5,
    bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.9,
              edgecolor="0.7"))
section.set_aspect("equal")
section.set_xlim(-0.4, base_width + 0.4)
section.set_ylim(-KEY_DEPTH - 1.6, fill_top + 0.4)
section.set_xlabel("m")
section.set_ylabel("m")
section.set_title(f"The wall the map picks - toe {best_toe:.2f} m, "
                  f"heel {best_heel:.2f} m\n"
                  f"the pressure block under the base is the engine's own "
                  f"qmax/qmin", fontsize=10)

# 2. The feasible region.
chart = axes[0][1]
mesh_t, mesh_h = np.meshgrid(TOES, HEELS)
shade = chart.contourf(mesh_t, mesh_h, np.where(usable, volume, np.nan),
                       levels=18, cmap="YlGnBu")
figure.colorbar(shade, ax=chart, label="concrete (m3 per metre run)")
chart.contourf(mesh_t, mesh_h, np.where(usable, np.nan, 1.0),
               levels=[0.5, 1.5], colors=["0.88"])
palette = {"overturning": "#2ca02c", "sliding": "#ff7f0e",
           "bearing": "#d62728"}
for name, surface in CHECKS.items():
    if np.nanmin(surface) > 1.0 or np.nanmax(surface) < 1.0:
        continue
    line = chart.contour(mesh_t, mesh_h, surface, levels=[1.0],
                         colors=palette[name], linewidths=2.4)
    chart.clabel(line, fmt={1.0: name}, fontsize=8)
if count:
    chart.plot(best_toe, best_heel, marker="*", markersize=22,
               color="white", markeredgecolor="black", zorder=6)
chart.set_xlabel("toe projection b (m)")
chart.set_ylabel("heel projection d (m)")
chart.set_title("Concrete inside the feasible region\n"
                "grey: fails at least one of the three checks", fontsize=10)

# 3. The stem, down its own height.
stem = axes[1][0]
heights = chosen["heights"][:POINTS]
moment = chosen["m_wall"][:POINTS]
stem.fill_betweenx(heights, 0, moment, color="#4c78a8", alpha=0.35)
stem.plot(moment, heights, color="#1f4e79", linewidth=2.0,
          label="bending moment")
stem.invert_yaxis()          # 0 at the top of the stem
stem.set_xlabel("stem moment (kNm/m)")
stem.set_ylabel("metres below the top of the stem")
stem.set_title("The stem's own bending moment, position by position",
               fontsize=10)
crack = stem.twiny()
crack.plot(chosen["wall_cw"][:POINTS], heights, color="#b03030",
           linewidth=1.6, linestyle="--", label="crack width")
crack.set_xlabel("crack width (mm)", color="#b03030")
# The y axis is inverted, so "upper" is the top of the stem - where
# both curves are near zero and there is room for a legend.
stem.legend(loc="upper right", fontsize=8)
crack.legend(loc="center right", fontsize=8)
stem.grid(True, linewidth=0.3, color="0.88")

# 4. Sensitivity.
sensitive = axes[1][1]
markers = {"water table (m)": "o", "friction (deg)": "s",
           "fill slope (deg)": "^"}
tones = {"water table (m)": "#3a7ca5", "friction (deg)": "#59a14f",
         "fill slope (deg)": "#c07000"}
for name, rows in sensitivity.items():
    if len(rows) < 2:
        continue
    # Normalised on its own range so three different variables share one
    # axis - the shape of each line is the point, not its position.
    span = max(row[0] for row in rows) - min(row[0] for row in rows)
    base = min(row[0] for row in rows)
    xs = [(row[0] - base) / span * 100.0 for row in rows]
    sensitive.plot(xs, [row[2] for row in rows], marker=markers[name],
                   markersize=6, linewidth=2.0, color=tones[name],
                   label=f"{name}  ({base:.0f} to {base + span:.0f})")
sensitive.axhline(1.5, color="black", linestyle="--", linewidth=1.6)
sensitive.annotate("required sliding factor 1.5", (2, 1.55), fontsize=8)
sensitive.set_xlabel("how far along its own range the variable is (%)")
sensitive.set_ylabel("sliding safety factor")
sensitive.set_title("What the answer is sensitive to\n"
                    "the water table is not one variable among three",
                    fontsize=10)
sensitive.legend(fontsize=8)
sensitive.grid(True, linewidth=0.3, color="0.85")

figure.suptitle(
    f"Retaining wall section and sizing map - {CODE}\n"
    f"{STEM_HEIGHT:.1f} m stem, water at {WATER:.1f} m, theta "
    f"{THETA:.0f} deg, delta {DELTA:.0f} deg, fill slope {ALPHA:.0f} deg, "
    f"fcu {FCU:.0f} MPa, allowable {ALLOWABLE:.0f} kPa  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "retaining_wall_section_and_sizing.png")
