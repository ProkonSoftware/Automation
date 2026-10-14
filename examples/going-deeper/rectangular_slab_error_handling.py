# ---
# Example:  Error handling - what a failed call looks like, and how to branch on it
# Feature:  rectangular_slab (C04 Rectangular Slab)
# Verified: yes - 2026-09-10 - behavioural: every printed category/code/hint, the transposed direction message measured BOTH ways, and all four silent successes measured on prokon-automation.exe
# ---
# Every failure raises one exception type, prokon.v5.ProkonError, carrying:
#   .category  what KIND of problem  ("invalid_input", "no_solution", ...)
#   .code      the specific machine-readable code
#   .message   what went wrong, in words
#   .hints     how to fix it - often the full list of allowed values
#   .envelope  THE WHOLE DOCUMENT THE ENGINE SENT - or None
#   .warnings  what it warned about, read off that envelope
#   .logs      what it logged, read off that envelope
#
# A robust script branches on .category. On this engine that pays off more
# than on most: rectangular_slab genuinely raises "no_solution" for a
# well-formed request it cannot analyse (section 5), which is the outcome
# every geometry search has to survive.
#
# ⚠ AND IT HAS THE OPPOSITE FAILURE, WHICH IS WORSE. Sections 6 to 9 all
# arrive as SUCCESS - a result dictionary, no exception - carrying an answer
# you must not build. Read those twice. Only ONE of them says anything at
# all, and it is the one that was fixed most recently.

import prokon.v5

ENCASTRE = "FixedAgainstVerticalDisplacementAndRotation"

GOOD = dict(
    design_code="BS8110 - 1997",
    lx=7.5, ly=5.0,                     # m
    h=200.0, dx=165.0, dy=150.0,        # mm
    fcu=30.0, fy=450.0,                 # MPa
    edge_top=ENCASTRE, edge_right=ENCASTRE,
    edge_bottom=ENCASTRE, edge_left=ENCASTRE,
    load_cases=[{"number": 1, "lf": 1.4, "udl": 7.5}],
)

FACES = ("x_top", "x_bot", "y_top", "y_bot")

# --- 1. A typo in a choice value: category "invalid_input", with the whole
#        allowed list in .hints. Choice values are exact, INCLUDING capitals:
#        "bs8110 - 1997" is refused the same way.
try:
    prokon.v5.rectangular_slab.analyse(**{**GOOD, "design_code": "BS 8110"})
except prokon.v5.ProkonError as e:
    print(f"1) {e.category} / {e.code}")
    print(f"   {e.message}")
    print(f"   all {len(e.hints)} design codes are in .hints: "
          f"{', '.join(e.hints[:3])}, ...")

# --- 2a. LEAVE AN ARGUMENT OUT and PYTHON refuses, before any engine process
#         is launched. analyse() takes real keyword-only parameters, so a
#         misspelled name is caught the same way - and Python usually suggests
#         the one you meant:
#             analyse() got an unexpected keyword argument 'fcux'.
#             Did you mean 'fcu'?
#         Usually, not always: the suggestion is Python's own edit-distance
#         heuristic, and it gives up on a long enough mangling.
try:
    prokon.v5.rectangular_slab.analyse(
        **{k: v for k, v in GOOD.items() if k != "fcu"})
except TypeError as e:
    print(f"\n2a) TypeError, raised by PYTHON: {e}")
    print("    no process was launched - this costs nothing and is instant.")

# --- 2b. PASS IT AS None and the PACKAGE refuses. None means NOT SUPPLIED,
#         which is not the same as a value, so it is never put on the wire.
try:
    prokon.v5.rectangular_slab.analyse(**{**GOOD, "fcu": None})
except prokon.v5.ProkonError as e:
    print(f"\n2b) {e.category} / {e.code}")
    print(f"    {e.message}")

# --- 3. A misspelt input NAME is refused too, never silently ignored --------
try:
    prokon.v5.rectangular_slab.analyse(**{**GOOD, "fcux": 30.0})
except TypeError as e:
    print(f"\n3) TypeError: {e}")
    print("   an input this engine does not have cannot be quietly dropped.")

# --- 4. The load table is JSON, and a malformed one is named as such -------
try:
    prokon.v5.rectangular_slab.analyse(**{**GOOD, "load_cases": "not a table"})
except prokon.v5.ProkonError as e:
    print(f"\n4) {e.category} / {e.code}")
    print(f"   {e.message[:100]}")

