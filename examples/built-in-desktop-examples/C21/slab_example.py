# ---
# Example:  Built-in desktop example - Slab Example
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes - 2026-10-02 - every result checked against the desktop calcsheet export of this save file (CrWidth.exe 5.3.7.0, W5.3.07); Ro %, tension capacity and the Opt1/Opt2 bar arrangements chosen under the user-defined Ro critical differ as recorded in F-C21-1, F-C21-2 and F-C21-4 and are labelled as such; exact on prokon-automation.exe
# ---
# The desktop program's own Examples-menu case "Slab Example", run from Python.
# The engine reads the desktop's save file, analyses it, and every result is
# printed beside the number the desktop prints on its calcsheet.
# Slab mode: three load cases, user bars Y10@250, user-defined Ro critical 0.64 %.
#
# To see the match for yourself: open SlabExample-W5.3.07.C21 (beside this script) in
# PROKON Crack Widths, run the design, and compare each load case's output
# table: the four optimum bar columns Opt1-Opt4, the User column, and the
# fct / Ro critical / critical load case footer.
#
# The desktop figures come from the desktop's own calcsheet export of this
# file (W5.3.07 - 15 Jun 2026 (CrWidth.exe FileVersion 5.3.7.0, built 2026-08-17 15:32:56), run 2026-09-09), as read out of that export into the C21
# repository's dotnet/C21CrackWidths.Tests/ReferenceData/desktop-parity.json,
# entry "genuine-slab-example-2026-09-09" (export: DLL/VerificationExamples/desktop-parity-2026-09-09/SlabExample-W5.3.07.json).
# A value matches when it agrees to the number of decimals the calcsheet prints.
#
# load_file warns that "national_annex" is not stored in a .C21 file. It only
# matters for a Eurocode design; this example uses BS8007 - 1987, so nothing
# extra needs to be passed.

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "SlabExample-W5.3.07.C21")

# -- Load the desktop save file and analyse exactly what it holds ---------
loaded = prokon.v5.crack_widths.load_file(path=SAVE_FILE)["result"]
result = prokon.v5.crack_widths.analyse(**loaded["inputs"])["result"]

print(f"Example     : Slab Example  ({os.path.basename(SAVE_FILE)})")
print(f"Design code : {loaded['inputs']['design_code']}")
print(f"Load cases  : {result['load_case_count']}\n")

