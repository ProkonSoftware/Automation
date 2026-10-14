# ---
# Example:  The post-tensioned floor, drawn - tendon profile, stress envelopes, design window
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes - 2026-09-04 - the desktop's own DEFAULT EXAMPLE reproduces its pinned punching veff triple; every strip in the design window measured on prokon-automation.exe
# ---
# A post-tensioned floor is designed against a band, not a limit. Too
# little prestress and the slab cracks in service; too much and it
# over-compresses at TRANSFER, when the concrete is young and none of the
# live load is there to hold it down. The answer lives between two
# surfaces, and that is exactly what a chart is for.
#
# Four panels, all off the same engine:
#
#   THE ELEVATION      the slab and the tendon profile, drawn to scale
#                      from cables["dc"] - the engine's own cable depth at
#                      each of its 140 result positions. Not a sketch.
#   THE STRESSES       the SLS extreme-fibre envelopes along the beam,
#                      with the code's permissible band shaded behind
#                      them. Where the envelope leaves the band, the slab
#                      does not work.
#   THE WINDOW         a map over (slab depth, balanced load) of how close
#                      the worst stress gets to its limit - service AND
#                      transfer together. The region inside the black
#                      contour is the design window, and the script checks
#                      the conventional "60 to 100 %" against it rather
#                      than assuming it.
#   THE DEFLECTION     the long-term deflected shape, with span/250 drawn
#                      across it.
#
# ⚠ THE STAGE THAT GOVERNS IS OFTEN TRANSFER. The window panel is drawn
# from the WORSE of the two stages at every point, and the script reports
# which one bound each cell - because a sweep that only watches service
# stresses reports a comfortable answer and a cracked soffit.
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


# -- The floor ----------------------------------------------------------
CODE = "BS8110 - 1997"
SPANS = (9.0, 11.0, 9.0)     # m
WIDTH = 3000.0               # mm of slab strip
LIVE = 3.0                   # kPa
FINISHES = 1.2               # kPa
FCU = 40.0
FCI = 30.0                   # at transfer
DEPTH = 280.0                # mm, the reference strip
BALANCED = 90.0              # % of dead load balanced, the reference
DEFLECTION_LIMIT = 250.0     # span / this

DEPTHS = np.arange(220.0, 341.0, 20.0)        # 7 mm
BALANCES = np.arange(40.0, 141.0, 10.0)       # 11 %

TENDON = {
    "no": 1, "bond": "Bonded", "strength": 260.7, "max_stress_pct": 80,
    "dia": 18, "area": 140, "k": 0.0015, "u": 0.05, "pullin": 5,
    "relax": 2, "est": 195e6, "min_harp_radius": 1.0,
}

print("THE POST-TENSIONED FLOOR, DRAWN")
print(f"  {CODE}, spans {SPANS} m, {WIDTH:.0f} mm strip")
print(f"  fcu {FCU:.0f} MPa (fci {FCI:.0f} at transfer), "
      f"{LIVE:.1f} kPa live + {FINISHES:.1f} kPa finishes")
print(f"  grid: {len(DEPTHS)} depths x {len(BALANCES)} balanced loads "
      f"= {len(DEPTHS) * len(BALANCES)} engine calls")

# -- The anchor ---------------------------------------------------------
# The desktop Captain program's own bundled example, punching columns and
# all, because that is what the pinned values were taken from.
DEFAULT = dict(
    design_code="BS8110 - 1997", title="DEFAULT EXAMPLE",
    fcu=19.2, fy=450.0, fyv=250.0, fci=14.4,
    ec=26e6, est=206e6, density=24.0,
    top_cover=25.0, bottom_cover=25.0,
    attached_torsional_members=True, edge_beam=True,
    redistribution_pct=10.0)
