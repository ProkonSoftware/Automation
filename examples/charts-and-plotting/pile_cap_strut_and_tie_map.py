# ---
# Example:  The pile cap as a truss - the strut-and-tie plan and the design boundary
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes - 2026-09-04 - the CSA reference cap reproduces its pinned strut/node/overhang triple; every cap, code and refusal measured on prokon-automation.exe
# ---
# A pile cap by strut and tie is a truss: the column load runs down
# inclined concrete struts to the piles, and horizontal steel ties pull
# the pile heads together. Every number C16 reports belongs to one member
# of that truss, and the fastest way to understand a cap is to see the
# truss drawn with those numbers on it.
#
# So the first panel draws it - piles, column, struts and ties, to scale,
# each member shaded by how hard it is working.
#
# ⚠ THE DRAWING IS CHECKED AGAINST THE ENGINE BEFORE IT IS BELIEVED. The
# cap plan the script draws is derived from the layout it supplied, and
# C16 publishes cap_dim_x itself - so the two are compared with == before
# anything is plotted. And the tie-to-edge mapping is an assumption, so
# the script reports whether the four tie forces are equal: on a symmetric
# cap they must be, and if they are the assumption cannot change the
# picture.
#
# The other panels are the design decisions:
#
#   THE BOUNDARY   tie steel over (cap thickness, pile spacing) - because
#                  measured, that is the ONLY reading that responds to the
#                  geometry. Every safety factor on this engine is
#                  invariant to both levers: the strut force and the strut
#                  capacity move together and their ratio does not budge.
#                  The edge of the map is a REFUSAL - C16 declines a cap
#                  whose depth is under half the pile spacing - so the
#                  script keeps the refusal message and draws it.
#   THE COUNT      cost against thickness for two, three, four and five
#                  piles - which count wins, and where it changes.
#   THE CODES      the same cap through the four codes C16 offers. Three
#                  of the four do not reach a safety factor of 1.0 on it,
#                  which is also the control that proves the factors above
#                  are not simply frozen numbers.
#
# ⚠ C16 WORKS IN METRES. Every length below is metres - cap, piles and
# column alike. It is the only engine in this set that does.
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

import math
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

import prokon.v5

# -- SAVE THE PNG, AND SHOW IT IN SPYDER --------------------------------
# Spyder runs matplotlib on its own backend - "inline" puts the figure in
# the Plots pane, "automatic" opens a window - so plt.show() displays the
# chart right where you are working. A headless run (a batch job, or this
# documentation's own sweep) runs the Agg backend, where show() can only
# warn. So ASK the backend, and write the PNG either way.
#
# There is deliberately NO matplotlib.use("Agg") here. That call forces
# the headless backend, and a script that forces it can never draw into
# Spyder's Plots pane - which is where you actually want to see it.
HEADLESS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template"}


def deliver(figure, filename):
    """Write the figure to a PNG, then show it if the backend can."""
    path = Path(filename).resolve()
    figure.savefig(path, dpi=150, facecolor="white")
    size = path.stat().st_size
    print("\nWritten: {0}".format(path))
    print("  {0:,} bytes  ({1})".format(
        size, "a real image" if size > 20_000 else "SUSPICIOUSLY SMALL"))
    if str(matplotlib.get_backend()).lower() in HEADLESS:
        plt.close(figure)
        print("  backend is headless - the PNG is the whole output")
    else:
        plt.show()          # Spyder: straight into the Plots pane
        print("  and shown on the {0} backend".format(
            matplotlib.get_backend()))


# -- The cap ------------------------------------------------------------
CODE = "CSA-A23.3:2019"
COLUMN = 0.5              # m square
PILE_DIA = 0.6            # m
TOLERANCE = 0.05          # m setting-out tolerance
OVERHANG = 0.3            # m beyond the pile face
REBAR_DEPTH = 0.1         # m soffit to bottom-steel centroid
FC = 30.0                 # MPa
FY = 400.0                # MPa
LOAD = 4000.0             # kN factored

SPACING = 1.8             # m, the reference cap
THICKNESS = 1.2           # m, the reference cap

