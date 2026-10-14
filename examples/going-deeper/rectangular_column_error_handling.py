# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  rectangular_column (C11 Rectangular Column)
# Verified: yes — 2026-09-09 — behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "environment", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it — often the full list of allowed values
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT — or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. But on THIS feature the
# exceptions are only half the story: the refusal you are most likely to
# meet never raises. It comes back as DATA, on a call that succeeded.
# Section 5 is the one to read twice.

import prokon.v5

GOOD = dict(
    design_code="SABS 0100 - 2000",
    h=400.0, b=400.0,                 # mm — h is the larger dimension
    dc_x=40.0, dc_y=40.0,             # mm to the bar centroids
    fcu=30.0, fy=450.0,               # MPa
    lex=4000.0, ley=4000.0,           # mm — effective lengths
    bracing_x="Braced", bracing_y="Braced",
    betad=0.6, deltas=1.0,
    load_cases=[
        {"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
        {"n": 2000, "m2x": 125, "m1x":  75, "m2y":  90, "m1y": 55},
    ],
)


def printable(text):
    """Engine wording, made safe to print on any console — see 3b."""
    return text.encode("ascii", "replace").decode("ascii")


# --- 1. A typo in a choice value: category "invalid_input", with the
#        whole allowed list in .hints. Choice values are exact, INCLUDING
#        capitals: "sabs 0100 - 2000" is refused the same way.
try:
    prokon.v5.rectangular_column.analyse(**{**GOOD, "design_code": "SABS 0100"})["result"]
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
#         mangling ('FCU' gets no suggestion at all).
try:
    prokon.v5.rectangular_column.analyse(**{k: v for k, v in GOOD.items() if k != "fcu"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fcu": None}
try:
    prokon.v5.rectangular_column.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   hint: {e.hints[0].split('. ')[0]}...")

# --- 3. The engine's own validation refuses in its own words — still
#        "invalid_input", code INVALID_INPUT — and here .hints is EMPTY.
#        The sentence is the whole of the answer, so print it:
try:
    prokon.v5.rectangular_column.analyse(**{**GOOD, "dc_x": 250.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}   ({len(e.hints)} hints)")
    print(f"   {e.message}")

# --- 3b. AND MIND YOUR CONSOLE. A few of those sentences are written
#        with real mathematical symbols, and a Windows console on the
#        default code page raises UnicodeEncodeError the moment you print
#        one. Measured on this feature: the h-versus-b rule carries a
#        "greater-or-equal" sign and the h-versus-4b rule a multiplication
#        sign. Fold anything that came from the engine before printing it:
try:
    prokon.v5.rectangular_column.analyse(**{**GOOD, "h": 300.0, "b": 400.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3b) {e.category} / {e.code}")
    print(f"   {printable(e.message)}")
    print(f"   plain ASCII as it stands? {e.message.isascii()} "
          f"- the '?' above stands in for the symbol")

# --- 4. The load schedule has its own code, INVALID_LOAD_CASES, and it
#        names the offending case by index. A misspelt member is REFUSED,
#        never ignored — "mx1" cannot silently become a missing "m2x":
try:
    prokon.v5.rectangular_column.analyse(
        **{**GOOD, "load_cases": [{"n": 1500, "mx1": 250, "m1x": 150,
                                   "m2y": 150, "m1y": 90}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n4) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 5. NOW THE HARD PART: THE COMMON REFUSAL IS NOT AN EXCEPTION.
#        Ask for a moment at an end you pinned and the call SUCCEEDS.
#        There is no arrangement, has_feasible_design is False, and the
#        reason is in sweep_errors — one copy per bar diameter the engine
#        swept, so six identical sentences are one problem, not six:
r = prokon.v5.rectangular_column.analyse(**{**GOOD, "end_cond_top_x": "Pinned"})["result"]
print("\n5) a pinned top carrying m2x = 250: no exception at all")
print(f"   has_feasible_design = {r['has_feasible_design']}   "
      f"options = {len(r['options'])}   "
      f"sweep_errors = {len(r['sweep_errors'])} "
      f"({len(set(r['sweep_errors']))} distinct)")
print(f"   {printable(r['sweep_errors'][0])}")

# --- 5b. The control, to show it really is the moment and not the pin:
#        move the same 250 kNm to the bottom end, which is not pinned,
#        and the identical column designs normally.
r = prokon.v5.rectangular_column.analyse(
    **{**GOOD, "end_cond_top_x": "Pinned",
       "load_cases": [{"n": 1500, "m2x": 0, "m1x": 250, "m2y": 150, "m1y": 90}]})["result"]
print(f"5b) the same moment at the bottom end: {len(r['options'])} arrangements, "
      f"Ast = {r['options'][0]['ast']:.0f} mm2")

# --- 5c. Three other everyday mistakes arrive in exactly this shape.
#        Whatever you do with sweep_errors, do it for all of them:
for label, overrides in (
        ("a braced cantilever", {"end_cond_top_x": "Free"}),
        ("a moment at a free top", {"end_cond_top_x": "Free",
                                    "end_cond_bot_x": "Free",
                                    "bracing_x": "Unbraced"}),
        ("deltas left out under ACI", {"design_code": "ACI 318 - 2019",
                                       "deltas": 0.0})):
    r = prokon.v5.rectangular_column.analyse(**{**GOOD, **overrides})["result"]
    print(f"5c) {label:<26} -> {len(r['options'])} options, "
          f"{printable(r['sweep_errors'][0])}")

# --- 6. And the mirror image: A HOPELESS COLUMN IS A SUCCESS. The engine
#        designs whatever it is asked. Push the load up and it fills the
#        section with steel, reports has_feasible_design True, and leaves
#        the judgement to you. 15.4 % is where it saturates:
r = prokon.v5.rectangular_column.analyse(
    **{**GOOD, "load_cases": [{"n": 4000, "m2x": 250, "m1x": 150,
                               "m2y": 150, "m1y": 90}]})["result"]
best = r["options"][0]
print(f"\n6) N = 4000 kN on the same 400 x 400: "
      f"has_feasible_design = {r['has_feasible_design']}, "
      f"{best['perc']:.1f} % steel as {best['bar_description']} "
      f"({best['ast']:.0f} mm2) - not a column, a saturated section")

# --- 6b. A TENSILE axial force is accepted and designed, and the RESULT
#        dict says nothing about it - the flag lives on the envelope's
#        warnings, beside the result rather than in it. A current build
#        re-emits it as a ProkonWarning attributed to this very line (and
#        analyse(...)["warnings"] hands you the text as data);
#        an older one dropped it in silence. Check the sign of your own
#        loads either way, and never screen on the result dict alone:
r = prokon.v5.rectangular_column.analyse(
    **{**GOOD, "load_cases": [{"n": -500, "m2x": 100, "m1x": 60,
                               "m2y": 50, "m1y": 30}]})["result"]
print(f"6b) N = -500 kN (tension): {len(r['options'])} arrangements, "
      f"{r['options'][0]['perc']:.2f} % steel, and no flag in the result")

# --- 7. A failure that is NOT the engine's: the whole request travels as
#        one command line, and Windows caps that at 32 767 characters
#        including its terminating NUL. On this section, 560 five-member
#        cases still launch and 561 do not. It arrives in one of TWO
#        shapes, so guard for both: a current shim measures the line and
#        refuses it as invalid_input / COMMAND_LINE_TOO_LONG before
#        spawning anything, while an older one - and any direct CLI
#        launch - dies inside CreateProcess as environment /
#        ENGINE_NOT_LAUNCHABLE ([WinError 206]). Either way the answer is
#        the same: batch a long schedule into calls of a few hundred:
too_many = [{"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90}
            for _ in range(561)]
try:
    prokon.v5.rectangular_column.analyse(**{**GOOD, "load_cases": too_many})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n7) 561 load cases: {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 8. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout". Raise it for
#        very large runs, or set None to wait forever:
prokon.v5.timeout_seconds = 300.0
print(f"\n8) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. It has to guard BOTH shapes:
#     the exception, and the successful call that designed nothing. Note
#     what is NOT here — no "no_solution" branch. `analyse` never returned
#     one in any refusal probed on this feature; the engine's own refusals
#     come back as data, in sweep_errors.
MAX_STEEL_PERCENT = 4.0        # your code's clause and your detailing limit


def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.rectangular_column.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "invalid_input":
            return None, f"input problem: {printable(e.message)}"
        raise  # environment and timeout trouble should stop the run

    if not result["options"]:
        reason = (printable(result["sweep_errors"][0])
                  if result["sweep_errors"] else "no reason given")
        return None, f"nothing designed: {reason}"

    best = result["options"][0]
    if best["perc"] >= MAX_STEEL_PERCENT:
        return None, f"{best['perc']:.3f} % steel, over the {MAX_STEEL_PERCENT:.0f} % limit"
    return result, None


print()
for label, inputs in (
        ("as given", GOOD),
        ("pinned top, moment left on", {**GOOD, "end_cond_top_x": "Pinned"}),
        ("N = 4000 kN", {**GOOD, "load_cases": [{"n": 4000, "m2x": 250, "m1x": 150,
                                                 "m2y": 150, "m1y": 90}]}),
        ("h below b", {**GOOD, "h": 300.0, "b": 400.0})):
    result, reason = try_analyse(**inputs)
    verdict = f"ok, Ast = {result['options'][0]['ast']:.0f} mm2" if result else reason
    print(f"9) batch-safe call, {label:<26} -> {verdict}")

# --- 10. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
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
        prokon.v5.rectangular_column.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n10) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 10a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("10a  refused before dispatch", **{**GOOD, "design_code": "SABS 0100"})

# 10b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("10b  refused by the engine", **{**GOOD, "dc_x": 250.0})

# 10c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("10c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")
