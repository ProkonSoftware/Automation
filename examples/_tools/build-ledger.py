# Internal verification harness - NOT part of the user documentation.
#
# Rebuilds the LEDGER TABLE inside VERIFICATION.md from the scripts' own
# headers, and rewrites the coverage matrix.
#
# Usage:
#   python _tools/build-ledger.py [--check]
#
#   --check   report what would change and exit non-zero, changing nothing.
#
# ⚠ WHY THIS IS GENERATED AND THE PROSE IS NOT. VERIFICATION.md's rule is
# that a script's header and the ledger MUST AGREE. Two hand-maintained
# copies of the same fact do not stay equal - so the ledger's table is
# derived from the headers, which makes disagreement impossible rather
# than merely discouraged. Everything above and below the table is
# hand-written and is left exactly as it is.
#
# The header is the single source of truth for: the feature list, the
# verified date, and what the script was checked against. It cannot
# express what the FILE does not know - so the prose sections carry the
# reasoning, and this tool never touches them.

import argparse
import re
import sys
from pathlib import Path

_EXAMPLES_ROOT = Path(__file__).resolve().parent.parent
_LEDGER = _EXAMPLES_ROOT / "VERIFICATION.md"
_TOOLS = "_tools"

_BEGIN = "<!-- BEGIN GENERATED LEDGER -->"
_END = "<!-- END GENERATED LEDGER -->"

_EXAMPLE = re.compile(r"^# Example:\s*(.+?)\s*$", re.M)
_FEATURE = re.compile(r"^# Feature:\s*(.*?)^# (?:Repeats|Verified):",
                      re.M | re.S)
_VERIFIED = re.compile(r"^# Verified:\s*(\S+)\s*[-–—]\s*"
                       r"(\S+)\s*[-–—]\s*(.+?)\s*$", re.M)

ENGINES = ("beam_section", "circular_column", "continuous_beam",
           "crack_widths", "general_column", "pad_footing", "pile_cap",
           "prestressed_concrete", "punching_shear", "rectangular_column",
           "rectangular_slab", "retaining_wall")

# ⚠ A FOLDER MISSING FROM THIS TUPLE IS SILENTLY DROPPED FROM THE COVERAGE
# MATRIX, not from the ledger. `scripts()` globs the whole tree, so a new
# folder's scripts get their ledger row either way - but `build()` counts an
# engine appearance only `if category in counts[engine]`, so the totals stay
# exactly as they were and nothing complains. Measured 2026-09-07 when
# `design-code-comparisons` was added: the row count went 107 -> 108 while
# `rectangular_column` stayed at 13 and `engine appearances` at 156.
CATEGORIES = (
    "quickstarts", 
    "going-deeper", 
    "recipes", 
    "workflows",
    "design-studies",
    "design-code-comparisons",
    "checking",
    "charts-and-plotting",
    "carbon-and-cost",
    "cb-reinforcement-study",
    "built-in-desktop-examples"
)


def read_header(path):
    """(title, features, verdict, date, checked against) from one script."""
    text = path.read_text(encoding="utf-8")

    title = _EXAMPLE.search(text)
    title = title.group(1) if title else "(no Example: line)"

    feature = _FEATURE.search(text)
    features = " ".join(
        line.lstrip("#").strip()
        for line in (feature.group(1) if feature else "").splitlines()
        if line.strip().lstrip("#").strip())

    verified = _VERIFIED.search(text)
    if verified:
        verdict, date, against = verified.groups()
    else:
        verdict, date, against = "MISSING", "", "(no Verified: line)"

    return title, features, verdict, date, against


def engines_in(features):
    """The engine wire names the Feature line declares."""
    return [engine for engine in ENGINES
            if re.search(rf"\b{engine}\b", features)]


def scripts():
    found = []
    for path in sorted(_EXAMPLES_ROOT.rglob("*.py")):
        if _TOOLS in path.relative_to(_EXAMPLES_ROOT).parts:
            continue
        found.append(path)
    return found


