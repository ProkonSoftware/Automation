# ---
# Example:  One slab panel, twenty-nine design codes
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - the BS8110 anchor reproduces the desktop's own calcsheet for its Default Example (689 / 349 / 1106 / 566); every code cell and both annex groups measured on prokon-automation.exe
# ---
# C04 offers twenty-nine design codes. Running one panel through all of them
# takes about half a minute and answers three questions that matter on any
# international job:
#
#   1. how much does the CODE change the steel?
#   2. which codes DO NOT DESIGN AT ALL, and how would you notice?
#   3. what does the national annex actually do?
#
# ⚠ QUESTION 2 IS NOT RHETORICAL. Four of the twenty-nine are crack-width
# codes with no flexural rules. They return SUCCESS and they return numbers,
# and the numbers are all zero - not because no steel is needed, but because
# none was calculated. The engine now says so in a WARNING, and reading that
# warning is the whole technique. It is also the point of this script: the
# answer you must not accept is the one that looks perfectly normal.

import prokon.v5

# The panel is the desktop program's own Default Example, so the BS8110 row of
# the table below can be checked against a calcsheet rather than against this
# script.
ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"
PROPPED = "FixedAgainstVerticalDisplacement"

PANEL = dict(
    lx=13.81, ly=8.21, h=250.0, dx=200.0, dy=220.0, fcu=25.0, fy=450.0,
    edge_top=ENCASTRE, edge_right=ENCASTRE, edge_bottom=ENCASTRE,
    edge_left=PROPPED,
    load_cases=[
        {"number": 1, "lf": 1.4, "udl": 2.0,
         "p": 4.0, "x": 4.19, "y": 6.45,
         "l": 4.1, "x1": 2.44, "y1": 4.05, "x2": 10.03, "y2": 6.65},
        {"lf": 1.6, "udl": 2.0,
         "p": 4.0, "x": 10.06, "y": 2.99,
         "l": 2.0, "x1": 2.59, "y1": 2.62, "x2": 9.99, "y2": 4.61},
        {"number": 2, "lf": 1.4, "udl": 1.0, "p": 12.0, "x": 3.28, "y": 6.6},
    ],
    envelope="1,2",
)

FACES = ("x_top", "x_bot", "y_top", "y_bot")

CODES = prokon.v5.rectangular_slab.DESIGN_CODE_VALUES

print("ONE SLAB PANEL, TWENTY-NINE DESIGN CODES")
print(f"  {PANEL['lx']} x {PANEL['ly']} m, {PANEL['h']:.0f} mm thick, "
      f"dx {PANEL['dx']:.0f} / dy {PANEL['dy']:.0f}, "
      f"fcu {PANEL['fcu']:.0f}, fy {PANEL['fy']:.0f}")
print("  the desktop program's Default Example, loads and all")

# ── The anchor ──────────────────────────────────────────────────────────
# What the desktop printed on its calcsheet for this panel, to the digit it
# printed. The engine carries more precision; this is the published answer.
CALCSHEET = {"x_top": 689, "x_bot": 349, "y_top": 1106, "y_bot": 566}

anchor = prokon.v5.rectangular_slab.analyse(
    design_code="BS8110 - 1997", **PANEL)["result"]

print("\n  anchor: BS8110 - 1997, against the desktop's own calcsheet")
for face in FACES:
    got = anchor["ast"][face]
    print(f"    {face:<6} {got:10.4f}   calcsheet {CALCSHEET[face]:>5}"
          f"   {'agrees' if round(got) == CALCSHEET[face] else 'DIFFERS'}")

# ── 1 and 2 together: the table, with the no-design detector ───────────
#
# HOW TO DETECT A CODE THAT DOES NOT DESIGN. Read envelope["warnings"].
#
# ⚠ AND READ IT OFF THE ENVELOPE, NOT FROM PYTHON'S WARNING MACHINERY. This
# package also re-emits each warning through `warnings.warn`, and you will see
# four of them scroll past above this table - one per crack-width code, because
# each message names a different code and Python treats them as different
# warnings.
#
# That is the flattering case. MEASURED: three calls with the SAME code publish
# the warning on the envelope all three times, and Python surfaces it ONCE - the
# default once-per-location rule. Sweep one crack-width code over twenty panels
# and nineteen silent wrong answers go by. A warning filter can also switch the
# whole channel off. The list on the envelope is complete on every single call
# and cannot be filtered, which is why the loop below branches on it.
print("\n1. THE TABLE   (mm2/m; 'NO DESIGN' means the code has no flexural rules)")
print(f"   {'code':<24} {'x_top':>9} {'x_bot':>9} {'y_top':>9} {'y_bot':>9}"
      f"  warning?")

designed = {}
no_design = []

