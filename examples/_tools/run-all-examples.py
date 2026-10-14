# Internal verification harness - NOT part of the user documentation.
#
# Runs EVERY example script in this tree against prokon-automation.exe and
# reports one line per script. Non-zero exit if any script failed, so this
# file is the gate: a broken example cannot ship quietly.
#
# Usage:
#   <sealed-runtime>/python.exe _tools/run-all-examples.py [options]
#
#   --jobs N          scripts in flight at once (default 4).
#   --timeout S       seconds per script (default 600).
#   --filter TEXT     run only scripts whose path contains TEXT (repeatable).
#   --list            list what would run, and stop.
#   --package-dir D   passed through to run-example.py.
#   --engine-home D   passed through to run-example.py.
#   --keep-output D   write every script's stdout/stderr under D.
#   --failures-file F write one reported script per line to F, for a caller.
#   --heartbeat S     seconds between "still going" lines (0 disables).
#   --quiet           results only - no "running" lines, no heartbeat.
#
# EVERY SCRIPT ANNOUNCES ITSELF TWICE: once the moment it STARTS, and once
# the moment it FINISHES, carrying its verdict. Nothing waits for anything
# else. That is the whole reporting contract of this file, and it is worth
# stating plainly because the obvious way to write this sweep breaks it.
#
# WHY NOT ThreadPoolExecutor.map - MEASURED 2026-09-08, AND THIS IS THE
# DEFECT THIS FILE WAS REWRITTEN TO DELETE. `pool.map` yields results in
# SUBMISSION order, not completion order, so a finished script is withheld
# until every script submitted before it has also finished. Measured on the
# twelve chart examples with --jobs 6:
#
#     crack_widths_selection_map.py   finished at  67.6s, printed at 194.3s
#     eight scripts finished before   460.6s, ALL EIGHT printed at 460.6s
#     the first result line arrived at 194.3s - 194 seconds of pure silence
#
# One 460-second script at the head of the queue silenced the other eleven.
# `as_completed` is therefore not a preference here, it is the fix. And the
# progress counter counts REPORTED completions rather than finished ones,
# so it can never run ahead of what the reader has actually been shown.
#
# EACH SCRIPT RUNS IN ITS OWN PROCESS, in its own temporary working
# directory. That is not tidiness: an example that writes a spreadsheet
# writes it to the working directory, and a script that hangs or dies must
# not be able to take the sweep with it, nor to make the NEXT script's
# result a statement about this one.
#
# WHAT A PASS MEANS, AND WHAT IT DOES NOT. A pass here is "the script ran
# to completion, printed something, and exited 0". That is a REGRESSION
# GATE, not verification - VERIFICATION.md's definition stands, and it
# needs a number checked against a pinned value, a desktop run or a
# published worked example. This tool is what tells you an example that WAS
# verified still runs; it is deliberately unable to tell you a number is
# right, so it can never be read as if it could.
#
# THE HEADER IS CHECKED TOO, because a green run of an unverified script is
# exactly the state VERIFICATION.md exists to prevent. Every script must
# carry a "# Verified:" line, and one that says anything other than "yes"
# is reported as UNVERIFIED even when it runs perfectly. A script absent
# from VERIFICATION.md's ledger is reported the same way.
#
# A FAILURE PRINTS ITS CAUSE WHERE IT HAPPENED, AND --quiet CANNOT SUPPRESS
# THAT. It used to: --quiet withheld the stderr excerpt, and
# verify-everything.py always passed --quiet, so the one caller that
# matters showed a bare "exit 1" and nothing else until the end-of-run
# summary. A sweep read while it ran, or killed before it finished, then
# named no cause at all. --quiet now means "no per-script running lines",
# and it has no say over how a failure is reported.
#
# TWO MORE WAYS THIS FILE USED TO EXIT NON-ZERO WITHOUT NAMING ANYTHING,
# BOTH MEASURED 2026-09-08 WITH ONE SCRIPT (_probe/probe_hidden.py: no
# Verified header, stdout carrying a cp437-encodable non-ASCII character):
#
#   (a) the per-script note was ASSIGNED rather than appended when the
#       header was bad, which ERASED an already-recorded non-ASCII flag
#       from the line;
#   (b) `nonascii` fed the exit code and had NO end-of-run section, so a
#       script offending only on the ASCII rule made the sweep exit 1 with
#       the word "ASCII" appearing nowhere in its entire output.
#
# The measured old output for that one script was
#   PASS  _probe/probe_hidden.py  [header: Verified: MISSING]  [not in VERIFICATION.md]
# followed by exit 1. Both are fixed here: notes accumulate, and there is a
# NON-ASCII STDOUT section beside the other three.
#
# AND EVERY SCRIPT RUNS UNDER cp437, WHICH IS NOT A DETAIL. That is the
# code page a default Windows console still starts in, and it cannot encode
# an em dash. A script that prints one dies with UnicodeEncodeError at the
# exact moment it was reporting something - which is the worst possible
# moment, because the reader sees a traceback instead of an answer.
#
# This was measured, not assumed. On 2026-09-02 five shipped examples
# printed a literal em dash; under cp437 one of them
# (recipes/general_column_smallest_section.py) exited 1 with a
# UnicodeEncodeError naming the character, while an ASCII-only control
# (quickstarts/beam_section_quickstart.py) exited 0 under utf-8, cp1252 AND
# cp437. So the failure is the character, not the setting. Under cp1252 the
# em dash survives, which is exactly why a sweep on this machine's own
# default would have missed all five.
#
# --io-encoding changes it; utf-8 hides the whole class of fault, so it is
# a deliberate choice rather than the default. Non-ASCII stdout is ALSO
# reported directly, because that rule does not depend on a code page.

