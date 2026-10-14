# ---
# Example:  Independent check of a retaining wall - stability and cracking
# Feature:  retaining_wall + crack_widths (C14 Retaining Wall + C21 Crack Widths)
# Verified: yes - 2026-09-18 - the parity wall reproduces its pinned stability values and the reference slab its pinned triple; every wall measured on prokon-automation.exe; the wall pair re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example (the C21 crack triple is untouched)
# ---
# Checking a retaining wall means checking four things and one of them is
# not in the drawing at all:
#
#   OVERTURNING   is there a factor of safety?
#   SLIDING       likewise, and it is usually the binding one
#   BEARING       against the geotechnical allowable
#   CRACKING      against the exposure class, with THE BARS AS DRAWN
#
# C14 reports its own crack widths for the steel IT would design. That is
# not the question. The question is whether the bars on the drawing hold
# the crack limit - which is C21's job, with the arrangement supplied.
#
# ⚠ AND THE SAFETY FACTORS ARE INPUTS, NOT CONSTANTS. C14 takes
# sf_overturning and sf_sliding and reports the ACHIEVED factor against
# them as a ratio. A checker with a different view of the required factors
# changes those inputs; the ratio then answers the checker's question and
# not the designer's.

import math

import prokon.v5

CONCRETE_CODE = "BS8110 - 1997"
CRACK_CODE = "BS8007 - 1987"
FCU = 30.0
FY = 450.0

# The checker's own required factors, which may differ from the designer's.
REQUIRED_OVERTURNING = 2.0
REQUIRED_SLIDING = 1.5
CRACK_LIMIT = 0.3

# ── The walls, as drawn ────────────────────────────────────────────────
# (mark, retained m, toe m, heel m, base m, stem top m, stem base m,
#  theta deg, surcharge kPa, water m, stem bars as drawn)
WALLS = (
    ("W1", 3.0, 0.60, 1.60, 0.40, 0.25, 0.35, 30.0,  5.0, 0.0, "Y16@200"),
    ("W2", 4.0, 0.70, 2.20, 0.50, 0.30, 0.40, 30.0, 10.0, 0.0, "Y20@175"),
    ("W3", 5.0, 0.80, 2.60, 0.60, 0.30, 0.50, 28.0, 10.0, 2.0, "Y25@150"),
    ("W4", 3.5, 0.40, 1.20, 0.40, 0.25, 0.35, 26.0, 15.0, 1.5, "Y16@200"),
    ("W5", 6.0, 1.00, 3.20, 0.70, 0.35, 0.60, 30.0, 10.0, 3.0, "Y25@125"),
)


def mesh_area(description):
    """mm2/m from 'Y20@175'. Written out so a checker can see it."""
    diameter, _, spacing = description.partition("@")
    bar = float(diameter.lstrip("YTR"))
    return (math.pi * bar ** 2 / 4.0) * 1000.0 / float(spacing)


print("INDEPENDENT CHECK OF A RETAINING WALL SCHEDULE")
print(f"  {CONCRETE_CODE} with {CRACK_CODE} crack widths")
print(f"  the CHECKER's required factors: overturning "
      f"{REQUIRED_OVERTURNING}, sliding {REQUIRED_SLIDING}, "
      f"crack {CRACK_LIMIT} mm")

# ── Both engines, against their own pins ───────────────────────────────
wall_anchor = prokon.v5.retaining_wall.analyse(
    concrete_code="BS8110 - 1997", h1=5.0, h2=0.7, h3=0.8, hw=2.8,
    b=0.55, d=2.5, c=0.4, f=0.7, xf=3.05, at=0.3, ab=0.4, x=0.45,
    theta=27.0, alpha=9.0, delta=20.0, dg=18.0, db=25.0,
    fcu=25.0, fy=450.0, sf_overturning=1.5, sf_sliding=1.5,
    dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9, pmax=400.0, mu=0.5,
    cover_wall=50.0, cover_base=50.0,
    seismic=True, kh=0.02, kv=0.01, seis_w_loads=True,
    allow_seep=True, toe_back_force=True,
    load_cases=[
        {"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0, "lynl": 1.0,
         "xlv": 2.0, "ph": 0.5},
        {"name": "Truck", "w": 2.0, "p": 0.5, "xp": 2.0, "lynl": 2.0,
         "xlv": 1.0, "ph": 3.0},
        {"name": "Train", "w": 3.0, "lynl": 1.0, "xlv": 2.0}])["result"]
