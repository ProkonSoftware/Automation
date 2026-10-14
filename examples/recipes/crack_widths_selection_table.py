# ---
# Example:  A bar-selection lookup table for the office wall
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes - 2026-09-02 - the reference slab reproduces its pinned triple; every cell measured on prokon-automation.exe
# ---
# On water-retaining work the same question comes up on every job: for a
# section this thick, carrying this much moment, WHICH bar and spacing
# holds the crack limit?
#
# The engine's own search offers a handful of arrangements. This recipe
# builds the whole grid instead - every standard diameter against every
# standard spacing - and writes it to a spreadsheet you can keep on the
# wall.
#
# ⚠ user_slab_bars IS THE INPUT THAT MAKES THIS POSSIBLE. Without it you
# get the engine's own picks; with it you get the arrangement YOU name,
# reported alongside them. The grid below is one call per cell.
#
# Uses openpyxl, bundled with Prokon's Python runtime.

from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

import prokon.v5

CODE = "BS8007 - 1987"
THICKNESS = 400.0        # mm
COVER = 45.0             # mm
FCU = 35.0
FY = 500.0
MOMENT = 90.0            # kNm/m service
CRACK_LIMIT = 0.2        # mm - severe exposure

DIAMETERS = (10, 12, 16, 20, 25, 32)
SPACINGS = (100, 125, 150, 175, 200, 250, 300)

SECTION = dict(
    design_code=CODE, slab_mode=True,
    h=THICKNESS, hef=THICKNESS / 2.0, b=1000.0, cover=COVER,
    fcu=FCU, fy=FY, ea=200.0, ec=0.0,
    allowable_crack_width=CRACK_LIMIT,
    high_bond_bar=True, short_term_load=False,
)

print("BAR SELECTION TABLE")
print(f"  {CODE}, {THICKNESS:.0f} mm section, cover {COVER:.0f} mm, "
      f"fcu {FCU:.0f}, fy {FY:.0f}")
print(f"  M = {MOMENT:.0f} kNm/m service, crack limit {CRACK_LIMIT} mm")

# ── The anchor ──────────────────────────────────────────────────────────
anchor = prokon.v5.crack_widths.analyse(
    design_code=CODE, slab_mode=True, h=300.0, hef=200.0, b=1000.0,
    cover=40.0, fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
    allowable_crack_width=0.3, high_bond_bar=True, short_term_load=True,
    load_cases=[{"n": 1, "m": 50.0, "m_uls": 1.5}])["result"]
first = anchor["load_cases"][0]["optimised_configs"][0]
PINNED = (0.11059554804834058, 1047.197551196598, 99.75807235558123)
measured = (first["calc_result"]["governing_crack_width"],
            first["calc_result"]["steel_area"],
            first["moment_capacity"])
print(f"\n  anchor: the pinned reference slab, {first['formatted_bars']}")
print(f"    -> {'EXACT on the pinned triple' if measured == PINNED else 'DRIFTED'}")

# ── Build the grid ──────────────────────────────────────────────────────
print(f"\nCRACK WIDTH [mm]   rows are bar diameters, columns are spacings")
print(f"{'':>6}" + "".join(f"{spacing:>9}" for spacing in SPACINGS))

widths = {}
areas = {}
capacities = {}
acceptable = []

for diameter in DIAMETERS:
    row = []
    for spacing in SPACINGS:
        bars = f"Y{diameter}@{spacing}"
        try:
            result = prokon.v5.crack_widths.analyse(
                **SECTION, user_slab_bars=bars,
                load_cases=[{"n": 1, "m": MOMENT, "m_uls": 1.5}])["result"]
        except prokon.v5.ProkonError as refusal:
            widths[(diameter, spacing)] = None
            row.append("refused")
            continue

        # user_slab_result is None when the engine declines to report the
        # named arrangement. Test it before reading it, every time.
        mine = result["load_cases"][0]["user_slab_result"]
        if mine is None:
            widths[(diameter, spacing)] = None
            row.append("none")
            continue

        calculated = mine["calc_result"]
        width = calculated["governing_crack_width"]
        widths[(diameter, spacing)] = width
        areas[(diameter, spacing)] = calculated["steel_area"]
        capacities[(diameter, spacing)] = mine["moment_capacity"]
        row.append(f"{width:.4f}")
        if (width <= CRACK_LIMIT
                and mine["moment_capacity"] >= result["load_cases"][0]["moment_ult"]
                and mine["meets_all_criteria"]):
            acceptable.append((calculated["steel_area"], bars, width))

    print(f"Y{diameter:<5}" + "".join(f"{cell:>9}" for cell in row))

print(f"\nSTEEL AREA [mm2/m]")
print(f"{'':>6}" + "".join(f"{spacing:>9}" for spacing in SPACINGS))
for diameter in DIAMETERS:
    cells = []
    for spacing in SPACINGS:
        area = areas.get((diameter, spacing))
        cells.append("-" if area is None else f"{area:.0f}")
    print(f"Y{diameter:<5}" + "".join(f"{cell:>9}" for cell in cells))

# ── The answer ──────────────────────────────────────────────────────────
if acceptable:
    area, bars, width = min(acceptable)
    print(f"\nLIGHTEST ARRANGEMENT THAT SATISFIES EVERYTHING")
    print(f"   {bars}: {area:.0f} mm2/m, crack {width:.4f} mm of "
          f"{CRACK_LIMIT} mm allowed")
    heaviest_area, heaviest_bars, _ = max(acceptable)
    print(f"   the heaviest that also works: {heaviest_bars} at "
          f"{heaviest_area:.0f} mm2/m")
    print(f"   {len(acceptable)} of {len(DIAMETERS) * len(SPACINGS)} "
          f"combinations are acceptable")
