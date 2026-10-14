# ---
# Example:  Built-in desktop example - Double Column
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (Base.exe 5.3.8.0, Ver W5.3.08 - 04 Aug 2026); no differences; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Double Column"
# (a 6 x 3 m combined footing under two columns, two load cases), run from Python. The engine reads the desktop's save file,
# analyses it, and every result is printed beside the number the desktop
# prints on its calcsheet.
#
# To see the match for yourself: open TwoColumnExample-W5.3.08.C15 (beside this script) in
# PROKON Pad Footing, run the design, and compare the calcsheet rows named in
# the "Calcsheet" column below.
#
# The desktop figures were read from the desktop's own calcsheet export of
# this file (TwoColumnExample-W5.3.08-all-load-cases.json, Base.exe 5.3.8.0 "Ver W5.3.08 - 04 Aug 2026", 2026-09-09),
# as transcribed into the C15 repository's desktop-parity.json
# (entry genuine-twocolumn-2026-09-09). A value matches when it agrees to the number of
# decimals the calcsheet prints.
#
# load_file warns that the file's bending-schedule "Suggested" column and
# column-parameter grid are not read. Neither is an input to any result
# compared here, so no extra input is passed to analyse.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "TwoColumnExample-W5.3.08.C15")

# -- Load the desktop save file and analyse exactly what it holds ---------
loaded = prokon.v5.pad_footing.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.pad_footing.analyse(**loaded["inputs"])["result"]
cases = {lc["index"]: lc for lc in result["load_cases"]}

print(f"Example     : Double Column  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Load cases  : {len(cases)}\n")

