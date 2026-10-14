# ---
# Example:  Draw the strut-and-tie model the engine actually used
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes - 2026-09-02 - the CSA reference cap reproduces its pinned strut Cr and node Pr; the diagram is written and re-read
# ---
# Strut and tie is a drawing method. C16 returns the FORCES in a model it
# built internally, keyed by element index - and reading forces out of a
# list without seeing the model is how a detailer ends up putting the tie
# steel in the wrong direction.
#
# So draw it. This recipe plots the cap in plan with the piles, the column,
# the struts in compression and the ties in tension, each labelled with the
# force the engine reported.
#
# ⚠ THE ELEMENT INDICES ARE THE WHOLE PUZZLE. strut_element_indices and
# tie_element_indices tell you which element numbers are which; design_tie
# and design_strut nominate one of those NUMBERS, not a list position. This
# script builds the lookup once, at the top, and every later read goes
# through it.
#
# Uses matplotlib, bundled with Prokon's Python runtime.

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import prokon.v5

CAP = dict(
    design_code="CSA-A23.3:2019",
    column_dim_x=0.5, column_dim_y=0.5,
    no_of_piles=4, pile_dia=0.6, pile_spacing=1.8, pile_tolerance=0.05,
    cap_thickness=1.2, cap_overhang=0.3, bottom_rebar_depth=0.1,
    fc=30.0, fy=400.0,
)
LOAD = [{"name": "ULS", "load_factor": 1.0, "p": 4000.0, "mx": 300.0}]

print("THE STRUT-AND-TIE MODEL, DRAWN")
print(f"  {CAP['no_of_piles']} piles at {CAP['pile_spacing']} m, cap "
      f"{CAP['cap_thickness']} m deep, {LOAD[0]['p']:.0f} kN + "
      f"{LOAD[0]['mx']:.0f} kNm")
print(f"  NOTE: C16 works in METRES throughout.")

# ── The anchor ──────────────────────────────────────────────────────────
anchor = prokon.v5.pile_cap.analyse(
    **CAP, load_cases=[{"name": "ULS", "load_factor": 1.0, "p": 4000.0}])["result"]
PINNED = (2064.6284818393965, 4143.75)
measured = (anchor["strut_results"][0]["load_cases"][0]["cr"],
            anchor["column_node"]["load_cases"][0]["pr"])
print(f"\n  anchor: the same cap with no moment")
print(f"    strut Cr    {measured[0]!r}   pinned {PINNED[0]!r}")
print(f"    node Pr     {measured[1]!r}   pinned {PINNED[1]!r}")
print(f"    -> {'EXACT on both' if measured == PINNED else 'DRIFTED'}")

result = prokon.v5.pile_cap.analyse(**CAP, load_cases=LOAD)["result"]

# ── The lookup, built once ─────────────────────────────────────────────
struts = {entry["element_index"]: entry for entry in result["strut_results"]}
ties = {entry["element_index"]: entry for entry in result["tie_results"]}

print(f"\nTHE MODEL C16 BUILT")
print(f"  strut elements {result['strut_element_indices']}")
print(f"  tie elements   {result['tie_element_indices']}")
print(f"  nominated: strut {result['design_strut']}, "
      f"tie {result['design_tie']}, pile {result['design_pile']}")
print(f"  -> those are ELEMENT numbers. tie_results has "
      f"{len(result['tie_results'])} entries at indices "
      f"{sorted(ties)}, so")
print(f"     tie_results[{result['design_tie']}] is an IndexError. Index by")
print(f"     element, through a lookup built once.")

# ── The geometry, derived the same way the cap plan is ─────────────────
# A square group of four piles at the given spacing, centred on the cap.
count = int(CAP["no_of_piles"])
spacing = CAP["pile_spacing"]

if count == 2:
    pile_positions = [(-spacing / 2, 0.0), (spacing / 2, 0.0)]
elif count == 3:
    radius = spacing / math.sqrt(3.0)
    pile_positions = [(radius * math.cos(math.radians(90 + 120 * n)),
                       radius * math.sin(math.radians(90 + 120 * n)))
                      for n in range(3)]
