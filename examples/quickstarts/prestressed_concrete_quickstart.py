# ---
# Example:  Prestressed concrete — your first analysis
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes — 2026-09-02 — every printed value matches the desktop program's own; exact on prokon-automation.exe
#           output for its bundled two-span example (Prokon W5.3.06 tabular export,
#           values pinned in the C02 parity suite), punching shear included
# ---
# Analyse a post-tensioned two-span flat slab strip: frame analysis,
# tendon losses, SLS/transfer/ULS envelopes, deflections, crack widths
# and punching shear — one call, one dictionary of results.
#
# The model below is the desktop Captain program's own bundled example
# ("DEFAULT EXAMPLE"), transcribed input grid for input grid. Each list
# input mirrors one grid of the desktop program, row for row.

import prokon.v5

result = prokon.v5.prestressed_concrete.analyse(
    design_code="BS8110 - 1997",   # spelled exactly as the desktop names it
    title="DEFAULT EXAMPLE",

    # Materials (the desktop's parameter grid, same units)
    fcu=19.2,       # concrete strength [MPa]
    fy=450.0,       # reinforcement yield stress [MPa]
    fyv=250.0,      # shear reinforcement yield stress [MPa]
    fci=14.4,       # concrete strength at transfer [MPa]
    ec=26e6,        # concrete E-modulus [kN/m2]
    est=206e6,      # reinforcement E-modulus [kN/m2]
    density=24.0,   # own weight is added to the dead load [kN/m3]
    top_cover=25.0, bottom_cover=25.0,          # [mm]

    # Options and factors that differ from their defaults
    attached_torsional_members=True,
    edge_beam=True,
    redistribution_pct=10.0,       # % moment redistribution

    # Tendon material property set 1 (referenced by the cable sets)
    tendon_properties=[
        {"no": 1, "bond": "Unbonded", "strength": 260.7,   # kN per cable
         "max_stress_pct": 80, "dia": 18, "area": 140,     # mm, mm2
         "k": 0.0015, "u": 0.05,     # wobble / curvature friction
         "pullin": 5, "relax": 2,    # wedge pull-in [mm], relaxation [%]
         "est": 195e6, "min_harp_radius": 1.0},
    ],

    # Explicit cable layout: two sets, jacked from opposite ends.
    # x_live / x_dead are the ANCHOR POSITIONS in metres from the beam
    # origin — the engine derives the per-span anchor codes from them,
    # exactly as the desktop does. b1/b2/b3 are cable depths below the
    # top at span start / lowest point / span end [mm].
    cable_sets=[
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
    ],

    # Geometry: a 5 m wide, 250 mm deep slab strip over two spans
    sections=[
        {"name": "sec1", "bw": 5000, "d": 250},    # mm
        {"name": "sec2", "bw": 5000, "d": 500},
        {"name": "sec3", "bw": 2500, "d": 500},
    ],
    span_segments=[
        {"span": 1, "length": 8.0, "sec_left": "sec1"},   # m
        {"span": 2, "length": 7.5, "sec_left": "sec1"},
    ],

    # Supports: 300-square columns below (and above at the ends), 3 m
    # high, far ends fixed. The letter cells are the desktop's own.
    supports=[
        {"no": 1, "d_below": 300, "b_below": 300, "h_below": 3.0, "code_below": "F",
                  "d_above": 300, "b_above": 300, "h_above": 3.0, "code_above": "F"},
        {"no": 2, "d_below": 300, "h_below": 3.0, "code_below": "F"},
        {"no": 3, "d_below": 300, "b_below": 300, "h_below": 3.0, "code_below": "F",
                  "d_above": 300, "b_above": 300, "h_above": 3.0, "code_above": "F"},
    ],

    # The load grid. A blank "case"/"span" cell continues the row above,
    # exactly as in the desktop grid.
    loads=[
        {"case": "D", "span": 1, "wl": 6},                             # kN/m
        {"span": 2, "wl": 6, "p": 10, "p_pos": 2, "m": 10, "m_pos": 4},  # + point load & moment
        {"case": "L", "span": 1, "wl": 15},
        {"span": 2, "wl": 15},
    ],

    # Additional (non-prestressed) reinforcement, bar strings verbatim
    additional_rebar=[
        {"span": 1, "pos": "T", "bars": "8Y16", "left_end": "Hook",
         "right_end": "Bend", "x": 5.0, "length": 6.0},
        {"span": 1, "pos": "B", "bars": "8Y16", "left_end": "Hook", "length": 8.0},
        {"span": 2, "pos": "B", "bars": "8Y16", "right_end": "Bend", "length": 7.0},
    ],

    # Punching shear checks at all three columns: only what the engine
    # lets persist — everything else is re-derived from the frame.
    # "pcy" is the desktop model's stored Y-prestress force at the column
    # [kN]; it is optional, and omitting it drops the Y deduction from
    # veff (see the note at the punching print below).
    punching_columns=[
        {"no": 1, "slope_y": 0.05, "pcy": 280, "cable_type": 1,
         "nc_x": [4, 5, 6, 7], "nc_y": [1, 1, 2, 2],
         "ast_x": [402, 402, 603, 804], "ast_y": [565, 565, 565, 565]},
        {"no": 2, "slope_y": 0.06, "pcy": 280, "cable_type": 1,
         "nc_x": [5, 6, 7, 8], "nc_y": [1, 1, 2, 2],
         "ast_x": [942, 942, 942, 942], "ast_y": [804, 804, 804, 804]},
        {"no": 3, "slope_y": 0.05, "pcy": 280, "cable_type": 1,
         "nc_x": [4, 5, 6, 7], "nc_y": [1, 1, 2, 2],
         "ast_x": [402, 402, 603, 804], "ast_y": [565, 565, 565, 565]},
    ],

    # A copy of the desktop's full text report, written after analysis
    report_path="captain_report.txt",
)["result"]