import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_EXAMPLES_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIRECTORY_NAME = "_tools"
_LEDGER = _EXAMPLES_ROOT / "VERIFICATION.md"
_RUNNER = Path(__file__).resolve().parent / "run-example.py"

_VERIFIED_LINE = re.compile(r"^#\s*Verified:\s*(\S+)", re.MULTILINE)
_LEDGER_SCRIPT = re.compile(r"`((?:[\w.\-]+/)+[\w.\-]+\.py)`")

# ONE lock for BOTH the counters and the printing. Two locks would let a
# line print against a count taken a moment earlier, and a progress report
# that disagrees with itself is worse than no progress report at all.
_SPEAK = threading.Lock()


def _scripts(filters):
    """Every example in the tree, sorted, with the harness itself excluded."""
    found = []
    for path in sorted(_EXAMPLES_ROOT.rglob("*.py")):
        if _TOOLS_DIRECTORY_NAME in path.relative_to(_EXAMPLES_ROOT).parts:
            continue
        relative = path.relative_to(_EXAMPLES_ROOT).as_posix()
        if filters and not any(f in relative for f in filters):
            continue
        found.append(path)
    return found


def _header_verdict(path):
    """"yes", or whatever the header claims, or None when there is no header."""
    match = _VERIFIED_LINE.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip().lower() if match else None


def _ledger_entries():
    """The script paths the ledger lists, as posix relative paths."""
    if not _LEDGER.is_file():
        return set()
    return set(_LEDGER_SCRIPT.findall(_LEDGER.read_text(encoding="utf-8")))


def _ascii(text):
    """Plain ASCII, always - anything else becomes a visible escape.

    This harness's own stdout must be ASCII, and a failure tail is the one
    place non-ASCII can enter it: an example's stderr is decoded from
    cp437, where every byte above 127 maps to some Unicode character. Left
    alone, that character then has to survive THIS process's own stdout
    encoding, which is the platform's and not cp437 - so the harness could
    die with UnicodeEncodeError while reporting someone else's failure, or
    hand its own caller bytes the caller decodes differently. Escaping it
    keeps the byte visible and the harness ASCII.
    """
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _keep_failure_output(relative, out, err, code):
    """Write a failed script's complete stdout and stderr, and return the path.

    Lives beside the harness's other scratch, under the system temp directory, so a
    sweep run from a read-only checkout still works and nothing lands in the tree the
    fingerprint watches. Returns None if it cannot be written - a failure to record a
    failure must never replace the failure.

    The folder is a CONSTANT path and files in it are overwritten by name, so a file
    from an earlier sweep sits beside a current one and looks equally fresh. That is the
    shape CLAUDE.md records as having cost 46 MCP test failures, and the honest fix here
    is not a cleanup pass - a sweep must never delete evidence a person may still be
    reading - but a STAMP: every file says when it was written and which run wrote it,
    so "this is from the run I just did" is something the reader checks rather than
    assumes. Three reviewers raised the staleness; none could have read a date, because
    there wasn't one.
    """
    try:
        folder = Path(tempfile.gettempdir()) / "prokon-sweep-failures"
        folder.mkdir(parents=True, exist_ok=True)

        name = relative.replace("/", "__").replace(chr(92), "__") + ".txt"
        path = folder / name

        path.write_text(
            "script : {0}{1}exit   : {2}{1}written: {3}{1}run pid: {4}{1}"
            "{1}---- stdout ----{1}{5}{1}{1}---- stderr ----{1}{6}{1}"
            .format(relative, chr(10), code,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    os.getpid(), out, err),
            encoding="utf-8", errors="backslashreplace")

        return path
    except Exception:
        return None