RATE_CONCRETE = 1900.0    # per m3
RATE_STEEL = 25.0         # per kg
RATE_EXCAVATION = 200.0   # per m3
DENSITY_STEEL = 7850.0

THICKNESSES = np.arange(0.6, 1.81, 0.1)      # 13 m
SPACINGS = np.arange(1.20, 2.71, 0.15)       # 11 m
COUNTS = (2, 3, 4, 5)
CODES = prokon.v5.pile_cap.DESIGN_CODE_VALUES

print("THE PILE CAP AS A TRUSS")
print(f"  {CODE}, {COLUMN * 1000:.0f} mm column, "
      f"{PILE_DIA * 1000:.0f} mm piles, fc {FC:.0f}, fy {FY:.0f}")
print(f"  P = {LOAD:.0f} kN factored")
print(f"  grid: {len(THICKNESSES)} thicknesses x {len(SPACINGS)} spacings "
      f"= {len(THICKNESSES) * len(SPACINGS)} engine calls, plus "
      f"{len(COUNTS) * len(THICKNESSES) + len(CODES)} more")

# -- The anchor ---------------------------------------------------------
PINNED = (2064.6284818393965, 4143.75, 0.226)
envelope = prokon.v5.pile_cap.analyse(
    design_code=CODE, column_dim_x=0.5, column_dim_y=0.5, no_of_piles=4,
    pile_dia=0.6, pile_spacing=1.8, pile_tolerance=0.05,
    cap_thickness=1.2, cap_overhang=0.3, bottom_rebar_depth=0.1,
    fc=30.0, fy=400.0,
    load_cases=[{"name": "ULS", "load_factor": 1.0, "p": 4000.0}])
anchor = envelope["result"]
measured = (anchor["strut_results"][0]["load_cases"][0]["cr"],
            anchor["column_node"]["load_cases"][0]["pr"],
            anchor["overhang_min_required"])
