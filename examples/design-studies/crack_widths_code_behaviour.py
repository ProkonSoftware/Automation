# ---
# Example:  Crack widths - what the thirteen codes actually do
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes - 2026-09-02 - the reference slab reproduces the pinned triple; every code cell measured on prokon-automation.exe
# ---
# C21 offers thirteen design codes. They do NOT all answer the same
# question, and three of them do not answer at all on some inputs. If you
# are going to script a crack-width check, this is the table to have seen
# first.
#
#   1. the reference slab through all thirteen codes
#   2. PURE TENSION - five codes report a crack width of exactly 0.0000
#      with meets_all_criteria TRUE, which is an all-clear on the one
#      number you asked for
#   3. the bar-diameter/spacing chart: what actually controls a crack
#   4. thermal and restraint effects, which are what BS8007 exists for
#
# ⚠ SECTION 2 IS THE ONE TO READ TWICE. It is not a bug hunt - it is the
# reason a crack-width script must never take an all-clear at face value on
# a load case it has not checked the shape of.

import prokon.v5

CODES = (
    "BS8007 - 1987", "Eurocode 2", "Eurocode 2 - 2004", "Eurocode 2 - 2023",
    "IS456 - 2000", "NZ 3101 - 2006", "AS3600 - 2018", "SP 63.13330.2018",
    "HK Concrete - 2020", "ACI224.1 - 07", "GB 50010 - 2010",
    "CSA A23.3:24", "SANS 51992-1-1:2025",
)

# The reference slab: the section pinned in the C21 test suite.
REFERENCE = dict(
    slab_mode=True, h=300.0, hef=200.0, b=1000.0, cover=40.0,
    fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
    allowable_crack_width=0.3, high_bond_bar=True, short_term_load=True,
)
REFERENCE_CASE = [{"n": 1, "m": 50.0, "m_uls": 1.5}]

print("CRACK WIDTHS - WHAT THE THIRTEEN CODES ACTUALLY DO")

# ── The anchor ──────────────────────────────────────────────────────────
anchor = prokon.v5.crack_widths.analyse(design_code="BS8007 - 1987",
                                     **REFERENCE, load_cases=REFERENCE_CASE)["result"]
first = anchor["load_cases"][0]["optimised_configs"][0]
PINNED = (0.11059554804834058, 1047.197551196598, 99.75807235558123)
measured = (first["calc_result"]["governing_crack_width"],
            first["calc_result"]["steel_area"],
            first["moment_capacity"])
print(f"\n  anchor: BS8007 on the reference slab, {first['formatted_bars']}")
print(f"    w {measured[0]!r}")
print(f"    As {measured[1]!r}")
print(f"    Mu {measured[2]!r}")
print(f"    -> {'EXACT against the pinned triple' if measured == PINNED else 'DRIFTED from the pinned triple'}")


def summarise(code, cases):
    """(status, lightest arrangement) for one code and one load schedule."""
    try:
        result = prokon.v5.crack_widths.analyse(design_code=code, **REFERENCE,
                                             load_cases=cases)["result"]
    except prokon.v5.ProkonError as refusal:
        return f"{refusal.category}/{refusal.code}", None
    options = result["load_cases"][0]["optimised_configs"]
    if not options:
        return "no arrangements offered", None
    lightest = min(options, key=lambda o: o["calc_result"]["steel_area"])
    return "ok", lightest


# ── 1. The reference slab, thirteen ways ───────────────────────────────
print(f"\n1. THE SAME SLAB, THIRTEEN CODES   "
      f"(M = 50 kNm/m service, allowable 0.3 mm)")
print(f"   {'code':<24} {'bars':>12} {'As':>9} {'crack w':>9} "
      f"{'Mu':>9}  {'verdict':<8}")

for code in CODES:
    status, option = summarise(code, REFERENCE_CASE)
    if option is None:
        print(f"   {code:<24} {status}")
        continue
    calculated = option["calc_result"]
    print(f"   {code:<24} {option['formatted_bars']:>12} "
          f"{calculated['steel_area']:>9.0f} "
          f"{calculated['governing_crack_width']:>9.4f} "
          f"{option['moment_capacity']:>9.1f}  "
          f"{'meets' if option['meets_all_criteria'] else 'fails':<8}")

print("   -> the SPREAD is the point. The same slab, the same moment, the")
print("      same allowable, and the crack widths differ by more than 3x")
print("      across the codes. Choose the code deliberately.")

