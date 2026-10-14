# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  circular_column (C12 Circular Column)
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
# A robust script branches on .category. This feature is one of the few
# where "no_solution" is not theoretical: the engine RUNS and DECLINES on
# four everyday mistakes (section 5), so that branch earns its place.
#
# And it has the opposite hazard too. Section 6 is the half that bites:
# the column the engine cannot honestly design comes back as a SUCCESS.

import math

import prokon.v5

GOOD = dict(
    design_code="BS8110 - 1997",
    diameter=220.0, cover=40.0,       # mm
    fcu=25.0, fy=450.0,               # MPa
    lex=2250.0, ley=2250.0,           # mm — required, no default
    deltas=1.0,                       # required, no default
    load_cases=[{"n": 700.0}],        # kN, compression positive
)


def printable(text):
    """Engine and hint wording, made safe to print on any console — see 2b."""
    return text.encode("ascii", "replace").decode("ascii")


# --- 1. A typo in a choice value: category "invalid_input", with the whole
#        allowed list in .hints. Choice values are exact, INCLUDING capitals
#        — "bs8110 - 1997" is refused identically. C12's spellings differ
#        from other features', so read them off .hints rather than guessing:
try:
    prokon.v5.circular_column.analyse(**{**GOOD, "design_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   all {len(e.hints)} design codes are in .hints: "
          f"{', '.join(e.hints[:3])}, ...")

# --- 2a. LEAVE AN ARGUMENT OUT and PYTHON refuses, before any engine
#         process is launched. analyse() takes real keyword-only
#         parameters, so a misspelled name is caught the same way -- and
#         Python usually suggests the one you meant:
#             analyse() got an unexpected keyword argument 'deltasx'.
#             Did you mean 'deltas'?
#         Usually, not always: the suggestion is Python's own
#         edit-distance heuristic, and it gives up on a long enough
#         mangling ('DELTAS' gets no suggestion at all).
try:
    prokon.v5.circular_column.analyse(**{k: v for k, v in GOOD.items() if k != "deltas"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "deltas": None}
deltas_hint = ""
try:
    prokon.v5.circular_column.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    deltas_hint = e.hints[0]
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   hint: {printable(deltas_hint)[:96]}...")

# --- 2c. MIND YOUR CONSOLE. That hint is not plain ASCII — it is written
#         with real em-dashes, and a Windows console on the default code
#         page raises UnicodeEncodeError the moment you print one raw. So
#         does one of the engine's own refusals (section 5c). Fold anything
#         that came off the wire before printing it, as printable() does:
print(f"2c) plain ASCII as it stands? {deltas_hint.isascii()} "
      f"- each '?' above stands in for one em-dash")

# --- 3. The wrapper's own validation refuses in its own words — still
#        "invalid_input", code INVALID_INPUT — and here .hints is EMPTY.
#        The sentence is the whole of the answer, so print it:
try:
    prokon.v5.circular_column.analyse(**{**GOOD, "cover": 110.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}   ({len(e.hints)} hints)")
    print(f"   {e.message}")

# --- 4. The load schedule has its own code, INVALID_LOAD_CASES, and it
#        names the row and the member. A misspelt member is REFUSED, never
#        ignored — "mx2" cannot silently become a zero moment:
try:
    prokon.v5.circular_column.analyse(
        **{**GOOD, "load_cases": [{"n": 700.0, "mx2": 30.0}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n4) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 5. "no_solution" IS REAL HERE, and it is not exotic. The request was
#        well-formed, the engine ran, and it declined. Four shapes you will
#        actually meet — all category "no_solution", code ENGINE_REFUSED:
print()
for label, overrides in (
        ("deltas = 0 under ACI",   {"design_code": "ACI 318 - 2014",
                                    "deltas": 0.0}),
        ("moment at a pinned top", {"end_cond_top_x": "Pinned",
                                    "load_cases": [{"n": 700.0, "m2x": 30.0}]}),
        ("a braced cantilever",    {"end_cond_top_x": "Free"}),
        ("a 14 m effective length", {"lex": 14000.0, "ley": 14000.0})):
    try:
        prokon.v5.circular_column.analyse(**{**GOOD, **overrides})["result"]
    except prokon.v5.ProkonError as e:
        print(f"5) {label:<23} -> {e.category} / {e.code}: {e.message}")

# --- 5b. Two things about those four. First, deltas = 0 is refused by ten
#        of the twenty-one codes and accepted by the rest, so the same
#        script can pass on one code and fail on another. Second, the
#        slenderness limit is the CODE's, not the engine's: measured, the
#        limit named in the message is 60 under BS8110 - 1997, 100 under
#        ACI 318 - 2014, 120 under AS3600 - 2018 and 140 under
#        Eurocode 2 - 1992 — so "too slender" is a per-code verdict.
#
# --- 5c. And read the RESTRAINT you sent, not the noun in the message.
#        `end_cond_bot_x="Pinned"` is refused in the name of "free":
try:
    prokon.v5.circular_column.analyse(
        **{**GOOD, "end_cond_bot_x": "Pinned",
           "load_cases": [{"n": 700.0, "m1x": 60.0}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n5c) a PINNED bottom end, refused as: {e.message}")

#        This is also where the second non-ASCII sentence lives. C12 has
#        two cover rules from two different layers, and only the engine's
#        carries a symbol:
try:
    prokon.v5.circular_column.analyse(**{**GOOD, "cover": 105.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"5c) cover 105 on a 220 mm column: {e.category} / {e.code}")
    print(f"    {printable(e.message)}   (ASCII? {e.message.isascii()})")
    print("    cover 110 tripped the wrapper's rule in 3; 105 gets past it "
          "and the ENGINE refuses.")

# --- 6. NOW THE HALF THAT BITES: A HOPELESS COLUMN IS A SUCCESS.
#        No exception, no flag — the absurd number is in percentage_steel
#        and the judgement is yours. This is the schedule row every C12
#        script needs a guard for:
r = prokon.v5.circular_column.analyse(
    design_code="BS8110 - 1997", diameter=300.0, cover=50.0,
    fcu=30.0, fy=450.0, lex=3000.0, ley=3000.0, deltas=1.0,
    load_cases=[{"n": 6000.0, "m2x": 200.0, "m1x": 100.0}])["result"]
case = r["load_case_results"][0]
print(f"\n6) 300 mm carrying 6000 kN + 200 kNm: all_pass = {r['all_pass']}, "
      f"buckles = {case['buckles']}")
print(f"   ...and {r['percentage_steel']:.2f} % steel ({r['total_as']:.0f} mm2), "
      f"which no design code permits. Nothing on the wire says so.")

# --- 6b. `all_pass` records only that no case BUCKLED. Check the steel
#        against your own code clause, exactly as you would reading the
#        desktop's output — that is what the batch guard below does.
#
# --- 6c. A second silence: a FREE bottom end is never moment-checked.
#        The pinned bottom in 5c refused a 60 kNm m1x; declare the same
#        end Free and the moment is accepted and quietly redistributed:
r = prokon.v5.circular_column.analyse(
    **{**GOOD, "end_cond_bot_x": "Free",
       "load_cases": [{"n": 700.0, "m1x": 60.0}]})["result"]
print(f"\n6c) the same 60 kNm on a FREE bottom end: no exception, "
      f"{r['percentage_steel']:.2f} % steel")
print(f"    the 60 kNm came back as a design moment of "
      f"{r['load_case_results'][0]['moment_x']:.0f} kNm. If an end carries "
      f"no moment, say Pinned\n    and let the refusal in 5c protect you.")

# --- 6d. A THIRD: several outputs are simply never written, and they are
#        published as 0, not as None. `nuz` is written only on the
#        slenderness path, so 0 on a short column means "not computed",
#        never "no capacity":
short = prokon.v5.circular_column.analyse(**GOOD)["result"]
slender = prokon.v5.circular_column.analyse(**{**GOOD, "lex": 6000.0, "ley": 6000.0})["result"]
print(f"\n6d) nuz: {short['nuz']:.0f} at lex = 2250 (short), "
      f"{slender['nuz']:.1f} kN at lex = 6000 (slender) - same column")

# --- 6e. The same trap runs through the per-case keys, and WHICH of them
#        are live depends on the design code. Measured on one 400 mm
#        column at lex = ley = 9000: BS8110 leaves all of these at 0,
#        AS3600 - 2018 writes mux_balance, Eurocode 2 - 1992 writes
#        delta_x. Confirm a key is populated for YOUR code before you
#        branch on it — and never read a 0 as a computed zero:
BIG = dict(diameter=400.0, cover=50.0, fcu=30.0, fy=450.0,
           lex=9000.0, ley=9000.0, deltas=1.0,
           load_cases=[{"n": 1500.0, "m2x": 60.0}])
print()
for code in ("BS8110 - 1997", "AS3600 - 2018", "Eurocode 2 - 1992"):
    c = prokon.v5.circular_column.analyse(
        **{**BIG, "design_code": code})["result"]["load_case_results"][0]
    print(f"6e) {code:<18} delta_x = {float(c['delta_x']):<10.4f} "
          f"mux_balance = {float(c['mux_balance']):<10.4f} "
          f"unity_ratio_x = {float(c['unity_ratio_x']):.4f}")
print("6e) yield_mode was 1 on every code and column probed; its "
      "documented 2 and 3 never appear.")

# --- 6f. And one design code is unusable rather than merely quirky.
#        SP 63.13330.2018 answers every column with the gross concrete
#        area as its steel — measured to the last digit on this column,
#        and on two others. It reports all_pass = True while doing it:
r = prokon.v5.circular_column.analyse(**{**GOOD, "design_code": "SP 63.13330.2018"})["result"]
gross = math.pi * GOOD["diameter"] ** 2 / 4.0
print(f"\n6f) SP 63.13330.2018: total_as = {r['total_as']:.4f} mm2, "
      f"percentage_steel = {r['percentage_steel']}, all_pass = {r['all_pass']}")
print(f"    the gross concrete area is {gross:.4f} mm2 - identical: "
      f"{r['total_as'] == gross}. Do not use this code.")

# --- 7. A failure that is NOT the engine's: the whole request travels as
#        one command line, and Windows caps that at 32 767 characters.
#        Measured here, 484 five-member cases went through and 485 did
#        not — the exact number moves with the length of the executable's
#        own path, so treat it as "a few hundred", not as a constant. The
#        category is "environment": the process never started.
too_many = [{"n": 1500.0, "m2x": 60.0, "m1x": 30.0, "m2y": 40.0, "m1y": 20.0}
            for _ in range(485)]
try:
    prokon.v5.circular_column.analyse(**{**GOOD, "load_cases": too_many})["result"]
except prokon.v5.ProkonError as e:
    tail = e.message[e.message.find("[WinError"):]
    print(f"\n7) 485 load cases: {e.category} / {e.code}")
    print(f"   {tail}")
    print("   Batch a long schedule into calls of a couple of hundred cases.")

# --- 8. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout".
#
#        SET IT ON THIS FEATURE. The reference page records a measured
#        hang: "IS:456 - 2000 never returns for steel outside roughly
#        411-459 MPa" — at fy = 500 the process spins indefinitely, while
#        fy = 450 answers the same column in about 0.4 s. Two of the three
#        standard Indian grades fall outside that band, so an ordinary
#        call can hang rather than fail. A timeout turns that into an
#        exception you can branch on. (This script does not demonstrate
#        it — a documented hang is not something an example should run.)
prokon.v5.timeout_seconds = 300.0
print(f"\n8) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. It guards BOTH shapes: the
#     exception, and the successful call that designed a column nobody
#     could build. Unlike most features in this set, the "no_solution"
#     branch here is not defensive — section 5 fires it four ways.
MAX_STEEL_PERCENT = 6.0        # BS8110 3.12.6.2, a vertically cast column


def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.circular_column.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            return None, f"engine declined: {printable(e.message)}"
        if e.category == "invalid_input":
            return None, f"input problem: {printable(e.message)}"
        raise  # environment and timeout trouble should stop the run

    # The two checks the wire will not do for you.
    if not result["all_pass"]:
        return None, "a load case buckled"
    if result["percentage_steel"] > MAX_STEEL_PERCENT:
        return None, (f"{result['percentage_steel']:.2f} % steel, over the "
                      f"{MAX_STEEL_PERCENT:.0f} % limit")
    return result, None


print()
for label, inputs in (
        ("as given", GOOD),
        ("cover 105 of 220", {**GOOD, "cover": 105.0}),
        ("14 m effective length", {**GOOD, "lex": 14000.0, "ley": 14000.0}),
        ("free bottom, m1x = 60", {**GOOD, "end_cond_bot_x": "Free",
                                   "load_cases": [{"n": 700.0, "m1x": 60.0}]}),
        ("SP 63.13330.2018", {**GOOD, "design_code": "SP 63.13330.2018"})):
    result, reason = try_analyse(**inputs)
    verdict = (f"ok, As = {result['total_as']:.1f} mm2 "
               f"({result['percentage_steel']:.2f} %)" if result else reason)
    print(f"9) batch-safe call, {label:<22} -> {verdict}")

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
        prokon.v5.circular_column.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n10) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 10a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("10a  refused before dispatch", **{**GOOD, "design_code": "BS 8110"})

# 10b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("10b  refused by the engine", **{**GOOD, "cover": 110.0})

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
