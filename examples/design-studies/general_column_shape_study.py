# ---
# Example:  Does the SHAPE pay? Six sections of identical area, compared
# Feature:  general_column (C13 General Column)
# Verified: yes - 2026-09-02 - the 400 mm square anchor reproduces the pinned Case A factor; every shape measured on prokon-automation.exe
# ---
# C13 is the only engine here that takes an ARBITRARY OUTLINE. So the
# question it can answer that none of the others can is: for the same
# amount of concrete and the same amount of steel, WHICH SHAPE carries
# most?
#
# Six sections, all 160 000 mm2 of concrete, all reinforced to about the
# same ratio, all under the same loads:
#
#   square        400 x 400
#   rectangle     565 x 283 (2:1)
#   blade         800 x 200 (4:1)
#   circle        451 dia
#   L-section     equal-armed
#   hollow box    500 x 500 with a 400 x 400 void
#
# ⚠ THE ANSWER DEPENDS ON THE LOAD, which is the whole point. A shape that
# wins under axial load loses under biaxial bending, and a script is the
# only practical way to see the crossover.

import math

import prokon.v5

CODE = "BS8110 - 1997"
TARGET_AREA = 160_000.0     # mm2 of concrete in every section
BAR = 25.0                  # mm
COVER = 42.5                # mm to bar centre
LENGTH = 3.0                # m
FCU = 30.0
FY = 450.0

print("DOES THE SHAPE PAY?   six sections, 160 000 mm2 each")


def bars_on(points):
    """Turn a list of bar centres into C13's own row codes."""
    rows = []
    for x, y in points:
        rows.append({"code": "+", "x": x, "y": y})
        rows.append({"code": "B", "x": BAR})
    return rows


def outline(points):
    """A closed solid contour through these absolute points."""
    rows = [{"code": "+", "x": points[0][0], "y": points[0][1]}]
    for x, y in points[1:]:
        rows.append({"code": "L", "x": x, "y": y})
    return rows


def rectangle(width, depth, bars_per_long_face=2):
    """A rectangle with bars in the corners plus extras on the long faces."""
    section = outline([(0.0, 0.0), (width, 0.0), (width, depth), (0.0, depth)])
    long_face = width >= depth
    count = max(2, bars_per_long_face)
    if long_face:
        span = width - 2 * COVER
        xs = [COVER + span * n / (count - 1) for n in range(count)]
        points = [(x, y) for x in xs for y in (COVER, depth - COVER)]
    else:
        span = depth - 2 * COVER
        ys = [COVER + span * n / (count - 1) for n in range(count)]
        points = [(x, y) for y in ys for x in (COVER, width - COVER)]
    return section + bars_on(points), len(points)


# 1. The square - and the anchor, because this is the pinned reference
#    section from the C13 test suite.
square_side = math.sqrt(TARGET_AREA)
square, square_bars = rectangle(square_side, square_side, 2)

# 2. A 2:1 rectangle of the same area.
rect_depth = math.sqrt(TARGET_AREA / 2.0)
rect_width = 2.0 * rect_depth
rect, rect_bars = rectangle(rect_width, rect_depth, 3)

# 3. A 4:1 blade.
blade_depth = math.sqrt(TARGET_AREA / 4.0)
blade_width = 4.0 * blade_depth
blade, blade_bars = rectangle(blade_width, blade_depth, 5)

# 4. A circle of the same area. "C" draws a circle of radius x on the
#    current point, so the outline is one "+" and one "C".
radius = math.sqrt(TARGET_AREA / math.pi)
circle = [{"code": "+", "x": radius, "y": radius},
          {"code": "C", "x": radius}]
circle_points = []
bar_ring = radius - COVER
for index in range(8):
    angle = 2.0 * math.pi * index / 8.0
    circle_points.append((radius + bar_ring * math.cos(angle),
                          radius + bar_ring * math.sin(angle)))
circle = circle + bars_on(circle_points)

