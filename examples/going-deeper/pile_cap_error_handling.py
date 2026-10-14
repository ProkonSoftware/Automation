# ---
# Example:  Error handling — what a failed call looks like, and how to branch on it
# Feature:  pile_cap (C16 Pile Cap)
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
# A robust script branches on .category. On this feature that pays off:
# pile_cap genuinely raises "no_solution" for a well-formed cap it ran and
# declined (section 6), and pile uplift is the everyday cause. Any layout
# search has to survive it.
#
# It also has the opposite failure. Sections 7 to 11 all arrive as
# SUCCESS — a result dictionary, no exception — carrying a cap you must
# not build, or a key that cannot mean what it looks like it means. Read
# those twice.
#
# NOTE: every length on this feature is in METRES — cap, piles and column
# alike — matching the desktop program's own input page.

import prokon.v5

GOOD = dict(
    design_code="CSA-A23.3:2019",
    column_dim_x=0.5, column_dim_y=0.5,
    no_of_piles=4, pile_dia=0.6, pile_spacing=1.8, pile_tolerance=0.05,
    cap_thickness=1.2, cap_overhang=0.3, bottom_rebar_depth=0.1,
    fc=30.0, fy=400.0,
    load_cases=[{"name": "ULS", "load_factor": 1.0, "p": 4000.0}],
)


def plain(text):
    """Engine prose, made safe for any console.

    Most of this feature's messages are plain ASCII, but two are not:
    the uplift refusal in section 6 carries a real em dash, and so does
    the `load_cases` description that a malformed schedule quotes back at
    you (section 5b). On a cp1252 or cp437 console printing those raw
    raises UnicodeEncodeError and takes the script down at the exact
    moment it was reporting a problem. Substituting is the safe default;
    drop this helper only if you control the console.
    """
    return text.encode("ascii", "replace").decode()


# --- 1. A typo in a choice value: category "invalid_input", with the
#        whole allowed list in .hints. Choice values are exact, INCLUDING
#        capitals and stray whitespace — "csa-a23.3:2019" and
#        "CSA-A23.3:2019 " are both refused exactly like "CSA A23.3":
try:
    prokon.v5.pile_cap.analyse(**{**GOOD, "design_code": "CSA A23.3"})["result"]
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   all {len(e.hints)} design codes are in .hints: {', '.join(e.hints)}")

# --- 2a. LEAVE AN ARGUMENT OUT and PYTHON refuses, before any engine
#         process is launched. analyse() takes real keyword-only
#         parameters, so a misspelled name is caught the same way -- and
#         Python usually suggests the one you meant:
#             analyse() got an unexpected keyword argument 'fcx'.
#             Did you mean 'fc'?
#         Usually, not always: the suggestion is Python's own
#         edit-distance heuristic, and it gives up on a long enough
#         mangling ('FC' gets no suggestion at all).
try:
    prokon.v5.pile_cap.analyse(**{k: v for k, v in GOOD.items() if k != "fc"})["result"]
except TypeError as e:
    print("\n2a) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 2b. PASS IT AS None and the ENGINE refuses, as "invalid_input" /
#         MISSING_REQUIRED_INPUT. This is the one that bites in practice:
#         a blank spreadsheet cell reads as None, and PROKON never
#         quietly substitutes a value the calculation depends on.
incomplete = {**GOOD, "fc": None}
try:
    prokon.v5.pile_cap.analyse(**incomplete)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   hint: {plain(e.hints[0])}")

# --- 3. A misspelt input NAME is refused too, never silently ignored --
#        and PYTHON is what refuses it, because analyse() declares one
#        real parameter per input. So "cap_thicknes" cannot quietly
#        become a missing "cap_thickness" and design a thinner cap: the
#        call never happens, and the suggestion is free.
typo = {k: v for k, v in GOOD.items() if k != "cap_thickness"}
try:
    prokon.v5.pile_cap.analyse(**typo, cap_thicknes=1.2)["result"]
except TypeError as e:
    print("\n3) TypeError -- Python refused; no engine was launched")
    print(f"   {e}")

# --- 4. The validation refuses in its own words — still "invalid_input",
#        code INVALID_INPUT — and it publishes ONE HINT PER RULE that
#        failed. The message has them all joined into a sentence; the
#        hints have them separately, so report the list, not the blob.
#        One round trip tells you everything that is wrong:
try:
    prokon.v5.pile_cap.analyse(**{**GOOD, "column_dim_x": 9.0,
                               "cap_thickness": 1.0, "pile_spacing": 3.0,
                               "cap_overhang": 0.0})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n4) {e.category} / {e.code}   ({len(e.hints)} hints)")
    print(f"   {e.message}")
    for hint in e.hints:
        print(f"     - {hint}")

