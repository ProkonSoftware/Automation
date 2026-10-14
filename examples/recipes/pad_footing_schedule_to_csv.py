# ---
# Example:  A foundation schedule for the site engineer, as CSV
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes - 2026-09-02 - the reference footing reproduces its pinned sls.pm / as_x / as_y / vcx; every mark measured on prokon-automation.exe
# ---
# The site engineer wants one row per foundation: mark, size, depth, level,
# reinforcement, and the bearing pressure to check against the trial pit.
# CSV, because it opens in anything and imports into the setting-out
# spreadsheet without a conversation.
#
# This recipe also does the thing a schedule generator must do and is easy
# to skip: it SIZES each pad rather than reporting one, growing the plan
# and the depth until every check passes.
#
# ⚠ AND IT WRITES THE GOVERNING CHECK INTO THE SCHEDULE. A pad that is
# 0.99 of its bearing allowable and a pad that is 0.31 both read "OK", and
# the first one is the one that moves when the geotechnical report is
# revised. Recording which check governed, and by how much, is what turns
# a schedule into something you can re-use.

import csv
from pathlib import Path

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
ALLOWABLE = 175.0        # kPa, from the geotechnical report
FOUNDING_LEVEL = -1.80   # m relative to finished floor

# A 0.2 m step, because a pad is set out to the nearest 100 mm on site and
# a finer sweep spends engine calls on a precision nobody builds to. At
# 0.1 m this recipe took 131 s; at 0.2 m it takes about half that and
# produces the same schedule.
PLANS = tuple(1.2 + 0.2 * step for step in range(18))     # 1.2 to 4.6 m
DEPTHS = (0.40, 0.50, 0.60, 0.75, 0.90, 1.10)

# ── The columns to found ───────────────────────────────────────────────
# (mark, column m, SLS axial kN, Mx kNm, Hx kN)
COLUMNS = (
    ("F1", 0.30,  350.0,  10.0,  8.0),
    ("F2", 0.40,  620.0,  25.0, 15.0),
    ("F3", 0.40,  900.0,  40.0, 20.0),
    ("F4", 0.50, 1400.0,  60.0, 30.0),
    ("F5", 0.50, 1850.0,  85.0, 40.0),
    ("F6", 0.60, 2600.0, 120.0, 55.0),
)

print("FOUNDATION SCHEDULE TO CSV")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}")
print(f"  allowable bearing {ALLOWABLE:.0f} kPa, founding level "
      f"{FOUNDING_LEVEL:+.2f} m")

# ── The anchor ──────────────────────────────────────────────────────────
anchor = prokon.v5.pad_footing.analyse(
    design_code=CODE, a=2.5, b=2.5, yf=0.6, z=0.5,
    c1=0.4, d1=0.4, e1=0.0, f1=0.0, fcu=30.0, fy=450.0,
    allowable_bearing_pressure=200.0,
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
    bar_dia_x_top=12.0, bar_spacing_x_top=250.0,
    bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
    load_cases=[{"name": "LC1", "pa1": 600.0, "hx1": 30.0,
                 "mx1": 20.0, "lf1": 1.4}])["result"]
PINNED = (133.98908218356328, 409.45851380730784, 369.07602339181034,
          0.3568429018580138)
measured = (anchor["max_bearing_pressure_sls"],
            anchor["critical_uls"]["reinforcement"]["as_x"],
            anchor["critical_uls"]["reinforcement"]["as_y"],
            anchor["critical_uls"]["shear"]["vcx"])
print(f"\n  anchor: the golden 2.5 m footing")
print(f"    -> {'EXACT on all four pinned values' if measured == PINNED else 'DRIFTED'}")


def utilisations(result, allowable):
    """Every check as a utilisation, with 'not checked' kept distinct."""
    critical = result["critical_uls"]
    shear = critical["shear"]
    sls = critical["sls"]
    found = {
        "bearing": result["max_bearing_pressure_sls"] / allowable,
        "shear x": shear["vx"] / shear["vcx"] if shear["vcx"] else None,
        "shear y": shear["vy"] / shear["vcy"] if shear["vcy"] else None,
        # ⚠ vcp = 0 means the perimeter did not fit, so nothing was
        # checked. None, never 0/0.
        "punching": shear["vp"] / shear["vcp"] if shear["vcp"] else None,
    }
    # 999999.99 is the sentinel for "no destabilising action", not a factor.
    if sls["sf_ovt"] and sls["sf_ovt"] != 999999.99:
        found["overturning"] = 2.0 / sls["sf_ovt"]
    if sls["sf_sliding"] and sls["sf_sliding"] != 999999.99:
        found["sliding"] = 1.5 / sls["sf_sliding"]
    return found


