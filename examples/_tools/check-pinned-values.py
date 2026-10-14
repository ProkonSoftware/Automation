# Internal verification harness - NOT part of the user documentation.
#
# THE NUMERIC ORACLE. run-all-examples.py tells you an example still RUNS;
# this file tells you it still gets the same ANSWER, to the last binary
# digit, on all twelve engines.
#
# Usage:
#   <sealed-runtime>/python.exe _tools/check-pinned-values.py [options]
#
#   --package-dir D   the folder containing the `prokon` package.
#   --engine-home D   an engine folder, exported as PROKON_ENGINE_HOME.
#   --module NAME     check only this module (repeatable).
#   --self-test       prove the oracle can FAIL, then stop.
#   --show            print every checked value, not just the failures.
#
# HOW IT AVOIDS A SECOND COPY OF THE INPUTS, which is the whole design.
# A pin needs two halves: the inputs, and the number they produce. If this
# file carried both, it would be a transcription of the example - and a
# transcription drifts. So it carries only the EXPECTED NUMBERS, and gets
# the inputs by RUNNING THE EXAMPLE ITSELF with prokon.v5.<module>.analyse
# wrapped to record every call. The example is the single source of the
# inputs; this file is the single source of the answers. Change the
# example's section and this oracle fails loudly rather than silently
# checking a section nobody documents.
#
# WHY == AND NOT A TOLERANCE. These engines are the incumbent Delphi
# calculation, and the numbers are its numbers. A tolerance would let a
# real change in the calculation hide inside it, which is exactly what a
# golden master exists to prevent. Where the example itself only prints a
# rounded value, the pin here is still the full-precision result - the
# printed digits are what the READER checks, and the full float is what
# the ENGINE promised.
#
# EVERY PIN'S PROVENANCE IS IN VERIFICATION.md, beside the script that
# produced it: a value pinned in that engine's own test suite, a desktop
# run, or a published worked example. This file re-checks them; it does
# not originate them, and a number appearing here for the first time is
# not yet a pin.
#
# THE POSITIVE CONTROL IS BUILT IN. --self-test corrupts one expected
# value and requires this tool to report a failure. Without it, a bug that
# made every comparison pass would look exactly like a clean run: the
# oracle would be constant, and a constant oracle is not evidence.

import argparse
import os
import re
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _scratch import scratch_directory

_EXAMPLES_ROOT = Path(__file__).resolve().parent.parent
_QUICKSTARTS = _EXAMPLES_ROOT / "quickstarts"
# ⚠ ProkonForIDE\ was inserted above the installers on 2026-09-09. See the same
# constant in run-example.py: a miss here is silent, falling through to whatever
# package the interpreter already has.
_REPO_STAGING = (Path("ProkonForIDE") / "ProkonSpyderInstaller"
                 / "build" / "staging" / "python")

_LEADING_INDEX = re.compile(r"^\[(\d+)\]")

