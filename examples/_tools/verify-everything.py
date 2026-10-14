# Internal verification harness - NOT part of the user documentation.
#
# THE MASTER SCRIPT. One command that runs every check this tree has, in
# the order that makes a failure easiest to read, and reports a single
# verdict.
#
# Usage:
#   <sealed-runtime>/python.exe _tools/verify-everything.py [options]
#
#   --jobs N          examples in flight at once (default 6).
#   --package-dir D   the folder containing the `prokon` package.
#   --engine-home D   an engine folder, exported as PROKON_ENGINE_HOME.
#   --filter TEXT     sweep only examples whose path contains TEXT
#                     (repeatable). A FILTERED RUN IS NOT A PASS - see below.
#   --skip-slow       skip the example sweep, run the fast gates only.
#   --keep-output D   pass through to the sweep.
#   --heartbeat S     pass through to the sweep (0 disables).
#   --timeout S       seconds per example, passed through to the sweep.
#
# WHY --timeout IS REACHABLE FROM HERE - MEASURED 2026-09-08. The sweep has
# always had the knob; this file could not reach it, so the sweep's own
# default of 600 seconds was the only value a full verification could ever
# use. That default is not comfortably clear of this tree:
# charts-and-plotting/general_column_capacity_rosette.py runs in 460.6
# seconds ALONE and exceeds 600 under a full sweep's contention for six job
# slots, timing out at exactly 600.0s / exit 124 in two independent full
# runs. Raising the limit is the honest response to a script that is slow;
# there is nothing here that lets a script be skipped.
#
# THE FOUR GATES, AND WHY THIS ORDER:
#
#   1. THE LEDGER          is VERIFICATION.md's table current with the
#                          script headers? Cheap, and a stale ledger means
#                          the tree changed without being recorded.
#
#   2. THE ORACLE'S OWN    can check-pinned-values.py FAIL? A pinned-value
#      SELF-TEST           check that cannot fail is not evidence, and this
#                          runs before the check it validates. Without it,
#                          gate 3 passing means nothing.
#
#   3. THE PINNED VALUES   do all twelve engines still return the numbers
#                          pinned in their own test suites, to the last
#                          binary digit? If this fails, no example's output
#                          is worth reading and the sweep would only tell
#                          you they still RUN.
#
#   4. THE EXAMPLE SWEEP   does every script run to completion, print
#                          something, exit 0, carry a verified header, sit
#                          in the ledger, and print pure ASCII? Slowest, so
#                          last - and by then a failure here is about a
#                          script rather than about the engine.
#
# AN EARLY GATE FAILING DOES NOT STOP THE LATER ONES. All four run and all
# four are reported, because "the ledger is stale AND two examples fail" is
# more useful than finding out one week at a time. The exit code is
# non-zero if any of them failed.
#
# THE VERDICT NAMES THE SCRIPT, NOT JUST THE GATE - MEASURED 2026-09-08.
# It used to name only the gate, and that is not a cosmetic difference: the
# two PowerShell harnesses that drive this file (Test-ExamplesInSpyder.ps1,
# Test-GenerationCoexistence.ps1) capture the whole run and display
# `Show-Tail 18` - the last eighteen lines. The sweep's own list of failing
# scripts sits far above that window, so the operator was shown a verdict
# saying "the example sweep FAILED" and nothing whatever about which of a
# hundred-odd scripts did it. Every gate is therefore TEE'd here: streamed
# to the console live AND remembered, so the verdict can reprint the part
# that matters at the bottom, where a tail can see it.
#
# A FILTERED RUN MUST NEVER READ AS A FULL PASS. Both PowerShell harnesses
# decide success by matching `ALL <N> GATES PASSED`, so a filtered run
# deliberately prints a DIFFERENT sentence that cannot match that pattern.
# --filter exists so this harness can be tested against a planted failure
# in seconds instead of ten minutes; it is a developer instrument, and the
# shipping callers pass no filter at all.

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_EXAMPLES_ROOT = _TOOLS.parent

