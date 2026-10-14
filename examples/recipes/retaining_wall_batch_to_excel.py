# ---
# Example:  Retaining wall — a schedule of walls to Excel
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes — 2026-09-02 — the W1 row matches the C14 desktop-parity calcsheet; exact on prokon-automation.exe
# ---
# A site rarely has one retaining wall. Design the whole schedule in one
# run and hand the results over as a spreadsheet: minutes of desktop
# clicking becomes seconds of script time, with every number coming from
# the same engine the desktop uses.
#
# Uses pandas + openpyxl, both bundled with Prokon's Python runtime.

from pathlib import Path

import pandas as pd

import prokon.v5

# Everything the walls have in common. Each wall below overrides what it
# needs — this is just a Python dictionary, so you can build it from your
# own spreadsheet with pd.read_excel(...) instead.
COMMON = dict(
    concrete_code="BS8110 - 1997",
    fcu=25.0, fy=450.0,                 # MPa
    db=25.0, dg=18.0,                   # kN/m3
    sf_overturning=1.5, sf_sliding=1.5,
    dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9,
    mu=0.5,
    cover_wall=50.0, cover_base=50.0,
)

# The schedule. W1 is Prokon's own C14 verification wall, kept here as a
# reference row: its results are checked against the desktop calcsheet,
# so a run that reproduces them proves the whole batch is sound.
SCHEDULE = [
    dict(
        wall="W1 verification wall",
        h1=5.0, h2=0.7, h3=0.8, hw=2.8,
        b=0.55, d=2.50, c=0.40, f=0.70, xf=3.05,
        at=0.30, ab=0.40, x=0.45,
        theta=27.0, alpha=9.0, delta=20.0,
        pmax=400.0,
        seismic=True, kh=0.02, kv=0.01, seis_w_loads=True,
        allow_seep=True, toe_back_force=True,
        load_cases=[
            {"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0, "lynl": 1.0, "xlv": 2.0, "ph": 0.5},
            {"name": "Truck",   "w": 2.0, "p": 0.5, "xp": 2.0, "lynl": 2.0, "xlv": 1.0, "ph": 3.0},
            {"name": "Train",   "w": 3.0,                      "lynl": 1.0, "xlv": 2.0},
        ],
    ),
    dict(
        wall="W2 yard wall 3 m",
        h1=3.0, b=0.50, d=1.40, c=0.35, at=0.25, ab=0.30,
        theta=30.0, delta=15.0, pmax=150.0,
        load_cases=[{"name": "Yard traffic", "w": 10.0}],
    ),
    dict(
        wall="W3 road wall 4.5 m",
        h1=4.5, h2=0.5, b=0.70, d=2.00, c=0.45, at=0.30, ab=0.40,
        theta=30.0, delta=15.0, pmax=200.0,
        load_cases=[
            {"name": "Permanent", "w": 5.0},
            {"name": "Truck", "w": 10.0, "p": 120.0, "xp": 1.2},
        ],
    ),
    dict(
        wall="W4 basement 6 m",
        h1=6.0, hw=3.0, b=0.80, d=2.60, c=0.55, at=0.35, ab=0.50,
        theta=28.0, delta=14.0, pmax=250.0,
        load_cases=[{"name": "Surcharge", "w": 15.0}],
    ),
    dict(
        wall="W5 undersized 5 m",   # deliberately too small — see the verdict
        h1=5.0, b=0.40, d=1.00, c=0.35, at=0.25, ab=0.30,
        theta=30.0, delta=15.0, pmax=150.0,
        load_cases=[{"name": "Surcharge", "w": 15.0}],
    ),
]

# The 55-slot arrays do not all share one grid: wall_cw and base_cw are
# both written over the first 51 slots, so [:51] is right for the two read
# below — but not for m_base, as_base_total or as_req_base, which run
# further along the base. See the feature page before slicing those.
POINTS = 51

rows = []
for wall in SCHEDULE:
    inputs = dict(COMMON)
    inputs.update({k: v for k, v in wall.items() if k != "wall"})

    result = prokon.v5.retaining_wall.analyse(**inputs)["result"]

    # The three stability checks, in the sense each ratio is published in:
    # the first two are achieved/required (want >= 1), the third is
    # qmax/pmax (want <= 1).
    ovt = result["overturning_ratio"]
    sld = result["sliding_ratio"]
    bear = result["bearing_ratio"]
    fails = ([] if ovt >= 1 else ["overturning"]) \
        + ([] if sld >= 1 else ["sliding"]) \
        + ([] if bear <= 1 else ["bearing"])

    rows.append({
        "wall": wall["wall"],
        "H [m]": inputs["h1"],
        "base [m]": round(inputs["b"] + inputs["ab"] + inputs["d"], 3),
        "SF overturning": round(result["sf_overturning"], 3),
        "SF sliding": round(result["sf_sliding"], 3),
        "qmax [kPa]": round(result["qmax"], 2),
        "allowable [kPa]": inputs["pmax"],
        "governing LC": result["governing_lc"],
        "wall As [mm2/m]": round(result["as_wall_req"]),
        "base As [mm2/m]": round(result["as_base_req"]),
        "max crack [mm]": round(max(max(result["wall_cw"][:POINTS]),
                                    max(result["base_cw"][:POINTS])), 3),
        "verdict": "OK" if not fails else "FAILS " + " + ".join(fails),
        "back vertical bars": result["bs_zones"][0],
    })

table = pd.DataFrame(rows)
print(table.to_string(index=False))

# W5 is in the schedule to make the point that an inadequate wall is not
# an error: C14 analyses it happily and reports poor safety factors. The
# verdict column above — not any single result key — is what catches it.

out = Path("retaining_wall_schedule.xlsx")
table.to_excel(out, index=False, sheet_name="Retaining walls")
print(f"\nWritten: {out.resolve()}")
