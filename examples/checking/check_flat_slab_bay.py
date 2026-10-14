# ---
# Example:  Independent check of a flat-slab bay, steel and column head
# Feature:  rectangular_slab + punching_shear (C04 Rectangular Slab + C23 Punching Shear)
# Verified: yes - 2026-09-10 - the slab anchor reproduces the desktop calcsheet for its own Default Example (689 / 349 / 1106 / 566) and the head anchor its pinned uo/Asv; every bay measured on prokon-automation.exe
# ---
# A flat slab has two checks that fail in completely different ways, and a
# drawing check has to do both:
#
#   the SLAB      is there enough steel in each strip, top and bottom?
#   the HEAD      does the column punch through, and is the FACE within
#                 the code's ceiling?
#
# The second one is the dangerous one. A slab short of bending steel cracks
# and sags; a column head that fails its face check fails suddenly.
#
# ⚠ AND THE FACE CHECK IS THE ONE A DRAWING CANNOT FIX. Adding shear links
# does nothing for it - measured in design-studies/punching_shear_remedies.py
# and re-checked here. So the check reports the face separately from the
# perimeters, always.

import math

import prokon.v5

CODE = "BS8110 - 1997"

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"
FCU = 35.0
FY = 500.0
FYV = 500.0
CONCRETE = 25.0

# ── The bays, as drawn ─────────────────────────────────────────────────
# (bay, span m, slab mm, column mm, ULS load kPa, top bars, bottom bars,
#  shear links provided as mm2 per perimeter, or 0 for none)
# The loads are already ULTIMATE, so the load table below carries lf = 1.0
# and the engine's own self-weight factor is left at its default.
BAYS = (
    ("A1", 7.5, 250.0, 400.0, 17.3, "Y16@150", "Y12@200", 0.0),
    ("A2", 7.5, 275.0, 500.0, 17.5, "Y16@200", "Y12@200", 0.0),
    ("B1", 8.4, 300.0, 500.0, 19.0, "Y20@150", "Y16@200", 1200.0),
    # B2 is the one to look at: a 225 mm slab landing on a 350 mm column over
    # an 8.4 m span. It is drawable, it is buildable, and its column face is
    # over the code ceiling - which no amount of reinforcement will fix.
    ("B2", 8.4, 225.0, 350.0, 19.0, "Y20@200", "Y16@250", 0.0),
    ("C1", 6.0, 200.0, 350.0, 15.0, "Y12@150", "Y10@200", 0.0),
)


def mesh_area(description):
    """mm2/m from 'Y16@150'. Spelled out so a checker can see it."""
    diameter, _, spacing = description.partition("@")
    bar = float(diameter.lstrip("YTR"))
    return (math.pi * bar ** 2 / 4.0) * 1000.0 / float(spacing)


print("INDEPENDENT CHECK OF A FLAT-SLAB BAY")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}")

# ── The engine check, on both engines ──────────────────────────────────
# The slab anchor is the desktop program's OWN Default Example, so this check
# starts by proving the engine still reproduces a published calcsheet before it
# is trusted with anything drawn.
SLAB_PINNED = (688.5778364639625, 348.6899816006131,
               1105.9653884167026, 566.2790078087527)
slab_anchor = prokon.v5.rectangular_slab.analyse(
    design_code=CODE, lx=13.81, ly=8.21, h=250.0, dx=200.0, dy=220.0,
    fcu=25.0, fy=450.0,
    edge_top=ENCASTRE, edge_right=ENCASTRE, edge_bottom=ENCASTRE,
    edge_left="FixedAgainstVerticalDisplacement",
    load_cases=[
        {"number": 1, "lf": 1.4, "udl": 2.0,
         "p": 4.0, "x": 4.19, "y": 6.45,
         "l": 4.1, "x1": 2.44, "y1": 4.05, "x2": 10.03, "y2": 6.65},
        {"lf": 1.6, "udl": 2.0,
         "p": 4.0, "x": 10.06, "y": 2.99,
         "l": 2.0, "x1": 2.59, "y1": 2.62, "x2": 9.99, "y2": 4.61},
        {"number": 2, "lf": 1.4, "udl": 1.0, "p": 12.0, "x": 3.28, "y": 6.6},
    ],
    envelope="1,2")["result"]
slab_measured = tuple(slab_anchor["ast"][face]
                      for face in ("x_top", "x_bot", "y_top", "y_bot"))

HEAD_PINNED = (1600, 2519.6003848228493)
head_anchor = prokon.v5.punching_shear.analyse(
    design_code=CODE, col_width=400.0, col_breadth=400.0,
    effective_depth=200.0, nearest_edge_x=10_000.0, nearest_edge_y=10_000.0,
    fcu=35.0, fy=500.0, fyv=500.0,
    load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}])["result"]
head_measured = (head_anchor["uo"],
                 head_anchor["critical_perimeters"][0]["asv"])

print(f"\n  engine check, both engines, against their own pinned values:")
print(f"    C04 quadruple  {'EXACT' if slab_measured == SLAB_PINNED else 'DRIFTED'}"
      f"   {slab_measured[1]!r}")
print(f"    C23 uo / Asv   {'EXACT' if head_measured == HEAD_PINNED else 'DRIFTED'}"
      f"   {head_measured[1]!r}")
if slab_measured != SLAB_PINNED or head_measured != HEAD_PINNED:
    print("    -> resolve the drift before checking anything else.")

