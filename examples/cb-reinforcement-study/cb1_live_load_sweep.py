# ---
# Example:  CB1 live-load sweep - required reinforcement, two design codes
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes - 2026-09-18 - CB1.C01 and CB2.C01 differ ONLY in the loads they store (live 10 against 50 kN/m) and this script discards stored loads, so the two must give IDENTICAL results - measured 2026-09-18, stored loads differ and every envelope comes back identical, which makes the pair a control that can respond rather than a coincidence; the anchor reproduces its pinned values; every sweep point measured on prokon-automation.exe
# ---
"""
CB1 live-load sweep — required reinforcement, two design codes.

Reads the continuous-beam LAYOUT from CB1.C01 (sections, segments, supports and
the material / analysis settings), DISCARDS the loads the file carries, and
re-analyses the same beam under a live load that sweeps from 0 to 100 kN/m.

Load model
----------
* Dead load            : zero (no dead-load rows are applied).
* Self-weight          : off, via concrete_density = 0 kN/m3.
* Live load            : uniformly distributed, kN/m, applied over the FULL
                         length of every span, the only thing that varies.

Design codes: SABS 0100 - 2000 and SANS 51992-1-1:2025.

Output
------
Figure 1 : 12 plots — 6 pairs, one pair per live load (0, 20, 40, 60, 80,
           100 kN/m), the pairs stacked horizontally from lowest to highest.
           Each pair is required SHEAR reinforcement above required BENDING
           reinforcement. Both design codes are drawn on every pair.
Figure 2 : 6 3D surfaces — required shear, required BOTTOM bending and
           required TOP bending reinforcement against (position along the
           beam, live load), one surface per quantity per code, over 0 to
           100 kN/m in 10 kN/m steps. Stacked horizontally: one column per
           quantity, one row per design code.

Engine result fields used (units per the PROKON continuous-beam reference)
-------------------------------------------------------------------------
    envelopes["position"]      m       distance from the LEFT END of the beam
    envelopes["asv_required"]  mm2/mm  required links Asv/sv  (x1000 -> mm2/m)
    envelopes["ast_bottom"]    mm2     required bottom (sagging) steel
    envelopes["ast_top"]       mm2     required top (hogging) steel

The "*_provided" envelopes are deliberately NOT read: bar detailing is not
exposed in this version, so they do not mean what their names suggest.
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np

import prokon.v5

# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------

# The layout file. Defaults to CB1.C01 sitting beside this script.
_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
DATA_FILE = os.path.join(_HERE, "CB1.C01")

DESIGN_CODES = ("SABS 0100 - 2000", "SANS 51992-1-1:2025")

# Fine sweep, used for the 3D surfaces: 0 .. 100 kN/m in 10 kN/m steps.
LIVE_LOADS_FINE = list(range(0, 101, 10))

# Coarse sweep, used for the 6 paired plots: 0 .. 100 kN/m in 20 kN/m steps.
# A subset of the fine sweep, so no analysis is run twice.
LIVE_LOADS_PAIRS = list(range(0, 101, 20))

CODE_COLOUR = {"SABS 0100 - 2000": "tab:blue", "SANS 51992-1-1:2025": "tab:orange"}

SAVE_PNG = True  # also write the two figures beside this script


# --------------------------------------------------------------------------
# Read the layout, drop the file's loads
# --------------------------------------------------------------------------

def read_layout(path):
    """Return the .C01 inputs as analyse() keyword arguments, with the file's
    loads removed and self-weight suppressed."""
    loaded = prokon.v5.continuous_beam.load_file(path=path)["result"]
    layout = dict(loaded["inputs"])

    layout.pop("loads", None)        # ignore the loads stored in the file
    layout["concrete_density"] = 0   # no self-weight

    # analyse() takes the table inputs as JSON strings; load_file hands them
    # back as Python lists, so re-encode them.
    for key in ("sections", "segments", "supports"):
        layout[key] = json.dumps(layout[key])

    return layout, loaded["title"]


def span_lengths(layout):
    """Span lengths in m, summed from the segments (a span can be built from
    several segments: span == 0 continues the previous one)."""
    lengths = []
    for seg in json.loads(layout["segments"]):
        if seg["span"] == 0:
            lengths[-1] += seg["length"]
        else:
            lengths.append(seg["length"])
    return lengths


def uniform_live_load(n_spans, w):
    """Live load of w kN/m over the whole of every span, as the loads input."""
    return json.dumps([{"case": "Live", "span": s, "w_left": float(w)}
                       for s in range(1, n_spans + 1)])


# --------------------------------------------------------------------------
# Run the sweep
# --------------------------------------------------------------------------

def run_sweep(layout, n_spans, codes, live_loads):
    """Analyse every (code, live load) combination.

    Returns (position, results) where position is the common x-grid in m and
    results[(code, w)] is a dict of the reinforcement envelopes.
    """
    results = {}
    position = None

    for code in codes:
        for w in live_loads:
            inputs = dict(layout)
            inputs["design_code"] = code
            inputs["loads"] = uniform_live_load(n_spans, w)

            env = prokon.v5.continuous_beam.analyse(**inputs)["result"]["envelopes"]

            x = np.asarray(env["position"], dtype=float)
            if position is None:
                position = x
            elif not np.array_equal(x, position):
                # Every run shares one geometry, so the output stations must
                # match. If they ever did not, the 3D mesh below would be
                # silently wrong -- so refuse instead of plotting nonsense.
                raise RuntimeError(
                    "position grid changed between runs ({} kN/m, {})".format(w, code))

            results[(code, w)] = {
                # mm2/mm -> mm2/m, the unit links are normally quoted in
                "asv": np.asarray(env["asv_required"], dtype=float) * 1000.0,
                "ast_bottom": np.asarray(env["ast_bottom"], dtype=float),
                "ast_top": np.asarray(env["ast_top"], dtype=float),
            }
            print("  analysed  {:<20s}  live load {:3d} kN/m".format(code, w))

    return position, results


# --------------------------------------------------------------------------
# Figure 1 -- 6 pairs, horizontally stacked
# --------------------------------------------------------------------------

def plot_pairs(position, results, codes, live_loads, support_x, title):
    n = len(live_loads)
    fig, axes = plt.subplots(2, n, figsize=(4.0 * n, 8.0), sharex=True,
                             sharey="row", constrained_layout=True)

    for col, w in enumerate(live_loads):
        ax_shear, ax_bend = axes[0, col], axes[1, col]

        for code in codes:
            data = results[(code, w)]
            colour = CODE_COLOUR[code]
            ax_shear.plot(position, data["asv"], color=colour, lw=1.4, label=code)
            ax_bend.plot(position, data["ast_bottom"], color=colour, lw=1.4,
                         label="{} — bottom".format(code))
            ax_bend.plot(position, data["ast_top"], color=colour, lw=1.4, ls="--",
                         label="{} — top".format(code))

        ax_shear.set_title("Live load {} kN/m".format(w), fontsize=11)
        for ax in (ax_shear, ax_bend):
            for sx in support_x:
                ax.axvline(sx, color="0.75", lw=0.8, zorder=0)
            ax.grid(True, alpha=0.3)
        ax_bend.set_xlabel("Position along beam (m)")

        if col == 0:
            ax_shear.set_ylabel("Required shear reinforcement\n$A_{sv}/s_v$ (mm²/m)")
            ax_bend.set_ylabel("Required bending reinforcement\n$A_{st}$ (mm²)")
            ax_shear.legend(fontsize=8, loc="upper center")
            ax_bend.legend(fontsize=7, loc="upper center")

    fig.suptitle("{} — required reinforcement against live load "
                 "(dead load 0, self-weight off)".format(title), fontsize=14)
    return fig


# --------------------------------------------------------------------------
# Figure 2 -- 6 3D surfaces
# --------------------------------------------------------------------------

def plot_surfaces(position, results, codes, live_loads, title):
    loads = np.asarray(live_loads, dtype=float)
    mesh_x, mesh_y = np.meshgrid(position, loads)

    # One surface per (quantity, code). Bottom and top bending steel are kept
    # apart rather than summed: they peak in different places along the beam --
    # bottom at midspan, top over the interior support -- so one combined
    # surface would hide both shapes.
    surfaces = {}
    for code in codes:
        for quantity, key in (("shear", "asv"),
                              ("bending_bottom", "ast_bottom"),
                              ("bending_top", "ast_top")):
            surfaces[(quantity, code)] = np.vstack(
                [results[(code, w)][key] for w in live_loads])

    # (key, column header, z-axis label, colour map). The header names the
    # quantity once at the top of its column, so the z label carries only the
    # symbol and unit rather than repeating the words six times.
    quantities = (
        ("shear", "Required shear reinforcement", "$A_{sv}/s_v$ (mm²/m)", "viridis"),
        ("bending_bottom", "Required BOTTOM bending reinforcement", "$A_{st}$ (mm²)", "plasma"),
        ("bending_top", "Required TOP bending reinforcement", "$A_{st}$ (mm²)", "cividis"),
    )

    # One colour and height scale per quantity, so a quantity's column compares
    # the two codes directly. Computed up front because the quantity is now the
    # COLUMN, so the loop meets a quantity once per code rather than once.
    zmax = {}
    for quantity, _, _, _ in quantities:
        top = max(surfaces[(quantity, c)].max() for c in codes)
        zmax[quantity] = top if top > 0 else 1.0

    # The quantities are stacked HORIZONTALLY: one column per quantity, one row
    # per design code. The code is named once down the far left and the
    # quantity once along the top, instead of a title on every panel.
    fig = plt.figure(figsize=(20.0, 11.0))
    grid = []
    panel = 1
    for code in codes:
        row = []
        for quantity, _, zlabel, cmap in quantities:
            ax = fig.add_subplot(len(codes), len(quantities), panel, projection="3d")
            ax.plot_surface(mesh_x, mesh_y, surfaces[(quantity, code)],
                            cmap=cmap, vmin=0.0, vmax=zmax[quantity],
                            rstride=1, cstride=1, linewidth=0, antialiased=True)
            ax.set_xlabel("Position along beam (m)")
            ax.set_ylabel("Live load (kN/m)")
            ax.set_zlabel(zlabel, fontsize=9)
            ax.set_zlim(0.0, zmax[quantity] * 1.05)
            ax.view_init(elev=28, azim=-125)
            row.append(ax)
            panel += 1
        grid.append(row)

    fig.suptitle("{} — required reinforcement against position and live load"
                 .format(title), fontsize=15)
    # tight_layout leaves 3D axes badly boxed, so set the margins directly.
    # The left margin is wide enough for the design-code labels.
    fig.subplots_adjust(left=0.055, right=0.99, bottom=0.02, top=0.91,
                        wspace=0.04, hspace=0.06)

    # Headers and row labels are placed from the axes' OWN boxes, and only
    # after subplots_adjust, because that call is what finally fixes where each
    # box sits. Reading the boxes rather than hard-coding figure coordinates
    # means the labels follow the grid if the margins or the panel count change.
    for col, (_, header, _, _) in enumerate(quantities):
        box = grid[0][col].get_position()
        fig.text(0.5 * (box.x0 + box.x1), box.y1, header,
                 ha="center", va="bottom", fontsize=13)
    for row_index, code in enumerate(codes):
        box = grid[row_index][0].get_position()
        fig.text(0.018, 0.5 * (box.y0 + box.y1), code,
                 ha="center", va="center", rotation=90, fontsize=14)

    return fig


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# The anchor
# --------------------------------------------------------------------------

# ⭐ CB1.C01 AND CB2.C01 ARE A CONTROL, AND IT IS THE ONE THIS SCRIPT NEEDS.
# The two files differ ONLY in the loads they store - live 10 kN/m against
# 50 kN/m - and this script DISCARDS stored loads and applies its own. So the
# two must produce identical envelopes, and because they differ in exactly the
# thing being questioned, agreement is evidence rather than a coincidence.
# Measured 2026-09-18: the stored loads do differ, and the position grid, asv,
# ast_bottom and ast_top all come back identical.
#
# The pins are the other half. The control proves the loads are discarded; the
# pins prove the numbers have not moved since. Neither alone is enough - a
# script that ignored the file entirely would pass the control, and a script
# that read the wrong file would pass the pins.
ANCHOR_CODE = "SABS 0100 - 2000"
ANCHOR_LIVE = 50
CONTROL_FILE = "CB2.C01"

PINNED = (691.3290179583561,     # max asv         mm2/m
          887.6884486166392,     # max ast_bottom  mm2
          867.9810867721185)     # max ast_top     mm2


def anchor_maxima(filename):
    """The three envelope maxima for one layout file, at the anchor point."""
    layout, _ = read_layout(os.path.join(_HERE, filename))
    n_spans = len(span_lengths(layout))
    _, results = run_sweep(layout, n_spans, (ANCHOR_CODE,), (ANCHOR_LIVE,))
    env = results[(ANCHOR_CODE, ANCHOR_LIVE)]
    return (float(np.max(env["asv"])),
            float(np.max(env["ast_bottom"])),
            float(np.max(env["ast_top"])))


def anchor_check():
    """Run the anchor and its control, and say plainly whether both held."""
    measured = anchor_maxima(os.path.basename(DATA_FILE))
    control = anchor_maxima(CONTROL_FILE)

    print("\n  anchor: {} at {} kN/m live".format(ANCHOR_CODE, ANCHOR_LIVE))
    for label, value, pin in zip(("max asv", "max ast_bottom", "max ast_top"),
                                 measured, PINNED):
        print("    {:<16s} {!r:22} pinned {!r}".format(label, value, pin))
    print("    -> {}".format(
        "EXACT on all three" if measured == PINNED else "DRIFTED"))
    print("    control: {} stores different loads and must give the same answer"
          .format(CONTROL_FILE))
    print("    -> {}".format(
        "IDENTICAL - the stored loads really are discarded" if control == measured
        else "DRIFTED - the stored loads are NOT being discarded"))


def main():
    layout, title = read_layout(DATA_FILE)
    lengths = span_lengths(layout)
    n_spans = len(lengths)
    support_x = np.concatenate(([0.0], np.cumsum(lengths)))

    print("Layout read from {}".format(DATA_FILE))
    print("  title      : {}".format(title))
    print("  spans      : {}  ({} m, total {} m)".format(
        n_spans, " + ".join(str(L) for L in lengths), sum(lengths)))
    print("  loads from the file are ignored; dead load 0, self-weight off")
    print("Running {} analyses...".format(len(DESIGN_CODES) * len(LIVE_LOADS_FINE)))

    anchor_check()

    position, results = run_sweep(layout, n_spans, DESIGN_CODES, LIVE_LOADS_FINE)

    fig_pairs = plot_pairs(position, results, DESIGN_CODES, LIVE_LOADS_PAIRS,
                           support_x, title)
    fig_surfaces = plot_surfaces(position, results, DESIGN_CODES,
                                 LIVE_LOADS_FINE, title)

    if SAVE_PNG:
        for fig, name in ((fig_pairs, "cb1_reinforcement_pairs.png"),
                          (fig_surfaces, "cb1_reinforcement_surfaces.png")):
            out = os.path.join(_HERE, name)
            fig.savefig(out, dpi=130)
            print("Saved {}".format(out))

    plt.show()


if __name__ == "__main__":
    main()
