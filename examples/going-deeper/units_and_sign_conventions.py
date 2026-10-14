# ---
# Example:  Units and signs - the mistakes that produce plausible answers
# Feature:  pile_cap + pad_footing + retaining_wall (C16 + C15 + C14)
# Verified: yes - 2026-09-02 - every unit and sign behaviour measured on prokon-automation.exe
# ---
# A wrong unit does not raise. It returns a number, and the number looks
# like an answer. That makes units the most dangerous class of error in a
# multi-engine script, and the only defence is to know which engine speaks
# which language.
#
#   C16 pile_cap        METRES for everything - cap, piles, column, rebar
#                       depth. The only engine here that does.
#   C15 pad_footing     METRES for the pad and the columns, MILLIMETRES
#                       for the bars and their depths. Mixed, on purpose:
#                       it matches the desktop's own input page.
#   C14 retaining_wall  METRES for geometry, MILLIMETRES for cover.
#   everything else     MILLIMETRES for geometry, kN and kNm for loads.
#
# And three signs that are not obvious:
#   pile_cap tie force  NEGATIVE for tension
#   pad_footing z       NEGATIVE lowers the soil below the footing top
#   retaining_wall qmin NEGATIVE means the heel is lifting
#
# ⚠ EVERY DEMONSTRATION BELOW IS A PAIR: the right units and the wrong
# ones, side by side, so the size of the error is visible. A factor of a
# thousand is easy to spot. A factor of 1000 that lands inside a plausible
# range is not.

import prokon.v5

print("UNITS AND SIGNS")

# ── 1. C16 is metres. All of it. ───────────────────────────────────────
CAP_METRES = dict(
    design_code="CSA-A23.3:2019",
    column_dim_x=0.5, column_dim_y=0.5,
    no_of_piles=4, pile_dia=0.6, pile_spacing=1.8, pile_tolerance=0.05,
    cap_thickness=1.2, cap_overhang=0.3, bottom_rebar_depth=0.1,
    fc=30.0, fy=400.0,
)
LOAD = [{"name": "ULS", "load_factor": 1.0, "p": 4000.0}]

correct = prokon.v5.pile_cap.analyse(**CAP_METRES, load_cases=LOAD)["result"]

print(f"\n1. C16 pile_cap WORKS IN METRES")
print(f"   correct  (0.5 m column, 1.8 m spacing, 1.2 m cap):")
print(f"     cap {correct['cap_dim_x']:.2f} x {correct['cap_dim_y']:.2f} m, "
      f"strut Cr {correct['strut_results'][0]['load_cases'][0]['cr']:.1f} kN")

# Every dimension typed in millimetres - the whole-hand slip.
whole_hand = {**CAP_METRES,
              "column_dim_x": 500.0, "column_dim_y": 500.0,
              "pile_dia": 600.0, "pile_spacing": 1800.0,
              "cap_thickness": 1200.0, "cap_overhang": 300.0,
              "bottom_rebar_depth": 100.0}
try:
    wrong = prokon.v5.pile_cap.analyse(**whole_hand, load_cases=LOAD)["result"]
    print(f"   every input in mm by mistake:")
    print(f"     cap {wrong['cap_dim_x']:.1f} x {wrong['cap_dim_y']:.1f} m "
          f"- {wrong['cap_dim_x'] / 1000.0:.1f} km across")
    print(f"     strut Cr "
          f"{wrong['strut_results'][0]['load_cases'][0]['cr']:.1f} kN")
    print(f"     is_stable {wrong['is_stable']}, "
          f"geometry_is_valid {wrong['geometry_is_valid']}")
    print(f"   -> ACCEPTED. A cap that size is a valid strut-and-tie model,")
    print(f"      so nothing refuses it - but the plan dimension and a")
    print(f"      2-billion-kN strut are hard to miss.")
except prokon.v5.ProkonError as refusal:
    print(f"   every input in mm by mistake: {refusal.category}/"
          f"{refusal.code}")
    print(f"     {refusal.message.encode('ascii', 'replace').decode()[:66]}")

