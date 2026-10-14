# ---
# Example:  Gravity load take-down - floor beam to column to footing
# Feature:  continuous_beam + beam_section + rectangular_column + pad_footing
#           (C01 Continuous Beam + C22 Beam Section + C11 Rectangular Column
#            + C15 Pad Footing)
# Verified: yes - 2026-09-02 - every number measured on prokon-automation.exe; the reactions are C01's own
# ---
# The oldest job in reinforced concrete: work out what the beam carries,
# hand its support reactions to the columns, hand the column loads to the
# footings. Done by hand it is an afternoon of transcription, and every
# transcription is a chance to drop a decimal.
#
# Here the reactions are READ OUT OF C01'S RESULT. Nothing is re-typed, so
# there is nothing to mis-type - and if you change a span length at the top
# of this file, every column and every footing below moves with it.
#
#   1. continuous_beam    a 3-span edge beam: moments, steel, reactions
#   2. beam_section       the same critical section re-checked WITH TORSION,
#                         which an edge beam carries and C01 does not model
#   3. rectangular_column each column, from C01's own reaction
#   4. pad_footing        each footing, from the column load
#
# ⚠ WHY STEP 2 EXISTS, and it is the interesting part. C01 designs a
# continuous beam for bending and shear. It has no torsion. An EDGE beam
# picks up torsion from the slab framing into one side of it, and that
# torsion is real steel. C22 is the engine that takes it. Running both is
# not redundancy - it is two different questions about one beam.

import prokon.v5

CODE = "BS8110 - 1997"

# ── The brief: an edge beam on grid A, three spans ──────────────────────
SPANS = (6.0, 7.0, 6.0)     # m
BW = 300.0                  # beam web width, mm
BEAM_H = 600.0              # beam overall depth, mm
SLAB_H = 175.0              # the one-way slab framing into it, mm
SLAB_SPAN = 4.5             # m, slab span perpendicular to the beam
STOREY = 3.6                # m
FLOORS = 3

FCU = 30.0
FY = 500.0
FYV = 250.0
CONCRETE = 25.0
ALLOWABLE = 175.0           # kPa, a modest founding stratum

# Slab loads. An EDGE beam takes half a slab span, plus the parapet.
slab_dead = SLAB_H / 1000.0 * CONCRETE + 1.5     # self weight + finishes
slab_live = 2.5                                  # kPa, residential
parapet = 4.0                                    # kN/m of dead load

w_dead = slab_dead * SLAB_SPAN / 2.0 + parapet
w_live = slab_live * SLAB_SPAN / 2.0

print("GRAVITY TAKE-DOWN - grid A edge beam, 3 spans")
print(f"  spans {SPANS} m, beam {BW:.0f} x {BEAM_H:.0f}, slab {SLAB_H:.0f} mm "
      f"spanning {SLAB_SPAN} m")
print(f"  beam line load: dead {w_dead:.2f} kN/m (incl. {parapet:.1f} parapet)"
      f" + live {w_live:.2f} kN/m")

# ── 1. The beam ─────────────────────────────────────────────────────────
# C01 generates self weight itself when given a density, so the line load
# above is everything EXCEPT the beam's own weight.
beam = prokon.v5.continuous_beam.analyse(
    design_code=CODE,
    fcu=FCU, fy=FY, fyv=FYV,
    concrete_density=CONCRETE,
    cover_top=40.0, cover_bot=40.0,
    live_permanent_percent=25.0,
    creep_coefficient=2.0,
    shrinkage_strain=300e-6,
    sections=[{"n": 1, "bw": BW, "d": BEAM_H}],
    segments=[{"span": n + 1, "length": length, "sec_left": 1}
              for n, length in enumerate(SPANS)],
    supports=[{"n": n + 1} for n in range(len(SPANS) + 1)],
    loads=[row for n, _ in enumerate(SPANS) for row in (
        {"case": "Dead", "span": n + 1, "w_left": w_dead},
        {"case": "Live", "span": n + 1, "w_left": w_live},
    )],
)["result"]

print(f"\n1. BEAM  (C01)   {beam['span_count']} spans, "
      f"{beam['total_length']:.1f} m, {beam['position_count']} positions")
print(f"   sagging {beam['max_sagging_moment']:>8.1f} kNm   "
      f"hogging {beam['max_hogging_moment']:>8.1f} kNm   "
      f"shear {beam['max_shear']:>7.1f} kN")
print(f"   {'span':>5} {'As bot':>9} {'As top':>9} {'Asv/sv':>9} "
      f"{'defl':>8} {'limit':>8}  {'crack':>7}")