print("\n  anchor: the CSA reference cap, 4 piles at 1.8 m under 4000 kN")
print(f"    strut Cr          {measured[0]!r}   pinned {PINNED[0]!r}")
print(f"    column node Pr    {measured[1]!r}   pinned {PINNED[1]!r}")
print(f"    overhang required {measured[2]!r}   pinned {PINNED[2]!r}")
print(f"    -> {'EXACT on all three' if measured == PINNED else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def cap(thickness=THICKNESS, spacing=SPACING, piles=4, code=CODE):
    """One cap. Returns the whole result, or None if the engine refuses.

    ⚠ UPLIFT ARRIVES AS A REFUSAL, not as a flag - has_uplift stays False
    right up to the point where the engine declines the cap - so the
    except arm here is a real branch, not defensive noise.
    """
    try:
        return prokon.v5.pile_cap.analyse(
            design_code=code, column_dim_x=COLUMN, column_dim_y=COLUMN,
            no_of_piles=piles, pile_dia=PILE_DIA,
            pile_spacing=float(spacing), pile_tolerance=TOLERANCE,
            cap_thickness=float(thickness), cap_overhang=OVERHANG,
            bottom_rebar_depth=REBAR_DEPTH, fc=FC, fy=FY,
            load_cases=[{"name": "ULS", "load_factor": 1.0, "p": LOAD}])["result"]
    except prokon.v5.ProkonError:
        return None


def worst_factor(result):
    """The governing safety factor over every strut and both node families.

    ⚠ TIES DO NOT PUBLISH AN sf - a tie gives tf and as_required, and its
    check is whether you provide that steel. They are read separately.
    """
    factors = [strut["load_cases"][0]["sf"]
               for strut in result["strut_results"]]
    factors.append(result["column_node"]["load_cases"][0]["sf"])
    factors += [node["load_cases"][0]["sf"] for node in result["pile_nodes"]]
    return min(factors)


def price(result, thickness):
    """Concrete, steel and excavation for one cap."""
    plan = result["cap_dim_x"] * result["cap_dim_y"]
    volume = plan * thickness
    # The design tie's steel, run both ways across the cap.
    tie = max(entry["load_cases"][0]["as_required"]
              for entry in result["tie_results"])
    minimum = result["tie_minim_reinforcement"] * math.sqrt(plan)
    steel_mm2 = max(tie, minimum) * 2.0
    steel_kg = steel_mm2 / 1e6 * math.sqrt(plan) * DENSITY_STEEL
    return {
        "concrete": volume * RATE_CONCRETE,
        "steel": steel_kg * RATE_STEEL,
        "excavation": volume * RATE_EXCAVATION,
        "cost": (volume * (RATE_CONCRETE + RATE_EXCAVATION)
                 + steel_kg * RATE_STEEL),
        "volume": volume,
        "steel_kg": steel_kg,
    }


# -- The reference cap, and the check on the drawing --------------------
reference = cap()
print(f"\nTHE REFERENCE CAP   4 piles at {SPACING:.2f} m, "
      f"{THICKNESS:.2f} m thick")
print(f"   cap plan  {reference['cap_dim_x']:.3f} x "
      f"{reference['cap_dim_y']:.3f} m")

drawn_plan = SPACING + PILE_DIA + 2.0 * OVERHANG
print("\nDOES THE DRAWING MATCH THE ENGINE?")
print(f"   the plan this script would draw: spacing {SPACING:.2f} + pile "
      f"{PILE_DIA:.2f} + 2 x overhang {OVERHANG:.2f}")
print(f"     = {drawn_plan:.6f} m")
print(f"   the plan the engine reports:      "
      f"{reference['cap_dim_x']:.6f} m")
exact_plan = abs(drawn_plan - reference["cap_dim_x"]) < 1e-9
print(f"   -> {'IDENTICAL, so the plan below is the real cap' if exact_plan else 'DIFFERENT - the drawing is only indicative'}")

tie_forces = [entry["load_cases"][0]["tf"] for entry in
              reference["tie_results"]]
tie_steel = [entry["load_cases"][0]["as_required"] for entry in
             reference["tie_results"]]
all_equal = max(tie_forces) - min(tie_forces) < 1e-9
print(f"   the four tie forces: "
      + "  ".join(f"{value:.2f}" for value in tie_forces))
print(f"   -> {'all equal' if all_equal else 'NOT equal'}, "
      f"{'so which tie is drawn on which edge cannot change the picture'
         if all_equal else 'so the tie-to-edge mapping below matters'}")
print("      (on a symmetric cap under a concentric load they must be;")
print("      that is the check, and it is why the assumed mapping is safe")
print("      HERE and would need establishing on an eccentric cap)")

print(f"\n   {'member':>16} {'force (kN)':>11} {'capacity':>10} {'SF':>7}")
for strut in reference["strut_results"]:
    row = strut["load_cases"][0]
    print(f"   {'strut ' + str(strut['element_index']):>16} "
          f"{row['cf']:>11.1f} {row['cr']:>10.1f} {row['sf']:>7.3f}")
node = reference["column_node"]["load_cases"][0]
print(f"   {'column node':>16} {node['pf']:>11.1f} {node['pr']:>10.1f} "
      f"{node['sf']:>7.3f}")
for pile in reference["pile_nodes"]:
    row = pile["load_cases"][0]
    print(f"   {'pile node ' + str(pile['index']):>16} {row['pf']:>11.1f} "
          f"{row['pr']:>10.1f} {row['sf']:>7.3f}")
for index, entry in enumerate(reference["tie_results"]):
    row = entry["load_cases"][0]
    print(f"   {'tie ' + str(entry['element_index']):>16} "
          f"{row['tf']:>11.1f} {'-':>10} {'(steel: ' + format(row['as_required'], '.0f') + ' mm2)':>7}")
print(f"   governing safety factor {worst_factor(reference):.3f}")

# -- The design boundary ------------------------------------------------
# ⚠ The boundary here is NOT a low safety factor. It is a refusal: C16
# validates the layout before it designs anything, and declines a cap that
# breaks its geometry rules. So the refusal MESSAGE is collected, because
# it is the only thing that says where the edge is and why.
factor = np.full((len(THICKNESSES), len(SPACINGS)), np.nan)
strut_factor = np.full_like(factor, np.nan)
tie_steel = np.full_like(factor, np.nan)
cost = np.full_like(factor, np.nan)
strut_force = np.full_like(factor, np.nan)
strut_capacity = np.full_like(factor, np.nan)
refusal_reasons = {}
refusals = 0

for row, thickness in enumerate(THICKNESSES):
    for column, spacing in enumerate(SPACINGS):
        try:
            result = prokon.v5.pile_cap.analyse(
                design_code=CODE, column_dim_x=COLUMN, column_dim_y=COLUMN,
                no_of_piles=4, pile_dia=PILE_DIA,
                pile_spacing=float(spacing), pile_tolerance=TOLERANCE,
                cap_thickness=float(thickness), cap_overhang=OVERHANG,
                bottom_rebar_depth=REBAR_DEPTH, fc=FC, fy=FY,
                load_cases=[{"name": "ULS", "load_factor": 1.0,
                             "p": LOAD}])["result"]
        except prokon.v5.ProkonError as refusal:
            refusals += 1
            text = refusal.message.encode("ascii", "replace").decode()
            refusal_reasons[text] = refusal_reasons.get(text, 0) + 1
            continue
        factor[row, column] = worst_factor(result)
        strut = result["strut_results"][0]["load_cases"][0]
        strut_factor[row, column] = strut["sf"]
        strut_force[row, column] = strut["cf"]
        strut_capacity[row, column] = strut["cr"]
        tie_steel[row, column] = max(entry["load_cases"][0]["as_required"]
                                     for entry in result["tie_results"])
        cost[row, column] = price(result, float(thickness))["cost"]

answered = int(np.count_nonzero(~np.isnan(factor)))
valid = ~np.isnan(factor)
adequate = valid & (factor >= 1.0)
print(f"\nTHE DESIGN BOUNDARY   {answered} caps answered, "
      f"{refusals} refused")
for text, count in sorted(refusal_reasons.items(), key=lambda row: -row[1]):
    print(f"   refused {count:>3} times: {text}")
print(f"   {int(np.count_nonzero(adequate))} of the {answered} that ran "
      f"reach a safety factor of 1.0")
print("   -> the boundary on this map is a REFUSAL, not a low factor. C16")
print("      validates the layout before it designs anything, so a cap")
print("      that is out of proportion never gets a number at all. A")
print("      script that only catches exceptions to skip them loses the")
print("      one sentence that says where the edge is.")

# -- The reading that does not move, and the control on it --------------
# CLAIM: on this engine and this code, the safety factors are invariant to
# cap thickness and pile spacing - the strut force and its capacity move
# together and the ratio does not.
# CONTROL: the same reading MUST move for something. Changing the design
# code moves it (measured below), so the number is not simply frozen.
print("\nTHE SAFETY FACTORS DO NOT RESPOND TO THE GEOMETRY")
print(f"   {'thickness':>10} {'spacing':>8} {'strut Cf':>9} "
      f"{'strut Cr':>9} {'ratio':>8} {'tie steel':>10}")
for thickness, spacing in ((0.7, 1.20), (1.4, 1.20), (1.4, 1.80),
                           (1.8, 2.40)):
    row = list(THICKNESSES).index(
        min(THICKNESSES, key=lambda value: abs(value - thickness)))
    column = list(SPACINGS).index(
        min(SPACINGS, key=lambda value: abs(value - spacing)))
    if np.isnan(strut_factor[row, column]):
        continue
    print(f"   {THICKNESSES[row]:>10.2f} {SPACINGS[column]:>8.2f} "
          f"{strut_force[row, column]:>9.1f} "
          f"{strut_capacity[row, column]:>9.1f} "
          f"{strut_factor[row, column]:>8.4f} "
          f"{tie_steel[row, column]:>8.0f} mm2")
spread = (np.nanmax(strut_factor) - np.nanmin(strut_factor))
print(f"   across all {answered} valid caps the strut factor spans "
      f"{spread:.6f}")
print(f"   and the governing factor spans "
      f"{np.nanmax(factor) - np.nanmin(factor):.6f}")
print("   -> Cf and Cr move a long way and their RATIO does not move at")
print("      all. Thickening the cap or spreading the piles buys no")
print("      margin on any strut or node. The only thing the geometry")
print(f"      changes is the tie steel, and that spans "
      f"{np.nanmin(tie_steel):.0f} to {np.nanmax(tie_steel):.0f} mm2.")

usable = np.where(adequate, cost, np.nan)
if np.any(adequate):
    best = np.unravel_index(np.nanargmin(usable), usable.shape)
    best_thickness = float(THICKNESSES[best[0]])
    best_spacing = float(SPACINGS[best[1]])
    print(f"\n   cheapest valid cap: {best_thickness:.2f} m thick, piles "
          f"at {best_spacing:.2f} m")
    print(f"     cost {usable[best]:.0f}, governing factor "
          f"{factor[best]:.3f}, tie steel "
          f"{tie_steel[best]:.0f} mm2")
    print("   -> it sits hard against the validity rule, because nothing")
    print("      inside the valid region penalises it for being there.")

# -- Pile count ---------------------------------------------------------
print(f"\nHOW MANY PILES?   at {SPACING:.2f} m spacing")
print(f"   {'thickness':>10}" + "".join(f"{count:>10} piles"
                                        for count in COUNTS))
count_curves = {count: {"thickness": [], "cost": [], "factor": []}
                for count in COUNTS}
for thickness in THICKNESSES:
    line = []
    for count in COUNTS:
        result = cap(thickness=float(thickness), piles=count)
        if result is None:
            line.append("refused")
            continue
        money = price(result, float(thickness))
        good = worst_factor(result)
        count_curves[count]["thickness"].append(float(thickness))
        count_curves[count]["cost"].append(money["cost"])
        count_curves[count]["factor"].append(good)
        line.append(f"{money['cost']:.0f}" + ("" if good >= 1.0 else "!"))
    print(f"   {thickness:>10.2f}" + "".join(f"{cell:>16}" for cell in line))
print("   ! marks a cap that does not reach a safety factor of 1.0")

print(f"\n   {'piles':>6} {'cheapest adequate':>19} {'cost':>9} "
      f"{'cap plan':>10}")
for count in COUNTS:
    data = count_curves[count]
    good = [(data["cost"][i], data["thickness"][i])
            for i in range(len(data["cost"])) if data["factor"][i] >= 1.0]
    if not good:
        print(f"   {count:>6} {'none adequate':>19}")
        continue
    money, thickness = min(good)
    result = cap(thickness=thickness, piles=count)
    print(f"   {count:>6} {thickness:>16.2f} m {money:>9.0f} "
          f"{result['cap_dim_x']:>4.2f} x {result['cap_dim_y']:.2f}")

# -- The four codes -----------------------------------------------------
print(f"\nTHE FOUR CODES   the reference cap, unchanged")
print(f"   {'code':>18} {'worst SF':>9} {'strut Cr':>10} {'tie steel':>11}")
code_rows = []
for name in CODES:
    result = cap(code=name)
    if result is None:
        print(f"   {name:>18} {'refused':>9}")
        continue
    tie = max(entry["load_cases"][0]["as_required"]
              for entry in result["tie_results"])
    code_rows.append((name, worst_factor(result),
                      result["strut_results"][0]["load_cases"][0]["cr"],
                      tie))
    print(f"   {name:>18} {code_rows[-1][1]:>9.3f} "
          f"{code_rows[-1][2]:>10.1f} {tie:>9.0f} mm2")
if len(code_rows) > 1:
    factors = [row[1] for row in code_rows]
    steels = [row[3] for row in code_rows]
    print(f"   -> the safety factors span {min(factors):.3f} to "
          f"{max(factors):.3f} ({max(factors) / min(factors):.2f}x) and")
    print(f"      the tie steel {min(steels):.0f} to {max(steels):.0f} mm2 "
          f"({max(steels) / min(steels):.2f}x) on ONE cap.")

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(2, 2, figsize=(15, 11))
figure.patch.set_facecolor("white")

# 1. The truss, in plan.
truss = axes[0][0]
half = SPACING / 2.0
piles = [(-half, -half), (half, -half), (half, half), (-half, half)]
plan_half = reference["cap_dim_x"] / 2.0

truss.add_patch(Rectangle((-plan_half, -plan_half),
                          reference["cap_dim_x"], reference["cap_dim_y"],
                          facecolor="0.93", edgecolor="0.4",
                          linewidth=1.6, zorder=0))

strut_factors = [strut["load_cases"][0]["sf"]
                 for strut in reference["strut_results"]]
for index, (x, y) in enumerate(piles):
    safety = strut_factors[index % len(strut_factors)]
    force = reference["strut_results"][index % len(strut_factors)]
    truss.plot([0, x], [0, y], linewidth=5.0,
               color=plt.cm.RdYlGn(min(safety / 3.0, 1.0)), zorder=2,
               solid_capstyle="round")
    truss.annotate(f"strut\n{force['load_cases'][0]['cf']:.0f} kN\n"
                   f"SF {safety:.2f}", (x * 0.55, y * 0.55),
                   ha="center", va="center", fontsize=7.5, zorder=5,
                   bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                             alpha=0.85, edgecolor="none"))