# --- 5. THE ONE WORTH BRANCHING ON: a well-formed request the engine ran
#        and DECLINED. Every input is the right type and in range as far as
#        Python is concerned; the engine's own validator is what refuses.
try:
    prokon.v5.rectangular_slab.analyse(**{**GOOD, "dx": 80.0})
except prokon.v5.ProkonError as e:
    print(f"\n5) {e.category} / {e.code}")
    print(f"   {e.message}")
    print("   -> 'no_solution' means A REAL ENGINE RAN AND SAID NO. It is not")
    print("      a bug and not a typo: an effective depth below h/2 is not a")
    print("      slab. A search over geometry must catch this and move on.")

# --- 5b. ⚠ AND READ THAT MESSAGE CAREFULLY, BECAUSE IT NAMES THE OTHER
#         DIRECTION. `dx` was the input that was wrong; the engine complained
#         about "deff Y-direction". Measured both ways:
#
#             dx=80  ->  "The value of deff Y-direction<h/2 mm"
#             dy=80  ->  "The value of deff X-direction<h/2 mm"
#
#         This is not a wrapper bug and the ANSWERS are not affected - the
#         desktop program's own variable names are transposed against its own
#         screen labels (its `snavar` reads the row labelled "deff X-direction"
#         into the variable `dy`), and the validator speaks in variables while
#         the wire speaks in labels. The wire is named for what you type.
#         So: trust the message that an effective depth is wrong, and check
#         BOTH of yours rather than the one it names.
try:
    prokon.v5.rectangular_slab.analyse(**{**GOOD, "dy": 80.0})
except prokon.v5.ProkonError as e:
    print(f"\n5b) dy was the bad input, and the message says: {e.message}")

# --- 5c. The control: the same panel with a valid dx analyses normally. A
#         refusal that fired for everything would teach nothing.
control = prokon.v5.rectangular_slab.analyse(**GOOD)["result"]
print(f"\n5c) the control, dx back to {GOOD['dx']:.0f} mm: "
      f"ast x_top = {control['ast']['x_top']:.1f} mm2/m")

# ══════════════════════════════════════════════════════════════════════════
# NOW THE FAILURES THAT SUCCEED.
# ══════════════════════════════════════════════════════════════════════════

# --- 6. AN EMPTY LOAD TABLE IS ACCEPTED, and you get a design ---------------
#        Nothing is wrong with the request: a panel with no imposed load is a
#        real thing. But the engine always adds the slab's OWN WEIGHT, so the
#        answer is a self-weight-only design that looks exactly like a normal
#        one - four moments, four steel areas, no warning.
nothing_on_it = prokon.v5.rectangular_slab.analyse(
    **{**GOOD, "load_cases": []})["result"]

print(f"\n6) an EMPTY load table succeeded.")
print(f"   ast x_top = {nothing_on_it['ast']['x_top']:.1f} mm2/m, from "
      f"{nothing_on_it['moment_max']['x_top']:.2f} kNm/m")
print(f"   loaded:    {control['ast']['x_top']:.1f} mm2/m, from "
      f"{control['moment_max']['x_top']:.2f} kNm/m")
print("   -> that is the SELF WEIGHT alone. If your load table failed to")
print("      build - an empty query, a bad filter - this is what you get,")
print("      and it is a plausible-looking design for a slab carrying")
print("      nothing. Check that the table you built is not empty.")

# --- 7. AN ENVELOPE NAMING THE WRONG CASES IS ACCEPTED --------------------
#        The envelope string is never checked against the load table. Naming a
#        case that does not exist is not refused, and - the part that costs
#        money - naming only SOME of the cases that do exist is not refused
#        either. You get a real answer to a question you did not mean to ask.
TWO_CASES = [
    {"number": 1, "lf": 1.4, "udl": 7.5},
    {"number": 2, "lf": 1.6, "udl": 15.0},   # the heavier case
]

both = prokon.v5.rectangular_slab.analyse(
    **{**GOOD, "load_cases": TWO_CASES, "envelope": "1,2"})["result"]
only_first = prokon.v5.rectangular_slab.analyse(
    **{**GOOD, "load_cases": TWO_CASES, "envelope": "1"})["result"]
not_there = prokon.v5.rectangular_slab.analyse(
    **{**GOOD, "load_cases": TWO_CASES, "envelope": "9"})["result"]

print(f"\n7) the SAME two-case model, enveloped three ways - all succeeded:")
print(f"   envelope='1,2'  ast x_top = {both['ast']['x_top']:8.1f} mm2/m"
      f"   (both cases)")
print(f"   envelope='1'    ast x_top = {only_first['ast']['x_top']:8.1f} mm2/m"
      f"   (misses the heavier case)")
