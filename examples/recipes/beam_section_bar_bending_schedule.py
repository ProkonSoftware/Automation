# ---
# Example:  A bar bending schedule, straight to CSV
# Feature:  beam_section (C22 Beam Section)
# Verified: yes - 2026-09-02 - the 300x500 BS8110 anchor reproduces the pinned mu/ast; every schedule row measured on prokon-automation.exe
# ---
# The deliverable at the end of a beam design is not a set of areas - it is
# a BAR BENDING SCHEDULE: bar mark, type, diameter, number, length, shape
# code, and a mass total for the quantity surveyor.
#
# C22 gives the arrangements. Turning them into a schedule is arithmetic
# plus your own detailing rules, and both are written out here so you can
# replace them with your practice's own.
#
# ⚠ THE LENGTHS AND SHAPE CODES ARE MINE, NOT THE ENGINE'S. C22 designs
# sections; it does not detail bars. Laps, anchorage and shape codes come
# from the detailing standard you work to - BS 8666 here - and they are
# assumptions this script makes visible rather than hides.

import csv
import math
from pathlib import Path

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
FYV = 450.0
COVER = 40.0
STEEL_DENSITY = 7850.0 / 1e9        # kg per mm3

# ── The beams to schedule ──────────────────────────────────────────────
# (mark, span m, bw, h, M kNm, V kN)
BEAMS = (
    ("B1", 6.0, 300.0, 500.0, 200.0, 100.0),
    ("B2", 5.0, 250.0, 450.0, 140.0,  85.0),
    ("B3", 7.5, 350.0, 600.0, 320.0, 150.0),
    ("B4", 4.5, 250.0, 400.0,  95.0,  70.0),
    ("B5", 9.0, 400.0, 750.0, 520.0, 210.0),
)

# BS 8666 anchorage and lap, as multiples of the bar diameter. YOUR
# standard goes here.
ANCHORAGE = 40          # bar diameters into the support
LAP = 40                # bar diameters
LINK_HOOK = 10          # bar diameters per hook, two hooks per link


def bars_from(description):
    """(count, diameter) from '5Y20'."""
    count, _, diameter = description.partition("Y")
    return int(count), float(diameter)


def links_from(description):
    """(legs, diameter, spacing) from '2Y10@350'."""
    head, _, spacing = description.partition("@")
    legs, _, diameter = head.partition("Y")
    return int(legs), float(diameter), float(spacing)


def mass(diameter, length_mm, count):
    """kg for a group of bars."""
    return (math.pi * diameter ** 2 / 4.0) * length_mm * count * STEEL_DENSITY


print("BAR BENDING SCHEDULE")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm")
print(f"  detailing: anchorage {ANCHORAGE}d, laps {LAP}d, "
      f"link hooks {LINK_HOOK}d each")

# ── The anchor ──────────────────────────────────────────────────────────
anchor = prokon.v5.beam_section.analyse(
    design_code=CODE, m=200.0, v=100.0, bw=300.0, h=500.0,
    dc_t=COVER, dc_b=COVER, dc_s=COVER, fcu=FCU, fy=FY, fyv=FYV)["result"]
PINNED = (295.18197048179997, 1287.32677061758)
measured = (anchor["mu"], anchor["ast"])
print(f"\n  anchor: B1's section is the pinned reference")
print(f"    mu  {measured[0]!r}   pinned {PINNED[0]!r}")
print(f"    ast {measured[1]!r}   pinned {PINNED[1]!r}")
print(f"    -> {'EXACT' if measured == PINNED else 'DRIFTED'}")

# ── Build the schedule ──────────────────────────────────────────────────
schedule = []
mark_number = 1

