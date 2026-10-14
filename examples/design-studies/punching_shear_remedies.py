# ---
# Example:  Punching shear - the four remedies, priced against each other
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes - 2026-09-02 - the reference head reproduces the pinned uo and perimeter-1 Asv; every remedy row measured on prokon-automation.exe
# ---
# A flat slab that fails punching has four ways out, and they are not
# interchangeable:
#
#   1. THICKEN THE SLAB          works everywhere, costs the whole floor
#   2. ENLARGE THE COLUMN        cheap locally, ugly, and often refused
#      by the architect
#   3. ADD A DROP PANEL          local, effective, formwork cost
#   4. ADD SHEAR REINFORCEMENT   cheapest concrete, most labour
#
# Only ONE of them fixes a failed COLUMN FACE. This script prices all four
# on the same overloaded head and says which checks each one can and
# cannot satisfy.
#
# ⚠ THE FACE CHECK HAS NO REINFORCEMENT REMEDY. vcu is a CEILING on the
# stress at the column face, not a capacity you can reinforce past. If the
# face fails, links are irrelevant - the concrete or the column has to
# grow. Section 0 establishes that before anything is priced.

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 35.0
FY = 500.0
FYV = 500.0
BAY = 7.5              # m
COVER = 35.0           # mm to the top bar centre

print("PUNCHING SHEAR - THE FOUR REMEDIES")


def head(col_width, col_breadth, depth, shear, steel_ratio=1.0,
         code=CODE, edge_x=15_000.0, edge_y=15_000.0):
    """One column head. Flexural steel scales with the perimeter width."""
    def across(perimeter):
        reach = col_width + 2 * 1.5 * perimeter * depth
        return steel_ratio * 1200.0 * min(reach, BAY * 1000.0) / 1000.0

    return prokon.v5.punching_shear.analyse(
        design_code=code,
        col_width=col_width, col_breadth=col_breadth,
        effective_depth=depth,
        nearest_edge_x=edge_x, nearest_edge_y=edge_y,
        fcu=FCU, fy=FY, fyv=FYV,
        asx_1=across(1), asx_2=across(2), asx_3=across(3), asx_4=across(4),
        asy_1=across(1) * 0.9, asy_2=across(2) * 0.9,
        asy_3=across(3) * 0.9, asy_4=across(4) * 0.9,
        load_cases=[{"v": shear, "mx": 45.0, "my": 30.0}],
    )["result"]


def verdict(result):
    """(face ok, worst Asv over all perimeters, perimeters needing steel)."""
    face = result["vu"][result["critical_load_case_index"]]
    needing = [p["perimeter"] for p in result["critical_perimeters"]
               if p["asv"] > 0]
    worst = max((p["asv"] for p in result["critical_perimeters"]), default=0.0)
    return face <= result["vcu"], worst, needing


# ── The anchor ──────────────────────────────────────────────────────────
# The pinned reference head from the C23 suite: 400 sq, de 200, V = 800,
# no flexural steel supplied.
PINNED_UO = 1600
PINNED_ASV = 2519.6003848228493
anchor = prokon.v5.punching_shear.analyse(
    design_code=CODE, col_width=400.0, col_breadth=400.0,
    effective_depth=200.0, nearest_edge_x=10_000.0, nearest_edge_y=10_000.0,
    fcu=35.0, fy=500.0, fyv=500.0,
    load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}])["result"]
print(f"\n  anchor: 400 sq, de 200, V = 800 kN, no flexural steel")
print(f"    uo  {anchor['uo']!r}   pinned {PINNED_UO!r}")
print(f"    perimeter-1 Asv {anchor['critical_perimeters'][0]['asv']!r}")
print(f"    pinned          {PINNED_ASV!r}")
print(f"    -> {'EXACT on both' if (anchor['uo'] == PINNED_UO and anchor['critical_perimeters'][0]['asv'] == PINNED_ASV) else 'DRIFTED'}")

# ── 0. The problem, and the check with no remedy ───────────────────────
# A 250 mm slab on a 300 mm column carrying a 7.5 m bay of heavy floor.
# Slim on purpose: this is the geometry that fails its FACE check, and
# the face is the check with no reinforcement remedy.
COLUMN = 300.0         # mm - a slim column, which is the point
SLAB = 250.0
DEPTH = SLAB - COVER
LOAD = 26.0            # kPa ULS - a heavily loaded floor
SHEAR = LOAD * BAY * BAY