UNBONDED = {**TENDON, "bond": "Unbonded"}
envelope = prokon.v5.prestressed_concrete.analyse(
    **DEFAULT,
    tendon_properties=[UNBONDED],
    cable_sets=[
        {"n": 4, "prop": 1, "x_live": 0.0, "x_dead": 15.5,
         "spans": [{"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125,
                    "b2": 34, "b3": 34},
                   {"span": 2, "lo": 0.4, "ro": 0.0, "b1": 34,
                    "b2": 34, "b3": 125}]},
        {"n": 3, "prop": 1, "x_live": 15.5, "x_dead": 0.0,
         "spans": [{"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125,
                    "b2": 34, "b3": 34},
                   {"span": 2, "lo": 0.38, "ro": 0.0, "b1": 34,
                    "b2": 34, "b3": 125}]}],
    sections=[{"name": "sec1", "bw": 5000, "d": 250},
              {"name": "sec2", "bw": 5000, "d": 500},
              {"name": "sec3", "bw": 2500, "d": 500}],
    span_segments=[{"span": 1, "length": 8.0, "sec_left": "sec1"},
                   {"span": 2, "length": 7.5, "sec_left": "sec1"}],
    supports=[
        {"no": 1, "d_below": 300, "b_below": 300, "h_below": 3.0,
         "code_below": "F", "d_above": 300, "b_above": 300,
         "h_above": 3.0, "code_above": "F"},
        {"no": 2, "d_below": 300, "h_below": 3.0, "code_below": "F"},
        {"no": 3, "d_below": 300, "b_below": 300, "h_below": 3.0,
         "code_below": "F", "d_above": 300, "b_above": 300,
         "h_above": 3.0, "code_above": "F"}],
    loads=[{"case": "D", "span": 1, "wl": 6},
           {"span": 2, "wl": 6, "p": 10, "p_pos": 2, "m": 10, "m_pos": 4},
           {"case": "L", "span": 1, "wl": 15},
           {"span": 2, "wl": 15}],
    punching_columns=[
        {"no": number, "slope_y": slope, "pcy": 280, "cable_type": 1,
         "nc_x": nc_x, "nc_y": [1, 1, 2, 2], "ast_x": ast_x,
         "ast_y": ast_y}
        for number, slope, nc_x, ast_x, ast_y in (
            (1, 0.05, [4, 5, 6, 7], [402, 402, 603, 804], [565] * 4),
            (2, 0.06, [5, 6, 7, 8], [942] * 4, [804] * 4),
            (3, 0.05, [4, 5, 6, 7], [402, 402, 603, 804], [565] * 4))])
PINNED_VEFF = (537.0024640743725, 575.0436234065779, 469.57376394972823)
measured = tuple(column["perimeters"][0]["veff"]
                 for column in envelope["result"]["punching"])
print("\n  anchor: the desktop's own DEFAULT EXAMPLE, 8.0 + 7.5 m")
for number, (value, pin) in enumerate(zip(measured, PINNED_VEFF), start=1):
    print(f"    column {number} perimeter-1 veff {value!r:22} pinned {pin!r}")
print(f"    -> {'EXACT on all three' if measured == PINNED_VEFF else 'DRIFTED'}")
print(f"    engine {envelope['module']} {envelope['module_version']}")


def floor(depth=DEPTH, balanced=BALANCED):
    """One post-tensioned strip. Returns the result, or None if refused.

    ⚠ balanced_dead_load_pct AND cable_sets ARE MUTUALLY EXCLUSIVE, and
    exactly one must be supplied. The anchor above lays its cables by
    hand because that is what the pinned model does; a sweep wants the
    generated profile, which is what this does.
    """
    try:
        return prokon.v5.prestressed_concrete.analyse(
            design_code=CODE, title=f"{balanced:.0f} % balanced",
            fcu=FCU, fy=450.0, fyv=250.0, fci=FCI,
            ec=30e6, est=200e6, density=24.0,
            top_cover=30.0, bottom_cover=30.0,
            permanent_live_load_pct=25.0, creep=2.0,
            balanced_dead_load_pct=float(balanced),
            generated_profile="Parabolic",
            tendon_properties=[TENDON],
            sections=[{"name": "strip", "bw": WIDTH, "d": float(depth)}],
            span_segments=[{"span": number + 1, "length": length,
                            "sec_left": "strip"}
                           for number, length in enumerate(SPANS)],
            supports=[{"no": number + 1, "d_below": 400, "b_below": 400,
                       "h_below": 3.2, "code_below": "F"}
                      for number in range(len(SPANS) + 1)],
            loads=[row for number, _ in enumerate(SPANS) for row in (
                {"case": "D", "span": number + 1,
                 "wl": FINISHES * WIDTH / 1000.0},
                {"case": "L", "span": number + 1,
                 "wl": LIVE * WIDTH / 1000.0})])["result"]
    except prokon.v5.ProkonError:
        return None


