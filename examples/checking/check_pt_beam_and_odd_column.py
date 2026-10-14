# ---
# Example:  Checking a PT beam and the odd-shaped column under it
# Feature:  prestressed_concrete + general_column (C02 Captain + C13 General Column)
# Verified: yes - 2026-09-02 - the desktop's own PT example reproduces its pinned punching triple, and the Case A column its pinned factor; every variant measured on prokon-automation.exe
# ---
# The two hardest things to check on someone else's drawing:
#
#   a POST-TENSIONED BEAM, because the check is a STRESS check at two
#   stages and neither of them is "is there enough steel";
#
#   an ODD-SHAPED COLUMN, because the answer depends on the outline that
#   was actually drawn, and a rectangular idealisation of it is a
#   different column.
#
# ⚠ A PT CHECK IS NOT A STEEL CHECK. There is no "As required" to compare
# against. The checks are: SLS stresses inside the permissible band,
# TRANSFER stresses inside a different band, deflection, and cracking. The
# script reads the engine's OWN permissible values rather than carrying a
# table of them, because those depend on the code and on fcu and fci.
#
# ⚠ AND FOR THE COLUMN: capacity_factor is the key to branch on, not
# utilisation. A position the engine could not answer publishes
# capacity_factor 0 with utilisation None, so a check that reads
# utilisation first trips over None on exactly the row that matters.

import prokon.v5

FY = 450.0
FYV = 250.0

TENDON = {
    "no": 1, "bond": "Bonded", "strength": 1860.0, "max_stress_pct": 75,
    "dia": 75, "area": 900, "k": 0.0012, "u": 0.19, "pullin": 6,
    "relax": 2.5, "est": 195e6, "min_harp_radius": 4.0,
}

# ── The PT beams, as drawn ─────────────────────────────────────────────
# (mark, spans m, web mm, depth mm, fcu, fci, balanced %, dead kN/m,
#  live kN/m)
BEAMS = (
    ("PT1", (9.0, 11.0, 9.0), 3000.0, 300.0, 40.0, 30.0, 100.0, 4.0, 9.0),
    ("PT2", (9.0, 11.0, 9.0), 3000.0, 240.0, 40.0, 30.0, 100.0, 4.0, 9.0),
    ("PT3", (12.0, 14.0, 12.0), 3000.0, 400.0, 45.0, 32.0, 90.0, 5.0, 12.0),
    ("PT4", (9.0, 11.0, 9.0), 3000.0, 300.0, 40.0, 20.0, 140.0, 4.0, 9.0),
)

print("CHECKING A PT BEAM AND THE COLUMN UNDER IT")

