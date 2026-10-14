# ---
# Example:  Retaining wall — your first analysis
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes — 2026-09-18 — re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example. They agree with the envelope C14 re-pinned to (4.476/1.634/97.29, steel 916.53/792.46) to 0.008-0.075%; exact on prokon-automation.exe
# ---
# Analyse a concrete cantilever retaining wall — stability, reinforcement
# and crack widths — straight from Python. One call with named inputs, a
# plain dictionary of results back.
#
# The wall below is the one Prokon's own C14 verification run used, so
# every number printed here has been checked against the desktop's own
# calcsheet, not merely against itself.
#
# Only eleven inputs are required (concrete_code, h1, b, d, c, at, ab,
# theta, delta, fcu, fy); everything else has a documented default. They
# are all spelled out here because this is a real, checked wall.

import prokon.v5

result = prokon.v5.retaining_wall.analyse(
    concrete_code="BS8110 - 1997",   # spelled exactly as the desktop names it

    # Geometry, all in METRES. The base is made of three parts:
    #   b  = the toe   — the projection in FRONT of the stem
    #   d  = the heel  — the projection BEHIND it, under the retained fill
    #   ab = the stem thickness where it meets the base
    # so the base slab is b + d + ab wide (here 0.55 + 2.50 + 0.40 = 3.45 m).
    h1=5.0,      # stem height above the base
    h2=0.7,      # soil in front, above dredge level
    h3=0.8,      # depth below dredge level
    hw=2.8,      # water table height (0 = no water table)
    b=0.55,      # toe projection
    d=2.50,      # heel projection
    c=0.40,      # base slab thickness
    f=0.70,      # shear key depth (0 = no shear key)
    xf=3.05,     # shear key position, measured from the back of the heel
    at=0.30,     # stem thickness at the top
    ab=0.40,     # stem thickness at the base
    x=0.45,      # stem batter

    # Soil, in degrees and kN/m3
    theta=27.0,  # internal friction angle of the retained soil
    alpha=9.0,   # fill slope angle (0 = level fill)
    delta=20.0,  # wall/soil friction angle
    dg=18.0,     # soil density
    db=25.0,     # concrete density

    # Materials, MPa
    fcu=25.0,    # concrete strength
    fy=450.0,    # reinforcement yield strength

    # Safety and load factors, and the allowable bearing pressure in kPa
    sf_overturning=1.5,
    sf_sliding=1.5,
    dl_fac=1.4,
    ll_fac=1.6,
    dl_fac_o=0.9,
    pmax=400.0,
    mu=0.5,      # soil Poisson's ratio

    # Cover to reinforcement, mm
    cover_wall=50.0,
    cover_base=50.0,

    # Seismic — kh/kv are read only when seismic is True
    seismic=True,
    kh=0.02,
    kv=0.01,
    seis_w_loads=True,   # include live loads in the seismic combination

    allow_seep=True,        # seepage allowed under the base slab
    toe_back_force=True,    # active pressure on the back of the shear key

    # The load schedule: a list of dictionaries, one per case. Pass it as
    # an ordinary Python list — no JSON string to build yourself.
    load_cases=[
        {"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0, "lynl": 1.0, "xlv": 2.0, "ph": 0.5},
        {"name": "Truck",   "w": 2.0, "p": 0.5, "xp": 2.0, "lynl": 2.0, "xlv": 1.0, "ph": 3.0},
        {"name": "Train",   "w": 3.0,                      "lynl": 1.0, "xlv": 2.0},
    ],
)["result"]

# ── Stability ────────────────────────────────────────────────────────────
# The safety factors are envelopes over every load case; governing_lc says
# which case produced them, counting from 1 as the desktop does.
print(f"Governing load case : {result['governing_lc']}")                 # 3 (Train)
print(f"Overturning   SF    = {result['sf_overturning']:.3f}"
      f"   (required 1.5)")                                              # 4.762
print(f"Sliding       SF    = {result['sf_sliding']:.3f}"
      f"   (required 1.5)")                                              # 1.673
print(f"Bearing  qmax/qmin  = {result['qmax']:.2f} / {result['qmin']:.2f} kPa"
      f"   (allowable 400)")                                             # 93.55 / 33.81

# Two of the three ratios read "bigger is better", the bearing one does not:
#   overturning_ratio = achieved SF / required SF     -> want >= 1
#   sliding_ratio     = achieved SF / required SF     -> want >= 1
#   bearing_ratio     = qmax / pmax                   -> want <= 1
ovt, sld, bear = (result["overturning_ratio"],
                  result["sliding_ratio"],
                  result["bearing_ratio"])
print(f"\nOverturning {ovt:5.2f}x required   {'OK' if ovt >= 1 else 'FAILS'}")   # 3.17x
print(f"Sliding     {sld:5.2f}x required   {'OK' if sld >= 1 else 'FAILS'}")     # 1.12x
print(f"Bearing     {bear:5.2f}x allowable  {'OK' if bear <= 1 else 'FAILS'}")   # 0.23x

# ── Reinforcement and crack widths ───────────────────────────────────────
# The steel figures are worst-case envelopes over the wall and the base,
# in mm2 per metre run of wall.
print(f"\nWall steel required : {result['as_wall_req']:.0f} mm2/m")      # 846 mm2/m
print(f"Base steel required : {result['as_base_req']:.0f} mm2/m")       # 729 mm2/m

# The distributed arrays are 55 slots long, and they do NOT all share one
# grid. heights[0..50] runs DOWN the stem in fifty equal steps, from 0 at
# the top to h1 - c at the base (4.60 m here); wall_cw sits on that grid,
# and base_cw is written over the same first 51 slots, so [:51] is right
# for all three. It is NOT right for m_base, as_base_total or as_req_base,
# which run further along the base — see the feature page before slicing
# those.
POINTS = 51
wall_cw = max(result["wall_cw"][:POINTS])
base_cw = max(result["base_cw"][:POINTS])
print(f"Largest wall crack  = {wall_cw:.2f} mm")                        # 0.14 mm
print(f"Largest base crack  = {base_cw:.2f} mm")                        # 0.17 mm
print(f"Engine crack verdict: {'OK' if result['crack_ok'] else 'EXCEEDED'}")

# The bending moment envelope along the stem, at full precision:
heights = result["heights"][:POINTS]
m_wall = result["m_wall"][:POINTS]
worst = max(range(POINTS), key=lambda i: m_wall[i])
print(f"\nPeak stem moment    = {m_wall[worst]:.1f} kNm/m"
      f" at {heights[worst]:.2f} m below the top of the stem")          # 107.6 at 4.60 m


# And the bar schedule Prokon would draw — twelve zones, in the desktop's
# own order (back/front verticals, horizontals, starters, base bars, ...).
print("\nBending schedule zones:")
for zone, bars in enumerate(result["bs_zones"], start=1):
    print(f"  zone {zone:2d}  {bars or '(no bars required)'}")