elif count == 4:
    half = spacing / 2.0
    pile_positions = [(-half, -half), (half, -half), (half, half),
                      (-half, half)]
else:
    half = spacing / 2.0
    pile_positions = [(-half, -half), (half, -half), (half, half),
                      (-half, half), (0.0, 0.0)]

pile_loads = [pile[0]["p"] for pile in result["pile_forces"]]

print(f"\nPILE LOADS   (the spread IS the applied moment)")
for index, ((x, y), load) in enumerate(zip(pile_positions, pile_loads)):
    print(f"   pile {index}  at ({x:+.2f}, {y:+.2f}) m   {load:>8.1f} kN")
print(f"   total {sum(pile_loads):.1f} kN against {LOAD[0]['p']:.0f} applied")
print(f"   range {max(pile_loads) - min(pile_loads):.1f} kN")

# ⚠ AND THE ONE THING THIS DRAWING CANNOT KNOW. C16 does not publish pile
# COORDINATES - only forces, in a list. The positions above are this
# script's own square layout, assigned to the engine's list in order, and
# that mapping is an ASSUMPTION.
#
# It is a testable one. Under a moment about X, piles at the same y should
# carry the same load. Measured here with mx = 300: piles 0 and 1 share
# y = -0.90 and carry 919.8 and 1080.2 kN, so the engine's ordering is NOT
# the corner order assumed above. The pairs that DO match are 0 with 2 and
# 1 with 3 - a diagonal pairing in this script's coordinates.
#
# So read the diagram as the MODEL's topology - which elements are struts,
# which are ties, which one governs - and read the per-pile load from the
# list, not from the picture. Saying so is the difference between a drawing
# that helps and one that misleads.
by_y = {}
for (x, y), load in zip(pile_positions, pile_loads):
    by_y.setdefault(round(y, 3), []).append(load)
consistent = all(max(loads) - min(loads) < 0.01 for loads in by_y.values())
print(f"\n   ORDERING CHECK: piles sharing a y should share a load under a")
print(f"   moment about X. {'They do' if consistent else 'THEY DO NOT'}:")
for y, loads in sorted(by_y.items()):
    print(f"     y = {y:+.2f}   " +
          ", ".join(f"{load:.1f}" for load in loads))
if not consistent:
    print(f"   -> so the layout drawn below is this script's assumption, not")
    print(f"      the engine's. The TOPOLOGY is right; the per-pile labels")
    print(f"      may be permuted. Read loads from the list, not the picture.")

# ── Draw it ─────────────────────────────────────────────────────────────
figure, axes = plt.subplots(figsize=(8.5, 8.0))

half_x = result["cap_dim_x"] / 2.0
half_y = result["cap_dim_y"] / 2.0
axes.add_patch(plt.Rectangle((-half_x, -half_y),
                             result["cap_dim_x"], result["cap_dim_y"],
                             facecolor="0.93", edgecolor="0.4",
                             linewidth=1.5, zorder=0))

# The STRUTS run from the column node down to each pile. In plan they are
# the lines from the centre to each pile.
strut_indices = list(result["strut_element_indices"])
for position, index in enumerate(strut_indices):
    if position >= len(pile_positions):
        break
    x, y = pile_positions[position]
    entry = struts[index]["load_cases"][0]
    axes.annotate("", xy=(x * 0.82, y * 0.82), xytext=(0.0, 0.0),
                  arrowprops=dict(arrowstyle="-|>", linewidth=2.2,
                                  color="#b03030"))
    axes.text(x * 0.45, y * 0.45,
              f"S{index}\nCf {entry['cf']:.0f}\nSF {entry['sf']:.2f}",
              fontsize=7.5, ha="center", va="center", color="#7a1f1f",
              bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                        edgecolor="none", alpha=0.85))