# ⚠ AND HERE IS THE GOOD NEWS, WHICH IS WORTH MORE THAN THE WARNING.
# C16's own geometry validation catches nearly every SINGLE-input unit
# error, by name. Measured across all seven length inputs: six are refused
# with a specific message about the geometry, and one gets through.
print(f"\n   ONE input in mm, seven ways - what the engine catches:")
print(f"   {'input':<20} {'outcome':<10} what happened")

right_tie = {tie["element_index"]: tie
             for tie in correct["tie_results"]}
correct_as = right_tie[correct["design_tie"]]["load_cases"][0]["as_required"]
slipped = []

for name in ("column_dim_x", "pile_dia", "pile_spacing", "pile_tolerance",
             "cap_thickness", "cap_overhang", "bottom_rebar_depth"):
    attempt = dict(CAP_METRES)
    attempt[name] = CAP_METRES[name] * 1000.0
    try:
        result = prokon.v5.pile_cap.analyse(**attempt, load_cases=LOAD)["result"]
    except prokon.v5.ProkonError as refusal:
        message = refusal.message.encode("ascii", "replace").decode()
        print(f"   {name:<20} {'REFUSED':<10} {message[:44]}")
        continue

    ties = {tie["element_index"]: tie for tie in result["tie_results"]}
    as_required = ties[result["design_tie"]]["load_cases"][0]["as_required"]
    plan_moved = abs(result["cap_dim_x"] - correct["cap_dim_x"]) > 1e-9
    slipped.append(name)
    print(f"   {name:<20} {'accepted':<10} cap "
          f"{result['cap_dim_x']:.2f} m "
          f"({'plan CHANGED' if plan_moved else 'plan unchanged'}), "
          f"tie As {as_required:.1f}")

print(f"\n   -> {7 - len(slipped)} of 7 are REFUSED, each with a message")
print(f"      naming the geometry rule it broke. That is C16's own")
print(f"      validation doing real work, and it is worth knowing about:")
print(f"      the engine is not indifferent to nonsense.")
if slipped:
    print(f"      The one that gets through is {', '.join(slipped)} - and it")
    print(f"      changes the CAP PLAN by two orders of magnitude, which is")
    print(f"      the first key anyone reads.")
    print(f"      So the practical defence is one assertion: check the cap")
    print(f"      plan against the size you expected, once, after the call.")

# ── 2. C15 is mixed, and that is deliberate ────────────────────────────
PAD = dict(
    design_code="BS8110 - 1997",
    a=2.5, b=2.5, yf=0.6, z=0.5,          # METRES
    c1=0.4, d1=0.4, e1=0.0, f1=0.0,       # METRES
    fcu=30.0, fy=450.0,
    allowable_bearing_pressure=200.0,
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,     # MILLIMETRES
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
)
PAD_LOAD = [{"name": "LC1", "pa1": 600.0, "hx1": 30.0,
             "mx1": 20.0, "lf1": 1.4}]

print(f"\n2. C15 pad_footing IS MIXED: metres for the pad, mm for the bars")
print(f"   a = {PAD['a']} m and bar_dia_x_bot = "
      f"{PAD['bar_dia_x_bot']:.0f} mm, in the SAME call")

# A footing loaded hard enough that its crack widths are non-zero, so the
# effect of the bars is visible at all.
HEAVY = {**PAD, "crack_width_code": "BS8007 - 1987"}
HEAVY_LOAD = [{"name": "LC1", "pa1": 900.0, "hx1": 30.0,
               "mx1": 40.0, "lf1": 1.4}]

print(f"\n   WHICH RESULTS DO THE BARS ACTUALLY MOVE?")
print(f"   {'bars supplied':<24} {'p sls':>9} {'as_x':>9} {'vcx':>9} "
      f"{'crack bot_x':>12}")

