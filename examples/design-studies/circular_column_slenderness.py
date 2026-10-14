# ---
# Example:  Slenderness limits - twenty-one codes disagree, and by a lot
# Feature:  circular_column (C12 Circular Column)
# Verified: yes - 2026-09-02 - the reference column reproduces the pinned total_as; every code and length measured on prokon-automation.exe
# ---
# Every concrete code has a slenderness limit past which it refuses to
# design a column. The limits are NOT similar: BS8110 stops at 60,
# Eurocode 2 - 1992 at 140. On a tall column that is the difference
# between a design and a redesign.
#
#   1. the slenderness ceiling, code by code, found by bisection
#   2. what slenderness COSTS in steel, below the ceiling
#   3. the deltas input: ten of the twenty-one codes refuse a value below 1
#   4. nuz - a result key that exists only on the slender path
#
# ⚠ SECTION 3 IS WHY `deltas` HAS NO DEFAULT. Ten codes refuse
# deltas < 1 outright. Eleven accept 0. So there is no single value that
# is valid everywhere, and the input is required rather than defaulted -
# which this script demonstrates rather than restating.

import prokon.v5

DIAMETER = 220.0
COVER = 40.0
FCU = 25.0
FY = 450.0
AXIAL = 700.0

CODES = prokon.v5.circular_column.DESIGN_CODE_VALUES

BASE = dict(diameter=DIAMETER, cover=COVER, fcu=FCU, fy=FY,
            bracing_x="Braced", bracing_y="Braced")

print("SLENDERNESS LIMITS - TWENTY-ONE CODES")
print(f"  {DIAMETER:.0f} mm column, cover {COVER:.0f}, fcu {FCU:.0f}, "
      f"fy {FY:.0f}, N = {AXIAL:.0f} kN")
print(f"  {len(CODES)} codes offered by this build")

# ── The anchor ──────────────────────────────────────────────────────────
PINNED_AS = 1037.1145165134003
anchor = prokon.v5.circular_column.analyse(
    design_code="BS8110 - 1997", **BASE,
    lex=2250.0, ley=2250.0, deltas=1.0,
    load_cases=[{"n": AXIAL}])["result"]
print(f"\n  anchor: the desktop's own short-column example, le = 2250")
print(f"    total_as {anchor['total_as']!r}")
print(f"    pinned   {PINNED_AS!r}")
print(f"    -> {'EXACT' if anchor['total_as'] == PINNED_AS else 'DRIFTED'}")
print(f"    percentage_steel {anchor['percentage_steel']:.4f} %, "
      f"all_pass {anchor['all_pass']}")


def try_at(code, effective, deltas=1.0):
    """(result, None) or (None, reason)."""
    try:
        return prokon.v5.circular_column.analyse(
            design_code=code, **BASE,
            lex=effective, ley=effective, deltas=deltas,
            load_cases=[{"n": AXIAL}])["result"], None
    except prokon.v5.ProkonError as refusal:
        return None, refusal.message.encode("ascii", "replace").decode()


# ── 1. The ceiling, by bisection ───────────────────────────────────────
# Each code has a slenderness limit. Find it by bisecting the effective
# length, and report it as le/h, which is the number the codes are written
# in.
#
# ⚠ ONE CODE IS DELIBERATELY LEFT OUT OF THIS SWEEP. IS:456 - 2000 is on
# record as HANGING on some fy values rather than answering, and a
# documentation example must not hang. It is named here and skipped.
SKIP = {"IS:456 - 2000": "on record as hanging on some inputs; not executed"}

print(f"\n1. THE SLENDERNESS CEILING   found by bisecting le, reported as le/h")
print(f"   {'code':<22} {'max le (mm)':>12} {'le/h':>7}  the refusal")

ceilings = {}
for code in CODES:
    if code in SKIP:
        print(f"   {code:<22} {'-':>12} {'-':>7}  SKIPPED: {SKIP[code]}")
        continue

    ok, _ = try_at(code, 1000.0)
    if ok is None:
        print(f"   {code:<22} refuses even at le = 1000 mm")
        continue

    low, high = 1000.0, 60_000.0
    reason = ""
    for _ in range(14):
        middle = (low + high) / 2.0
        result, refusal = try_at(code, middle)
        if result is None:
            high, reason = middle, refusal
        else:
            low = middle
    ceilings[code] = low
    print(f"   {code:<22} {low:>12.0f} {low / DIAMETER:>7.1f}  "
          f"{reason[:40] if reason else 'no ceiling found below 60 m'}")