# -- Desktop calcsheet values, at the precision the calcsheet prints ------
# (load case, calcsheet row, calcsheet section, desktop value, decimals shown,
#  result group, result field)
rows = [
    # Load case 1
    (1, 'Soil pressure (ULS) (kN/m2)'       , 'Soil pressure',   511.95, 2, 'uls', 'pm'),
    (1, 'Soil pressure (SLS) (kN/m2)'       , 'Soil pressure',   325.05, 2, 'sls', 'pm'),
    (1, 'SF overturning (ULS)'              , 'Stability'    ,     2.65, 2, 'uls', 'sf_ovt'),
    (1, 'SF overturning (SLS)'              , 'Stability'    ,     2.73, 2, 'sls', 'sf_ovt'),
    (1, 'Safety Factor slip (ULS)'          , 'Stability'    ,    33.18, 2, 'uls', 'sf_sliding'),
    (1, 'Safety Factor slip (SLS)'          , 'Stability'    ,    37.14, 2, 'sls', 'sf_sliding'),
    (1, 'Design moment X (kNm/m)'           , 'Bottom (ULS)' ,   143.79, 2, 'reinforcement', 'mdes_x'),
    (1, 'Reinforcement X (mm2/m)'           , 'Bottom (ULS)' ,      455, 0, 'reinforcement', 'as_x'),
    (1, 'Design moment Y (kNm/m)'           , 'Bottom (ULS)' ,    127.4, 1, 'reinforcement', 'mdes_y'),
    (1, 'Reinforcement Y (mm2/m)'           , 'Bottom (ULS)' ,      408, 0, 'reinforcement', 'as_y'),
    (1, 'Design moment X (kNm/m)'           , 'Top (ULS)'    ,  -248.76, 2, 'reinforcement', 'mneg_x'),
    (1, 'Reinforcement X (mm2/m)'           , 'Top (ULS)'    ,      787, 0, 'reinforcement', 'ac_x'),
    (1, 'Design moment Y (kNm/m)'           , 'Top (ULS)'    ,   -67.57, 2, 'reinforcement', 'mneg_y'),
    (1, 'Reinforcement Y (mm2/m)'           , 'Top (ULS)'    ,      216, 0, 'reinforcement', 'ac_y'),
    (1, 'Linear Shear X (MPa)'              , 'Shear'        ,    0.015, 3, 'shear', 'vx'),
    (1, 'Linear Shear Y (MPa)'              , 'Shear'        ,      0.0, 1, 'shear', 'vy'),
    (1, 'Punching Shear (MPa)'              , 'Shear'        ,    0.105, 3, 'shear', 'vp'),
    (1, 'vc (MPa)'                          , 'Shear'        ,    0.357, 3, 'shear', 'vcp'),
    (1, 'SLS Moment X (kNm/m)'              , 'Bottom (SLS)' ,    91.14, 2, 'reinforcement', 'mdes_x_sls'),
    (1, 'SLS Moment Y (kNm/m)'              , 'Bottom (SLS)' ,    81.22, 2, 'reinforcement', 'mdes_y_sls'),
    (1, 'Crack width X (mm)'                , 'Bottom (SLS)' ,      0.0, 1, 'crack_widths', 'bottom_x'),
    (1, 'Crack width Y (mm)'                , 'Bottom (SLS)' ,      0.0, 1, 'crack_widths', 'bottom_y'),
    (1, 'Crack width X (mm)'                , 'Top (SLS)'    ,      0.0, 1, 'crack_widths', 'top_x'),
    (1, 'Crack width Y (mm)'                , 'Top (SLS)'    ,      0.0, 1, 'crack_widths', 'top_y'),
    # Load case 2
    (2, 'Soil pressure (ULS) (kN/m2)'       , 'Soil pressure',   284.64, 2, 'uls', 'pm'),
    (2, 'Soil pressure (SLS) (kN/m2)'       , 'Soil pressure',   187.33, 2, 'sls', 'pm'),
    (2, 'SF overturning (ULS)'              , 'Stability'    ,    12.22, 2, 'uls', 'sf_ovt'),
    (2, 'SF overturning (SLS)'              , 'Stability'    ,    12.55, 2, 'sls', 'sf_ovt'),
    (2, 'Safety Factor slip (ULS)'          , 'Stability'    ,    73.46, 2, 'uls', 'sf_sliding'),
    (2, 'Safety Factor slip (SLS)'          , 'Stability'    ,    83.94, 2, 'sls', 'sf_sliding'),
    (2, 'Design moment X (kNm/m)'           , 'Bottom (ULS)' ,   124.43, 2, 'reinforcement', 'mdes_x'),
    (2, 'Reinforcement X (mm2/m)'           , 'Bottom (ULS)' ,      394, 0, 'reinforcement', 'as_x'),
    (2, 'Design moment Y (kNm/m)'           , 'Bottom (ULS)' ,   114.53, 2, 'reinforcement', 'mdes_y'),
    (2, 'Reinforcement Y (mm2/m)'           , 'Bottom (ULS)' ,      367, 0, 'reinforcement', 'as_y'),
    (2, 'Design moment X (kNm/m)'           , 'Top (ULS)'    ,   -199.8, 1, 'reinforcement', 'mneg_x'),
    (2, 'Reinforcement X (mm2/m)'           , 'Top (ULS)'    ,      632, 0, 'reinforcement', 'ac_x'),
    (2, 'Design moment Y (kNm/m)'           , 'Top (ULS)'    ,   -54.27, 2, 'reinforcement', 'mneg_y'),
    (2, 'Reinforcement Y (mm2/m)'           , 'Top (ULS)'    ,      174, 0, 'reinforcement', 'ac_y'),
    (2, 'Linear Shear X (MPa)'              , 'Shear'        ,    0.044, 3, 'shear', 'vx'),
    (2, 'Linear Shear Y (MPa)'              , 'Shear'        ,      0.0, 1, 'shear', 'vy'),
    (2, 'Punching Shear (MPa)'              , 'Shear'        ,     0.08, 2, 'shear', 'vp'),
    (2, 'vc (MPa)'                          , 'Shear'        ,    0.357, 3, 'shear', 'vcp'),
    (2, 'SLS Moment X (kNm/m)'              , 'Bottom (SLS)' ,    78.13, 2, 'reinforcement', 'mdes_x_sls'),
    (2, 'SLS Moment Y (kNm/m)'              , 'Bottom (SLS)' ,    71.91, 2, 'reinforcement', 'mdes_y_sls'),
    (2, 'Crack width X (mm)'                , 'Bottom (SLS)' ,      0.0, 1, 'crack_widths', 'bottom_x'),
    (2, 'Crack width Y (mm)'                , 'Bottom (SLS)' ,      0.0, 1, 'crack_widths', 'bottom_y'),
    (2, 'Crack width X (mm)'                , 'Top (SLS)'    ,      0.0, 1, 'crack_widths', 'top_x'),
    (2, 'Crack width Y (mm)'                , 'Top (SLS)'    ,      0.0, 1, 'crack_widths', 'top_y'),
]

# No differences are recorded for this file: the desktop-parity record
# compares every row above and finds none divergent.
KNOWN_DIFFERENCES = {}

print(f"{'Case':4} {'Result':30} {'Calcsheet':12} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 82)
matched = known = differed = 0
for case, label, section, desktop, dp, group, field in rows:
    script = cases[case][group][field]
    if round(script, dp) == round(desktop, dp):
        verdict, matched = "MATCH", matched + 1
    elif (case, label) in KNOWN_DIFFERENCES:
        verdict, known = "known difference: " + KNOWN_DIFFERENCES[(case, label)], known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{case:<4} {label:30} {section:12} {desktop:>10.{dp}f} {script:>10.{dp}f}  {verdict}")

print("-" * 82)
print(f"{matched} of {len(rows)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