crack_anchor = prokon.v5.crack_widths.analyse(
    design_code="BS8007 - 1987", slab_mode=True, h=300.0, hef=200.0,
    b=1000.0, cover=40.0, fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
    allowable_crack_width=0.3, high_bond_bar=True, short_term_load=True,
    load_cases=[{"n": 1, "m": 50.0, "m_uls": 1.5}])["result"]

WALL_PINNED = (4.477940718035636, 1.6341314510288516)
CRACK_PINNED = 0.11059554804834058
wall_measured = (wall_anchor["sf_overturning"], wall_anchor["sf_sliding"])
crack_measured = (crack_anchor["load_cases"][0]["optimised_configs"][0]
                  ["calc_result"]["governing_crack_width"])
print(f"\n  engine check:")
print(f"    C14 SF pair  {'EXACT' if wall_measured == WALL_PINNED else 'DRIFTED'}"
      f"   {wall_measured[0]!r}")
print(f"    C21 crack w  {'EXACT' if crack_measured == CRACK_PINNED else 'DRIFTED'}"
      f"   {crack_measured!r}")

# ── The check ───────────────────────────────────────────────────────────
print(f"\n{'mark':<5} {'H':>5} {'ovt SF':>8} {'/req':>6} {'sld SF':>8} "
      f"{'/req':>6} {'qmax':>8} {'As req':>8} {'prov':>8} {'crack':>8}  "
      f"verdict")
print("-" * 100)

faults = []
for (mark, retained, toe, heel, base, stem_top, stem_base,
     theta, surcharge, water, bars) in WALLS:

    # ⚠ The checker's own required factors go IN, so the ratios that come
    # back answer the checker's question. A ratio computed against the
    # designer's factors would be the designer's answer restated.
    wall = prokon.v5.retaining_wall.analyse(
        concrete_code=CONCRETE_CODE,
        crack_width_code=CRACK_CODE,
        h1=retained, b=toe, d=heel, c=base,
        at=stem_top, ab=stem_base,
        theta=theta, delta=2.0 * theta / 3.0,
        hw=water, dg=19.0, db=25.0,
        fcu=FCU, fy=FY,
        cover_wall=50.0, cover_base=50.0,
        sf_overturning=REQUIRED_OVERTURNING,
        sf_sliding=REQUIRED_SLIDING,
        pmax=200.0,
        load_cases=[{"name": "Surcharge", "w": surcharge}])["result"]

    provided = mesh_area(bars)
    required = wall["as_wall_req"]

    # The crack check with the bars AS DRAWN. C14's own crack figures are
    # for the steel it would have designed, which is a different question.
    stem = stem_base * 1000.0
    moment = max(abs(value) for value in wall["m_wall"])
    crack = prokon.v5.crack_widths.analyse(
        design_code=CRACK_CODE, slab_mode=True,
        h=stem, hef=stem / 2.0, b=1000.0, cover=50.0,
        fcu=FCU, fy=FY, ea=200.0, ec=0.0,
        allowable_crack_width=CRACK_LIMIT,
        high_bond_bar=True, short_term_load=False,
        user_slab_bars=bars,
        load_cases=[{"n": 1, "m": moment, "m_uls": 1.5}])["result"]

    mine = crack["load_cases"][0]["user_slab_result"]
    # user_slab_result is None when no arrangement was supplied, and the
    # engine can also decline to report one - test before reading.
    drawn_crack = (mine["calc_result"]["governing_crack_width"]
                   if mine is not None else None)

    reasons = []
    if wall["overturning_ratio"] < 1.0:
        reasons.append(f"overturning {wall['sf_overturning']:.2f} against a "
                       f"required {REQUIRED_OVERTURNING}")
    if wall["sliding_ratio"] is None:
        reasons.append("sliding is not reported for this wall type")
    elif wall["sliding_ratio"] < 1.0:
        reasons.append(f"sliding {wall['sf_sliding']:.2f} against a required "
                       f"{REQUIRED_SLIDING}")
    if not 0.0 < wall["bearing_ratio"] <= 1.0:
        reasons.append(f"bearing {wall['qmax']:.1f} kPa, ratio "
                       f"{wall['bearing_ratio']:.2f}")
    if provided < required:
        reasons.append(f"stem steel short by {required - provided:.0f} mm2/m")
    if drawn_crack is None:
        reasons.append(f"the engine reported no result for {bars}")
    elif drawn_crack > CRACK_LIMIT:
        reasons.append(f"the DRAWN bars crack at {drawn_crack:.4f} mm "
                       f"against a {CRACK_LIMIT} mm limit")

    def cell(value, spec):
        return "null" if value is None else format(value, spec)

    print(f"{mark:<5} {retained:>5.1f} "
          f"{cell(wall['sf_overturning'], '8.2f')} "
          f"{cell(wall['overturning_ratio'], '6.2f')} "
          f"{cell(wall['sf_sliding'], '8.2f')} "
          f"{cell(wall['sliding_ratio'], '6.2f')} "
          f"{cell(wall['qmax'], '8.1f')} "
          f"{required:>8.0f} {provided:>8.0f} "
          f"{cell(drawn_crack, '8.4f')}  "
          f"{'PASS' if not reasons else 'FAIL'}")
    for reason in reasons:
        print(f"{'':<5} -> {reason}")
    if reasons:
        faults.append(mark)

