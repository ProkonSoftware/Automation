# ---
# Example:  What actually sizes a pad footing
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes - 2026-09-02 - the reference footing reproduces the pinned sls.pm / vcx; every sweep row measured on prokon-automation.exe
# ---
# A pad footing has four possible governing checks and they rarely all
# bind at once:
#
#   bearing pressure   the ground
#   one-way shear      the concrete
#   punching shear     the column
#   overturning        the horizontal load
#
# Which one sizes YOUR footing depends on the allowable pressure and on how
# much horizontal load there is. This script maps that, then covers the two
# cases that surprise people: an eccentric column and a combined footing.
#
# ⚠ THE MOST IMPORTANT LINE IN THIS FILE. C15 reports an INADEQUATE footing
# as a SUCCESSFUL analysis. Measured in section 2 below:
# has_feasible_design stays TRUE at 290 kPa against a 200 kPa
# allowable. Nothing is derived from allowable_bearing_
# pressure - the comparison is the CALLER'S job, every time. And
# max_bearing_pressure is the ULTIMATE pressure: the one to compare against
# an allowable is max_bearing_pressure_sls.

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0

REFERENCE = dict(
    design_code=CODE, a=2.5, b=2.5, yf=0.6, z=0.5,
    c1=0.4, d1=0.4, e1=0.0, f1=0.0,
    fcu=FCU, fy=FY, allowable_bearing_pressure=200.0,
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
    bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
    bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
)

print("WHAT ACTUALLY SIZES A PAD FOOTING")

# ── The anchor ──────────────────────────────────────────────────────────
PINNED_PM = 133.98908218356328
PINNED_VCX = 0.3568429018580138
anchor = prokon.v5.pad_footing.analyse(
    **REFERENCE,
    load_cases=[{"name": "LC1", "pa1": 600.0, "hx1": 30.0,
                 "mx1": 20.0, "lf1": 1.4}])["result"]
print(f"\n  anchor: the golden 2.5 x 2.5 x 0.6 m footing under 600 kN")
print(f"    sls.pm {anchor['max_bearing_pressure_sls']!r}")
print(f"    pinned {PINNED_PM!r}")
print(f"    vcx    {anchor['critical_uls']['shear']['vcx']!r}")
print(f"    pinned {PINNED_VCX!r}")
exact = (anchor["max_bearing_pressure_sls"] == PINNED_PM
         and anchor["critical_uls"]["shear"]["vcx"] == PINNED_VCX)
print(f"    -> {'EXACT on both' if exact else 'DRIFTED'}")
print(f"    and the ULTIMATE pressure is "
      f"{anchor['max_bearing_pressure']:.4f} kPa - a DIFFERENT number, not")
print(f"    comparable with the {REFERENCE['allowable_bearing_pressure']:.0f} kPa allowable")


def footing(plan, depth, load, horizontal=0.0, moment=0.0,
            allowable=200.0, **overrides):
    settings = dict(REFERENCE)
    settings.update(a=plan, b=plan, yf=depth,
                    allowable_bearing_pressure=allowable)
    settings.update(overrides)
    return prokon.v5.pad_footing.analyse(
        **settings,
        load_cases=[{"name": "LC", "pa1": load, "hx1": horizontal,
                     "mx1": moment, "lf1": 1.4}])["result"]


def checks(result, allowable):
    """Every check, as a utilisation. Above 1.0 fails."""
    critical = result["critical_uls"]
    shear = critical["shear"]
    sls = critical["sls"]
    found = {
        "bearing": result["max_bearing_pressure_sls"] / allowable,
        "shear x": shear["vx"] / shear["vcx"] if shear["vcx"] else None,
        "shear y": shear["vy"] / shear["vcy"] if shear["vcy"] else None,
        # ⚠ vcp = 0 means the punching perimeter did not FIT in the pad, so
        # the check never ran. Reporting it as None rather than as 0/0 keeps
        # "not checked" distinct from "passed".
        "punching": shear["vp"] / shear["vcp"] if shear["vcp"] else None,
        "overturning": 2.0 / sls["sf_ovt"] if sls["sf_ovt"] else None,
        "sliding": 1.5 / sls["sf_sliding"] if sls["sf_sliding"] else None,
    }
    return found


NAMES = ("bearing", "shear x", "shear y", "punching", "overturning",
         "sliding")

# ── 1. Which check governs, against allowable pressure ─────────────────
print(f"\n1. WHICH CHECK GOVERNS   1000 kN, 3.0 x 3.0 x 0.7 m, "
      f"allowable swept")
print(f"   {'allowable':>10} " + "".join(f"{name:>12}" for name in NAMES)
      + "  governs")

for allowable in (100.0, 150.0, 200.0, 300.0, 500.0, 1000.0):
    result = footing(3.0, 0.7, 1000.0, horizontal=50.0, moment=40.0,
                     allowable=allowable)
    found = checks(result, allowable)
    cells = "".join(f"{'n/a' if found[name] is None else format(found[name], '.3f'):>12}"
                    for name in NAMES)
    real = {name: value for name, value in found.items() if value is not None}
    worst = max(real, key=real.get)
    print(f"   {allowable:>10.0f} {cells}  {worst} ({real[worst]:.2f})")

