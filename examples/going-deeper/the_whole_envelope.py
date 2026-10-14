# ---
# Example:  The whole envelope - everything analyse() hands you
# Feature:  beam_section + punching_shear + rectangular_slab (C22 + C23 + C04)
#           - the transport, not any one engine
# Verified: yes - 2026-09-10 - every field and behaviour, and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# analyse() gives you a VERSIONED ENVELOPE: the result, plus which engine
# answered, which host produced it, how long it took, what it warned about
# and what it logged. The computed answer is envelope["result"]; everything
# beside it is the record.
#
# Four things that live out there rather than in the result:
#   1. REPRODUCIBILITY   the engine version, in the record
#   2. FAILURE DETAIL    a failure raises, and the envelope rides the error
#   3. WARNINGS AS DATA  readable as strings, as well as Python warnings
#   4. TIMING            elapsed_milliseconds, for batches that must fit
#
# ⚠ THE ENVELOPE IS A PUBLISHED CONTRACT. Fields are added, never removed
# or renamed - which is what lets a script written today keep working. So
# reading an unknown field defensively is right, and assuming a field will
# disappear is not.

import prokon.v5

GOOD = dict(
    design_code="BS8110 - 1997",
    m=200.0, v=100.0, bw=300.0, h=500.0,
    dc_t=40.0, dc_b=40.0, dc_s=40.0,
    fcu=30.0, fy=450.0, fyv=450.0,
)

# ── 1. What is in there ────────────────────────────────────────────────
envelope = prokon.v5.beam_section.analyse(**GOOD)

print("1. THE ENVELOPE'S OWN FIELDS")
for key in sorted(envelope):
    value = envelope[key]
    if key == "result":
        print(f"   {key:<18} a dict of {len(value)} keys")
    elif isinstance(value, (list, dict)):
        print(f"   {key:<18} {type(value).__name__} of {len(value)}: {value}")
    else:
        print(f"   {key:<18} {value!r}")

print(f"\n   envelope_version is the INTEGER {envelope['envelope_version']!r},")
print(f"   not a string. Fields are added and never removed, so a script")
print(f"   that reads it can be written once.")
print(f"   the numbers you came for are under 'result':")
print(f"     mu = {envelope['result']['mu']} kNm")

# ── 2. Reproducibility ─────────────────────────────────────────────────
print(f"\n2. WHICH ENGINE ANSWERED")
print(f"   module          {envelope['module']}")
print(f"   module_version  {envelope['module_version']}")
print(f"   producer        {envelope['meta']['producer_version']}")
print(f"   started_at      {envelope['meta']['started_at']}")
print(f"   elapsed         {envelope['meta']['elapsed_milliseconds']} ms")
print(f"   -> module_version is the ENGINE's; producer_version is the HOST's.")
print(f"      They are different things and both belong in a calculation")
print(f"      record. Without them, 'PROKON says 295.2 kNm' is not a")
print(f"      reproducible statement.")

# Two engines in one process, each with its own version. That is the whole
# point of one binary carrying twelve of them.
other = prokon.v5.punching_shear.analyse(
    design_code="BS8110 - 1997",
    col_width=400.0, col_breadth=400.0, effective_depth=200.0,
    nearest_edge_x=10_000.0, nearest_edge_y=10_000.0,
    fcu=35.0, fy=500.0, fyv=500.0,
    load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}])
print(f"\n   a second engine, from the same executable:")
print(f"     {other['module']:<16} {other['module_version']}")
print(f"     {envelope['module']:<16} {envelope['module_version']}")
print(f"   same producer: "
      f"{other['meta']['producer_version'] == envelope['meta']['producer_version']}")
print(f"   -> one host, twelve engines, each versioned separately. A")
print(f"      calculation record needs the engine's version, not the")
print(f"      host's, to say which arithmetic ran.")

# ── 3. A failure raises, and carries the envelope ──────────────────────
# analyse() returns only when the run produced an answer, so a returned
# envelope has always reported ok and you never have to check for it. When
# the run produced no answer you get a ProkonError - and the whole document
# the engine sent is on it, so nothing is lost by raising.
print(f"\n3. A FAILURE RAISES - AND THE ENVELOPE RIDES THE ERROR")

BAD = {**GOOD, "design_code": "BS 8110"}

try:
    prokon.v5.beam_section.analyse(**BAD)
    print("   returned - unexpected")
except prokon.v5.ProkonError as refusal:
    print(f"   raised {type(refusal).__name__}: "
          f"{refusal.category}/{refusal.code}")
    print(f"     message  {refusal.message}")
    print(f"     hints    {len(refusal.hints)} value(s)")
    print(f"   and the whole envelope is still there:")
    print(f"     envelope keys  {sorted(refusal.envelope)}")
    print(f"     ok             {refusal.envelope['ok']}")
    print(f"     elapsed        {refusal.envelope['meta']['elapsed_milliseconds']} ms")
    print(f"   -> so a report generator writes the failure INTO the report")
    print(f"      instead of dying halfway through it, and does not have to")
    print(f"      choose between catching the error and keeping the record.")

    # ⚠ MEASURED, AND NOT WHAT YOU MIGHT ASSUME: THIS failure envelope
    # carries no 'module' and no 'module_version'. That is not a property
    # of failure - it is a property of WHEN the refusal happened. A bad
    # design_code is refused before the host has resolved which of its
    # twelve engines you meant, so there is no engine to name yet.
    print(f"   module_version present on a failure: "
          f"{'module_version' in refusal.envelope}")

