# ---
# Example:  General column — your first analysis
# Feature:  general_column (C13 General Column)
# Verified: yes — 2026-09-02 — case 1 matches the values pinned in the C13 test suite; exact on prokon-automation.exe
# ---
# Check a reinforced-concrete column for axial load and biaxial moments,
# straight from Python. Two things make this feature different from the
# single-section ones:
#
#   * the CROSS-SECTION is a list of drawing rows — any shape you can
#     outline, with the bars placed where you put them;
#   * the LOADING is a list of load cases — the engine checks them all
#     in one call and reports each one separately.

import prokon.v5

# A 400 x 400 column. "+" opens the solid outline, "L" draws its edges
# (the engine closes the contour itself). Each bar is a "+" at its
# centre followed by "B" with the diameter: four Y25 corner bars with
# 30 mm cover (42.5 mm to the bar centre). All in mm.
section = [
    {"code": "+", "x": 0,     "y": 0},
    {"code": "L", "x": 400,   "y": 0},
    {"code": "L", "x": 400,   "y": 400},
    {"code": "L", "x": 0,     "y": 400},
    {"code": "+", "x": 42.5,  "y": 42.5},  {"code": "B", "x": 25},
    {"code": "+", "x": 357.5, "y": 42.5},  {"code": "B", "x": 25},
    {"code": "+", "x": 357.5, "y": 357.5}, {"code": "B", "x": 25},
    {"code": "+", "x": 42.5,  "y": 357.5}, {"code": "B", "x": 25},
]

# Two load cases, checked together: axial in kN (compression positive),
# end moments in kNm. An omitted moment is zero — but a misspelt key is
# refused, never silently zeroed.
load_cases = [
    {"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50},
    {"axial": 2000, "moment_x_top": 90, "moment_y_top": 30,
                    "moment_x_bottom": 90, "moment_y_bottom": 30},
]

result = prokon.v5.general_column.analyse(
    design_code="BS8110 - 1997",  # spelled exactly as the desktop names it
    length=3.0,                   # column length [m] — metres, not mm
    fcu=30.0,                     # concrete strength [MPa]
    fy=450.0,                     # reinforcement yield strength [MPa]
    section=section,
    load_cases=load_cases,
    # braced=True, end_top="FullyFixed", end_bottom="FullyFixed" and
    # effective_length_factor=1.0 are the defaults, written out on the
    # feature page.
)["result"]

# What the engine read off your section rows:
print(f"Bars              {result['bar_count']}  "
      f"(As = {result['steel_area']:.0f} mm2, "
      f"{result['reinforcement_ratio']:.2f}% of "
      f"{result['concrete_area']:.0f} mm2)")          # 4 bars, 1963 mm2, 1.23%

# The verdict: has_feasible_design is genuinely the pass/fail — it is
# True only when every load case, at every position, has a capacity
# factor of at least 1.0.
print(f"Feasible design   {result['has_feasible_design']}")   # True
print(f"Governing case    LC{result['critical_load_case']} "
      f"at {result['critical_position']}")                    # LC2 at Bottom
print(f"Min capacity      {result['min_capacity_factor']:.3f}"
      f"  (utilisation {result['utilisation']:.3f})")         # 1.124 (0.890)

# Each load case reports separately — case 1's numbers are the same as
# they would be if it were analysed alone.
print("\ncase   factor   utilisation   governs at   short column")
for case in result["load_cases"]:
    print(f"LC{case['load_case']}    {case['min_capacity_factor']:6.3f}"
          f"   {1 / case['min_capacity_factor']:11.3f}"
          f"   {case['governing_position']:>10}"
          f"   {case['is_short_column']}")
# LC1 comes back at 2.179 — the value pinned against the desktop
# program's own design report in the C13 test suite. LC2 at 1.124.
