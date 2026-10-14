# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes — 2026-09-09 — behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "timeout", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it — often the full list of allowed values
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT — or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. But on THIS feature the
# exceptions are the easy half: a retaining wall that falls over is a
# perfectly successful analysis. The sections after 4 are the ones that
# catch people out.

import prokon.v5

GOOD = dict(
    concrete_code="BS8110 - 1997",
    h1=4.0,                       # stem height above the base, m
    b=0.70, d=2.00, c=0.40,       # toe, heel, base thickness, m
    at=0.25, ab=0.35,             # stem thickness top and base, m
    theta=30.0, delta=15.0,       # soil angles, degrees
    fcu=30.0, fy=450.0,           # MPa
    pmax=200.0,                   # allowable bearing pressure, kPa
    load_cases=[{"name": "Traffic", "w": 10.0}],
)

# --- 1. A typo in a choice value: category "invalid_input", with hints.
#        Choice values are exact, INCLUDING capitals and the spacing:
#        "bs8110 - 1997" and "BS 8110" are both refused.
try:
    prokon.v5.retaining_wall.analyse(**{**GOOD, "concrete_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   all {len(e.hints)} concrete codes are in .hints: "
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
    prokon.v5.retaining_wall.analyse(**{k: v for k, v in GOOD.items() if k != "fcu"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fcu": None}
try:
    prokon.v5.retaining_wall.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   hint: {e.hints[0]}")

# --- 3. The engine's own validation also refuses, in its own words —
#        still "invalid_input", code INVALID_INPUT, with one hint line per
#        offending field (so .hints can hold several). Here a toe
#        projection is given as a negative number:
try:
    prokon.v5.retaining_wall.analyse(**{**GOOD, "b": -0.5})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   {len(e.hints)} field(s) named in .hints")

# --- 4. The load schedule has its own code, INVALID_LOAD_CASES. A member
#        the command does not read is refused, never ignored — a misspelt
#        "lyn1" cannot silently become a default:
try:
    prokon.v5.retaining_wall.analyse(
        **{**GOOD, "load_cases": [{"name": "Traffic", "lyn1": 1.0}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n4) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 5. AND NOW THE HARD PART: AN INADEQUATE WALL IS A SUCCESS.
#        Nothing raises. This is wall W5 from the batch recipe next door —
#        a 5 m wall on a 1.70 m base — and the analysis comes back happily,
#        with stability ratios well under 1 and a bearing pressure no soil
#        on earth would carry. Your checks are the only verdict there is:
UNDERSIZED = dict(
    concrete_code="BS8110 - 1997",
    h1=5.0, b=0.40, d=1.00, c=0.35, at=0.25, ab=0.30,
    theta=30.0, delta=15.0,
    fcu=25.0, fy=450.0, db=25.0, dg=18.0,
    sf_overturning=1.5, sf_sliding=1.5,
    dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9, mu=0.5,
    cover_wall=50.0, cover_base=50.0,
    pmax=150.0,
    load_cases=[{"name": "Surcharge", "w": 15.0}],
)
r = prokon.v5.retaining_wall.analyse(**UNDERSIZED)["result"]
print("\n5) an undersized 5 m wall: no exception at all")
print(f"   overturning {r['overturning_ratio']:.3f}x required   "
      f"sliding {r['sliding_ratio']:.3f}x required")
print(f"   qmax = {r['qmax']:.0f} kPa against a 150 kPa allowable "
      f"(bearing_ratio {r['bearing_ratio']:.1f})")

# --- 5b. Worse: CHECK ALL THREE RATIOS, NOT ONE. Once the resultant
#        leaves the base the wall has already overturned, and qmax comes
#        back NEGATIVE — so bearing_ratio (qmax/pmax) goes negative with
#        it and sails through a lone "<= 1" test:
r = prokon.v5.retaining_wall.analyse(
    **{**GOOD, "h1": 6.0, "b": 0.10, "d": 0.30, "c": 0.30,
       "load_cases": [{"name": "Surcharge", "w": 20.0}]})["result"]
print(f"\n5b) a wall that has fallen over: qmax = {r['qmax']:.1f} kPa, "
      f"bearing_ratio = {r['bearing_ratio']:.3f}")
print(f"    bearing_ratio <= 1 is {r['bearing_ratio'] <= 1}, and yet "
      f"overturning is only {r['overturning_ratio']:.3f}x required")

# --- 6. A second silence: A RESULT KEY CAN COME BACK None. Ask for
#        user-defined earth-pressure coefficients and leave k2 (Ka) at its
#        default of 0, and the stability figures are not computable — the
#        run still succeeds, and five keys arrive as None rather than as
#        an error. `None >= 1` raises TypeError, so guard before you test:
r = prokon.v5.retaining_wall.analyse(**{**GOOD, "use_user_k_values": True})["result"]
nulls = [k for k in ("sf_overturning", "sf_sliding", "sf_bearing",
                     "overturning_ratio", "sliding_ratio")
         if r[k] is None]
print(f"\n6) use_user_k_values=True with k2 left at 0: no exception, "
      f"{len(nulls)} null keys")
print(f"   {', '.join(nulls)}")

# --- 6b. And a third: four of the 28 concrete_code values are crack-width
#        codes. They run, they return ok, and they design NO steel. Read
#        the two reinforcement keys back and treat a pair of zeros as
#        "nothing was designed":
r = prokon.v5.retaining_wall.analyse(**{**GOOD, "concrete_code": "BS8007 - 1987"})["result"]
print(f"\n6b) concrete_code='BS8007 - 1987' (a crack-width code): "
      f"as_wall_req = {r['as_wall_req']}, as_base_req = {r['as_base_req']}")

# --- 7. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout". Raise it for
#        very large schedules, or set None to wait forever:
prokon.v5.timeout_seconds = 300.0
print(f"\n7) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. Note what is NOT here: no
#     "no_solution" branch. `analyse` never returns one — every refusal
#     measured on this feature is "invalid_input" — so the adequacy check
#     has to be folded in beside the exceptions, or an overturned wall
#     quietly reports as a success.
def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.retaining_wall.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "invalid_input":
            return None, f"input problem: {e.message}"
        raise  # environment and timeout trouble should stop the run

    checks = (result["overturning_ratio"], result["sliding_ratio"],
              result["bearing_ratio"])
    if any(v is None for v in checks):
        return None, "stability not computable (null safety factors)"
    ovt, sld, bear = checks
    fails = ([] if ovt >= 1 else ["overturning"]) \
        + ([] if sld >= 1 else ["sliding"]) \
        + ([] if 0 <= bear <= 1 else ["bearing"])
    if fails:
        return None, "wall inadequate: " + " + ".join(fails)
    return result, None


for label, inputs in (("as given", GOOD),
                      ("undersized", UNDERSIZED),
                      ("own K values", {**GOOD, "use_user_k_values": True})):
    result, reason = try_analyse(**inputs)
    print(f"8) batch-safe call, {label}: {'ok' if result else reason}")

# --- 9. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
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
        prokon.v5.retaining_wall.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n9) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 9a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("9a  refused before dispatch", **{**GOOD, "concrete_code": "BS 8110"})

# 9b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("9b  refused by the engine", **{**GOOD, "b": -0.5})

# 9c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("9c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")