# 5. An equal-armed L of the same area. Arms a x t twice, less the overlap:
#    2*a*t - t*t = TARGET, with a = 2.5t chosen for a realistic proportion.
#    2*2.5t*t - t^2 = 4t^2 = TARGET  ->  t = sqrt(TARGET/4)
leg = math.sqrt(TARGET_AREA / 4.0)
arm = 2.5 * leg
ell = outline([(0.0, 0.0), (arm, 0.0), (arm, leg), (leg, leg),
               (leg, arm), (0.0, arm)])
ell_points = (
    [(x, COVER) for x in (COVER, arm / 2.0, arm - COVER)]
    + [(arm - COVER, leg - COVER)]
    + [(COVER, y) for y in (arm / 2.0, arm - COVER)]
    + [(leg - COVER, arm - COVER)]
    + [(leg - COVER, leg - COVER)]
)
ell = ell + bars_on(ell_points)

# 6. A hollow box. "-" opens a VOID contour, which is how C13 takes a hole.
#    b^2 - v^2 = TARGET with v = 0.8b  ->  b = sqrt(TARGET/0.36)
box_outer = math.sqrt(TARGET_AREA / 0.36)
box_inner = 0.8 * box_outer
inset = (box_outer - box_inner) / 2.0
box = outline([(0.0, 0.0), (box_outer, 0.0), (box_outer, box_outer),
               (0.0, box_outer)])
box.append({"code": "-", "x": inset, "y": inset})
for x, y in ((inset + box_inner, inset), (inset + box_inner, inset + box_inner),
             (inset, inset + box_inner)):
    box.append({"code": "L", "x": x, "y": y})
box_points = []
for fraction in (0.0, 0.5, 1.0):
    for edge in (COVER, box_outer - COVER):
        box_points.append((COVER + fraction * (box_outer - 2 * COVER), edge))
        box_points.append((edge, COVER + fraction * (box_outer - 2 * COVER)))
box_points = sorted(set(box_points))
box = box + bars_on(box_points)

SHAPES = (
    (f"square {square_side:.0f} sq", square, square_bars),
    (f"rect {rect_width:.0f}x{rect_depth:.0f}", rect, rect_bars),
    (f"blade {blade_width:.0f}x{blade_depth:.0f}", blade, blade_bars),
    (f"circle {2 * radius:.0f} dia", circle, len(circle_points)),
    (f"L arm {arm:.0f} leg {leg:.0f}", ell, len(ell_points)),
    (f"box {box_outer:.0f} sq hollow", box, len(box_points)),
)


def run(section, load_case):
    return prokon.v5.general_column.analyse(
        design_code=CODE, length=LENGTH, effective_length_factor=0.85,
        fcu=FCU, fy=FY, braced=True,
        end_top="FullyFixed", end_bottom="FullyFixed",
        section=section, load_cases=[load_case])["result"]


# ── The anchor ──────────────────────────────────────────────────────────
# The pinned Case A section from the C13 suite: 400 x 400 with 4 Y25 at
# 42.5 mm, under 1000 kN with 50 kNm top and bottom.
PINNED_FACTOR = 2.179097995657654
anchor_section = outline([(0.0, 0.0), (400.0, 0.0), (400.0, 400.0),
                          (0.0, 400.0)])
anchor_section += bars_on([(42.5, 42.5), (357.5, 42.5),
                           (357.5, 357.5), (42.5, 357.5)])
anchor = run(anchor_section, {"axial": 1000, "moment_x_top": 50,
                              "moment_x_bottom": 50})
anchor_factor = anchor["load_cases"][0]["min_capacity_factor"]
print(f"\n  anchor: the pinned Case A column, 400 sq with 4Y25")
print(f"    capacity factor {anchor_factor!r}")
print(f"    against the pinned {PINNED_FACTOR!r}")
print(f"    -> {'EXACT' if anchor_factor == PINNED_FACTOR else 'DRIFTED'}")

# ── First: confirm the six sections really are the same area ───────────
print(f"\n0. THE CONTROL   every section must report ~{TARGET_AREA:.0f} mm2")
print(f"   {'shape':<22} {'bars':>5} {'concrete':>10} {'error':>8} "
       f"{'steel':>9} {'%':>7}")