def stages(result):
    """How close each stage gets to its own limits, as a utilisation.

    The fcc/fct limits publish in N/m2; the stresses in MPa. Compression
    is positive and tension negative, so a tension term is the magnitude
    of the most negative fibre stress.

    ⚠ A TENSION UTILISATION IS CLAMPED AT ZERO. When the whole section is
    in compression the "most tensile" fibre stress is still positive, and
    the raw ratio comes out NEGATIVE - which is not a utilisation, it is
    "there is no tension here to check". Left unclamped it also sorts
    below every real reading, so the governing stage would still be
    right; clamping just stops a negative number appearing in a column
    headed "utilisation".
    """
    sls = result["sls"]
    transfer = result["transfer"]
    limits = {
        "service compression": (max(sls["svsma"]), sls["fcc"] / 1e6),
        "service tension": (-min(sls["svsmi"]), sls["fct"] / 1e6),
        "transfer compression": (max(transfer["svtma"]),
                                 transfer["fcct"] / 1e6),
        "transfer tension": (-min(transfer["svtmi"]),
                             transfer["fctt"] / 1e6),
    }
    return {name: (max(0.0, value / limit) if limit else np.nan)
            for name, (value, limit) in limits.items()}, limits


# -- The reference strip ------------------------------------------------
reference = floor()
utilisation, limits = stages(reference)
print(f"\nTHE REFERENCE STRIP   {WIDTH:.0f} x {DEPTH:.0f} mm, "
      f"{BALANCED:.0f} % balanced")
print(f"   {'stage':>22} {'stress':>9} {'limit':>9} {'utilisation':>12}")
for name, (value, limit) in limits.items():
    print(f"   {name:>22} {value:>8.3f} MPa {limit:>8.3f} "
          f"{utilisation[name]:>12.3f}")
worst_stage = max(utilisation, key=utilisation.get)
print(f"   -> the governing stage is {worst_stage.upper()} at "
      f"{utilisation[worst_stage]:.3f}")

deflection = max(abs(value) for value in reference["deflections"]["ditot"]
                 if value is not None)
longest = max(SPANS)
print(f"   long-term deflection {deflection:.2f} mm against "
      f"span/{DEFLECTION_LIMIT:.0f} = "
      f"{longest * 1000 / DEFLECTION_LIMIT:.1f} mm"
      f"  ->  {'OK' if deflection <= longest * 1000 / DEFLECTION_LIMIT else 'EXCEEDED'}")
print(f"   cable mass {reference['quantities']['cable_mass']:.1f} kg, "
      f"rebar {reference['quantities']['main_rebar_mass']:.1f} kg over "
      f"{reference['quantities']['slab_area']:.0f} m2")

# -- The window ---------------------------------------------------------
worst = np.full((len(DEPTHS), len(BALANCES)), np.nan)
service_only = np.full_like(worst, np.nan)
binding = {}
cable_mass = np.full_like(worst, np.nan)
sag = np.full_like(worst, np.nan)
refused = 0

for row, depth in enumerate(DEPTHS):
    for column, balanced in enumerate(BALANCES):
        result = floor(depth=float(depth), balanced=float(balanced))
        if result is None:
            refused += 1
            continue
        found, _ = stages(result)
        worst[row, column] = max(found.values())
        service_only[row, column] = max(
            found["service compression"], found["service tension"])
        binding[(row, column)] = max(found, key=found.get)
        cable_mass[row, column] = result["quantities"]["cable_mass"]
        sag[row, column] = max(
            abs(value) for value in result["deflections"]["ditot"]
            if value is not None)

answered = int(np.count_nonzero(~np.isnan(worst)))
inside = (worst <= 1.0)
print(f"\nTHE DESIGN WINDOW   {answered} strips answered, {refused} refused")
print(f"   {int(np.count_nonzero(inside))} of them keep EVERY stress inside "
      f"its limit")

only_service = (service_only <= 1.0)
missed = int(np.count_nonzero(only_service & ~inside))
print("\nWATCHING ONLY THE SERVICE STAGE")
print(f"   {int(np.count_nonzero(only_service))} strips pass on service "
      f"stresses alone")
print(f"   {int(np.count_nonzero(inside))} pass once TRANSFER is included")
print(f"   -> {missed} strips would be reported as working by a sweep that")
print("      only watched the service stage. At transfer the concrete is")
print(f"      young ({FCI:.0f} MPa, not {FCU:.0f}) and the full prestress "
      f"is on with")
print("      none of the live load to balance it.")

counted = {}
for key, name in binding.items():
    counted[name] = counted.get(name, 0) + 1