# -- Desktop calcsheet values, exactly as the calcsheet prints them -------
# (load case, column, quantity, desktop as printed, recorded finding or None)
# A finding id marks a difference recorded in desktop-parity.json.
DESKTOP = [
    (1, 'Footer' , 'Concrete fct (MPa)'          , '1.3'        , None),
    (1, 'Footer' , 'Ro critical (%)'             , '0.64'       , None),
    (1, 'Footer' , 'Critical load case'          , '1'          , None),
    (1, 'Opt1'   , 'bars'                        , 'Y10@100'    , 'F-C21-4'),
    (1, 'Opt1'   , 'crackWidthCombined'          , '0.16'       , 'F-C21-4'),
    (1, 'Opt1'   , 'crackWidthT1Only'            , '0.06'       , 'F-C21-4'),
    (1, 'Opt1'   , 'crackWidthT1PlusT2'          , '0.16'       , 'F-C21-4'),
    (1, 'Opt1'   , 'steelArea'                   , '785'        , 'F-C21-4'),
    (1, 'Opt1'   , 'reinforcementRatioPercent'   , '0.63'       , 'F-C21-1'),
    (1, 'Opt1'   , 'steelStress'                 , '155'        , 'F-C21-4'),
    (1, 'Opt1'   , 'momentCapacity'              , '58.7'       , 'F-C21-4'),
    (1, 'Opt1'   , 'tensionCapacity'             , '51.1'       , 'F-C21-2'),
    (1, 'Opt2'   , 'bars'                        , 'Y16@200'    , None),
    (1, 'Opt2'   , 'crackWidthCombined'          , '0.2'        , None),
    (1, 'Opt2'   , 'crackWidthT1Only'            , '0.08'       , None),
    (1, 'Opt2'   , 'crackWidthT1PlusT2'          , '0.2'        , None),
    (1, 'Opt2'   , 'steelArea'                   , '1005'       , None),
    (1, 'Opt2'   , 'reinforcementRatioPercent'   , '0.8'        , 'F-C21-1'),
    (1, 'Opt2'   , 'steelStress'                 , '124'        , None),
    (1, 'Opt2'   , 'momentCapacity'              , '74.1'       , None),
    (1, 'Opt2'   , 'tensionCapacity'             , '64.5'       , 'F-C21-2'),
    (1, 'Opt3'   , 'bars'                        , 'Y25@300'    , None),
    (1, 'Opt3'   , 'crackWidthCombined'          , '0.18'       , None),
    (1, 'Opt3'   , 'crackWidthT1Only'            , '0.08'       , None),
    (1, 'Opt3'   , 'crackWidthT1PlusT2'          , '0.19'       , None),
    (1, 'Opt3'   , 'steelArea'                   , '1636'       , None),
    (1, 'Opt3'   , 'reinforcementRatioPercent'   , '1.31'       , 'F-C21-1'),
    (1, 'Opt3'   , 'steelStress'                 , '81'         , None),
    (1, 'Opt3'   , 'momentCapacity'              , '118.1'      , None),
    (1, 'Opt3'   , 'tensionCapacity'             , '102.7'      , 'F-C21-2'),
    (1, 'Opt4'   , 'bars'                        , 'Y40@500'    , None),
    (1, 'Opt4'   , 'crackWidthCombined'          , '0.17'       , None),
    (1, 'Opt4'   , 'crackWidthT1Only'            , '0.08'       , None),
    (1, 'Opt4'   , 'crackWidthT1PlusT2'          , '0.2'        , None),
    (1, 'Opt4'   , 'steelArea'                   , '2513'       , None),
    (1, 'Opt4'   , 'reinforcementRatioPercent'   , '2.01'       , 'F-C21-1'),
    (1, 'Opt4'   , 'steelStress'                 , '56'         , None),
    (1, 'Opt4'   , 'momentCapacity'              , '175.0'      , None),
    (1, 'Opt4'   , 'tensionCapacity'             , '152.2'      , 'F-C21-2'),
    (1, 'User'   , 'bars'                        , 'Y10@250'    , None),
    (1, 'User'   , 'crackWidthCombined'          , '0.44'       , None),
    (1, 'User'   , 'crackWidthT1Only'            , '0.16'       , None),
    (1, 'User'   , 'crackWidthT1PlusT2'          , '0.4'        , None),
    (1, 'User'   , 'steelArea'                   , '314'        , None),
    (1, 'User'   , 'reinforcementRatioPercent'   , '0.25'       , 'F-C21-1'),
    (1, 'User'   , 'steelStress'                 , '371'        , None),
    (1, 'User'   , 'momentCapacity'              , '23.5'       , None),
    (1, 'User'   , 'tensionCapacity'             , '20.4'       , 'F-C21-2'),
    (2, 'Footer' , 'Concrete fct (MPa)'          , '1.3'        , None),
    (2, 'Footer' , 'Ro critical (%)'             , '0.64'       , None),
    (2, 'Footer' , 'Critical load case'          , '1'          , None),
    (2, 'Opt1'   , 'bars'                        , 'Y10@125'    , 'F-C21-4'),
    (2, 'Opt1'   , 'crackWidthCombined'          , '0.11'       , 'F-C21-4'),
    (2, 'Opt1'   , 'crackWidthT1Only'            , '0.08'       , 'F-C21-4'),
    (2, 'Opt1'   , 'crackWidthT1PlusT2'          , '0.18'       , 'F-C21-4'),
    (2, 'Opt1'   , 'steelArea'                   , '628'        , 'F-C21-4'),
    (2, 'Opt1'   , 'reinforcementRatioPercent'   , '0.5'        , None),
    (2, 'Opt1'   , 'steelStress'                 , '100'        , 'F-C21-4'),
    (2, 'Opt1'   , 'momentCapacity'              , '41.7'       , 'F-C21-4'),
    (2, 'Opt1'   , 'tensionCapacity'             , '97.4'       , 'F-C21-2'),
    (2, 'Opt2'   , 'bars'                        , 'Y16@200'    , None),
    (2, 'Opt2'   , 'crackWidthCombined'          , '0.11'       , None),
    (2, 'Opt2'   , 'crackWidthT1Only'            , '0.08'       , None),
    (2, 'Opt2'   , 'crackWidthT1PlusT2'          , '0.18'       , None),
    (2, 'Opt2'   , 'steelArea'                   , '1005'       , None),
    (2, 'Opt2'   , 'reinforcementRatioPercent'   , '0.8'        , 'F-C21-1'),
    (2, 'Opt2'   , 'steelStress'                 , '65'         , None),
    (2, 'Opt2'   , 'momentCapacity'              , '66.0'       , None),
    (2, 'Opt2'   , 'tensionCapacity'             , '154.0'      , 'F-C21-2'),
    (2, 'Opt3'   , 'bars'                        , 'Y25@300'    , None),
    (2, 'Opt3'   , 'crackWidthCombined'          , '0.11'       , None),
    (2, 'Opt3'   , 'crackWidthT1Only'            , '0.08'       , None),
    (2, 'Opt3'   , 'crackWidthT1PlusT2'          , '0.17'       , None),
    (2, 'Opt3'   , 'steelArea'                   , '1636'       , None),
    (2, 'Opt3'   , 'reinforcementRatioPercent'   , '1.31'       , 'F-C21-1'),
    (2, 'Opt3'   , 'steelStress'                 , '42'         , None),
    (2, 'Opt3'   , 'momentCapacity'              , '105.5'      , None),
    (2, 'Opt3'   , 'tensionCapacity'             , '246.1'      , 'F-C21-2'),
    (2, 'Opt4'   , 'bars'                        , 'Y40@500'    , None),
    (2, 'Opt4'   , 'crackWidthCombined'          , '0.12'       , None),
    (2, 'Opt4'   , 'crackWidthT1Only'            , '0.08'       , None),
    (2, 'Opt4'   , 'crackWidthT1PlusT2'          , '0.18'       , None),
    (2, 'Opt4'   , 'steelArea'                   , '2513'       , None),
    (2, 'Opt4'   , 'reinforcementRatioPercent'   , '2.01'       , 'F-C21-1'),
    (2, 'Opt4'   , 'steelStress'                 , '29'         , None),
    (2, 'Opt4'   , 'momentCapacity'              , '157.1'      , None),
    (2, 'Opt4'   , 'tensionCapacity'             , '366.6'      , 'F-C21-2'),
    (2, 'User'   , 'bars'                        , 'Y10@250'    , None),
    (2, 'User'   , 'crackWidthCombined'          , '0.2'        , None),
    (2, 'User'   , 'crackWidthT1Only'            , '0.16'       , None),
    (2, 'User'   , 'crackWidthT1PlusT2'          , '0.36'       , None),
    (2, 'User'   , 'steelArea'                   , '314'        , None),
    (2, 'User'   , 'reinforcementRatioPercent'   , '0.25'       , 'F-C21-1'),
    (2, 'User'   , 'steelStress'                 , '194'        , None),
    (2, 'User'   , 'momentCapacity'              , '20.9'       , None),
    (2, 'User'   , 'tensionCapacity'             , '48.7'       , 'F-C21-2'),
    (3, 'Footer' , 'Concrete fct (MPa)'          , '1.3'        , None),
    (3, 'Footer' , 'Ro critical (%)'             , '0.64'       , None),
    (3, 'Footer' , 'Critical load case'          , '1'          , None),
    (3, 'Opt1'   , 'bars'                        , 'Y10@175'    , 'F-C21-4'),
    (3, 'Opt1'   , 'crackWidthCombined'          , '0.15'       , 'F-C21-4'),
    (3, 'Opt1'   , 'crackWidthT1Only'            , '0.07'       , 'F-C21-4'),
    (3, 'Opt1'   , 'crackWidthT1PlusT2'          , '0.15'       , 'F-C21-4'),
    (3, 'Opt1'   , 'steelArea'                   , '449'        , 'F-C21-4'),
    (3, 'Opt1'   , 'reinforcementRatioPercent'   , '0.36'       , 'F-C21-1'),
    (3, 'Opt1'   , 'steelStress'                 , '206'        , 'F-C21-4'),
    (3, 'Opt1'   , 'momentCapacity'              , '35.2'       , 'F-C21-4'),
    (3, 'Opt1'   , 'tensionCapacity'             , '15.6'       , 'F-C21-2'),
    (3, 'Opt2'   , 'bars'                        , 'Y16@350'    , 'F-C21-4'),
    (3, 'Opt2'   , 'crackWidthCombined'          , '0.18'       , 'F-C21-4'),
    (3, 'Opt2'   , 'crackWidthT1Only'            , '0.08'       , 'F-C21-4'),
    (3, 'Opt2'   , 'crackWidthT1PlusT2'          , '0.19'       , 'F-C21-4'),
    (3, 'Opt2'   , 'steelArea'                   , '574'        , 'F-C21-4'),
    (3, 'Opt2'   , 'reinforcementRatioPercent'   , '0.46'       , 'F-C21-1'),
    (3, 'Opt2'   , 'steelStress'                 , '165'        , 'F-C21-4'),
    (3, 'Opt2'   , 'momentCapacity'              , '44.4'       , 'F-C21-4'),
    (3, 'Opt2'   , 'tensionCapacity'             , '19.8'       , 'F-C21-2'),
    (3, 'Opt3'   , 'bars'                        , 'Y25@500'    , None),
    (3, 'Opt3'   , 'crackWidthCombined'          , '0.16'       , None),
    (3, 'Opt3'   , 'crackWidthT1Only'            , '0.08'       , None),
    (3, 'Opt3'   , 'crackWidthT1PlusT2'          , '0.17'       , None),
    (3, 'Opt3'   , 'steelArea'                   , '982'        , None),
    (3, 'Opt3'   , 'reinforcementRatioPercent'   , '0.79'       , 'F-C21-1'),
    (3, 'Opt3'   , 'steelStress'                 , '102'        , None),
    (3, 'Opt3'   , 'momentCapacity'              , '74.3'       , None),
    (3, 'Opt3'   , 'tensionCapacity'             , '33.0'       , 'F-C21-2'),
    (3, 'Opt4'   , 'bars'                        , 'Y40@500'    , None),
    (3, 'Opt4'   , 'crackWidthCombined'          , '0.1'        , None),
    (3, 'Opt4'   , 'crackWidthT1Only'            , '0.05'       , None),
    (3, 'Opt4'   , 'crackWidthT1PlusT2'          , '0.11'       , None),
    (3, 'Opt4'   , 'steelArea'                   , '2513'       , None),
    (3, 'Opt4'   , 'reinforcementRatioPercent'   , '2.01'       , 'F-C21-1'),
    (3, 'Opt4'   , 'steelStress'                 , '44'         , None),
    (3, 'Opt4'   , 'momentCapacity'              , '183.3'      , None),
    (3, 'Opt4'   , 'tensionCapacity'             , '81.5'       , 'F-C21-2'),
    (3, 'User'   , 'bars'                        , 'Y10@250'    , None),
    (3, 'User'   , 'crackWidthCombined'          , '0.21'       , None),
    (3, 'User'   , 'crackWidthT1Only'            , '0.1'        , None),
    (3, 'User'   , 'crackWidthT1PlusT2'          , '0.21'       , None),
    (3, 'User'   , 'steelArea'                   , '314'        , None),
    (3, 'User'   , 'reinforcementRatioPercent'   , '0.25'       , 'F-C21-1'),
    (3, 'User'   , 'steelStress'                 , '290'        , None),
    (3, 'User'   , 'momentCapacity'              , '24.6'       , None),
    (3, 'User'   , 'tensionCapacity'             , '11.0'       , 'F-C21-2'),
]
REASONS = {
    'F-C21-1': 'Ro is a different ratio on each side: the desktop divides the steel by the surface zone hef, the engine by the effective depth',
    'F-C21-2': 'the desktop calcsheet prints twice the tension capacity the engine returns (exactly a factor of two)',
    'F-C21-4': 'the minimum-steel check uses the user-defined Ro critical 0.64 % here but a stale 0.35 % on the desktop, so a different bar arrangement is chosen',
}


