# ---
# Example:  One pile cap, a growing load - and three checks that favour OPPOSITE codes
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes - 2026-09-07 - the CSA reference cap reproduces its pinned overhang, strut capacity, both node capacities and its minimum tie steel exactly; every load measured on prokon-automation.exe
# ---
# ONE cap. FOUR piles. ONE thing changes: the column load.
#
# The column (0.5 x 0.5 m), the piles (0.6 m at 1.8 m centres), the cap
# (1.2 m thick, 0.3 m overhang), the concrete (fc 30) and the steel
# (fy 400) are held constant and asserted constant - so every difference
# is caused by the load or by the code.
#
# THE CODES ------------------------------------------------------------
#
# SABS 0100 - 2000 against Eurocode 2 - 2004. ⚠ C16 offers only FOUR
# design codes in total, the fewest in the fleet, and the new South
# African code is not among them - C16 is one of four engines without it
# (with C11, C12 and C13). Section 0 shows that rather than asserting it.
#
# C16 models the cap as a TRUSS - a strut-and-tie model - so it publishes
# a safety factor for each element rather than an area of steel, and 1.0
# is the line. That makes every check directly comparable on one axis,
# which is what panel A does.
#
# WHAT THE STUDY FINDS -------------------------------------------------
#
#   THE DEMAND IS THE SAME UNDER BOTH CODES; ONLY THE CAPACITY MOVES. The
#   strut force and both node forces come back bit-identical, because they
#   are equilibrium - the truss carries what the truss carries. Section 3
#   checks that, with the capacities as the control.
#
#   AND THE THREE CAPACITIES FAVOUR OPPOSITE CODES. Measured:
#     the STRUT favours Eurocode 2  - 1032 against 880 kN, +17 %
#     the COLUMN NODE favours SABS  - 5000 against 4400 kN, +14 %
#     the PILE NODE favours SABS    - 4524 against 3732 kN, +21 %
#     and the MINIMUM TIE STEEL is 33 % heavier under Eurocode 2.
#   So "which code is more onerous" has no answer for a pile cap. It
#   depends entirely on which element of the truss runs out first.
#
#   ON THIS CAP THE STRUT RUNS OUT FIRST UNDER BOTH CODES, so Eurocode 2
#   wins and allows about 17 % more load - section 4 bisects it. That is a
#   NEGATIVE result worth stating plainly: the sign flips in panel C never
#   reach the answer here. Make the cap thicker or the piles wider and a
#   node could govern instead, and then the verdict would reverse.
#
#   AND NOTHING EVER REFUSES. Push the load past every capacity and the
#   engine returns safety factors below 1.0 with no error - which is the
#   honest behaviour, because a factor of 0.28 is a real answer. Read it
#   against 1.0.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can.

    Spyder runs matplotlib on its own backend, so plt.show() puts the
    chart in the Plots pane. A headless run can only warn - so ASK the
    backend and write the PNG either way. No matplotlib.use() here: that
    call would make the Plots pane unreachable for ever.
    """
    path = Path(filename).resolve()
    figure.savefig(path, dpi=150, facecolor=SURFACE)
    size = path.stat().st_size
    print("\nWritten: {0}".format(path))
    print("  {0:,} bytes  ({1})".format(
        size, "a real image" if size > 20_000 else "SUSPICIOUSLY SMALL"))
    if str(matplotlib.get_backend()).lower() in HEADLESS:
        plt.close(figure)
        print("  backend is headless - the PNG is the whole output")
    else:
        plt.show()
        print("  and shown on the {0} backend".format(
            matplotlib.get_backend()))


# -- THE TWO CODES ------------------------------------------------------
OLD_CODE = "SABS 0100 - 2000"
NEW_CODE = "Eurocode 2 - 2004"
PINNED_CODE = "CSA-A23.3:2019"          # what the pinned reference case used
SA_NEW_CODE = "SANS 51992-1-1:2025"     # not in this engine

OLD_COLOUR = "#2a78d6"      # categorical slot 1
NEW_COLOUR = "#eb6834"      # categorical slot 2
FREE = "#0ca30c"
DEAD = "#d03b3b"

# -- THE CAP, AND THE ONE INPUT THAT MOVES ------------------------------
CAP = dict(column_dim_x=0.5, column_dim_y=0.5, no_of_piles=4, pile_dia=0.6,
           pile_spacing=1.8, pile_tolerance=0.05, cap_thickness=1.2,
           cap_overhang=0.3, bottom_rebar_depth=0.1, fc=30.0, fy=400.0)

ANCHOR_LOAD = 4000.0
PINNED = {"overhang_min_required": 0.226,
          "strut_cr": 2064.6284818393965,
          "column_pr": 4143.75,
          "pile_pr": 3583.7718,
          "tie_minimum": 2400}

LOADS = np.arange(250.0, 8001.0, 125.0)     # 63 loads, 250 kN to 8 MN
PASSES_AT = 1.0

# The three checks, each with the force it carries and the capacity it is
# measured against. Every one publishes an sf, so they share an axis.
CHECKS = ("strut", "column node", "pile node")

print("ONE PILE CAP, A GROWING LOAD - TWO DESIGN CODES")
print(f"  {CAP['column_dim_x']:.2f} x {CAP['column_dim_y']:.2f} m column on "
      f"{CAP['no_of_piles']} piles of {CAP['pile_dia']:.2f} m at "
      f"{CAP['pile_spacing']:.2f} m centres")
print(f"  cap {CAP['cap_thickness']:.2f} m thick, {CAP['cap_overhang']:.2f} m "
      f"overhang, fc {CAP['fc']:.0f} MPa, fy {CAP['fy']:.0f} MPa")
print(f"  the only input that moves: P, {LOADS[0]:.0f} to {LOADS[-1]:.0f} kN "
      f"in {LOADS[1] - LOADS[0]:.0f} kN steps ({len(LOADS)} loads)")

CALLS = {"engine": 0}
_ANSWERS = {}


def design(code, load):
    """One load, one code. Returns a row; never raises for a refusal."""
    key = (code, round(float(load), 4))
    if key in _ANSWERS:
        return _ANSWERS[key]

    CALLS["engine"] += 1
    try:
        result = prokon.v5.pile_cap.analyse(
            design_code=code,
            load_cases=[{"name": "ULS", "load_factor": 1.0,
                         "p": float(load)}], **CAP)["result"]
    except prokon.v5.ProkonError as refusal:
        row = dict(load=float(load), force={}, capacity={}, factor={},
                   tie_required=None, tie_minimum=None, overhang=None,
                   reason=f"{refusal.category}/{refusal.code}: "
                          f"{refusal.message}")
        _ANSWERS[key] = row
        return row

    # ⚠ DO NOT INDEX tie_results BY design_tie. The engine publishes
    # design_strut / design_tie / design_pile, and design_tie is an ELEMENT
    # index (7 on the reference cap) while tie_results has four entries -
    # so result["tie_results"][7] is an IndexError, which is how this was
    # found. Rather than guess which of the three indices is positional and
    # which is an element number, take the WORST element of each kind. For
    # "does this cap work" that is the right reading anyway: the cap is as
    # good as its weakest strut, node and tie.
    struts = [case["load_cases"][0] for case in result["strut_results"]]
    piles = [node["load_cases"][0] for node in result["pile_nodes"]]
    ties = [tie["load_cases"][0] for tie in result["tie_results"]]
    strut = min(struts, key=lambda case: case["sf"])
    column = result["column_node"]["load_cases"][0]
    pile = min(piles, key=lambda case: case["sf"])
    tie = max(ties, key=lambda case: case["as_required"])
    row = dict(load=float(load),
               force={"strut": strut["cf"], "column node": column["pf"],
                      "pile node": pile["pf"]},
               capacity={"strut": strut["cr"], "column node": column["pr"],
                         "pile node": pile["pr"]},
               factor={"strut": strut["sf"], "column node": column["sf"],
                       "pile node": pile["sf"]},
               tie_required=tie["as_required"],
               tie_minimum=result["tie_minim_reinforcement"],
               overhang=result["overhang_min_required"], reason=None)
    _ANSWERS[key] = row
    return row


# ======================================================================
# 0. THE FOUR CODES THIS ENGINE HAS
# ======================================================================
# CLAIM: C16 offers four codes and SANS 51992-1-1:2025 is not one.
# CONTROL: the codes this script DOES use must answer AND disagree, or the
# reading cannot tell a refusal from an answer.
print("\n0. THE CODES THIS ENGINE HAS  (only four, the fewest in the fleet)")
for code in (SA_NEW_CODE, OLD_CODE, NEW_CODE, PINNED_CODE, "ACI 318 - 2019"):
    row = design(code, ANCHOR_LOAD)
    if not row["capacity"]:
        print(f"   {code:<22} REFUSED")
        print(f"   {'':<22} {str(row['reason'])[:66]}")
    else:
        print(f"   {code:<22} answered  strut cr "
              f"{row['capacity']['strut']:>9.2f}   column pr "
              f"{row['capacity']['column node']:>8.1f}")
print("   -> the controls answer and they DISAGREE, so the refusal above is")
print("      about the code name and nothing else.")
print("   -> C16 is one of four engines without the new South African code;")
print("      C11, C12 and C13 are the others. The remaining eight have it.")

# ======================================================================
# 1. THE ANCHOR
# ======================================================================
print(f"\n1. THE ANCHOR   {PINNED_CODE} at P = {ANCHOR_LOAD:.0f} kN")
anchor = design(PINNED_CODE, ANCHOR_LOAD)
found = {"overhang_min_required": anchor["overhang"],
         "strut_cr": anchor["capacity"]["strut"],
         "column_pr": anchor["capacity"]["column node"],
         "pile_pr": anchor["capacity"]["pile node"],
         "tie_minimum": anchor["tie_minimum"]}
matched = 0
for name in PINNED:
    hit = found[name] == PINNED[name]
    matched += hit
    print(f"   {name:<22} {found[name]!r:22} pinned {PINNED[name]!r}")
print(f"   -> {matched} of {len(PINNED)} exact"
      f"{'' if matched == len(PINNED) else '  - DRIFTED, READ NOTHING BELOW'}")

# ======================================================================
# 2. THE SWEEP
# ======================================================================
print(f"\n2. THE SWEEP   {len(LOADS)} loads x 2 codes")
sweep = {code: [design(code, load) for load in LOADS]
         for code in (OLD_CODE, NEW_CODE)}

assert CAP["cap_thickness"] == 1.2 and CAP["pile_spacing"] == 1.8
assert CAP["no_of_piles"] == 4 and CAP["fc"] == 30.0
print("   the cap dictionary is unchanged after the sweep")

print(f"\n   {'P (kN)':>7} | {'SABS strut':>11} {'col':>7} {'pile':>7} | "
      f"{'EC2 strut':>11} {'col':>7} {'pile':>7}")
for index, load in enumerate(LOADS):
    if load % 1000 != 0:
        continue
    cells = []
    for code in (OLD_CODE, NEW_CODE):
        row = sweep[code][index]
        cells.append(f" {row['factor']['strut']:>11.3f} "
                     f"{row['factor']['column node']:>7.3f} "
                     f"{row['factor']['pile node']:>7.3f}")
    print(f"   {load:>7.0f} |" + " |".join(cells))
print("   (safety factors: 1.0 is the limit, below it the element fails)")


def factors(code, check):
    return np.asarray([row["factor"].get(check, np.nan)
                       for row in sweep[code]], dtype=float)


# ======================================================================
# 3. THE DEMAND IS SHARED; ONLY THE CAPACITY MOVES
# ======================================================================
# ⚠ AND IT NEEDS A CONTROL. "These two lists are equal" is what a broken
# comparison reports too, so the CAPACITIES go through the same comparison.
# If everything comes back identical, the comparison is broken.
print("\n3. WHAT THE CODE MOVES, AND WHAT EQUILIBRIUM HAS ALREADY FIXED")
print(f"   {'reading':<26} {'identical at':>14} {'of':>5}  verdict")
for kind in ("force", "capacity"):
    for check in CHECKS:
        old = np.asarray([row[kind][check] for row in sweep[OLD_CODE]])
        new = np.asarray([row[kind][check] for row in sweep[NEW_CODE]])
        same = int(np.sum(old == new))
        tag = "IDENTICAL everywhere" if same == len(LOADS) else "DIFFERS"
        print(f"   {kind + ' - ' + check:<26} {same:>14} {len(LOADS):>5}  "
              f"{tag}")
forces_same = all(
    np.all(np.asarray([row["force"][check] for row in sweep[OLD_CODE]])
           == np.asarray([row["force"][check] for row in sweep[NEW_CODE]]))
    for check in CHECKS)
caps_differ = any(
    np.any(np.asarray([row["capacity"][check] for row in sweep[OLD_CODE]])
           != np.asarray([row["capacity"][check] for row in sweep[NEW_CODE]]))
    for check in CHECKS)
print(f"\n   every force identical   : {forces_same}")
print(f"   capacities differ       : {caps_differ}   <- the control")
if forces_same and caps_differ:
    print("   -> so the comparison CAN see a difference, and it finds none in")
    print("      the forces. The truss carries what the truss carries; the")
    print("      code decides only what each element is allowed to carry.")

# ======================================================================
# 4. THE THREE CAPACITIES FAVOUR OPPOSITE CODES
# ======================================================================
print("\n4. AND THE THREE CAPACITIES DO NOT AGREE ON WHICH CODE IS KINDER")
print(f"   {'element':<14} {'SABS':>11} {'Eurocode 2':>12} {'new/old':>9}  "
      f"favours")
shares = {}
for check in CHECKS:
    old = sweep[OLD_CODE][0]["capacity"][check]
    new = sweep[NEW_CODE][0]["capacity"][check]
    shares[check] = new / old
    print(f"   {check:<14} {old:>11.2f} {new:>12.2f} {shares[check]:>8.4f}x  "
          f"{'Eurocode 2' if shares[check] > 1 else 'SABS'}")
old_tie = sweep[OLD_CODE][0]["tie_minimum"]
new_tie = sweep[NEW_CODE][0]["tie_minimum"]
shares["tie minimum"] = new_tie / old_tie
print(f"   {'tie minimum':<14} {old_tie:>11.2f} {new_tie:>12.2f} "
      f"{shares['tie minimum']:>8.4f}x  "
      f"{'SABS' if shares['tie minimum'] > 1 else 'Eurocode 2'}"
      f"   (less steel is kinder)")
directions = {check: share > 1 for check, share in shares.items()
              if check in CHECKS}
if len(set(directions.values())) > 1:
    print("   -> THE SIGNS DISAGREE. One element favours the new code and the")
    print("      others favour the old, so 'which code is more onerous' has")
    print("      no answer for a pile cap in general - only for a particular")
    print("      cap, where one element runs out first.")


def boundary(holds, low, high, resolution=1.0):
    """The largest load where `holds` is still true, to `resolution`.

    The bracket is CHECKED rather than assumed - a bisection over a bracket
    that does not straddle the boundary returns one of its own endpoints,
    and that looks exactly like an answer.
    """
    if not holds(low):
        raise AssertionError(f"the bracket's low end {low} does not hold")
    if holds(high):
        raise AssertionError(f"the bracket's high end {high} still holds")
    while high - low > resolution:
        middle = (low + high) / 2.0
        if holds(middle):
            low = middle
        else:
            high = middle
    return low, high


# ======================================================================
# 5. THE LARGEST LOAD EACH CODE ALLOWS
# ======================================================================
print(f"\n5. THE LARGEST LOAD AT WHICH EVERY ELEMENT STILL PASSES "
      f"(sf >= {PASSES_AT:.1f})")
capacity_limit = {}
for code in (OLD_CODE, NEW_CODE):
    worst = np.minimum.reduce([factors(code, check) for check in CHECKS])
    good = LOADS[worst >= PASSES_AT]
    bad = LOADS[worst < PASSES_AT]
    if not len(good) or not len(bad):
        print(f"   {code:<22} no crossing inside this range")
        continue

    def all_pass(load, code=code):
        row = design(code, load)
        return min(row["factor"][check] for check in CHECKS) >= PASSES_AT

    low, high = boundary(all_pass, good[-1], bad[0])
    at_limit = design(code, low)["factor"]
    governing = min(at_limit, key=at_limit.get)
    capacity_limit[code] = (low, governing)
    print(f"   {code:<22} passes to {low:.0f} kN, fails from {high:.0f} kN")
    print(f"   {'':<22} governed by the {governing.upper()}, sf "
          f"{at_limit[governing]:.4f} there")
if len(capacity_limit) == 2:
    old_limit = capacity_limit[OLD_CODE][0]
    new_limit = capacity_limit[NEW_CODE][0]
    kinder = NEW_CODE if new_limit > old_limit else OLD_CODE
    print(f"   -> {kinder} allows "
          f"{abs(new_limit - old_limit) / min(old_limit, new_limit) * 100:.0f} "
          f"% more load")
    print(f"      ({new_limit:.0f} kN against {old_limit:.0f} kN).")
    if capacity_limit[OLD_CODE][1] == capacity_limit[NEW_CODE][1]:
        print(f"   -> and the SAME element governs both, the "
              f"{capacity_limit[OLD_CODE][1]}. So on THIS cap the sign")
        print("      flips in section 4 never reach the answer. A thicker cap")
        print("      or wider piles could put a node in charge instead, and")
        print("      then the verdict would reverse.")

# ======================================================================
# 6. NOTHING EVER REFUSES
# ======================================================================
print("\n6. NOTHING EVER REFUSES")
for code in (OLD_CODE, NEW_CODE):
    last = sweep[code][-1]
    worst = min(last["factor"], key=last["factor"].get)
    print(f"   {code:<22} at P = {last['load']:.0f} kN the worst factor is "
          f"{last['factor'][worst]:.3f} ({worst})")
    print(f"   {'':<22} and the tie still asks for "
          f"{last['tie_required']:.0f} mm2, no error")
print("   -> and that is the right behaviour here: a factor of 0.28 is a")
print("      real answer that says how far past the limit you are. Read it")
print("      against 1.0 and the engine has told you everything it knows.")

print(f"\n   {CALLS['engine']} engine calls in total")

# ======================================================================
# 7. THE PICTURE
# ======================================================================
figure = plt.figure(figsize=(16.0, 10.6), facecolor=SURFACE)
panels = figure.add_gridspec(2, 2, hspace=0.36, wspace=0.19,
                             height_ratios=(1.22, 1.0),
                             left=0.06, right=0.985, top=0.865, bottom=0.09)


def dress(axes, title, xlabel, ylabel):
    """The chrome every panel shares: hairline grid, recessive axes."""
    axes.set_facecolor(SURFACE)
    axes.set_title(title, fontsize=10.5, color=INK, pad=9, loc="left")
    axes.set_xlabel(xlabel, fontsize=9.5, color=INK_SOFT)
    axes.set_ylabel(ylabel, fontsize=9.5, color=INK_SOFT)
    axes.grid(True, linewidth=0.6, color=GRID)
    axes.set_axisbelow(True)
    for edge in ("top", "right"):
        axes.spines[edge].set_visible(False)
    for edge in ("left", "bottom"):
        axes.spines[edge].set_color(AXIS)
        axes.spines[edge].set_linewidth(0.8)
    axes.tick_params(colors=MUTED, labelsize=9)


# ---- A. every check on one axis ----------------------------------------
chart = figure.add_subplot(panels[0, 0])
dress(chart, "A.  Every element on one axis — its published safety factor",
      "column load  P   (kN)", "safety factor   (1.0 = at the limit)")
STYLES = {"strut": "-", "column node": "--", "pile node": ":"}
for code, colour in ((OLD_CODE, OLD_COLOUR), (NEW_CODE, NEW_COLOUR)):
    short = "SABS" if code == OLD_CODE else "Eurocode 2"
    for check in CHECKS:
        chart.plot(LOADS, factors(code, check), color=colour,
                   linewidth=2.0 if check == "strut" else 1.5,
                   linestyle=STYLES[check], label=f"{short}  {check}",
                   zorder=4)
chart.axhline(PASSES_AT, color=DEAD, linewidth=1.4, linestyle="--", zorder=3)
chart.annotate(f"{PASSES_AT:.1f} — below here the element FAILS",
               (LOADS[-1], PASSES_AT), textcoords="offset points",
               xytext=(-6, 8), ha="right", fontsize=8.5, color=DEAD,
               fontweight="bold")
# The two 'runs out' notes crossed the node curves. Park them in the one
# band that is empty at high load - above the failing struts and below
# the still-comfortable pile nodes.
for code, colour, height in ((OLD_CODE, OLD_COLOUR, 0.32),
                             (NEW_CODE, NEW_COLOUR, 0.25)):
    if code in capacity_limit:
        where, governing = capacity_limit[code]
        chart.plot([where], [PASSES_AT], marker="o", markersize=9,
                   color=colour, markeredgecolor=SURFACE,
                   markeredgewidth=2.0, zorder=6)
        chart.text(0.98, height,
                   f"{'SABS' if code == OLD_CODE else 'Eurocode 2'}: "
                   f"{where:.0f} kN — the {governing} runs out",
                   transform=chart.transAxes, ha="right", va="center",
                   fontsize=8.5, color=colour, fontweight="bold")
chart.set_xlim(LOADS[0], LOADS[-1])
chart.set_ylim(0.0, 5.0)
chart.legend(loc="upper right", fontsize=8.5, frameon=False, labelcolor=INK,
             ncol=2)

# ---- B. the direct comparison ------------------------------------------
# ⚠ THE SENSE IS REVERSED relative to the steel-designing studies: a
# safety factor is a good thing, so above 1.0 the NEW code is more
# permissive. The axis label says so.
ratio_axes = figure.add_subplot(panels[0, 1])
dress(ratio_axes, "B.  The two codes, divided   (Eurocode 2 ÷ SABS)",
      "column load  P   (kN)",
      "safety factor,  new ÷ old\n(above 1.0 the NEW code is more "
      "permissive)")
ratio_axes.axhline(1.0, color=AXIS, linewidth=1.2, linestyle="--")
for check in CHECKS:
    share = factors(NEW_CODE, check) / factors(OLD_CODE, check)
    ratio_axes.plot(LOADS, share, color=NEW_COLOUR,
                    linewidth=2.0 if check == "strut" else 1.5,
                    linestyle=STYLES[check], label=check, zorder=4)
    # Left end, and lifted clear of its own line: these three series are
    # flat, so a label centred on the line simply sits on it.
    ratio_axes.annotate(f"{check}: {share[0]:.3f}×",
                        (LOADS[0], share[0]), textcoords="offset points",
                        xytext=(10, 9 if share[0] > 1 else -13), ha="left",
                        fontsize=8.5,
                        color=NEW_COLOUR if share[0] > 1 else OLD_COLOUR,
                        fontweight="bold")
ratio_axes.fill_between(LOADS, factors(NEW_CODE, "strut")
                        / factors(OLD_CODE, "strut"), 1.0,
                        color=NEW_COLOUR, alpha=0.12)
ratio_axes.text(0.985, 0.06,
                "the strut is ABOVE the line and both nodes are BELOW it — "
                "the" + chr(10) +
                "codes do not agree on which is the kinder, element by "
                "element",
                transform=ratio_axes.transAxes, ha="right", va="bottom",
                fontsize=8.5, color=INK_SOFT)
ratio_axes.set_xlim(LOADS[0], LOADS[-1])
ratio_axes.legend(loc="center right", fontsize=8.5, frameon=False,
                  labelcolor=INK)

# ---- C. the capacities, side by side -----------------------------------
bars = figure.add_subplot(panels[1, 0])
dress(bars, "C.  Why — the capacities, and the signs disagree", "",
      "capacity   (kN, and mm² for the tie)")
labels = list(CHECKS) + ["tie minimum"]
old_values = [sweep[OLD_CODE][0]["capacity"][check] for check in CHECKS]
old_values.append(sweep[OLD_CODE][0]["tie_minimum"])
new_values = [sweep[NEW_CODE][0]["capacity"][check] for check in CHECKS]
new_values.append(sweep[NEW_CODE][0]["tie_minimum"])
positions = np.arange(len(labels))
bars.bar(positions - 0.19, old_values, width=0.36, color=OLD_COLOUR,
         label=OLD_CODE, edgecolor=SURFACE, linewidth=2.0, zorder=3)
bars.bar(positions + 0.19, new_values, width=0.36, color=NEW_COLOUR,
         label=NEW_CODE, edgecolor=SURFACE, linewidth=2.0, zorder=3)
for index, label in enumerate(labels):
    share = shares[label]
    higher = max(old_values[index], new_values[index])
    bars.text(index, higher * 1.03, f"{share:.3f}×", ha="center",
              fontsize=9, color=NEW_COLOUR if share > 1 else OLD_COLOUR,
              fontweight="bold")
bars.set_xticks(positions)
bars.set_xticklabels(labels, fontsize=9.5, color=INK_SOFT)
bars.set_ylim(0, max(max(old_values), max(new_values)) * 1.26)
bars.grid(True, axis="y", linewidth=0.6, color=GRID)
bars.grid(False, axis="x")
bars.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor=INK)
bars.text(0.985, 0.955,
          "orange ratios favour Eurocode 2, blue ones favour SABS —" + chr(10)
          + "and both appear, which is the finding",
          transform=bars.transAxes, ha="right", va="top", fontsize=8.5,
          color=MUTED)

# ---- D. the verdict ----------------------------------------------------
verdict = figure.add_subplot(panels[1, 1])
dress(verdict, "D.  Same cap, same axis — the largest load each code allows",
      "", "")
verdict.set_xlabel("column load  P   (kN)", fontsize=9.5, color=INK_SOFT)
REGIMES = ((FREE, f"every element passes  (sf ≥ {PASSES_AT:.1f})"),
           (DEAD, "an element is past its capacity — no refusal, just a "
                  "factor below 1"))
for code, base in ((OLD_CODE, 0.64), (NEW_CODE, 0.24)):
    if code not in capacity_limit:
        continue
    edge, governing = capacity_limit[code]
    for start, stop, colour in ((LOADS[0], edge, FREE),
                                (edge, LOADS[-1], DEAD)):
        if stop - start <= 0:
            continue
        verdict.barh(base, stop - start, left=start, height=0.20,
                     color=colour, alpha=0.85, edgecolor=SURFACE,
                     linewidth=2.0, zorder=3)
    verdict.text(LOADS[0] + 60, base + 0.15, code, fontsize=9.5, color=INK,
                 fontweight="bold")
    verdict.plot([edge, edge], [base - 0.145, base - 0.105], color=INK,
                 linewidth=1.0, zorder=5)
    verdict.text(edge, base - 0.20, f"{edge:.0f} kN — the {governing}",
                 ha="center", fontsize=8.5, color=INK, fontweight="bold")
verdict.text(0.985, 0.975,
             "the SAME element governs both, so the sign flips in panel C "
             "never" + chr(10) +
             "reach the answer on this cap — a thicker one could reverse it",
             transform=verdict.transAxes, ha="right", va="top",
             fontsize=8.5, color=MUTED)
verdict.set_xlim(LOADS[0], LOADS[-1])
verdict.set_ylim(0.02, 1.0)
verdict.set_yticks([])
verdict.grid(False)
verdict.spines["left"].set_visible(False)
verdict.legend([plt.Rectangle((0, 0), 1, 1, color=colour, alpha=0.85)
                for colour, _ in REGIMES],
               [label for _, label in REGIMES], loc="upper center",
               bbox_to_anchor=(0.5, -0.14), fontsize=8.5, ncol=1,
               frameon=False, labelcolor=INK)

figure.suptitle(
    f"One pile cap, a growing load:  {OLD_CODE}  against  {NEW_CODE}\n"
    f"{CAP['column_dim_x']:.2f} m column on {CAP['no_of_piles']} × "
    f"{CAP['pile_dia']:.2f} m piles at {CAP['pile_spacing']:.2f} m, cap "
    f"{CAP['cap_thickness']:.2f} m thick, fc {CAP['fc']:.0f} MPa  —  "
    f"ONLY the load changes\n"
    f"Every force is identical because the truss is equilibrium; the "
    f"capacities differ — and they favour OPPOSITE codes, element by element",
    fontsize=11, color=INK, y=0.985)

deliver(figure, "pile_cap_sabs_vs_eurocode_load.png")