print("\n   which stage governs, cell by cell:")
for name in sorted(counted, key=counted.get, reverse=True):
    print(f"     {name:>22}: {counted[name]:>3} of {answered}")

CONVENTIONAL = (60.0, 100.0)
print(f"\n   {'depth':>6}   the balanced-load range that works")
ranges = {}
for row, depth in enumerate(DEPTHS):
    working = [BALANCES[c] for c in range(len(BALANCES))
               if inside[row, c]]
    if not working:
        print(f"   {depth:>6.0f}   nothing on the grid")
        continue
    ranges[float(depth)] = (min(working), max(working), len(working))
    holes = [BALANCES[c] for c in range(len(BALANCES))
             if not inside[row, c]
             and min(working) < BALANCES[c] < max(working)]
    print(f"   {depth:>6.0f}   {min(working):.0f} % to {max(working):.0f} % "
          f"({len(working)} of {len(BALANCES)} tried)"
          + (f"   with a hole at "
             f"{', '.join(format(value, '.0f') for value in holes)} %"
             if holes else ""))

# Say only what the table says. The conventional range is a claim to be
# CHECKED here, not a conclusion to be reached.
if ranges:
    covers = sum(1 for low, high, _ in ranges.values()
                 if low <= CONVENTIONAL[0] and high >= CONVENTIONAL[1])
    highs = [high for _, high, _ in ranges.values()]
    lows = [low for low, _, _ in ranges.values()]
    print(f"   -> the conventional {CONVENTIONAL[0]:.0f} to "
          f"{CONVENTIONAL[1]:.0f} % is CONTAINED in the workable")
    print(f"      window on {covers} of the {len(ranges)} depths, and every "
          f"window runs up to")
    print(f"      {min(highs):.0f} to {max(highs):.0f} % - so on this floor "
          f"the conventional upper")
    print("      bound is conservative rather than tight, and there is real")
    print("      prestress available above it.")
    print(f"   -> the LOWER edge does NOT fall steadily with depth: "
          f"{lows[0]:.0f} % at the")
    print(f"      thinnest, {max(lows):.0f} % somewhere in the middle, "
          f"{lows[-1]:.0f} % at the thickest.")
    print("      That is the kind of thing a sweep finds and a rule of")
    print("      thumb cannot express, and it is why the window is drawn")
    print("      rather than summarised.")

# -- The cheapest strip in the window -----------------------------------
if np.any(inside):
    priced = np.where(inside, cable_mass, np.nan)
    best = np.unravel_index(np.nanargmin(priced), priced.shape)
    print(f"\n   least prestressing steel inside the window: "
          f"{DEPTHS[best[0]]:.0f} mm at {BALANCES[best[1]]:.0f} % balanced")
    print(f"     {priced[best]:.1f} kg of cable, deflection "
          f"{sag[best]:.2f} mm")

# -- The figure ---------------------------------------------------------
figure, axes = plt.subplots(2, 2, figsize=(15.5, 10))
figure.patch.set_facecolor("white")

x = np.array(reference["positions"])
support_x = [0.0]
for length in SPANS:
    support_x.append(support_x[-1] + length)

# 1. The elevation, with the real tendon profile.
elevation = axes[0][0]
elevation.fill_between(x, 0, -DEPTH, color="0.88", edgecolor="0.4",
                       linewidth=1.2)
elevation.plot(x, [-value for value in reference["cables"]["dc"]],
               color="#b03030", linewidth=2.4, label="tendon centroid")
for position in support_x:
    elevation.plot([position - 0.2, position + 0.2], [-DEPTH, -DEPTH],
                   color="black", linewidth=3)
    elevation.plot([position], [-DEPTH - 40], marker="^", markersize=10,
                   color="0.3")
elevation.set_ylim(-DEPTH - 90, 40)
elevation.set_xlabel("position along the strip (m)")
elevation.set_ylabel("mm below the top surface")
elevation.set_title(f"The strip in elevation, {WIDTH:.0f} x {DEPTH:.0f} mm - "
                    f"the tendon profile is\nthe engine's own cables['dc'], "
                    f"one value per result position", fontsize=10)
elevation.legend(fontsize=8, loc="lower right")
elevation.grid(True, linewidth=0.3, color="0.9")

# 2. The stress envelopes against the permissible band.
stress = axes[0][1]
sls = reference["sls"]
transfer = reference["transfer"]
compression = sls["fcc"] / 1e6
tension = -sls["fct"] / 1e6
stress.axhspan(tension, compression, color="#59a14f", alpha=0.12,
               label="service permissible band")