print("   -> at a low allowable the GROUND sizes the footing, and the")
print("      bearing utilisation is the only column that moves - every")
print("      other check is a property of the concrete and the load, not")
print("      of the allowable. Somewhere around 300 to 500 kPa ONE-WAY")
print("      SHEAR takes over as the governing check on this footing.")
print("      A script that only watches bearing therefore stops improving")
print("      the design the moment the ground stops being the constraint,")
print("      and never notices that something else now binds.")

# ── 2. The inadequate footing that reports success ─────────────────────
print(f"\n2. THE SUCCESS THAT IS NOT ONE   1.5 x 1.5 x 0.6 m under 600 kN")
small = footing(1.5, 0.6, 600.0, allowable=200.0)
shear = small["critical_uls"]["shear"]
print(f"   has_feasible_design {small['has_feasible_design']}, no exception")
print(f"   SLS bearing {small['max_bearing_pressure_sls']:.2f} kPa against a "
      f"200 kPa allowable = "
      f"{100.0 * small['max_bearing_pressure_sls'] / 200.0:.0f} %")
print(f"   punching vp {shear['vp']:.4f}   vcp {shear['vcp']:.4f}")
if shear["vcp"] == 0:
    print(f"   -> vcp is ZERO: the punching perimeter does not FIT in a pad")
    print(f"      this small, so the check NEVER RAN. Test 'vp <= vcp' and")
    print(f"      you get 0 <= 0, which reads as a pass. Test vcp > 0 FIRST.")
print(f"   steel as_x {small['critical_uls']['reinforcement']['as_x']:.0f} "
      f"mm2/m - a real number for a footing you must not build.")

# ── 3. An eccentric column ─────────────────────────────────────────────
# e1 and f1 move the column off the footing's centroid. A little
# eccentricity is normal (a boundary column); too much and the engine
# refuses.
print(f"\n3. AN ECCENTRIC COLUMN   3.0 x 3.0 m, column moved along x")
print(f"   {'e1 (m)':>8} {'p sls':>9} {'p uls':>9} {'ecc/plan':>9} "
      f"{'ovt SF':>8}  verdict")

for eccentricity in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75):
    try:
        result = footing(3.0, 0.7, 1000.0, e1=eccentricity)
    except prokon.v5.ProkonError as refusal:
        print(f"   {eccentricity:>8.2f}  {refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:44]}")
        continue
    sls = result["critical_uls"]["sls"]
    print(f"   {eccentricity:>8.2f} {result['max_bearing_pressure_sls']:>9.2f} "
          f"{result['max_bearing_pressure']:>9.2f} "
          f"{eccentricity / 3.0:>9.3f} {sls['sf_ovt']:>8.2f}  "
          f"{'over allowable' if result['max_bearing_pressure_sls'] > 200.0 else 'ok'}")

print("   -> the pressure climbs fast, and the engine refuses only when the")
print("      column leaves the base entirely. Everything before that is")
print("      YOUR judgement about a pressure distribution you can accept.")

# ── 4. The combined footing ────────────────────────────────────────────
# Supplying c2/d2/e2/f2 makes it a two-column footing. All four are needed
# together - a partial set is refused, which is the right behaviour.
print(f"\n4. A COMBINED FOOTING   two columns, 3.0 m apart, on one base")

print(f"   first: what a PARTIAL second column does")
try:
    prokon.v5.pad_footing.analyse(
        **{**REFERENCE, "a": 5.0, "b": 2.5, "c2": 0.4},
        load_cases=[{"name": "LC", "pa1": 600.0, "lf1": 1.4}])["result"]
    print(f"     accepted - which would mean c2 was silently ignored")
except prokon.v5.ProkonError as refusal:
    print(f"     {refusal.category} / {refusal.code}")
    print(f"     {refusal.message.encode('ascii', 'replace').decode()[:100]}")

print(f"\n   {'length':>8} {'p sls':>9} {'ovt SF':>8} {'as_x':>8} "
      f"{'as_y':>8} {'mneg_x':>9}  verdict")

for length in (4.0, 4.5, 5.0, 5.5, 6.0, 7.0):
    try:
        result = prokon.v5.pad_footing.analyse(
            **{**REFERENCE, "a": length, "b": 2.5, "yf": 0.8,
               "c1": 0.4, "d1": 0.4, "e1": -1.5, "f1": 0.0,
               "c2": 0.4, "d2": 0.4, "e2": 1.5, "f2": 0.0,
               "allowable_bearing_pressure": 200.0},
            load_cases=[{"name": "LC", "pa1": 900.0, "pa2": 600.0,
                         "lf1": 1.4, "lf2": 1.4}])["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"   {length:>8.1f}  {refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:44]}")
        continue
    critical = result["critical_uls"]
    print(f"   {length:>8.1f} {result['max_bearing_pressure_sls']:>9.2f} "
          f"{critical['sls']['sf_ovt']:>8.2f} "
          f"{critical['reinforcement']['as_x']:>8.0f} "
          f"{critical['reinforcement']['as_y']:>8.0f} "
          f"{critical['reinforcement']['mneg_x']:>9.1f}  "
          f"{'ok' if result['max_bearing_pressure_sls'] <= 200.0 else 'over allowable'}")

print("   -> mneg_x is the giveaway: a combined footing HOGS between the")
print("      two columns, so it needs TOP steel that a single pad never")
print("      does. On a single-column pad that key is 0; here it is not.")
