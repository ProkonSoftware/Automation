# ---
# Example:  Punching shear — how deep must the drop panel be?
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes — 2026-09-02 — the sweep reproduces the depth-vs-Asv ladder pinned in the C23 test suite; exact on prokon-automation.exe
# ---
# The desktop program checks ONE column head at a time, so sizing a drop
# panel means typing a depth, reading the answer, and typing another. A
# script sweeps the depth and reports the shallowest panel that carries
# the punching shear with no shear reinforcement at all — which is what a
# flat-slab designer usually wants, because shear links at a column head
# are slow to fix and easy to get wrong on site.
#
# Two checks decide it, and the script applies both explicitly:
#
#   1. the column FACE:  vu <= vcu   (no amount of reinforcement fixes this)
#   2. every PERIMETER:  asv == 0    (no shear reinforcement required)
#
# There is no single "passes" key to read instead. asv is the required
# area, so zero means "nothing needed" — that is the verdict.

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"
COL_A, COL_B = 400.0, 400.0     # column plan size [mm]
EDGE_X, EDGE_Y = 10000.0, 10000.0   # internal column: edges far away [mm]
FCU, FY, FYV = 35.0, 500.0, 500.0   # [MPa]
LOAD = [{"v": 800.0, "mx": 50.0, "my": 30.0}]   # kN, kNm, kNm

DEPTHS = range(150, 476, 25)    # effective depth of the panel [mm]


def check(effective_depth, flexural_steel=None):
    """Analyse one depth and return (face_ok, worst asv, governing perimeter)."""
    steel = flexural_steel or {}

    r = prokon.v5.punching_shear.analyse(
        design_code=DESIGN_CODE,
        col_width=COL_A, col_breadth=COL_B,
        effective_depth=float(effective_depth),
        nearest_edge_x=EDGE_X, nearest_edge_y=EDGE_Y,
        fcu=FCU, fy=FY, fyv=FYV,
        load_cases=LOAD,
        **steel,
    )["result"]

    critical = r["critical_load_case_index"]
    face_ok = r["vu"][critical] <= r["vcu"]

    worst = max(r["critical_perimeters"], key=lambda p: p["asv"])

    return face_ok, worst["asv"], worst["perimeter"], r["vu"][critical]


# ── The sweep, with no flexural steel entered ───────────────────────────
# Leaving asx_*/asy_* out means the engine reads the top steel as ZERO,
# which is the pessimistic reading: less concrete capacity, so more shear
# reinforcement. Good for a first pass — the answer is on the safe side.
print(f"{'de [mm]':>8} {'vu [MPa]':>9} {'face':>6} "
      f"{'worst Asv [mm2]':>16} {'at perimeter':>13}")

answer = None

for depth in DEPTHS:
    try:
        face_ok, asv, perimeter, vu = check(depth)
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            # A well-formed request the engine ran and declined. A normal
            # outcome in a search — carry on to the next depth.
            print(f"{depth:>8} {'-- no solution at this depth --':>47}")
            continue
        raise  # a typo or environment trouble is a real error

    print(f"{depth:>8} {vu:>9.4f} {'ok' if face_ok else 'OVER':>6} "
          f"{asv:>16.1f} {perimeter if asv > 0 else '-':>13}")

    if answer is None and face_ok and asv == 0:
        answer = depth

print(f"\nShallowest panel needing no shear reinforcement: de = {answer} mm")

# Measured, and worth knowing: the required steel does NOT fall smoothly
# with depth. Under BS8110 the first critical perimeter sits 1.5*de from
# the column face, so a deeper slab pushes the perimeter outwards as well
# as adding capacity, and the two effects pull in opposite directions.
# Search for the first depth that PASSES, never for a trend.

# ── The same sweep with the real top steel ──────────────────────────────
# asx_n / asy_n are the areas of flexural steel crossing critical
# perimeter n. The desktop works them out from the bar spacing you type;
# in a script you do the same arithmetic once. For the BS8110 family the
# band that perimeter n spans is:
#
#     width = column dimension + 2 * (n + 1) * 0.75 * de
#
# so the area crossing it is (width / spacing) * one bar's area.
BAR_DIA, SPACING = 16.0, 200.0      # T16 at 200 centres, both ways [mm]
BAR_AREA = 3.14159265358979 * BAR_DIA ** 2 / 4.0


def top_steel(effective_depth):
    """asx_1..asy_4 for T16 @ 200, the way the desktop derives them."""
    areas = {}

    for n in (1, 2, 3, 4):
        band = 2 * (n + 1) * 0.75 * effective_depth
        areas[f"asx_{n}"] = (COL_A + band) / SPACING * BAR_AREA
        areas[f"asy_{n}"] = (COL_B + band) / SPACING * BAR_AREA

    return areas


print(f"\nWith T{BAR_DIA:.0f} @ {SPACING:.0f} top steel both ways:")
print(f"{'de [mm]':>8} {'worst Asv [mm2]':>16}")

with_steel = None

for depth in DEPTHS:
    _, asv, _, _ = check(depth, top_steel(depth))

    print(f"{depth:>8} {asv:>16.1f}")

    if with_steel is None and asv == 0:
        with_steel = depth

print(f"\nWith the top steel counted: de = {with_steel} mm is enough")
print(f"Ignoring it costs {answer - with_steel} mm of slab.")
