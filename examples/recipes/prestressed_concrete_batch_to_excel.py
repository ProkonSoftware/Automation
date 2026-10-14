# ---
# Example:  Prestressed concrete — a batch of design variants to Excel
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes — 2026-09-02 — the S1 row matches the desktop-pinned C02 parity; exact on prokon-automation.exe
#           values (ULS 310.20 kNm, tendon force 1242.4 kN, crack 0.4138 mm); the
#           other rows measured against the built surface; spreadsheet written and
#           re-read with openpyxl
# ---
# Run a family of post-tensioned slab variants in one go and hand the
# comparison to whoever needs it as a spreadsheet. What would be four
# desktop sessions - retyping grids, visiting every result tab - is one
# script run, with every number coming from the same engine.
#
# The base model is the desktop Captain program's own two-span example
# (see the quick-start). Uses pandas + openpyxl, both bundled with
# Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

# ------------------------------------------------------------ base model
BASE = dict(
    design_code="BS8110 - 1997",
    fcu=19.2, fy=450.0, fyv=250.0, fci=14.4,
    ec=26e6, est=206e6, density=24.0,
    top_cover=25.0, bottom_cover=25.0,
    attached_torsional_members=True, edge_beam=True,
    redistribution_pct=10.0,
    tendon_properties=[
        {"no": 1, "bond": "Unbonded", "strength": 260.7, "max_stress_pct": 80,
         "dia": 18, "area": 140, "k": 0.0015, "u": 0.05, "pullin": 5,
         "relax": 2, "est": 195e6, "min_harp_radius": 1.0},
    ],
    span_segments=[
        {"span": 1, "length": 8.0, "sec_left": "sec1"},
        {"span": 2, "length": 7.5, "sec_left": "sec1"},
    ],
    supports=[
        {"no": 1, "d_below": 300, "b_below": 300, "h_below": 3.0, "code_below": "F",
                  "d_above": 300, "b_above": 300, "h_above": 3.0, "code_above": "F"},
        {"no": 2, "d_below": 300, "h_below": 3.0, "code_below": "F"},
        {"no": 3, "d_below": 300, "b_below": 300, "h_below": 3.0, "code_below": "F",
                  "d_above": 300, "b_above": 300, "h_above": 3.0, "code_above": "F"},
    ],
    additional_rebar=[
        {"span": 1, "pos": "T", "bars": "8Y16", "left_end": "Hook",
         "right_end": "Bend", "x": 5.0, "length": 6.0},
        {"span": 1, "pos": "B", "bars": "8Y16", "left_end": "Hook", "length": 8.0},
        {"span": 2, "pos": "B", "bars": "8Y16", "right_end": "Bend", "length": 7.0},
    ],
    punching_columns=[
        {"no": 1, "slope_y": 0.05, "cable_type": 1,
         "nc_x": [4, 5, 6, 7], "nc_y": [1, 1, 2, 2],
         "ast_x": [402, 402, 603, 804], "ast_y": [565, 565, 565, 565]},
        {"no": 2, "slope_y": 0.06, "cable_type": 1,
         "nc_x": [5, 6, 7, 8], "nc_y": [1, 1, 2, 2],
         "ast_x": [942, 942, 942, 942], "ast_y": [804, 804, 804, 804]},
        {"no": 3, "slope_y": 0.05, "cable_type": 1,
         "nc_x": [4, 5, 6, 7], "nc_y": [1, 1, 2, 2],
         "ast_x": [402, 402, 603, 804], "ast_y": [565, 565, 565, 565]},
    ],
)

