# ---
# Example:  Pile cap — a schedule of caps to Excel
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes — 2026-09-02 — PC1 matches the values pinned in the C16 test suite; the rest measured; exact on prokon-automation.exe
# ---
# Design a whole pile-cap schedule in one run and hand the results over as
# a spreadsheet. An afternoon of desktop sessions becomes seconds of
# script time — with every number coming from the engine the desktop uses,
# and every cap checked the same way.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.
#
# Reminder: lengths are in METRES on this feature.

from pathlib import Path

import pandas as pd

import prokon.v5

DESIGN_CODE = "CSA-A23.3:2019"

# The schedule: one row per cap. In practice you would read this from
# your own spreadsheet with pd.read_excel(...).
schedule = pd.DataFrame([
    # ref    col   piles  dia  spacing  thick  overhang  fc     fy
    ("PC1",  0.50,   4,   0.60,   1.8,   1.2,    0.30,   30.0, 400.0),
    ("PC2",  0.60,   3,   0.60,   1.5,   1.3,    0.30,   30.0, 450.0),
    ("PC3",  0.70,   4,   0.75,   2.1,   1.4,    0.35,   35.0, 450.0),
    ("PC4",  0.45,   4,   0.60,   1.8,   1.2,    0.30,   30.0, 450.0),
    ("PC5",  0.80,   5,   0.75,   2.1,   1.5,    0.35,   35.0, 450.0),
], columns=["ref", "col", "piles", "dia", "spacing", "thick", "overhang", "fc", "fy"])

# The load schedule for each cap. Two rows sharing one combination: the
# empty name continues the previous row, so dead and live are summed with
# their own factors into a single ULS case.
LOADS = {
    "PC1": [{"name": "ULS", "load_factor": 1.0, "p": 4000.0}],
    "PC2": [{"name": "ULS", "load_factor": 1.2, "p": 2500.0},
            {"name": "",    "load_factor": 1.5, "p":  700.0}],
    "PC3": [{"name": "ULS", "load_factor": 1.2, "p": 4500.0, "mx": 200.0},
            {"name": "",    "load_factor": 1.5, "p": 1500.0, "mx":  80.0}],
    "PC4": [{"name": "ULS", "load_factor": 1.2, "p": 3500.0},
            {"name": "",    "load_factor": 1.5, "p": 1200.0}],
    "PC5": [{"name": "ULS", "load_factor": 1.2, "p": 7000.0, "my": 300.0},
            {"name": "",    "load_factor": 1.5, "p": 2000.0, "my": 120.0}],
}

results = []
for cap in schedule.itertuples(index=False):
    r = prokon.v5.pile_cap.analyse(
        design_code=DESIGN_CODE,
        column_dim_x=cap.col, column_dim_y=cap.col,
        no_of_piles=int(cap.piles), pile_dia=cap.dia, pile_spacing=cap.spacing,
        pile_tolerance=0.05,
        cap_thickness=cap.thick, cap_overhang=cap.overhang, bottom_rebar_depth=0.1,
        fc=cap.fc, fy=cap.fy, load_cases=LOADS[cap.ref],
    )["result"]

    strut_sf = min(lc["sf"] for e in r["strut_results"] for lc in e["load_cases"])
    col_sf = min(lc["sf"] for lc in r["column_node"]["load_cases"])
    pile_sf = min(lc["sf"] for nd in r["pile_nodes"] for lc in nd["load_cases"])
    # Ties are the negative (tension) elements of the force grid.
    # tie_results carries real tf and as_required values as of
    # 2026-08-28; this read is the cross-check on them — see the
    # feature page.
    tie_t = max(-min(r["element_forces"][e]) for e in r["tie_element_indices"])

    results.append({
        "ref": cap.ref,
        "cap X [m]": round(r["cap_dim_x"], 3),
        "cap Y [m]": round(r["cap_dim_y"], 3),
        "max pile P [kN]": round(max(f["p"] for pile in r["pile_forces"] for f in pile), 1),
        "strut SF": round(strut_sf, 3),
        "col node SF": round(col_sf, 3),
        "pile node SF": round(pile_sf, 3),
        "max tie T [kN]": round(tie_t, 1),
        "As min [mm2/m]": round(r["tie_minim_reinforcement"]),
        "overhang req [m]": round(r["overhang_min_required"], 3),
        # C16 reports demand and capacity; the verdict is ours to make.
        # An inadequate cap is a SUCCESSFUL analysis, not a refusal.
        "verdict": "OK" if (min(strut_sf, col_sf, pile_sf) >= 1.0
                            and cap.overhang >= r["overhang_min_required"]
                            and not r["has_uplift"]) else "CHECK",
    })

table = schedule.merge(pd.DataFrame(results), on="ref")
print(table.to_string(index=False))

failing = table[table["verdict"] == "CHECK"]["ref"].tolist()
if failing:
    print(f"\nInadequate in this schedule: {', '.join(failing)}. "
          f"Each returned a normal, successful analysis - nothing refused, "
          f"nothing warned.")

out = Path("pile_cap_schedule.xlsx")
table.to_excel(out, index=False, sheet_name="Pile caps")
print(f"\nWritten: {out.resolve()}")