def assert_every_category_is_known():
    """Refuse a top-level folder this file does not know about.

    ⛔ THE COMMENT ABOVE PREDICTED THIS AND IT HAPPENED AGAIN. `design-code-comparisons`
    was dropped silently on 2026-09-07; `cb-reinforcement-study` was dropped silently on
    2026-09-18, and the run that should have caught it printed "coverage spread 0" over a
    matrix missing two continuous_beam scripts.

    ⚠ AND --check COULD NEVER HAVE CAUGHT EITHER. It rebuilds the table with this same
    tuple and compares the result with the file, so both sides share the blind spot and
    agree - a check and the thing it checks, agreeing for the wrong reason. The only thing
    that can see a missing category is a comparison against the TREE, which is this.
    """
    present = sorted({path.relative_to(_EXAMPLES_ROOT).parts[0]
                      for path in _EXAMPLES_ROOT.rglob("*.py")
                      if _TOOLS not in path.relative_to(_EXAMPLES_ROOT).parts})

    unknown = [name for name in present if name not in CATEGORIES]
    if unknown:
        raise SystemExit(
            "these example folders are not in CATEGORIES, so their scripts would get ledger "
            "rows and be dropped from the coverage matrix: {0}\n"
            "Add them to CATEGORIES in {1} and regenerate.".format(
                ", ".join(unknown), __file__))


def build():
    """The generated block, as a string.

    The category check runs first, before a single row is counted: a folder nobody has
    classified would otherwise be silently absent from the matrix rather than refused.
    """
    assert_every_category_is_known()

    rows = []
    counts = {engine: {category: 0 for category in CATEGORIES}
              for engine in ENGINES}

    for path in scripts():
        relative = path.relative_to(_EXAMPLES_ROOT).as_posix()
        category = path.relative_to(_EXAMPLES_ROOT).parts[0]
        title, features, verdict, date, against = read_header(path)

        for engine in engines_in(features):
            if category in counts[engine]:
                counts[engine][category] += 1

        # A pipe inside a cell would break the table.
        cell = lambda text: text.replace("|", "/")
        rows.append(
            f"| `{relative}` | {cell(title)} | {cell(features)} | "
            f"**{verdict}** | {date} | {cell(against)} |")

    lines = [_BEGIN, "",
             "<!-- Generated by _tools/build-ledger.py from the scripts'",
             "     own headers. Do not hand-edit this block: run the tool.",
             "     The prose outside it is hand-written and never touched. -->",
             "",
             f"**{len(rows)} example scripts.** Every row below is read out of "
             "that script's",
             "own header, so the ledger cannot disagree with the file.",
             "",
             "| Script | Example | Feature | Verified | Date | Checked against |",
             "|---|---|---|---|---|---|"]
    lines.extend(rows)

    # The coverage matrix, which is the answer to "is any engine
    # under-documented".
    totals = {engine: sum(counts[engine].values()) for engine in ENGINES}
    lines += ["", "### Coverage by engine", "",
              "One row per engine, one column per category. The point of the",
              "table is the TOTAL column: no engine is better documented",
              "than another.", "",
              "| Engine | " + " | ".join(CATEGORIES) + " | total |",
              "|---" * (len(CATEGORIES) + 2) + "|"]
    for engine in ENGINES:
        cells = " | ".join(str(counts[engine][category])
                           for category in CATEGORIES)
        lines.append(f"| `{engine}` | {cells} | **{totals[engine]}** |")
    per_category = " | ".join(
        str(sum(counts[engine][category] for engine in ENGINES))
        for category in CATEGORIES)
    lines.append(f"| **engine appearances** | {per_category} | "
                 f"**{sum(totals.values())}** |")

    spread = max(totals.values()) - min(totals.values())
    lines += ["",
              f"Minimum {min(totals.values())}, maximum "
              f"{max(totals.values())}, spread {spread}.",
              "", _END]
    return "\n".join(lines), spread


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()

    block, spread = build()
    text = _LEDGER.read_text(encoding="utf-8")

    if _BEGIN not in text or _END not in text:
        print(f"VERIFICATION.md has no {_BEGIN} / {_END} markers - add them "
              f"where the generated table belongs.", file=sys.stderr)
        return 2

    start = text.index(_BEGIN)
    end = text.index(_END) + len(_END)
    updated = text[:start] + block + text[end:]

    if arguments.check:
        if updated == text:
            print(f"VERIFICATION.md is up to date "
                  f"({len(scripts())} scripts, coverage spread {spread}).")
            return 0
        print("VERIFICATION.md is STALE - run _tools/build-ledger.py",
              file=sys.stderr)
        return 1

    if updated == text:
        print(f"VERIFICATION.md already up to date "
              f"({len(scripts())} scripts).")
        return 0

    with open(_LEDGER, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)
    print(f"VERIFICATION.md rewritten: {len(scripts())} scripts, "
          f"coverage spread {spread}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
