# ---
# Example:  Limits - how big a call can be, and how long it may take
# Feature:  rectangular_column + continuous_beam (C11 + C01) - the transport
# Verified: yes - 2026-09-09 - every limit and refusal, and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# Three limits sit between your script and an engine, and they are
# different in kind:
#
#   1. THE ENGINE'S OWN LIMIT      C11 takes up to 5000 load cases; C01
#                                  takes 60 sections, 200 segments,
#                                  300 loads. Documented, and refused
#                                  cleanly.
#   2. THE OPERATING SYSTEM'S      every input travels as a command-line
#                                  argument, and Windows can launch at
#                                  most 32 766 characters. Reached long
#                                  before the engine's own limit.
#   3. YOUR TIMEOUT                prokon.v5.timeout_seconds, PER CALL and
#                                  not per batch.
#
# ⚠ THE SECOND ONE IS THE SURPRISE. C11 advertises 5000 load cases and the
# command line runs out at a few hundred. The engine's limit is real and
# unreachable - which is the sort of thing worth knowing before you write
# the loop, not after.

import prokon.v5

CODE = "SABS 0100 - 2000"

COLUMN = dict(
    design_code=CODE, h=400.0, b=400.0, dc_x=40.0, dc_y=40.0,
    fcu=30.0, fy=450.0, lex=3000.0, ley=3000.0,
    bracing_x="Braced", bracing_y="Braced", betad=0.6, deltas=1.0,
)

print("LIMITS, TIMEOUTS AND BATCHING")

# ── 1. Where the command line runs out ─────────────────────────────────
# Bisect the number of load cases C11 will accept in ONE call. The
# refusal is not the engine's; it happens before the process starts.
print(f"\n1. HOW MANY LOAD CASES FIT IN ONE CALL?")
print(f"   C11's documented engine limit: 5000")


def try_cases(count):
    """(True, note) or (False, reason)."""
    cases = [{"n": 1500.0 + index, "m2x": 100.0, "m1x": 50.0,
              "m2y": 60.0, "m1y": 30.0} for index in range(count)]
    try:
        result = prokon.v5.rectangular_column.analyse(**COLUMN,
                                                    load_cases=cases)["result"]
        return True, f"{len(result['options'])} arrangement(s)"
    except prokon.v5.ProkonError as refusal:
        return False, f"{refusal.category}/{refusal.code}"


print(f"   {'cases':>7}  outcome")
for count in (1, 10, 100, 200, 400, 500, 600, 1000, 5000):
    ok, note = try_cases(count)
    print(f"   {count:>7}  {'ok - ' + note if ok else 'REFUSED - ' + note}")

low, high = 1, 5000
for _ in range(14):
    middle = (low + high) // 2
    ok, _ = try_cases(middle)
    if ok:
        low = middle
    else:
        high = middle

print(f"\n   the boundary: {low} cases launch, {high} do not.")
ok, reason = try_cases(high)
print(f"   at {high}: {reason}")
try:
    try_cases(high)
except Exception:
    pass
try:
    cases = [{"n": 1500.0 + index, "m2x": 100.0, "m1x": 50.0,
              "m2y": 60.0, "m1y": 30.0} for index in range(high)]
    prokon.v5.rectangular_column.analyse(**COLUMN, load_cases=cases)["result"]
except prokon.v5.ProkonError as refusal:
    print(f"   full refusal: {refusal.category} / {refusal.code}")
    print(f"     {refusal.message.encode('ascii', 'replace').decode()[:120]}")
    for hint in refusal.hints[:2]:
        print(f"     hint: {hint.encode('ascii', 'replace').decode()[:110]}")

print(f"\n   -> the engine advertises 5000 and the transport stops at about")
print(f"      {low}. The limit that binds is the OPERATING SYSTEM's command")
print(f"      line, because every input travels on it. And the exact cut-off")
print(f"      MOVES with the width of your numbers: wider values, fewer")
print(f"      cases. So do not hard-code {low} - batch, and let the refusal")
print(f"      tell you when a batch is too big.")

# ── 2. The batching pattern ────────────────────────────────────────────
# Split, run, and recombine. The results are per-case, so recombining is
# concatenation - but the SUMMARY keys are per-call and have to be
# re-derived across the batches.
print(f"\n2. THE BATCHING PATTERN")

TOTAL = 900
BATCH = 200
all_cases = [{"n": 1000.0 + 5.0 * index, "m2x": 80.0 + 0.1 * index,
              "m1x": 40.0, "m2y": 50.0, "m1y": 25.0}
             for index in range(TOTAL)]

