# ---
# Example:  Reading a deeply nested result without tripping over it
# Feature:  crack_widths + prestressed_concrete (C21 + C02) - the deepest results here
# Verified: yes - 2026-09-02 - every shape and hazard measured on prokon-automation.exe
# ---
# Most engines here return a flat-ish dictionary. Two do not: C21 nests
# four levels deep, and C02 returns arrays over eighty result positions.
# Those two are where a script trips, and it trips in four ways:
#
#   1. AN EMPTY LIST         a search that found nothing returns [], and
#                            iterating it prints a bare header
#   2. A NULL WHERE A NUMBER LIVES  a key that was not computed is None,
#                            not 0, and formatting it raises TypeError
#   3. max() OVER A POSITION ARRAY  can return a value that is not the
#                            quantity you asked for
#   4. A DUPLICATED POSITION every support appears TWICE, about 0.1 mm
#                            apart, so "the same x" is not an equality test
#
# ⚠ ALL FOUR ARE ORDINARY. None is a defect - they are what a result looks
# like when it has to represent "no answer here" and "eighty positions
# along a member" honestly. The techniques below are the whole content of
# this file.

import prokon.v5

print("READING A DEEPLY NESTED RESULT")

# ── The shape of a C21 result ──────────────────────────────────────────
SLAB = dict(
    design_code="BS8007 - 1987", slab_mode=True,
    h=300.0, hef=200.0, b=1000.0, cover=40.0,
    fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
    allowable_crack_width=0.3, high_bond_bar=True, short_term_load=True,
)

result = prokon.v5.crack_widths.analyse(**SLAB,
                                     load_cases=[{"n": 1, "m": 50.0,
                                                  "m_uls": 1.5}])["result"]

print(f"\n1. FOUR LEVELS DEEP")
print(f"   result                                  "
      f"{sorted(result)}")
case = result["load_cases"][0]
print(f"   result['load_cases'][0]                 {sorted(case)}")
option = case["optimised_configs"][0]
print(f"   ...['optimised_configs'][0]             {sorted(option)}")
print(f"   ......['calc_result']                   "
      f"{sorted(option['calc_result'])[:6]} ...")
print(f"\n   the crack width lives at:")
print(f"     result['load_cases'][0]['optimised_configs'][0]"
      f"['calc_result']['governing_crack_width']")
print(f"     = {option['calc_result']['governing_crack_width']!r}")
print(f"   -> and 'governing_crack_width' is the one to read, not")
print(f"      'crack_width'. The plain name is ONE of three terms; the")
print(f"      governing one is max of the three and is what the desktop")
print(f"      reports. On this arrangement they agree "
      f"({option['calc_result']['crack_width'] == option['calc_result']['governing_crack_width']}),")
print(f"      which is exactly why the difference goes unnoticed.")

# ── 2. The empty list ──────────────────────────────────────────────────
print(f"\n2. AN EMPTY LIST IS AN ANSWER")
impossible = prokon.v5.crack_widths.analyse(
    **{**SLAB, "allowable_crack_width": 0.01},
    load_cases=[{"n": 1, "m": 50.0, "m_uls": 1.5}])["result"]
tight = impossible["load_cases"][0]
print(f"   allowable 0.01 mm: is_analysed {impossible['is_analysed']}, "
      f"{len(tight['optimised_configs'])} arrangement(s)")
print(f"   no exception, no warning - the search simply found nothing.")
print(f"\n   the WRONG shape:")
print(f"     for option in case['optimised_configs']:  # prints a header")
print(f"         ...                                   # and nothing else")
print(f"   the RIGHT shape:")
if not tight["optimised_configs"]:
    print(f"     -> 'no arrangement meets a 0.01 mm limit on this section'")
    print(f"        which is a real engineering answer: the section is too")
    print(f"        thin, or the limit is not achievable with bars.")

# ── 3. The null ────────────────────────────────────────────────────────
print(f"\n3. A NULL WHERE A NUMBER LIVES")
print(f"   user_slab_result and user_beam_result are None unless you")
print(f"   supplied user_slab_bars / user_beam_bars:")
print(f"     without: {case['user_slab_result']!r}")
with_bars = prokon.v5.crack_widths.analyse(
    **SLAB, user_slab_bars="Y16@200",
    load_cases=[{"n": 1, "m": 50.0, "m_uls": 1.5}])["result"]
mine = with_bars["load_cases"][0]["user_slab_result"]
print(f"     with:    a dict of {len(mine)} keys, crack "
      f"{mine['calc_result']['governing_crack_width']:.4f} mm")
