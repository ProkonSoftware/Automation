# ---
# Example:  Punching shear — your first column head
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes — 2026-09-02 — perimeter-1 Asv matches the value pinned in the C23 test suite; exact on prokon-automation.exe
# ---
# Check punching shear at a column head in a flat slab, straight from
# Python. This is the whole pattern: one call with named inputs, a plain
# dictionary of results back.

import prokon.v5

# A 400 x 400 internal column in a 200 mm effective-depth flat slab,
# C35 concrete, 500 MPa steel, checked to BS8110 - 1997 for one ultimate
# load case: 800 kN of shear with 50 and 30 kNm of transfer moment.
#
# The slab edges are 10 m away in both directions, which is how you say
# "this column is internal": the engine treats the column as an edge or
# corner column whenever an edge falls inside the outermost critical
# perimeter, so give a genuinely large distance when it does not.
#
# The flexural (top) steel is deliberately left out here. The engine then
# reads it as ZERO steel, which lowers the concrete's shear capacity and
# so overstates the reinforcement needed — safe, but pessimistic. Supply
# asx_1..asx_4 and asy_1..asy_4 in real work; the reference page explains
# how to work them out from your bar spacing.
result = prokon.v5.punching_shear.analyse(
    design_code="BS8110 - 1997",   # spelled exactly as the desktop names it
    col_width=400.0,        # column dimension A [mm]
    col_breadth=400.0,      # column dimension B [mm]
    effective_depth=200.0,  # effective slab depth de [mm]
    nearest_edge_x=10000.0, # distance to the nearest slab edge in X [mm]
    nearest_edge_y=10000.0, # distance to the nearest slab edge in Y [mm]
    fcu=35.0,               # concrete strength [MPa]
    fy=500.0,               # flexural reinforcement yield strength [MPa]
    fyv=500.0,              # shear reinforcement yield strength [MPa]
    load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}],  # kN, kNm, kNm
)["result"]

# ── Check 1: the column face ────────────────────────────────────────────
# The stress on the column face must stay under the code's ceiling. This
# check has no remedy in reinforcement — if it fails, the column or the
# slab has to get bigger.
uo = result["uo"]                                  # column-face perimeter [mm]
vu = result["vu"][result["critical_load_case_index"]]   # applied stress [MPa]
vcu = result["vcu"]                                # code's ceiling [MPa]

print(f"Column face perimeter  uo  = {uo:.0f} mm")            # 1600 mm
print(f"Face shear stress      vu  = {vu:.4f} MPa"
      f"  (limit {vcu:.4f} MPa)"                              # 2.6641 / 4.7329
      f"  ->  {'OK' if vu <= vcu else 'FACE OVERSTRESSED'}")

# ── Check 2: the five critical perimeters ───────────────────────────────
# Prokon works outwards through five critical perimeters. At each one it
# reports the shear the perimeter must carry (veff), what the concrete
# alone can carry (vcap), and the shear reinforcement that closes the gap
# (asv). asv = 0 means that perimeter needs no shear reinforcement.
print("\nperimeter   r [mm]   ucrit [mm]   Vcap [kN]   Veff [kN]   Asv [mm2]")

for p in result["critical_perimeters"]:
    print(f"{p['perimeter']:>9} {p['radial_distance']:>8.0f} {p['ucrit']:>12.0f} "
          f"{p['vcap']:>11.1f} {p['veff']:>11.1f} {p['asv']:>11.1f}")

# Perimeter 1 needs 2519.6 mm2 here — the value the C23 test suite pins
# for exactly this section.

# ── The reinforcement Prokon suggests ───────────────────────────────────
# Five bar arrangements per perimeter, each providing at least the area
# required. An empty description means that perimeter needs nothing.
print("\nShear reinforcement options, perimeter 1:")

for bar in result["bars"][0]:
    if bar["description"]:
        print(f"  {bar['description']:>8}  ({bar['area']:.0f} mm2 provided)")

# ── Warnings the desktop would print on the calcsheet ───────────────────
# vc_warning is the BS8110-family "shear stress v exceeds 2*vc" note (and
# the IS456 equivalent). It asks for justification of the design; it is
# not a failure. Codes outside those families never set it.
if result["vc_warning"]:
    print("\nWarning: shear stress exceeds twice the concrete capacity -"
          " justification of the design is required.")