for code in CODES:
    try:
        envelope = prokon.v5.rectangular_slab.analyse(design_code=code, **PANEL)
    except prokon.v5.ProkonError as refusal:
        print(f"   {code:<24} {refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:44]}")
        continue

    result = envelope["result"]
    warnings_published = envelope["warnings"]

    if warnings_published:
        no_design.append(code)
        print(f"   {code:<24} " + "".join(f"{result['ast'][f]:>9.0f}" for f in FACES)
              + "  <-- WARNED: computes no reinforcement")
        continue

    designed[code] = result
    print(f"   {code:<24} " + "".join(f"{result['ast'][f]:>9.0f}" for f in FACES))

print(f"\n   {len(designed)} codes designed, {len(no_design)} did not.")

if no_design:
    print(f"   the ones that do not: {', '.join(no_design)}")
    print("   -> these are CRACK-WIDTH codes. They belong in a crack_width_code")
    print("      input (C01, C14 and C15 all have one), not in design_code.")
    print("      C04 has no such input, so on this engine they are simply the")
    print("      wrong choice - and every area they return is zero.")
    print()
    print("   NOTE WHAT IS *NOT* ZERO. The MOMENTS are still computed and")
    print("      still right: the panel was solved, only the reinforcement was")
    print("      never designed. A script reading moment_max alone would see")
    print("      nothing wrong at all.")

# ── The spread, which is what the table is for ─────────────────────────
if designed:
    print(f"\n2. THE SPREAD   bottom steel in x, across the "
          f"{len(designed)} designing codes")

    ranked = sorted(designed.items(), key=lambda item: item[1]["ast"]["x_bot"])
    lightest_code, lightest = ranked[0]
    heaviest_code, heaviest = ranked[-1]

    print(f"   lightest {lightest_code:<24} {lightest['ast']['x_bot']:>9.1f} mm2/m")
    print(f"   heaviest {heaviest_code:<24} {heaviest['ast']['x_bot']:>9.1f} mm2/m")
    print(f"   ratio    {heaviest['ast']['x_bot'] / lightest['ast']['x_bot']:.3f}x")

    reference = designed.get("BS8110 - 1997")
    if reference:
        print(f"   BS8110   {reference['ast']['x_bot']:>9.1f} mm2/m (the anchor above)")

    print("   -> the same panel, the same loads, and the answer moves by that")
    print("      ratio. On an export job the code is not a formality.")

# ── 3. What the national annex actually does ───────────────────────────
# Three annexes are offered for the Eurocode family. Measure what they do
# rather than trusting a note that says they are the same.
print("\n3. THE NATIONAL ANNEX   Eurocode 2 - 2004, three annexes")
print(f"   {'annex':<16} {'x_top':>10} {'x_bot':>10} {'y_top':>10} {'y_bot':>10}")

annex_results = {}
for annex in (None,) + prokon.v5.rectangular_slab.NATIONAL_ANNEX_VALUES:
    extra = {} if annex is None else {"national_annex": annex}
    try:
        result = prokon.v5.rectangular_slab.analyse(
            design_code="Eurocode 2 - 2004", **PANEL, **extra)["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"   {str(annex):<16} {refusal.category}/{refusal.code}")
        continue

    annex_results[annex] = tuple(result["ast"][face] for face in FACES)
    print(f"   {'(omitted)' if annex is None else annex:<16}"
          + "".join(f"{value:>10.2f}" for value in annex_results[annex]))

if annex_results:
    groups = {}
    for annex, values in annex_results.items():
        groups.setdefault(values, []).append(
            "(omitted)" if annex is None else annex)

    print(f"   -> {len(groups)} DISTINCT answer(s) from {len(annex_results)} settings:")
    for values, names in groups.items():
        print(f"      {', '.join(names)}  ->  x_bot {values[1]:.4f}")

    if len(groups) < len(annex_results):
        print("      Some of these are bit-identical, which is worth KNOWING:")
        print("      an annex that changes nothing today may change something")
        print("      in a later engine, so name the one you mean.")

# ── 4. And the annex on a code that has none ───────────────────────────
# Supplying an annex to a code that accepts none is REFUSED, not ignored.
# That is the behaviour you want, and it is worth seeing once.
print("\n4. AN ANNEX WHERE THERE IS NONE")
try:
    prokon.v5.rectangular_slab.analyse(
        design_code="BS8110 - 1997", national_annex="UnitedKingdom", **PANEL)
    print("   accepted - which would mean the annex was silently ignored")
except prokon.v5.ProkonError as refusal:
    print(f"   {refusal.category} / {refusal.code}")
    print(f"   {refusal.message.encode('ascii', 'replace').decode()}")
    print("   -> refused rather than ignored. An input that is quietly dropped")
    print("      is the worst kind, because the result looks fine.")
