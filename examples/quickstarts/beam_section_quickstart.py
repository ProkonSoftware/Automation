# ---
# Example:  Beam section — your first analysis
# Feature:  beam_section (C22 Beam Section)
# Verified: yes — 2026-09-02 — mu/ast match values pinned in the C22 test suite; exact on prokon-automation.exe
# ---
# Design a rectangular reinforced-concrete beam section for bending and
# shear, straight from Python. This is the whole pattern: one call with
# named inputs, a plain dictionary of results back.

import prokon.v5

# A 300 x 500 beam in C30 concrete with 450 MPa steel, designed to
# BS8110 - 1997 for an ultimate moment of 200 kNm and shear of 100 kN.
result = prokon.v5.beam_section.analyse(
    design_code="BS8110 - 1997",  # spelled exactly as the desktop names it
    m=200.0,     # ultimate moment [kNm]
    v=100.0,     # ultimate shear force [kN]
    bw=300.0,    # web width [mm]
    h=500.0,     # overall section depth [mm]
    dc_t=40.0,   # cover to centre of top reinforcement [mm]
    dc_b=40.0,   # cover to centre of bottom reinforcement [mm]
    dc_s=40.0,   # side cover to centre of reinforcement [mm]
    fcu=30.0,    # concrete strength [MPa]
    fy=450.0,    # main reinforcement yield strength [MPa]
    fyv=450.0,   # shear reinforcement yield strength [MPa]
)["result"]

# The results are the engine's own full-precision numbers — the same
# values the desktop program computes for this section.
print(f"Moment capacity   Mu  = {result['mu']:.1f} kNm")     # 295.2 kNm
print(f"Tension steel     Ast = {result['ast']:.0f} mm2")    # 1287 mm2
print(f"Min steel         Anom= {result['anom']:.0f} mm2")
print(f"Neutral axis      x   = {result['x_na']:.1f} mm")

# Shear: compare the applied stress against the code's ceiling yourself,
# exactly as you would read them off the desktop's output.
vv, vcu = result["vv"], result["vcu"]                        # both MPa
print(f"Shear stress      v   = {vv:.2f} MPa  (limit {vcu:.2f} MPa)"
      f"  ->  {'OK' if vv <= vcu else 'SECTION FAILS IN SHEAR'}")

# Prokon also proposes bar arrangements, ready to print or compare:
print("\nTension bar options:")
for bar in result["reinforcement"]["tension_bars"]:
    print(f"  {bar['description']:>8}  ({bar['area']:.0f} mm2 provided)")

print("\nShear link options:")
for link in result["reinforcement"]["shear_links"]:
    print(f"  {link['description']:>10}  ({link['area']:.3f} mm2/mm provided)")
