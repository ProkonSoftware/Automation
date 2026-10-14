# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  beam_section (C22 Beam Section)
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
# A robust script branches on .category. A script that has to REPORT a
# failure reads .envelope. This example walks the cases you will actually
# meet, and ends with the envelope, because that is the part a batch or a
# calc sheet needs.

import prokon.v5

GOOD = dict(
    design_code="BS8110 - 1997",
    m=200.0, v=100.0, bw=300.0, h=500.0,
    dc_t=40.0, dc_b=40.0, dc_s=40.0,
    fcu=30.0, fy=450.0, fyv=450.0,
)

# --- 1. A typo in a choice value: category "invalid_input", with hints.
#        Choice values are exact, INCLUDING capitals: "bs8110 - 1997"
#        would be refused too.
try:
    prokon.v5.beam_section.analyse(**{**GOOD, "design_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   allowed values include: {', '.join(e.hints[:4])}, ...")

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
    prokon.v5.beam_section.analyse(**{k: v for k, v in GOOD.items() if k != "fcu"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fcu": None}
try:
    prokon.v5.beam_section.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 3. The engine's own validation also refuses, in its own words —
#        still category "invalid_input". Here the covers leave no room
#        for a lever arm:
try:
    prokon.v5.beam_section.analyse(**{**GOOD, "h": 150.0, "dc_t": 90.0, "dc_b": 90.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 3b. And know your feature: beam_section DESIGNS WHATEVER IT IS
#        ASKED. An absurd request does not fail — it returns absurd
#        steel. The desktop's eyeball check is gone in a script, so
#        sanity-check results yourself:
r = prokon.v5.beam_section.analyse(**{**GOOD, "m": 5000.0, "h": 250.0})["result"]
steel_pct = 100.0 * r["ast"] / (GOOD["bw"] * 250.0)
print(f"\n3b) m=5000 kNm on a 300x250 'works': Ast = {r['ast']:.0f} mm2 "
     f"= {steel_pct:.0f}% steel - physically meaningless. Check your outputs.")

# (Other features DO refuse a well-formed request that has no answer —
# that arrives as category "no_solution", the case worth branching on
# in any search loop, as the batch-safe pattern below does.)

# --- 4. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout". Raise it for
#        very large runs, or set None to wait forever:
prokon.v5.timeout_seconds = 300.0
print(f"\n4) timeout now {prokon.v5.timeout_seconds} s per call")
# --- 5. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
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
        prokon.v5.beam_section.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n5) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 5a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("5a  refused before dispatch", **{**GOOD, "design_code": "BS 8110"})

# 5b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("5b  refused by the engine", **{**GOOD, "h": 150.0, "dc_t": 90.0, "dc_b": 90.0})

# 5c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("5c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")

# --- 6. The pattern to copy into batch scripts:
def try_analyse(**inputs):
    """Return (result, None) or (None, record) - never crash the batch."""
    try:
        return prokon.v5.beam_section.analyse(**inputs)["result"], None
    except prokon.v5.ProkonError as failure:
        if failure.category in ("no_solution", "invalid_input"):
            # The DIAGNOSIS goes into the row, not just the message. A sweep
            # of a thousand sections is worth little if its failures come back
            # as bare strings you cannot trace to an engine version.
            return None, diagnose(failure)
        raise  # environment/internal trouble should stop the run

result, record = try_analyse(**GOOD)
print(f"\n6) batch-safe call: {'ok' if result else record['message']}")

result, record = try_analyse(**{**GOOD, "h": 150.0, "dc_t": 90.0, "dc_b": 90.0})
print(f"   a failed row keeps its record: {record['code']} from "
      f"{record['module']} {record['module_version']}")
