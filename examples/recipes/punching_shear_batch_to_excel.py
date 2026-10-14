# ---
# Example:  Punching shear — a floor's column heads to Excel
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes — 2026-09-02 — the C1 row matches the Asv value pinned in the C23 test suite; exact on prokon-automation.exe
# ---
# Check every column head on a floor plate in one run and hand the
# results over as a spreadsheet. An afternoon of desktop sessions becomes
# seconds of script time — with every number coming from the same engine
# the desktop uses.
#
# The spreadsheet carries the two checks that actually decide a column
# head, because the result has no single pass/fail key to copy:
#
#   * face:   vu <= vcu           — no reinforcement can fix this one
#   * links:  worst Asv over the five perimeters, and where it occurs
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

DESIGN_CODE = "BS8110 - 1997"
FCU, FY, FYV = 35.0, 500.0, 500.0   # [MPa]

# The floor's column schedule. "edge_x"/"edge_y" are the distances to the
# nearest slab edge in millimetres — 10000 says "internal in this
# direction"; a small value makes it an edge or corner column, which the
# engine picks up from the geometry rather than from a flag.
#
# "as_top" is the flexural steel crossing each critical perimeter, both
# ways, in mm2. 0 means the top steel is not detailed yet: the engine
# then assumes none, which understates the concrete capacity and so
# overstates the links required. See the drop-panel recipe for turning a
# bar spacing into these areas.
schedule = pd.DataFrame([
    # name    A       B      de     edge_x   edge_y   as_top    V      Mx     My
    ("C1",  400.0, 400.0, 200.0,  10000.0, 10000.0,    0.0,  800.0,  50.0,  30.0),
    ("C2",  500.0, 500.0, 250.0,  10000.0, 10000.0, 1500.0, 1100.0,  60.0,  40.0),
    ("C3",  400.0, 300.0, 200.0,    250.0, 10000.0, 1200.0,  500.0,  30.0,   0.0),
    ("C4",  300.0, 300.0, 175.0,    200.0,   200.0, 1000.0,  300.0,  20.0,  20.0),
    ("C5",  250.0, 250.0, 120.0,  10000.0, 10000.0,  800.0, 2500.0,   0.0,   0.0),
], columns=["column", "a", "b", "de", "edge_x", "edge_y", "as_top",
            "v", "mx", "my"])

rows = []

for head in schedule.itertuples(index=False):
    steel = {f"as{axis}_{n}": head.as_top for axis in ("x", "y") for n in (1, 2, 3, 4)}

    try:
        r = prokon.v5.punching_shear.analyse(
            design_code=DESIGN_CODE,
            col_width=head.a, col_breadth=head.b, effective_depth=head.de,
            nearest_edge_x=head.edge_x, nearest_edge_y=head.edge_y,
            fcu=FCU, fy=FY, fyv=FYV,
            load_cases=[{"v": head.v, "mx": head.mx, "my": head.my}],
            **steel,
        )["result"]
    except prokon.v5.ProkonError as e:
        # A refusal is an answer a schedule needs — record it and carry on
        # rather than losing the whole run to one bad column.
        rows.append({"column": head.column, "verdict": f"REFUSED ({e.category})",
                     "note": e.message})
        continue

    critical = r["critical_load_case_index"]
    vu, vcu = r["vu"][critical], r["vcu"]

    worst = max(r["critical_perimeters"], key=lambda p: p["asv"])

    # The first bar arrangement Prokon offers for the governing perimeter.
    suggestion = r["bars"][worst["perimeter"] - 1][0]["description"]

    rows.append({
        "column": head.column,
        # corner_code says how the engine read the position: 0 internal,
        # 1 edge in X, 2 edge in Y, 3 corner.
        "position": {0: "internal", 1: "edge X", 2: "edge Y", 3: "corner"}[
            worst["corner_code"]],
        "uo [mm]": round(r["uo"]),
        "vu [MPa]": round(vu, 3),
        "vcu [MPa]": round(vcu, 3),
        "face ok": vu <= vcu,
        "worst Asv [mm2]": round(worst["asv"], 1),
        "at perimeter": worst["perimeter"] if worst["asv"] > 0 else None,
        "links": suggestion or "none required",
        "verdict": ("FACE OVERSTRESSED" if vu > vcu
                    else "links required" if worst["asv"] > 0
                    else "no shear reinforcement needed"),
        # The BS8110-family "v exceeds 2*vc" calcsheet note. Codes outside
        # that family and IS456 never set it, so an empty column here is
        # not evidence of anything on those codes.
        "note": ("v exceeds 2*vc - justify the design" if r["vc_warning"] else ""),
    })

table = schedule.merge(pd.DataFrame(rows), on="column")

print(table.to_string(index=False))

out = Path("punching_shear_column_heads.xlsx")
table.to_excel(out, index=False, sheet_name="Column heads")
print(f"\nWritten: {out.resolve()}")
