# ---
# Example:  Draw the section you just analysed
# Feature:  general_column (C13 General Column)
# Verified: yes - 2026-09-02 - the Case A section reproduces its pinned capacity factor and gross area; the drawing is written and re-read
# ---
# C13 takes an arbitrary outline as a list of row codes. That is powerful
# and it is easy to get wrong: a mistyped coordinate gives you a valid
# analysis of a section you did not mean.
#
# So DRAW IT. This recipe plots the outline and the bars from the SAME data
# the engine was given, and prints the engine's own reported gross area
# beside the area of the polygon as drawn. If those two disagree, the
# drawing is telling you the outline is wrong before the numbers do.
#
# ⚠ THE SHOELACE AREA IS THE CHECK, and it is the point of the file. The
# engine reports concrete_area; the script computes the polygon's area
# independently from the same coordinates. Agreement means the engine read
# the outline the way you drew it. Nothing else in the result says so.
#
# Uses matplotlib, bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # write a file, never open a window
import matplotlib.pyplot as plt

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
BAR = 25.0
COVER = 42.5


def build(outline, bar_points, bar=BAR):
    """C13's row codes from a polygon and a list of bar centres."""
    rows = [{"code": "+", "x": outline[0][0], "y": outline[0][1]}]
    for x, y in outline[1:]:
        rows.append({"code": "L", "x": x, "y": y})
    for x, y in bar_points:
        rows.append({"code": "+", "x": x, "y": y})
        rows.append({"code": "B", "x": bar})
    return rows


def shoelace(points):
    """The polygon's area, computed independently of the engine.

    The shoelace formula. Two lines, and it is the only way to know that
    the engine read your outline the way you drew it.
    """
    total = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


# ── The sections ────────────────────────────────────────────────────────
SQUARE = [(0.0, 0.0), (400.0, 0.0), (400.0, 400.0), (0.0, 400.0)]
SQUARE_BARS = [(42.5, 42.5), (357.5, 42.5), (357.5, 357.5), (42.5, 357.5)]

ELL = [(0.0, 0.0), (800.0, 0.0), (800.0, 350.0), (350.0, 350.0),
       (350.0, 800.0), (0.0, 800.0)]
ELL_BARS = ([(x, COVER) for x in (COVER, 280.0, 520.0, 800.0 - COVER)]
            + [(800.0 - COVER, 350.0 - COVER)]
            + [(COVER, y) for y in (280.0, 520.0, 800.0 - COVER)]
            + [(280.0, 800.0 - COVER), (350.0 - COVER, 800.0 - COVER)])

TEE = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 300.0), (650.0, 300.0),
       (650.0, 800.0), (350.0, 800.0), (350.0, 300.0), (0.0, 300.0)]
TEE_BARS = ([(x, COVER) for x in (COVER, 300.0, 700.0, 1000.0 - COVER)]
            + [(COVER, 300.0 - COVER), (1000.0 - COVER, 300.0 - COVER)]
            + [(x, 800.0 - COVER) for x in (350.0 + COVER, 650.0 - COVER)]
            + [(350.0 + COVER, 500.0), (650.0 - COVER, 500.0)])

