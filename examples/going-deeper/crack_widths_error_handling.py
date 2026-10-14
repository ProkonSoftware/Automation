# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  crack_widths (C21 Crack Widths)
# Verified: yes — 2026-09-09 — behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "internal", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it — often the full list of allowed values
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT — or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. This example walks the cases you
# will actually meet on this feature — and the two that never raise at
# all, which are the ones that catch people out.

import prokon.v5

GOOD = dict(
    design_code="BS8007 - 1987", slab_mode=True,
    h=300.0, hef=200.0, b=1000.0, cover=40.0,
    fcu=30.0, fy=450.0, ea=200.0, ec=26.0,
    allowable_crack_width=0.3,
    load_cases='[{"n": 1, "m": 50, "m_uls": 1.5}]',
)

# --- 1. A typo in a choice value: category "invalid_input", with hints.
#        Choice values are exact, INCLUDING capitals and the spaces around
#        the dash: "bs8007 - 1987" and "BS8007" are both refused.
try:
    prokon.v5.crack_widths.analyse(**{**GOOD, "design_code": "BS8007"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   all {len(e.hints)} design codes are in .hints: "
          f"{', '.join(e.hints[:4])}, ...")

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
    prokon.v5.crack_widths.analyse(**{k: v for k, v in GOOD.items() if k != "fcu"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fcu": None}
try:
    prokon.v5.crack_widths.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 3. The engine's own validation also refuses, in its own words —
#        still "invalid_input", code INVALID_INPUT, with one hint line
#        per offending field. Here the cover eats the section:
try:
    prokon.v5.crack_widths.analyse(**{**GOOD, "cover": 290.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   hints: {e.hints}")

# --- 4. The one refusal that is NOT your fault. Two of the thirteen
#        design codes offered have no crack-width routine in the engine —
#        "Eurocode 2" (the 1992 edition) and "CSA A23.3:24" — so asking
#        for either is category "internal", a reported engine defect
#        rather than a bad request. No input will make it answer; the
#        hints name codes that do.
try:
    prokon.v5.crack_widths.analyse(**{**GOOD, "design_code": "Eurocode 2"})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n4) {e.category} / {e.code}")
    print(f"   {e.message.split(': ', 1)[0]}")

# --- 5. And know your feature: A SECTION WITH NO ANSWER IS A SUCCESS.
#        Ask for the impossible and nothing raises — the run comes back
#        ok, and `optimised_configs` is simply EMPTY. Checking the list
#        is the only signal you get:
r = prokon.v5.crack_widths.analyse(
    **{**GOOD, "load_cases": '[{"n": 1, "m": 5000, "m_uls": 1.5}]'})["result"]
found = r["load_cases"][0]["optimised_configs"]
print(f"\n5) m=5000 kNm/m on a 300 mm slab: no exception, "
      f"is_analysed={r['is_analysed']}, {len(found)} arrangements offered")

# --- 5b. Same silence on a bar string the engine cannot read. "Y16" has
#        no spacing, so it is dropped — no error, and the result is
#        indistinguishable from naming no bars at all. Read yours back.
case = prokon.v5.crack_widths.analyse(**{**GOOD, "user_slab_bars": "Y16"})["result"]["load_cases"][0]
print(f"5b) user_slab_bars='Y16' silently dropped: "
      f"user_slab_result={case['user_slab_result']}, "
      f"max_user_crack_width={case['max_user_crack_width']}")

# (`national_annex` is a choice of GB, SG or EU, and only on the three
# Eurocode-family codes. Anything else is refused before the engine runs:
# an unlisted value - "UK" included, though it names the engine's own
# default - as INPUT_VALUE_NOT_ALLOWED with the three in `hints`; one of
# the three on a code that takes no annex as INVALID_INPUT naming the
# codes that do. Omit it to get the default. This input USED TO HANG the
# engine on both those paths, which is why it is described here and not
# demonstrated; the loop is still in the engine but the wire can no
# longer reach it. On an older build, treat it as a hard rule.)

# --- 6. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout". Nothing on
#        the current surface is known to need it:
prokon.v5.timeout_seconds = 300.0
print(f"\n6) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. Note that the empty list
#     from section 5 has to be folded in beside the exceptions, or a
#     section with no answer quietly reports as a success:
def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.crack_widths.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "invalid_input":
            return None, f"input problem: {e.message}"
        if e.category == "internal":
            return None, f"this design code cannot answer ({e.code})"
        raise  # environment and timeout trouble should stop the run
    if not result["load_cases"][0]["optimised_configs"]:
        return None, "no arrangement meets the allowable crack width"
    return result, None


# (The "no_solution" category exists on this feature and is correctly
# mapped, but nothing measured on the shipped surface reaches it — an
# infeasible section arrives as the empty list handled above.)

for label, inputs in (("as given", GOOD),
                      ("0.01 mm limit", {**GOOD, "allowable_crack_width": 0.01})):
    result, reason = try_analyse(**inputs)
    print(f"7) batch-safe call, {label}: {'ok' if result else reason}")

# --- 8. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
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
        prokon.v5.crack_widths.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n8) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 8a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("8a  refused before dispatch", **{**GOOD, "design_code": "BS8007"})

# 8b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("8b  refused by the engine", **{**GOOD, "cover": 290.0})

# 8c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("8c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")