print(f"   envelope='9'    ast x_top = {not_there['ast']['x_top']:8.1f} mm2/m"
      f"   (a case that does not exist)")
print("   -> no refusal, no warning, and the middle one is UNDER-DESIGNED by")
print(f"      {100 * (1 - only_first['ast']['x_top'] / both['ast']['x_top']):.0f} %"
      f" against the model it was given. Build the envelope string from the")
print("      case numbers you actually created, never by hand.")

# --- 8. ZERO STEEL UNDER A REAL MOMENT ------------------------------------
#        The engine returns ok, no warning, and ast = 0 for a face it could
#        not design. Read it as 'no steel needed' and you will build a slab
#        with nothing in two of its faces.
too_thin = prokon.v5.rectangular_slab.analyse(
    **{**GOOD, "h": 110.0, "dx": 79.0, "dy": 67.0})["result"]

declined = [face for face in FACES
            if too_thin["ast"][face] == 0.0 and too_thin["moment_max"][face] > 0.0]

print(f"\n8) a 110 mm panel under the same load succeeded, with NO warning.")
for face in FACES:
    print(f"   {face:<6} moment {too_thin['moment_max'][face]:7.2f} kNm/m"
          f"   ast {too_thin['ast'][face]:8.2f} mm2/m")
print(f"   -> {len(declined)} face(s) carry a moment and no steel: "
      f"{', '.join(declined)}")
print("   -> THE TEST IS `ast == 0 and moment_max > 0`. A face with no moment")
print("      legitimately needs no steel; a face with a moment and no steel")
print("      is the engine declining to design it. Nothing in the result")
print("      distinguishes the two for you.")

# --- 9. A DESIGN CODE THAT DESIGNS NOTHING - and the one trap that SPEAKS --
#        Four of the twenty-nine codes are crack-width codes with no flexural
#        rules. They return success and every area is zero. Unlike section 8,
#        this one publishes a warning, and the warning is the whole answer.
crack_code = prokon.v5.rectangular_slab.analyse(
    **{**GOOD, "design_code": "BS8007 - 1987"})

print(f"\n9) BS8007 - 1987 succeeded, and every area is zero:")
print(f"   {crack_code['result']['ast']}")
print(f"   moments, though, are real: "
      f"x_top {crack_code['result']['moment_max']['x_top']:.2f} kNm/m")
print(f"   warnings: {len(crack_code['warnings'])}")
for text in crack_code["warnings"]:
    print(f"     {text[:96]}...")
print("   -> THIS is what sections 6, 7 and 8 do not do. The envelope's")
print("      `warnings` list is complete on every call and cannot be")
print("      filtered away, so a batch that reads it cannot miss this.")

# --- 10. Timeouts ---------------------------------------------------------
#         Each call may take up to prokon.v5.timeout_seconds. A timeout is a
#         TRANSPORT failure: the host never answered, so there is no envelope.
saved = prokon.v5.timeout_seconds
try:
    prokon.v5.timeout_seconds = 1e-6
    prokon.v5.rectangular_slab.analyse(**GOOD)
    print("\n10) a microsecond timeout was survived - unexpected")
except prokon.v5.ProkonError as e:
    print(f"\n10) {e.category} / {e.code}")
    print(f"    envelope is None: {e.envelope is None}")
except ValueError as e:
    print(f"\n10) refused before launching: {e}")
finally:
    prokon.v5.timeout_seconds = saved

# --- 11. THE ENVELOPE IS ON THE EXCEPTION ---------------------------------
#         Anything the HOST answered carries an envelope; a transport failure
#         carries None. Both raise, so `e.envelope is None` is the FIRST
#         question a handler asks.
try:
    prokon.v5.rectangular_slab.analyse(**{**GOOD, "dx": 80.0})
except prokon.v5.ProkonError as e:
    print(f"\n11) the refusal from section 5, examined:")
    print(f"    envelope is None:  {e.envelope is None}")
    if e.envelope is not None:
        print(f"    module:            {e.envelope['module']}")
        print(f"    module_version:    {e.envelope['module_version']}")
        print(f"    ok:                {e.envelope['ok']}")
    print(f"    warnings:          {e.warnings}")
    print("    -> a refusal is a full record, not just a string. It goes into")
    print("       a calculation file exactly as a success does.")

print("\n" + "-" * 72)
print("Four of the eleven sections above are SUCCESSES you must not build.")
print("Only section 9 tells you so. The other three - an empty load table, an")
print("envelope naming nothing, and zero steel under a moment - are checks")
print("your script has to make, and this file is where the tests live.")
