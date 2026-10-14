# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes — 2026-09-09 — behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "no_solution", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it — the allowed values, the input's own
#              description, or the engine's own refusal sentences
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT — or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. For a prestressed member that is
# only half the job: C02 analyses almost anything it is handed, and its
# most expensive answers are SUCCESSES — sections 4 to 6.
#
# (Only ASCII is printed below. Engine and validator sentences may carry
# characters a cp1252 console cannot render — printing an unmeasured
# message can crash the script on the print, not on the calculation.
# Every message printed here was measured to be plain ASCII.)

import prokon.v5

# A single-span post-tensioned slab strip: 5 m wide, 300 mm deep, 8 m,
# twelve unbonded cables, and the bottom steel the slab actually has.
GOOD = dict(
    design_code="BS8110 - 1997",
    fcu=19.2, fy=450.0, fyv=250.0, fci=14.4,        # MPa
    ec=26e6, est=206e6,                             # kN/m2
    density=24.0,                                   # kN/m3
    top_cover=25.0, bottom_cover=25.0,              # mm
    tendon_properties=[{"no": 1, "bond": "Unbonded", "strength": 260.7,
                        "max_stress_pct": 80, "dia": 18, "area": 140,
                        "k": 0.0015, "u": 0.05, "pullin": 5, "relax": 2,
                        "est": 195e6, "min_harp_radius": 1.0}],
    cable_sets=[{"n": 12, "prop": 1, "x_live": 0.0, "x_dead": 8.0,
                 "spans": [{"span": 1, "lo": 0, "ro": 0,
                            "b1": 150, "b2": 40, "b3": 150}]}],
    sections=[{"name": "slab", "bw": 5000, "d": 300}],
    span_segments=[{"span": 1, "length": 8.0, "sec_left": "slab"}],
    loads=[{"case": "D", "span": 1, "wl": 6.0},
           {"case": "L", "span": 1, "wl": 15.0}],
    additional_rebar=[{"span": 1, "pos": "B", "bars": "8Y16", "length": 8.0}],
)