for index in range(len(piles)):
    start = piles[index]
    end = piles[(index + 1) % len(piles)]
    row = reference["tie_results"][index % len(reference["tie_results"])]
    truss.plot([start[0], end[0]], [start[1], end[1]], linewidth=3.0,
               color="#b03030", linestyle="--", zorder=2)
    truss.annotate(f"tie {abs(row['load_cases'][0]['tf']):.0f} kN\n"
                   f"{row['load_cases'][0]['as_required']:.0f} mm2",
                   ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2),
                   ha="center", va="center", fontsize=7.5, color="#b03030",
                   zorder=5,
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                             alpha=0.85, edgecolor="none"))

for index, (x, y) in enumerate(piles):
    reaction = reference["pile_forces"][index][0]["p"]
    truss.add_patch(Circle((x, y), PILE_DIA / 2.0, facecolor="#4c78a8",
                           edgecolor="black", linewidth=1.2, zorder=3))
    # Radially outward, so it never lands on the strut label that runs
    # from this pile back to the column.
    truss.annotate(f"{reaction:.0f} kN",
                   (x * 1.0 + (0.30 if x > 0 else -0.30),
                    y + (0.30 if y > 0 else -0.30)),
                   ha="center", va="center", fontsize=8, zorder=6,
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                             alpha=0.85, edgecolor="none"))

