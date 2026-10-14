# ---
# Example:  A batch that finishes - every failure mode, handled
# Feature:  circular_column + general_column (C12 + C13) - the pattern, not one engine
# Verified: yes - 2026-09-09 - every failure mode, and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe
# ---
# A batch of 200 sections that dies on section 47 has wasted the run and
# told you nothing about sections 48 to 200. This is the pattern that
# finishes, and every branch in it exists because something really does
# fail that way.
#
# The five things that can go wrong, and what each one means:
#
#   TypeError            you left an argument out, or misspelled one.
#                        Python raised it; no engine ran. NEVER catch this
#                        in a batch - it is a bug in your script, and
#                        swallowing it hides it on every row.
#   invalid_input        the row's data is wrong. Skip the row, record why.
#   no_solution          the request was well formed and has no answer.
#                        Skip the row; this is a RESULT, not an error.
#   environment          something outside the calculation is wrong.
#                        STOP - the next row will fail the same way.
#   internal             report it. Do not retry.
#
# ⚠ AND THE SIXTH, WHICH IS THE DANGEROUS ONE: a row that SUCCEEDS and is
# still wrong. Every engine here reports an inadequate design as a
# successful analysis. Section 4 handles that, and it is the only branch
# with no exception to catch.
#
# ⭐ AND WHAT A BATCH MUST RECORD, not merely branch on: the whole document
# the engine sent rides the error as .envelope, so a skipped row can keep
# a full diagnosis instead of a truncated sentence.
#
#   envelope is None            nothing came back - a timeout, a command
#                               line too long, an unlaunchable executable.
#                               There is no document. ASK THIS FIRST.
#   envelope, module is None    the HOST refused before it dispatched, so
#                               there is no engine to name. Category, code,
#                               hints and timing are still there.
#   envelope, module is a name  an ENGINE ran and refused. The full record:
#                               which engine, which version, and when.
#
# A row logged as "bad input: cover too large" is untraceable six months
# later. A row logged with the engine's own version is not - and that is
# the difference between a batch log and an audit record.

import prokon.v5

CODE = "BS8110 - 1997"
STEEL_LIMIT = 4.0        # %, a limit YOU choose

# ── The batch, with deliberate faults in it ────────────────────────────
# One row per column. Rows 3, 5, 7 and 9 are broken in different ways.
BATCH = (
    {"mark": "K1", "diameter": 450.0, "cover": 45.0, "fcu": 30.0,
     "fy": 450.0, "lex": 3000.0, "deltas": 1.0, "n": 1500.0, "m": 80.0},
    {"mark": "K2", "diameter": 500.0, "cover": 45.0, "fcu": 30.0,
     "fy": 450.0, "lex": 3000.0, "deltas": 1.0, "n": 2200.0, "m": 110.0},
    # a design code that does not exist
    {"mark": "K3", "diameter": 450.0, "cover": 45.0, "fcu": 30.0,
     "fy": 450.0, "lex": 3000.0, "deltas": 1.0, "n": 1500.0, "m": 80.0,
     "design_code": "BS 8110"},
    {"mark": "K4", "diameter": 400.0, "cover": 45.0, "fcu": 30.0,
     "fy": 450.0, "lex": 3000.0, "deltas": 1.0, "n": 900.0, "m": 50.0},
    # cover past half the diameter - the wrapper refuses this one
    {"mark": "K5", "diameter": 400.0, "cover": 250.0, "fcu": 30.0,
     "fy": 450.0, "lex": 3000.0, "deltas": 1.0, "n": 900.0, "m": 50.0},
    {"mark": "K6", "diameter": 600.0, "cover": 50.0, "fcu": 35.0,
     "fy": 500.0, "lex": 4000.0, "deltas": 1.0, "n": 3200.0, "m": 160.0},
    # slenderness past the code's limit - the engine refuses this one
    {"mark": "K7", "diameter": 300.0, "cover": 45.0, "fcu": 30.0,
     "fy": 450.0, "lex": 30_000.0, "deltas": 1.0, "n": 800.0, "m": 40.0},
    {"mark": "K8", "diameter": 350.0, "cover": 45.0, "fcu": 30.0,
     "fy": 450.0, "lex": 2800.0, "deltas": 1.0, "n": 700.0, "m": 35.0},
    # a section that SUCCEEDS and must not be built - 300 mm under 5000 kN
    {"mark": "K9", "diameter": 300.0, "cover": 45.0, "fcu": 30.0,
     "fy": 450.0, "lex": 3000.0, "deltas": 1.0, "n": 5000.0, "m": 100.0},
    {"mark": "K10", "diameter": 550.0, "cover": 50.0, "fcu": 35.0,
     "fy": 500.0, "lex": 3600.0, "deltas": 1.0, "n": 2600.0, "m": 130.0},
)

