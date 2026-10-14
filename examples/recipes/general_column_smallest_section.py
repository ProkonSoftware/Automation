# ---
# Example:  General column — goal-seek the smallest square column that works
# Feature:  general_column (C13 General Column)
# Verified: yes — 2026-09-02 — the 400 mm row matches the value pinned in the C13 test suite; exact on prokon-automation.exe
# ---
# The desktop program checks ONE column at a time. A script can search:
# here we shrink a square column until it stops working, and pick the
# smallest size that still carries the load — with a real safety margin,
# not a lucky pass.
#
# The section is rebuilt for every trial size by a small helper — that
# is the pattern to copy for any parametric geometry.

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"
LENGTH = 3.0                 # column length [m]
FCU, FY = 30.0, 450.0        # materials [MPa]
BAR_DIA = 25.0               # four corner bars [mm]
COVER = 30.0                 # cover to the bar surface [mm]

LOAD_CASES = [
    {"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50},  # kN, kNm
]

# A pass at 1.0007 is a pass by 0.07% — nothing you would build. Decide
# your own acceptance margin and let the script enforce it.
REQUIRED_FACTOR = 1.05


def square_section(size_mm):
    """A size x size outline with four corner bars, as engine rows."""
    a = COVER + BAR_DIA / 2          # face to bar centre: 42.5 mm
    b = size_mm - a
    return [
        {"code": "+", "x": 0,       "y": 0},
        {"code": "L", "x": size_mm, "y": 0},
        {"code": "L", "x": size_mm, "y": size_mm},
        {"code": "L", "x": 0,       "y": size_mm},
        {"code": "+", "x": a, "y": a}, {"code": "B", "x": BAR_DIA},
        {"code": "+", "x": b, "y": a}, {"code": "B", "x": BAR_DIA},
        {"code": "+", "x": b, "y": b}, {"code": "B", "x": BAR_DIA},
        {"code": "+", "x": a, "y": b}, {"code": "B", "x": BAR_DIA},
    ]


print(f"{'size':>6} {'factor':>8} {'utilisation':>12}  verdict")

first_feasible = None
chosen = None

for size in range(225, 425, 25):
    result = prokon.v5.general_column.analyse(
        design_code=DESIGN_CODE,
        length=LENGTH, fcu=FCU, fy=FY,
        section=square_section(float(size)),
        load_cases=LOAD_CASES,
    )["result"]

    factor = result["min_capacity_factor"]

    # An overstressed column is a RESULT, not an exception: the verdict
    # key flips and the loop reads it. (An exception here would mean the
    # request itself was wrong — that is a bug to fix, so let it raise.)
    if not result["has_feasible_design"]:
        verdict = "over-stressed"
    elif factor < REQUIRED_FACTOR:
        verdict = "passes, but under the required margin"
    else:
        verdict = "ok"

    print(f"{size:>6} {factor:>8.4f} {result['utilisation']:>12.4f}  {verdict}")

    if result["has_feasible_design"] and first_feasible is None:
        first_feasible = (size, factor)
    if factor >= REQUIRED_FACTOR and chosen is None:
        chosen = (size, factor)

# Measured with this load set: 225 fails (factor 0.848); 250 is the
# first feasible size — at a factor of 1.0007, a 0.07% margin; 275 is
# the first size that clears the 1.05 requirement (factor 1.165). The
# 400 row's 2.179 is the value pinned against the desktop program in
# the C13 test suite — the anchor that ties this sweep to the desktop.
size, factor = first_feasible
print(f"\nFirst size that passes at all: {size} mm  (factor {factor:.4f} - "
      f"a {100 * (factor - 1):.2f}% margin; too thin to build on)")

size, factor = chosen
print(f"Smallest size at >= {REQUIRED_FACTOR:.2f}:      {size} mm  "
      f"(factor {factor:.4f})")