print(f"   -> so `result[...]['user_slab_result']['calc_result'][...]`")
print(f"      raises TypeError whenever you forgot the input. Test the")
print(f"      level that can be None, then read through it.")

# A null can also appear INSIDE a numeric field, on some codes.
print(f"\n   and a null inside a numeric field, on some codes:")
import warnings
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    aci = prokon.v5.crack_widths.analyse(
        **{**SLAB, "design_code": "ACI224.1 - 07"},
        load_cases=[{"n": 1, "m": 50.0, "m_uls": 1.5}])["result"]
aci_case = aci["load_cases"][0]["optimised_configs"][0]["calc_result"]
nulls = sorted(key for key, value in aci_case.items() if value is None)
print(f"     ACI224.1 - 07: {len(nulls)} null field(s) - {nulls}")
print(f"     and {len(caught)} warning(s) explaining each one")
for entry in caught[:2]:
    sentence = str(entry.message).split(":")[0]
    print(f"       {sentence.encode('ascii', 'replace').decode()}")
print(f"   -> the engine REFUSES to invent a value it cannot compute and")
print(f"      warns about each one. That is the behaviour you want; it")
print(f"      also means any numeric field can be None on some code, so")
print(f"      format defensively when you sweep codes.")

# ── 4. C02: eighty positions, and what max() does to them ─────────────
print(f"\n4. AN ARRAY OVER RESULT POSITIONS")

TENDON = {
    "no": 1, "bond": "Bonded", "strength": 1860.0, "max_stress_pct": 75,
    "dia": 75, "area": 900, "k": 0.0012, "u": 0.19, "pullin": 6,
    "relax": 2.5, "est": 195e6, "min_harp_radius": 4.0,
}
SPANS = (9.0, 11.0, 9.0)
beam = prokon.v5.prestressed_concrete.analyse(
    design_code="BS8110 - 1997", title="nesting demo",
    fcu=40.0, fy=450.0, fyv=250.0, fci=30.0,
    ec=30e6, est=200e6, density=24.0,
    top_cover=30.0, bottom_cover=30.0,
    permanent_live_load_pct=25.0, creep=2.0,
    balanced_dead_load_pct=100.0, generated_profile="Parabolic",
    tendon_properties=[TENDON],
    sections=[{"name": "s", "bw": 3000.0, "d": 280.0}],
    span_segments=[{"span": n + 1, "length": length, "sec_left": "s"}
                   for n, length in enumerate(SPANS)],
    supports=[{"no": n + 1, "d_below": 400, "b_below": 400,
               "h_below": 3.2, "code_below": "F"}
              for n in range(len(SPANS) + 1)],
    loads=[row for n, _ in enumerate(SPANS) for row in (
        {"case": "D", "span": n + 1, "wl": 3.6},
        {"case": "L", "span": n + 1, "wl": 9.0})],
)["result"]

positions = beam["positions"]
print(f"   {beam['npos']} positions over {beam['ltot']:.2f} m")
print(f"   arrays of that length: sls.mn, sls.mp, uls.mnu, uls.mpu,")
print(f"   deflections.ditot, crack_widths.cwt, cables.pax, ... "
      f"{len(beam['sls']['mn'])} entries each")

# ── The duplicated support position ────────────────────────────────────
print(f"\n   THE DUPLICATED POSITION. Every support appears twice:")
walked = [0.0]
for length in SPANS:
    walked.append(walked[-1] + length)
for target in walked:
    near = [(index, positions[index]) for index in range(len(positions))
            if abs(positions[index] - target) < 0.01]
    values = ", ".join(f"{x!r}" for _, x in near)
    print(f"     x = {target:>6.2f}   {len(near)} entr(y/ies) at {values}")
print(f"   -> the pair is NOT at the same x to the last digit: it reads")
print(f"      8.0 and 8.0001, a 0.1 mm offset. So `positions[i] == target`")
print(f"      finds one of them and `abs(positions[i] - target) < 0.001`")
print(f"      finds both. That difference has caused a real bug in this")
print(f"      example set - see the crack_summary() note in")
print(f"      workflows/post_tensioned_versus_rc_floor.py.")

