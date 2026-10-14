# ---
# Example:  Crack widths — your first analysis
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes — 2026-09-02 — crack width and steel area match values pinned in the C21 test suite; exact on prokon-automation.exe
# ---
# Check the crack widths in a reinforced-concrete section under service
# loading, and see the bar arrangements Prokon proposes to keep the
# cracks inside your allowable. This is the whole pattern: one call with
# named inputs, a dictionary of results back.
#
# The section here is a 300 mm water-retaining slab strip designed to
# BS8007 - 1987 — the classic crack-width job.

import prokon.v5

ALLOWABLE = 0.3  # the crack width we are designing to [mm]

result = prokon.v5.crack_widths.analyse(
    design_code="BS8007 - 1987",  # spelled exactly as the desktop names it
    slab_mode=True,   # a slab: bars are a diameter at a spacing, results per metre
    h=300.0,          # overall section depth [mm]
    hef=200.0,        # depth of the effective tension zone [mm]
    b=1000.0,         # width [mm] — see the note at the bottom
    cover=40.0,       # cover to the reinforcement [mm]
    fcu=30.0,         # concrete strength [MPa]
    fy=450.0,         # reinforcement yield strength [MPa]
    ea=200.0,         # elastic modulus of the steel [GPa]
    ec=26.0,          # elastic modulus of the concrete [GPa]
    allowable_crack_width=ALLOWABLE,
    high_bond_bar=True,
    short_term_load=True,
    # The serviceability load schedule is a JSON array of case objects.
    # One case here: 50 kNm/m service moment, ULS factor 1.5.
    load_cases='[{"n": 1, "m": 50, "m_uls": 1.5}]',
)["result"]

# Results are grouped per load case, in case-number order.
case = result["load_cases"][0]
print(f"Load case {case['load_case_number']}: "
      f"ultimate moment {case['moment_ult']:.0f} kNm/m")   # 75 kNm/m

# `optimised_configs` holds the arrangements the engine's own bar search
# found for this case. Reading them is the point of the run.
print(f"\n{'bars':>9} {'crack w':>9} {'As':>10} {'Mu':>10}   verdict")
for option in case["optimised_configs"]:
    calc = option["calc_result"]

    # ALWAYS read `governing_crack_width` — it is max(w, wmax1, wmax2),
    # the number the desktop reports and checks. The plainly-named
    # `crack_width` is only one of the three terms and can under-report
    # (measured: 0.1679 against 0.1719 mm on a restrained-thermal case).
    width = calc["governing_crack_width"]

    print(f"{option['formatted_bars']:>9} "
          f"{width:>7.4f} mm "
          f"{calc['steel_area']:>7.0f} mm2 "
          f"{option['moment_capacity']:>7.1f} kNm/m   "
          f"{'OK' if option['meets_all_criteria'] else 'NO GOOD'}")

# Measured for this section:
#     Y10@75    0.1106 mm    1047 mm2     99.8 kNm/m   OK
#    Y16@250    0.2224 mm     804 mm2     75.6 kNm/m   OK
#    Y25@500    0.2420 mm     982 mm2     90.5 kNm/m   OK
#    Y40@500    0.1119 mm    2513 mm2    223.9 kNm/m   OK

# `meets_all_criteria` is the engine's own verdict on one arrangement —
# crack width within the allowable AND both capacities adequate. It is a
# real verdict (measured False on an under-reinforced section), but do
# not stop there: an arrangement that fails on CAPACITY can report a
# crack width of 0.0, which reads like "no cracking" and is not. So
# check the width yourself as well, exactly as you would on paper.
best = min(case["optimised_configs"], key=lambda o: o["calc_result"]["steel_area"])
width = best["calc_result"]["governing_crack_width"]
adequate = (best["moment_capacity"] >= case["moment_ult"]
            and width <= ALLOWABLE
            and best["meets_all_criteria"])

print(f"\nLightest arrangement offered: {best['formatted_bars']} "
      f"({best['calc_result']['steel_area']:.0f} mm2/m)")
print(f"  crack width {width:.4f} mm against an allowable of {ALLOWABLE} mm"
      f"  ->  {'ACCEPT' if adequate else 'DO NOT USE'}")

# A note on `b` in slab mode: it is required, but every published result
# is per metre width regardless of what you pass (measured — b = 1, 500,
# 1000 and 2000 give byte-identical results). Pass 1000.0 and read
# "mm2" as "mm2/m", "kNm" as "kNm/m".
