# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  continuous_beam (C01 Continuous Beam)
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
# A robust script branches on .category. On THIS feature the model is four
# grids, so most of the refusals you will meet are grid refusals — and they
# name the row and the member. The sections after 5 are the other half: the
# results that come back looking perfectly successful and are not what
# their names suggest.

import prokon.v5

# The reference two-span beam: 2 x 6 m of a 300 x 500 rectangle, 20 kN/m
# dead + 10 kN/m live, BS8110 - 1997. Same model as the quick-start.
GOOD = dict(
    design_code="BS8110 - 1997",
    sections=[{"n": 1, "bw": 300, "d": 500}],
    segments=[{"span": 1, "length": 6, "sec_left": 1},
              {"span": 2, "length": 6, "sec_left": 1}],
    supports=[{"n": 1}, {"n": 2}, {"n": 3}],
    loads=[{"case": "Dead", "span": 1, "w_left": 20},
           {"case": "Dead", "span": 2, "w_left": 20},
           {"case": "Live", "span": 1, "w_left": 10},
           {"case": "Live", "span": 2, "w_left": 10}],
    fyv=250.0, cover_top=30.0, cover_bot=40.0,
    live_permanent_percent=25.0, creep_coefficient=2.0,
    shrinkage_strain=300e-6,
)