for member, span, width, depth, moment, shear in BEAMS:
    result = prokon.v5.beam_section.analyse(
        design_code=CODE, m=moment, v=shear, bw=width, h=depth,
        dc_t=COVER, dc_b=COVER, dc_s=COVER, fcu=FCU, fy=FY, fyv=FYV)["result"]

    tension = result["reinforcement"]["tension_bars"]
    links = result["reinforcement"]["shear_links"]

    if not tension:
        print(f"\n  {member}: the engine offered no tension arrangement - "
              f"detail by hand against Ast = {result['ast']:.0f} mm2")
        continue

    # The lightest arrangement that covers the required area. The engine's
    # own list is already area-sufficient, so the first is the lightest.
    count, diameter = bars_from(tension[0]["description"])
    # Straight bar, anchored both ends. Shape code 00 in BS 8666.
    bottom_length = span * 1000.0 + 2 * ANCHORAGE * diameter
    schedule.append({
        "member": member, "mark": f"{mark_number:02d}",
        "position": "bottom", "type": "Y", "diameter": diameter,
        "number": count, "length_mm": round(bottom_length),
        "shape": "00 (straight)",
        "mass_kg": round(mass(diameter, bottom_length, count), 2),
        "area_provided": round(tension[0]["area"], 1),
        "area_required": round(result["ast"], 1),
    })
    mark_number += 1

    # Nominal top steel, two bars, to carry the links. A detailing rule,
    # not an engine output.
    top_diameter = 12.0
    top_length = span * 1000.0 + 2 * ANCHORAGE * top_diameter
    schedule.append({
        "member": member, "mark": f"{mark_number:02d}",
        "position": "top (nominal)", "type": "Y", "diameter": top_diameter,
        "number": 2, "length_mm": round(top_length),
        "shape": "00 (straight)",
        "mass_kg": round(mass(top_diameter, top_length, 2), 2),
        "area_provided": round(2 * math.pi * top_diameter ** 2 / 4.0, 1),
        "area_required": 0.0,
    })
    mark_number += 1

    if links and links[0]["description"]:
        legs, link_diameter, spacing = links_from(links[0]["description"])
        # A closed link: the perimeter inside the cover, plus two hooks.
        perimeter = 2 * ((width - 2 * COVER) + (depth - 2 * COVER))
        link_length = perimeter + 2 * LINK_HOOK * link_diameter
        number = int(span * 1000.0 / spacing) + 1
        schedule.append({
            "member": member, "mark": f"{mark_number:02d}",
            "position": f"links @ {spacing:.0f}", "type": "Y",
            "diameter": link_diameter, "number": number,
            "length_mm": round(link_length), "shape": "51 (closed link)",
            "mass_kg": round(mass(link_diameter, link_length, number), 2),
            "area_provided": round(links[0]["area"], 4),
            "area_required": round(result["asv"], 4),
        })
        mark_number += 1

# ── Print it, then write it ────────────────────────────────────────────
FIELDS = ("member", "mark", "position", "type", "diameter", "number",
          "length_mm", "shape", "mass_kg", "area_provided", "area_required")

print(f"\n{'member':<7} {'mark':<5} {'position':<16} {'dia':>4} {'no':>4} "
      f"{'length':>8} {'shape':<16} {'mass kg':>8} {'prov':>9} {'req':>9}")
print("-" * 104)
for row in schedule:
    print(f"{row['member']:<7} {row['mark']:<5} {row['position']:<16} "
          f"{row['diameter']:>4.0f} {row['number']:>4} "
          f"{row['length_mm']:>8} {row['shape']:<16} "
          f"{row['mass_kg']:>8.2f} {row['area_provided']:>9} "
          f"{row['area_required']:>9}")

total = sum(row["mass_kg"] for row in schedule)
print("-" * 104)
print(f"{'TOTAL':<7} {'':<5} {'':<16} {'':>4} "
      f"{sum(row['number'] for row in schedule):>4} {'':>8} {'':<16} "
      f"{total:>8.2f} kg")

by_diameter = {}
for row in schedule:
    by_diameter[row["diameter"]] = (by_diameter.get(row["diameter"], 0.0)
                                    + row["mass_kg"])
print(f"\nmass by diameter, which is how steel is ordered:")
for diameter in sorted(by_diameter):
    print(f"   Y{diameter:.0f}  {by_diameter[diameter]:>8.2f} kg  "
          f"({100 * by_diameter[diameter] / total:.0f} %)")

output = Path("bar_bending_schedule.csv")
with open(output, "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(schedule)

# Read it back. A file that was written is not the same as a file that
# can be read, and this is one line.
with open(output, newline="", encoding="utf-8") as handle:
    read_back = list(csv.DictReader(handle))
print(f"\nWritten: {output.resolve()}")
print(f"  {len(read_back)} row(s) written and re-read, "
      f"{'headers match' if list(read_back[0]) == list(FIELDS) else 'HEADERS DIFFER'}")

print()
print("What the engine gave: areas, and the arrangements that cover them.")
print("What this script added: lengths, shape codes, bar marks and mass -")
print("all of it from the detailing rules at the top of the file. Change")
print("those to your practice's own and the schedule follows.")
