# ---
# Example:  Prestressed concrete — how much prestress is enough?
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes — 2026-09-02 — the reference model's envelope and tendon force match; exact on prokon-automation.exe
#           the desktop-pinned C02 parity values (ULS 310.20 kNm, 1242.4 kN); every
#           sweep row measured against the built surface
# ---
# The desktop program analyses one cable layout at a time. This script
# *searches*: it hands the cable layout to the engine's own generator
# (balanced_dead_load_pct) and sweeps the balanced-load percentage,
# reading off stresses, deflections and crack widths at each step —
# then picks the least prestress that satisfies the code's SLS stress
# limits. Re-running the desktop seven times becomes one script run.
#
# The structure is the desktop Captain program's own two-span example
# (see the quick-start); only the cable route changes.

import prokon.v5

# ----------------------------------------------------------------- model
MODEL = dict(
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
    sections=[{"name": "sec1", "bw": 5000, "d": 250}],
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
    loads=[
        {"case": "D", "span": 1, "wl": 6},
        {"span": 2, "wl": 6, "p": 10, "p_pos": 2, "m": 10, "m_pos": 4},
        {"case": "L", "span": 1, "wl": 15},
        {"span": 2, "wl": 15},
    ],
    additional_rebar=[
        {"span": 1, "pos": "T", "bars": "8Y16", "left_end": "Hook",
         "right_end": "Bend", "x": 5.0, "length": 6.0},
        {"span": 1, "pos": "B", "bars": "8Y16", "left_end": "Hook", "length": 8.0},
        {"span": 2, "pos": "B", "bars": "8Y16", "right_end": "Bend", "length": 7.0},
    ],
)

# -------------------------------------------------- calibration first
# The desktop example runs this structure with an explicit cable layout
# that was generated at 60 % balance. Reproduce it and check two values
# the C02 parity suite pins against the desktop's printed output — if
# this assert fails, stop trusting the sweep.
reference = prokon.v5.prestressed_concrete.analyse(**MODEL, cable_sets=[
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
])["result"]
assert abs(max(reference["uls"]["mpu"]) - 310.2043) < 0.01     # desktop: 310.20 kNm
assert abs(reference["cables"]["pax"][0] - 1242.35) < 0.01     # desktop: 1242.4 kN

# ----------------------------------------------------------- the sweep
# The code's SLS stress limits, read from the reference run (published
# in N/m2 — divide by 1e6 for MPa).
fcc = reference["sls"]["fcc"] / 1e6     # permissible compression: 6.40 MPa
fct = reference["sls"]["fct"] / 1e6     # permissible tension:     1.97 MPa

print("Balanced-load sweep - two-span PT slab strip, BS8110 - 1997")
print(f"Permissible SLS stresses: compression {fcc:.2f} MPa, tension {fct:.2f} MPa\n")
print("balance   cable   compression  worst tension  deflection  crack")
print("   [%]  mass [kg]     [MPa]         [MPa]         [mm]     [mm]")

rows = []
for balance in (30, 45, 60, 75, 90, 105, 120):
    r = prokon.v5.prestressed_concrete.analyse(
        **MODEL, balanced_dead_load_pct=float(balance))["result"]
    row = {
        "balance": balance,
        "mass": r["quantities"]["cable_mass"],
        "comp": max(r["sls"]["svsma"]),         # extreme compression (+)
        "tens": min(r["sls"]["svsmi"]),         # extreme tension (-)
        # deflections can be large under low prestress; take the extreme
        "defl": max((v for v in r["deflections"]["ditot"] if v is not None), key=abs),
        "crack": max(r["crack_widths"]["cwt"] + r["crack_widths"]["cwb"]),
    }
    rows.append(row)
    print(f"  {row['balance']:4d}  {row['mass']:8.1f}  {row['comp']:10.2f}"
          f"  {row['tens']:12.2f}  {row['defl']:11.2f}  {row['crack']:6.3f}")

# Measured sweep (for orientation — the printed table is the source):
#    30      64.4        5.87         -4.72        31.03   0.745
#    45      88.2        5.54         -4.10        17.57   0.617
#    60     123.5        5.09         -3.09         7.85   0.413  <- the desktop example
#    75     186.9        4.48         -1.08         4.98   0.013
#    90     233.7        3.96         -0.16         3.59   0.000
#   105     251.3        3.75          0.19         2.79   0.000
#   120     298.0        4.58          0.70        -4.16   0.000  <- over-balanced: hogs

# ------------------------------------------------------------ verdicts
# Least prestress whose stresses satisfy the code's basic SLS limits
# (tension within fct, compression within fcc):
ok = [row for row in rows if row["comp"] <= fcc and -row["tens"] <= fct]
best = min(ok, key=lambda row: row["balance"])
print(f"\nLeast prestress within the code's SLS stress limits: "
      f"{best['balance']} % balance ({best['mass']:.0f} kg of cable)")   # 75 % (187 kg)

# And the fully compressed option — no SLS tension anywhere:
crackfree = [row for row in rows if row["tens"] >= 0]
if crackfree:
    first = min(crackfree, key=lambda row: row["balance"])
    print(f"First fully compressed layout (no SLS tension): "
          f"{first['balance']} % balance ({first['mass']:.0f} kg of cable)")  # 105 % (251 kg)

# Reading the table like an engineer: the desktop example's 60 % layout
# accepts 3.09 MPa of hypothetical tension and designs for a 0.41 mm
# crack; 75 % brings the tension inside the basic permissible 1.97 MPa
# for 51 % more cable steel; past ~105 % the slab hogs — more prestress
# stops helping. The engine generated 2 or 3 cable sets per run as the
# desktop would; their as-analysed drapes are in result["cables"]["sets"].
