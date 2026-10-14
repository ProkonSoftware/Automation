# ---
# Example:  Independent check of a foundation schedule - pads and pile caps
# Feature:  pad_footing + pile_cap (C15 Pad Footing + C16 Pile Cap)
# Verified: yes - 2026-09-02 - both references reproduce their pinned values; every schedule row measured on prokon-automation.exe
# ---
# Foundations are where a check earns its fee, because two of the checks
# are silent:
#
#   * an INADEQUATE PAD reports a successful analysis. Nothing is derived
#     from allowable_bearing_pressure - the comparison is yours.
#   * a PUNCHING CHECK THAT NEVER RAN reports vp = vcp = 0, and "vp <= vcp"
#     reads 0 <= 0, which looks like a pass.
#
# ⚠ AND THE TWO ENGINES USE DIFFERENT UNITS. C15 takes metres for the pad
# and millimetres for the bars; C16 takes METRES throughout, including the
# column and the rebar depth. The schedule below is written in the units a
# drawing uses and converted at each call, in the open.

import prokon.v5

FCU = 30.0
FY = 450.0
ALLOWABLE = 200.0        # kPa, from the geotechnical report

# ── The schedule, as drawn ─────────────────────────────────────────────
# Pads: (mark, plan m, depth m, column m, SLS load kN, moment kNm)
PADS = (
    ("F1", 2.50, 0.60, 0.40,  600.0, 20.0),
    ("F2", 2.00, 0.50, 0.40,  700.0, 30.0),
    ("F3", 3.50, 0.80, 0.50, 1600.0, 60.0),
    ("F4", 1.50, 0.60, 0.40,  600.0,  0.0),
    ("F5", 4.00, 0.90, 0.60, 2400.0, 90.0),
)

# Caps: (mark, piles, pile dia m, spacing m, thickness m, column m,
#        ULS load kN, moment kNm, tie steel provided mm2)
CAPS = (
    ("PC1", 4, 0.60, 1.80, 1.20, 0.50, 4000.0,    0.0, 2600.0),
    ("PC2", 4, 0.60, 1.80, 1.00, 0.50, 4000.0,  500.0, 2600.0),
    ("PC3", 3, 0.60, 1.80, 1.20, 0.50, 3000.0,    0.0, 2000.0),
    ("PC4", 5, 0.75, 2.40, 1.60, 0.80, 8000.0, 1000.0, 6000.0),
    ("PC5", 2, 0.60, 1.80, 1.20, 0.40, 2000.0,  200.0, 1800.0),
)

print("INDEPENDENT CHECK OF A FOUNDATION SCHEDULE")
print(f"  fcu {FCU:.0f}, fy {FY:.0f}, allowable bearing {ALLOWABLE:.0f} kPa")

# ── Both engines, against their own pins ───────────────────────────────
pad_anchor = prokon.v5.pad_footing.analyse(
    design_code="BS8110 - 1997", a=2.5, b=2.5, yf=0.6, z=0.5,
    c1=0.4, d1=0.4, e1=0.0, f1=0.0, fcu=30.0, fy=450.0,
    allowable_bearing_pressure=200.0,
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
    bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
    bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
    load_cases=[{"name": "LC1", "pa1": 600.0, "hx1": 30.0,
                 "mx1": 20.0, "lf1": 1.4}])["result"]
cap_anchor = prokon.v5.pile_cap.analyse(
    design_code="CSA-A23.3:2019", column_dim_x=0.5, column_dim_y=0.5,
    no_of_piles=4, pile_dia=0.6, pile_spacing=1.8, pile_tolerance=0.05,
    cap_thickness=1.2, cap_overhang=0.3, bottom_rebar_depth=0.1,
    fc=30.0, fy=400.0,
    load_cases=[{"name": "ULS", "load_factor": 1.0, "p": 4000.0}])["result"]

PAD_PINNED = 133.98908218356328
CAP_PINNED = 2064.6284818393965
print(f"\n  engine check:")
print(f"    C15 sls.pm  {pad_anchor['max_bearing_pressure_sls']!r}   "
      f"{'EXACT' if pad_anchor['max_bearing_pressure_sls'] == PAD_PINNED else 'DRIFTED'}")