# The contrast, on the same engine: a refusal the ENGINE itself made, after
# the host dispatched to it. Same category, same exception type - and the
# reproducibility fields are all there.
try:
    prokon.v5.beam_section.analyse(**{**GOOD, "h": 150.0,
                                      "dc_t": 90.0, "dc_b": 90.0})
    print("   returned - unexpected")
except prokon.v5.ProkonError as refusal:
    print(f"\n   the SAME category, refused AFTER dispatch:")
    print(f"     {refusal.category}/{refusal.code}")
    print(f"     module          {refusal.envelope.get('module')}")
    print(f"     module_version  {refusal.envelope.get('module_version')}")
    print(f"   -> so there are THREE states, not two, and reading the")
    print(f"      identity with .get() rather than [] is what makes one")
    print(f"      handler cover all of them:")
    print(f"        envelope is None            nothing came back")
    print(f"        envelope, module is None    the HOST refused")
    print(f"        envelope, module is a name  an ENGINE refused")

# ⚠ AND .envelope IS None WHEN THERE WAS NO ENVELOPE AT ALL - a timeout, an
# unlaunchable executable, unreadable output. Those are TRANSPORT failures:
# the engine never answered, so there is nothing to attach. That is how you
# tell the two apart in one line.
print(f"\n   a transport failure, where no envelope exists:")
saved = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    prokon.v5.beam_section.analyse(**GOOD)
    print("   a bad timeout was accepted - unexpected")
except prokon.v5.ProkonError as refusal:
    print(f"     {refusal.category}/{refusal.code}: {refusal.message}")
    print(f"     envelope is None: {refusal.envelope is None}")
finally:
    prokon.v5.timeout_seconds = saved
print(f"   -> THE RULE. Anything the HOST answered carries an envelope; a")
print(f"      TRANSPORT failure carries None. Both raise, so")
print(f"      `error.envelope is None` is the FIRST question - and")
print(f"      `envelope.get('module')` is the second, because an envelope")
print(f"      alone does not tell you an engine ran.")

# ── 4. Warnings, both ways ─────────────────────────────────────────────
import warnings

print(f"\n4. WARNINGS - AS PYTHON WARNINGS, AND AS DATA")

# rectangular_slab's crack-width codes warn loudly, so they make the point:
# BS8007 has no flexural rules, so the panel is solved and NO reinforcement is
# designed - a success, with every steel area zero, and a warning that says so.
_ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"
SLAB = dict(design_code="BS8007 - 1987",
            lx=7.5, ly=5.0, h=200.0, dx=165.0, dy=150.0,
            fcu=30.0, fy=450.0,
            edge_top=_ENCASTRE, edge_right=_ENCASTRE,
            edge_bottom=_ENCASTRE, edge_left=_ENCASTRE,
            load_cases=[{"number": 1, "lf": 1.4, "udl": 7.5}])

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    warned = prokon.v5.rectangular_slab.analyse(**SLAB)

print(f"   as Python warnings: {len(caught)} of category "
      f"{caught[0].category.__name__ if caught else '-'}")
if caught:
    sentence = str(caught[0].message).split(".")[0]
    print(f"     {sentence.encode('ascii', 'replace').decode()}.")

print(f"   as data:            {len(warned['warnings'])} string(s) in "
      f"envelope['warnings']")
for entry in warned["warnings"]:
    sentence = str(entry).split(".")[0]
    print(f"     {sentence.encode('ascii', 'replace').decode()}.")
print(f"   -> the SAME text, twice over, from ONE call. As a Python warning")
print(f"      it is visible by default and filterable; as a string it goes")
print(f"      into a report. A warning survives a SUCCESS because it is")
print(f"      actionable, so neither route should be silenced unread.")

# ── 5. Timing, and why a batch needs it ────────────────────────────────
print(f"\n5. TIMING   ten calls, measured by the engine itself")
elapsed = []
for depth in (400.0, 450.0, 500.0, 550.0, 600.0,
              650.0, 700.0, 750.0, 800.0, 850.0):
    single = prokon.v5.beam_section.analyse(**{**GOOD, "h": depth})
    elapsed.append(single["meta"]["elapsed_milliseconds"])

print(f"   per call: {elapsed}")
print(f"   min {min(elapsed)} ms, max {max(elapsed)} ms, "
      f"mean {sum(elapsed) / len(elapsed):.1f} ms")
print(f"   -> each call is a FRESH PROCESS: the executable starts, loads one")
print(f"      native library, answers, and exits. That is why the numbers")
print(f"      are what they are, and why a sweep of a thousand sections is")
print(f"      minutes rather than seconds.")
print(f"   -> the number to plan a batch with. 500 calls at "
      f"{sum(elapsed) / len(elapsed):.0f} ms is about")
print(f"      {500 * sum(elapsed) / len(elapsed) / 1000:.0f} s, and")
print(f"      prokon.v5.timeout_seconds applies PER CALL, not to the batch.")

# ── 6. Logs ────────────────────────────────────────────────────────────
print(f"\n6. LOGS")
print(f"   envelope['logs'] on a success: {envelope['logs']}")
print(f"   -> empty here. The field exists so that an engine which has")
print(f"      something to say can say it without inventing a channel, and")
print(f"      a script that reads it defensively keeps working when one")
print(f"      does. Iterate it; do not index it.")
print(f"   on a FAILURE the same list is on the error as .logs, beside")
print(f"   .warnings - so a failed run's diagnostics are not lost either.")

print(f"\n{'-' * 72}")
print("One call, one shape. envelope['result'] is the answer you came for;")
print("the fields beside it are what makes the answer a RECORD - which")
print("engine version produced it, how long it took, and what it warned")
print("about. A run that produced no answer raises instead, with the whole")
print("document on the error when there is one.")
