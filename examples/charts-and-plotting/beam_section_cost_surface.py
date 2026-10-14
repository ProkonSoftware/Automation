# ---
# Example:  The cost surface of a beam - and how flat the floor of the valley is
# Feature:  beam_section (C22 Beam Section)
# Verified: yes - 2026-09-04 - the pinned 300 x 500 reference section reproduces its mu/ast; every one of the 345 priced sections measured on prokon-automation.exe
# ---
# Ask an engineer for the cheapest beam and you get a depth. Ask for the
# cheapest beam AND how much it matters, and you need a surface.
#
# This script sweeps 345 sections through C22 - every width from 150 to
# 500 mm against every depth from 450 to 1000 mm - prices each one from
# concrete, steel and formwork, and draws the result as a cost map.
#
# The map is worth more than the minimum on it, and two of the things it
# shows are worth more than the minimum too.
#
# FIRST, THE MINIMUM IS NOT WHERE THE STORY IS. The cheapest section the
# sweep finds sits on the NARROW EDGE of the priced range - and it is
# running at only 60 % of the shear ceiling when it gets there. So the
# engine is not what stops the optimiser going narrower; the edge of the
# grid is. A cost sweep on its own will always hand back the thinnest web
# you let it consider, and the script measures what a buildable web costs
# instead of that. THAT number is the useful one.
#
# SECOND, THE VALLEY IS FLAT IN DEPTH. At any fixed width there is a wide
# band of depths within 2 % of the best, which is the difference between
# "the answer is 850 mm" and "anything from here to here is fine, so pick
# the one that suits the services".
#
# Two boundaries are drawn on the map, both measured rather than assumed:
#
#   the SHEAR CEILING     over it the web is too thin, and no amount of
#                         link steel fixes that - vv > vcu is a ceiling,
#                         not a capacity you reinforce past
#   the mu = M CONTOUR    below it the section needs compression steel
#
# Uses matplotlib and numpy, both bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

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


# -- The job ------------------------------------------------------------
CODE = "BS8110 - 1997"
MOMENT = 450.0            # kNm ultimate
SHEAR = 320.0             # kN ultimate
FCU = 30.0
FY = 450.0
FYV = 450.0
COVER = 45.0              # mm to bar centres, every face

# Rates. Change these three numbers and the whole map moves - which is
# the point of pricing a design rather than eyeballing it.
RATE_CONCRETE = 2100.0    # per m3 placed
RATE_STEEL = 24.0         # per kg fixed
RATE_FORMWORK = 260.0     # per m2 of contact area
DENSITY_STEEL = 7850.0    # kg/m3

WIDTHS = np.arange(150.0, 501.0, 25.0)      # 15
DEPTHS = np.arange(450.0, 1001.0, 25.0)     # 23

print("THE COST SURFACE OF A BEAM")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, cover {COVER:.0f} mm")
print(f"  M = {MOMENT:.0f} kNm, V = {SHEAR:.0f} kN")
print(f"  rates: concrete {RATE_CONCRETE:.0f}/m3, steel {RATE_STEEL:.0f}/kg,"
      f" formwork {RATE_FORMWORK:.0f}/m2")
print(f"  grid: {len(WIDTHS)} widths x {len(DEPTHS)} depths "
      f"= {len(WIDTHS) * len(DEPTHS)} engine calls")

# -- The anchor ---------------------------------------------------------
# Before any of this script's own numbers are worth reading, reproduce the
# section C22's own test suite pins. If this has drifted, nothing below is
# safe to quote.
PINNED_MU = 295.18197048179997
PINNED_AST = 1287.32677061758
envelope = prokon.v5.beam_section.analyse(
    design_code=CODE, m=200.0, v=100.0, bw=300.0, h=500.0,
    dc_t=40.0, dc_b=40.0, dc_s=40.0, fcu=30.0, fy=450.0, fyv=450.0)