# ── The comparison that makes the crack check worth doing ──────────────
print(f"\n{'-' * 100}")
print("C14's OWN crack figures against C21's, for the DRAWN bars:")
print(f"{'mark':<5} {'C14 worst wall_cw':>19} {'C21 on drawn bars':>19}  "
      f"the difference")

for (mark, retained, toe, heel, base, stem_top, stem_base,
     theta, surcharge, water, bars) in WALLS:
    wall = prokon.v5.retaining_wall.analyse(
        concrete_code=CONCRETE_CODE, crack_width_code=CRACK_CODE,
        h1=retained, b=toe, d=heel, c=base, at=stem_top, ab=stem_base,
        theta=theta, delta=2.0 * theta / 3.0, hw=water,
        dg=19.0, db=25.0, fcu=FCU, fy=FY,
        cover_wall=50.0, cover_base=50.0,
        sf_overturning=REQUIRED_OVERTURNING, sf_sliding=REQUIRED_SLIDING,
        pmax=200.0,
        load_cases=[{"name": "Surcharge", "w": surcharge}])["result"]
    stem = stem_base * 1000.0
    moment = max(abs(value) for value in wall["m_wall"])
    crack = prokon.v5.crack_widths.analyse(
        design_code=CRACK_CODE, slab_mode=True,
        h=stem, hef=stem / 2.0, b=1000.0, cover=50.0,
        fcu=FCU, fy=FY, ea=200.0, ec=0.0,
        allowable_crack_width=CRACK_LIMIT,
        high_bond_bar=True, short_term_load=False, user_slab_bars=bars,
        load_cases=[{"n": 1, "m": moment, "m_uls": 1.5}])["result"]
    mine = crack["load_cases"][0]["user_slab_result"]
    theirs = max(wall["wall_cw"])
    ours = (mine["calc_result"]["governing_crack_width"]
            if mine is not None else None)
    if ours is None:
        note = "C21 reported nothing for these bars"
    elif theirs == 0:
        note = "C14 reports zero - it designed no steel here"
    else:
        note = f"{ours / theirs:.2f}x C14's figure"
    print(f"{mark:<5} {theirs:>19.4f} "
          f"{'none' if ours is None else format(ours, '19.4f')}  {note}")

print(f"\n{'-' * 100}")
if faults:
    print(f"Walls needing attention: {', '.join(faults)}")
else:
    print("Every wall passes against the checker's own factors.")
print()
print("The two figures in that last table are answers to DIFFERENT")
print("questions. C14 reports the crack width of the steel it would have")
print("designed; C21 reports the crack width of the bars on the drawing.")
print("Only the second one is a check.")