problem = head(COLUMN, COLUMN, DEPTH, SHEAR)
face_ok, worst_asv, needing = verdict(problem)
face_stress = problem["vu"][problem["critical_load_case_index"]]

print(f"\n0. THE PROBLEM   {SLAB:.0f} mm slab, {COLUMN:.0f} mm column, "
      f"V = {SHEAR:.0f} kN")
print(f"   face vu {face_stress:.4f} MPa against vcu {problem['vcu']:.4f}"
      f"  ->  {'OK' if face_ok else 'FACE OVERSTRESSED'}")
print(f"   perimeters needing shear steel: {needing or 'none'}")
print(f"   worst Asv {worst_asv:.0f} mm2")

# Prove the "no remedy" claim rather than asserting it: the face stress
# depends on uo and V ALONE, so nothing about reinforcement moves it.
print(f"\n   PROOF that reinforcement cannot fix a face check:")
print(f"   {'flexural steel':>16} {'face vu':>10} {'vcu':>10} {'worst Asv':>11}")
for ratio in (0.5, 1.0, 2.0, 4.0, 8.0):
    probe = head(COLUMN, COLUMN, DEPTH, SHEAR, steel_ratio=ratio)
    print(f"   {f'{ratio:.1f}x':>16} "
          f"{probe['vu'][probe['critical_load_case_index']]:>10.4f} "
          f"{probe['vcu']:>10.4f} "
          f"{max(p['asv'] for p in probe['critical_perimeters']):>11.0f}")
print("   -> vu and vcu do not move at all. Eight times the flexural steel")
print("      changes the PERIMETER capacities and leaves the FACE exactly")
print("      where it was. That is what 'no remedy' means.")

# ── 1. Thicken the slab ────────────────────────────────────────────────
print(f"\n1. THICKEN THE SLAB   the whole floor gets deeper")
print(f"   {'slab':>7} {'de':>7} {'face vu':>9} {'vcu':>9} {'face':>6} "
      f"{'perims':>8} {'worst Asv':>10} {'extra m3/bay':>13}")

for slab in (250.0, 275.0, 300.0, 325.0, 350.0, 400.0):
    depth = slab - COVER
    shear = LOAD * BAY * BAY + (slab - SLAB) / 1000.0 * 25.0 * 1.4 * BAY * BAY
    result = head(COLUMN, COLUMN, depth, shear)
    ok, worst, needs = verdict(result)
    extra = (slab - SLAB) / 1000.0 * BAY * BAY
    print(f"   {slab:>7.0f} {depth:>7.0f} "
          f"{result['vu'][result['critical_load_case_index']]:>9.4f} "
          f"{result['vcu']:>9.4f} {'OK' if ok else 'FAIL':>6} "
          f"{str(needs) if needs else 'none':>8} {worst:>10.0f} "
          f"{extra:>13.2f}")
print("   -> two things to read here. The self weight in the shear")
print("      column means a thicker slab LOADS ITSELF, so the remedy is")
print("      partly self-defeating. And worst Asv is NOT monotonic: as")
print("      perimeters drop out of the set that needs steel, the worst")
print("      remaining one can be a different perimeter with a different")
print("      demand. Read the perimeter list beside the number.")

# ── 2. Enlarge the column ──────────────────────────────────────────────
print(f"\n2. ENLARGE THE COLUMN   local, and the only fix for a face check")
print(f"   {'column':>8} {'uo':>7} {'face vu':>9} {'face':>6} "
      f"{'perims':>10} {'worst Asv':>10}")

for size in (400.0, 500.0, 600.0, 700.0, 800.0, 1000.0):
    result = head(size, size, DEPTH, SHEAR)
    ok, worst, needs = verdict(result)
    print(f"   {size:>8.0f} {result['uo']:>7.0f} "
          f"{result['vu'][result['critical_load_case_index']]:>9.4f} "
          f"{'OK' if ok else 'FAIL':>6} {str(needs) if needs else 'none':>10} "
          f"{worst:>10.0f}")
