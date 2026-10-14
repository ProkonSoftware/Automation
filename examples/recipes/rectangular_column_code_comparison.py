# ---
# Example:  Rectangular column — the same column through twelve design codes
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes — 2026-09-02 — six of the twelve rows match values pinned against the desktop in the C11 test suite; exact on prokon-automation.exe
# ---
# One column, one load set, twelve design codes, one run. On the desktop
# this is twelve sessions of retyping; here it is a loop and a table.
#
# It is a real engineering question, not a party trick: the same 400 x 400
# column under the same loads needs 3143 mm2 of steel to NZ 3101 - 2006
# and 5836 mm2 to IS:456 - 2000 — 86 % more. If you work across
# jurisdictions, or are checking someone else's design to a code you do
# not use daily, this is the table you want in front of you.
#
# Uses pandas, bundled with Prokon's Python runtime.

import pandas as pd

import prokon.v5

# The column. Fixed for every code, so the only variable is the code.
COLUMN = dict(
    h=400.0, b=400.0,             # mm
    dc_x=40.0, dc_y=40.0,         # mm to the bar centroids
    fcu=30.0, fy=450.0,           # MPa — read as fcu / fck / f'c per code
    lex=4000.0, ley=4000.0,       # mm, effective lengths
    bracing_x="Braced", bracing_y="Braced",
    betad=0.6,
    # deltas MUST be supplied for the ACI, CSA, AS3600 and AS5100 codes:
    # they refuse 0, and an omitted deltas IS 0. It is inert on the rest,
    # so one value serves the whole table rather than a special case.
    deltas=1.0,
    bar_dia=25.0,                 # also price it in Y25 bars, per code
    load_cases=[
        {"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
        {"n": 2000, "m2x": 125, "m1x":  75, "m2y":  90, "m1y": 55},
    ],
)

CODES = [
    "SABS 0100 - 2000",
    "BS8110 - 1997",
    "CP65 - 1999",
    "Eurocode 2 - 2004",
    "Eurocode 2 - 2023",
    "ACI 318 - 2019",
    "CSA-A23.3:2019",
    "AS3600 - 2018",
    "IS:456 - 2000",
    "NZ 3101 - 2006",
    "HK Concrete - 2020",
    "SP 63.13330.2018",
]

MAX_STEEL_PERCENT = 4.0    # your acceptance policy, applied to every code

rows = []
for code in CODES:
    try:
        result = prokon.v5.rectangular_column.analyse(design_code=code, **COLUMN)["result"]
    except prokon.v5.ProkonError as error:
        # A code the engine cannot design to would land here as
        # category "no_solution". Recorded rather than aborting the table.
        print(f"  {code}: {error.category} - {error.message}")
        continue

    if not result["options"]:
        reason = result["sweep_errors"][0] if result["sweep_errors"] else "no reason given"
        print(f"  {code}: no arrangement - {reason}")
        continue

    best = result["options"][0]
    first_case = best["load_case_results"][0]

    rows.append({
        "design code": code,
        "Ast [mm2]": round(best["ast"], 1),
        "steel %": round(best["perc"], 3),
        "within limit": best["perc"] <= MAX_STEEL_PERCENT,
        "cheapest bars": best["bar_description"],
        "in Y25": result["preferred"]["bar_description"],
        # LC1's design moment about X-X: applied 250 kNm, plus whatever
        # minimum-eccentricity / slenderness the code itself adds.
        "LC1 Mxe [kNm]": round(first_case["mxe"], 1),
        # Biaxial utilisation — only seven of the 23 codes publish it,
        # and where they do it sits just under 1.0 by construction (the
        # engine sized the steel to it). None on the other sixteen, so
        # it is rendered as text: "not published" is a different fact
        # from "computed as zero", and a numeric column would blur them.
        "LC1 unity": ("not published" if first_case["unity"] is None
                      else f"{first_case['unity']:.4f}"),
    })

table = pd.DataFrame(rows).sort_values("Ast [mm2]").reset_index(drop=True)
print(table.to_string(index=False))

lightest = table.iloc[0]
heaviest = table.iloc[-1]
spread = heaviest["Ast [mm2]"] / lightest["Ast [mm2]"] - 1.0

print(f"\nLightest: {lightest['design code']} at {lightest['Ast [mm2]']:.0f} mm2")
print(f"Heaviest: {heaviest['design code']} at {heaviest['Ast [mm2]']:.0f} mm2")
print(f"Spread across the twelve codes: {100 * spread:.0f} %")

# Six of these rows are pinned against the desktop program in the C11
# parity suite, so the table is anchored rather than merely consistent:
#   SABS 0100 - 2000    4521.0    (desktop 4521)
#   BS8110 - 1997       4521.0    (desktop 4521)
#   Eurocode 2 - 2004   4385.4    (desktop 4385)
#   ACI 318 - 2019      3246.3    (desktop 3246)
#   AS3600 - 2018       4323.9    (desktop 4324)
#   IS:456 - 2000       5835.6    (desktop 5836)
# SABS 0100 - 2000 and BS8110 - 1997 agreeing exactly is correct on THIS
# column, not a bug: the two code paths are the same expression
# rearranged and they coincide whenever the X and Y covers are equal.
