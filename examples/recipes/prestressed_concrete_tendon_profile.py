# ---
# Example:  The tendon profile and the desktop's own report, from one call
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes - 2026-09-02 - the desktop's own example reproduces its pinned punching veff triple; the report and the chart are written and re-read
# ---
# Two deliverables from one analysis:
#
#   1. A CHART of the cable profile down the member, with the force in the
#      cable at every position - which is the drawing a stressing engineer
#      works from.
#   2. THE DESKTOP'S OWN TEXT REPORT, written to a file. C02 has an input
#      for it, `report_path`, and no other engine here does.
#
# ⚠ report_path IS UNIQUE TO C02, and it is worth knowing about. Every
# other engine gives you a result dictionary and nothing else; C02 will
# additionally write the CAPTAIN.OUT report the desktop produces. On a job
# that has to hand over a calculation package, that file is the package.
#
# Uses matplotlib, bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import prokon.v5

REPORT = Path("captain_report.txt")

# The desktop program's own default example.
MODEL = dict(
    design_code="BS8110 - 1997",
    title="DEFAULT EXAMPLE",
    fcu=19.2, fy=450.0, fyv=250.0, fci=14.4,
    ec=26e6, est=206e6, density=24.0,
    top_cover=25.0, bottom_cover=25.0,
    attached_torsional_members=True, edge_beam=True,
    redistribution_pct=10.0,
    tendon_properties=[{
        "no": 1, "bond": "Unbonded", "strength": 260.7, "max_stress_pct": 80,
        "dia": 18, "area": 140, "k": 0.0015, "u": 0.05, "pullin": 5,
        "relax": 2, "est": 195e6, "min_harp_radius": 1.0,
    }],
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
                    "b2": 34, "b3": 125}]},
    ],
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
         "h_above": 3.0, "code_above": "F"},
    ],
    loads=[{"case": "D", "span": 1, "wl": 6},
           {"span": 2, "wl": 6, "p": 10, "p_pos": 2, "m": 10, "m_pos": 4},
           {"case": "L", "span": 1, "wl": 15},
           {"span": 2, "wl": 15}],
    additional_rebar=[
        {"span": 1, "pos": "T", "bars": "8Y16", "left_end": "Hook",
         "right_end": "Bend", "x": 5.0, "length": 6.0},
        {"span": 1, "pos": "B", "bars": "8Y16", "left_end": "Hook",
         "length": 8.0},
        {"span": 2, "pos": "B", "bars": "8Y16", "right_end": "Bend",
         "length": 7.0},
    ],
    punching_columns=[
        {"no": number, "slope_y": slope, "pcy": 280, "cable_type": 1,
         "nc_x": nc_x, "nc_y": [1, 1, 2, 2], "ast_x": ast_x,
         "ast_y": ast_y}
        for number, slope, nc_x, ast_x, ast_y in (
            (1, 0.05, [4, 5, 6, 7], [402, 402, 603, 804], [565] * 4),
            (2, 0.06, [5, 6, 7, 8], [942] * 4, [804] * 4),
            (3, 0.05, [4, 5, 6, 7], [402, 402, 603, 804], [565] * 4))
    ],
    report_path=str(REPORT),
)

print("TENDON PROFILE AND THE DESKTOP'S OWN REPORT")

result = prokon.v5.prestressed_concrete.analyse(**MODEL)["result"]

PINNED = (537.0024640743725, 575.0436234065779, 469.57376394972823)
measured = tuple(column["perimeters"][0]["veff"]
                 for column in result["punching"])
print(f"\n  anchor: the desktop's DEFAULT EXAMPLE, 8.0 + 7.5 m")
print(f"    perimeter-1 veff {tuple(round(v, 4) for v in measured)}")
print(f"    -> {'EXACT on the pinned triple' if measured == PINNED else 'DRIFTED'}")

# ── 1. The report file ─────────────────────────────────────────────────
if REPORT.is_file():
    raw = REPORT.read_bytes()

    # ⚠ THE REPORT IS NOT UTF-8, AND FINDING THAT OUT MATTERS. It is the
    # desktop's own output file, written in the engine's own code page. An
    # earlier version of this recipe read it as UTF-8 with
    # errors="replace" and then reported the U+FFFD replacements as
    # "non-ASCII characters in the report" - which was the READER lying
    # about the file, not the file being odd. Try the candidates in order
    # and name the one that decodes cleanly.
    text = encoding = None
    for candidate in ("ascii", "utf-8", "cp1252", "cp437"):
        try:
            text = raw.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("cp1252", errors="replace")
        encoding = "nothing cleanly - cp1252 with replacements"

    report_lines = text.splitlines()
    print(f"\n1. THE DESKTOP'S OWN REPORT")
    print(f"   {REPORT.resolve()}")
    print(f"   {len(report_lines)} line(s), {len(raw)} bytes")
    print(f"   decodes cleanly as: {encoding}")
    print(f"   first five lines:")
    for line in report_lines[:5]:
        print(f"     {line.rstrip().encode('ascii', 'replace').decode()}")
    above_ascii = sorted({character for character in text
                          if ord(character) > 127})
    print(f"   characters above ASCII: "
          f"{[hex(ord(c)) for c in above_ascii] if above_ascii else 'none'}")
    if above_ascii:
        print(f"   -> name that encoding explicitly when you read it, and")
        print(f"      fold before printing: a cp437 console dies on these.")
    else:
        print(f"   -> pure ASCII, so it prints anywhere. Do not rely on")
        print(f"      that - it is the desktop's file, not a contract.")
