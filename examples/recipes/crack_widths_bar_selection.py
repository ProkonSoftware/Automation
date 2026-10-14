# ---
# Example:  Crack widths — pick the lightest bar arrangement that meets a 0.2 mm limit
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes — 2026-09-02 — the engine's Y10@75 row is the value pinned in the C21 test suite; every catalogue row measured; exact on prokon-automation.exe
# ---
# A liquid-retaining wall has to keep cracks below 0.2 mm. The desktop
# program evaluates ONE user arrangement at a time, so choosing between
# thirty-five candidates means thirty-five sessions of retyping. A script
# runs the whole catalogue in a few seconds and reports the lightest
# arrangement that genuinely works.
#
# This is a real goal-seek, and it earns its keep: the engine's own bar
# search returns four arrangements off its internal grid, and sweeping
# YOUR OWN catalogue — the diameters and spacings your detailer actually
# uses — finds a lighter answer than any of them.
#
# ⚠ The lesson this recipe exists to teach: you cannot select on crack
# width alone. A grossly under-reinforced section reports a SMALL crack
# width, because the section is nowhere near cracking under a load it
# cannot carry. Screen on capacity first.

import prokon.v5

# The wall panel. Everything but the reinforcement is fixed.
WALL = dict(
    design_code="BS8007 - 1987",
    slab_mode=True,
    h=300.0,          # wall thickness [mm]
    hef=200.0,        # effective tension zone [mm]
    b=1000.0,         # per metre of wall (see the quick-start's note on b)
    cover=40.0,       # cover [mm]
    fcu=30.0,         # concrete strength [MPa]
    fy=450.0,         # reinforcement yield strength [MPa]
    ea=200.0,         # steel modulus [GPa]
    ec=26.0,          # concrete modulus [GPa]
    high_bond_bar=True,
    short_term_load=True,
    load_cases='[{"n": 1, "m": 50, "m_uls": 1.5}]',   # 50 kNm/m service, 1.5 ULS
)

ALLOWABLE = 0.2               # liquid-retaining crack width limit [mm]
DIAMETERS = (10, 12, 16, 20, 25)
SPACINGS = (100, 125, 150, 175, 200, 250, 300)

# One reference run tells us the ultimate moment the arrangement must
# carry, and what the engine's own bar search would offer.
reference = prokon.v5.crack_widths.analyse(allowable_crack_width=ALLOWABLE, **WALL)["result"]
case = reference["load_cases"][0]
m_ult = case["moment_ult"]

print(f"Wall panel 300 mm, BS8007 - 1987, allowable crack width {ALLOWABLE} mm")
print(f"Ultimate moment to carry: {m_ult:.0f} kNm/m\n")            # 75 kNm/m

print("The engine's own search offered:")
for option in case["optimised_configs"]:
    print(f"   {option['formatted_bars']:>8}  "
          f"{option['calc_result']['steel_area']:>7.1f} mm2/m  "
          f"w = {option['calc_result']['governing_crack_width']:.4f} mm  "
          f"Mu = {option['moment_capacity']:.1f} kNm/m")
# Measured:  Y10@75  1047.2 mm2/m  0.1106 mm   99.8 kNm/m
#            Y16@200 1005.3 mm2/m  0.1671 mm   94.5 kNm/m
#            Y25@400 1227.2 mm2/m  0.1856 mm  113.1 kNm/m
#            Y40@500 2513.3 mm2/m  0.1119 mm  223.9 kNm/m
# The first row is this feature's reference value: Y10@75 comes back at
# 0.11059554804834058 mm on 1047.197551196598 mm2/m, the numbers pinned
# to the last digit in C21's own test suite.

print(f"\n{'bars':>9} {'As':>12} {'crack w':>10} {'Mu':>11}  verdict")

workable = []
for dia in DIAMETERS:
    for spacing in SPACINGS:
        bars = f"Y{dia}@{spacing}"

        analysis = prokon.v5.crack_widths.analyse(
            allowable_crack_width=ALLOWABLE,
            user_slab_bars=bars,          # evaluate THIS arrangement
            **WALL,
        )["result"]

        # The named arrangement comes back beside the engine's own search.
        # It is None when the engine could not read the notation at all.
        evaluated = analysis["load_cases"][0]["user_slab_result"]
        if evaluated is None:
            print(f"{bars:>9}   (the engine did not read this notation)")
            continue

        calc = evaluated["calc_result"]
        width = calc["governing_crack_width"]     # never `crack_width` — see below
        capacity = evaluated["moment_capacity"]

        # THE SCREEN, in the order an engineer would apply it:
        #   1. can the section carry the load at all?
        #   2. is the crack width inside the allowable?
        #   3. does the engine agree on every criterion?
        strong_enough = capacity >= m_ult
        narrow_enough = width <= ALLOWABLE
        accepted = strong_enough and narrow_enough and evaluated["meets_all_criteria"]

        if not strong_enough:
            verdict = "under-strength"
        elif not narrow_enough:
            verdict = "cracks too wide"
        elif not accepted:
            verdict = "engine rejects"
        else:
            verdict = "OK"

        print(f"{bars:>9} {calc['steel_area']:>9.1f} mm2 "
              f"{width:>7.4f} mm {capacity:>7.1f} kNm/m  {verdict}")

        if accepted:
            workable.append((calc["steel_area"], bars, width, capacity))

# The lightest arrangement that passes every check.
area, bars, width, capacity = min(workable)
margin = (capacity / m_ult - 1.0) * 100.0

print(f"\nLightest workable arrangement: {bars}")
print(f"  steel        {area:.1f} mm2/m")                  # 904.8 mm2/m
print(f"  crack width  {width:.4f} mm  (allowable {ALLOWABLE} mm)")   # 0.1500 mm
print(f"  moment       {capacity:.1f} kNm/m against {m_ult:.0f} kNm/m "
      f"- {margin:.0f}% spare")                            # 85.8 vs 75 -> 14%

# That is 10 % less steel than the lightest arrangement the engine's own
# search offered (Y16@200 at 1005.3 mm2/m), and 14 % less than its first
# choice — the whole reason for sweeping a catalogue of your own.
print("\nNext three, by weight:")
for area, bars, width, capacity in sorted(workable)[1:4]:
    print(f"  {bars:>8}  {area:>7.1f} mm2/m  w = {width:.4f} mm  "
          f"Mu = {capacity:.1f} kNm/m ({(capacity / m_ult - 1.0) * 100.0:.0f}% spare)")
# Measured:  Y16@200 1005.3 mm2/m 0.1671 mm  94.5 kNm/m (26% spare)
#            Y20@300 1047.2 mm2/m 0.1906 mm  97.6 kNm/m (30% spare)
#            Y12@100 1131.0 mm2/m 0.1139 mm 107.3 kNm/m (43% spare)

# ⚠ WHY A WIDTH-ONLY FILTER WOULD BE DANGEROUS HERE — measured on this
# very wall. Y10@300 reports the SMALLEST crack width in the whole
# catalogue, 0.0712 mm, comfortably better than the 0.1500 mm of the
# answer above. It carries 24.9 kNm/m against the 75 kNm/m applied.
# Sorting on crack width and taking the smallest would hand you the
# weakest section on the list.
#
# ⚠ AND ALWAYS READ `governing_crack_width`, NOT `crack_width`. The two
# are equal on a plain flexural case like this one, and they are NOT
# equal once temperature and restraint are involved: `crack_width` is
# one of the three terms the governing value takes the maximum of, and
# it under-reports. See the batch-to-Excel recipe's roof slab.