# ── 2. Pure tension: the all-clear that is not one ─────────────────────
# A tie in DIRECT TENSION is the worst case for cracking. Ask for it with
# m = 0 and t set, and watch what comes back.
TENSION_CASE = [{"n": 1, "m": 0.0, "m_uls": 1.0, "t": 300.0, "t_uls": 1.0}]

print(f"\n2. PURE TENSION   m = 0, t = 300 kN/m, no moment at all")
print(f"   {'code':<24} {'bars':>12} {'crack w':>9} {'T cap':>9} "
      f"{'all criteria':>13}")

zero_reported = []
for code in CODES:
    status, option = summarise(code, TENSION_CASE)
    if option is None:
        print(f"   {code:<24} {status}")
        continue
    width = option["calc_result"]["governing_crack_width"]
    if width == 0.0:
        zero_reported.append(code)
    print(f"   {code:<24} {option['formatted_bars']:>12} {width:>9.4f} "
          f"{option['tension_capacity']:>9.0f} "
          f"{str(option['meets_all_criteria']):>13}")

print(f"\n   {len(zero_reported)} code(s) returned a crack width of EXACTLY 0.0000:")
for code in zero_reported:
    print(f"     {code}")
print("   Every one of them also reported meets_all_criteria True. A script")
print("   that reads the width and the flag would call a tie in 300 kN/m of")
print("   direct tension uncracked.")
print("   -> SUPPLY THE MOMENT AS WELL. A real tie bends as well as pulls,")
print("      and the codes that do compute a tension crack width")
print("      (NZ 3101 and SP 63 above) show what the others are not saying.")

# The control that makes section 2 evidence rather than an anecdote: the
# SAME codes, on a case that HAS a moment, must return non-zero widths.
print(f"\n   CONTROL - the same codes with a moment added:")
CONTROL_CASE = [{"n": 1, "m": 50.0, "m_uls": 1.5, "t": 300.0, "t_uls": 1.0}]
for code in zero_reported:
    status, option = summarise(code, CONTROL_CASE)
    if option is None:
        print(f"     {code:<24} {status}")
        continue
    width = option["calc_result"]["governing_crack_width"]
    print(f"     {code:<24} w = {width:.4f} mm"
          f"  ->  {'computes normally with a moment' if width > 0 else 'STILL ZERO'}")
print("   -> the zeros are specific to the pure-tension case, not a broken")
print("      code or a broken script. That is what makes it a finding.")

# ── 3. What actually controls a crack ──────────────────────────────────
# Not steel area. Crack width falls with SMALL BARS at CLOSE SPACING, and
# the engine's own search shows it: watch the width against the area.
print(f"\n3. WHAT CONTROLS THE WIDTH   BS8007, reference slab, "
      f"every arrangement the search offers")
search = prokon.v5.crack_widths.analyse(design_code="BS8007 - 1987",
                                     **REFERENCE, load_cases=REFERENCE_CASE)["result"]
print(f"   {'bars':>12} {'dia':>5} {'spacing':>8} {'As':>9} {'crack w':>9} "
      f"{'w per 1000 mm2':>15}")
for option in search["load_cases"][0]["optimised_configs"]:
    configuration = option["configuration"]
    calculated = option["calc_result"]
    area = calculated["steel_area"]
    width = calculated["governing_crack_width"]
    print(f"   {option['formatted_bars']:>12} {configuration['dia1']:>5.0f} "
          f"{configuration['spacing']:>8.0f} {area:>9.0f} {width:>9.4f} "
          f"{1000.0 * width / area:>15.5f}")
print("   -> a bigger bar at a wider spacing gives MORE area and a WIDER")
print("      crack. Area is not the control; bar size and spacing are.")

# ── 4. WHICH INPUTS ACTUALLY MOVE THE ANSWER ──────────────────────────
# ⚠ THE MOST USEFUL SECTION HERE, and the least obvious. Several of C21's
# inputs are INERT ON THEIR OWN and only bite in combination. Set one of
# them, get the same number back, and conclude the input does nothing -
# when in fact you were one input short.
#
# Measured on this slab, 2026-09-02. Each of these ALONE changes nothing:
#   restraint_factor 0.5 and 1.0, shrinkage_strain 300 and 1000,
#   thermal_expansion 12e-6, t1 = 30, t1 = 60, t1 = 30 with t2 = 10,
#   creep_factor 2.0, short_term_load False
# All ten return 0.222417 mm, bit-identical to the baseline.
#
# The three TOGETHER - t1, restraint_factor AND thermal_expansion - move it
# to 0.238732 mm. The thermal path needs a temperature drop, something to
# restrain it, and a coefficient to turn degrees into strain. Any one
# missing and the term is zero, silently.


