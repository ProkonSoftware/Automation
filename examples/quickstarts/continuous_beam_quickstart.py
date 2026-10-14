# ---
# Example:  Continuous beam — your first analysis
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes — 2026-09-02 — steel/deflection/crack values match the C01 goldens AND the desktop calcsheet transcription; exact on prokon-automation.exe
# ---
# Analyse and design a two-span reinforced-concrete beam straight from
# Python. The model is four small tables — sections, segments, supports,
# loads — exactly like the desktop program's input grids, passed as plain
# Python lists of dictionaries.

import prokon.v5

# Two 6 m spans of a 300 x 500 rectangle, 20 kN/m dead + 10 kN/m live on
# each span, designed to BS8110 - 1997. You supply UNFACTORED dead and
# live loads; the engine applies the load factors and the code's pattern
# loading itself.
result = prokon.v5.continuous_beam.analyse(
    design_code="BS8110 - 1997",
    sections=[{"n": 1, "bw": 300, "d": 500}],        # web width x depth [mm]
    segments=[
        {"span": 1, "length": 6, "sec_left": 1},     # span lengths [m]
        {"span": 2, "length": 6, "sec_left": 1},
    ],
    supports=[{"n": 1}, {"n": 2}, {"n": 3}],         # three simple supports
    loads=[
        {"case": "Dead", "span": 1, "w_left": 20},   # UDLs [kN/m]
        {"case": "Dead", "span": 2, "w_left": 20},
        {"case": "Live", "span": 1, "w_left": 10},
        {"case": "Live", "span": 2, "w_left": 10},
    ],
    fyv=250.0,                     # link steel [MPa]  (main steel fy defaults to 450)
    cover_top=30.0, cover_bot=40.0,          # to bar CENTRES [mm]
    live_permanent_percent=25.0,   # serviceability: 25% of live is permanent,
    creep_coefficient=2.0,         # creep factor 2,
    shrinkage_strain=300e-6,       # 300 microstrain shrinkage (as a strain!)
)["result"]

# ── The envelope extremes, over the code's load patterns ─────────────────
print(f"Spans analysed        {result['span_count']}  "
      f"({result['total_length']:.0f} m total)")
print(f"Max sagging moment    {result['max_sagging_moment']:8.1f} kNm")   # 132.5
print(f"Max hogging moment    {result['max_hogging_moment']:8.1f} kNm")   # -198.0
print(f"Max shear             {result['max_shear']:8.1f} kN")             # 165.0

# ── Required reinforcement, span by span ─────────────────────────────────
# Steel areas are mm2; shear steel is Asv/sv in mm2 per mm, exactly as the
# desktop calcsheet prints it.
for span in result["spans"]:
    print(f"Span {span['span_number']}:  As-bot {span['max_bottom_steel']:6.0f} mm2   "     # 805
          f"As-top {span['max_top_steel']:6.0f} mm2   "                                     # 1235
          f"Asv/sv {span['max_shear_steel']:.3f} mm2/mm")                                   # 0.608

# ── Serviceability — the verdict is yours, so check it explicitly ────────
span_mm = 6000.0
limit = span_mm / 250.0
defl = result["max_deflection"]        # mm, long-term total   (12.45)
crack = result["max_crack_width"]      # mm                    (0.117)
print(f"Deflection            {defl:8.2f} mm  (limit span/250 = {limit:.1f} mm)"
      f"  ->  {'OK' if defl <= limit else 'EXCEEDED'}")
print(f"Crack width           {crack:8.3f} mm")

# ── Support reactions [kN] ───────────────────────────────────────────────
for s in result["supports"]:
    print(f"Support {s['support_number']}:  dead {s['reaction_dead']:6.1f}   "
          f"live {s['reaction_live']:5.1f}   ultimate {s['reaction_ultimate']:6.1f}")

# The full position-by-position output is also here: 22 named envelopes,
# each one value per analysis position — ready for numpy or matplotlib
# (see the envelope-chart recipe).
env = result["envelopes"]
print(f"\nEnvelopes: {len(env)} series x {result['position_count']} positions, "
      f"x = 0 to {env['position'][-1]:.0f} m")