print(f"    C16 strut Cr {cap_anchor['strut_results'][0]['load_cases'][0]['cr']!r}   "
      f"{'EXACT' if cap_anchor['strut_results'][0]['load_cases'][0]['cr'] == CAP_PINNED else 'DRIFTED'}")

# ── The pads ────────────────────────────────────────────────────────────
print(f"\nPADS  (C15)")
print(f"{'mark':<6} {'plan':>10} {'p sls':>9} {'/allow':>8} {'ovt SF':>8} "
      f"{'vx/vcx':>8} {'vp/vcp':>10}  verdict")
print("-" * 80)

pad_faults = []
for mark, plan, depth, column, load, moment in PADS:
    result = prokon.v5.pad_footing.analyse(
        design_code="BS8110 - 1997",
        a=plan, b=plan, yf=depth, z=0.4,
        c1=column, d1=column, e1=0.0, f1=0.0,
        fcu=FCU, fy=FY,
        allowable_bearing_pressure=ALLOWABLE,
        bar_dia_x_bot=16.0, bar_spacing_x_bot=150.0,
        bar_dia_y_bot=16.0, bar_spacing_y_bot=150.0,
        load_cases=[{"name": mark, "pa1": load, "mx1": moment, "lf1": 1.45}])["result"]

    critical = result["critical_uls"]
    shear = critical["shear"]
    pressure = result["max_bearing_pressure_sls"]
    bearing_ratio = pressure / ALLOWABLE
    one_way = shear["vx"] / shear["vcx"] if shear["vcx"] else None

    reasons = []
    if bearing_ratio > 1.0:
        reasons.append(f"bearing {pressure:.1f} kPa is "
                       f"{100 * bearing_ratio:.0f} % of the allowable")
    if one_way is not None and one_way > 1.0:
        reasons.append(f"one-way shear {one_way:.2f} of capacity")
    # ⚠ vcp > 0 FIRST. A pad too small for its own punching perimeter
    # publishes vp = vcp = 0, and "vp <= vcp" would call that a pass.
    if shear["vcp"] <= 0:
        punching = "NOT CHECKED"
        reasons.append("the punching perimeter does not fit in the pad - the "
                       "check never ran, and 0 <= 0 is not a pass")
    else:
        punching = f"{shear['vp'] / shear['vcp']:.2f}"
        if shear["vp"] > shear["vcp"]:
            reasons.append(f"punching {punching} of capacity")
    # ⚠ 999999.99 IS A SENTINEL, NOT A SAFETY FACTOR. Measured
    # 2026-09-02: with the destabilising action exactly zero, C15
    # publishes 999999.99 for sf_ovt and for sf_sliding. Put a
    # moment of 0.001 kNm on the same pad and it becomes 486450 - a
    # real, enormous number - so the sentinel marks the
    # divide-by-zero case specifically. A check that prints it as a
    # factor of a million reads as nonsense; report it as "no
    # overturning action" instead, which is what it means.
    SENTINEL = 999999.99
    overturning = critical["sls"]["sf_ovt"]
    if overturning == SENTINEL:
        overturning_text = "n/a"
    else:
        overturning_text = f"{overturning:.2f}"
        if overturning < 2.0:
            reasons.append(f"overturning SF {overturning:.2f} below 2.0")

    print(f"{mark:<6} {f'{plan:.2f}x{depth:.2f}':>10} {pressure:>9.1f} "
          f"{bearing_ratio:>8.2f} {overturning_text:>8} "
          f"{'n/a' if one_way is None else format(one_way, '.2f'):>8} "
          f"{punching:>10}  {'PASS' if not reasons else 'FAIL'}")
    for reason in reasons:
        print(f"{'':<6} -> {reason}")
    if reasons:
        pad_faults.append(mark)

# ── The caps ────────────────────────────────────────────────────────────
print(f"\nPILE CAPS  (C16)")
print(f"{'mark':<6} {'piles':>6} {'cap plan':>14} {'worst SF':>9} "
      f"{'where':<14} {'tie req':>9} {'prov':>8}  verdict")