def column_result(case, column):
    if column == "User":
        return case["user_slab_result"] or case["user_beam_result"]
    return case["optimised_configs"][int(column[3:]) - 1]


def script_value(case, column, quantity):
    if quantity == "Critical load case":
        return result["critical_load_case"]
    if column == "Footer":
        calc = case["optimised_configs"][0]["calc_result"]
        if quantity == "Concrete fct (MPa)":
            return calc["concrete_tensile_strength"]
        return calc["critical_reinforcement_ratio"] * 100
    col = column_result(case, column)
    calc = col["calc_result"]
    return {
        "bars": col["formatted_bars"] + col["formatted_bars_secondary"],
        "crackWidthCombined": calc["crack_width"],
        "crackWidthT1Only": calc["crack_width_component_1"],
        "crackWidthT1PlusT2": calc["crack_width_component_2"],
        "steelArea": calc["steel_area"],
        "reinforcementRatioPercent": calc["reinforcement_ratio"],
        "steelStress": calc["steel_stress"],
        "momentCapacity": col["moment_capacity"],
        "tensionCapacity": col["tension_capacity"],
    }[quantity]


cases = {c["load_case_number"]: c for c in result["load_cases"]}

print(f"{'Result':38} {'Calcsheet':12} {'Desktop':>10} {'Script':>10}  Verdict")
print("-" * 100)
matched = known = differed = 0
for n, column, quantity, shown, finding in DESKTOP:
    script = script_value(cases[n], column, quantity)
    if quantity == "bars":
        script_shown = script
    else:
        dp = len(shown.split(".")[1]) if "." in shown else 0
        script_shown = f"{script:.{dp}f}"
    if script_shown == shown:
        verdict, matched = "MATCH", matched + 1
    elif finding:
        verdict, known = f"known difference ({finding}): {REASONS[finding]}", known + 1
    else:
        verdict, differed = "DIFFERS", differed + 1
    print(f"{column + ' ' + quantity:38} {'Load case ' + str(n):12} "
          f"{shown:>10} {script_shown:>10}  {verdict}")

print("-" * 100)
print(f"{matched} of {len(DESKTOP)} results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
