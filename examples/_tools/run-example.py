# Internal verification harness - NOT part of the user documentation.
#
# Runs ONE example script exactly as an engineer runs it: `import prokon.v5`,
# and nothing else. The harness's only job is to put the shipped `prokon`
# package on sys.path when this interpreter has not had it installed, so a
# documentation example can be verified before the installer has been run
# on the machine doing the verifying.
#
# THE EXAMPLE SCRIPT NEVER KNOWS ABOUT THIS FILE. It does `import prokon.v5`,
# it gets the shipped package, and the package resolves the engine through
# its own probe order (prokon/v5/_discovery.py). Nothing here reaches past
# `import prokon.v5` into the engine, so a passing run says something about
# the product rather than about the harness.
#
# Usage:
#   python run-example.py [options] <example-script.py> [script args...]
#
#   --package-dir DIR   the folder CONTAINING the `prokon` package.
#   --engine-home DIR   an engine folder, exported as PROKON_ENGINE_HOME.
#   --in-place          run in the current directory instead of a temp one.
#   --show-target       print the interpreter, package and engine, then run.
#
# WHERE THE PACKAGE COMES FROM - explicit, named, first hit wins:
#
#   1. --package-dir                     the deliberate override.
#   2. PROKON_EXAMPLES_PACKAGE_DIR       the same, from the environment.
#   3. <repo>/ProkonForIDE/ProkonSpyderInstaller/build/staging/python
#                                        the installer's own build output,
#                                        which sits beside staging/engine/,
#                                        so the package's DECLARED sibling
#                                        layout finds prokon-automation.exe
#                                        with no environment variable at all.
#   4. whatever `import prokon.v5` already finds in this interpreter.
#
# There is no search and there is no PATH candidate: an example verified
# against an engine nobody named is not verified. A run prints which
# package and which executable answered, so the ledger can cite them.

import argparse
import os
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _scratch import scratch_directory

# ⚠ ProkonForIDE\ was inserted above the installers on 2026-09-09 so a VS Code
# generation could sit beside the Spyder one. Candidate 3 is silent when it misses:
# resolution simply falls through to candidate 4, "whatever this interpreter already
# has", and the ledger then cites a package nobody named.
_REPO_STAGING = (Path("ProkonForIDE") / "ProkonSpyderInstaller"
                 / "build" / "staging" / "python")


def _repo_root():
    """The Prokon.CLI checkout this file lives in: <repo>/Documentation/Prokon-5.4/examples/_tools."""
    return Path(__file__).resolve().parents[4]


def _package_dir(requested):
    """The folder to put on sys.path, or None to use an already-installed package."""
    if requested:
        return Path(requested).resolve(), "--package-dir"

    from_environment = os.environ.get("PROKON_EXAMPLES_PACKAGE_DIR")
    if from_environment:
        return Path(from_environment).resolve(), "PROKON_EXAMPLES_PACKAGE_DIR"

    staged = _repo_root() / _REPO_STAGING
    if (staged / "prokon" / "v5" / "__init__.py").is_file():
        return staged.resolve(), "installer build output"

    return None, "already installed in this interpreter"


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True, description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package-dir", default=None)
    parser.add_argument("--engine-home", default=None)
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--show-target", action="store_true")
    parser.add_argument("script", type=Path)
    parser.add_argument("script_args", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()

    script = arguments.script.resolve()
    if not script.is_file():
        print(f"example script not found: {script}", file=sys.stderr)
        return 2

    package_dir, why = _package_dir(arguments.package_dir)
    if package_dir is not None:
        if not (package_dir / "prokon" / "v5" / "__init__.py").is_file():
            print(f"no `prokon.v5` package in {package_dir} ({why})", file=sys.stderr)
            return 2
        sys.path.insert(0, str(package_dir))

    if arguments.engine_home:
        # Absolute, because the package refuses a relative one - and it is
        # right to: a relative engine home means a different engine from
        # every working directory, and this harness changes the working
        # directory by default.
        os.environ["PROKON_ENGINE_HOME"] = str(Path(arguments.engine_home).resolve())

    if arguments.show_target:
        # `import prokon.v5 as prokon` rather than `import prokon`: the engines live on the
        # VERSIONED module now, and the bare parent is a PEP 420 namespace package that
        # deliberately exposes nothing. The local name stays `prokon` so the rest of this
        # harness reads the way an example does.
        import prokon.v5 as prokon
        print(f"interpreter : {sys.executable}")
        print(f"python      : {sys.version.split()[0]}")
        print(f"package     : {package_dir or '(installed)'}  [{why}]")
        print(f"engines     : {len(prokon.engines)}")
        print(f"executable  : {prokon.beam_section.executable}")
        print("-" * 72)
        sys.stdout.flush()

    sys.argv = [str(script)] + [a for a in arguments.script_args if a != "--"]

    # A recipe that writes a spreadsheet or a chart writes it to the working
    # directory, which must not be the documentation tree.
    if arguments.in_place:
        runpy.run_path(str(script), run_name="__main__")
        return 0

    # NOT tempfile.TemporaryDirectory, and _scratch.py says why at length: the
    # engine this example spawns inherits the scratch folder as its working
    # directory, and Windows does not always release that handle before the next
    # statement deletes the tree. Measured at about one run in four, on an example
    # that had already printed correct results.
    with scratch_directory("prokon-example-"):
        runpy.run_path(str(script), run_name="__main__")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