# module -> (example script, [(result path, the exact number it must return)])
#
# Paths are dotted, with [n] for a list index. A key that CONTAINS a dot -
# "shear.ok", "sls.pm" - is written with the dot and resolved longest-key
# first, so a flat key beats a nested walk.
PINS = {
    "beam_section": ("beam_section_quickstart.py", [
        ("mu", 295.18197048179997),
        ("ast", 1287.32677061758),
    ]),
    "circular_column": ("circular_column_quickstart.py", [
        ("total_as", 1037.1145165134003),
    ]),
    "continuous_beam": ("continuous_beam_quickstart.py", [
        ("spans[0].max_bottom_steel", 805.0209555473922),
        ("spans[0].max_top_steel", 1235.4393480298781),
        ("spans[0].max_shear_steel", 0.6078222002339925),
        ("max_deflection", 12.446682698091044),
        ("max_crack_width", 0.11738993516717798),
    ]),
    "crack_widths": ("crack_widths_quickstart.py", [
        ("load_cases[0].optimised_configs[0].calc_result.governing_crack_width",
         0.11059554804834058),
        ("load_cases[0].optimised_configs[0].calc_result.steel_area", 1047.197551196598),
        ("load_cases[0].optimised_configs[0].moment_capacity", 99.75807235558123),
    ]),
    "general_column": ("general_column_quickstart.py", [
        # LC1's own factor, not the result-level minimum - that is the
        # minimum over BOTH cases and reads 1.1236 here.
        ("load_cases[0].min_capacity_factor", 2.179097995657654),
        ("load_cases[1].min_capacity_factor", 1.123583760958025),
        ("steel_area", 1963.4954084936207),
        ("concrete_area", 160000),
        ("reinforcement_ratio", 1.227184630308513),
    ]),
    "pad_footing": ("pad_footing_quickstart.py", [
        ("max_bearing_pressure_sls", 133.98908218356328),
        ("max_bearing_pressure", 182.9047150569886),
        ("load_cases[0].shear.vcx", 0.3568429018580138),
    ]),
    "pile_cap": ("pile_cap_quickstart.py", [
        ("overhang_min_required", 0.226),
        ("strut_results[0].load_cases[0].cr", 2064.6284818393965),
        ("column_node.load_cases[0].pr", 4143.75),
        ("pile_nodes[0].load_cases[0].pr", 3583.7718),
        ("tie_minim_reinforcement", 2400),
    ]),
    "prestressed_concrete": ("prestressed_concrete_quickstart.py", [
        ("punching[0].perimeters[0].veff", 537.0024640743725),
        ("punching[1].perimeters[0].veff", 575.0436234065779),
        ("punching[2].perimeters[0].veff", 469.57376394972823),
    ]),
    "punching_shear": ("punching_shear_quickstart.py", [
        ("uo", 1600),
        ("critical_perimeters[0].asv", 2519.6003848228493),
    ]),
    "rectangular_column": ("rectangular_column_quickstart.py", [
        ("options[0].ast", 4521.012783203123),
        ("options[0].perc", 2.8249267578124986),
    ]),
    # ⚠ REPINNED 2026-09-10, AND THE OLD PINS COULD NOT SIMPLY BE RE-MEASURED.
    # This engine's analyse used to design a one-metre STRIP from four moments you
    # supplied; it now analyses the whole PANEL and works the moments out itself. The
    # old quadruple was an answer to a question the engine no longer accepts.
    #
    # The replacement panel is the desktop program's OWN Default Example - the one
    # that opens when you start Slab.exe - so every pin here is a value that program
    # printed on its calcsheet, not a number this tree originated. Both halves of the
    # answer are pinned: the steel AND the moments it came from, because the moments
    # are what this engine now computes and the steel is only what follows from them.
    "rectangular_slab": ("rectangular_slab_quickstart.py", [
        ("ast.x_top", 688.5778364639625),          # calcsheet  689
        ("ast.x_bot", 348.6899816006131),          # calcsheet  349
        ("ast.y_top", 1105.9653884167026),         # calcsheet 1106
        ("ast.y_bot", 566.2790078087527),          # calcsheet  566
        ("moment_max.x_top", 50.62170890244854),   # calcsheet  50.6
        ("moment_max.x_bot", 25.924342110306455),  # calcsheet  25.9
        ("moment_max.y_top", 86.78118560016168),   # calcsheet  86.8
        ("moment_max.y_bot", 46.31177450818539),   # calcsheet  46.3
    ]),
    "retaining_wall": ("retaining_wall_quickstart.py", [
        ("sf_overturning", 4.477940718035636),
        ("sf_sliding", 1.6341314510288516),
        ("qmax", 97.26517611421157),
        ("as_wall_req", 915.8514440593759),
        ("as_base_req", 791.8667235080961),
    ]),
}

_MISSING = object()