else:
    print(f"\n1. THE REPORT WAS NOT WRITTEN")
    print(f"   report_path was {REPORT}, and nothing is there. On a")
    print(f"   read-only working directory that is what happens, and it is")
    print(f"   silent - the analysis succeeds either way. Check for the")
    print(f"   file; do not assume it.")

# ── 2. The cable profile ───────────────────────────────────────────────
positions = result["positions"]
depths = result["cables"]["dc"]          # cable depth below the top, mm
forces = result["cables"]["pax"]         # cable force, kN

print(f"\n2. THE CABLE PROFILE")
print(f"   {len(positions)} positions over {result['ltot']:.2f} m")
print(f"   depth below the top:  {min(depths):.1f} to {max(depths):.1f} mm")
print(f"   force:                {min(forces):.1f} to {max(forces):.1f} kN")
print(f"   loss along the member: "
      f"{100 * (1 - min(forces) / max(forces)):.2f} %")

print(f"\n   {'set':>4} {'cables':>7} {'live end':>9} {'dead end':>9} "
      f"{'Pav':>9} {'stressed':>9} {'wedge kN':>9}")
for cable_set in result["cables"]["sets"]:
    print(f"   {cable_set['set']:>4} "
          f"{len(cable_set['geometry']):>7} "
          f"{cable_set['x_live']:>9.2f} {cable_set['x_dead']:>9.2f} "
          f"{cable_set['pav']:>9.1f} {cable_set['stressed_len']:>9.2f} "
          f"{cable_set['pw_force']:>9.1f}")

print(f"\n   losses: elastic {result['cables']['perc_elas']:.2f} % + "
      f"creep {result['cables']['perc_creep']:.2f} % + "
      f"shrinkage {result['cables']['perc_shrink']:.2f} % +")
print(f"           relaxation {result['cables']['perc_relax']:.2f} % + "
      f"wedge {result['cables']['perc_wedge']:.2f} %")
print(f"   long-term loss factor {result['cables']['lossf']:.6f}")

# ── Draw it ─────────────────────────────────────────────────────────────
figure, (profile, force_panel) = plt.subplots(
    2, 1, figsize=(11, 8), sharex=True,
    gridspec_kw={"height_ratios": [1.4, 1.0]})

# The member outline: the section depth at each position. C02 gives the
# section per segment, so the depth is drawn from the span_segments.
depth_at = []
walked = 0.0
for segment in MODEL["span_segments"]:
    section = next(entry for entry in MODEL["sections"]
                   if entry["name"] == segment["sec_left"])
    depth_at.append((walked, walked + segment["length"], section["d"]))
    walked += segment["length"]

for start, end, section_depth in depth_at:
    profile.add_patch(plt.Rectangle((start, -section_depth), end - start,
                                    section_depth, facecolor="0.93",
                                    edgecolor="0.5", linewidth=1.2,
                                    zorder=0))

# The cable, plotted as a depth BELOW the top - so negative on the axis.
profile.plot(positions, [-depth for depth in depths],
             color="#1f4e8c", linewidth=2.2, zorder=2,
             label="cable centroid")

support_x = [0.0]
for segment in MODEL["span_segments"]:
    support_x.append(support_x[-1] + segment["length"])
for x in support_x:
    profile.axvline(x, color="0.55", linestyle=":", linewidth=1.0)

profile.set_ylabel("depth below the top (mm)")
profile.set_title(
    f"Cable profile - {MODEL['title']}, {MODEL['design_code']}\n"
    f"{len(result['cables']['sets'])} cable set(s), "
    f"{result['cables']['pax'][0]:.0f} kN at x = 0, "
    f"{100 * (1 - result['cables']['lossf']):.2f} % long-term loss",
    fontsize=10)
profile.grid(True, linewidth=0.3, color="0.9")
profile.legend(fontsize=8, loc="lower right")

force_panel.plot(positions, forces, color="#b03030", linewidth=2.0)
force_panel.fill_between(positions, min(forces) * 0.98, forces,
                         color="#f0d6d6", alpha=0.7)
for x in support_x:
    force_panel.axvline(x, color="0.55", linestyle=":", linewidth=1.0)
force_panel.set_xlabel("position along the member (m)")
force_panel.set_ylabel("cable force (kN)")
force_panel.set_title(
    f"Cable force after losses - {min(forces):.0f} to {max(forces):.0f} kN",
    fontsize=10)
force_panel.grid(True, linewidth=0.3, color="0.9")

figure.tight_layout()
chart = Path("tendon_profile.png")
figure.savefig(chart, dpi=140)
plt.close(figure)

size = chart.stat().st_size
print(f"\nWritten: {chart.resolve()}")
print(f"  {size} bytes, "
      f"{'a real image' if size > 20_000 else 'SUSPICIOUSLY SMALL'}")

print()
print("The lower panel is the one a stressing engineer reads: the force is")
print("not constant down the member, and the difference between the two")
print("ends is friction and wedge pull-in. C02 publishes it per position, so")
print("there is no need to estimate it.")