def _clock(seconds):
    """A duration a reader takes in at a glance.

    One decimal under a minute, because most examples finish in well under
    one second and rounding them all to "0s" throws away the only number
    on the line. Minutes above that, because nobody reads 460.6.
    """
    if seconds < 60:
        return "{0:.1f}s".format(seconds)
    return "{0}m{1:02d}s".format(int(seconds) // 60, int(seconds) % 60)


class Progress(object):
    """What has started, what has finished, and what is still in flight.

    Every method both moves the counters and prints, under one lock, so the
    number on a line is the number that was true when it was written.
    """

    def __init__(self, total, width, announce_starts):
        self.total = total
        self.width = width
        self.announce_starts = announce_starts
        self.in_flight = {}          # relative path -> monotonic start
        self.done = 0
        self.failed = 0
        self.began = time.monotonic()

    def starting(self, relative):
        """The script has this instant begun running."""
        with _SPEAK:
            self.in_flight[relative] = time.monotonic()
            if self.announce_starts:
                print("{0:<{1}}  running".format(_ascii(relative), self.width))
                sys.stdout.flush()

    def finished(self, relative, verdict, seconds, trailer, note):
        """One completion line. `verdict` is PASS, FAIL or DRIFT.

        Anything that is not PASS counts as failed, which is what makes DRIFT a
        verdict rather than a footnote: a script reporting its own anchor drifted
        used to print PASS with a note appended, and the headline counted it among
        the passes while the exit code said otherwise.
        """
        with _SPEAK:
            self.in_flight.pop(relative, None)
            self.done += 1
            if verdict != "PASS":
                self.failed += 1
            print("{0:<{1}}  {2}  {3:>6}  [{4:>3}/{5}, {6} failed]{7}{8}".format(
                _ascii(relative), self.width, verdict, _clock(seconds),
                self.done, self.total, self.failed, trailer, note))
            sys.stdout.flush()

    def detail(self, lines):
        """The cause of a failure, printed where the failure happened."""
        with _SPEAK:
            for line in lines:
                print("      | {0}".format(_ascii(line)))
            sys.stdout.flush()

    def heartbeat(self):
        """Proof of life while one long script holds the sweep open.

        NO ETA, AND THAT IS DELIBERATE - MEASURED 2026-09-08. A first cut
        divided elapsed time by completions and printed "~2s left" while a
        45-second script was still running, because the six that had
        already finished took under half a second each. These examples run
        anywhere from 0.2 to 460 seconds and nothing here knows which is
        which in advance, so any such figure is a guess wearing a number's
        clothing. What this prints instead is all fact: how many are in
        flight, which has been running longest and for how long, how many
        are done, and how long the sweep has been going.
        """
        with _SPEAK:
            if not self.in_flight:
                return
            now = time.monotonic()
            slowest = max(self.in_flight.items(), key=lambda item: now - item[1])
            print("....  {0} in flight, longest {1} {2}  |  {3}/{4} done, "
                  "{5} elapsed".format(
                      len(self.in_flight), Path(slowest[0]).name,
                      _clock(now - slowest[1]), self.done, self.total,
                      _clock(now - self.began)))
            sys.stdout.flush()


def _pulse(progress, every, stop):
    while not stop.wait(every):
        progress.heartbeat()


def _run_one(path, arguments, progress):
    """Run one example. Returns (path, exit code, seconds, stdout, stderr)."""
    progress.starting(path.relative_to(_EXAMPLES_ROOT).as_posix())

    command = [sys.executable, str(_RUNNER)]
    if arguments.package_dir:
        command += ["--package-dir", arguments.package_dir]
    if arguments.engine_home:
        command += ["--engine-home", arguments.engine_home]
    command.append(str(path))

    environment = dict(os.environ)
    # matplotlib must never try to open a window in a sweep.
    environment["MPLBACKEND"] = "Agg"
    # The console a reader actually has. See the note at the top.
    environment["PYTHONIOENCODING"] = arguments.io_encoding

    started = time.monotonic()
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True,
            encoding=arguments.io_encoding, errors="replace",
            timeout=arguments.timeout, env=environment,
        )
        return (path, completed.returncode, time.monotonic() - started,
                completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as expired:
        out = expired.stdout or ""
        if isinstance(out, bytes):
            out = out.decode(arguments.io_encoding, "replace")

        # The child's OWN stderr, and then our line - not our line INSTEAD of it. Until
        # 2026-09-18 expired.stderr was dropped on the floor and replaced by the TIMEOUT
        # sentence, so the kept transcript for a hang - the one failure where a partial
        # transcript is the whole evidence, because there is no exit and no traceback -
        # carried one synthesised line and nothing the script had said. Three reviewers
        # named it against _keep_failure_output's promise of "complete stdout and stderr".
        err = expired.stderr or ""
        if isinstance(err, bytes):
            err = err.decode(arguments.io_encoding, "replace")

        timed_out = "TIMEOUT after {0}s".format(arguments.timeout)
        return (path, 124, time.monotonic() - started, out,
                (err.rstrip() + chr(10) + timed_out) if err.strip() else timed_out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--filter", action="append", default=[])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--package-dir", default=None)
    parser.add_argument("--engine-home", default=None)
    parser.add_argument("--keep-output", default=None)
    parser.add_argument("--failures-file", default=None)
    parser.add_argument("--heartbeat", type=int, default=30)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--io-encoding", default="cp437")
    arguments = parser.parse_args()

    scripts = _scripts(arguments.filter)
    if not scripts:
        print("no example scripts matched", file=sys.stderr)
        return 2

    if arguments.list:
        for path in scripts:
            print(path.relative_to(_EXAMPLES_ROOT).as_posix())
        print("\n{0} script(s)".format(len(scripts)))
        return 0

    keep = Path(arguments.keep_output).resolve() if arguments.keep_output else None
    if keep:
        keep.mkdir(parents=True, exist_ok=True)

    ledger = _ledger_entries()

    relatives = [p.relative_to(_EXAMPLES_ROOT).as_posix() for p in scripts]
    width = min(max(len(name) for name in relatives), 60)

    print("PROKON example sweep - {0} script(s), {1} at a time".format(
        len(scripts), arguments.jobs))
    print("interpreter: {0}".format(sys.executable))
    print("console    : PYTHONIOENCODING={0}".format(arguments.io_encoding))
    print("every script says `running` when it starts and PASS or FAIL when it ends,")
    print("in COMPLETION order - nothing is held back waiting for a slower script.")
    print("=" * 100)
    sys.stdout.flush()

    progress = Progress(len(scripts), width, announce_starts=not arguments.quiet)

    stop = threading.Event()
    heart = None
    if arguments.heartbeat > 0 and not arguments.quiet:
        heart = threading.Thread(target=_pulse,
                                 args=(progress, arguments.heartbeat, stop),
                                 daemon=True)
        heart.start()

    failures, unverified, unlisted, nonascii, results = [], [], [], [], []
    drifted = []
    started = time.monotonic()

    try:
        with ThreadPoolExecutor(max_workers=arguments.jobs) as pool:
            futures = [pool.submit(_run_one, path, arguments, progress)
                       for path in scripts]

            # COMPLETION ORDER. See the measurement at the top of this file.
            for future in as_completed(futures):
                path, code, seconds, out, err = future.result()
                relative = path.relative_to(_EXAMPLES_ROOT).as_posix()
                results.append((relative, code, seconds))

                if keep:
                    target = keep / (relative.replace("/", "__") + ".txt")
                    target.write_text(
                        "$ {0}\nexit {1} in {2:.1f}s\n--- stdout ---\n{3}\n"
                        "--- stderr ---\n{4}\n".format(
                            relative, code, seconds, out, err),
                        encoding="utf-8")

                verdict = _header_verdict(path)
                note = ""
                # Encoding-independent, and stricter than the code page: the
                # rule is plain ASCII, so say so even where cp437 coped.
                unprintable = sorted({c for c in out if ord(c) > 127})
                if unprintable:
                    nonascii.append((relative, unprintable))
                    note += "  [non-ASCII stdout: {0}]".format(
                        " ".join(hex(ord(c)) for c in unprintable[:6]))
                # A SCRIPT THAT SAYS ITS OWN ANCHOR DRIFTED HAS FAILED, AND UNTIL
                # 2026-09-18 THIS SWEEP PASSED IT. Measured that day: C14's DevOps
                # 10408 fix moved five values, six retaining-wall examples printed
                # DRIFTED for 687 seconds, and the sweep reported every one of them
                # as PASS. Only check-pinned-values.py failed - and it pins ONE
                # example per module, so the other five copies of that anchor were
                # checked by nothing at all.
                #
                # The examples already own the right oracle: each compares its
                # measured values with its pinned anchor by EXACT equality, with no
                # tolerance, and prints the verdict. Nothing here needs to know a
                # value, a module or a tolerance - it needs to stop discarding an
                # answer the script already computed. Roughly 53 examples across all
                # twelve engines carry the pattern, so this covers the fleet rather
                # than the engine that happened to move.
                #
                # Their own words are the argument: several print
                # "DRIFTED, READ NOTHING BELOW". A sweep that reads a script saying
                # that and reports PASS is asserting the opposite of what it was told.
                if "DRIFTED" in out:
                    drifted.append(relative)
                    note += "  [the script reports its pinned anchor DRIFTED]"

                if verdict != "yes":
                    unverified.append(relative)
                    note += "  [header: Verified: {0}]".format(verdict or "MISSING")
                if relative not in ledger:
                    unlisted.append(relative)
                    note += "  [not in VERIFICATION.md]"

                if code == 0 and out.strip():
                    # DRIFT, not PASS. The script ran and said its own pinned anchor no
                    # longer matches the engine - reporting that as a pass is asserting
                    # the opposite of what it was told, which several of them say in as
                    # many words: "DRIFTED, READ NOTHING BELOW".
                    progress.finished(relative,
                                      "DRIFT" if relative in drifted else "PASS",
                                      seconds, "", note)
                elif code == 0:
                    # ⛔ THIS FAILURE KEEPS ITS OUTPUT TOO, AND IT IS THE ONE THAT NEEDS
                    # IT MOST. Until 2026-09-18 _keep_failure_output was called only on the
                    # non-zero branch below, and this branch threw `err` away entirely - it
                    # did not even print a stderr tail, unlike every other failure. All five
                    # reviewers found it, and the asymmetry is backwards: stdout is empty
                    # here BY DEFINITION of the branch, so stderr is not merely the best
                    # evidence, it is the only evidence there is. A script that writes a
                    # traceback to stderr from an atexit handler and still exits 0 left
                    # nothing behind at all.
                    kept = _keep_failure_output(relative, out, err, code)

                    detail = "exited 0 but printed nothing"
                    if kept:
                        detail = "[full output: {0}]  {1}".format(
                            _ascii(str(kept)), detail)

                    failures.append((relative, code, detail))
                    progress.finished(relative, "FAIL", seconds,
                                      "  <- printed nothing", note)
                    progress.detail(["exited 0 but printed nothing at all - an "
                                     "example with no output has nothing to verify"]
                                    + err.strip().splitlines()[-14:])
                else:
                    # \u26d4 THE WHOLE OUTPUT IS KEPT FOR EVERY RECORDED FAILURE, AND THE TAIL
                    # ALONE ONCE COST A DIAGNOSIS. On 2026-09-18 one script failed inside
                    # the gate with OSError [Errno 22] and the only record was three
                    # lines, truncated by the caller's display at 150 characters - so the
                    # path the write failed on was cut off mid-way and the one fact that
                    # would have named the cause was gone. The script passed on every
                    # later attempt, in two interpreters, so there was nothing left to
                    # read. --keep-output already existed; it is not much use as an option
                    # you have to have known to pass BEFORE the failure you did not expect.
                    #
                    # \u26a0 ONLY ON FAILURE. A passing sweep writes nothing: 133 scripts'
                    # full output every run would be noise, and the tail is enough when
                    # there is nothing to diagnose.
                    kept = _keep_failure_output(relative, out, err, code)

                    tail = _ascii(" | ".join(
                        line for line in err.strip().splitlines()[-3:]
                        if line.strip()))
                    # ⚠ THE POINTER GOES FIRST, BECAUSE THE ONLY CALLER THAT CONDENSES
                    # THIS TRUNCATES IT. verify-everything.py prints a reported script as
                    # detail.strip()[:200]; the kept path is around 110 of those characters,
                    # so appended at the END a stderr tail of any length pushes it off - and
                    # the operator sees the same truncated tail that cost the diagnosis, with
                    # no hint that the full transcript exists. Putting it first costs the tail
                    # its last characters instead, which is the half that was already being
                    # lost. One reviewer computed this; the threshold is arithmetic, not luck.
                    if kept:
                        tail = "[full output: {0}]  {1}".format(_ascii(str(kept)), tail)
                    failures.append((relative, code, tail))
                    # Say TIMEOUT on the line. `exit 124` is this file's own
                    # invention for a killed script and means nothing to a
                    # reader, while a timeout is the one failure whose cause
                    # is already known without reading any stderr.
                    progress.finished(
                        relative, "FAIL", seconds,
                        "  <- TIMEOUT after {0}s".format(arguments.timeout)
                        if code == 124 else "  <- exit {0}".format(code),
                        note)
                    # ALWAYS, and --quiet has no say. See the note at the top.
                    progress.detail(
                        err.strip().splitlines()[-14:]
                        or ["exit {0}, and it wrote nothing to stderr".format(code)])
    finally:
        stop.set()
        if heart is not None:
            heart.join(timeout=2)

    elapsed = time.monotonic() - started
    print("=" * 100)
    # Drifted scripts are their own column. Folding them into "passed" is how a run
    # printed "133 passed, 0 failed" and then exited 1.
    #
    # ⚠ A SET UNION, NOT TWO SUBTRACTIONS - the two lists OVERLAP. `drifted` is
    # appended on "DRIFTED" in stdout, before and independently of the exit-code branch,
    # so a script that prints its drift banner and THEN raises is in both, and
    # len(scripts) - len(failures) - len(drifted) counts it twice. All five reviewers
    # found it. It is not hypothetical here: the chart examples compute and print their
    # anchor comparison before they ever call savefig, which is the call that failed in
    # this tree on 2026-09-18. The first version of this line replaced a number that was
    # wrong in one direction with one that could be wrong in the other.
    reported = {name for name, _, _ in failures} | set(drifted)
    print("{0} passed, {1} failed, {2} drifted  in {3:.1f}s wall".format(
        len(scripts) - len(reported), len(failures), len(drifted), elapsed))

    if failures:
        print("\nFAILED ({0}):".format(len(failures)))
        for relative, code, tail in sorted(failures):
            print("  {0}  (exit {1})  {2}".format(relative, code, tail))

    if unverified:
        print("\nUNVERIFIED HEADER ({0}) - ran, but the header does not claim "
              "verification:".format(len(unverified)))
        for relative in sorted(unverified):
            print("  {0}".format(relative))

    if unlisted:
        print("\nNOT IN VERIFICATION.md ({0}):".format(len(unlisted)))
        for relative in sorted(unlisted):
            print("  {0}".format(relative))

    if drifted:
        print("\nANCHOR DRIFTED ({0}) - the script ran, and says its own pinned "
              "values no longer match the engine:".format(len(drifted)))
        for relative in sorted(drifted):
            print("  {0}".format(relative))
        print("  A DRIFT IS NOT AUTOMATICALLY A BUG. Either the engine's answer "
              "changed or the example's inputs did - check the example's diff "
              "first, then VERIFICATION.md for what that anchor was originally "
              "checked against. What it is NOT is something to pass over.")

    if nonascii:
        print("\nNON-ASCII STDOUT ({0}):".format(len(nonascii)))
        for relative, characters in sorted(nonascii):
            print("  {0}  {1}".format(
                relative, " ".join(hex(ord(c)) for c in characters[:12])))

    print("\nslowest:")
    for relative, _, seconds in sorted(results, key=lambda r: -r[2])[:8]:
        print("  {0:6.1f}s  {1}".format(seconds, relative))

    # The reported names, handed up to whatever ran this sweep, so a caller
    # that shows only a tail can still name the SCRIPT rather than the gate.
    if arguments.failures_file:
        reported = ["{0}\tFAILED\t{1}".format(name, tail)
                    for name, _, tail in sorted(failures)]
        reported += ["{0}\tUNVERIFIED\t".format(name)
                     for name in sorted(unverified)]
        reported += ["{0}\tNOT-IN-LEDGER\t".format(name)
                     for name in sorted(unlisted)]
        reported += ["{0}\tDRIFTED\t".format(name) for name in sorted(drifted)]
        reported += ["{0}\tNON-ASCII\t{1}".format(
            name, " ".join(hex(ord(c)) for c in characters[:12]))
            for name, characters in sorted(nonascii)]
        Path(arguments.failures_file).write_text(
            "\n".join(reported) + ("\n" if reported else ""), encoding="utf-8")

    return 1 if (failures or unverified or unlisted or nonascii or drifted) else 0


if __name__ == "__main__":
    raise SystemExit(main())
