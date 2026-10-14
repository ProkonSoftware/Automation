# ---
# Example:  CB1 - total tonnage of reinforcing steel against live load
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes - 2026-09-18 - CB1.C01 and CB2.C01 differ ONLY in the loads they store (live 10 against 50 kN/m) and this script discards stored loads, so the two must give IDENTICAL results - measured 2026-09-18, stored loads differ and every envelope comes back identical, which makes the pair a control that can respond rather than a coincidence; the anchor reproduces its pinned values; every sweep point measured on prokon-automation.exe; the link length is pinned too, being the one number that would move if the layout were read wrongly while the analysis still succeeded
# ---
"""
CB1 - total tonnage of reinforcing steel against live load, two design codes.

Reads the continuous-beam LAYOUT from CB1.C01 (sections, segments, supports and
the material / analysis settings), DISCARDS the loads the file carries, and
re-analyses the same beam under a live load that sweeps from 0 to 100 kN/m in
5 kN/m steps, to SABS 0100 - 2000 and to SANS 51992-1-1:2025.

Load model
----------
* Dead load    : zero - no dead-load rows are applied.
* Self-weight  : off, via concrete_density = 0 kN/m3.
* Live load    : uniformly distributed, kN/m, over the FULL length of every
                 span. The only thing that varies.

Everything else - section, spans, supports, fcu/fy/fyv, covers, the load
factors, redistribution, creep and shrinkage - is taken from the file and left
alone, so the two codes are compared on one identical beam.

Output
------
One figure, one set of axes:

    total tonnage of steel required  (t)   vs   live load  (kN/m)

with one colour per design code, so the two are read off directly.
Solid line  = total steel   (longitudinal + shear links)
Dashed line = the longitudinal (bending) part of that total, same colour, so
              the link contribution is visible rather than buried.

How the tonnage is obtained
---------------------------
The engine publishes reinforcement as envelopes along the beam. For each live
load the area under those curves is integrated along the beam length
(trapezium rule) to give a steel VOLUME, which is multiplied by the steel
density to give a mass.

  longitudinal   ast[mm2] integrated over x[m]  ->  mm2.m  ->  m3 directly.
  shear links    asv_required is Asv/sv in mm2/mm - an area per unit length of
                 beam, not an area. Integrating it alone gives mm2, not a
                 volume. It becomes a volume only when multiplied by the
                 developed length of one link, LINK_LENGTH below, which is
                 derived from the section and cover read from the file.

At every station the steel taken is the GREATER of the computed requirement
and the code's own nominal minimum - that is the steel that must actually be
placed, and it is why the 0 kN/m end of the graph is not zero. The two codes
impose different minima, which is part of what is being compared.

Engine result fields used (units per the PROKON continuous-beam reference)
--------------------------------------------------------------------------
    envelopes["position"]            m       distance from the beam's left end
    envelopes["ast_bottom"]          mm2     computed bottom (sagging) steel
    envelopes["ast_bottom_nominal"]  mm2     code minimum bottom steel
    envelopes["ast_top"]             mm2     computed top (hogging) steel
    envelopes["ast_top_nominal"]     mm2     code minimum top steel
    envelopes["asv_required"]        mm2/mm  computed links, Asv/sv
    envelopes["asv_nominal"]         mm2/mm  code minimum links, Asv/sv

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

_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()


def _find(name):
    """The named file, looked for beside this script and then in the working
    directory. Says which places it looked rather than failing inside the
    engine with a path the caller never typed."""
    for folder in (_HERE, os.getcwd()):
        candidate = os.path.join(folder, name)
        if os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(
        "{} is not beside this script ({}) nor in the working directory ({})"
        .format(name, _HERE, os.getcwd()))


DATA_FILE = _find("CB2.C01")

DESIGN_CODES = ("SABS 0100 - 2000", "SANS 51992-1-1:2025")
CODE_COLOUR = {"SABS 0100 - 2000": "tab:blue", "SANS 51992-1-1:2025": "tab:red"}

# Live load sweep: 0 to 100 kN/m in 5 kN/m steps.
LIVE_LOADS = list(range(0, 101, 5))

# Reinforcing steel density, kg/m3.
STEEL_DENSITY = 7850.0

# Added to the link's centre-line perimeter for the two hooks, mm. The engine
# publishes Asv/sv only, so the bar diameter and bend detail are not known
# here; this is a stated detailing allowance, not an engine output.
LINK_HOOK_ALLOWANCE = 150.0

SAVE_PNG = True


# --------------------------------------------------------------------------
# numpy compatibility: trapz was renamed trapezoid in numpy 2.0 and the old
# name has since been removed, so neither name alone is safe.
# --------------------------------------------------------------------------

_integrate = getattr(np, "trapezoid", None) or np.trapz


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


def link_length(layout):
    """Developed length of one shear link, mm.

    Taken as the centre-line perimeter of a closed rectangular link plus a hook
    allowance. The link centre line is placed at the cover read from the file,
    which is cover to the CENTRE of the main reinforcement - the link sits a
    little outside that, so this is a slight under-estimate.

    Refuses a non-prismatic beam rather than quietly using one section's
    geometry for the whole length: with a haunch or a section change the link
    length varies along the beam and a single number would be wrong.
    """
    by_number = {sec["n"]: sec for sec in json.loads(layout["sections"])}
    used = {seg[key] for seg in json.loads(layout["segments"])
            for key in ("sec_left", "sec_right") if seg.get(key)}

    shapes = {(by_number[n]["bw"], by_number[n]["d"]) for n in used}
    if len(shapes) != 1:
        raise RuntimeError(
            "this script computes ONE link length and so needs a prismatic beam, "
            "but the segments use {} different section shapes: {}. Extend "
            "link_length() to vary the link length along the beam before using "
            "it on this file.".format(len(shapes), sorted(shapes)))

    bw, h = shapes.pop()
    cover = 0.5 * (float(layout["cover_top"]) + float(layout["cover_bot"]))
    return 2.0 * ((bw - 2.0 * cover) + (h - 2.0 * cover)) + LINK_HOOK_ALLOWANCE


def uniform_live_load(n_spans, w):
    """Live load of w kN/m over the whole of every span, as the loads input."""
    return json.dumps([{"case": "Live", "span": s, "w_left": float(w)}
                       for s in range(1, n_spans + 1)])


# --------------------------------------------------------------------------
# Run the sweep, and turn each envelope into a mass
# --------------------------------------------------------------------------

def steel_masses(env, link_mm):
    """Mass of steel the beam requires, in tonnes, from one analysis.

    Returns (bending_t, links_t). At every station the steel taken is the
    greater of the computed requirement and the code's nominal minimum.
    """
    x = np.asarray(env["position"], dtype=float)                                # m

    ast = (np.maximum(np.asarray(env["ast_bottom"], dtype=float),
                      np.asarray(env["ast_bottom_nominal"], dtype=float))
           + np.maximum(np.asarray(env["ast_top"], dtype=float),
                        np.asarray(env["ast_top_nominal"], dtype=float)))       # mm2
    asv = np.maximum(np.asarray(env["asv_required"], dtype=float),
                     np.asarray(env["asv_nominal"], dtype=float))               # mm2/mm

    # mm2 integrated over m -> mm2.m ; 1 mm2.m = 1e-6 m3
    bending_m3 = _integrate(ast, x) * 1.0e-6

    # (mm2/mm) integrated over m: multiply by 1000 mm/m to integrate over mm,
    # then by the link's developed length in mm, giving mm3; 1 mm3 = 1e-9 m3.
    links_m3 = _integrate(asv, x) * 1000.0 * link_mm * 1.0e-9

    return (bending_m3 * STEEL_DENSITY / 1000.0,
            links_m3 * STEEL_DENSITY / 1000.0)


def run_sweep(layout, n_spans, link_mm, codes, live_loads):
    """Analyse every (code, live load) combination.

    Returns tonnage[code] = (bending_t array, links_t array), aligned to
    live_loads.
    """
    tonnage = {}
    station_count = None

    for code in codes:
        bending, links = [], []
        for w in live_loads:
            inputs = dict(layout)
            inputs["design_code"] = code
            inputs["loads"] = uniform_live_load(n_spans, w)

            env = prokon.v5.continuous_beam.analyse(**inputs)["result"]["envelopes"]

            # Every run shares one geometry, so the output stations must match.
            # If they ever did not, the integrals would be comparing different
            # discretisations - so refuse rather than plot nonsense.
            if station_count is None:
                station_count = len(env["position"])
            elif len(env["position"]) != station_count:
                raise RuntimeError(
                    "station count changed between runs ({} kN/m, {}): {} vs {}"
                    .format(w, code, len(env["position"]), station_count))

            b, s = steel_masses(env, link_mm)
            bending.append(b)
            links.append(s)
            print("  analysed  {:<20s}  live load {:3d} kN/m   "
                  "bending {:6.3f} t   links {:6.3f} t   total {:6.3f} t"
                  .format(code, w, b, s, b + s))

        tonnage[code] = (np.asarray(bending), np.asarray(links))

    return tonnage


# --------------------------------------------------------------------------
# The graph
# --------------------------------------------------------------------------

def plot_tonnage(tonnage, codes, live_loads, link_mm, title, source):
    loads = np.asarray(live_loads, dtype=float)
    fig, ax = plt.subplots(figsize=(11.0, 7.0), constrained_layout=True)

    for code in codes:
        bending, links = tonnage[code]
        colour = CODE_COLOUR[code]
        ax.plot(loads, bending + links, color=colour, lw=2.0, marker="o", ms=4.5,
                label="{} - total (bending + links)".format(code))
        ax.plot(loads, bending, color=colour, lw=1.2, ls="--", alpha=0.85,
                label="{} - bending only".format(code))

    ax.set_xlabel("Live load applied to every span (kN/m)")
    ax.set_ylabel("Total reinforcing steel required (tonnes)")
    # The file name and the title STORED in that file are both shown. They can
    # disagree - CB2.C01 carries the stored title "CB1" - so naming only one of
    # them would leave the reader unsure which beam the figure is of.
    ax.set_title("{} - steel tonnage against live load\n"
                 "layout from {} (stored title \"{}\"), "
                 "dead load 0, self-weight off"
                 .format(os.path.splitext(source)[0], source, title), fontsize=13)
    ax.set_xlim(loads.min(), loads.max())
    ax.set_ylim(bottom=0.0)
    ax.set_xticks(loads[::2])
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=9)

    ax.text(0.99, 0.02,
            "steel density {:.0f} kg/m³   ·   link developed length {:.0f} mm\n"
            "steel = max(computed requirement, code nominal minimum) at every station"
            .format(STEEL_DENSITY, link_mm),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            color="0.35",
            bbox=dict(boxstyle="round,pad=0.4", fc="0.96", ec="0.8"))

    return fig


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# The anchor
# --------------------------------------------------------------------------

# ⭐ THE SAME CONTROL AS ITS SIBLING, AND FOR THE SAME REASON. CB1.C01 and
# CB2.C01 differ ONLY in the loads they store, which this script discards, so
# the tonnages must be identical. Measured 2026-09-18: they are, to the last
# bit, and the stored loads do differ - so the agreement is about the discard
# rather than about two identical files.
#
# The link length is pinned beside the tonnages deliberately: it is derived
# from the section and cover read from the FILE plus a stated hook allowance,
# so it is the one number here that would move if the layout were read wrongly
# while the analysis still succeeded.
ANCHOR_CODE = "SABS 0100 - 2000"
ANCHOR_LIVE = 50
CONTROL_FILE = "CB2.C01"

PINNED_LINK_MM = 1630.0
PINNED_TONNES = (0.07000780103745105,    # bending
                 0.07780289381930802)    # links


def anchor_tonnage(filename):
    """The link length and the two tonnages for one layout, at the anchor point."""
    layout, _ = read_layout(os.path.join(_HERE, filename))
    n_spans = len(span_lengths(layout))
    link_mm = link_length(layout)
    tonnage = run_sweep(layout, n_spans, link_mm, (ANCHOR_CODE,), (ANCHOR_LIVE,))
    bending, links = tonnage[ANCHOR_CODE]
    return float(link_mm), (float(bending[0]), float(links[0]))


def anchor_check():
    """Run the anchor and its control, and say plainly whether both held."""
    link_mm, measured = anchor_tonnage(os.path.basename(DATA_FILE))
    control_link, control = anchor_tonnage(CONTROL_FILE)

    print("\n  anchor: {} at {} kN/m live".format(ANCHOR_CODE, ANCHOR_LIVE))
    print("    link length      {!r:22} pinned {!r}".format(link_mm, PINNED_LINK_MM))
    for label, value, pin in zip(("bending t", "links t"), measured, PINNED_TONNES):
        print("    {:<16s} {!r:22} pinned {!r}".format(label, value, pin))
    print("    -> {}".format(
        "EXACT on all three" if (link_mm, measured) == (PINNED_LINK_MM, PINNED_TONNES)
        else "DRIFTED"))
    print("    control: {} stores different loads and must give the same answer"
          .format(CONTROL_FILE))
    print("    -> {}".format(
        "IDENTICAL - the stored loads really are discarded"
        if (control_link, control) == (link_mm, measured)
        else "DRIFTED - the stored loads are NOT being discarded"))


def main():
    layout, title = read_layout(DATA_FILE)
    lengths = span_lengths(layout)
    n_spans = len(lengths)
    link_mm = link_length(layout)

    print("Layout read from {}".format(DATA_FILE))
    print("  title      : {}".format(title))
    print("  spans      : {}  ({} m, total {} m)".format(
        n_spans, " + ".join(str(L) for L in lengths), sum(lengths)))
    print("  sections   : {}".format(layout["sections"]))
    print("  link length: {:.0f} mm (centre-line perimeter + {:.0f} mm hooks)"
          .format(link_mm, LINK_HOOK_ALLOWANCE))
    print("  loads from the file are ignored; dead load 0, self-weight off")
    print("Running {} analyses...".format(len(DESIGN_CODES) * len(LIVE_LOADS)))

    anchor_check()

    tonnage = run_sweep(layout, n_spans, link_mm, DESIGN_CODES, LIVE_LOADS)

    print("\nSteel required, tonnes")
    header = "  live load |"
    for code in DESIGN_CODES:
        header += "  {:^24s}|".format(code)
    print(header)
    print("     (kN/m) |" + "  bending  links  total  |" * len(DESIGN_CODES))
    print("  " + "-" * (11 + 26 * len(DESIGN_CODES)))
    for i, w in enumerate(LIVE_LOADS):
        row = "  {:9d} |".format(w)
        for code in DESIGN_CODES:
            b, s = tonnage[code][0][i], tonnage[code][1][i]
            row += "   {:6.3f} {:6.3f} {:6.3f}  |".format(b, s, b + s)
        print(row)

    source = os.path.basename(DATA_FILE)
    fig = plot_tonnage(tonnage, DESIGN_CODES, LIVE_LOADS, link_mm, title, source)

    if SAVE_PNG:
        # Named after the file actually read, so a run against another layout
        # cannot overwrite the previous one's figure.
        out = os.path.join(_HERE, "{}_steel_tonnage_vs_live_load.png"
                           .format(os.path.splitext(source)[0].lower()))
        fig.savefig(out, dpi=140)
        print("\nSaved {}".format(out))

    plt.show()


# The plain "__main__" guard is not enough on its own. Measured: PROKON's
# prokon_run_script executes the file with __name__ == "" , so a script guarded
# only on "__main__" runs nothing and exits 0 with no output - a silent pass.
# Both names are accepted so the script behaves the same run as a file, run
# from Spyder, and run through the MCP scripting tool.
if __name__ in ("__main__", ""):
    main()