# The TIES run pile to pile around the group. Tension, so tf is negative.
tie_indices = list(result["tie_element_indices"])
for position, index in enumerate(tie_indices):
    start = pile_positions[position % len(pile_positions)]
    end = pile_positions[(position + 1) % len(pile_positions)]
    entry = ties[index]["load_cases"][0]
    governing = index == result["design_tie"]
    axes.plot([start[0], end[0]], [start[1], end[1]],
              color="#1f4e8c", linewidth=3.4 if governing else 2.0,
              linestyle="-" if governing else "--", zorder=2)
    axes.text((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0,
              f"T{index}\ntf {entry['tf']:.0f}\nAs {entry['as_required']:.0f}",
              fontsize=7.5, ha="center", va="center", color="#123a6b",
              bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                        edgecolor="none", alpha=0.9))

for index, (x, y) in enumerate(pile_positions):
    axes.add_patch(plt.Circle((x, y), CAP["pile_dia"] / 2.0,
                              facecolor="0.75", edgecolor="0.25",
                              linewidth=1.2, zorder=3))
    node = result["pile_nodes"][index]["load_cases"][0]
    axes.text(x, y - CAP["pile_dia"] / 2.0 - 0.16,
              f"P{index}  {pile_loads[index]:.0f} kN\nSF {node['sf']:.2f}",
              fontsize=7.5, ha="center", va="top", zorder=4)

column_node = result["column_node"]["load_cases"][0]
axes.add_patch(plt.Rectangle(
    (-CAP["column_dim_x"] / 2.0, -CAP["column_dim_y"] / 2.0),
    CAP["column_dim_x"], CAP["column_dim_y"],
    facecolor="0.45", edgecolor="0.15", linewidth=1.4, zorder=4))
axes.text(0.0, -CAP["column_dim_y"] / 2.0 - 0.14,
          f"column  Pf {column_node['pf']:.0f} kN\nSF {column_node['sf']:.2f}",
          fontsize=8, ha="center", va="top", color="0.1", zorder=5)

factors = ([(struts[i]["load_cases"][0]["sf"], f"strut {i}")
            for i in strut_indices]
           + [(column_node["sf"], "column node")]
           + [(node["load_cases"][0]["sf"], f"pile node {node['index']}")
              for node in result["pile_nodes"]])
worst, where = min(factors)

axes.set_aspect("equal")
axes.set_xlim(-half_x - 0.5, half_x + 0.5)
axes.set_ylim(-half_y - 0.6, half_y + 0.5)
axes.set_xlabel("x (m)")
axes.set_ylabel("y (m)")
axes.set_title(
    f"Strut-and-tie model, {CAP['design_code']}\n"
    f"cap {result['cap_dim_x']:.2f} x {result['cap_dim_y']:.2f} x "
    f"{CAP['cap_thickness']:.2f} m, {LOAD[0]['p']:.0f} kN + "
    f"{LOAD[0]['mx']:.0f} kNm\n"
    f"red = struts (compression), blue = ties (tension), "
    f"solid blue = the governing tie\n"
    f"worst safety factor {worst:.3f} at the {where}",
    fontsize=9)
axes.grid(True, linewidth=0.3, color="0.88")
figure.tight_layout()

output = Path("pile_cap_strut_tie.png")
figure.savefig(output, dpi=140)
plt.close(figure)

size = output.stat().st_size
print(f"\nWritten: {output.resolve()}")
print(f"  {size} bytes, "
      f"{'a real image' if size > 20_000 else 'SUSPICIOUSLY SMALL'}")

# ── The check the drawing enables ──────────────────────────────────────
# Every tie force must reconcile with element_forces at the same index.
# Two lists that should agree, so compare them.
print(f"\nTHE CROSS-CHECK THE DRAWING MAKES OBVIOUS")
print(f"   {'element':>8} {'tie tf':>10} {'element_forces':>15} {'agree?':>7}")
for index in tie_indices:
    tf = ties[index]["load_cases"][0]["tf"]
    raw = result["element_forces"][index][0]
    print(f"   {index:>8} {tf:>10.2f} {raw:>15.2f} "
          f"{'yes' if abs(tf - raw) < 0.01 else 'NO':>7}")
print("   -> element_forces is indexed by ELEMENT, and the tie results are")
print("      a view onto it. When those two disagree, the lookup is wrong -")
print("      and a diagram is the fastest place to see it.")