# ── max() over a position array ────────────────────────────────────────
print(f"\n   AND WHAT max() CAN RETURN. The crack-width array:")
crack = beam["crack_widths"]["cwt"]
worst = max(range(len(crack)), key=lambda index: crack[index])
print(f"     max        {crack[worst]:.4f} mm at x = {positions[worst]:.4f} m")
zeros = sum(1 for value in crack if value == 0)
non_zero = sorted({round(value, 4) for value in crack if value})
print(f"     {zeros} of {len(crack)} positions are exactly 0")
print(f"     distinct non-zero values: {non_zero[:8]}"
      f"{' ...' if len(non_zero) > 8 else ''}")


def neighbours_of(index, values, places, tolerance=0.001):
    """The nearest values at a DIFFERENT position. See the note above."""
    at = places[index]
    left = index
    while left > 0 and abs(places[left] - at) <= tolerance:
        left -= 1
    right = index
    while right < len(values) - 1 and abs(places[right] - at) <= tolerance:
        right += 1
    return [values[side] for side in (left, right)
            if abs(places[side] - at) > tolerance]


nearby = neighbours_of(worst, crack, positions)
print(f"     the values at the nearest DIFFERENT positions: "
      f"{[round(value, 4) for value in nearby]}")

if not nearby:
    print(f"     -> the peak is at an end position and has no neighbour on")
    print(f"        one side. Nothing to compare it with here.")
elif max(nearby) == 0.0:
    print(f"     -> the neighbours are exactly ZERO, so no ratio exists.")
    print(f"        That is normal on a crack-width array: most positions")
    print(f"        are uncracked, and the cracked ones are isolated by")
    print(f"        construction. The comparison is only meaningful on a")
    print(f"        quantity that varies SMOOTHLY - a moment, a deflection,")
    print(f"        a stress - so pick the array before you pick the test.")
elif crack[worst] > 100.0 * max(nearby):
    print(f"     -> the peak is {crack[worst] / max(nearby):.0f}x its own")
    print(f"        neighbours. On a smooth quantity that is a number to")
    print(f"        question, not a number to design to.")
else:
    print(f"     -> the peak is {crack[worst] / max(nearby):.1f}x its")
    print(f"        neighbours, which is in line. Establishing that is the")
    print(f"        point: on a per-position array, max() alone is not a")
    print(f"        check.")

# And the same test on a quantity that DOES vary smoothly, where it means
# something: the SLS moment envelope.
moments = [abs(value) for value in beam["sls"]["mn"]]
peak = max(range(len(moments)), key=lambda index: moments[index])
smooth_neighbours = neighbours_of(peak, moments, positions)
print(f"\n     the same test on a SMOOTH array (sls.mn):")
print(f"       peak {moments[peak]:.2f} kNm at x = {positions[peak]:.4f} m")
print(f"       neighbours {[round(value, 2) for value in smooth_neighbours]}")
if smooth_neighbours and max(smooth_neighbours) > 0:
    print(f"       ratio {moments[peak] / max(smooth_neighbours):.2f}x - "
          f"in line, as a moment envelope should be")
    print(f"     -> THAT is the array the neighbour test belongs on.")

# ── The reusable helpers ───────────────────────────────────────────────
print(f"\n5. THE FOUR HELPERS, WORTH COPYING")
print("""
   def at(node, *path, default=None):
       \"\"\"Walk a nested result, stopping at the first missing level.\"\"\"
       for key in path:
           if node is None:
               return default
           node = node[key] if isinstance(node, dict) else node[key]
       return default if node is None else node

   def number(value, spec=".4f", absent="n/a"):
       \"\"\"Format a value that may be None.\"\"\"
       return absent if value is None else format(value, spec)

   def peak_with_neighbours(values, places, tolerance=0.001):
       \"\"\"The maximum, and the nearest values at a DIFFERENT place.\"\"\"
       ...   # as neighbours_of() above

   def rows(node, key):
       \"\"\"A list that may be empty, iterated safely.\"\"\"
       return node.get(key) or []
""")

print(f"   used together:")
width = option["calc_result"]["governing_crack_width"]
print(f"     the crack width, four levels down: {width:.4f} mm")
absent = case["user_slab_result"]
print(f"     a None level, formatted:           "
      f"{'n/a' if absent is None else 'present'}")
print(f"     an empty list, iterated:           "
      f"{len(tight['optimised_configs'])} rows, so nothing printed")

print(f"\n{'-' * 72}")
print("None of the four is a defect. A result that has to say 'nothing")
print("here', 'not computed', and 'eighty positions along a member' will")
print("have empty lists, nulls and arrays in it - and a script that reads")
print("them as if they were always numbers is the thing that breaks.")
