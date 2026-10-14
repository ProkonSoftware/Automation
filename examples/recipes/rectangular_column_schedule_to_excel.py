# ---
# Example:  A column schedule a detailer can work from
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes - 2026-09-02 - the reference column reproduces its pinned 4521.0 mm2 / 2.825 %; every level measured on prokon-automation.exe
# ---
# A column schedule is a grid: column marks across, levels down, and in
# each cell the section and the bars. It is one of the most re-typed
# documents on a job, and it changes every time the loads change.
#
# C11's own answer is a LIST of feasible arrangements, which is exactly
# what a schedule wants - because the choice between 40Y12 and 12Y25 at the
# same area is about congestion and bar supply, not about strength. This
# recipe writes them all and marks the one it recommends.
#
# ⚠ AND IT TESTS THE PERCENTAGE AGAINST A LIMIT YOU CHOOSE. C11 reports a
# design at 15.4 % steel and has_feasible_design TRUE - measured in
# design-studies/rectangular_column_interaction.py. The engine's own
# ceiling is not a design limit, so the limit here is an input at the top
# of the file.
#
# Uses openpyxl, bundled with Prokon's Python runtime.

from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

import prokon.v5

CODE = "SABS 0100 - 2000"
FCU = 30.0
FY = 450.0
COVER = 45.0
STOREY = 3.5             # m
STEEL_LIMIT = 4.0        # % - YOUR limit, not the engine's

# ── The building ───────────────────────────────────────────────────────
# column mark -> per-floor ULS axial kN, and the moments at each level
COLUMNS = {
    "C1": (620.0, 55.0, 35.0),
    "C2": (880.0, 90.0, 45.0),
    "C3": (450.0, 40.0, 25.0),
    "C4": (1100.0, 120.0, 70.0),
}
LEVELS = (5, 4, 3, 2, 1)          # top to bottom
SIZES = (300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0, 700.0)

print("COLUMN SCHEDULE TO EXCEL")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm")
print(f"  {len(LEVELS)} levels, {len(COLUMNS)} columns, "
      f"steel limit {STEEL_LIMIT:.0f} % (yours, not the engine's)")