# --- 4b. Same code, different author: rules the ARGUMENT READER cannot
#        express are checked by the wrapper before the engine is called,
#        and there the hints are the allowed values instead:
for bad in (4.5, 6):
    try:
        prokon.v5.pile_cap.analyse(**{**GOOD, "no_of_piles": bad})["result"]
    except prokon.v5.ProkonError as e:
        print(f"\n4b) {e.code}: {e.message}")
        print(f"    hints: {e.hints}")

# --- 5. The load schedule has its own code, and its hints are EMPTY —
#        the message carries the whole explanation. A member the command
#        does not read is refused rather than defaulted, so a misspelt
#        "mxx" cannot silently become a zero moment:
try:
    prokon.v5.pile_cap.analyse(**{**GOOD, "load_cases": [
        {"name": "ULS", "load_factor": 1.0, "p": 4000.0, "mxx": 150.0}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n5) {e.category} / {e.code}   ({len(e.hints)} hints)")
    print(f"   {plain(e.message)}")

# --- 5b. The same code covers the grouping rules. Rows sharing a name are
#        summed into one factored combination, and an empty name continues
#        the previous row — but a name that comes BACK after a different
#        one is refused rather than answered, because the engine would
#        group it wrongly and the wrong answer would look right. This is
#        the second message that needs plain(): it quotes the schedule's
#        own description, em dashes and all.
try:
    prokon.v5.pile_cap.analyse(**{**GOOD, "load_cases": [
        {"name": "A", "load_factor": 1.0, "p": 1000.0},
        {"name": "B", "load_factor": 1.0, "p": 1000.0},
        {"name": "A", "load_factor": 1.0, "p": 1000.0}]})["result"]
except prokon.v5.ProkonError as e:
    print(f"\n5b) {e.code}: {plain(e.message)}")

# --- 6. THE ONE WORTH BRANCHING ON: a well-formed cap the engine ran and
#        declined. Category "no_solution", no hints — the sentence is the
#        whole answer. The everyday cause is pile uplift, and this is the
#        message that needs plain(): it carries a real em dash.
UPLIFT = {**GOOD, "load_cases": [
    {"name": "ULS", "load_factor": 1.0, "p": 1000.0, "mx": 936.0}]}
try:
    prokon.v5.pile_cap.analyse(**UPLIFT)["result"]
except prokon.v5.ProkonError as e:
    print(f"\n6) {e.category} / {e.code}   ({len(e.hints)} hints)")
    print(f"   {plain(e.message)}")

# --- 6b. It is a sharp edge, not a gradual one, and that is what makes
#        it a NORMAL outcome in a search: nudge the moment down and the
#        same cap designs. "invalid_input" never becomes designable this
#        way; "no_solution" often does.
for mx in (930.0, 935.0, 936.0):
    try:
        r = prokon.v5.pile_cap.analyse(**{**GOOD, "load_cases": [
            {"name": "ULS", "load_factor": 1.0, "p": 1000.0, "mx": mx}]})["result"]
        least = min(f["p"] for pile in r["pile_forces"] for f in pile)
        print(f"6b) mx = {mx:5.0f} kNm -> designed, least pile reaction {least:6.2f} kN")
    except prokon.v5.ProkonError as e:
        print(f"6b) mx = {mx:5.0f} kNm -> {e.category} ({plain(e.message)})")

# --- 6c. The same category has a second, much less obvious cause. A
#        `load_factor` of 0 DROPS its row. Drop every row and the
#        schedule is empty by the time the engine sees it, and what comes
#        back is the engine's raw range check, not a helpful sentence.
#        (A row whose `p` is 0 is caught earlier, and says so properly —
#        so the two ways of asking for nothing are NOT reported alike.)
for label, rows in (
        ("p = 0, factor 1", [{"name": "U", "load_factor": 1.0, "p": 0.0}]),
        ("p = 4000, factor 0", [{"name": "U", "load_factor": 0.0, "p": 4000.0}])):
    try:
        prokon.v5.pile_cap.analyse(**{**GOOD, "load_cases": rows})["result"]
    except prokon.v5.ProkonError as e:
        print(f"6c) {label:<20} -> {e.category} / {e.code}: {plain(e.message)}")

# --- 7. NOW THE FAILURES THAT SUCCEED. The engine reports demand and
#        capacity; the verdict is yours. An inadequate cap is a
#        SUCCESSFUL analysis — no exception, every status key reassuring:
BAD = {**GOOD, "column_dim_x": 0.45, "column_dim_y": 0.45, "fy": 450.0,
       "load_cases": [{"name": "ULS", "load_factor": 1.2, "p": 3500.0},
                      {"name": "",    "load_factor": 1.5, "p": 1200.0}]}
r = prokon.v5.pile_cap.analyse(**BAD)["result"]
strut = r["strut_results"][0]["load_cases"][0]
node = r["column_node"]["load_cases"][0]
print(f"\n7) a 450 mm column on this cap at 6000 kN returns OK:")
print(f"   is_stable = {r['is_stable']}, geometry_is_valid = "
      f"{r['geometry_is_valid']}, has_uplift = {r['has_uplift']}")
print(f"   strut       Cf = {strut['cf']:.0f} kN  Cr = {strut['cr']:.0f} kN  "
      f"SF = {strut['sf']}")
print(f"   column node Pf = {node['pf']:.0f} kN  Pr = {node['pr']:.0f} kN  "
      f"SF = {node['sf']:.3f}")
print("   Nothing in the result says 'inadequate'. Test SF >= 1 yourself.")

# --- 8. And the verdict is CODE-SPECIFIC. The same cap, the same load,
#        four design codes: adequate under one, inadequate under three —
#        every one of them a successful call:
print()
for code in ("CSA-A23.3:2019", "ACI 318 - 2019",
             "Eurocode 2 - 2004", "SABS 0100 - 2000"):
    r = prokon.v5.pile_cap.analyse(**{**GOOD, "design_code": code})["result"]
    worst = min(
        [lc["sf"] for e in r["strut_results"] for lc in e["load_cases"]]
        + [lc["sf"] for lc in r["column_node"]["load_cases"]]
        + [lc["sf"] for nd in r["pile_nodes"] for lc in nd["load_cases"]])
    print(f"8) {code:<18} worst SF = {worst:.3f}  -> "
          f"{'OK' if worst >= 1.0 else 'CAP INADEQUATE'}")

# --- 9. Three status keys look like the checks you want. They are not.
#        Measured over 384 caps — four codes x 2..5 piles x a grid of
#        loads, moments and horizontals — `has_uplift` was NEVER True,
#        `is_stable` never False, `geometry_is_valid` never False and
#        `column_node` never None. Uplift ARRIVES AS THE REFUSAL in
#        section 6, so by the time you hold a result there is none:
#        `if not result["has_uplift"]` is a test that cannot fail.
r = prokon.v5.pile_cap.analyse(**{**GOOD, "load_cases": [
    {"name": "ULS", "load_factor": 1.0, "p": 1000.0, "mx": 935.0}]})["result"]
least = min(f["p"] for pile in r["pile_forces"] for f in pile)
print(f"\n9) a cap 1 kNm from refusal: has_uplift = {r['has_uplift']}, "
      f"least pile reaction = {least} kN")
print("   Branch on the EXCEPTION for uplift, never on the flag.")

# --- 10. `design_tie` is an ELEMENT index, not a position in
#        `tie_results` — it is one of the values in `tie_element_indices`.
#        Indexing tie_results with it is wrong at every pile count this
#        engine designs, and here it is loud rather than silent:
print()
for piles in (2, 3, 4, 5):
    r = prokon.v5.pile_cap.analyse(**{**GOOD, "no_of_piles": piles})["result"]
    try:
        r["tie_results"][r["design_tie"]]
        outcome = "no error (but the wrong row)"
    except IndexError:
        outcome = "IndexError"
    print(f"10) {piles} piles: design_tie = {r['design_tie']}, "
          f"tie_element_indices = {r['tie_element_indices']}, "
          f"len(tie_results) = {len(r['tie_results'])} -> {outcome}")

# --- 10b. The right way round, and the cross-check that proves it. Every
#        tie carries its own `tf` and `as_required`, and `tf` reconciles
#        EXACTLY with the element-force grid at its own element index —
#        so the two reads can never drift apart:
r = prokon.v5.pile_cap.analyse(**GOOD)["result"]
governing = next(t for t in r["tie_results"]
                 if t["element_index"] == r["design_tie"])
for tie in r["tie_results"]:
    element = tie["element_index"]
    for i, lc in enumerate(tie["load_cases"]):
        assert lc["tf"] == r["element_forces"][element][i]     # kN, the same number
print(f"10b) every tie's tf reconciles with element_forces exactly "
      f"({len(r['tie_results'])} ties checked)")
print(f"     governing tie, element {governing['element_index']}: "
      f"tf = {governing['load_cases'][0]['tf']} kN "
      f"(negative is tension), As required = "
      f"{governing['load_cases'][0]['as_required']:.2f} mm2")
print(f"     tie_minim_reinforcement = {r['tie_minim_reinforcement']} mm2/m "
      f"is the code MINIMUM, not the requirement - compare, don't substitute.")

# --- 11. Two more numbers that do not mean what they look like.
#        `overhang_min_required` is a check the engine performs FOR you to
#        read, not one it enforces: supply less and the cap is designed
#        anyway, with geometry_is_valid still True.
r = prokon.v5.pile_cap.analyse(**{**GOOD, "cap_overhang": 0.10})["result"]
print(f"\n11) overhang 0.100 m supplied against "
      f"{r['overhang_min_required']:.3f} m required: designed, "
      f"geometry_is_valid = {r['geometry_is_valid']}")

# --- 11b. And the strut factors arrive ROUNDED. Cf comes at 2 decimals
#        and SF at 3, while Cr and every bearing-node value are full
#        precision — so a strut whose true Cr/Cf is 0.9995 publishes
#        SF = 1, and a bare `sf >= 1` test passes it. Recompute the
#        ratio when the margin is what you are deciding on:
print()
for p in (5280.0, 5281.0, 5283.0, 5285.0):
    r = prokon.v5.pile_cap.analyse(**{**GOOD, "load_cases": [
        {"name": "ULS", "load_factor": 1.0, "p": p}]})["result"]
    s = r["strut_results"][0]["load_cases"][0]
    warn = "  <-- published SF passes, true SF does not" \
        if s["sf"] >= 1.0 > s["cr"] / s["cf"] else ""
    print(f"11b) P = {p:.0f} kN: published SF = {s['sf']:<6} "
          f"true Cr/Cf = {s['cr'] / s['cf']:.6f}{warn}")

# --- 12. Timeouts. Each call may take up to prokon.v5.timeout_seconds
#        (default 120.0) before raising category "timeout". Raise it for
#        very large runs, or set None to wait forever. This feature caps
#        the schedule at 20 rows, so no run gets big enough to need it:
prokon.v5.timeout_seconds = 300.0
print(f"\n12) timeout now {prokon.v5.timeout_seconds} s per call")


# --- The pattern to copy into batch scripts. This feature really does
#     need the "no_solution" branch — and it still needs the adequacy
#     screen, because the engine never refuses an inadequate cap.
def try_analyse(**inputs):
    """Return (result, None) or (None, reason) — never crash the batch."""
    try:
        result = prokon.v5.pile_cap.analyse(**inputs)["result"]
    except prokon.v5.ProkonError as e:
        if e.category == "no_solution":
            return None, f"no design: {plain(e.message)}"
        if e.category == "invalid_input":
            return None, f"input problem: {plain(e.message)}"
        raise  # environment and timeout trouble should stop the run

    # The verdict the engine does not give you. Recomputed from Cr/Cf on
    # the struts, because the published SF is rounded (section 11b).
    worst = min(
        [lc["cr"] / lc["cf"] for e in result["strut_results"] for lc in e["load_cases"]]
        + [lc["sf"] for lc in result["column_node"]["load_cases"]]
        + [lc["sf"] for nd in result["pile_nodes"] for lc in nd["load_cases"]])
    if worst < 1.0:
        return None, f"cap inadequate (worst factor {worst:.3f})"
    if inputs["cap_overhang"] < result["overhang_min_required"]:
        return None, (f"overhang {inputs['cap_overhang']:.3f} m short of "
                      f"{result['overhang_min_required']:.3f} m")
    return result, None


print()
for label, inputs in (
        ("the reference cap", GOOD),
        ("450 mm column, 6000 kN", BAD),
        ("uplift", UPLIFT),
        ("overhang 0.10 m", {**GOOD, "cap_overhang": 0.10}),
        ("SABS 0100 - 2000", {**GOOD, "design_code": "SABS 0100 - 2000"}),
        ("a mistyped code", {**GOOD, "design_code": "CSA A23.3"})):
    result, reason = try_analyse(**inputs)
    verdict = (f"ok, cap {result['cap_dim_x']:.2f} x {result['cap_dim_y']:.2f} m"
               if result else reason)
    print(f"13) batch-safe call, {label:<23} -> {verdict}")

# --- 14. THE ENVELOPE IS ON THE EXCEPTION ----------------------------
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
        prokon.v5.pile_cap.analyse(**inputs)
        print(f"   {label}: returned - unexpected")
    except prokon.v5.ProkonError as failure:
        print(f"   {label}")
        for key, value in diagnose(failure).items():
            shown = f"{len(value)} value(s)" if key == "hints" else value
            print(f"     {key:<18} {shown}")

print(f"\n14) ONE diagnose(), OVER ALL THREE KINDS OF FAILURE")

# 14a. Refused BEFORE dispatch: an envelope, but no engine identity.
diagnosed("14a  refused before dispatch", **{**GOOD, "design_code": "CSA A23.3"})

# 14b. Refused BY THE ENGINE, after dispatch: an envelope WITH identity
#       and version - which is what a calculation record actually needs.
diagnosed("14b  refused by the engine", **{**GOOD, "column_dim_x": 9.0, "cap_thickness": 1.0,
           "pile_spacing": 3.0, "cap_overhang": 0.0})

# 14c. A TRANSPORT failure: no envelope at all. The guard inside
#       diagnose() is what makes this a diagnosis instead of a TypeError.
saved_timeout = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = "not a number"
    diagnosed("14c  never reached the engine", **GOOD)
finally:
    prokon.v5.timeout_seconds = saved_timeout

print("   -> ONE function, every failure path, and it cannot raise a")
print("      TypeError of its own. That is what asking `envelope is None`")
print("      before reading anything out of it buys you.")
print("   -> file that dict beside the row that failed, and months later")
print("      the failure is still traceable to an engine version. A bare")
print("      message is not.")