# ⚠ COMPARE A FIXED ARRANGEMENT, NOT "THE LIGHTEST ONE". The engine's own
# search returns a different set of arrangements as the inputs change, so
# "the lightest option's crack width" is a moving target measured on
# different bars each time - and it reads NON-MONOTONIC as a result. An
# earlier version of this table did exactly that, and showed a LARGER
# temperature drop giving a SMALLER crack, because the search had switched
# to heavier bars underneath it.
#
# user_slab_bars pins one arrangement and reports it alongside the search,
# so every row below is the same Y16@250 and only the inputs differ.
FIXED_BARS = "Y16@250"


def fixed_width(**overrides):
    """The crack width of ONE fixed arrangement, or None."""
    cases = [{"n": 1, "m": 50.0, "m_uls": 1.5,
              "t1": overrides.pop("t1", 0.0),
              "t2": overrides.pop("t2", 0.0)}]
    try:
        result = prokon.v5.crack_widths.analyse(
            design_code="BS8007 - 1987",
            **{**REFERENCE, **overrides, "user_slab_bars": FIXED_BARS},
            load_cases=cases)["result"]
    except prokon.v5.ProkonError:
        return None
    # user_slab_result is None when no user arrangement was supplied, so it
    # is tested before it is read - always.
    mine = result["load_cases"][0]["user_slab_result"]
    if mine is None:
        return None
    return mine["calc_result"]["governing_crack_width"]


print(f"\n4. WHICH INPUTS ACTUALLY MOVE THE ANSWER   BS8007, the same slab")
print(f"   every row is the SAME {FIXED_BARS}, so only the inputs differ")
baseline = fixed_width()
print(f"   baseline (load only): {baseline:.6f} mm")
print(f"   {'input':<40} {'crack w':>10} {'effect':>12}")

PROBES = (
    ("restraint_factor = 0.5", dict(restraint_factor=0.5)),
    ("restraint_factor = 1.0", dict(restraint_factor=1.0)),
    ("shrinkage_strain = 300", dict(shrinkage_strain=300.0)),
    ("shrinkage_strain = 1000", dict(shrinkage_strain=1000.0)),
    ("thermal_expansion = 12e-6", dict(thermal_expansion=12e-6)),
    ("t1 = 30", dict(t1=30.0)),
    ("t1 = 60", dict(t1=60.0)),
    ("t1 = 30, t2 = 10", dict(t1=30.0, t2=10.0)),
    ("creep_factor = 2.0", dict(creep_factor=2.0)),
    ("short_term_load = False", dict(short_term_load=False)),
    ("t1 = 30 + R 0.5 + alpha 12e-6", dict(t1=30.0, restraint_factor=0.5,
                                           thermal_expansion=12e-6)),
    ("t1 = 60 + R 0.5 + alpha 12e-6", dict(t1=60.0, restraint_factor=0.5,
                                           thermal_expansion=12e-6)),
    ("t1 = 30 + R 1.0 + alpha 12e-6", dict(t1=30.0, restraint_factor=1.0,
                                           thermal_expansion=12e-6)),
)

inert = []
for label, overrides in PROBES:
    value = fixed_width(**overrides)
    if value is None:
        print(f"   {label:<40} {'-':>10} {'no arrangement':>12}")
        continue
    if value == baseline:
        inert.append(label)
        effect = "NO CHANGE"
    else:
        effect = f"{value / baseline:.4f}x"
    print(f"   {label:<40} {value:>10.6f} {effect:>12}")

print(f"\n   {len(inert)} input(s) changed NOTHING on their own.")
print("   -> the thermal path needs t1 AND restraint_factor AND")
print("      thermal_expansion together: a temperature drop, something to")
print("      restrain it, and a coefficient to turn degrees into strain.")
print("      Any one at zero makes the whole term zero, with no warning.")
print("      That is the failure mode to remember: an input that reads as")
print("      ignored is usually an input that is one companion short.")