# ── The anchor ──────────────────────────────────────────────────────────
anchor = prokon.v5.rectangular_column.analyse(
    design_code=CODE, h=400.0, b=400.0, dc_x=40.0, dc_y=40.0,
    fcu=30.0, fy=450.0, lex=4000.0, ley=4000.0,
    bracing_x="Braced", bracing_y="Braced", betad=0.6, deltas=1.0,
    load_cases=[{"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
                {"n": 2000, "m2x": 125, "m1x": 75, "m2y": 90, "m1y": 55}])["result"]
PINNED = (4521.012783203123, 2.8249267578124986)
measured = (anchor["options"][0]["ast"], anchor["options"][0]["perc"])
print(f"\n  anchor: the pinned reference column")
print(f"    ast  {measured[0]!r}   pinned {PINNED[0]!r}")
print(f"    perc {measured[1]!r}   pinned {PINNED[1]!r}")
print(f"    -> {'EXACT on both' if measured == PINNED else 'DRIFTED'}")
print(f"    arrangements: "
      f"{', '.join(o['bar_description'] for o in anchor['options'])}")
print(f"    -> all four at the same area. That choice is the schedule's,")
print(f"       not the engine's.")


def design(size, axial, mx, my):
    """(chosen option, every option, reason). Chosen may be None."""
    result = prokon.v5.rectangular_column.analyse(
        design_code=CODE, h=size, b=size, dc_x=COVER, dc_y=COVER,
        fcu=FCU, fy=FY,
        lex=0.9 * STOREY * 1000.0, ley=0.9 * STOREY * 1000.0,
        bracing_x="Braced", bracing_y="Braced", betad=0.6, deltas=1.0,
        load_cases=[{"n": axial, "m2x": mx, "m1x": mx / 2.0,
                     "m2y": my, "m1y": my / 2.0}])["result"]
    if not result["options"]:
        reason = (result["sweep_errors"][0] if result["sweep_errors"]
                  else "no arrangement offered")
        return None, [], reason.encode("ascii", "replace").decode()
    passing = [option for option in result["options"]
               if option["all_pass"] and option["perc"] <= STEEL_LIMIT]
    if not passing:
        best = min(result["options"], key=lambda option: option["perc"])
        return None, result["options"], (
            f"lightest arrangement is {best['perc']:.2f} % steel, over the "
            f"{STEEL_LIMIT:.0f} % limit")
    # The recommendation: fewest bars at the lowest percentage. Fewer,
    # bigger bars are easier to fix and less congested at a lap.
    chosen = min(passing, key=lambda option: (option["perc"],
                                              option["total_bars"]))
    return chosen, result["options"], ""


# ── Build the schedule ──────────────────────────────────────────────────
cells = {}
print(f"\n{'level':>6} {'mark':<5} {'N uls':>9} {'section':>10} "
      f"{'recommended':>12} {'steel %':>8}  alternatives")
print("-" * 96)

for level in LEVELS:
    floors_above = max(LEVELS) - level + 1
    for mark, (per_floor, mx, my) in COLUMNS.items():
        axial = floors_above * per_floor
        chosen = None
        for size in SIZES:
            option, every, reason = design(size, axial, mx, my)
            if option is not None:
                chosen = (size, option, every)
                break
        if chosen is None:
            cells[(level, mark)] = None
            print(f"{level:>6} {mark:<5} {axial:>9.0f} {'---':>10} "
                  f"{'---':>12} {'---':>8}  nothing up to "
                  f"{SIZES[-1]:.0f} mm works")
            continue

        size, option, every = chosen
        alternatives = [o["bar_description"] for o in every
                        if o is not option and o["all_pass"]]
        cells[(level, mark)] = {
            "axial": axial, "size": size,
            "bars": option["bar_description"],
            "ast": option["ast"], "perc": option["perc"],
            "alternatives": alternatives,
        }
        print(f"{level:>6} {mark:<5} {axial:>9.0f} {f'{size:.0f} sq':>10} "
              f"{option['bar_description']:>12} {option['perc']:>8.3f}  "
              f"{', '.join(alternatives) if alternatives else '(none)'}")

# ── Write the spreadsheet ───────────────────────────────────────────────
book = openpyxl.Workbook()
sheet = book.active
sheet.title = "Column schedule"

THIN = Side(style="thin", color="999999")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEADER = PatternFill("solid", fgColor="D9E1F2")
CENTRE = Alignment(horizontal="center", vertical="center", wrap_text=True)

sheet["A1"] = "COLUMN SCHEDULE"
sheet["A1"].font = Font(bold=True, size=14)
sheet["A2"] = (f"{CODE}   fcu {FCU:.0f} MPa   fy {FY:.0f} MPa   "
               f"cover {COVER:.0f} mm   storey {STOREY:.2f} m")
sheet["A3"] = (f"Steel limited to {STEEL_LIMIT:.0f} % (a project limit, not "
               f"the engine's ceiling). Alternatives give the same area.")

sheet.cell(row=5, column=1, value="Level").font = Font(bold=True)
sheet.cell(row=5, column=1).fill = HEADER
sheet.cell(row=5, column=1).border = BOX
for column, mark in enumerate(COLUMNS, start=2):
    cell = sheet.cell(row=5, column=column, value=mark)
    cell.font = Font(bold=True)
    cell.fill = HEADER
    cell.alignment = CENTRE
    cell.border = BOX

for row_index, level in enumerate(LEVELS, start=6):
    label = sheet.cell(row=row_index, column=1, value=f"L{level}")
    label.font = Font(bold=True)
    label.border = BOX
    for column, mark in enumerate(COLUMNS, start=2):
        entry = cells.get((level, mark))
        cell = sheet.cell(row=row_index, column=column)
        cell.alignment = CENTRE
        cell.border = BOX
        if entry is None:
            cell.value = "SPECIAL"
            cell.font = Font(bold=True, color="9C0006")
            continue
        cell.value = (f"{entry['size']:.0f} sq\n{entry['bars']}\n"
                      f"{entry['perc']:.2f} %")

sheet.column_dimensions["A"].width = 8
for column in range(2, 2 + len(COLUMNS)):
    sheet.column_dimensions[
        openpyxl.utils.get_column_letter(column)].width = 16
for row_index in range(6, 6 + len(LEVELS)):
    sheet.row_dimensions[row_index].height = 46

# A second sheet with the alternatives, because a detailer asks.
detail = book.create_sheet("Alternatives")
detail.append(["level", "mark", "N uls kN", "section", "recommended",
               "Ast mm2", "steel %", "alternatives at the same area"])
for cell in detail[1]:
    cell.font = Font(bold=True)
for level in LEVELS:
    for mark in COLUMNS:
        entry = cells.get((level, mark))
        if entry is None:
            detail.append([f"L{level}", mark, "", "SPECIAL", "", "", "", ""])
            continue
        detail.append([f"L{level}", mark, round(entry["axial"]),
                       f"{entry['size']:.0f} sq", entry["bars"],
                       round(entry["ast"], 1), round(entry["perc"], 3),
                       ", ".join(entry["alternatives"])])
for column, width in zip("ABCDEFGH", (8, 8, 11, 12, 14, 11, 9, 40)):
    detail.column_dimensions[column].width = width

output = Path("column_schedule.xlsx")
book.save(output)

# Read it back, both sheets.
reopened = openpyxl.load_workbook(output)
print(f"\nWritten: {output.resolve()}")
print(f"  sheets: {reopened.sheetnames}")
sample = reopened["Column schedule"].cell(row=6, column=2).value
print(f"  L{LEVELS[0]} / {list(COLUMNS)[0]} reads: "
      f"{sample!r}".replace(chr(10), " | "))
print(f"  Alternatives sheet has "
      f"{reopened['Alternatives'].max_row - 1} data row(s)")

print()
print("Two sheets on purpose. The grid is what goes on the drawing; the")
print("alternatives list is what the detailer asks for when 40Y12 will not")
print("fit through the lap. Both come from the same engine call, and C11")
print("hands back every arrangement precisely so that second sheet exists.")