truss.add_patch(Rectangle((-COLUMN / 2, -COLUMN / 2), COLUMN, COLUMN,
                          facecolor="0.3", edgecolor="black",
                          linewidth=1.4, zorder=4))
truss.annotate(f"{LOAD:.0f} kN", (0, 0), ha="center", va="center",
               color="white", fontsize=8, fontweight="bold", zorder=5)

truss.set_xlim(-plan_half - 0.25, plan_half + 0.25)
truss.set_ylim(-plan_half - 0.3, plan_half + 0.25)
truss.set_aspect("equal")
truss.set_xlabel("m")
truss.set_ylabel("m")
truss.set_title(f"The truss in plan - {reference['cap_dim_x']:.2f} x "
                f"{reference['cap_dim_y']:.2f} m cap\n"
                f"struts shaded by safety factor, ties dashed red",
                fontsize=10)

# 2. The design boundary - a refusal, and the one reading that moves.
chart = axes[0][1]
mesh_s, mesh_t = np.meshgrid(SPACINGS, THICKNESSES)
shade = chart.contourf(mesh_s, mesh_t, tie_steel, levels=20, cmap="YlOrBr")
figure.colorbar(shade, ax=chart, label="tie steel required (mm2)")
chart.contourf(mesh_s, mesh_t, np.where(valid, np.nan, 1.0),
               levels=[0.5, 1.5], colors=["0.85"])