print(f"   {TOTAL} cases in batches of {BATCH}")
print(f"   {'batch':>6} {'cases':>6} {'arrangements':>13} "
      f"{'lightest %':>11} {'feasible':>9}")

lightest_overall = None
batches = 0
for start in range(0, TOTAL, BATCH):
    chunk = all_cases[start:start + BATCH]
    batches += 1
    result = prokon.v5.rectangular_column.analyse(**COLUMN, load_cases=chunk)["result"]
    passing = [option for option in result["options"] if option["all_pass"]]
    lightest = min((option["perc"] for option in passing), default=None)
    if lightest is not None:
        lightest_overall = (lightest if lightest_overall is None
                            else max(lightest_overall, lightest))
    print(f"   {batches:>6} {len(chunk):>6} {len(result['options']):>13} "
          f"{'-' if lightest is None else format(lightest, '.3f'):>11} "
          f"{str(result['has_feasible_design']):>9}")

print(f"\n   -> the steel that must be provided is the WORST of the batch")
print(f"      minima, {lightest_overall:.3f} % here - NOT the minimum of the")
print(f"      minima. Recombining a batch means re-deriving the summary,")
print(f"      and getting that direction wrong under-designs the column.")

# ── 3. C01's own table limits, which are the engine's and are clean ───
print(f"\n3. C01's TABLE LIMITS   these ARE the engine's, and they refuse "
      f"cleanly")

BEAM = dict(design_code="BS8110 - 1997", fcu=30.0, fy=450.0, fyv=250.0)


def try_spans(count):
    try:
        prokon.v5.continuous_beam.analyse(
            **BEAM,
            sections=[{"n": 1, "bw": 300.0, "d": 500.0}],
            segments=[{"span": index + 1, "length": 4.0, "sec_left": 1}
                      for index in range(count)],
            supports=[{"n": index + 1} for index in range(count + 1)],
            loads=[{"case": "Dead", "span": 1, "w_left": 20.0}])["result"]
        return True, ""
    except prokon.v5.ProkonError as refusal:
        return False, (f"{refusal.category}/{refusal.code}: "
                       f"{refusal.message.encode('ascii', 'replace').decode()[:70]}")


print(f"   {'spans':>7} {'supports':>9}  outcome")
for count in (1, 10, 30, 55, 59, 60, 61, 80):
    ok, reason = try_spans(count)
    print(f"   {count:>7} {count + 1:>9}  "
          f"{'ok' if ok else reason.splitlines()[0]}")
    if not ok:
        for line in reason.splitlines()[1:]:
            print(f"   {'':>7} {'':>9}  {line.strip()}")
print(f"   -> 59 spans is the most this model takes, and the refusal says")
print(f"      why: a beam has one more SUPPORT than it has spans, and")
print(f"      supports are capped at 60. The engine names the table and")
print(f"      the number, which is what a limit should look like.")
print(f"   -> compare that with section 1, where the refusal is about a")
print(f"      command line and says nothing about your model - because")
print(f"      nothing of yours had run yet.")

# ── 4. The timeout, which is per call ──────────────────────────────────
print(f"\n4. THE TIMEOUT IS PER CALL, NOT PER BATCH")
print(f"   prokon.v5.timeout_seconds = {prokon.v5.timeout_seconds} (the default)")

# A timeout so small that nothing can finish, to see the category.
saved = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = 0.001
    prokon.v5.rectangular_column.analyse(
        **COLUMN, load_cases=[{"n": 1500, "m2x": 100, "m1x": 50,
                               "m2y": 60, "m1y": 30}])["result"]
    print(f"   at 0.001 s the call SUCCEEDED - faster than the timeout")
except prokon.v5.ProkonError as refusal:
    print(f"   at 0.001 s: {refusal.category} / {refusal.code}")
    print(f"     {refusal.message.encode('ascii', 'replace').decode()[:100]}")
finally:
    prokon.v5.timeout_seconds = saved

print(f"   back to {prokon.v5.timeout_seconds} s")

# And what a bad timeout does, which is refuse before launching anything.
for value in (0, -5, "300", None):
    try:
        prokon.v5.timeout_seconds = value
        prokon.v5.rectangular_column.analyse(
            **COLUMN, load_cases=[{"n": 1500, "m2x": 100, "m1x": 50,
                                   "m2y": 60, "m1y": 30}])["result"]
        print(f"   timeout_seconds = {value!r:<8} accepted "
              f"({'waits indefinitely' if value is None else 'unexpected'})")
    except prokon.v5.ProkonError as refusal:
        print(f"   timeout_seconds = {value!r:<8} {refusal.category}/"
              f"{refusal.code}")
    finally:
        prokon.v5.timeout_seconds = saved