print("   -> the face stress falls as 1/uo, so it responds directly. This")
print("      is the ONE remedy that fixes a face check, and it is usually")
print("      the one the architect refuses.")

# ── 3. A drop panel ────────────────────────────────────────────────────
# A drop panel is a local thickening. To C23 that is simply a larger
# effective depth at the head, with the slab beyond it unchanged - so the
# comparison is against section 1 at the same depth but WITHOUT the
# whole-floor concrete.
print(f"\n3. A DROP PANEL   the same depth as section 1, one bay in twenty")
print(f"   {'panel de':>9} {'face':>6} {'perims':>10} {'worst Asv':>10} "
      f"{'m3 per head':>12} {'vs thickening':>14}")

PANEL = 2.4            # m square drop panel
for slab in (300.0, 350.0, 400.0, 450.0, 500.0):
    depth = slab - COVER
    result = head(COLUMN, COLUMN, depth, SHEAR)
    ok, worst, needs = verdict(result)
    panel_volume = (slab - SLAB) / 1000.0 * PANEL * PANEL
    floor_volume = (slab - SLAB) / 1000.0 * BAY * BAY
    print(f"   {depth:>9.0f} {'OK' if ok else 'FAIL':>6} "
          f"{str(needs) if needs else 'none':>10} {worst:>10.0f} "
          f"{panel_volume:>12.2f} {panel_volume / floor_volume:>13.2f}x")
print(f"   -> the same structural effect for about a tenth of the concrete,")
print(f"      because a {PANEL} m panel is a small part of a {BAY} m bay.")
print(f"      What the table cannot price is the formwork, which is where")
print(f"      the drop panel's real cost lives.")

# ── 4. Shear reinforcement ─────────────────────────────────────────────
# The engine already tells you the area; what it also tells you is which
# BARS deliver it, and that is where the labour cost becomes visible.
print(f"\n4. SHEAR REINFORCEMENT   the arrangements the engine offers")
result = head(COLUMN, COLUMN, DEPTH, SHEAR)
print(f"   face check: {'OK' if verdict(result)[0] else 'STILL FAILS - links cannot help'}")
for perimeter in result["critical_perimeters"]:
    if perimeter["asv"] <= 0:
        continue
    options = [bar["description"]
               for bar in result["bars"][perimeter["perimeter"] - 1]
               if bar["description"]]
    print(f"   perimeter {perimeter['perimeter']}: "
          f"{perimeter['asv']:>8.0f} mm2 required   "
          f"{', '.join(options[:4]) if options else '(nothing offered)'}")
if result["vc_warning"]:
    print("   the code's 'v exceeds 2 vc' flag is set: the design needs")
    print("   justifying on the calcsheet. Not a failure, but not silence")
    print("   either - read vc_warning and say something about it.")

# ── 5. And where the column sits ───────────────────────────────────────
# An EDGE or CORNER column is a different problem, and the engine decides
# which you have from the edge distances - not from a flag you set.
print(f"\n5. INTERNAL, EDGE OR CORNER   the same head, edges moved in")
print(f"   {'edge x':>9} {'edge y':>9} {'uo':>7} {'ucrit 1':>9} "
      f"{'face vu':>9} {'worst Asv':>10}")

for edge_x, edge_y in ((15_000.0, 15_000.0), (1500.0, 15_000.0),
                       (600.0, 15_000.0), (600.0, 600.0), (300.0, 300.0)):
    result = head(COLUMN, COLUMN, DEPTH, SHEAR, edge_x=edge_x, edge_y=edge_y)
    print(f"   {edge_x:>9.0f} {edge_y:>9.0f} {result['uo']:>7.0f} "
          f"{result['critical_perimeters'][0]['ucrit']:>9.0f} "
          f"{result['vu'][result['critical_load_case_index']]:>9.4f} "
          f"{max(p['asv'] for p in result['critical_perimeters']):>10.0f}")
print("   -> uo and ucrit both shrink as an edge comes inside the")
print("      perimeter, so the SAME load is a harder check at an edge and")
print("      harder again at a corner. There is no 'edge column' switch:")
print("      supply the real distances and let the engine decide.")