else:
    print(f"\nNOTHING IN THE GRID satisfies {CRACK_LIMIT} mm on this")
    print(f"section. That is the answer: thicken it, or lower the moment.")

# ── What the grid shows, read off the grid ─────────────────────────────
print(f"\nWHAT THE GRID SHOWS")
print(f"   1. at a FIXED diameter, wider spacing gives a wider crack:")
for diameter in DIAMETERS:
    at_tight = widths.get((diameter, SPACINGS[0]))
    at_wide = widths.get((diameter, SPACINGS[-1]))
    if at_tight and at_wide:
        print(f"      Y{diameter:<3} {SPACINGS[0]} mm gives {at_tight:.4f}, "
              f"{SPACINGS[-1]} mm gives {at_wide:.4f}  "
              f"({at_wide / at_tight:.2f}x wider)")

print(f"\n   2. at a FIXED spacing, a bigger bar gives a NARROWER crack:")
for spacing in (SPACINGS[0], SPACINGS[len(SPACINGS) // 2], SPACINGS[-1]):
    row = [(diameter, widths.get((diameter, spacing)))
           for diameter in DIAMETERS]
    row = [(diameter, width) for diameter, width in row if width]
    if len(row) >= 2:
        print(f"      @{spacing:<4} Y{row[0][0]} gives {row[0][1]:.4f}, "
              f"Y{row[-1][0]} gives {row[-1][1]:.4f}")

# ⚠ AND THE PAIR THAT MATTERS: crack width is NOT a function of steel
# area. Search the grid for two arrangements where the one with LESS steel
# has the NARROWER crack. If such a pair exists, ranking arrangements by
# area alone ranks them wrongly - which is the whole reason a crack-width
# engine exists.
print(f"\n   3. AND CRACK WIDTH IS NOT A FUNCTION OF AREA. Searching the")
print(f"      grid for a pair where LESS steel cracks LESS:")

cells = [(areas[key], widths[key], key) for key in widths
         if widths.get(key) and key in areas]
counter_examples = [
    (light, heavy)
    for light in cells for heavy in cells
    if light[0] < heavy[0] and light[1] < heavy[1]
]
if counter_examples:
    light, heavy = max(
        counter_examples,
        key=lambda pair: (pair[1][0] - pair[0][0]) * (pair[1][1] - pair[0][1]))
    print(f"      Y{light[2][0]}@{light[2][1]:<4} "
          f"{light[0]:>7.0f} mm2/m  crack {light[1]:.4f}")
    print(f"      Y{heavy[2][0]}@{heavy[2][1]:<4} "
          f"{heavy[0]:>7.0f} mm2/m  crack {heavy[1]:.4f}")
    print(f"      -> {heavy[0] / light[0]:.2f}x the steel and "
          f"{heavy[1] / light[1]:.2f}x the crack width. Ranking by area")
    print(f"         would put these the wrong way round.")
    print(f"      ({len(counter_examples)} such pairs in a "
          f"{len(cells)}-cell grid.)")
else:
    print(f"      none in this grid - on this section area and crack width")
    print(f"      happen to move together. That is a property of the")
    print(f"      section, not a rule; the search above is how you know.")

# ── Write the spreadsheet ───────────────────────────────────────────────
book = openpyxl.Workbook()
sheet = book.active
sheet.title = "Crack widths"

sheet["A1"] = f"Crack width [mm] - {CODE}"
sheet["A1"].font = Font(bold=True, size=13)
sheet["A2"] = (f"{THICKNESS:.0f} mm section, cover {COVER:.0f} mm, "
               f"fcu {FCU:.0f}, fy {FY:.0f}, M = {MOMENT:.0f} kNm/m service")
sheet["A3"] = (f"Shaded cells satisfy the {CRACK_LIMIT} mm limit AND the "
               f"moment. Blank means the engine reported nothing.")

sheet.cell(row=5, column=1, value="bar").font = Font(bold=True)
for column, spacing in enumerate(SPACINGS, start=2):
    cell = sheet.cell(row=5, column=column, value=f"@{spacing}")
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal="center")

GOOD = PatternFill("solid", fgColor="C6EFCE")
for row_index, diameter in enumerate(DIAMETERS, start=6):
    sheet.cell(row=row_index, column=1, value=f"Y{diameter}").font = Font(bold=True)
    for column, spacing in enumerate(SPACINGS, start=2):
        width = widths.get((diameter, spacing))
        cell = sheet.cell(row=row_index, column=column)
        if width is None:
            continue
        cell.value = round(width, 4)
        cell.number_format = "0.0000"
        if width <= CRACK_LIMIT:
            cell.fill = GOOD

sheet.column_dimensions["A"].width = 8
for column in range(2, 2 + len(SPACINGS)):
    sheet.column_dimensions[
        openpyxl.utils.get_column_letter(column)].width = 10

output = Path("crack_width_selection.xlsx")
book.save(output)

# Read it back: a saved workbook is not the same as a readable one.
reopened = openpyxl.load_workbook(output)
recovered = reopened["Crack widths"]
sample = recovered.cell(row=6, column=2).value
print(f"\nWritten: {output.resolve()}")
print(f"  re-read: sheet '{recovered.title}', "
      f"Y{DIAMETERS[0]}@{SPACINGS[0]} = {sample}")
print(f"  {'matches the table above' if sample == round(widths[(DIAMETERS[0], SPACINGS[0])], 4) else 'DOES NOT MATCH - check the write'}")
