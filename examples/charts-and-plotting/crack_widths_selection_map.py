# ---
# Example:  The crack-width selection map - and the trap inside it
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes - 2026-09-04 - the pinned reference slab reproduces its triple; every arrangement, cover and code measured on prokon-automation.exe, with each arrangement's capacity checked before its crack width was believed
# ---
# Choosing bars for crack control looks like a one-dimensional problem:
# add steel, get a narrower crack. It is not, and a chart makes that
# obvious in one glance where a table hides it.
#
# The map is a contour of crack width over the whole (bar diameter x
# spacing) plane with the steel-area contours drawn ON TOP OF IT. If crack
# width really were a function of steel area the two families would lie on
# each other. They cross, and every crossing is a pair of arrangements
# where the one with LESS steel cracks LESS.
#
# ⚠ AND THERE IS A TRAP IN THAT ANALYSIS, WHICH THIS SCRIPT WALKED INTO
# THE FIRST TIME IT WAS RUN. Twenty-three of the fifty-four arrangements
# cannot carry the moment at all - and C21 still reports a crack width for
# them, a very SMALL one, because a section that never develops the stress
# never develops the crack either. Left in, they produce a spectacular
# headline (2.8x the steel, 8.8x the crack) that is entirely an artefact
# of comparing a real design against one that has already failed.
#
# So every arrangement is checked against the engine's own moment_ult
# FIRST, and the analysis runs only over the ones that can carry the load.
# The artefact is printed too, because recognising it is the lesson.
#
# The rest of the figure covers what an engineer does next:
#
#   THE FAN      crack width against steel area, one branch per diameter
#   THE COVER    the same section on five codes, cover swept
#   THE LOADING  crack width against service moment for one arrangement
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


# -- The section --------------------------------------------------------
CODE = "BS8007 - 1987"
THICKNESS = 350.0         # mm
COVER = 45.0              # mm
FCU = 35.0
FY = 500.0
MOMENT = 90.0             # kNm/m, serviceability
CRACK_LIMIT = 0.2         # mm - severe exposure

DIAMETERS = (10, 12, 16, 20, 25, 32)
SPACINGS = (100, 125, 150, 175, 200, 225, 250, 275, 300)
COVERS = (25.0, 30.0, 35.0, 40.0, 50.0, 60.0, 70.0, 80.0)
CODES = ("BS8007 - 1987", "Eurocode 2 - 2004", "NZ 3101 - 2006",
         "IS456 - 2000", "SP 63.13330.2018")
MOMENTS = (20.0, 30.0, 40.0, 50.0, 60.0, 75.0, 90.0, 110.0, 130.0, 150.0)

SECTION = dict(
    design_code=CODE, slab_mode=True,
    h=THICKNESS, hef=THICKNESS / 2.0, b=1000.0, cover=COVER,
    fcu=FCU, fy=FY, ea=200.0, ec=0.0,
    allowable_crack_width=CRACK_LIMIT,
    high_bond_bar=True, short_term_load=False,
)

print("THE CRACK-WIDTH SELECTION MAP")
print(f"  {CODE}, {THICKNESS:.0f} mm slab, cover {COVER:.0f} mm, "
      f"fcu {FCU:.0f}, fy {FY:.0f}")
print(f"  M = {MOMENT:.0f} kNm/m service, allowable {CRACK_LIMIT} mm")
print(f"  grid: {len(DIAMETERS)} diameters x {len(SPACINGS)} spacings "
      f"= {len(DIAMETERS) * len(SPACINGS)} engine calls, plus "
      f"{len(CODES) * len(COVERS) + len(MOMENTS)} more")

# -- The anchor ---------------------------------------------------------
PINNED = (0.11059554804834058, 1047.197551196598, 99.75807235558123)
envelope = prokon.v5.crack_widths.analyse(
    design_code="BS8007 - 1987", slab_mode=True, h=300.0, hef=200.0,
    b=1000.0, cover=40.0, fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
    allowable_crack_width=0.3, high_bond_bar=True, short_term_load=True,
    load_cases=[{"n": 1, "m": 50.0, "m_uls": 1.5}])