print("-" * 92)

cap_faults = []
for (mark, piles, pile_dia, spacing, thickness, column,
     load, moment, tie_provided) in CAPS:
    try:
        result = prokon.v5.pile_cap.analyse(
            design_code="CSA-A23.3:2019",
            column_dim_x=column, column_dim_y=column,
            no_of_piles=piles, pile_dia=pile_dia,
            pile_spacing=spacing, pile_tolerance=0.05,
            cap_thickness=thickness, cap_overhang=0.3,
            bottom_rebar_depth=0.1,
            fc=FCU, fy=FY,
            load_cases=[{"name": mark, "load_factor": 1.0,
                         "p": load, "mx": moment}])["result"]
    except prokon.v5.ProkonError as refusal:
        # ⚠ THIS IS A CHECK RESULT, NOT A SCRIPT ERROR. Uplift and an
        # invalid geometry both arrive as refusals, and both are things a
        # checker must report rather than skip.
        message = refusal.message.encode("ascii", "replace").decode()
        print(f"{mark:<6} {piles:>6} {'-':>14} {'-':>9} {'-':<14} "
              f"{'-':>9} {tie_provided:>8.0f}  REFUSED")
        print(f"{'':<6} -> {refusal.category}/{refusal.code}: {message}")
        cap_faults.append(mark)
        continue

    factors = [(s["load_cases"][0]["sf"], f"strut {s['element_index']}")
               for s in result["strut_results"]]
    factors.append((result["column_node"]["load_cases"][0]["sf"],
                    "column node"))
    factors += [(n["load_cases"][0]["sf"], f"pile node {n['index']}")
                for n in result["pile_nodes"]]
    worst, where = min(factors)

    by_element = {tie["element_index"]: tie for tie in result["tie_results"]}
    tie = by_element[result["design_tie"]]["load_cases"][0]
    tie_required = tie["as_required"]

    reasons = []
    if worst < 1.0:
        reasons.append(f"safety factor {worst:.3f} at the {where}")
    if tie_provided < tie_required:
        reasons.append(f"tie steel short by "
                       f"{tie_required - tie_provided:.0f} mm2")
    if tie_provided < result["tie_minim_reinforcement"]:
        reasons.append(f"below the code minimum "
                       f"{result['tie_minim_reinforcement']:.0f} mm2/m")
    if not result["geometry_is_valid"]:
        reasons.append("the engine reports the geometry as invalid")

    print(f"{mark:<6} {piles:>6} "
          f"{result['cap_dim_x']:>6.2f} x {result['cap_dim_y']:<5.2f} "
          f"{worst:>9.3f} {where:<14} {tie_required:>9.0f} "
          f"{tie_provided:>8.0f}  {'PASS' if not reasons else 'FAIL'}")
    for reason in reasons:
        print(f"{'':<6} -> {reason}")
    if reasons:
        cap_faults.append(mark)

# ── The report ──────────────────────────────────────────────────────────
print(f"\n{'-' * 92}")
print(f"pads:  {len(PADS) - len(pad_faults)} of {len(PADS)} pass"
      + (f"; attention on {', '.join(pad_faults)}" if pad_faults else ""))
print(f"caps:  {len(CAPS) - len(cap_faults)} of {len(CAPS)} pass"
      + (f"; attention on {', '.join(cap_faults)}" if cap_faults else ""))
print()
print("The two silent checks are the ones worth spelling out in a report:")
print("  * every FAIL above came back from the engine as ok=true, with the")
print("    single exception of the refusals - so 'the analysis ran' is not")
print("    a finding and never was;")
print("  * a pad whose punching perimeter does not FIT publishes vp = vcp")
print("    = 0. Any check that reads 'vp <= vcp' without testing vcp > 0")
print("    first signs off a pad nobody checked.")
print()
print("And one number in the table is not a number: 999999.99 is the")
print("sentinel C15 publishes when the destabilising action is exactly")
print("zero, so it is reported as n/a above rather than as a factor of a")
print("million. Add 0.001 kNm of moment and it becomes 486450 instead -")
print("which is how you can tell the two cases apart.")