print("A BATCH THAT NEVER DIES")
print(f"  {len(BATCH)} rows, {CODE}, steel limit {STEEL_LIMIT:.0f} % "
      f"(yours, not the engine's)")

designs = []
skipped = []
flagged = []
stopped = None


def diagnose(failure):
    """Everything worth recording about one failed row, from the error alone."""
    record = {
        "category": failure.category,
        "code": failure.code,
        # Engine prose is not guaranteed ASCII - fold it once, here.
        "message": failure.message.encode("ascii", "replace").decode(),
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
    record["started_at"] = meta.get("started_at")
    record["elapsed_ms"] = meta.get("elapsed_milliseconds")
    return record

print(f"\n{'mark':<5} {'dia':>5} {'N':>7} {'steel':>9} {'%':>7} "
      f"{'outcome':<14} note")
print("-" * 92)

for row in BATCH:
    mark = row["mark"]

    # ⚠ NOT IN THE try. A TypeError here is a bug in the batch-building
    # code, and it must reach you on row 1 rather than being logged on
    # every row. Only the ENGINE call is guarded.
    inputs = dict(
        design_code=row.get("design_code", CODE),
        diameter=row["diameter"], cover=row["cover"],
        fcu=row["fcu"], fy=row["fy"],
        lex=row["lex"], ley=row["lex"],
        bracing_x="Braced", bracing_y="Braced",
        deltas=row["deltas"],
        load_cases=[{"n": row["n"], "m1x": row["m"]}],
    )

    try:
        result = prokon.v5.circular_column.analyse(**inputs)["result"]

    except prokon.v5.ProkonError as refusal:
        record = diagnose(refusal)
        message = record["message"]

        if refusal.category == "invalid_input":
            print(f"{mark:<5} {row['diameter']:>5.0f} {row['n']:>7.0f} "
                  f"{'-':>9} {'-':>7} {'bad input':<14} "
                  f"{refusal.code}: {message[:36]}")
            skipped.append((mark, record))
            continue

        if refusal.category == "no_solution":
            # A RESULT, not an error: the request was well formed and the
            # engine has no answer for it.
            print(f"{mark:<5} {row['diameter']:>5.0f} {row['n']:>7.0f} "
                  f"{'-':>9} {'-':>7} {'no solution':<14} {message[:36]}")
            skipped.append((mark, record))
            continue

        if refusal.category in ("environment", "licence"):
            # The next row will fail identically. Stopping is the only
            # honest response; carrying on produces a report full of the
            # same message.
            print(f"{mark:<5} STOPPING: {refusal.category}/{refusal.code}")
            print(f"      {message}")
            for hint in refusal.hints[:3]:
                print(f"      hint: "
                      f"{hint.encode('ascii', 'replace').decode()}")
            stopped = (mark, record)
            break

        if refusal.category in ("timeout", "cancelled"):
            print(f"{mark:<5} {'-':>5} {'-':>7} {'-':>9} {'-':>7} "
                  f"{refusal.category:<14} {message[:36]}")
            skipped.append((mark, record))
            continue

        # internal, or a category this script has never seen. Report it and
        # do not retry - and do not swallow it either.
        print(f"{mark:<5} UNEXPECTED {refusal.category}/{refusal.code}: "
              f"{message}")
        raise

    # ── The success branch, which still needs checking ─────────────────
    percentage = result["percentage_steel"]
    reasons = []
    if not result["all_pass"]:
        reasons.append("the engine reports all_pass FALSE")
    if percentage > STEEL_LIMIT:
        reasons.append(f"{percentage:.2f} % steel over the "
                       f"{STEEL_LIMIT:.0f} % limit")
    case = result["load_case_results"][0]
    if case["buckles"]:
        reasons.append("the engine reports buckling")

    if reasons:
        print(f"{mark:<5} {row['diameter']:>5.0f} {row['n']:>7.0f} "
              f"{result['total_as']:>9.0f} {percentage:>7.2f} "
              f"{'FLAGGED':<14} {reasons[0]}")
        for reason in reasons[1:]:
            print(f"{'':<5} {'':<5} {'':<7} {'':<9} {'':<7} {'':<14} "
                  f"{reason}")
        flagged.append((mark, reasons))
        continue

    print(f"{mark:<5} {row['diameter']:>5.0f} {row['n']:>7.0f} "
          f"{result['total_as']:>9.0f} {percentage:>7.2f} "
          f"{'ok':<14}")
    designs.append((mark, result))

# ── The report ──────────────────────────────────────────────────────────
print("-" * 92)
print(f"designed   {len(designs)}")
print(f"flagged    {len(flagged)}   (SUCCEEDED and must not be built)")
print(f"skipped    {len(skipped)}")
print(f"stopped    {'yes - ' + stopped[1]['category'] if stopped else 'no'}")
print(f"unreached  {len(BATCH) - len(designs) - len(flagged) - len(skipped) - (1 if stopped else 0)}")

if skipped:
    # The full diagnosis, not the sentence. Note which rows carry an engine
    # version and which cannot: a row that never reached an engine has no
    # engine to name.
    print(f"\nskipped rows, with the DIAGNOSIS the envelope carried:")
    for mark, record in skipped:
        print(f"   {mark:<5} {record['category']:<14} {record['code']}")
        print(f"         {record['message'][:64]}")
        if not record["has_envelope"]:
            print(f"         NO ENVELOPE - nothing came back, so there is "
                  f"nothing to record")
        elif record["module"] is None:
            print(f"         refused by the HOST before it reached an "
                  f"engine - no engine to name")
            print(f"         at {record['started_at']} "
                  f"({record['elapsed_ms']} ms)")
        else:
            print(f"         engine {record['module']} "
                  f"{record['module_version']}")
            print(f"         at {record['started_at']} "
                  f"({record['elapsed_ms']} ms)")
    print(f"   -> that is a row you can defend later. Every field came off")
    print(f"      refusal.envelope, and the `has_envelope` branch is")
    print(f"      what keeps the print from being a TypeError on a timeout.")

if flagged:
    print(f"\nFLAGGED ROWS - these are the ones to read twice. Every one")
    print(f"came back with ok = true and no exception at all:")
    for mark, reasons in flagged:
        print(f"   {mark:<5} {'; '.join(reasons)}")

# ── And the one branch there is no exception for ───────────────────────
print(f"\n{'-' * 92}")
print("THE BRANCH WITH NO EXCEPTION, spelled out")
absurd = prokon.v5.circular_column.analyse(
    design_code=CODE, diameter=300.0, cover=45.0, fcu=30.0, fy=450.0,
    lex=3000.0, ley=3000.0, bracing_x="Braced", bracing_y="Braced",
    deltas=1.0, load_cases=[{"n": 20_000.0}])["result"]
gross = 3.141592653589793 * 300.0 ** 2 / 4.0
print(f"   a 300 mm column under 20 000 kN:")
print(f"     total_as         {absurd['total_as']:.1f} mm2")
print(f"     percentage_steel {absurd['percentage_steel']:.2f} %")
print(f"     all_pass         {absurd['all_pass']}")
print(f"     gross area       {gross:.1f} mm2")
print(f"   -> no exception, no warning. "
      f"{absurd['percentage_steel']:.0f} % steel is not a")
print(f"      column, and only YOUR limit says so. Every engine in this")
print(f"      set behaves this way: an inadequate engineering answer is a")
print(f"      SUCCESSFUL calculation, because it IS one.")

# ── The same pattern on a second engine ────────────────────────────────
# The categories are the same across all twelve engines, which is what
# makes one handler reusable. C13 answers a different question - a capacity
# factor rather than a steel area - so the SUCCESS check differs and the
# FAILURE handling does not.
print(f"\nTHE SAME HANDLER, A DIFFERENT ENGINE (C13)")
SQUARE = [{"code": "+", "x": 0, "y": 0},
          {"code": "L", "x": 400, "y": 0},
          {"code": "L", "x": 400, "y": 400},
          {"code": "L", "x": 0, "y": 400},
          {"code": "+", "x": 42.5, "y": 42.5}, {"code": "B", "x": 25},
          {"code": "+", "x": 357.5, "y": 42.5}, {"code": "B", "x": 25},
          {"code": "+", "x": 357.5, "y": 357.5}, {"code": "B", "x": 25},
          {"code": "+", "x": 42.5, "y": 357.5}, {"code": "B", "x": 25}]

for label, load, code in (("the pinned Case A", 1000.0, CODE),
                          ("far too much load", 12_000.0, CODE),
                          ("a code C13 lacks", 1000.0, "BS 8110")):
    try:
        result = prokon.v5.general_column.analyse(
            design_code=code, length=3.0, fcu=30.0, fy=450.0,
            section=SQUARE,
            load_cases=[{"axial": load, "moment_x_top": 50,
                         "moment_x_bottom": 50}])["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"   {label:<20} {refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:40]}")
        continue
    factor = result["min_capacity_factor"]
    print(f"   {label:<20} capacity factor {factor:>8.4f}, "
          f"has_feasible_design {result['has_feasible_design']}"
          f"  ->  {'adequate' if factor >= 1.0 else 'OVERSTRESSED, and no exception'}")

print(f"\n{'-' * 92}")
print("The categories are the same on all twelve engines, so the failure")
print("handling above is written once. What changes per engine is the")
print("SUCCESS check - a steel percentage here, a capacity factor there -")
print("and that is the half a batch script has to write for itself.")
