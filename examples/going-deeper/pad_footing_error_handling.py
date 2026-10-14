# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  pad_footing (C15 Pad Footing)
# Verified: yes — 2026-09-09 — behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "no_solution", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it — the allowed values, or the input's own description
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT — or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. For a pad footing that is only half
# the job: C15's most dangerous outcome is not an exception at all — section 4.

import prokon.v5


def plain(text):
    """Engine text, folded to ASCII so it can be printed anywhere.

    ⚠ THIS IS NOT COSMETIC. The engine's own messages and hints are written
    in the house style of the fleet, which uses em dashes - 176 of them across
    the twelve engines' input descriptions and refusals. A default Windows
    console starts in code page 437, which cannot encode one, so

        print(f"   {plain(e.message)}")

    raises UnicodeEncodeError and takes the whole script down while the ENGINE
    behaved perfectly.

    Measured: this example ran clean until 2026-09-09, when C15's `load_cases`
    refusal gained an em dash (`c04cfec`), and then failed on the documentation
    sweep - which runs every example under cp437 deliberately, precisely to
    catch this. The engine text is not the defect; printing it raw is.

    Every sibling example that prints engine text already does this. Now this
    one does too.
    """
    return str(text).encode("ascii", "replace").decode("ascii")
#--------------------------------------------------------------------

GOOD = dict(
    design_code="BS8110 - 1997",
    a=2.5, b=2.5, yf=0.6, z=0.5,        # the footing, in METRES
    c1=0.4, d1=0.4, e1=0.0, f1=0.0,     # the column, in METRES
    fcu=30.0, fy=450.0,                 # MPa
    allowable_bearing_pressure=200.0,   # kPa, at SERVICEABILITY
    bar_dia_x_bot=16.0, bar_spacing_x_bot=200.0,
    bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0,
    load_cases=[{"name": "LC1", "pa1": 600.0, "hx1": 30.0, "mx1": 20.0, "lf1": 1.4}],
)

# --- 1. A typo in a choice value: category "invalid_input", with hints.
#        Choice values are exact, INCLUDING capitals: "bs8110 - 1997"
#        would be refused too.
try:
    prokon.v5.pad_footing.analyse(**{**GOOD, "design_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {plain(e.message)}")
    print(f"   allowed values include: {plain(', '.join(e.hints[:4]))}, ...")

# --- 2a. LEAVE AN ARGUMENT OUT and PYTHON refuses, before any engine
#         process is launched. analyse() takes real keyword-only
#         parameters, so a misspelled name is caught the same way -- and
#         Python usually suggests the one you meant:
#             analyse() got an unexpected keyword argument 'fyx'.
#             Did you mean 'fy'?
#         Usually, not always: the suggestion is Python's own
#         edit-distance heuristic, and it gives up on a long enough
#         mangling ('FY' gets no suggestion at all).
try:
    prokon.v5.pad_footing.analyse(**{k: v for k, v in GOOD.items() if k != "fy"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fy": None}
try:
    prokon.v5.pad_footing.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {plain(e.message)}")
    print(f"   hint: {plain(e.hints[0])}")

# --- 3. The engine's own validation also refuses, in its own words — still
#        category "invalid_input". Here the column is pushed off the pad:
try:
    prokon.v5.pad_footing.analyse(**{**GOOD, "e1": 2.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}")
    print(f"   {plain(e.message)}")

# --- 3b. A misspelt member of a load case is REFUSED, not ignored — nothing
#         in the results would ever show that your moment had not arrived.
try:
    prokon.v5.pad_footing.analyse(
        **{**GOOD, "load_cases": [{"name": "LC1", "pa1": 600.0, "mx": 20.0}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3b) {e.category} / {e.code}")
    print(f"   {plain(e.message)}")

# --- 4. And know your feature: C15 NEVER REFUSES AN INADEQUATE FOOTING. A
#        pad far too small for its load comes back as a SUCCESS, with
#        has_feasible_design still true — that flag only means "every case
#        solved and none uplifts or overturns at ULS", and says nothing about
#        bearing pressure, shear or crack width. Form those verdicts yourself:
small = prokon.v5.pad_footing.analyse(**{**GOOD, "a": 1.5, "b": 1.5})["result"]
case = small["load_cases"][0]
allowable = GOOD["allowable_bearing_pressure"]
print(f"\n4) 1.5 x 1.5 x 0.6 m under the same 600 kN: no exception, "
      f"has_feasible_design = {small['has_feasible_design']}")
print(f"   SLS bearing {case['sls']['pm']:.0f} kPa against the {allowable:.0f} "
      f"kPa allowable = {case['sls']['pm'] / allowable:.0%}")
print(f"   punching vp = {case['shear']['vp']:.0f}, vcp = "
      f"{case['shear']['vcp']:.0f}: the critical perimeter does not FIT in a "
      f"pad this small, so the check never ran and 'vp <= vcp' reads 0 <= 0. "
      f"Test vcp > 0 first.")

# (So there is no "no_solution" branch to write here. The category is mapped,
#  but C15's validator mirrors the desktop's guards and refuses first — every
#  failure above is "invalid_input".)

# --- 5. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout". Raise it for a
#        long load schedule — one call analyses up to 200 cases:
prokon.v5.timeout_seconds = 300.0
print(f"\n5) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. For pad footings the guard has
#     to read the ANSWER too, not only catch exceptions — see section 4.
def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.pad_footing.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "invalid_input":
            return None, f"input problem: {plain(e.message)}"
        raise  # environment/timeout trouble should stop the run
    # FIRST, because an unsolved case publishes sls.pm = -1 — a sentinel,
    # not a pressure — which would sail through the comparison below.
    if not result["has_feasible_design"]:
        return None, "a case did not solve, uplifts or overturns at ULS"
    # result["max_bearing_pressure_sls"] is this same number, published as
    # an aggregate; the walk is kept here so the guard reads on any build.
    worst = max(c["sls"]["pm"] for c in result["load_cases"])
    if worst > inputs["allowable_bearing_pressure"]:
        return None, f"bearing {worst:.0f} kPa over allowable"
    return result, None


print("\n6) batch-safe calls:")
for label, footing in (("2.5 x 2.5 m", GOOD),
                       ("1.5 x 1.5 m", {**GOOD, "a": 1.5, "b": 1.5})):
    result, reason = try_analyse(**footing)
    print(f"   {label}: {'ok' if result else reason}")

# --- 7. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
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
        prokon.v5.pad_footing.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n7) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 7a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("7a  refused before dispatch", **{**GOOD, "design_code": "BS 8110"})

# 7b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("7b  refused by the engine", **{**GOOD, "e1": 2.0})

# 7c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("7c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")