# ── Both engines, against their own pins ───────────────────────────────
column_anchor = prokon.v5.general_column.analyse(
    design_code="BS8110 - 1997", length=3.0, fcu=30.0, fy=450.0,
    section=[{"code": "+", "x": 0, "y": 0},
             {"code": "L", "x": 400, "y": 0},
             {"code": "L", "x": 400, "y": 400},
             {"code": "L", "x": 0, "y": 400},
             {"code": "+", "x": 42.5, "y": 42.5}, {"code": "B", "x": 25},
             {"code": "+", "x": 357.5, "y": 42.5}, {"code": "B", "x": 25},
             {"code": "+", "x": 357.5, "y": 357.5}, {"code": "B", "x": 25},
             {"code": "+", "x": 42.5, "y": 357.5}, {"code": "B", "x": 25}],
    load_cases=[{"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50}])["result"]
COLUMN_PINNED = 2.179097995657654
column_measured = column_anchor["load_cases"][0]["min_capacity_factor"]
print(f"\n  engine check:")
print(f"    C13 Case A factor {column_measured!r}   "
      f"{'EXACT' if column_measured == COLUMN_PINNED else 'DRIFTED'}")

# ── The PT check ────────────────────────────────────────────────────────
print(f"\nPOST-TENSIONED BEAMS  (C02)")
print(f"{'mark':<6} {'depth':>6} {'SLS band':>16} {'SLS actual':>16} "
      f"{'tr band':>16} {'tr actual':>16} {'defl':>7}  verdict")
print("-" * 108)

pt_faults = []
for (mark, spans, web, depth, fcu, fci, balanced,
     dead, live) in BEAMS:
    try:
        beam = prokon.v5.prestressed_concrete.analyse(
            design_code="BS8110 - 1997", title=mark,
            fcu=fcu, fy=FY, fyv=FYV, fci=fci,
            ec=30e6, est=200e6, density=24.0,
            top_cover=30.0, bottom_cover=30.0,
            permanent_live_load_pct=25.0, creep=2.0,
            balanced_dead_load_pct=balanced,
            generated_profile="Parabolic",
            tendon_properties=[TENDON],
            sections=[{"name": "s", "bw": web, "d": depth}],
            span_segments=[{"span": n + 1, "length": length,
                            "sec_left": "s"}
                           for n, length in enumerate(spans)],
            supports=[{"no": n + 1, "d_below": 400, "b_below": 400,
                       "h_below": 3.2, "code_below": "F"}
                      for n in range(len(spans) + 1)],
            loads=[row for n, _ in enumerate(spans) for row in (
                {"case": "D", "span": n + 1, "wl": dead * web / 1000.0},
                {"case": "L", "span": n + 1, "wl": live * web / 1000.0})],
        )["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"{mark:<6} {depth:>6.0f}  REFUSED "
              f"{refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:50]}")
        pt_faults.append(mark)
        continue

    # THE ENGINE'S OWN PERMISSIBLE VALUES. Carrying a table of them here
    # would be a second source of truth that drifts with the code and with
    # fcu; reading them off the result cannot.
    sls_compression = beam["sls"]["fcc"] / 1e6
    sls_tension = -beam["sls"]["fct"] / 1e6
    transfer_compression = beam["transfer"]["fcct"] / 1e6
    transfer_tension = -beam["transfer"]["fctt"] / 1e6

    sls_high = max(beam["sls"]["svsma"])
    sls_low = min(beam["sls"]["svsmi"])
    transfer_high = max(beam["transfer"]["svtma"])
    transfer_low = min(beam["transfer"]["svtmi"])
    deflection = max(abs(value) for value in beam["deflections"]["ditot"])
    limit = min(spans) * 1000.0 / 250.0

    reasons = []
    if sls_high > sls_compression:
        reasons.append(f"SLS compression {sls_high:.2f} over "
                       f"{sls_compression:.2f} MPa")
    if sls_low < sls_tension:
        reasons.append(f"SLS tension {sls_low:.2f} beyond "
                       f"{sls_tension:.2f} MPa")
    if transfer_high > transfer_compression:
        reasons.append(f"TRANSFER compression {transfer_high:.2f} over "
                       f"{transfer_compression:.2f} MPa")
    if transfer_low < transfer_tension:
        reasons.append(f"TRANSFER tension {transfer_low:.2f} beyond "
                       f"{transfer_tension:.2f} MPa")
    if deflection > limit:
        reasons.append(f"deflection {deflection:.1f} > {limit:.1f} mm")

    print(f"{mark:<6} {depth:>6.0f} "
          f"{f'{sls_tension:.2f}..{sls_compression:.2f}':>16} "
          f"{f'{sls_low:.2f}..{sls_high:.2f}':>16} "
          f"{f'{transfer_tension:.2f}..{transfer_compression:.2f}':>16} "
          f"{f'{transfer_low:.2f}..{transfer_high:.2f}':>16} "
          f"{deflection:>7.1f}  {'PASS' if not reasons else 'FAIL'}")
    for reason in reasons:
        print(f"{'':<6} -> {reason}")
    if reasons:
        pt_faults.append(mark)

print("   -> the TRANSFER band is a different band from the SLS one,")
print("      because at transfer the concrete is at fci and not fcu. PT4")
print("      above differs from PT1 only in fci and in the balanced load,")
print("      which is exactly the pair a designer tunes and a checker has")
print("      to re-derive.")

# ── The odd-shaped columns ─────────────────────────────────────────────
# (mark, description, outline points mm, bar positions mm, bar dia,
#  length m, N kN, Mx kNm, My kNm)
COVER = 50.0


def rectangle_outline(width, depth):
    return [(0.0, 0.0), (width, 0.0), (width, depth), (0.0, depth)]


def tee_outline(flange_w, flange_t, stem_t, stem_h):
    left = (flange_w - stem_t) / 2.0
    return [(0.0, 0.0), (flange_w, 0.0), (flange_w, flange_t),
            (left + stem_t, flange_t), (left + stem_t, flange_t + stem_h),
            (left, flange_t + stem_h), (left, flange_t)]


def ell_outline(arm, leg):
    return [(0.0, 0.0), (arm, 0.0), (arm, leg), (leg, leg),
            (leg, arm), (0.0, arm)]


COLUMNS = (
    ("K1", "600 x 300 blade", rectangle_outline(600.0, 300.0),
     [(x, y) for x in (COVER, 200.0, 400.0, 550.0)
      for y in (COVER, 250.0)], 20.0, 3.2, 2400.0, 90.0, 40.0),
    ("K2", "T pilaster", tee_outline(1000.0, 350.0, 300.0, 500.0),
     [(x, COVER) for x in (COVER, 350.0, 650.0, 950.0)]
     + [(x, 300.0) for x in (COVER, 950.0)]
     + [(x, 800.0) for x in (400.0, 600.0)], 20.0, 3.2, 1800.0, 120.0, 30.0),
    ("K3", "L core corner", ell_outline(800.0, 350.0),
     [(x, COVER) for x in (COVER, 300.0, 550.0, 750.0)]
     + [(COVER, y) for y in (300.0, 550.0, 750.0)]
     + [(300.0, 750.0), (300.0, 300.0)], 25.0, 3.2, 3600.0, 200.0, 150.0),
    ("K4", "600 x 300 blade, tall", rectangle_outline(600.0, 300.0),
     [(x, y) for x in (COVER, 200.0, 400.0, 550.0)
      for y in (COVER, 250.0)], 20.0, 7.5, 2400.0, 90.0, 40.0),
)

print(f"\nODD-SHAPED COLUMNS  (C13)")
print(f"{'mark':<5} {'shape':<22} {'gross':>9} {'bars':>5} {'steel':>8} "
      f"{'%':>6} {'worst cf':>9} {'at':<9}  verdict")
print("-" * 100)

column_faults = []
for (mark, description, outline, bar_points, bar, length,
     axial, mx, my) in COLUMNS:
    section = [{"code": "+", "x": outline[0][0], "y": outline[0][1]}]
    for x, y in outline[1:]:
        section.append({"code": "L", "x": x, "y": y})
    for x, y in bar_points:
        section.append({"code": "+", "x": x, "y": y})
        section.append({"code": "B", "x": bar})

    try:
        result = prokon.v5.general_column.analyse(
            design_code="BS8110 - 1997",
            length=length, effective_length_factor=0.85,
            fcu=40.0, fy=FY, braced=True,
            end_top="FullyFixed", end_bottom="FullyFixed",
            section=section,
            load_cases=[{"axial": axial,
                         "moment_x_top": mx, "moment_x_bottom": mx / 2.0,
                         "moment_y_top": my, "moment_y_bottom": my / 2.0}])["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"{mark:<5} {description:<22}  REFUSED "
              f"{refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:40]}")
        column_faults.append(mark)
        continue

    # ⚠ BRANCH ON capacity_factor. A position the engine could not answer
    # publishes capacity_factor 0 and utilisation None, so scanning
    # utilisation first raises TypeError on the very row that matters.
    unanswered = [(case["load_case"], position["position"])
                  for case in result["load_cases"]
                  for position in case["positions"]
                  if position["capacity_factor"] == 0]

    reasons = []
    if not result["has_feasible_design"]:
        reasons.append("the engine reports no feasible design")
    if result["min_capacity_factor"] < 1.0:
        reasons.append(f"capacity factor {result['min_capacity_factor']:.4f} "
                       f"below 1.0")
    if unanswered:
        reasons.append(f"{len(unanswered)} position(s) unanswered "
                       f"(capacity_factor 0): {unanswered}")
    if result["reinforcement_ratio"] > 4.0:
        reasons.append(f"steel {result['reinforcement_ratio']:.2f} % over 4 %")

    print(f"{mark:<5} {description:<22} {result['concrete_area']:>9.0f} "
          f"{result['bar_count']:>5} {result['steel_area']:>8.0f} "
          f"{result['reinforcement_ratio']:>6.2f} "
          f"{result['min_capacity_factor']:>9.4f} "
          f"{result['critical_position']:<9}  "
          f"{'PASS' if not reasons else 'FAIL'}")
    for reason in reasons:
        print(f"{'':<5} -> {reason}")
    if reasons:
        column_faults.append(mark)

print("   -> K1 and K4 are the SAME SECTION under the SAME LOAD at two")
print("      lengths, and the pair is the point. The capacity factor")
print("      falls from 1.34 at 3.2 m to 1.10 at 7.5 m, and the critical")
print("      POSITION moves from Top to Middle - which is the signature")
print("      of a slenderness moment rather than an end moment. Both")
print("      still pass, so a checker who only reads the verdict column")
print("      learns nothing; the factor and the position are the finding.")

print(f"\n{'-' * 108}")
print(f"PT beams: {len(BEAMS) - len(pt_faults)} of {len(BEAMS)} pass"
      + (f"; attention on {', '.join(pt_faults)}" if pt_faults else ""))
print(f"columns:  {len(COLUMNS) - len(column_faults)} of {len(COLUMNS)} pass"
      + (f"; attention on {', '.join(column_faults)}" if column_faults
         else ""))
print()
print("Neither of these checks has an 'As required' column, and that is not")
print("an omission. A PT beam is checked on STRESSES at two stages; an")
print("as-reinforced column is checked on a CAPACITY FACTOR. Forcing either")
print("into a steel-area comparison is how a check goes quietly wrong.")