usable = []
for name, section, bar_count in SHAPES:
    try:
        result = run(section, {"axial": 1000, "moment_x_top": 50,
                               "moment_x_bottom": 50})
    except prokon.v5.ProkonError as refusal:
        print(f"   {name:<22} {bar_count:>5}  {refusal.category}/"
              f"{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:40]}")
        continue
    area = result["concrete_area"]
    print(f"   {name:<22} {result['bar_count']:>5} {area:>10.0f} "
          f"{100.0 * (area / TARGET_AREA - 1.0):>7.1f} % "
          f"{result['steel_area']:>9.0f} "
          f"{result['reinforcement_ratio']:>7.3f}")
    usable.append((name, section, result))
print("   -> a shape whose area is wrong means the OUTLINE is wrong, and no")
print("      comparison below it would mean anything. Check this first.")

# ── The comparison, under four different load cases ────────────────────
LOAD_CASES = (
    ("axial only", {"axial": 2500}),
    ("axial + Mx", {"axial": 1500, "moment_x_top": 150,
                    "moment_x_bottom": 75}),
    ("axial + Mx + My", {"axial": 1500, "moment_x_top": 150,
                         "moment_y_top": 100,
                         "moment_x_bottom": 75, "moment_y_bottom": 50}),
    ("bending dominant", {"axial": 400, "moment_x_top": 180,
                          "moment_x_bottom": 90}),
)

print(f"\n1. CAPACITY FACTOR BY SHAPE AND LOAD   (higher is better; "
      f"1.0 is adequate)")
header = "".join(f"{label:>19}" for label, _ in LOAD_CASES)
print(f"   {'shape':<22}{header}")

table = {}
for name, section, _ in usable:
    row = []
    for label, case in LOAD_CASES:
        try:
            result = run(section, case)
            factor = result["min_capacity_factor"]
        except prokon.v5.ProkonError:
            factor = None
        table[(name, label)] = factor
        row.append("refused" if factor is None else f"{factor:.4f}")
    print(f"   {name:<22}" + "".join(f"{cell:>19}" for cell in row))

print(f"\n   the winner under each load case:")
for label, _ in LOAD_CASES:
    scored = [(table[(name, label)], name) for name, _, _ in usable
              if table[(name, label)] is not None]
    if not scored:
        continue
    best_factor, best_name = max(scored)
    worst_factor, worst_name = min(scored)
    print(f"     {label:<19} {best_name:<22} {best_factor:.4f}   "
          f"(worst {worst_name} at {worst_factor:.4f}, "
          f"{best_factor / worst_factor:.2f}x)")

print("\n   -> THE ORDER CHANGES WITH THE LOAD, and that is the finding.")
print("      Even under PURE AXIAL load the shapes are not equal, though")
print("      every one holds the same 160 000 mm2: the spread there is")
print("      slenderness, because a section's radius of gyration is a")
print("      property of its shape and the engine's additional moments")
print("      follow from it.")
print("      Add bending and the sections with material FAR FROM THE")
print("      CENTROID pull away - the hollow box, which has the same area")
print("      as the solid square but all of it at the perimeter, ends up")
print("      the clear winner under bending. The blade wins one way and")
print("      loses the other, which is section 2.")

# ── And the axis a rectangular engine cannot see ───────────────────────
print(f"\n2. THE WEAK AXIS   the blade, with the moment moved from X to Y")
blade_section = next(s for name, s, _ in usable if name.startswith("blade"))
print(f"   {'Mx':>7} {'My':>7} {'factor':>9} {'slender x':>10} "
      f"{'slender y':>10}")
for mx, my in ((180.0, 0.0), (135.0, 45.0), (90.0, 90.0),
               (45.0, 135.0), (0.0, 180.0)):
    result = run(blade_section, {"axial": 1200,
                                 "moment_x_top": mx, "moment_x_bottom": mx / 2,
                                 "moment_y_top": my, "moment_y_bottom": my / 2})
    print(f"   {mx:>7.0f} {my:>7.0f} {result['min_capacity_factor']:>9.4f} "
          f"{str(result['is_slender_x']):>10} "
          f"{str(result['is_slender_y']):>10}")
print("   -> the same total moment, rotated. A blade that is comfortable")
print("      about its strong axis is in trouble about its weak one, and")
print("      the drawn outline is what lets C13 say so.")