def _dig(node, path):
    """Resolve a dotted path with [n] indices anywhere along it.

    A key that CONTAINS a dot - "shear.ok", "sls.pm", "torsion.solved" - is
    written with its dot, and the longest literal key that fits wins. That
    matters because these engines publish flat keys with dots in them, so
    splitting on "." first would look for a nested dictionary that has never
    existed and report the pin as missing rather than as wrong.
    """
    while path:
        leading = _LEADING_INDEX.match(path)
        if leading:
            index = int(leading.group(1))
            if not isinstance(node, list) or index >= len(node):
                return _MISSING
            node = node[index]
            path = path[leading.end():]
            if path.startswith("."):
                path = path[1:]
            continue

        if not isinstance(node, dict):
            return _MISSING

        for candidate in sorted((k for k in node if path.startswith(k)),
                                key=len, reverse=True):
            rest = path[len(candidate):]
            if rest == "":
                return node[candidate]
            if rest.startswith("."):
                node, path = node[candidate], rest[1:]
                break
            if rest.startswith("["):
                node, path = node[candidate], rest
                break
        else:
            return _MISSING
    return node


def _package_dir(requested):
    if requested:
        return Path(requested).resolve()
    from_environment = os.environ.get("PROKON_EXAMPLES_PACKAGE_DIR")
    if from_environment:
        return Path(from_environment).resolve()
    staged = _EXAMPLES_ROOT.parents[2] / _REPO_STAGING
    return staged.resolve() if (staged / "prokon" / "v5" / "__init__.py").is_file() else None


