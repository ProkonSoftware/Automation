# ---
# Example:  A shear-link layout for the column heads, perimeter by perimeter
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes - 2026-09-02 - the reference head reproduces its pinned uo and perimeter-1 Asv; every head measured on prokon-automation.exe
# ---
# C23 reports, for each of five critical perimeters, the shear steel area
# required and the bar arrangements that provide it. What a drawing needs
# is different: the RADIAL POSITION of each perimeter, how many legs go on
# it, and where the last perimeter needing steel sits - because that is
# where the reinforced zone ends.
#
# This recipe turns the result into that layout, and it writes the schedule
# a fixer can work from.
#
# ⚠ THE FACE CHECK COMES FIRST, AND IT IS NOT A LINK PROBLEM. If vu
# exceeds vcu, no arrangement on any perimeter helps - the stress at the
# column face is capped by the code. So the layout is only computed for
# heads that pass the face check, and the others are reported as a
# geometry change.

import csv
import math
from pathlib import Path

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 35.0
FY = 500.0
FYV = 500.0
COVER = 35.0

# ── The heads ──────────────────────────────────────────────────────────
# (mark, column mm, slab mm, ULS shear kN, Mx kNm, My kNm, top steel mm2/m,
#  edge x mm, edge y mm)
HEADS = (
    ("H1", 400.0, 250.0,  950.0, 45.0, 30.0, 1100.0, 15000.0, 15000.0),
    ("H2", 400.0, 300.0, 1250.0, 55.0, 35.0, 1400.0, 15000.0, 15000.0),
    ("H3", 300.0, 250.0, 1400.0, 60.0, 40.0, 1400.0, 15000.0, 15000.0),
    ("H4", 500.0, 300.0, 1100.0, 50.0, 30.0, 1200.0,   800.0, 15000.0),
    ("H5", 500.0, 350.0, 1600.0, 70.0, 45.0, 1600.0,   700.0,   700.0),
)

print("SHEAR-LINK LAYOUT AT THE COLUMN HEADS")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, fyv {FYV:.0f}, "
      f"cover {COVER:.0f} mm")

# ── The anchor ──────────────────────────────────────────────────────────
anchor = prokon.v5.punching_shear.analyse(
    design_code=CODE, col_width=400.0, col_breadth=400.0,
    effective_depth=200.0, nearest_edge_x=10_000.0, nearest_edge_y=10_000.0,
    fcu=35.0, fy=500.0, fyv=500.0,
    load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}])["result"]
PINNED = (1600, 2519.6003848228493)
measured = (anchor["uo"], anchor["critical_perimeters"][0]["asv"])
print(f"\n  anchor: 400 sq, de 200, V = 800 kN")
print(f"    uo  {measured[0]!r}   pinned {PINNED[0]!r}")
print(f"    Asv {measured[1]!r}")
print(f"    pinned {PINNED[1]!r}")
print(f"    -> {'EXACT on both' if measured == PINNED else 'DRIFTED'}")

layout = []
face_failures = []