for span in beam["spans"]:
    limit = span["length"] * 1000.0 / 250.0
    print(f"   {span['span_number']:>5} {span['max_bottom_steel']:>9.0f} "
          f"{span['max_top_steel']:>9.0f} {span['max_shear_steel']:>9.3f} "
          f"{span['max_total_deflection']:>8.2f} {limit:>8.1f}  "
          f"{span['max_bottom_crack_width']:>7.4f}"
          f"{'' if span['max_total_deflection'] <= limit else '  <-- DEFLECTION'}")

print(f"   deflection worst {beam['max_deflection']:.2f} mm, "
      f"crack worst {beam['max_crack_width']:.4f} mm")

# -- 2. The same beam, now with the torsion an edge beam really carries --
# Torsion from the slab: the slab's end moment applied to the beam over its
# own span. A conservative and entirely conventional estimate, computed here
# rather than guessed.
slab_uls = 1.4 * slab_dead + 1.6 * slab_live
slab_end_moment = slab_uls * SLAB_SPAN ** 2 / 24.0     # kNm/m along the beam
torsion = slab_end_moment * SPANS[1] / 2.0             # kNm at the support

# First WITHOUT torsion, purely as a cross-check on the two engines. This is
# worth doing once on any job: C01 and C22 are different native libraries
# answering the same question, and if they disagree you want to know before
# the drawing goes out, not after.
plain = prokon.v5.beam_section.analyse(
    design_code=CODE,
    m=abs(beam["max_hogging_moment"]),
    v=beam["max_shear"],
    bw=BW, h=BEAM_H,
    dc_t=40.0, dc_b=40.0, dc_s=40.0,
    fcu=FCU, fy=FY, fyv=FYV,
)["result"]

section = prokon.v5.beam_section.analyse(
    design_code=CODE,
    m=abs(beam["max_hogging_moment"]),
    v=beam["max_shear"],
    tor=torsion,
    bw=BW, h=BEAM_H,
    dc_t=40.0, dc_b=40.0, dc_s=40.0,
    fcu=FCU, fy=FY, fyv=FYV,
)["result"]

print("\n2. CRITICAL SECTION  (C22)")
print(f"   M = {abs(beam['max_hogging_moment']):.1f} kNm (C01's own hogging), "
      f"V = {beam['max_shear']:.1f} kN")

# TWO ENGINES, ONE ANSWER. Measured 2026-09-02: C01's max_top_steel and
# C22's ast are the SAME NUMBER to the last binary digit - 738.2981992840653
# - on this beam. Two native libraries, two processes, zero difference.
# Printing the gap rather than asserting it keeps the example running if a
# future build moves either engine, while still saying so loudly. The exact
# value is pinned in _tools/check-pinned-values.py.
c01_steel = beam["spans"][0]["max_top_steel"]
gap = plain["ast"] - c01_steel
print(f"   cross-check: C01 top steel {c01_steel:.10f} mm2")
print(f"                C22 Ast       {plain['ast']:.10f} mm2")
print(f"                difference    {gap:.3e} mm2"
      f"  ->  {'IDENTICAL' if gap == 0.0 else 'THE TWO ENGINES DISAGREE'}")

print(f"\n   now the same section with T = {torsion:.1f} kNm of torsion:")
print(f"   bending capacity Mu = {section['mu']:.1f} kNm"
      f"  ->  {'OK' if section['mu'] >= abs(beam['max_hogging_moment']) else 'SECTION TOO SMALL'}")
print(f"   shear stress v = {section['vv']:.3f} MPa  (limit {section['vcu']:.3f})")
print(f"   {'':<22} {'shear only':>12} {'with torsion':>14}")
print(f"   {'longitudinal Ast':<22} {plain['ast']:>12.0f} {section['ast']:>14.0f}")
print(f"   {'torsion Ast1 (extra)':<22} {plain['ast1']:>12.0f} {section['ast1']:>14.0f}")
print(f"   {'links Asv/sv':<22} {plain['asv']:>12.4f} {section['asv']:>14.4f}")
print(f"   {'torsion links Asvt1':<22} {plain['asvt1']:>12.4f} {section['asvt1']:>14.4f}")

torsion_bars = section["reinforcement"]["combined_tension_torsion_bars"]
plain_bars = plain["reinforcement"]["tension_bars"]
if torsion_bars and plain_bars:
    print(f"   bars: bending alone {plain_bars[0]['description']}, "
          f"with torsion {torsion_bars[0]['description']}")
print("   -> the BENDING steel does not move: torsion arrives as Ast1 on top")
print(f"      of it ({section['ast1']:.0f} mm2 here) and as links roughly "
      f"{section['asvt1'] / section['asv']:.1f}x the")