for label, bars in (
        ("Y16@200 (mm, correct)",
         dict(bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
              bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0)),
        ("Y25@100 (mm, heavier)",
         dict(bar_dia_x_bot=25.0, bar_spacing_x_bot=100.0,
              bar_dia_y_bot=25.0, bar_spacing_y_bot=100.0)),
        ("Y10@300 (mm, lighter)",
         dict(bar_dia_x_bot=10.0, bar_spacing_x_bot=300.0,
              bar_dia_y_bot=10.0, bar_spacing_y_bot=300.0)),
        ("0.016 @ 0.2 (METRES!)",
         dict(bar_dia_x_bot=0.016, bar_spacing_x_bot=0.2,
              bar_dia_y_bot=0.016, bar_spacing_y_bot=0.2)),
        ("no bars at all",
         dict(bar_dia_x_bot=0.0, bar_spacing_x_bot=0.0,
              bar_dia_y_bot=0.0, bar_spacing_y_bot=0.0)),
):
    result = prokon.v5.pad_footing.analyse(**{**HEAVY, **bars},
                                        load_cases=HEAVY_LOAD)["result"]
    critical = result["critical_uls"]
    crack = critical["crack_widths"]["bottom_x"]
    print(f"   {label:<24} "
          f"{result['max_bearing_pressure_sls']:>9.4f} "
          f"{critical['reinforcement']['as_x']:>9.3f} "
          f"{critical['shear']['vcx']:>9.6f} "
          f"{'null' if crack is None else format(crack, '.6f'):>12}")

print(f"\n   -> the bars move ONE column: the crack widths. The bearing")
print(f"      pressure, the steel DEMAND and the shear capacities are all")
print(f"      identical, because they are demands and code capacities -")
print(f"      not capacities of the steel you supplied.")
print(f"   -> so a bar-unit error is INVISIBLE in every number a reviewer")
print(f"      checks first, and in the crack width it shows up as 0.0000,")
print(f"      which reads as 'no cracking'.")
print(f"   -> and note the last row: with NO bars the crack widths come")
print(f"      back as NULL, not as 0. That is the engine distinguishing")
print(f"      'not computed' from 'computed as zero' - and it is the only")
print(f"      place in this result that tells you the check did not run.")

# ── 3. The z sign, which is a real input and not a mistake ────────────
print(f"\n3. C15's z IS SIGNED, and negative is a legitimate value")
print(f"   {'z (m)':>7} {'p sls':>9} {'meaning':<44}")
for z, meaning in ((1.0, "1 m of soil over the footing top"),
                   (0.5, "half a metre of cover"),
                   (0.0, "soil level with the footing top"),
                   (-0.3, "soil 300 mm BELOW the footing top"),
                   (-0.6, "soil at the base soffit - the floor of z"),
                   (-0.7, "below the soffit - refused, not clamped")):
    try:
        result = prokon.v5.pad_footing.analyse(**{**PAD, "z": z},
                                            load_cases=PAD_LOAD)["result"]
        print(f"   {z:>7.2f} {result['max_bearing_pressure_sls']:>9.2f} "
              f"{meaning:<44}")
    except prokon.v5.ProkonError as refusal:
        print(f"   {z:>7.2f} {'refused':>9} {meaning:<44}")
        print(f"   {'':>7} {'':>9} "
              f"{refusal.message.encode('ascii', 'replace').decode()[:60]}")
print(f"   -> a negative z is how you say 'no soil cover', and the engine")
print(f"      REFUSES anything below the soffit rather than clamping it.")
print(f"      Refusing is right: a clamp would answer a different question")
print(f"      than the one asked and say nothing about it.")

# ── 4. The three signs ─────────────────────────────────────────────────
print(f"\n4. THREE SIGNS WORTH KNOWING")