for (mark, column, slab, shear, mx, my, top_steel,
     edge_x, edge_y) in HEADS:
    depth = slab - COVER

    def across(perimeter):
        """The top steel crossing one perimeter, from the mesh provided."""
        reach = column + 2 * 1.5 * perimeter * depth
        return top_steel * reach / 1000.0

    result = prokon.v5.punching_shear.analyse(
        design_code=CODE,
        col_width=column, col_breadth=column,
        effective_depth=depth,
        nearest_edge_x=edge_x, nearest_edge_y=edge_y,
        fcu=FCU, fy=FY, fyv=FYV,
        asx_1=across(1), asx_2=across(2), asx_3=across(3), asx_4=across(4),
        asy_1=across(1) * 0.9, asy_2=across(2) * 0.9,
        asy_3=across(3) * 0.9, asy_4=across(4) * 0.9,
        load_cases=[{"v": shear, "mx": mx, "my": my}])["result"]

    face_stress = result["vu"][result["critical_load_case_index"]]
    internal = abs(edge_x) > 5000.0 and abs(edge_y) > 5000.0
    position = ("internal" if internal
                else "corner" if abs(edge_x) <= 5000.0 and abs(edge_y) <= 5000.0
                else "edge")

    print(f"\n{mark}   {column:.0f} mm column, {slab:.0f} mm slab "
          f"(de {depth:.0f}), V = {shear:.0f} kN, {position}")
    print(f"   uo {result['uo']:.0f} mm, face vu {face_stress:.4f} MPa "
          f"against vcu {result['vcu']:.4f}")

    if face_stress > result["vcu"]:
        over = 100.0 * (face_stress / result["vcu"] - 1.0)
        print(f"   -> FACE OVERSTRESSED by {over:.0f} %. No link arrangement")
        print(f"      helps: vcu is a ceiling, not a capacity. The column or")
        print(f"      the slab has to grow. NO LAYOUT COMPUTED.")
        face_failures.append(mark)
        layout.append({
            "head": mark, "perimeter": "", "radial_mm": "",
            "ucrit_mm": "", "asv_required_mm2": "", "arrangement": "",
            "asv_provided_mm2": "", "note": "FACE OVERSTRESSED - "
                                            "no link remedy",
        })
        continue

    if result["vc_warning"]:
        print(f"   note: the code's 'v exceeds 2 vc' flag is set - the")
        print(f"   design needs justifying on the calcsheet.")

    print(f"   {'perim':>6} {'radial':>8} {'ucrit':>8} {'Veff':>9} "
          f"{'Vcap':>9} {'Asv req':>9}  arrangement")

    last_reinforced = 0
    for perimeter in result["critical_perimeters"]:
        number = perimeter["perimeter"]
        required = perimeter["asv"]

        if required <= 0:
            print(f"   {number:>6} {perimeter['radial_distance']:>8.0f} "
                  f"{perimeter['ucrit']:>8.0f} {perimeter['veff']:>9.1f} "
                  f"{perimeter['vcap']:>9.1f} {'-':>9}  "
                  f"(concrete alone carries it)")
            continue

        last_reinforced = number
        # bars is indexed by PERIMETER POSITION, so perimeter n is
        # bars[n - 1]. Its entries are the arrangements the engine offers,
        # each already providing at least the required area.
        options = [bar for bar in result["bars"][number - 1]
                   if bar["description"]]
        chosen = options[0] if options else None

        print(f"   {number:>6} {perimeter['radial_distance']:>8.0f} "
              f"{perimeter['ucrit']:>8.0f} {perimeter['veff']:>9.1f} "
              f"{perimeter['vcap']:>9.1f} {required:>9.0f}  "
              f"{chosen['description'] if chosen else 'NOTHING OFFERED'}"
              + (f" ({chosen['area']:.0f} mm2)" if chosen else ""))

        layout.append({
            "head": mark, "perimeter": number,
            "radial_mm": round(perimeter["radial_distance"]),
            "ucrit_mm": round(perimeter["ucrit"]),
            "asv_required_mm2": round(required),
            "arrangement": chosen["description"] if chosen else "SPECIAL",
            "asv_provided_mm2": (round(chosen["area"]) if chosen else ""),
            "note": "" if chosen else "no standard arrangement offered",
        })

    if last_reinforced:
        outermost = next(p for p in result["critical_perimeters"]
                         if p["perimeter"] == last_reinforced)
        # The reinforced zone extends to the last perimeter that needs
        # steel, plus the code's own detailing allowance. The 1.5d is a
        # detailing rule, stated rather than hidden.
        zone = outermost["radial_distance"] + 1.5 * depth
        print(f"   -> links needed on perimeters 1 to {last_reinforced}.")
        print(f"      The reinforced zone runs to "
              f"{outermost['radial_distance']:.0f} mm from the column face,")
        print(f"      plus 1.5d = {1.5 * depth:.0f} mm of detailing, so a "
              f"{2 * zone + column:.0f} mm")
        print(f"      square zone centred on the column.")
    else:
        print(f"   -> no shear reinforcement needed anywhere. The concrete")
        print(f"      carries every perimeter.")

# ── Write it ────────────────────────────────────────────────────────────
FIELDS = ("head", "perimeter", "radial_mm", "ucrit_mm",
          "asv_required_mm2", "arrangement", "asv_provided_mm2", "note")
output = Path("punching_link_layout.csv")
with open(output, "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(layout)

with open(output, newline="", encoding="utf-8") as handle:
    read_back = list(csv.DictReader(handle))

print(f"\n{'-' * 76}")
print(f"Written: {output.resolve()}")
print(f"  {len(read_back)} row(s) written and re-read, "
      f"{'headers match' if list(read_back[0]) == list(FIELDS) else 'HEADERS DIFFER'}")

if face_failures:
    print(f"\nHEADS WITH NO LINK REMEDY: {', '.join(face_failures)}")
    print("Those go on a different list from the rest, because they are a")
    print("design change and not a detailing one. Mixing them into a link")
    print("schedule is how a slab gets built with links it cannot use.")
else:
    print("\nEvery head passes its face check, so every head has a layout.")

print()
print("The radial distance is the number that makes this a layout rather")
print("than a table of areas: it says WHERE each perimeter is, and the last")
print("reinforced one says where the zone stops.")