# ── The check ───────────────────────────────────────────────────────────
print(f"\n{'bay':<5} {'slab':>6} {'span':>6} {'col':>6} "
      f"{'top req':>9} {'prov':>8} {'bot req':>9} {'prov':>8} "
      f"{'face':>6} {'links req':>10} {'prov':>8}  verdict")
print("-" * 116)

faults = []
for (bay, span, slab_h, column, load, top_bars, bottom_bars,
     links_provided) in BAYS:

    # ⚠ NO EQUIVALENT-FRAME SPLIT. This check used to do its own coefficient
    # arithmetic - m0 = wLl^2/8, then 0.63 hogging and 0.55 sagging - because
    # the engine wanted moments. It analyses the PANEL now, so the checker
    # hands over the bay and the load and lets the engine find the moments.
    # That removes the checker's own idealisation from the answer, which is
    # exactly what an INDEPENDENT check should not be carrying.
    #
    # The bay is taken as continuous on all four sides, which is what an
    # interior bay of a flat slab is.
    depth_x = slab_h - 35.0
    depth_y = slab_h - 50.0

    slab = prokon.v5.rectangular_slab.analyse(
        design_code=CODE, lx=span, ly=span, h=slab_h,
        dx=depth_x, dy=depth_y,
        fcu=FCU, fy=FY,
        edge_top=ENCASTRE, edge_right=ENCASTRE,
        edge_bottom=ENCASTRE, edge_left=ENCASTRE,
        load_cases=[{"number": 1, "lf": 1.0, "udl": load}])["result"]

    required_top = slab["ast"]["x_top"]
    required_bottom = slab["ast"]["x_bot"]
    provided_top = mesh_area(top_bars)
    provided_bottom = mesh_area(bottom_bars)

    shear = load * span * span

    def across(perimeter):
        reach = column + 2 * 1.5 * perimeter * depth_x
        return provided_top * min(reach, span * 1000.0) / 1000.0

    head = prokon.v5.punching_shear.analyse(
        design_code=CODE,
        col_width=column, col_breadth=column,
        effective_depth=depth_x,
        nearest_edge_x=span * 1000.0, nearest_edge_y=span * 1000.0,
        fcu=FCU, fy=FY, fyv=FYV,
        asx_1=across(1), asx_2=across(2), asx_3=across(3), asx_4=across(4),
        asy_1=across(1) * 0.9, asy_2=across(2) * 0.9,
        asy_3=across(3) * 0.9, asy_4=across(4) * 0.9,
        load_cases=[{"v": shear, "mx": 45.0, "my": 30.0}])["result"]

    face_stress = head["vu"][head["critical_load_case_index"]]
    face_ok = face_stress <= head["vcu"]
    links_required = max((p["asv"] for p in head["critical_perimeters"]),
                         default=0.0)

    reasons = []

    # A face carrying a moment that came back with NO steel is the engine
    # declining to design it, not a face that needs none. Reading it as zero
    # would report a too-thin slab as comfortably adequate.
    declined = [face for face in ("x_top", "x_bot", "y_top", "y_bot")
                if slab["ast"][face] == 0.0 and slab["moment_max"][face] > 0.0]
    if declined:
        reasons.append("the engine could not design " + ", ".join(declined)
                       + " - the slab is too thin")
    if provided_top < required_top:
        reasons.append(f"top steel short by "
                       f"{required_top - provided_top:.0f} mm2/m")
    if provided_bottom < required_bottom:
        reasons.append(f"bottom steel short by "
                       f"{required_bottom - provided_bottom:.0f} mm2/m")
    if not face_ok:
        reasons.append(f"COLUMN FACE overstressed: vu {face_stress:.3f} > "
                       f"vcu {head['vcu']:.3f} - no reinforcement fixes this")
    if links_required > links_provided:
        reasons.append(f"shear reinforcement short by "
                       f"{links_required - links_provided:.0f} mm2")

    print(f"{bay:<5} {slab_h:>6.0f} {span:>6.1f} {column:>6.0f} "
          f"{required_top:>9.0f} {provided_top:>8.0f} "
          f"{required_bottom:>9.0f} {provided_bottom:>8.0f} "
          f"{'OK' if face_ok else 'FAIL':>6} "
          f"{links_required:>10.0f} {links_provided:>8.0f}  "
          f"{'PASS' if not reasons else 'FAIL'}")
    for reason in reasons:
        print(f"{'':<5} -> {reason}")
    if reasons:
        faults.append((bay, face_ok, reasons))

# ── The summary a checker actually issues ──────────────────────────────
print(f"\n{'-' * 116}")
if not faults:
    print("Every bay passes as drawn.")
else:
    face_failures = [bay for bay, face_ok, _ in faults if not face_ok]
    other = [bay for bay, face_ok, _ in faults if face_ok]
    print(f"{len(faults)} bay(s) fail.")
    if face_failures:
        print(f"\n  CATEGORY 1 - the column FACE fails in: "
              f"{', '.join(face_failures)}")
        print(f"  These cannot be resolved by reinforcement. The slab or the")
        print(f"  column has to grow, and that is a design change rather")
        print(f"  than a detailing one. Raise it first and separately.")
    if other:
        print(f"\n  CATEGORY 2 - steel or links short in: {', '.join(other)}")
        print(f"  These are resolvable within the drawn geometry.")

print(f"\n{'-' * 116}")
print("The two categories are the point. A checker who reports 'five bays")
print("fail' has said much less than one who reports which failures can be")
print("drawn out and which cannot.")
