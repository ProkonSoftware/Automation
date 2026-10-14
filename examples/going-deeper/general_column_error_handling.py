# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  general_column (C13 General Column)
# Verified: yes — 2026-09-09 — behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "no_solution", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it — often the full list of allowed values
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT — or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. This feature gives you three
# things to branch on rather than one:
#
#   * the ordinary refusals — a typo, a missing input, a bad row;
#   * "no_solution", which is REAL here (section 7): the engine runs and
#     declines, on two everyday inputs;
#   * "timeout", which on this feature is a KNOWN ENGINE DEFECT and not a
#     slow machine — section 10, and it is the reason every C13 batch
#     wants a timeout set.
#
# And then the quiet half: sections 9a-9d are calls that SUCCEED while
# telling you something you must not take at face value.

import prokon.v5

SECTION = [                       # a 400 x 400 with four Y25 corner bars
    {"code": "+", "x": 0,     "y": 0},
    {"code": "L", "x": 400,   "y": 0},
    {"code": "L", "x": 400,   "y": 400},
    {"code": "L", "x": 0,     "y": 400},
    {"code": "+", "x": 42.5,  "y": 42.5},  {"code": "B", "x": 25},
    {"code": "+", "x": 357.5, "y": 42.5},  {"code": "B", "x": 25},
    {"code": "+", "x": 357.5, "y": 357.5}, {"code": "B", "x": 25},
    {"code": "+", "x": 42.5,  "y": 357.5}, {"code": "B", "x": 25},
]