SECTIONS = (
    ("Case A square 400", SQUARE, SQUARE_BARS,
     {"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50}),
    ("L core corner", ELL, ELL_BARS,
     {"axial": 4000, "moment_x_top": 220, "moment_y_top": 160,
      "moment_x_bottom": 110, "moment_y_bottom": 80}),
    ("T pilaster", TEE, TEE_BARS,
     {"axial": 2600, "moment_x_top": 180, "moment_x_bottom": 90}),
)

print("DRAW THE SECTION YOU JUST ANALYSED")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, Y{BAR:.0f} bars")

# ── The anchor ──────────────────────────────────────────────────────────
PINNED_FACTOR = 2.179097995657654
PINNED_AREA = 160000
anchor = prokon.v5.general_column.analyse(
    design_code=CODE, length=3.0, fcu=FCU, fy=FY,
    section=build(SQUARE, SQUARE_BARS),
    load_cases=[SECTIONS[0][3]])["result"]
print(f"\n  anchor: the Case A square")
print(f"    capacity factor "
      f"{anchor['load_cases'][0]['min_capacity_factor']!r}")
print(f"    pinned          {PINNED_FACTOR!r}")
print(f"    concrete_area   {anchor['concrete_area']!r}  "
      f"pinned {PINNED_AREA!r}")
exact = (anchor["load_cases"][0]["min_capacity_factor"] == PINNED_FACTOR
         and anchor["concrete_area"] == PINNED_AREA)
print(f"    -> {'EXACT on both' if exact else 'DRIFTED'}")

# ── Analyse, cross-check the outline, and draw ─────────────────────────
figure, axes = plt.subplots(1, len(SECTIONS),
                            figsize=(4.5 * len(SECTIONS), 5))
if len(SECTIONS) == 1:
    axes = [axes]

print(f"\n{'section':<22} {'drawn area':>12} {'engine area':>12} "
      f"{'agree?':>7} {'bars drawn':>11} {'counted':>8} {'factor':>8}")
print("-" * 90)

for panel, (name, outline, bar_points, load_case) in zip(axes, SECTIONS):
    result = prokon.v5.general_column.analyse(
        design_code=CODE, length=3.5, effective_length_factor=0.85,
        fcu=FCU, fy=FY, braced=True,
        end_top="FullyFixed", end_bottom="FullyFixed",
        section=build(outline, bar_points),
        load_cases=[load_case])["result"]

    drawn_area = shoelace(outline)
    engine_area = result["concrete_area"]
    # A tolerance, not equality: the two are computed by different code in
    # different languages. 0.1 % is far tighter than any drawing error.
    agree = abs(drawn_area - engine_area) / drawn_area < 0.001

    print(f"{name:<22} {drawn_area:>12.0f} {engine_area:>12.0f} "
          f"{'yes' if agree else 'NO':>7} {len(bar_points):>11} "
          f"{result['bar_count']:>8} "
          f"{result['min_capacity_factor']:>8.4f}")
    if not agree:
        print(f"{'':<22} -> the outline the engine read is NOT the polygon "
              f"you drew. Fix the row codes before reading any number.")
    if result["bar_count"] != len(bar_points):
        print(f"{'':<22} -> the engine counted "
              f"{result['bar_count']} bars, not {len(bar_points)}. A bar "
              f"outside the outline is silently dropped.")

    closed = list(outline) + [outline[0]]
    panel.plot([point[0] for point in closed],
               [point[1] for point in closed],
               color="0.2", linewidth=2.0)
    panel.fill([point[0] for point in closed],
               [point[1] for point in closed],
               color="0.88", zorder=0)
    for x, y in bar_points:
        panel.add_patch(plt.Circle((x, y), BAR / 2.0, color="0.15"))

    factor = result["min_capacity_factor"]
    panel.set_title(f"{name}\n"
                    f"{engine_area:.0f} mm2, "
                    f"{result['bar_count']} x Y{BAR:.0f} "
                    f"({result['reinforcement_ratio']:.2f} %)\n"
                    f"capacity factor {factor:.3f} "
                    f"{'OK' if factor >= 1.0 else 'OVERSTRESSED'}",
                    fontsize=9)
    panel.set_aspect("equal")
    panel.set_xlabel("x (mm)")
    panel.set_ylabel("y (mm)")
    panel.grid(True, linewidth=0.3, color="0.8")

figure.suptitle(f"General column sections - {CODE}", fontsize=11)
figure.tight_layout()

output = Path("column_sections.png")
figure.savefig(output, dpi=140)
plt.close(figure)

# A chart that was written is not the same as a chart that has content.
size = output.stat().st_size
print(f"\nWritten: {output.resolve()}")
print(f"  {size} bytes, "
      f"{'a real image' if size > 10_000 else 'SUSPICIOUSLY SMALL - check it'}")

print()
print("The shoelace column is the reason this recipe exists. An engine that")
print("mis-reads your outline still returns a capacity factor, and it will")
print("look entirely reasonable. Comparing the drawn area against the")
print("engine's own is two lines of arithmetic and it catches the whole")
print("class of error.")