chart.contourf(mesh_s, mesh_t, np.where(valid, np.nan, 1.0),
               levels=[0.5, 1.5], colors="none", hatches=["//"])
lines = chart.contour(mesh_s, mesh_t, tie_steel, levels=8, colors="0.25",
                      linewidths=0.9)
chart.clabel(lines, fmt="%.0f", fontsize=7)
edge = chart.contour(mesh_s, mesh_t, np.where(valid, 1.0, 0.0),
                     levels=[0.5], colors="black", linewidths=2.6)
chart.clabel(edge, fmt={0.5: "depth : spacing = 1 : 2"}, fontsize=8)
cheapest_cost = chart.contour(mesh_s, mesh_t, np.where(valid, cost, np.nan),
                              levels=6, colors="#1f4e79", linewidths=1.0,
                              linestyles="--")
chart.clabel(cheapest_cost, fmt="%.0f", fontsize=6.5)
if np.any(adequate):
    chart.plot(best_spacing, best_thickness, marker="*", markersize=22,
               color="white", markeredgecolor="black", zorder=6)
chart.set_xlabel("pile spacing (m)")
chart.set_ylabel("cap thickness (m)")
chart.set_title("Tie steel (filled) and cost (dashed blue)\n"
                "hatched: C16 REFUSES the layout - the boundary is a "
                "refusal,\nnot a low safety factor", fontsize=10)