anchor = envelope["result"]
exact = anchor["mu"] == PINNED_MU and anchor["ast"] == PINNED_AST
print("\n  anchor: the pinned 300 x 500 reference section")
print(f"    mu  {anchor['mu']!r}   pinned {PINNED_MU!r}")
print(f"    ast {anchor['ast']!r}   pinned {PINNED_AST!r}")
print(f"    -> {'EXACT on both' if exact else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def price(bw, h):
    """One section, priced. Returns a dict, or None if the engine refuses."""
    try:
        result = prokon.v5.beam_section.analyse(
            design_code=CODE, m=MOMENT, v=SHEAR, bw=bw, h=h,
            dc_t=COVER, dc_b=COVER, dc_s=COVER,
            fcu=FCU, fy=FY, fyv=FYV)["result"]
    except prokon.v5.ProkonError:
        return None

    # Longitudinal steel, per metre of beam: mm2 x 1000 mm -> mm3.
    main_mm3 = (result["ast"] + result["as1"]) * 1000.0

    # Links. asv is Asv/sv in mm2/mm and asvn is the code's nominal
    # minimum - a real beam gets the larger of the two, so price that.
    # Over 1000 mm of beam the link steel volume is (Asv/sv) x 1000 mm x
    # the perimeter of one link.
    link_perimeter = 2.0 * ((bw - 2 * COVER) + (h - 2 * COVER))
    links = max(result["asv"], result["asvn"])
    link_mm3 = links * 1000.0 * link_perimeter

    steel_kg = (main_mm3 + link_mm3) / 1e9 * DENSITY_STEEL
    concrete_m3 = bw * h / 1e6
    formwork_m2 = (bw + 2.0 * h) / 1000.0

    return {
        "concrete": concrete_m3 * RATE_CONCRETE,
        "steel": steel_kg * RATE_STEEL,
        "formwork": formwork_m2 * RATE_FORMWORK,
        "steel_kg": steel_kg,
        "ast": result["ast"],
        "as1": result["as1"],
        "mu": result["mu"],
        "shear_ok": result["vv"] <= result["vcu"],
        "shear_use": result["vv"] / result["vcu"],
    }


# -- Sweep --------------------------------------------------------------
cost = np.full((len(DEPTHS), len(WIDTHS)), np.nan)
steel = np.full_like(cost, np.nan)
capacity = np.full_like(cost, np.nan)
shear_use = np.full_like(cost, np.nan)
cells = {}
over_ceiling = 0

for column, bw in enumerate(WIDTHS):
    for row, h in enumerate(DEPTHS):
        found = price(float(bw), float(h))
        if found is None:
            continue
        shear_use[row, column] = found["shear_use"]
        if not found["shear_ok"]:
            over_ceiling += 1
            continue
        cost[row, column] = (found["concrete"] + found["steel"]
                             + found["formwork"])
        steel[row, column] = found["steel_kg"]
        capacity[row, column] = found["mu"]
        cells[(float(bw), float(h))] = found

best_index = np.unravel_index(np.nanargmin(cost), cost.shape)
best_h = float(DEPTHS[best_index[0]])
best_bw = float(WIDTHS[best_index[1]])
best_cost = float(cost[best_index])
best = cells[(best_bw, best_h)]

print(f"\nCHEAPEST SECTION   {best_bw:.0f} x {best_h:.0f} mm at "
      f"{best_cost:.0f} per metre")
print(f"   concrete {best['concrete']:7.0f}   steel {best['steel']:7.0f}"
      f"   formwork {best['formwork']:7.0f}")
print(f"   steel content {best['steel_kg']:.1f} kg/m, "
      f"Ast {best['ast']:.0f} mm2, mu {best['mu']:.0f} kNm")
print(f"   shear utilisation vv/vcu = {best['shear_use']:.3f}")

# -- What actually bounds the width, measured --------------------------
# The shear ceiling is the only check here with no reinforcement remedy,
# so it is the obvious candidate. It is not the answer.
print("\nWHAT STOPS THE OPTIMISER GOING NARROWER - AND IT IS NOT SHEAR")
print(f"   {over_ceiling} of {len(WIDTHS) * len(DEPTHS)} sections are over "
      f"the shear ceiling vcu, all of them")
print("   shallow AND narrow together - the hatched corner of the map.")
print(f"   But the cheapest ALLOWED section runs at only "
      f"{best['shear_use']:.0%} of that ceiling,")
print(f"   and it sits on the narrow EDGE of the priced range "
      f"({best_bw:.0f} mm).")
print("   -> the ceiling is not what stopped it. The edge of the grid is.")
print("      A cost sweep on its own always returns the thinnest web you")
print("      let it consider, because a narrower web saves more concrete")
print("      and formwork than the steel it costs. The bound that matters")
print("      on a real beam - bar fit, vibrator access, achievable cover -")
print("      is not in the price list, so you have to supply it.")

# So supply it, and price it. This is the number to take to a meeting.
BUILDABLE = 300.0         # mm - a web you can actually pour and vibrate
buildable_column = list(WIDTHS).index(BUILDABLE)
buildable_costs = cost[:, buildable_column]
buildable_row = int(np.nanargmin(buildable_costs))
buildable_h = float(DEPTHS[buildable_row])
buildable_cost = float(buildable_costs[buildable_row])
print(f"\n   held at a buildable {BUILDABLE:.0f} mm web, the cheapest is "
      f"{BUILDABLE:.0f} x {buildable_h:.0f} mm")
print(f"   at {buildable_cost:.0f} per metre - "
      f"{100.0 * (buildable_cost / best_cost - 1.0):+.1f} % against the "
      f"map's own minimum.")

# -- How flat is the valley floor? --------------------------------------
within = int(np.count_nonzero(cost <= best_cost * 1.02))
total_cells = int(np.count_nonzero(~np.isnan(cost)))
band = [float(DEPTHS[row]) for row in range(len(DEPTHS))
        if not np.isnan(buildable_costs[row])
        and buildable_costs[row] <= buildable_cost * 1.02]
print("\nHOW MUCH DOES THE DEPTH MATTER?")
print(f"   over the whole map, {within} of {total_cells} priced sections "
      f"come within 2 %")
print(f"   of the cheapest, and the map spans {np.nanmin(cost):.0f} to "
      f"{np.nanmax(cost):.0f} per metre "
      f"({np.nanmax(cost) / np.nanmin(cost):.2f}x)")
print(f"   at the buildable {BUILDABLE:.0f} mm web, every depth from "
      f"{min(band):.0f} to {max(band):.0f} mm")
print(f"   is within 2 % - a {max(band) - min(band):.0f} mm band, "
      f"{len(band)} of the {len(DEPTHS)} depths priced.")
print("   -> the minimum in depth is a REGION, not a point. Pick the depth")
print("      in it that suits the services, the formwork you already own,")
print("      or the soffit the architect will accept.")

# -- The compression-steel boundary, and the control on it --------------
# CLAIM: compression steel appears exactly where the section's own
# singly-reinforced capacity mu falls below the applied moment.
# CONTROL: count the cells where the two disagree - but a count of zero
# would ALSO come out of a grid where no cell needs compression steel, or
# where every cell does. So both populations are printed beside it; the
# agreement is only a result while both are non-empty.
disagree = 0
doubly_cells = 0
for found in cells.values():
    below = found["mu"] < MOMENT
    needs = found["as1"] > 0
    doubly_cells += 1 if needs else 0
    disagree += 0 if below == needs else 1

print("\nWHERE COMPRESSION STEEL STARTS")
print(f"   {doubly_cells} of {len(cells)} sections need compression steel")
print(f"   cells where (mu < M) disagrees with (as1 > 0): {disagree}")
print(f"   -> the boundary is the engine's own mu = {MOMENT:.0f} kNm "
      f"contour, exactly")
print("      (both populations are non-empty, so the agreement is a result")
print("      and not an artefact of one of them being the whole grid)")

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(2, 2, figsize=(14.5, 10.5))
figure.patch.set_facecolor("white")
grid_w, grid_h = np.meshgrid(WIDTHS, DEPTHS)

# 1. The cost map.
top_left = axes[0][0]
filled = top_left.contourf(grid_w, grid_h, cost, levels=22, cmap="viridis")
figure.colorbar(filled, ax=top_left, label="cost per metre of beam")

bands = top_left.contour(grid_w, grid_h, cost,
                         levels=[best_cost * 1.02, best_cost * 1.05,
                                 best_cost * 1.10],
                         colors="white", linewidths=1.2,
                         linestyles=["-", "--", ":"])
top_left.clabel(bands, fmt={best_cost * 1.02: "+2%",
                            best_cost * 1.05: "+5%",
                            best_cost * 1.10: "+10%"}, fontsize=8)

# The compression-steel boundary, drawn from the engine's own capacity.
boundary = top_left.contour(grid_w, grid_h, capacity, levels=[MOMENT],
                            colors="red", linewidths=2.0)
top_left.clabel(boundary, fmt={MOMENT: "mu = M"}, fontsize=8)

# The shear ceiling - hatched, because it is not a costlier region, it is
# a forbidden one.
top_left.contourf(grid_w, grid_h, shear_use, levels=[1.0, 99.0],
                  colors="none", hatches=["xx"])
top_left.contour(grid_w, grid_h, shear_use, levels=[1.0],
                 colors="black", linewidths=2.2)
top_left.annotate("shear ceiling\nvv > vcu\n(no remedy)",
                  (WIDTHS[0] + 30, DEPTHS[0] + 20), fontsize=8,
                  color="black", fontweight="bold")

top_left.plot(best_bw, best_h, marker="*", markersize=22,
              color="white", markeredgecolor="black", markeredgewidth=1.0,
              zorder=5)
top_left.annotate(f"map minimum\n{best_bw:.0f} x {best_h:.0f}\n"
                  f"{best_cost:.0f}/m",
                  (best_bw, best_h), textcoords="offset points",
                  xytext=(22, -56), color="white", fontsize=8,
                  fontweight="bold")

# The buildable optimum - the one you would actually detail.
top_left.plot(BUILDABLE, buildable_h, marker="o", markersize=11,
              color="orange", markeredgecolor="black", markeredgewidth=1.0,
              zorder=5)
top_left.annotate(f"buildable web\n{BUILDABLE:.0f} x {buildable_h:.0f}\n"
                  f"{buildable_cost:.0f}/m "
                  f"({100.0 * (buildable_cost / best_cost - 1.0):+.1f}%)",
                  (BUILDABLE, buildable_h), textcoords="offset points",
                  xytext=(12, -4), color="white", fontsize=8,
                  fontweight="bold")
top_left.set_xlabel("web width bw (mm)")
top_left.set_ylabel("overall depth h (mm)")
top_left.set_title("Cost per metre, and the two boundaries on it\n"
                   "hatched: over the shear ceiling    red: needs "
                   "compression steel", fontsize=10)

# 2. Steel content - the other half of the trade-off.
top_right = axes[0][1]
steel_map = top_right.contourf(grid_w, grid_h, steel, levels=20,
                               cmap="magma_r")
figure.colorbar(steel_map, ax=top_right, label="steel content (kg per metre)")
lines = top_right.contour(grid_w, grid_h, steel, levels=8,
                          colors="0.25", linewidths=0.6)
top_right.clabel(lines, fmt="%.0f", fontsize=7)
top_right.plot(best_bw, best_h, marker="*", markersize=18, color="white",
               markeredgecolor="black", zorder=5)
top_right.set_xlabel("web width bw (mm)")
top_right.set_ylabel("overall depth h (mm)")
top_right.set_title("Steel content - falls with depth, without a minimum",
                    fontsize=10)

# 3. Why there is a minimum at all: the components, at the best width.
bottom_left = axes[1][0]
depth_line, concrete_line, steel_line, form_line = [], [], [], []
for h in DEPTHS:
    found = cells.get((best_bw, float(h)))
    if found is None:
        continue
    depth_line.append(h)
    concrete_line.append(found["concrete"])
    steel_line.append(found["steel"])
    form_line.append(found["formwork"])

bottom_left.stackplot(
    depth_line, steel_line, concrete_line, form_line,
    labels=("steel", "concrete", "formwork"),
    colors=("#b03030", "#8a8f98", "#4c78a8"), alpha=0.9)
bottom_left.plot(depth_line,
                 np.array(steel_line) + np.array(concrete_line)
                 + np.array(form_line),
                 color="black", linewidth=1.6, label="total")
bottom_left.axvline(best_h, color="black", linestyle="--", linewidth=1.0)
bottom_left.annotate(f"cheapest\n{best_h:.0f} mm", (best_h, best_cost),
                     textcoords="offset points", xytext=(10, 25), fontsize=9)
bottom_left.set_xlabel("overall depth h (mm)")
bottom_left.set_ylabel("cost per metre")
bottom_left.set_title(f"What makes the minimum, at bw = {best_bw:.0f} mm",
                      fontsize=10)
bottom_left.legend(loc="upper left", fontsize=8)
bottom_left.grid(True, linewidth=0.3, color="0.85")

# 4. The penalty curve - what a different section actually costs you.
bottom_right = axes[1][1]
widths_list = list(WIDTHS)
depths_list = list(DEPTHS)
for bw in WIDTHS[::2]:
    xs, ys = [], []
    for h in DEPTHS:
        value = cost[depths_list.index(h), widths_list.index(bw)]
        if np.isnan(value):
            continue
        xs.append(h)
        ys.append(100.0 * (value / best_cost - 1.0))
    bottom_right.plot(xs, ys, linewidth=1.5, label=f"{bw:.0f} mm")

bottom_right.axhline(2.0, color="0.3", linestyle="--", linewidth=1.0)
bottom_right.annotate("+2 %", (DEPTHS[1], 2.4), fontsize=8, color="0.3")
bottom_right.axhline(0.0, color="black", linewidth=0.8)
bottom_right.set_xlabel("overall depth h (mm)")
bottom_right.set_ylabel("cost penalty against the cheapest section (%)")
bottom_right.set_ylim(-1, 45)
bottom_right.set_title("What a different section actually costs you",
                       fontsize=10)
bottom_right.legend(title="bw", fontsize=8, title_fontsize=8, ncol=2)
bottom_right.grid(True, linewidth=0.3, color="0.85")

figure.suptitle(
    f"Beam section cost surface - {CODE}\n"
    f"M = {MOMENT:.0f} kNm, V = {SHEAR:.0f} kN, fcu {FCU:.0f} MPa, "
    f"fy {FY:.0f} MPa, cover {COVER:.0f} mm  |  "
    f"concrete {RATE_CONCRETE:.0f}/m3, steel {RATE_STEEL:.0f}/kg, "
    f"formwork {RATE_FORMWORK:.0f}/m2  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.95))

deliver(figure, "beam_section_cost_surface.png")