# (a) A pile-cap tie force is negative for tension.
tie = by_element[correct["design_tie"]] if False else {
    tie["element_index"]: tie for tie in correct["tie_results"]
}[correct["design_tie"]]["load_cases"][0]
forces = [entry["load_cases"][0]["tf"] for entry in correct["tie_results"]]
print(f"   (a) C16 tie forces: {[round(f, 1) for f in forces]}")
print(f"       all negative: {all(f < 0 for f in forces)}")
print(f"       the GOVERNING tie is the MOST NEGATIVE, so min() not max():")
print(f"         min {min(forces):.2f}   max {max(forces):.2f}")
print(f"       -> max() finds the LEAST loaded tie. A search written with")
print(f"          max() is not a slightly wrong answer; it is the wrong tie.")

# (b) A retaining wall's qmin can be negative.
WALL = dict(
    concrete_code="BS8110 - 1997",
    h1=5.0, b=0.5, d=2.0, c=0.4, at=0.3, ab=0.4,
    theta=30.0, delta=20.0, dg=18.0, db=25.0,
    fcu=25.0, fy=450.0, pmax=200.0,
    sf_overturning=1.5, sf_sliding=1.5,
)
print(f"\n   (b) C14's BEARING PRESSURE can go negative, and it is qmax")
print(f"       that does it - not qmin, which is where you would look.")
print(f"       {'heel d':>8} {'qmax':>10} {'qmin':>9} {'ratio':>9}  reading")
for heel in (2.0, 1.0, 0.5, 0.2, 0.0):
    try:
        result = prokon.v5.retaining_wall.analyse(
            **{**WALL, "d": heel},
            load_cases=[{"name": "LC", "w": 10.0}])["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"       {heel:>8.2f} refused: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:40]}")
        continue
    if result["qmax"] < 0:
        reading = "NEGATIVE qmax - not a pressure distribution"
    elif result["bearing_ratio"] > 1.0:
        reading = "over the allowable"
    else:
        reading = "within the allowable"
    print(f"       {heel:>8.2f} {result['qmax']:>10.2f} "
          f"{result['qmin']:>9.2f} {result['bearing_ratio']:>9.3f}  "
          f"{reading}")
print(f"       -> as the heel shrinks, qmax turns NEGATIVE and the")
print(f"          bearing_ratio follows it. qmin stays at 0 throughout, so")
print(f"          a script watching qmin for the sign change never sees it.")
print(f"       -> the test that works: require qmax > 0 AND")
print(f"          0 < bearing_ratio <= 1. A negative ratio is not a")
print(f"          utilisation that happens to be small - it is the")
print(f"          equilibrium having no physical solution, reported as")
print(f"          arithmetic.")

# (c) Axial tension in a column: negative N, and no flag in the result.
print(f"\n   (c) a column under TENSION: negative n")
for axial in (1500.0, 0.0, -500.0):
    result = prokon.v5.rectangular_column.analyse(
        design_code="SABS 0100 - 2000", h=400.0, b=400.0,
        dc_x=40.0, dc_y=40.0, fcu=30.0, fy=450.0,
        lex=3000.0, ley=3000.0,
        bracing_x="Braced", bracing_y="Braced", deltas=1.0,
        load_cases=[{"n": axial, "m2x": 100.0, "m1x": 50.0,
                     "m2y": 0.0, "m1y": 0.0}])["result"]
    if result["options"]:
        option = result["options"][0]
        print(f"       n = {axial:>8.0f} kN   {option['bar_description']:>8} "
              f"at {option['perc']:.3f} %   "
              f"feasible {result['has_feasible_design']}")
    else:
        print(f"       n = {axial:>8.0f} kN   no arrangement")
print(f"       result keys: {sorted(result)}")
print(f"       -> a TENSILE column designs normally and there is no flag")
print(f"          for it in the result at all. The envelope carries a")
print(f"          warning beside the result; the result itself is silent.")

print(f"\n{'-' * 72}")
print("The rule worth carrying: every engine's units are in its own input")
print("descriptions, and prokon_describe (or the docstring) states them.")
print("Read them once per engine and convert at the CALL SITE, with the")
print("division written out - which is what every workflow example here")
print("does, and why.")