print(f"   -> None means WAIT FOREVER and is accepted deliberately; 0 and")
print(f"      a negative are refused, and so is a string. A batch that must")
print(f"      finish by a deadline needs its OWN clock: this setting bounds")
print(f"      each call, and a thousand calls at the limit is a thousand")
print(f"      times the limit.")

# -- 5. WHICH OF THESE THREE LIMITS LEAVES YOU A DOCUMENT --------------
# Every failure above raised prokon.v5.ProkonError. Only SOME of them
# left a document behind, and the difference is exactly whether the
# engine ever ran. The whole envelope rides the error as .envelope:
#
#   .envelope is None           nothing was launched, or nothing came
#                               back. There is no document. ASK THIS FIRST.
#   envelope, module is None    the HOST refused before it dispatched -
#                               an envelope, but no engine to name.
#   envelope, module is a name  an ENGINE ran and refused. The full record.
#
# For THIS file that split is the headline: two of the three limits never
# reach an engine, so two of them can tell you nothing about your model.

def diagnose(failure):
    """Everything worth recording about a failed analyse(), from the error alone."""
    record = {
        "category": failure.category,
        "code": failure.code,
        "hints": failure.hints,
        "warnings": failure.warnings,   # off the envelope; empty when there is none
        "logs": failure.logs,           # likewise
    }

    if failure.envelope is None:
        record["has_envelope"] = False
        return record                   # nothing else exists. Do not reach further.

    envelope = failure.envelope
    meta = envelope.get("meta") or {}

    record["has_envelope"] = True
    record["module"] = envelope.get("module")                  # None before dispatch
    record["module_version"] = envelope.get("module_version")  # None before dispatch
    record["elapsed_ms"] = meta.get("elapsed_milliseconds")
    return record


def diagnosed(label, call):
    try:
        call()
        print(f"   {label:<24} returned - unexpected")
    except prokon.v5.ProkonError as failure:
        record = diagnose(failure)
        print(f"   {label:<24} {record['category']}/{record['code']}")
        for key in ("has_envelope", "module", "module_version", "elapsed_ms"):
            if key in record:
                print(f"     {key:<20} {record[key]}")

print(f"\n5. WHICH FAILURES LEAVE A DOCUMENT BEHIND")

ONE_CASE = [{"n": 1500.0, "m2x": 100.0, "m1x": 50.0, "m2y": 60.0, "m1y": 30.0}]

# 5a. Limit 2 - the command line. Nothing was ever launched.
diagnosed("5a the command line", lambda: prokon.v5.rectangular_column.analyse(
    **COLUMN, load_cases=[{"n": 1500.0 + index, "m2x": 100.0, "m1x": 50.0,
                           "m2y": 60.0, "m1y": 30.0} for index in range(600)]))

# 5b. Limit 1 - the engine's own table. It ran, and it refused BY NAME,
#     so the record carries which engine and which version said so.
diagnosed("5b the engine's table", lambda: prokon.v5.continuous_beam.analyse(
    **BEAM,
    sections=[{"n": 1, "bw": 300.0, "d": 500.0}],
    segments=[{"span": index + 1, "length": 4.0, "sec_left": 1}
              for index in range(61)],
    supports=[{"n": index + 1} for index in range(62)],
    loads=[{"case": "Dead", "span": 1, "w_left": 20.0}]))

# 5c. Limit 3 - your timeout. It was launched and killed, so there is no
#     document either: a process that never answered wrote nothing.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = 0.001
    diagnosed("5c your timeout", lambda: prokon.v5.rectangular_column.analyse(
        **COLUMN, load_cases=ONE_CASE))
finally:
    prokon.v5.timeout_seconds = saved_timeout

print(f"   -> the command line and the timeout leave NO envelope, because")
print(f"      in one case nothing ran and in the other nothing came back.")
print(f"      Only the engine's own table limit gives you a document, and")
print(f"      it is the only one of the three that knows your model.")
print(f"   -> so the batch log for a limit failure should record the")
print(f"      diagnosis, not the sentence. `failure.envelope is None` is")
print(f"      what tells you whether there was anything to record.")

print(f"\n{'-' * 72}")
print("The three limits, in the order you will meet them:")
print("  * the command line, at a few hundred load cases - batch for it;")
print("  * the engine's own tables, refused by name - respect them;")
print("  * your timeout, per call - budget the batch yourself.")
print("And when you recombine a batch, re-derive the summary rather than")
print("summarising the summaries. That is the one that quietly")
print("under-designs.")