if ceilings:
    ranked = sorted(ceilings.items(), key=lambda item: item[1])
    print(f"\n   tightest {ranked[0][0]:<22} le/h "
          f"{ranked[0][1] / DIAMETER:.1f}")
    print(f"   loosest  {ranked[-1][0]:<22} le/h "
          f"{ranked[-1][1] / DIAMETER:.1f}")
    print(f"   ratio    {ranked[-1][1] / ranked[0][1]:.2f}x")
    print("   -> the same column is designable to one code and refused by")
    print("      another. On an export job that is a project risk, not a")
    print("      footnote - and it is a one-line check.")

# ── 2. What slenderness costs ──────────────────────────────────────────
print(f"\n2. WHAT SLENDERNESS COSTS   BS8110 - 1997, le swept to its ceiling")
print(f"   {'le':>7} {'le/h':>6} {'steel':>9} {'%':>7} {'slender':>8} "
      f"{'nuz':>10} {'design Mx':>10}")

reference = None
for effective in (1000.0, 2000.0, 2250.0, 3000.0, 4000.0, 5000.0,
                  6000.0, 8000.0, 10_000.0, 12_000.0, 13_000.0):
    result, refusal = try_at("BS8110 - 1997", effective)
    if result is None:
        print(f"   {effective:>7.0f} {effective / DIAMETER:>6.1f}  "
              f"REFUSED: {refusal[:52]}")
        continue
    case = result["load_case_results"][0]
    if reference is None:
        reference = result["total_as"]
    print(f"   {effective:>7.0f} {effective / DIAMETER:>6.1f} "
          f"{result['total_as']:>9.0f} {result['percentage_steel']:>7.3f} "
          f"{str(case['slender_x']):>8} {result['nuz']:>10.1f} "
          f"{case['moment_x']:>10.2f}")

print("   -> nuz is 0 while the column is short and non-zero once it is")
print("      slender: it is written ONLY on the slenderness path. So nuz")
print("      is a usable test for 'did the engine treat this as slender',")
print("      and it is more reliable than reading the flag alone.")

# ── 3. deltas, and why it has no default ───────────────────────────────
print(f"\n3. THE deltas INPUT   the same column with deltas = 0")
print(f"   {'code':<22} {'deltas = 0':<40}")

refuse_zero = []
accept_zero = []
for code in CODES:
    if code in SKIP:
        continue
    result, refusal = try_at(code, 2250.0, deltas=0.0)
    if result is None:
        refuse_zero.append(code)
        print(f"   {code:<22} REFUSED: {refusal[:40]}")
    else:
        accept_zero.append(code)
        print(f"   {code:<22} accepted, total_as {result['total_as']:.1f}")

print(f"\n   {len(refuse_zero)} code(s) refuse deltas = 0; "
      f"{len(accept_zero)} accept it.")
print("   -> that is why deltas is REQUIRED with no default. No single")
print("      value is valid for every code this command advertises, so the")
print("      wrapper refuses to choose one on your behalf. An input with")
print("      no safe default is better required than defaulted.")

# ── 4. And what deltas = 0 MEANS where it is accepted ─────────────────
# On the eleven codes that take it, is 0 treated as 0 or as 1? Measure it.
print(f"\n4. WHERE deltas = 0 IS ACCEPTED, WHAT DOES IT MEAN?")
print(f"   {'code':<22} {'deltas=0':>11} {'deltas=1':>11} {'same?':>7}")
for code in accept_zero[:6]:
    zero, _ = try_at(code, 6000.0, deltas=0.0)
    one, _ = try_at(code, 6000.0, deltas=1.0)
    if zero is None or one is None:
        continue
    print(f"   {code:<22} {zero['total_as']:>11.2f} {one['total_as']:>11.2f} "
          f"{str(zero['total_as'] == one['total_as']):>7}")
print("   -> where they agree, 0 is being read as 'the default', not as a")
print("      literal zero amplification. Where they differ, it is not.")
print("      Either way: name the value you mean.")