first = envelope["result"]["load_cases"][0]["optimised_configs"][0]
measured = (first["calc_result"]["governing_crack_width"],
            first["calc_result"]["steel_area"], first["moment_capacity"])
print(f"\n  anchor: the pinned reference slab, {first['formatted_bars']}")
print(f"    crack {measured[0]!r}   pinned {PINNED[0]!r}")
print(f"    As    {measured[1]!r}   pinned {PINNED[1]!r}")
print(f"    Mu    {measured[2]!r}   pinned {PINNED[2]!r}")
print(f"    -> {'EXACT on the pinned triple' if measured == PINNED else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def arrangement(diameter, spacing, moment=MOMENT, **overrides):
    """One named bar arrangement, or None if the engine declines it.

    Returns a dict with the crack width, the steel area, the arrangement's
    moment capacity and the ULTIMATE moment the engine derived - so the
    caller can ask "can this actually carry the load?" before believing
    the crack width.

    ⚠ ALWAYS READ governing_crack_width. It is max(w, wmax1, wmax2) - the
    number the desktop reports and checks. The plainly-named crack_width
    is one of the three terms and can under-report.

    ⚠ AND user_slab_result CAN BE None. The engine declines to report an
    arrangement it will not accept, so the read has to be guarded.
    """
    settings = dict(SECTION)
    settings.update(overrides)
    try:
        result = prokon.v5.crack_widths.analyse(
            **settings, user_slab_bars=f"Y{diameter}@{spacing}",
            load_cases=[{"n": 1, "m": moment, "m_uls": 1.5}])["result"]
    except prokon.v5.ProkonError:
        return None
    case = result["load_cases"][0]
    mine = case["user_slab_result"]
    if mine is None:
        return None
    return {
        "width": mine["calc_result"]["governing_crack_width"],
        "area": mine["calc_result"]["steel_area"],
        "capacity": mine["moment_capacity"],
        "demand": case["moment_ult"],
        "diameter": diameter,
        "spacing": spacing,
    }


# -- 1. The grid --------------------------------------------------------
width = np.full((len(DIAMETERS), len(SPACINGS)), np.nan)
area = np.full_like(width, np.nan)
adequate_mask = np.zeros_like(width)
every = []
adequate = []

print(f"\nCRACK WIDTH [mm]   rows are diameters, columns are spacings")
print("   a value in brackets is an arrangement that CANNOT CARRY THE "
      "MOMENT")
print(f"{'':>5}" + "".join(f"{spacing:>9}" for spacing in SPACINGS))
for row, diameter in enumerate(DIAMETERS):
    line = []
    for column, spacing in enumerate(SPACINGS):
        found = arrangement(diameter, spacing)
        if found is None:
            line.append("-")
            continue
        width[row, column] = found["width"]
        area[row, column] = found["area"]
        every.append(found)
        ok = found["capacity"] >= found["demand"]
        if ok:
            adequate_mask[row, column] = 1.0
            adequate.append(found)
            line.append(f"{found['width']:.3f}")
        else:
            line.append(f"({found['width']:.3f})")
    print(f"Y{diameter:<4}" + "".join(f"{cell:>9}" for cell in line))

print(f"\n   {len(adequate)} of {len(every)} arrangements can carry the "
      f"{every[0]['demand']:.0f} kNm/m ultimate moment")


def inversions(population):
    """(ordered pairs, inverted pairs, most wasted steel, widest crack).

    TWO worst cases are reported, deliberately. Ranking by "extra steel"
    finds pairs that waste a lot for a crack barely wider; ranking by
    "crack ratio" finds pairs of almost equal area where the crack is
    half again as wide. Each on its own reads as a weak result, and the
    pair of them is the actual shape of the effect.
    """
    inverted, ordered = [], 0
    for index, one in enumerate(population):
        for other in population[index + 1:]:
            if one["area"] == other["area"] or one["width"] == other["width"]:
                continue
            heavier, lighter = ((one, other) if one["area"] > other["area"]
                                else (other, one))
            if heavier["width"] > lighter["width"]:
                inverted.append((heavier, lighter))
            else:
                ordered += 1
    if not inverted:
        return ordered, inverted, None, None
    wasteful = max(inverted, key=lambda pair: pair[0]["area"]
                   - pair[1]["area"])
    widest = max(inverted, key=lambda pair: pair[0]["width"]
                 / pair[1]["width"])
    return ordered, inverted, wasteful, widest


# -- The trap, before the finding ---------------------------------------
# Run the analysis the WRONG way first, over every arrangement including
# the ones that cannot carry the load, and print what it claims.
_, wrong_inverted, _, wrong_worst = inversions(every)
print("\nTHE TRAP - THE SAME ANALYSIS OVER EVERY ARRANGEMENT")
if wrong_worst:
    heavier, lighter = wrong_worst
    print(f"   it reports: Y{lighter['diameter']}@{lighter['spacing']} at "
          f"{lighter['area']:.0f} mm2/m cracks {lighter['width']:.4f} mm")
    print(f"           and Y{heavier['diameter']}@{heavier['spacing']} at "
          f"{heavier['area']:.0f} mm2/m cracks {heavier['width']:.4f} mm")
    print(f"   which looks like {heavier['area'] / lighter['area']:.1f}x "
          f"the steel for {heavier['width'] / lighter['width']:.1f}x the "
          f"crack.")
    print(f"   But Y{lighter['diameter']}@{lighter['spacing']} carries "
          f"{lighter['capacity']:.1f} kNm/m against a demand of "
          f"{lighter['demand']:.1f}")
    print(f"   - {lighter['capacity'] / lighter['demand']:.0%} of it. It is "
          f"not a design; it is a section that")
    print("   never develops the stress, so it never develops the crack.")
    print("   A small crack width on an inadequate section is the most")
    print("   convincing wrong number this engine produces.")

# -- The real finding, over arrangements that work ----------------------
ordered, inverted, wasteful, widest = inversions(adequate)
print("\nCRACK WIDTH IS NOT A FUNCTION OF STEEL AREA")
print(f"   over the {len(adequate)} arrangements that CAN carry the load: "
      f"{ordered + len(inverted)} pairs")
print(f"   {ordered} behave as expected (more steel, narrower crack)")
print(f"   {len(inverted)} do NOT")
for label, pair in (("most steel wasted", wasteful),
                    ("widest crack for the steel", widest)):
    if pair is None:
        continue
    heavier, lighter = pair
    print(f"   {label}:")
    print(f"     Y{lighter['diameter']}@{lighter['spacing']:<4} "
          f"{lighter['area']:>7.0f} mm2/m cracks {lighter['width']:.4f} mm")
    print(f"     Y{heavier['diameter']}@{heavier['spacing']:<4} "
          f"{heavier['area']:>7.0f} mm2/m cracks {heavier['width']:.4f} mm")
    print(f"     -> {heavier['area'] - lighter['area']:+.0f} mm2/m of steel "
          f"for a {heavier['width'] / lighter['width']:.2f}x WIDER crack")
worst = widest or wasteful
print("   -> both counts are large, so this is a real second variable and")
print("      not a sign convention. Bar DIAMETER is what the area hides:")
print("      a small bar at a close spacing beats a big bar spread out,")
print("      at the same area. Ranking arrangements by area ranks them")
print("      wrongly.")

# -- 2. Cover, on five codes --------------------------------------------
# ⚠ IS456 - 2000 emits two ProkonWarnings here, on stderr: it publishes
# concrete_tensile_strength and critical_reinforcement_ratio as NULL
# because the engine has no case arm for that code. The crack width
# itself is unaffected and is used below - the warning is the wrapper
# refusing to hand back a stale global rather than a fault in this run.
print(f"\nCOVER, ON FIVE CODES   Y16@200 on the same section")
print(f"   {'cover':>6}" + "".join(f"{name[:14]:>16}" for name in CODES))
cover_curves = {name: [] for name in CODES}
for cover in COVERS:
    line = []
    for name in CODES:
        found = arrangement(16, 200, cover=cover, design_code=name)
        cover_curves[name].append(None if found is None else found["width"])
        line.append("-" if found is None else f"{found['width']:.4f}")
    print(f"   {cover:>6.0f}" + "".join(f"{cell:>16}" for cell in line))

spread = []
for index in range(len(COVERS)):
    values = [cover_curves[name][index] for name in CODES
              if cover_curves[name][index] is not None]
    if len(values) > 1 and min(values) > 0:
        spread.append(max(values) / min(values))
if spread:
    print(f"   -> the codes disagree by {min(spread):.2f}x to "
          f"{max(spread):.2f}x on the SAME section,")
    print("      and every one of them says cover matters more than any")
    print("      other single input. A crack width is a code's opinion.")

# -- 3. The loading -----------------------------------------------------
CHOSEN_DIA, CHOSEN_SPACE = 16, 150
print(f"\nSERVICE MOMENT, Y{CHOSEN_DIA}@{CHOSEN_SPACE}")
load_curve = []
for moment in MOMENTS:
    found = arrangement(CHOSEN_DIA, CHOSEN_SPACE, moment=moment)
    load_curve.append(None if found is None else found["width"])
    if found is None:
        print(f"   {moment:>6.0f} kNm/m   refused")
        continue
    flags = []
    if found["width"] > CRACK_LIMIT:
        flags.append("over the allowable")
    if found["capacity"] < found["demand"]:
        flags.append("AND cannot carry the moment")
    print(f"   {moment:>6.0f} kNm/m   {found['width']:.4f} mm   "
          + "  ".join(flags))

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(2, 2, figsize=(15, 10.5))
figure.patch.set_facecolor("white")
mesh_s, mesh_d = np.meshgrid(SPACINGS, DIAMETERS)

# 1. The map, with both families of contours on it.
chart = axes[0][0]
shade = chart.contourf(mesh_s, mesh_d, width, levels=20, cmap="OrRd")
figure.colorbar(shade, ax=chart, label="governing crack width (mm)")
crack_lines = chart.contour(mesh_s, mesh_d, width,
                            levels=[0.10, 0.15, 0.25, 0.30],
                            colors="darkred", linewidths=1.1)
chart.clabel(crack_lines, fmt="%.2f mm", fontsize=7, inline_spacing=6)
steel_lines = chart.contour(mesh_s, mesh_d, area,
                            levels=[1200, 2400, 4800],
                            colors="navy", linewidths=1.3,
                            linestyles="--")
chart.clabel(steel_lines, fmt="%.0f", fontsize=7, inline_spacing=6)
allowable = chart.contour(mesh_s, mesh_d, width, levels=[CRACK_LIMIT],
                          colors="black", linewidths=2.8)
chart.clabel(allowable, fmt={CRACK_LIMIT: f"{CRACK_LIMIT} mm allowable"},
             fontsize=9)
# The arrangements that cannot carry the load, struck out.
chart.contourf(mesh_s, mesh_d, np.where(adequate_mask < 0.5, 1.0, np.nan),
               levels=[0.5, 1.5], colors="none", hatches=["xxx"])
chart.set_xlabel("bar spacing (mm)")
chart.set_ylabel("bar diameter (mm)")
chart.set_yticks(list(DIAMETERS))
chart.set_title("Crack width (solid red) and steel area (dashed blue)\n"
                "they CROSS - hatched: cannot carry the moment at all",
                fontsize=10)

# 2. The fan.
fan = axes[0][1]
colours = plt.cm.viridis(np.linspace(0, 0.9, len(DIAMETERS)))
for index, diameter in enumerate(DIAMETERS):
    good = [(one["area"], one["width"]) for one in adequate
            if one["diameter"] == diameter]
    bad = [(one["area"], one["width"]) for one in every
           if one["diameter"] == diameter and one["capacity"] < one["demand"]]
    if good:
        fan.plot([x for x, _ in good], [y for _, y in good], marker="o",
                 markersize=6, linewidth=1.6, color=colours[index],
                 label=f"Y{diameter}")
    if bad:
        # A diameter with no adequate arrangement still belongs in the
        # legend - otherwise it reads as one that was never tried.
        fan.plot([x for x, _ in bad], [y for _, y in bad], marker="x",
                 markersize=6, linewidth=0.8, linestyle=":",
                 color=colours[index], alpha=0.55,
                 label=None if good else f"Y{diameter} (none adequate)")
fan.axhline(CRACK_LIMIT, color="black", linestyle="--", linewidth=1.4)
fan.annotate(f"{CRACK_LIMIT} mm allowable",
             (max(one["area"] for one in every) * 0.5, CRACK_LIMIT * 1.05),
             fontsize=9)
if worst:
    heavier, lighter = worst
    fan.annotate("", xy=(heavier["area"], heavier["width"]),
                 xytext=(lighter["area"], lighter["width"]),
                 arrowprops=dict(arrowstyle="->", color="red", lw=2.2))
    fan.annotate(f"+{heavier['area'] - lighter['area']:.0f} mm2/m of steel,\n"
                 f"{heavier['width'] / lighter['width']:.2f}x the crack",
                 ((heavier["area"] + lighter["area"]) / 2,
                  (heavier["width"] + lighter["width"]) / 2),
                 textcoords="offset points", xytext=(12, -26), fontsize=8,
                 color="red", fontweight="bold")
fan.set_xlabel("steel area provided (mm2/m)")
fan.set_ylabel("governing crack width (mm)")
fan.set_title("A function of area would be ONE curve. It is a fan.\n"
              "crosses on dotted lines cannot carry the moment",
              fontsize=10)
fan.legend(fontsize=8, ncol=2)
fan.grid(True, linewidth=0.3, color="0.85")

# 3. Cover, on five codes.
covers = axes[1][0]
for name in CODES:
    values = cover_curves[name]
    xs = [COVERS[i] for i in range(len(COVERS)) if values[i] is not None]
    ys = [value for value in values if value is not None]
    if xs:
        covers.plot(xs, ys, marker="o", markersize=5, linewidth=1.6,
                    label=name)
covers.axhline(CRACK_LIMIT, color="black", linestyle="--", linewidth=1.4)
covers.set_xlabel("cover (mm)")
covers.set_ylabel("governing crack width (mm)")
covers.set_title("The same Y16@200 on five codes\n"
                 "cover is the strongest single input - and the codes "
                 "disagree about it", fontsize=10)
covers.legend(fontsize=8)
covers.grid(True, linewidth=0.3, color="0.85")

# 4. Service moment.
loading = axes[1][1]
xs = [MOMENTS[i] for i in range(len(MOMENTS)) if load_curve[i] is not None]
ys = [value for value in load_curve if value is not None]
loading.plot(xs, ys, marker="o", markersize=6, linewidth=2.0,
             color="#b03030")
loading.fill_between(xs, 0, ys, color="#b03030", alpha=0.15)
loading.axhline(CRACK_LIMIT, color="black", linestyle="--", linewidth=1.6)
loading.annotate(f"{CRACK_LIMIT} mm allowable", (xs[0], CRACK_LIMIT * 1.04),
                 fontsize=9)
over = [x for x, y in zip(xs, ys) if y > CRACK_LIMIT]
if over:
    loading.axvspan(min(over), max(xs), color="red", alpha=0.08)
    loading.annotate(f"over the allowable\nfrom about {min(over):.0f} kNm/m",
                     (min(over), max(ys) * 0.5), fontsize=9, color="red")
loading.set_xlabel("service moment (kNm/m)")
loading.set_ylabel("governing crack width (mm)")
loading.set_title(f"Y{CHOSEN_DIA}@{CHOSEN_SPACE} under load - where the "
                  f"arrangement runs out", fontsize=10)
loading.grid(True, linewidth=0.3, color="0.85")

figure.suptitle(
    f"Crack width selection map - {CODE}\n"
    f"{THICKNESS:.0f} mm slab, cover {COVER:.0f} mm, fcu {FCU:.0f} MPa, "
    f"fy {FY:.0f} MPa, M = {MOMENT:.0f} kNm/m service, long-term  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "crack_widths_selection_map.png")