def _run_capturing(prokon, script):
    """Run an example with every analyse() call recorded. Returns the calls.

    ⚠ IN A TEMPORARY WORKING DIRECTORY, and that is not tidiness. An
    example writes its deliverable to the CURRENT directory, and
    quickstarts/prestressed_concrete_quickstart.py passes
    report_path="captain_report.txt" - so running the quickstarts from the
    examples folder drops a 44 KB report into the documentation tree, every
    time this oracle runs. Measured: it appeared in `git status` after a
    clean gate run, which is how it was found.
    """
    calls = []

    def wrap(name, module):
        real = module.analyse

        # ⚠ RECORD THE RESULT, RETURN THE ENVELOPE. analyse() hands back the whole
        # envelope, and the example unwraps it with ["result"] itself - so the
        # wrapper must pass the envelope through untouched or every example breaks.
        # The PINS, though, are written against the result dict, and _dig() below
        # walks paths like "spans[0].max_top_steel" that only exist inside it.
        def analyse(**inputs):
            envelope = real(**inputs)
            calls.append((name, inputs, envelope["result"]))
            return envelope

        return real, analyse

    restore = []
    for name, module in prokon.engines.items():
        real, wrapped = wrap(name, module)
        restore.append((module, real))
        module.analyse = wrapped

    devnull = open(os.devnull, "w", encoding="utf-8")
    saved_stdout = sys.stdout
    sys.stdout = devnull

    # NOT tempfile.TemporaryDirectory - see _scratch.py. The example spawns the
    # engine, the engine inherits this folder as its working directory, and Windows
    # does not reliably release that handle before the next statement deletes the
    # tree. It failed about one run in four, INCLUDING the self-test that is meant
    # to prove this oracle can fail at all.
    try:
        with scratch_directory("prokon-pins-"):
            runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.stdout = saved_stdout
        devnull.close()
        for module, real in restore:
            module.analyse = real

    return calls


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package-dir", default=None)
    parser.add_argument("--engine-home", default=None)
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--show", action="store_true")
    arguments = parser.parse_args()

    package_dir = _package_dir(arguments.package_dir)
    if package_dir is not None:
        sys.path.insert(0, str(package_dir))
    if arguments.engine_home:
        os.environ["PROKON_ENGINE_HOME"] = str(Path(arguments.engine_home).resolve())

    # See run-example.py: engines live on the versioned module; the bare parent is a
    # namespace package that exposes nothing. Local name kept as `prokon`.
    import prokon.v5 as prokon

    pins = dict(PINS)
    if arguments.module:
        pins = {k: v for k, v in pins.items() if k in arguments.module}
        if not pins:
            print("no module matched --module", file=sys.stderr)
            return 2

    if arguments.self_test:
        # THE POSITIVE CONTROL, and it runs the real engine. Three things
        # have to be true before a clean run above means anything:
        # a right value must compare equal, a value wrong by one ULP must
        # not, and an INDEXED path must actually resolve.
        #
        # That last one is not hypothetical. The first version of _dig
        # anchored its [n] pattern at the end of the path, so every
        # "spans[0].max_top_steel" resolved to <no such path> and 18 of 40
        # pins reported a drift that was entirely this file's fault. The
        # simple-path self-test passed throughout. So the control now
        # exercises a mid-path index, because a control that cannot fail
        # the way the code actually failed is not a control.
        script = _QUICKSTARTS / "continuous_beam_quickstart.py"
        calls = _run_capturing(prokon, script)
        result = calls[0][2]

        flat = _dig(result, "max_deflection")
        indexed = _dig(result, "spans[0].max_top_steel")
        print(f"self-test: flat path    max_deflection          = {flat!r}")
        print(f"self-test: indexed path spans[0].max_top_steel  = {indexed!r}")

        if indexed is _MISSING or not isinstance(indexed, float):
            print("SELF-TEST FAILED: an indexed path did not resolve to a number")
            return 1
        if _dig(result, "spans[99].max_top_steel") is not _MISSING:
            print("SELF-TEST FAILED: an out-of-range index did not report missing")
            return 1
        if _dig(result, "no_such_key") is not _MISSING:
            print("SELF-TEST FAILED: an absent key did not report missing")
            return 1

        corrupted = indexed * (1 + 2 ** -50)
        print(f"self-test: comparing against a deliberately wrong {corrupted!r}")
        if indexed == corrupted:
            print("SELF-TEST FAILED: a wrong value compared equal")
            return 1
        if indexed != 1235.4393480298781:
            print(f"SELF-TEST FAILED: expected 1235.4393480298781, got {indexed!r}")
            return 1

        print("SELF-TEST PASSED: right values accepted, wrong values rejected, "
              "indexed and absent paths both resolve correctly")
        return 0

    print(f"PROKON pinned-value check - {len(pins)} module(s)")
    print(f"interpreter: {sys.executable}")
    print(f"executable : {prokon.beam_section.executable}")
    print("=" * 100)

    drifts, checked = [], 0
    for module in sorted(pins):
        script_name, expectations = pins[module]
        script = _QUICKSTARTS / script_name
        if not script.is_file():
            drifts.append((module, script_name, "example script is missing", ""))
            print(f"FAIL  {module:22} {script_name} is missing")
            continue

        try:
            calls = _run_capturing(prokon, script)
        except Exception as failure:                       # noqa: BLE001
            drifts.append((module, script_name, f"the example raised {failure!r}", ""))
            print(f"FAIL  {module:22} the example raised {failure!r}")
            continue

        matching = [c for c in calls if c[0] == module]
        if not matching:
            drifts.append((module, script_name,
                           f"the example made no {module} call", ""))
            print(f"FAIL  {module:22} the example made no {module} call")
            continue

        result = matching[0][2]
        bad = []
        for path, expected in expectations:
            checked += 1
            got = _dig(result, path)
            if got is _MISSING:
                bad.append((path, "<no such path>", expected))
            elif got != expected:
                bad.append((path, got, expected))
            elif arguments.show:
                print(f"      {module:22} {path:52} {got!r}")

        if bad:
            for path, got, expected in bad:
                drifts.append((module, path, got, expected))
            print(f"FAIL  {module:22} {len(bad)} of {len(expectations)} pin(s) drifted")
            for path, got, expected in bad:
                print(f"        {path}")
                print(f"          got      {got!r}")
                print(f"          expected {expected!r}")
        else:
            print(f"PASS  {module:22} {len(expectations)} pin(s) exact  "
                  f"({script_name})")
        sys.stdout.flush()

    print("=" * 100)
    print(f"{checked - sum(1 for _ in drifts)} of {checked} pinned value(s) exact "
          f"across {len(pins)} module(s)")
    if drifts:
        print("\nA DRIFT IS NOT AUTOMATICALLY A BUG. Either the engine's answer "
              "changed, or\nthe example's inputs did. Check the example's diff "
              "first, then VERIFICATION.md\nfor what that pin was originally "
              "checked against.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