print("      shear requirement. That is steel C01 alone never asks for, and")
print("      it is why an edge beam gets both engines rather than one.")


# ── 3. The columns, from C01's own reactions ────────────────────────────
# C01 publishes reaction_ultimate per support. That is the number a column
# wants, and taking it from the result is the whole point of one binary.
print(f"\n3. COLUMNS  (C11)   {FLOORS} floors above ground")
print(f"   {'support':>8} {'R uls/floor':>12} {'N ground':>10} "
      f"{'size':>10} {'bars':>9} {'steel %':>8}")

column_loads = {}
for support in beam["supports"]:
    per_floor = support["reaction_ultimate"]
    self_weight = 1.4 * FLOORS * (0.4 * 0.4 * CONCRETE * STOREY)
    n_uls = FLOORS * per_floor + self_weight
    column_loads[support["support_number"]] = (
        n_uls,
        FLOORS * support["reaction_service"] + FLOORS * 0.4 * 0.4 * CONCRETE * STOREY,
    )

    # Grow the square column until the steel fits under 4 %.
    chosen = None
    for size in (300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0):
        column = prokon.v5.rectangular_column.analyse(
            design_code=CODE,
            h=size, b=size, dc_x=45.0, dc_y=45.0,
            fcu=FCU, fy=FY,
            lex=0.9 * STOREY * 1000.0, ley=0.9 * STOREY * 1000.0,
            bracing_x="Braced", bracing_y="Braced", deltas=1.0,
            load_cases=[{"n": n_uls, "m2x": 40.0, "m1x": 20.0,
                         "m2y": 25.0, "m1y": 12.0}],
        )["result"]
        if column["has_feasible_design"] and column["options"]:
            best = min(column["options"], key=lambda o: o["perc"])
            if best["perc"] <= 4.0 and best["all_pass"]:
                chosen = (size, best)
                break

    if chosen is None:
        print(f"   {support['support_number']:>8} {per_floor:>12.1f} "
              f"{n_uls:>10.0f}   no size up to 600 mm carries it at 4 % steel")
        continue

    size, best = chosen
    print(f"   {support['support_number']:>8} {per_floor:>12.1f} {n_uls:>10.0f} "
          f"{size:>7.0f} sq {best['bar_description']:>9} {best['perc']:>8.3f}")

# ── 4. The footings ─────────────────────────────────────────────────────
print(f"\n4. FOOTINGS  (C15)   {ALLOWABLE:.0f} kPa allowable")
print(f"   {'support':>8} {'N sls':>9} {'pad':>12} {'p sls':>9} "
      f"{'As x':>8} {'punching':>10}")

for number, (n_uls, n_sls) in sorted(column_loads.items()):
    answer = None
    for plan in [1.4 + 0.2 * step for step in range(16)]:     # 1.4 to 4.4 m
        footing = prokon.v5.pad_footing.analyse(
            design_code=CODE,
            a=plan, b=plan, yf=0.5, z=0.4,
            c1=0.4, d1=0.4, e1=0.0, f1=0.0,
            fcu=FCU, fy=FY,
            allowable_bearing_pressure=ALLOWABLE,
            bar_dia_x_bot=16.0, bar_spacing_x_bot=150.0,
            bar_dia_y_bot=16.0, bar_spacing_y_bot=150.0,
            load_cases=[{"name": "Gravity", "pa1": n_sls, "lf1": 1.45}],
        )["result"]
        if footing["max_bearing_pressure_sls"] <= ALLOWABLE:
            answer = (plan, footing)
            break

    if answer is None:
        print(f"   {number:>8} {n_sls:>9.0f}   nothing up to 4.4 m fits "
              f"{ALLOWABLE:.0f} kPa - consider a raft or piles")
        continue

    plan, footing = answer
    shear = footing["critical_uls"]["shear"]
    # vcp = 0 means the punching perimeter did not FIT in the pad, so the
    # check never ran. Reading "vp <= vcp" as 0 <= 0 would call that a pass.
    if shear["vcp"] <= 0:
        punching = "not checked"
    else:
        punching = "OK" if shear["vp"] <= shear["vcp"] else "FAILS"

    print(f"   {number:>8} {n_sls:>9.0f} {plan:>7.2f} sq  "
          f"{footing['max_bearing_pressure_sls']:>9.1f} "
          f"{footing['critical_uls']['reinforcement']['as_x']:>8.0f} "
          f"{punching:>10}")

print("\n" + "-" * 72)
print("Change a span at the top of this file and re-run: the reactions, the")
print("columns and the footings all follow. That is the difference between a")
print("script and a spreadsheet of transcribed numbers.")