# THE RELAY MUST NOT BE ABLE TO DIE ON WHAT IT IS RELAYING. This process
# now reprints every line its gates produce, so a single character that
# this console's encoding cannot represent would otherwise end the whole
# verification with a UnicodeEncodeError raised by the reporter rather than
# by anything under test. Escaping keeps the character visible and the run
# alive; `hasattr` because a stdout that has been replaced by a harness may
# not offer reconfigure().
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")


def _gate_environment():
    """The gates' environment, with the pipe's encoding NAMED on their side.

    A tee has two ends and they must agree. A gate's stdout here is a pipe,
    not a console, so Python picks its encoding from the platform - while
    this process decodes what arrives. Naming utf-8 for the child and
    decoding utf-8 here makes the pair correct by construction instead of
    by both happening to be on the same Windows code page.

    This does NOT touch the cp437 discipline the sweep enforces on the
    EXAMPLES: run-all-examples.py sets PYTHONIOENCODING explicitly for each
    example it spawns, which overrides this for exactly the process the
    rule is about. That is measured, not assumed - see the probe results in
    VERIFICATION.md's harness notes.
    """
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def run(name, description, command):
    """One gate, streamed live and remembered. Returns a result tuple."""
    print("=" * 100)
    print(f"GATE: {name}")
    print(f"      {description}")
    print(f"      $ {' '.join(Path(part).name if part.endswith('.py') else part for part in command[1:])}")
    print("=" * 100)
    sys.stdout.flush()

    started = time.monotonic()

    # TEE, not capture. `capture_output` would hold every line of a
    # ten-minute sweep until it ended, which is the exact fault this
    # harness was rewritten to remove; a plain inherited stdout would
    # stream but leave this process unable to say anything about what it
    # had just shown. Reading the pipe line by line does both.
    process = subprocess.Popen(
        command, cwd=_EXAMPLES_ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8",
        errors="replace", bufsize=1, env=_gate_environment())

    remembered = []
    for line in process.stdout:
        line = line.rstrip("\r\n")
        print(line)
        sys.stdout.flush()
        remembered.append(line)
    process.wait()

    seconds = time.monotonic() - started
    ok = process.returncode == 0
    print()
    print(f"      -> {'PASSED' if ok else 'FAILED'} "
          f"(exit {process.returncode}) in {seconds:.1f} s")
    print()
    sys.stdout.flush()
    return name, ok, seconds, process.returncode, remembered


def _reported_scripts(failures_file):
    """The sweep's own list of scripts it reported, as (path, why, detail)."""
    if not failures_file.is_file():
        return []
    reported = []
    for line in failures_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        while len(parts) < 3:
            parts.append("")
        reported.append((parts[0], parts[1], parts[2]))
    return reported


