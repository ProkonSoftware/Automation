# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  punching_shear (C23 Punching Shear)
# Verified: yes — 2026-09-09 — behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "no_solution", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it — the allowed values, the input's own
#              description, or EVERY rule the validator objected to
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT — or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. The most expensive outcome of all
# raises nothing at all: section 5. Note that "no_solution" is DEFENSIVE on
# this feature as of 2026-08-31 — see section 4 for the case that used to
# fire it, and still does on an older build.

import prokon.v5

GOOD = dict(
    design_code="BS8110 - 1997",
    col_width=400.0, col_breadth=400.0,
    effective_depth=200.0,
    nearest_edge_x=10000.0, nearest_edge_y=10000.0,
    fcu=35.0, fy=500.0, fyv=500.0,
    load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}],
)

# --- 1. A typo in a choice value: category "invalid_input", with hints.
#        Choice values are exact, INCLUDING capitals: "bs8110 - 1997" is
#        refused too. The whole list of design codes arrives in .hints.
try:
    prokon.v5.punching_shear.analyse(**{**GOOD, "design_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}\n   {e.message}")
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
    prokon.v5.punching_shear.analyse(**{k: v for k, v in GOOD.items() if k != "fcu"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fcu": None}
try:
    prokon.v5.punching_shear.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}\n   {e.message}\n   hint: {e.hints[0]}")

# --- 3. The engine's own validation refuses in its own words — still
#        "invalid_input", code INVALID_INPUT — and publishes EVERY failing
#        rule in .hints, so one round trip tells you all of them:
try:
    prokon.v5.punching_shear.analyse(
        **{**GOOD, "col_width": -1.0, "effective_depth": 0.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}")
    for hint in e.hints:
        print(f"   - {hint}")

# --- 3b. The load schedule has its own code. A misspelt member is REFUSED,
#         not ignored — no result would show your moment had not arrived:
try:
    prokon.v5.punching_shear.analyse(
        **{**GOOD, "load_cases": [{"v": 800.0, "mxx": 50.0}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3b) {e.category} / {e.code}\n   {e.message}")

# --- 3c. And an input this feature does not have is refused by PYTHON,
#         before any engine runs. There is no "metric" input: the surface
#         is metric-only, so the name is refused rather than accepted and
#         ignored -- and because analyse() declares one real parameter per
#         input, that refusal costs nothing and never reaches the engine.
try:
    prokon.v5.punching_shear.analyse(**{**GOOD, "metric": False})["result"]
except TypeError as e:
    print(f"\n3c) TypeError -- Python refused; no engine was launched\n   {e}")

# --- 3d. national_annex IS an input (2-letter ISO country code, 35 of them),
#         and it has two refusals of its own, both invalid_input and both
#         before the engine: a value outside the set, and one of the set on a
#         code that takes none. Only the three Eurocode 2 codes take one:
try:
    prokon.v5.punching_shear.analyse(**{**GOOD, "national_annex": "GB"})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3d) {e.category} / {e.code}\n   {e.message}")

# --- 4. "no_solution" on this feature. Until 2026-08-31 the allowed list was
#        NOT a runnable list: "SABS 0100 - 1992" was offered and the engine
#        declined it, because the two halves spelt the code differently. That
#        is fixed, so on a current build this call SUCCEEDS and all fourteen
#        codes run - but an older build still refuses it, so guard for both.
#        (The desktop lists the same calculation as "SABS 0100 - 2000".)
try:
    sabs = prokon.v5.punching_shear.analyse(
        **{**GOOD, "design_code": "SABS 0100 - 1992"})["result"]
    print(f"\n4) SABS 0100 - 1992 analysed: perimeter-1 asv = "
          f"{sabs['critical_perimeters'][0]['asv']:.3f} mm2, "
          f"vcu = {sabs['vcu']:.3f} MPa")
except prokon.v5.ProkonError as e:
    print(f"\n4) SABS 0100 - 1992 refused on this build: "
          f"{e.category} / {e.code}\n   {e.message}")

# --- 5. And know your feature: THE DANGEROUS ANSWERS ARRIVE AS SUCCESSES.
#        There is no pass/fail key, so nothing below raises.
#        (a) A hopeless column head is analysed and reinforced anyway:
bad = prokon.v5.punching_shear.analyse(
    **{**GOOD, "col_width": 250.0, "col_breadth": 250.0,
       "effective_depth": 120.0, "load_cases": [{"v": 2500.0}]})["result"]
i = bad["critical_load_case_index"]
print(f"\n5) 250 x 250 head, de = 120 mm under 2500 kN: vu = {bad['vu'][i]:.2f} "
      f"MPa against vcu = {bad['vcu']:.2f} = {bad['vu'][i] / bad['vcu']:.1f}x the "
      f"ceiling, and it still offers {bad['bars'][0][0]['description']} on "
      f"perimeter 1. Nothing you add fixes a face check - the column grows.")

#        (b) On "Eurocode 2 - 2023" the concrete capacity depends on the
#            flexural steel, so omitting asx_n / asy_n is not conservative:
steel = {f"as{d}_{n}": 1257.0 for d in ("x", "y") for n in (1, 2, 3, 4)}
bare = prokon.v5.punching_shear.analyse(**{**GOOD, "design_code": "Eurocode 2 - 2023"})["result"]
told = prokon.v5.punching_shear.analyse(
    **{**GOOD, "design_code": "Eurocode 2 - 2023", **steel})["result"]
print(f"\n5b) EC2-2023 without the steel areas: vc = "
      f"{[p['vc'] for p in bare['critical_perimeters']]} MPa, so every perimeter "
      f"looks like it needs shear steel. With 1257 mm2 each way perimeter 1 gives "
      f"vc = {told['critical_perimeters'][0]['vc']:.3f}. Always supply them.")

#        (c) And one input nothing validates: col_breadth. Zero or negative is
#            documented as a circular column of diameter col_width, but the
#            engine builds a SQUARE perimeter for both. Use the desktop.
square = prokon.v5.punching_shear.analyse(
    **{**GOOD, "col_width": 450.0, "col_breadth": 450.0})["result"]["uo"]
circle = prokon.v5.punching_shear.analyse(
    **{**GOOD, "col_width": 450.0, "col_breadth": 0.0})["result"]["uo"]
print(f"\n5c) col_width 450: col_breadth 450 gives uo = {square:.0f} mm and "
      f"col_breadth 0 gives uo = {circle:.0f} mm - the same square perimeter, "
      f"not the circular pi x 450 = 1414 mm.")

# --- 6. Timeouts. Each call may take up to prokon.v5.timeout_seconds (default
#        120.0) before raising category "timeout". Raise it for a long
#        schedule — one call analyses up to 200 load cases:
prokon.v5.timeout_seconds = 300.0
print(f"\n6) timeout now {prokon.v5.timeout_seconds} s per call")

# (A Windows note: .message and .hints are the ENGINE's own words and are not
#  all ASCII — its range and non-negativity rules carry a "greater than or
#  equal" sign, and printing one on a cp1252 console raises UnicodeEncodeError.
#  Log them to a UTF-8 file, or set PYTHONIOENCODING=utf-8.)


# --- The pattern to copy into batch scripts. Both categories fire here, and
#     the guard has to read the ANSWER too — see section 5.
def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.punching_shear.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            return None, f"the engine declined: {e.message}"
        if e.category == "invalid_input":
            return None, f"input problem: {e.message}"
        raise  # environment/timeout trouble should stop the run
    worst = result["vu"][result["critical_load_case_index"]]
    if worst > result["vcu"]:
        return None, f"face overstressed: vu {worst:.2f} > vcu {result['vcu']:.2f}"
    return result, None


print("\n7) batch-safe calls:")
for label, head in (("400 x 400, de 200", GOOD),
                    ("same head, SABS code",   # ok now; refused on an older build
                     {**GOOD, "design_code": "SABS 0100 - 1992"}),
                    ("250 x 250, de 120",
                     {**GOOD, "col_width": 250.0, "col_breadth": 250.0,
                      "effective_depth": 120.0, "load_cases": [{"v": 2500.0}]})):
    result, reason = try_analyse(**head)
    print(f"   {label}: {'ok' if result else reason}")

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
        prokon.v5.punching_shear.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n8) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 8a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("8a  refused before dispatch", **{**GOOD, "design_code": "BS 8110"})

# 8b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("8b  refused by the engine", **{**GOOD, "col_width": -1.0, "effective_depth": 0.0})

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