# --- 1. A typo in a choice value: category "invalid_input", with hints.
#        Choice values are exact, INCLUDING capitals and spacing:
#        "bs8110 - 1997", "BS8110-1997" and a trailing space are all
#        refused the same way.
try:
    prokon.v5.prestressed_concrete.analyse(**{**GOOD, "design_code": "BS 8110"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   {len(e.hints)} allowed values, starting {', '.join(e.hints[:3])}, ...")

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
    prokon.v5.prestressed_concrete.analyse(**{k: v for k, v in GOOD.items() if k != "fcu"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fcu": None}
try:
    prokon.v5.prestressed_concrete.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   hint: {e.hints[0]}")

# --- 3. The engine's own validation refuses too — in its own words, and
#        those words are in .hints, NOT in .message. When the message
#        reads as a COUNT, the sentences are the hints. Here the design
#        code is spelled correctly and offered by the list above, but
#        prestressed design to IS:456 needs M40 concrete or better:
try:
    prokon.v5.prestressed_concrete.analyse(**{**GOOD, "design_code": "IS:456 - 2000"})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3) {e.category} / {e.code}")
    print(f"   {e.message}")
    for hint in e.hints:
        print(f"   engine: {hint}")

# --- 3b. A misspelt member of a grid row is REFUSED, not ignored — and
#         the error names the row by its full path and lists the members
#         it does know. That matters most on the nested cable grid:
bad_cables = [{"n": 12, "prop": 1, "x_live": 0.0, "x_dead": 8.0,
               "spans": [{"span": 1, "lo": 0, "ro": 0,
                          "b1": 150, "bb2": 40, "b3": 150}]}]   # "bb2"
try:
    prokon.v5.prestressed_concrete.analyse(**{**GOOD, "cable_sets": bad_cables})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n3b) {e.category} / {e.code}")
    print(f"   {e.message}")

# --- 4. And now know your feature. A BAR STRING THE ENGINE CANNOT READ
#        IS DROPPED, SILENTLY. The high-yield letter must match
#        bar_designation (default "Y"): write "8T16" and the engine keeps
#        only what it could parse — one 8 mm bar — with no exception and
#        no message. Read your steel back:
print("\n4) same call, same 'ok', read the steel back:")
for bars in ("8Y16", "8T16"):
    r = prokon.v5.prestressed_concrete.analyse(
        **{**GOOD, "additional_rebar": [{"span": 1, "pos": "B",
                                         "bars": bars, "length": 8.0}]})["result"]
    print(f"   bars={bars!r}: provided steel "
          f"{max(abs(v) for v in r['reinforcement']['aeb']):8.2f} mm2"
          f"   crack {max(r['crack_widths']['cwb']):6.3f} mm"
          f"   deflection {max(v for v in r['deflections']['ditot'] if v is not None):7.2f} mm")
# 1608.50 mm2 / 0.025 mm / 18.15 mm  ->  50.27 mm2 / 9.970 mm / 262.53 mm.
# One wrong letter cost nearly 400 times the crack width. (Set
# bar_designation to "T" or "#" if that is the letter your bars use.)

# --- 5. AND SANITY-CHECK THE DEFLECTIONS. On some models the long-term
#        deflection and crack-width series come back as astronomical
#        garbage — no exception, "messages" empty, and the ELASTIC
#        deflection beside them still perfectly plausible. Measured here
#        on a strip with generated cables and no additional_rebar:
generated = {k: v for k, v in GOOD.items()
             if k not in ("cable_sets", "additional_rebar")}
r = prokon.v5.prestressed_concrete.analyse(**generated, balanced_dead_load_pct=60.0)["result"]
d = r["deflections"]
print(f"\n5) generated cables, no additional_rebar: messages={r['messages']}")
print(f"   elastic deflection max {max(d['demax']):.2f} mm   - plausible")
print(f"   total   deflection max {max(d['ditot']):.3g} mm   - garbage")
print(f"   crack width max        {max(r['crack_widths']['cwb']):.3g} mm   - garbage")
print("   give the model its real bonded steel and both return to sense:")
r = prokon.v5.prestressed_concrete.analyse(
    **{k: v for k, v in GOOD.items() if k != "cable_sets"},
    balanced_dead_load_pct=60.0)["result"]
print(f"   total deflection max {max(r['deflections']['ditot']):.2f} mm"
      f"   crack width max {max(r['crack_widths']['cwb']):.3f} mm")

# --- 6. A THIRD SUCCESS-SHAPED TRAP: uls.asv carries a FAIL SENTINEL.
#        A position where shear-link design failed publishes Asv/Sv as
#        2e-9, the value the desktop's graph uses to mark FAIL. A
#        position that genuinely needs no links reads exactly 0. Read
#        "the maximum link steel is 0.000000002" as "the design failed":
narrow = {**GOOD, "design_code": "Eurocode 2 - 2004",
          "sections": [{"name": "beam", "bw": 300, "d": 500}],
          "span_segments": [{"span": 1, "length": 10.0, "sec_left": "beam"}],
          "cable_sets": [{"n": 12, "prop": 1, "x_live": 0.0, "x_dead": 10.0,
                          "spans": [{"span": 1, "lo": 0, "ro": 0,
                                     "b1": 250, "b2": 60, "b3": 250}]}],
          "loads": [{"case": "D", "span": 1, "wl": 10.0},
                    {"case": "L", "span": 1, "wl": 30.0}],
          "additional_rebar": [{"span": 1, "pos": "B", "bars": "8Y16",
                                "length": 10.0}]}
r = prokon.v5.prestressed_concrete.analyse(**narrow)["result"]
asv = r["uls"]["asv"]
print(f"\n6) 300 x 500 web, 10 m, 40 kN/m: deflection "
      f"{max((v for v in r['deflections']['ditot'] if v is not None), key=abs):.2f} mm, "
      f"max Asv/Sv = {max(asv)}")
print(f"   {sum(1 for v in asv if v == 2e-9)} of {len(asv)} positions are the "
      f"2e-9 FAIL sentinel, {sum(1 for v in asv if v == 0)} are a genuine zero")

# (There is no "no_solution" branch to write. The category is mapped, but
#  C02's validators mirror the desktop's Check-input guards and refuse
#  first — every failure reachable across the shapes probed here, choice
#  typos to zero-length spans, is "invalid_input".)

# --- 7. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout". Raise it for
#        a long member: one call solves the whole frame, up to 50 spans:
prokon.v5.timeout_seconds = 300.0
print(f"\n7) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. On this feature the guard
#     has to read the ANSWER as well as catch exceptions — sections 4-6.
def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.prestressed_concrete.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "invalid_input":
            reason = e.message
            if e.hints and "error(s)" in e.message:
                reason = "; ".join(e.hints)     # the engine's own sentences
            return None, f"input problem: {reason}"
        raise  # environment/timeout trouble should stop the run
    worst = max((v for v in result["deflections"]["ditot"] if v is not None),
                key=abs)
    if abs(worst) > 1000.0:                     # 1 m on an 8 m span
        return None, "deflections not computed (garbage magnitude)"
    if 2e-9 in result["uls"]["asv"]:
        return None, "shear link design failed at one or more positions"
    # A punching entry is published for EVERY support, but the ones you
    # did not ask about publish vc/vcap as None with failed = False:
    # test for None before comparing, or an unchecked column reads "OK".
    for column in result["punching"]:
        for perimeter in column["perimeters"]:
            if perimeter["vcap"] is not None and perimeter["failed"]:
                return None, f"punching fails at column {column['no']}"
    return result, None


# (No guard above catches section 4 — a dropped bar string produces a
#  perfectly well-formed answer to a model that is not yours. The only
#  defence is to read result["reinforcement"]["aeb"] back against the
#  steel you asked for.)

print("\n8) batch-safe calls:")
for label, model in (("as given", GOOD),
                     ("generated cables, no rebar",
                      dict(generated, balanced_dead_load_pct=60.0)),
                     ("300 x 500 web", narrow)):
    result, reason = try_analyse(**model)
    print(f"   {label}: {'ok' if result else reason}")

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
        prokon.v5.prestressed_concrete.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n9) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 9a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("9a  refused before dispatch", **{**GOOD, "design_code": "BS 8110"})

# 9b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("9b  refused by the engine", **{**GOOD, "design_code": "IS:456 - 2000"})

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