def size_pad(column, axial, moment, horizontal):
    """The smallest pad that passes every check, or None."""
    for depth in DEPTHS:
        for plan in PLANS:
            result = prokon.v5.pad_footing.analyse(
                design_code=CODE, a=plan, b=plan, yf=depth,
                z=abs(FOUNDING_LEVEL) - depth,
                c1=column, d1=column, e1=0.0, f1=0.0,
                fcu=FCU, fy=FY,
                allowable_bearing_pressure=ALLOWABLE,
                friction=0.5,
                bar_dia_x_bot=16.0, bar_spacing_x_bot=150.0,
                bar_dia_y_bot=16.0, bar_spacing_y_bot=150.0,
                load_cases=[{"name": "SLS", "pa1": axial,
                             "mx1": moment, "hx1": horizontal,
                             "lf1": 1.45}])["result"]
            found = utilisations(result, ALLOWABLE)
            # A pad whose punching check never ran is not a passing pad.
            if found["punching"] is None:
                continue
            real = {name: value for name, value in found.items()
                    if value is not None}
            if all(value <= 1.0 for value in real.values()):
                governs = max(real, key=real.get)
                return plan, depth, result, governs, real[governs]
    return None


# ── Build the schedule ──────────────────────────────────────────────────
schedule = []
print(f"\n{'mark':<5} {'plan':>6} {'depth':>6} {'p sls':>8} {'/allow':>7} "
      f"{'as_x':>7} {'as_y':>7} {'governs':<12} {'at':>6}")
print("-" * 82)

for mark, column, axial, moment, horizontal in COLUMNS:
    sized = size_pad(column, axial, moment, horizontal)
    if sized is None:
        print(f"{mark:<5} nothing up to {PLANS[-1]:.1f} m x "
              f"{DEPTHS[-1]:.2f} m passes every check")
        schedule.append({
            "mark": mark, "plan_m": "", "depth_m": "",
            "founding_level_m": FOUNDING_LEVEL,
            "column_m": column, "sls_axial_kN": axial,
            "bearing_sls_kPa": "", "allowable_kPa": ALLOWABLE,
            "as_x_mm2_m": "", "as_y_mm2_m": "",
            "bottom_bars": "", "governing_check": "NONE PASSES",
            "governing_utilisation": "",
        })
        continue

    plan, depth, result, governs, utilisation = sized
    critical = result["critical_uls"]
    reinforcement = critical["reinforcement"]

    schedule.append({
        "mark": mark,
        "plan_m": round(plan, 2),
        "depth_m": round(depth, 2),
        "founding_level_m": FOUNDING_LEVEL,
        "column_m": column,
        "sls_axial_kN": axial,
        "bearing_sls_kPa": round(result["max_bearing_pressure_sls"], 1),
        "allowable_kPa": ALLOWABLE,
        "as_x_mm2_m": round(reinforcement["as_x"], 1),
        "as_y_mm2_m": round(reinforcement["as_y"], 1),
        "bottom_bars": "Y16@150 each way",
        "governing_check": governs,
        "governing_utilisation": round(utilisation, 3),
    })

    print(f"{mark:<5} {plan:>6.2f} {depth:>6.2f} "
          f"{result['max_bearing_pressure_sls']:>8.1f} "
          f"{result['max_bearing_pressure_sls'] / ALLOWABLE:>7.2f} "
          f"{reinforcement['as_x']:>7.0f} {reinforcement['as_y']:>7.0f} "
          f"{governs:<12} {utilisation:>6.2f}")

# ── The summary that makes the schedule re-usable ──────────────────────
print("-" * 82)
governing = {}
for row in schedule:
    if row["governing_check"]:
        governing[row["governing_check"]] = (
            governing.get(row["governing_check"], 0) + 1)
print(f"governing check across {len(schedule)} pads:")
for check, count in sorted(governing.items(), key=lambda item: -item[1]):
    print(f"   {check:<14} {count}")

tight = [row for row in schedule
         if row["governing_utilisation"] not in ("", None)
         and row["governing_utilisation"] > 0.9]
if tight:
    print(f"\npads above 0.90 utilisation - the ones that move if the")
    print(f"geotechnical allowable is revised down:")
    for row in tight:
        print(f"   {row['mark']}  {row['governing_check']} at "
              f"{row['governing_utilisation']:.3f}")
else:
    print(f"\nno pad is above 0.90 utilisation - there is room in all of them")

concrete = sum(row["plan_m"] ** 2 * row["depth_m"] for row in schedule
               if row["plan_m"] != "")
print(f"\ntotal concrete in the pads: {concrete:.2f} m3")

# ── Write it, and read it back ─────────────────────────────────────────
FIELDS = ("mark", "plan_m", "depth_m", "founding_level_m", "column_m",
          "sls_axial_kN", "bearing_sls_kPa", "allowable_kPa",
          "as_x_mm2_m", "as_y_mm2_m", "bottom_bars", "governing_check",
          "governing_utilisation")
output = Path("foundation_schedule.csv")
with open(output, "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(schedule)

with open(output, newline="", encoding="utf-8") as handle:
    read_back = list(csv.DictReader(handle))
print(f"\nWritten: {output.resolve()}")
print(f"  {len(read_back)} row(s) written and re-read, "
      f"{'headers match' if list(read_back[0]) == list(FIELDS) else 'HEADERS DIFFER'}")
print(f"  first row: {read_back[0]['mark']} at "
      f"{read_back[0]['plan_m']} m, {read_back[0]['governing_check']} "
      f"{read_back[0]['governing_utilisation']}")

print()
print("The governing_check column is the one that earns its place. Six pads")
print("all reading 'OK' tell you nothing about which one to revisit when the")
print("ground turns out worse than the report said.")