# --- 1. A typo in a choice value: category "invalid_input", with hints.
#        Choice values are exact, INCLUDING capitals and the spacing:
#        "bs8110 - 1997" and "BS 8110" are both refused. Note that this
#        program spells some codes differently from other features, so
#        copy from .hints rather than from another feature's page.
try:
    prokon.v5.continuous_beam.analyse(**{**GOOD, "design_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   all {len(e.hints)} design codes are in .hints: "
          f"{', '.join(e.hints[:4])}, ...")

# --- 2a. LEAVE AN ARGUMENT OUT and PYTHON refuses, before any engine
#         process is launched. analyse() takes real keyword-only
#         parameters, so a misspelled name is caught the same way -- and
#         Python usually suggests the one you meant:
#             analyse() got an unexpected keyword argument 'design_codex'.
#             Did you mean 'design_code'?
#         Usually, not always: the suggestion is Python's own
#         edit-distance heuristic, and it gives up on a long enough
#         mangling ('DESIGN_CODE' gets no suggestion at all).
try:
    prokon.v5.continuous_beam.analyse(**{k: v for k, v in GOOD.items() if k != "design_code"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "design_code": None}
try:
    prokon.v5.continuous_beam.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   hint: {e.hints[0]}")

# --- 3. A MALFORMED GRID gets its own code — one per table:
#        INVALID_SECTIONS, INVALID_SEGMENTS, INVALID_SUPPORTS,
#        INVALID_LOAD_CASES. A member the command does not read is
#        REFUSED, never ignored: a misspelt "sec_lft" cannot silently
#        become a defaulted section 0, and the refusal names the row, the
#        member and every member the table does read.
try:
    prokon.v5.continuous_beam.analyse(
        **{**GOOD, "segments": [{"span": 1, "length": 6, "sec_lft": 1},
                                {"span": 2, "length": 6, "sec_left": 1}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 3b. The same grammar refuses a missing required member, a value of
#         the wrong JSON type and a mis-cased choice value — each naming
#         the row. A wrong choice value carries the allowed names:
for label, table, rows in (
        ("missing member", "sections", [{"n": 1, "d": 500}]),
        ("wrong type", "sections", [{"n": 1, "bw": "300", "d": 500}]),
        ("mis-cased choice", "loads", [{"case": "dead", "span": 1, "w_left": 20}])):
    try:
        prokon.v5.continuous_beam.analyse(**{**GOOD, table: rows})["result"]
    except prokon.v5.ProkonError as e:
        print(f"   3b {label:17s} {e.code:20s} {e.message}")

# --- 4. Model-level problems are COLLECTED, not thrown one at a time.
#        An inconsistent model is one INVALID_INPUT refusal with every
#        finding as its own hint, so one round trip tells you everything
#        that is wrong. Here two segments name sections that do not exist
#        AND the support count does not match the span count:
try:
    prokon.v5.continuous_beam.analyse(
        **{**GOOD,
           "segments": [{"span": 1, "length": 6, "sec_left": 7},
                        {"span": 2, "length": 6, "sec_left": 9}],
           "supports": [{"n": 1}, {"n": 2}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n4) {e.category} / {e.code}")
    print(f"   {e.message.splitlines()[0]}")
    for hint in e.hints:
        print(f"     - {hint}")

# --- 5. The engine's own range checks refuse the same way, in the
#        engine's words, with the count in the message. This is the input
#        most often got wrong on this feature — shrinkage is a STRAIN, so
#        300 microstrain is 300e-6, and a bare 300 is out of range:
try:
    prokon.v5.continuous_beam.analyse(**{**GOOD, "shrinkage_strain": 300.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n5) {e.category} / {e.code}")
    print(f"   {e.message}   ->   {e.hints[0]}")

# --- 6. AND NOW THE HARD PART: THERE IS NO "no_solution" HERE. Every
#        refusal above is raised BEFORE the engine computes. Once a model
#        is well formed the engine designs it, however unbuildable it is,
#        and reports success. This 300 x 500 under 200 kN/m dead is a
#        successful analysis:
r = prokon.v5.continuous_beam.analyse(
    **{**GOOD, "loads": [{"case": "Dead", "span": 1, "w_left": 200},
                         {"case": "Dead", "span": 2, "w_left": 200}],
       "fyv": 250.0, "cover_top": 30.0, "cover_bot": 30.0,
       "live_permanent_percent": 0.0, "creep_coefficient": 0.0,
       "shrinkage_strain": 0.0})["result"]
env = r["envelopes"]
over = sum(1 for i in range(r["position_count"])
           if env["moment_positive"][i] > env["moment_capacity_bottom"][i])
print(f"\n6) 200 kN/m on a 300x500: no exception at all")
print(f"   As-bot {r['spans'][0]['max_bottom_steel']:.0f} mm2, "
      f"Asv/sv {r['spans'][0]['max_shear_steel']:.2f} mm2/mm")
print(f"   applied moment exceeds moment_capacity_bottom at {over} of "
      f"{r['position_count']} positions - and it still 'succeeded'")

# --- 6b. So compare demand against capacity yourself. The capacity
#         envelopes are section properties, not verdicts: where the
#         applied envelope passes them the engine simply designs
#         compression steel. moment_capacity_top is <= 0 everywhere and
#         moment_capacity_bottom >= 0, so the two comparisons run in
#         opposite directions:
print(f"   capacities on this beam: bottom {env['moment_capacity_bottom'][0]:+.1f} kNm, "
      f"top {env['moment_capacity_top'][0]:+.1f} kNm")

# --- 7. KNOW YOUR ENVELOPES: THE "PROVIDED" SERIES ARE NOT A CHECK.
#        Bar detailing is not exposed in this version, so the entered-bar
#        arrays the engine's second design pass reads are empty. Design
#        from the REQUIRED series; the provided ones are the residue of
#        that second pass:
r = prokon.v5.continuous_beam.analyse(**GOOD)["result"]
env, n = r["envelopes"], r["position_count"]
zero_bars = all(v == 0 for v in env["ast_bottom_provided"]) \
    and all(v == 0 for v in env["ast_top_provided"])
below_nominal = sum(1 for i in range(n)
                    if env["asv_provided"][i] < env["asv_nominal"][i])
print(f"\n7) the reference beam: {len(env)} envelopes x {n} positions")
print(f"   ast_bottom_provided / ast_top_provided all zero: {zero_bars}")
print(f"   asv_required peaks at {max(env['asv_required']):.4f} mm2/mm, "
      f"asv_nominal is {env['asv_nominal'][0]:.3f} everywhere")
print(f"   asv_provided reaches {max(env['asv_provided']):.4f} but falls BELOW "
      f"the nominal floor at {below_nominal} of {n} positions,")
print(f"   as low as {min(v for v in env['asv_provided'] if v > 0):.4f} mm2/mm "
      f"- design links from asv_required and asv_nominal")

# --- 7b. shear_capacity_provided is the same story: the concrete-only
#         capacity of a pass that saw no tension steel. It never rises
#         above shear_capacity_concrete, and neither of the two includes
#         links:
worst = min(range(n), key=lambda i: env["shear_capacity_concrete"][i])
print(f"   shear_capacity_provided {env['shear_capacity_provided'][worst]:.2f} kN vs "
      f"shear_capacity_concrete {env['shear_capacity_concrete'][worst]:.2f} kN "
      f"at x = {env['position'][worst]:.1f} m")

# --- 8. TWO MORE KEYS THAT DO NOT MEAN WHAT THEY SAY.
#        total_mass is a FORCE in kN — the self-weight generated from
#        concrete_density — not a mass. And crack widths are asymmetric
#        on this surface: the crack_width_top envelope is all zeros, so
#        the bottom face is only reachable through the per-span key.
r = prokon.v5.continuous_beam.analyse(**{**GOOD, "concrete_density": 24.0})["result"]
print(f"\n8) total_mass = {r['total_mass']:.1f} - that is 1.8 m3 x 24 kN/m3, "
      f"a WEIGHT in kN")
print(f"   crack_width_top all zero: "
      f"{all(v == 0 for v in r['envelopes']['crack_width_top'])}; "
      f"read max_bottom_crack_width per span: "
      f"{[round(s['max_bottom_crack_width'], 4) for s in r['spans']]}")

# --- 9. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout", code
#        ENGINE_DID_NOT_ANSWER. Ordinary runs return in well under a
#        second, but the engine CAN stop answering: covers too large for
#        the section — cover_top 250 on a 500 mm deep beam, for instance —
#        leave the call unanswered until the timeout stops it, rather than
#        refusing. Keep the timeout finite in a batch, so one bad row
#        costs you a timeout rather than the run.
prokon.v5.timeout_seconds = 300.0
print(f"\n9) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. Note what is NOT here: no
#     "no_solution" branch. `analyse` never returns one — every refusal
#     measured on this feature is "invalid_input", raised before the
#     engine computes — so the adequacy check has to be folded in beside
#     the exceptions, or an unbuildable beam quietly reports as a success.
def try_analyse(span_length_m, **inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.continuous_beam.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "invalid_input":
            # .hints carries every finding when the model itself is wrong,
            # so report those rather than the one-line summary.
            return None, "input problem: " + ("; ".join(e.hints) or e.message)
        raise  # environment and timeout trouble should stop the run

    env = result["envelopes"]
    fails = []
    if any(env["moment_positive"][i] > env["moment_capacity_bottom"][i]
           for i in range(result["position_count"])):
        fails.append("sagging over capacity")
    if any(env["moment_negative"][i] < env["moment_capacity_top"][i]
           for i in range(result["position_count"])):
        fails.append("hogging over capacity")
    if result["max_deflection"] > span_length_m * 1000.0 / 250.0:
        fails.append("deflection over span/250")
    if fails:
        return None, "beam inadequate: " + " + ".join(fails)
    return result, None


HEAVY = {**GOOD, "loads": [{"case": "Dead", "span": 1, "w_left": 200},
                           {"case": "Dead", "span": 2, "w_left": 200}]}
for label, inputs in (("as given", GOOD),
                      ("200 kN/m", HEAVY),
                      ("two supports", {**GOOD, "supports": [{"n": 1}, {"n": 2}]})):
    result, reason = try_analyse(6.0, **inputs)
    print(f"10) batch-safe call, {label}: {'ok' if result else reason}")

# --- 11. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
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
        prokon.v5.continuous_beam.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n11) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 11a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("11a  refused before dispatch", **{**GOOD, "design_code": "BS 8110"})

# 11b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("11b  refused by the engine", **{**GOOD, "shrinkage_strain": 300.0})

# 11c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("11c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")