GOOD = dict(
    design_code="BS8110 - 1997",
    length=3.0,                   # metres
    fcu=30.0, fy=450.0,           # MPa
    section=SECTION,
    load_cases=[{"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50}],
)


def printable(text):
    """Engine and hint wording, made safe to print on any console — see 3b."""
    return text.encode("ascii", "replace").decode("ascii")


def refusal(label, **overrides):
    """Call with GOOD + overrides, print the refusal, return it."""
    try:
        prokon.v5.general_column.analyse(**{**GOOD, **overrides})["result"]
    except prokon.v5.ProkonError as e:
        print(f"{label:<30} {e.category} / {e.code}")
        for line in printable(e.message).splitlines():
            print(f"      {line}")
        return e
    print(f"{label:<30} no refusal")
    return None


# --- 1. A typo in a choice value: category "invalid_input", with the whole
#        allowed list in .hints. Choice values are exact, INCLUDING capitals
#        — "bs8110 - 1997" is refused identically. C13's spellings are not
#        the other features' spellings, so read them off .hints:
try:
    prokon.v5.general_column.analyse(**{**GOOD, "design_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   all {len(e.hints)} design codes are in .hints: "
          f"{', '.join(e.hints[:3])}, ...")

# --- 2a. LEAVE AN ARGUMENT OUT and PYTHON refuses, before any engine
#         process is launched. analyse() takes real keyword-only
#         parameters, so a misspelled name is caught the same way -- and
#         Python usually suggests the one you meant:
#             analyse() got an unexpected keyword argument 'fcux'.
#             Did you mean 'fcu'?
#         Usually, not always: the suggestion is Python's own
#         edit-distance heuristic, and it gives up on a long enough
#         mangling.
for missing in ("fcu", "section"):
    try:
        prokon.v5.general_column.analyse(**{k: v for k, v in GOOD.items() if k != missing})["result"]
    except TypeError as e:
        print("\n2a) TypeError -- Python refused; no engine was launched")
        print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on. The
#         hint is the input's own description -- which for the two list
#         inputs is the whole vocabulary you needed in the first place:
for missing in ("fcu", "section"):
    incomplete = {**GOOD, missing: None}
    try:
        prokon.v5.general_column.analyse(**incomplete)["result"]
    except prokon.v5.ProkonError as e:
        print(f"\n2b) {e.category} / {e.code}")
        print(f"   {e.message}")
        print(f"   hint ({len(e.hints[0])} chars): {e.hints[0][:72]}"
              f"{'...' if len(e.hints[0]) > 72 else ''}")

# --- 3. THE TWO LIST INPUTS REFUSE BY ROW INDEX. `section` and
#        `load_cases` are read row by row, and a bad row is named — never
#        skipped, never defaulted. All of these are INVALID_INPUT with
#        .hints EMPTY: the sentence is the whole of the answer.
print()
for label, row in (
        ("mis-cased key",    {"code": "L", "X": 400, "y": 0}),
        ("no x at all",      {"code": "L", "y": 0}),
        ("unknown row code", {"code": "Z", "x": 400, "y": 0}),
        ("x as a string",    {"code": "L", "x": "four hundred", "y": 0})):
    rows = list(SECTION)
    rows[1] = row
    refusal(f"3) section, {label}", section=rows)

print()
for label, case in (
        ("misspelt member", {"axial": 1000, "moment_x_topp": 50}),
        ("no axial",        {"moment_x_top": 50})):
    refusal(f"3) load_cases, {label}", load_cases=[case])

# --- 3b. MIND YOUR CONSOLE. One of those four is not plain ASCII — the
#         "no x at all" sentence is written with a real em-dash, and a
#         Windows console on the default code page raises
#         UnicodeEncodeError the moment you print it raw. Fold anything
#         that came off the wire before printing it, as printable() does
#         (every message in this script goes through it):
rows = list(SECTION)
rows[1] = {"code": "L", "y": 0}
try:
    prokon.v5.general_column.analyse(**{**GOOD, "section": rows})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3b) plain ASCII as it stands? {e.message.isascii()} "
          f"- the '?' above stands in for one em-dash")

# --- 4. Two more codes, for two kinds of unreadable VALUE -- plus the
#        third case, which no longer reaches the engine at all: an input
#        this feature does not have is refused by PYTHON, because
#        analyse() declares one real parameter per input.
print()
refusal("4) braced='yes'", braced="yes")          # INPUT_VALUE_MALFORMED
refusal("4) length=None", length=None)            # UNSUPPORTED_INPUT_TYPE
try:
    prokon.v5.general_column.analyse(**GOOD, cover=30.0)["result"]
except TypeError as e:
    label = "4) an input C13 lacks"
    print(f"{label:<30} TypeError -- Python refused; no engine was launched")
    print(f"      {e}")

# --- 5. The model-level validator publishes EVERY finding, not the first.
#        One call, one exception, five sentences — fix them in one pass
#        instead of five round trips:
try:
    prokon.v5.general_column.analyse(
        design_code="BS8110 - 1997", length=0.0, fcu=0.0, fy=450.0,
        section=[], load_cases=[], national_annex="GB")["result"]
except prokon.v5.ProkonError as e:
    print(f"\n5) {e.category} / {e.code} - "
          f"{len(e.message.splitlines()) - 1} findings in one message")
    for line in e.message.splitlines():
        print(f"   {line}")

# --- 6. And the engine's own rules arrive in the engine's own words,
#        still as INVALID_INPUT. These are the ones a script trips over:
print()
refusal("6) moment at pinned top", end_top="Pinned")
refusal("6) braced + free top", end_top="Free")
refusal("6) annex on BS8110", national_annex="GB")
refusal("6) a case with no load", load_cases=[{"axial": 0}])

# --- 7. "no_solution" IS REAL HERE. The request was well-formed, the
#        engine ran, and it declined. Two shapes, both category
#        "no_solution", code ENGINE_REFUSED — so this branch is not
#        defensive on C13:
print()
refusal("7) CSA A23.3:24", design_code="CSA A23.3:24")
refusal("7) es = 20 GPa", es=20.0)

# --- 7b. That second one deserves a second look, because `es` is
#         OPTIONAL and its default is 200 GPa. Measured: 45 is refused,
#         50 is accepted — and 0 is accepted as MEANING THE DEFAULT, not
#         as a zero modulus. A zero that means "unset" is worth knowing
#         before you compute one into a batch:
zero_es = prokon.v5.general_column.analyse(**{**GOOD, "es": 0.0})["result"]
default = prokon.v5.general_column.analyse(**GOOD)["result"]
same = zero_es["min_capacity_factor"] == default["min_capacity_factor"]
print(f"\n7b) es = 0 gives {zero_es['min_capacity_factor']:.6f}, "
      f"es omitted gives {default['min_capacity_factor']:.6f} - "
      f"identical: {same}")

# --- 8. Both lists have a hard ceiling, and there is a THIRD ceiling
#        underneath them that is not the engine's at all. 200 load cases
#        go through; 201 are refused. 400 section rows go through; 401
#        are refused:
print()
many = [{"axial": 1000.0 + i} for i in range(201)]
refusal("8) 201 load cases", load_cases=many)

pad = [{"code": "+", "x": 100.0, "y": 100.0}, {"code": "B", "x": 8.0}]
big = list(SECTION) + pad * ((401 - len(SECTION)) // 2 + 1)
refusal(f"8) {len(big[:401])} section rows", section=big[:401])

# --- 8b. ...but ask for 400 rows AND 200 cases together — both legal —
#         and neither ceiling is what stops you. The whole request travels
#         as ONE command line, and Windows caps that at 32 767
#         characters. The category is "environment": the engine process
#         never started, so nothing was calculated and nothing is wrong
#         with your model. Split the schedule into smaller calls.
try:
    prokon.v5.general_column.analyse(
        **{**GOOD, "section": big[:400],
           "load_cases": [{"axial": 1000.0 + i, "moment_x_top": 50.0 + i,
                           "moment_y_top": 20.0 + i,
                           "moment_x_bottom": 50.0 + i,
                           "moment_y_bottom": 20.0 + i} for i in range(200)]})["result"]
except prokon.v5.ProkonError as e:
    tail = e.message[e.message.find("[WinError"):]
    print(f"\n8b) 400 rows + 200 cases: {e.category} / {e.code}")
    print(f"    {tail}")

# --- 9. NOW THE HALF THAT BITES. Four calls that SUCCEED.
#
# --- 9a. An overstressed column is a RESULT, not an error. No exception,
#         no flag beyond the verdict you have to read:
over = prokon.v5.general_column.analyse(**{**GOOD, "length": 15.0})["result"]
print(f"\n9a) the same column at 15 m: has_feasible_design = "
      f"{over['has_feasible_design']}, min_capacity_factor = "
      f"{over['min_capacity_factor']:.4f}, utilisation = "
      f"{over['utilisation']:.4f}")
print(f"    governing: LC{over['critical_load_case']} at "
      f"{over['critical_position']}. Branch on the verdict - "
      f"nothing raises.")

# --- 9b. `is_slender_x` and `is_slender_y` ARE NEVER WRITTEN. The engine
#         leaves them false on every column, including the one it has just
#         designed as slender. Read `is_short_column` per load case:
case = over["load_cases"][0]
print(f"\n9b) that 15 m column: is_slender_x = {over['is_slender_x']}, "
      f"is_slender_y = {over['is_slender_y']}")
print(f"    ...while is_short_column = {case['is_short_column']} and the "
      f"Middle position carries an\n    additional_moment_x of "
      f"{case['positions'][1]['additional_moment_x']:.1f} kNm - a "
      f"slenderness moment on a column the flags\n    call stocky. "
      f"is_short_column is the one to trust.")

# --- 9c. Per-position `utilisation` can be None. Where the engine
#         produced no capacity at a position, `capacity_factor` is 0 and
#         `utilisation` is None rather than a made-up 0 — so a screen on
#         `utilisation > 1` would SKIP the worst position in the run.
#         `capacity_factor` is always a number. Branch on that:
hopeless = prokon.v5.general_column.analyse(
    **{**GOOD, "load_cases": [{"axial": -1e-6,
                               "moment_x_top": 1e7, "moment_x_bottom": 1e7,
                               "moment_y_top": 1e7, "moment_y_bottom": 1e7}]})["result"]
print("\n9c) a load case the engine could not answer everywhere:")
print("      position  capacity_factor           utilisation")
for p in hopeless["load_cases"][0]["positions"]:
    print(f"      {p['position']:<9} {p['capacity_factor']:<25.6g} "
          f"{p['utilisation']!r}")

# --- 9d. And the same None can mean the OPPOSITE. The boundary treats a
#         capacity factor above 1e8 as "never computed" and republishes
#         min_capacity_factor as 0 — so a column too strong to measure
#         reports utilisation None and has_feasible_design FALSE, with
#         every position reading a quarter of a billion:
absurd = prokon.v5.general_column.analyse(
    **{**GOOD, "load_cases": [{"axial": 1e-5}]})["result"]
print(f"\n9d) 400 x 400 under 1e-5 kN: min_capacity_factor = "
      f"{absurd['min_capacity_factor']}, utilisation = "
      f"{absurd['utilisation']!r},")
print(f"    has_feasible_design = {absurd['has_feasible_design']} - while "
      f"every position reads "
      f"{absurd['load_cases'][0]['positions'][0]['capacity_factor']:.6g}.")
print("    A 0 min_capacity_factor is a sentinel, not a measurement. It "
      "takes an\n    absurd load to reach - but read it as 'no answer', "
      "never as 'no capacity'.")

# --- 10. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#         (default 120.0) before raising category "timeout", code
#         ENGINE_DID_NOT_ANSWER.
#
#         SET IT ON THIS FEATURE, AND MEAN IT. The reference page records
#         a known engine defect: on a slender column the moment magnifier
#         passes the ACI bound and the engine raises an internal message
#         box that nothing can click in a scripted run, so the call ends
#         only by timeout. The page names ACI 318 - 2019 and warns there
#         is no safe slenderness to retreat to (a 6 m column was measured
#         blocking too).
#
#         Measured on this build, 2026-08-29, and worth more than the
#         page currently says: the SAME block happens under
#         ACI 318 - 2005, ACI 318 - 2011 and ACI 318 - 2014. On the
#         400 x 400 reference column at 9 m, six of six attempts across
#         those three codes never returned; ACI 318 - 1999 and every
#         non-ACI code answered in about a third of a second. So treat
#         "ACI + slender" as the hazard, not "2019 + slender", give every
#         call a timeout, and measure a new ACI case for itself before
#         trusting it in a batch.
#
#         (This script never calls any of those four codes. A documented
#         hang is not something an example should execute; the batch guard
#         below shows what to do with the timeout when it reaches you.)
prokon.v5.timeout_seconds = 300.0
print(f"\n10) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. It guards all three shapes:
#     the exception, the timeout that is really a known defect, and the
#     successful call whose verdict you still have to read.
def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.general_column.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            return None, f"engine declined: {printable(e.message)}"
        if e.category == "invalid_input":
            last = printable(e.message).splitlines()[-1].strip(" -")
            return None, f"input problem: {last}"
        if e.category == "timeout":
            # On C13 this is the ACI message-box defect far more often
            # than it is a slow machine. Flag the row, keep the batch.
            return None, "timed out - check for the ACI slenderness defect"
        raise  # environment trouble should stop the run

    # The two checks the wire will not do for you.
    if result["min_capacity_factor"] == 0:
        return None, "no capacity factor computed (0 is a sentinel)"
    if not result["has_feasible_design"]:
        return None, (f"overstressed: utilisation "
                      f"{result['utilisation']:.3f} at "
                      f"{result['critical_position']}")
    return result, None


print()
for label, inputs in (
        ("as given", GOOD),
        ("15 m", {**GOOD, "length": 15.0}),
        ("CSA A23.3:24", {**GOOD, "design_code": "CSA A23.3:24"}),
        ("es = 20 GPa", {**GOOD, "es": 20.0}),
        ("moment at pinned top", {**GOOD, "end_top": "Pinned"}),
        ("N = 1e-5 kN", {**GOOD, "load_cases": [{"axial": 1e-5}]})):
    result, reason = try_analyse(**inputs)
    verdict = (f"ok, capacity factor {result['min_capacity_factor']:.3f}"
               if result else reason)
    print(f"11) batch-safe call, {label:<21} -> {verdict}")

# --- 12. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
#         .category/.code/.message/.hints are the SUMMARY. The whole
#         document the engine sent rides the error as .envelope, so a
#         failed call is a RECORD you can file, not a message you print
#         once and lose.
#
#         THERE ARE THREE STATES, and you must ask them in this order:
#
#         1. err.envelope is None
#              Nothing came back at all - a timeout, a command line too
#              long, an unlaunchable executable. There is no document, so
#              there is nothing to read. ASK THIS FIRST: reaching into a
#              field here is a TypeError, not a diagnosis.
#         2. err.envelope is a dict, and envelope["module"] is None
#              The HOST answered and refused before it dispatched. One
#              executable carries twelve engines, and a bad choice value is
#              refused before it has resolved which of them you meant - so
#              there is no engine to name. You still get the category, the
#              code, the hints and the timing.
#         3. err.envelope is a dict, and envelope["module"] is a name
#              An ENGINE ran and refused. This is the full record: which
#              engine, which version, when, and how long it took. This is
#              the one a calculation record needs.
#
#         So read the identity with .get(), never with [] - states 1 and 2
#         both lack it, for different reasons.
#
#         .warnings and .logs are read off that same envelope, which is why
#         they are empty LISTS when there is no envelope - never None, and
#         never a KeyError.

def diagnose(failure):
    """Everything worth recording about a failed analyse(), from the error alone."""
    record = {
        "category": failure.category,
        "code": failure.code,
        "message": failure.message,
        "hints": failure.hints,
        "warnings": failure.warnings,
        "logs": failure.logs,
    }

    if failure.envelope is None:
        record["has_envelope"] = False
        return record                    # nothing else exists. Do not reach further.

    envelope = failure.envelope
    meta = envelope.get("meta") or {}

    record["has_envelope"] = True
    record["envelope_version"] = envelope.get("envelope_version")
    record["module"] = envelope.get("module")                  # None before dispatch
    record["module_version"] = envelope.get("module_version")  # None before dispatch
    record["producer_version"] = meta.get("producer_version")
    record["started_at"] = meta.get("started_at")
    record["elapsed_ms"] = meta.get("elapsed_milliseconds")
    return record


def diagnosed(label, **inputs):
    try:
        prokon.v5.general_column.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n12) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 12a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("12a  refused before dispatch", **{**GOOD, "design_code": "BS 8110"})

# 12b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("12b  refused by the engine", **{**GOOD, "end_top": "Pinned"})

# 12c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("12c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")