# The desktop example's explicit cable layout (generated at 60 % balance)
CABLES_60 = [
    {"n": 4, "prop": 1, "x_live": 0.0, "x_dead": 15.5,
     "spans": [
         {"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125, "b2": 34, "b3": 34},
         {"span": 2, "lo": 0.4, "ro": 0.0, "b1": 34, "b2": 34, "b3": 125},
     ]},
    {"n": 3, "prop": 1, "x_live": 15.5, "x_dead": 0.0,
     "spans": [
         {"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125, "b2": 34, "b3": 34},
         {"span": 2, "lo": 0.38, "ro": 0.0, "b1": 34, "b2": 34, "b3": 125},
     ]},
]


def loads(live):
    return [
        {"case": "D", "span": 1, "wl": 6},
        {"span": 2, "wl": 6, "p": 10, "p_pos": 2, "m": 10, "m_pos": 4},
        {"case": "L", "span": 1, "wl": live},
        {"span": 2, "wl": live},
    ]


def section(depth):
    return [{"name": "sec1", "bw": 5000, "d": depth}]


# --------------------------------------------------------- the variants
# S1 is the desktop example itself - its row doubles as the anchor
# against the desktop-verified parity values. The others vary one thing
# each: slab depth, live load, and the cable route.
variants = [
    ("S1", "desktop example (250 slab, live 15)",
     dict(BASE, sections=section(250), loads=loads(15), cable_sets=CABLES_60)),
    ("S2", "300 slab, live 15",
     dict(BASE, sections=section(300), loads=loads(15), cable_sets=CABLES_60)),
    ("S3", "250 slab, live 25",
     dict(BASE, sections=section(250), loads=loads(25), cable_sets=CABLES_60)),
    ("S4", "250 slab, live 15, generated cables 90 %",
     dict(BASE, sections=section(250), loads=loads(15),
          balanced_dead_load_pct=90.0)),
]

rows = []
for name, description, model in variants:
    r = prokon.v5.prestressed_concrete.analyse(**model)["result"]

    # Worst punching perimeter over every checked column: highest
    # Veff/Vcap, and the total link area the engine requires. 'failed'
    # on a perimeter means the concrete alone is not enough - the
    # engine then reports the links to fix it in 'asv'.
    worst = max((p["veff"] / p["vcap"]
                 for col in r["punching"] for p in col["perimeters"]
                 if p["vcap"] and p["veff"] is not None), default=None)
    links = sum(p["asv"] for col in r["punching"] for p in col["perimeters"])

    rows.append({
        "variant": name,
        "description": description,
        "ULS M+ [kNm]": round(max(r["uls"]["mpu"]), 1),
        "ULS M- [kNm]": round(min(r["uls"]["mnu"]), 1),
        "SLS comp [MPa]": round(max(r["sls"]["svsma"]), 2),
        "SLS tens [MPa]": round(min(r["sls"]["svsmi"]), 2),
        "defl [mm]": round(max((v for v in r["deflections"]["ditot"]
                                if v is not None), key=abs), 1),
        "crack [mm]": round(max(r["crack_widths"]["cwt"]
                                + r["crack_widths"]["cwb"]), 3),
        "punch worst Veff/Vcap": round(worst, 2),
        "punch links [mm2]": round(links),
        "long-term loss [%]": round((1 - r["cables"]["lossf"]) * 100, 2),
        "cable [kg]": round(r["quantities"]["cable_mass"], 1),
        "rebar [kg]": round(r["quantities"]["main_rebar_mass"], 1),
    })

# The S1 anchor: these two values are pinned against the desktop's own
# printed output in the C02 parity suite. If they drift, stop.
assert abs(rows[0]["ULS M+ [kNm]"] - 310.2) < 0.05
assert abs(rows[0]["crack [mm]"] - 0.414) < 0.001

table = pd.DataFrame(rows)
print(table.to_string(index=False))

out = Path("pt_slab_variants.xlsx")
table.to_excel(out, index=False, sheet_name="PT slab variants")
print(f"\nWritten: {out.resolve()}")

# Read it straight back - proof the spreadsheet holds what we printed.
check = pd.read_excel(out)
assert len(check) == len(rows)
print(f"Re-read OK: {len(check)} variants, "
      f"S3 punching worst ratio {check.at[2, 'punch worst Veff/Vcap']}")

# What the table shows (measured):
#  - S1, the desktop example: ULS 310.2 kNm, 0.414 mm crack, punching
#    worst ratio 1.38 (columns 1 and 3 each need 793 mm2 of links -
#    the same 793.01 the desktop prints).
#  - S2, 50 mm deeper: stresses drop by a quarter, the crack halves,
#    and the punching links all but vanish (ratio 1.00, 1111 mm2).
#  - S3, live load 25: worst punching ratio 1.74, links demand 6175 mm2
#    - and column 2's perimeter 1 (748 kN vs 705.9 kN capacity) goes
#    over, a perimeter the concrete carried at live 15. Caught in the
#    batch, not on site.
#  - S4, generated cables at 90 % balance: a crack-free slab for about
#    110 kg more cable steel.