# ----------------------------------------------------------------------
# Results are per-position envelopes: every array has one entry per
# result position, aligned with result["positions"] (metres from the
# beam origin). min()/max() over an array gives the envelope extreme.
# All printed values below match the desktop program's own output for
# this example at its print precision.

print(f"{result['nspan']} spans, {result['ltot']} m, "
      f"{result['npos']} result positions\n")

uls, sls, tra = result["uls"], result["sls"], result["transfer"]

print("Bending envelopes [kNm]")
print(f"  ULS design moment   {min(uls['mnu']):8.2f} .. {max(uls['mpu']):7.2f}")   # -486.00 / 310.20
print(f"  SLS moment          {min(sls['mn']):8.2f} .. {max(sls['mp']):7.2f}")     # -213.16 / 126.64
print(f"  At transfer         {min(tra['mnt']):8.2f} .. {max(tra['mpt']):7.2f}")   # -101.50 /  48.79

# Concrete stresses against the code's permissible values. The fcc/fct
# limits publish in N/m2 — divide by 1e6 for MPa.
print("\nExtreme fibre stresses [MPa]  (compression +, tension -)")
print(f"  SLS       {min(sls['svsmi']):6.2f} .. {max(sls['svsma']):5.2f}"
      f"   (permissible {-sls['fct'] / 1e6:.2f} .. {sls['fcc'] / 1e6:.2f})")   # -3.09 .. 5.09 (-1.97 .. 6.40)
print(f"  Transfer  {min(tra['svtmi']):6.2f} .. {max(tra['svtma']):5.2f}"
      f"   (permissible {-tra['fctt'] / 1e6:.2f} .. {tra['fcct'] / 1e6:.2f})")  # -0.86 .. 3.03 (-1.71 .. 7.20)
# The SLS tension of 3.09 MPa exceeds the basic permissible 1.97 MPa —
# for this partially prestressed slab the story continues in the crack
# widths below, exactly as it does on the desktop's output tabs.

d = result["deflections"]
extreme = max((v for v in d["ditot"] if v is not None), key=abs)
print(f"\nTotal deflection extreme      {extreme:7.3f} mm")                # 7.846
print(f"Elastic deflection max        {max(d['demax']):7.3f} mm")          # 4.066
print(f"Crack width max  top {max(result['crack_widths']['cwt']):.4f} mm"  # 0.4138
      f"  bottom {max(result['crack_widths']['cwb']):.4f} mm")             # 0.0140

# Prestress: tendon force sum at the live-anchor end, and the losses
cab = result["cables"]
print(f"\nTendon force at x = 0 (long term)  {cab['pax'][0]:7.1f} kN")     # 1242.4
print(f"Losses: elastic {cab['perc_elas']:.2f} %  creep {cab['perc_creep']:.2f} %"
      f"  shrinkage {cab['perc_shrink']:.2f} %  relaxation {cab['perc_relax']:.2f} %")
#           0.35            1.38                4.43                2.00

# Shear: capacity envelope and required links (Asv/Sv)
print(f"\nShear capacity min   {min(uls['vca']):7.2f} kN")                 # 324.79
print(f"Links Asv/Sv max     {max(uls['asv']):7.4f} mm2/mm")               # 8.4211

# Punching shear: four perimeters per checked column. 'failed' means
# the perimeter needs more shear capacity than the concrete provides;
# 'asv' is the link area the engine then requires on that perimeter.
print("\nPunching (perimeter 1 of each column)")
for col in result["punching"]:
    p1 = col["perimeters"][0]
    verdict = f"links {p1['asv']:.0f} mm2" if p1["failed"] else "OK"
    print(f"  column {col['no']}:  Veff {p1['veff']:7.1f} kN"
          f"  capacity {p1['vcap']:7.1f} kN  ->  {verdict}")
# Column 1: Veff 537.0, capacity 398.0 -> links 793 mm2   (desktop: 793.01)
# Column 2: Veff 575.0, capacity 705.9 -> OK
# Column 3: Veff 469.6, capacity 398.0 -> links 793 mm2
# Each column above carries the desktop model's stored Y-prestress force
# as "pcy": 280, so these match the desktop print for print. Leave pcy
# out and the engine computes no Y term: veff then reads slope_y*280
# higher (+16.8 kN at column 2, +14.0 at columns 1 and 3), which is
# conservative — vcap/vc/ucrit/asv are the same either way. See the
# feature page for the details.

q = result["quantities"]
print(f"\nQuantities: rebar {q['main_rebar_mass']:.1f} kg"           # 265.9
      f"  links {q['link_mass']:.1f} kg  slab {q['slab_area']:.1f} m2")  # 7.9 / 77.5

print("\nThe desktop's full text report was written to captain_report.txt")