stress.axhline(compression, color="#2d6a26", linestyle="--", linewidth=1.4)
stress.axhline(tension, color="#2d6a26", linestyle="--", linewidth=1.4)
stress.plot(x, sls["svsma"], color="#1f4e79", linewidth=1.8,
            label="service, max fibre")
stress.plot(x, sls["svsmi"], color="#4c78a8", linewidth=1.8,
            label="service, min fibre")
stress.plot(x, transfer["svtma"], color="#e0a030", linewidth=1.4,
            linestyle=":", label="transfer, max fibre")
stress.plot(x, transfer["svtmi"], color="#c07000", linewidth=1.4,
            linestyle=":", label="transfer, min fibre")
stress.axhline(0, color="black", linewidth=0.8)
for position in support_x:
    stress.axvline(position, color="0.7", linewidth=0.8, linestyle=":")
stress.set_xlabel("position along the strip (m)")
stress.set_ylabel("extreme fibre stress (MPa, compression +)")
stress.set_title(f"Stress envelopes at {BALANCED:.0f} % balanced\n"
                 f"the green band is the code's own permissible range",
                 fontsize=10)
stress.legend(fontsize=7.5, ncol=2)
stress.grid(True, linewidth=0.3, color="0.9")

# 3. The window.
window = axes[1][0]
mesh_b, mesh_d = np.meshgrid(BALANCES, DEPTHS)
shade = window.contourf(mesh_b, mesh_d, worst, levels=20, cmap="RdYlGn_r",
                        vmin=0.3, vmax=1.7)
figure.colorbar(shade, ax=window,
                label="worst stress / its limit (service AND transfer)")
edge = window.contour(mesh_b, mesh_d, worst, levels=[1.0], colors="black",
                      linewidths=2.8)
window.clabel(edge, fmt={1.0: "all stages"}, fontsize=9)
service_edge = window.contour(mesh_b, mesh_d, service_only, levels=[1.0],
                              colors="blue", linewidths=2.0,
                              linestyles="--")
window.clabel(service_edge,
              fmt={1.0: "service only"}, fontsize=8)
window.plot(BALANCED, DEPTH, marker="*", markersize=20, color="white",
            markeredgecolor="black", zorder=6)
window.set_xlabel("dead load balanced (%)")
window.set_ylabel("slab depth (mm)")
window.set_title(
    "The design window: inside the BLACK contour every stage passes.\n"
    "The blue dashes are the bigger, WRONG window you get from the\n"
    "service stage alone.", fontsize=10)

# 4. The deflected shape.
shape = axes[1][1]
total = [value if value is not None else np.nan
         for value in reference["deflections"]["ditot"]]
elastic = [value if value is not None else np.nan
           for value in reference["deflections"]["demax"]]
shape.plot(x, total, color="#8b3ea8", linewidth=2.0,
           label="long-term total")
shape.plot(x, elastic, color="#8b3ea8", linewidth=1.0, linestyle="--",
           label="elastic")
limit = longest * 1000.0 / DEFLECTION_LIMIT
shape.axhline(limit, color="red", linestyle="--", linewidth=1.4,
              label=f"longest span / {DEFLECTION_LIMIT:.0f}")
shape.axhline(0, color="black", linewidth=0.8)
for position in support_x:
    shape.axvline(position, color="0.7", linewidth=0.8, linestyle=":")
shape.invert_yaxis()           # downward deflection drawn downwards
shape.set_xlabel("position along the strip (m)")
shape.set_ylabel("deflection (mm, down positive)")
shape.set_title("The long-term deflected shape\n"
                "prestress lifts the slab; creep puts it back",
                fontsize=10)
shape.legend(fontsize=8)
shape.grid(True, linewidth=0.3, color="0.9")

figure.suptitle(
    f"Post-tensioned floor strip - {CODE}\n"
    f"spans {SPANS} m, {WIDTH:.0f} mm wide, fcu {FCU:.0f} MPa "
    f"(fci {FCI:.0f} at transfer), {LIVE:.1f} kPa live + "
    f"{FINISHES:.1f} kPa finishes, bonded tendons, creep 2.0  |  "
    f"engine {envelope['module_version']}",
    fontsize=10)
figure.tight_layout(rect=(0, 0, 1, 0.93))

deliver(figure, "prestressed_concrete_stress_window.png")