# 3. Pile count.
counts = axes[1][0]
palette = dict(zip(COUNTS, ("#e0a030", "#59a14f", "#4c78a8", "#9467bd")))
for count in COUNTS:
    data = count_curves[count]
    if not data["thickness"]:
        continue
    good = [i for i in range(len(data["cost"])) if data["factor"][i] >= 1.0]
    counts.plot(data["thickness"], data["cost"], linewidth=1.0,
                linestyle=":", color=palette[count])
    if good:
        counts.plot([data["thickness"][i] for i in good],
                    [data["cost"][i] for i in good], linewidth=2.2,
                    marker="o", markersize=5, color=palette[count],
                    label=f"{count} piles")
        cheapest = min(good, key=lambda i: data["cost"][i])
        counts.plot(data["thickness"][cheapest], data["cost"][cheapest],
                    marker="*", markersize=16, color="white",
                    markeredgecolor="black", zorder=6)
counts.set_xlabel("cap thickness (m)")
counts.set_ylabel("cost of the cap")
counts.set_title("Two, three, four or five piles\n"
                 "solid where every strut and node reaches SF = 1.0",
                 fontsize=10)
counts.legend(fontsize=8)
counts.grid(True, linewidth=0.3, color="0.85")

# 4. The codes.
codes = axes[1][1]
if code_rows:
    names = [row[0] for row in code_rows]
    positions = np.arange(len(names))
    twin = codes.twinx()
    codes.bar(positions - 0.2, [row[1] for row in code_rows], width=0.4,
              color="#4c78a8", label="worst safety factor")
    twin.bar(positions + 0.2, [row[3] for row in code_rows], width=0.4,
             color="#b03030", label="tie steel required")
    # Headroom, so a full-height red bar does not appear to cross the
    # SF = 1.0 line, which belongs to the OTHER axis.
    twin.set_ylim(0, max(row[3] for row in code_rows) * 1.35)
    codes.axhline(1.0, color="black", linestyle="--", linewidth=1.4)
    codes.annotate("SF = 1.0", (-0.4, 1.05), fontsize=8)
    codes.set_xticks(positions)
    codes.set_xticklabels(names, fontsize=7.5, rotation=12)
    codes.set_ylabel("worst safety factor", color="#4c78a8")
    twin.set_ylabel("tie steel required (mm2)", color="#b03030")
    codes.set_title("The same cap, the four codes C16 offers", fontsize=10)
    codes.grid(True, axis="y", linewidth=0.3, color="0.85")

figure.suptitle(
    f"Pile cap strut and tie - {CODE}\n"
    f"{COLUMN * 1000:.0f} mm column on {PILE_DIA * 1000:.0f} mm piles, "
    f"P = {LOAD:.0f} kN, fc {FC:.0f} MPa, fy {FY:.0f} MPa, "
    f"overhang {OVERHANG:.2f} m  |  "
    f"concrete {RATE_CONCRETE:.0f}/m3, steel {RATE_STEEL:.0f}/kg  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.94))

deliver(figure, "pile_cap_strut_and_tie_map.png")