def _tail_of(remembered, lines=6):
    """The last few non-blank lines a gate printed, for the verdict."""
    return [line for line in remembered if line.strip()][-lines:]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--package-dir", default=None)
    parser.add_argument("--engine-home", default=None)
    parser.add_argument("--filter", action="append", default=[])
    parser.add_argument("--skip-slow", action="store_true")
    parser.add_argument("--keep-output", default=None)
    parser.add_argument("--heartbeat", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=None)
    arguments = parser.parse_args()

    passthrough = []
    if arguments.package_dir:
        passthrough += ["--package-dir", arguments.package_dir]
    if arguments.engine_home:
        passthrough += ["--engine-home", arguments.engine_home]

    scripts = [path for path in _EXAMPLES_ROOT.rglob("*.py")
               if "_tools" not in path.relative_to(_EXAMPLES_ROOT).parts]

    print()
    print("PROKON EXAMPLE TREE - FULL VERIFICATION")
    print(f"  tree        {_EXAMPLES_ROOT}")
    print(f"  interpreter {sys.executable}")
    print(f"  scripts     {len(scripts)}")
    print(f"  jobs        {arguments.jobs} examples in flight at once")
    if arguments.filter:
        print(f"  filter      {', '.join(arguments.filter)}"
              f"   <- PARTIAL RUN, not a pass")
    print("  progress    each gate streams live; the sweep names every script")
    print("              as it starts and again as it finishes")
    print()

    gates = []
    started = time.monotonic()

    gates.append(run(
        "the ledger",
        "VERIFICATION.md's table must match the scripts' own headers",
        [sys.executable, str(_TOOLS / "build-ledger.py"), "--check"]))

    gates.append(run(
        "the oracle's self-test",
        "the pinned-value check must be able to FAIL, or gate 3 is vacuous",
        [sys.executable, str(_TOOLS / "check-pinned-values.py"),
         "--self-test"] + passthrough))

    gates.append(run(
        "the pinned values",
        "all twelve engines, compared with == against their own test suites",
        [sys.executable, str(_TOOLS / "check-pinned-values.py")]
        + passthrough))

    reported = []
    with tempfile.TemporaryDirectory(prefix="prokon-verify-") as scratch:
        failures_file = Path(scratch) / "reported-scripts.txt"

        if arguments.skip_slow:
            print("=" * 100)
            print("GATE: the example sweep - SKIPPED (--skip-slow)")
            print("=" * 100)
            print()
        else:
            sweep = [sys.executable, str(_TOOLS / "run-all-examples.py"),
                     "--jobs", str(arguments.jobs),
                     "--heartbeat", str(arguments.heartbeat),
                     "--failures-file", str(failures_file)] + passthrough
            for text in arguments.filter:
                sweep += ["--filter", text]
            if arguments.timeout is not None:
                sweep += ["--timeout", str(arguments.timeout)]
            if arguments.keep_output:
                sweep += ["--keep-output", arguments.keep_output]
            gates.append(run(
                "the example sweep",
                f"{'the filtered subset' if arguments.filter else f'all {len(scripts)} scripts'}"
                f": run, exit 0, print something, verified header, in the "
                f"ledger, pure ASCII, under cp437",
                sweep))
            reported = _reported_scripts(failures_file)

    # -- The verdict --------------------------------------------------------
    print("=" * 100)
    print("VERDICT")
    print("=" * 100)
    print(f"  {'gate':<28} {'result':<8} {'seconds':>9}  exit")
    for name, ok, seconds, code, _ in gates:
        print(f"  {name:<28} {'PASSED' if ok else 'FAILED':<8} "
              f"{seconds:>9.1f}  {code}")

    failed = [name for name, ok, _, _, _ in gates if not ok]
    print(f"  {'':<28} {'':<8} {time.monotonic() - started:>9.1f}  total wall")
    print()

    # Name the SCRIPT, not just the gate. This is the part a `Show-Tail 18`
    # can actually see; see the note at the top of this file.
    if reported:
        print(f"  THE {len(reported)} SCRIPT(S) THE SWEEP REPORTED:")
        for path, why, detail in reported:
            print(f"    {why:<14} {path}")
            if detail.strip():
                print(f"                   {detail.strip()[:200]}")
        print()

    # And for any gate that is not the sweep, its own last words.
    for name, ok, _, _, remembered in gates:
        if ok or name == "the example sweep":
            continue
        print(f"  LAST WORDS OF THE FAILED GATE '{name}':")
        for line in _tail_of(remembered):
            print(f"    {line}")
        print()

    if failed:
        print(f"  {len(failed)} of {len(gates)} gate(s) FAILED: "
              f"{', '.join(failed)}")
        print()
        print("  Read them in gate order. A stale ledger is a bookkeeping")
        print("  fix; a drifted pinned value means the engine changed and")
        print("  nothing below it is worth reading; a sweep failure with the")
        print("  pins intact is a script problem.")
        return 1

    if arguments.filter:
        # Deliberately NOT the words the PowerShell harnesses match on. A
        # subset that passes says nothing about the tree.
        print(f"  FILTERED RUN: {len(gates)} gate(s) passed for "
              f"{', '.join(arguments.filter)} only.")
        print()
        print("  THIS IS NOT A PASS FOR THE TREE. Drop --filter to make a")
        print("  claim about the example tree as a whole.")
        return 0

    print(f"  ALL {len(gates)} GATES PASSED.")
    print()
    print("  Every example runs, every pinned value is exact, the ledger")
    print("  matches the headers, and nothing prints a character a default")
    print("  Windows console cannot show.")
    print()
    print("  What this does NOT tell you: whether a number is right for a")
    print("  case nobody pinned. The pinned values are the oracle, and they")
    print("  cover the reference case of each engine - see VERIFICATION.md")
    print("  for what each one was checked against.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
