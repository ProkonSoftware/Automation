# ---
# Example:  A wall stability sheet, with the section drawn to scale
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: yes - 2026-09-18 - the parity wall reproduces its pinned stability values; the sheet and the drawing are written and re-read; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example
# ---
# The deliverable for a retaining wall is a stability sheet: the three
# factors against the three requirements, the bearing pressure diagram, and
# a section showing what was actually analysed.
#
# The section drawing is not decoration. C14 takes eight dimensions and a
# batter, and a wall drawn from those numbers is the fastest way to see
# that you typed the heel where the toe should be.
#
# ⚠ AND THE PRESSURE DIAGRAM CARRIES A SIGN. qmin can be NEGATIVE, which
# means the heel is lifting - the pressure distribution has left the base.
# A bearing_ratio computed from a negative qmax is meaningless, and this
# sheet says so rather than printing it.
#
# Uses matplotlib, bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import prokon.v5

REQUIRED_OVERTURNING = 2.0
REQUIRED_SLIDING = 1.5

WALL = dict(
    concrete_code="BS8110 - 1997",
    h1=5.0, h2=0.7, h3=0.8, hw=2.8,
    b=0.55, d=2.5, c=0.4, f=0.7, xf=3.05,
    at=0.3, ab=0.4, x=0.45,
    theta=27.0, alpha=9.0, delta=20.0,
    dg=18.0, db=25.0,
    fcu=25.0, fy=450.0,
    sf_overturning=1.5, sf_sliding=1.5,
    dl_fac=1.4, ll_fac=1.6, dl_fac_o=0.9,
    pmax=400.0, mu=0.5,
    cover_wall=50.0, cover_base=50.0,
    seismic=True, kh=0.02, kv=0.01, seis_w_loads=True,
    allow_seep=True, toe_back_force=True,
    load_cases=[
        {"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0, "lynl": 1.0,
         "xlv": 2.0, "ph": 0.5},
        {"name": "Truck", "w": 2.0, "p": 0.5, "xp": 2.0, "lynl": 2.0,
         "xlv": 1.0, "ph": 3.0},
        {"name": "Train", "w": 3.0, "lynl": 1.0, "xlv": 2.0},
    ],
)

lines = []


def out(text=""):
    print(text)
    lines.append(text)


envelope = prokon.v5.retaining_wall.analyse(**WALL)
result = envelope["result"]

PINNED = (4.477940718035636, 1.6341314510288516, 97.26517611421157,
          915.8514440593759, 791.8667235080961)
measured = (result["sf_overturning"], result["sf_sliding"], result["qmax"],
            result["as_wall_req"], result["as_base_req"])

out("=" * 76)
out("RETAINING WALL STABILITY SHEET".center(76))
out("=" * 76)
out(f"Engine    : {envelope['module']} {envelope['module_version']}")
out(f"Host      : {envelope['meta']['producer_version']}")
out(f"Code      : {WALL['concrete_code']}")
out(f"Anchor    : the C14 desktop-parity wall - "
    f"{'all five pinned values EXACT' if measured == PINNED else 'DRIFTED'}")
out()

# ── Geometry ────────────────────────────────────────────────────────────
base_width = WALL["b"] + WALL["ab"] + WALL["d"]
out("1  GEOMETRY")
out("-" * 76)
out(f"   stem height h1        {WALL['h1']:>8.2f} m")
out(f"   toe projection b      {WALL['b']:>8.2f} m   (in FRONT of the stem)")
out(f"   heel projection d     {WALL['d']:>8.2f} m   (BEHIND it, under the fill)")
out(f"   stem thickness ab     {WALL['ab']:>8.2f} m   at the base")
out(f"   TOTAL base width      {base_width:>8.2f} m   = b + ab + d")
out(f"   base thickness c      {WALL['c']:>8.2f} m")
out(f"   shear key f at xf     {WALL['f']:>8.2f} m at {WALL['xf']:.2f} m")
out(f"   -> 'find_base_width' sizes b, the TOE only. The total base is the")
out(f"      sum above, which is the number a drawing shows.")
out()

# ── Stability ───────────────────────────────────────────────────────────
out("2  STABILITY")
out("-" * 76)
out(f"   governing load case {result['governing_lc']} of "
    f"{len(WALL['load_cases'])}")
out()
out(f"   {'check':<16} {'achieved':>10} {'required':>10} {'ratio':>8}  verdict")

verdicts = []
for label, achieved, required in (
        ("overturning", result["sf_overturning"], REQUIRED_OVERTURNING),
        ("sliding", result["sf_sliding"], REQUIRED_SLIDING)):
    if achieved is None:
        out(f"   {label:<16} {'null':>10} {required:>10.2f} {'-':>8}  "
            f"not reported for this wall type")
        continue
    ratio = achieved / required
    ok = ratio >= 1.0
    verdicts.append(ok)
    out(f"   {label:<16} {achieved:>10.3f} {required:>10.2f} {ratio:>8.2f}  "
        f"{'OK' if ok else 'FAILS'}")

# ⚠ THE SIGN ON qmin IS THE CHECK. A negative qmin means the pressure
# distribution has left the base - the heel is lifting - and a bearing
# ratio computed from that is not a utilisation of anything.
allowable = WALL["pmax"]
if result["qmin"] < 0:
    out(f"   {'bearing':<16} qmin is {result['qmin']:.2f} kPa - NEGATIVE.")
    out(f"   {'':<16} The heel is lifting; the pressure diagram has left")
    out(f"   {'':<16} the base and no bearing ratio applies.")
    verdicts.append(False)
else:
    ratio = result["qmax"] / allowable
    ok = ratio <= 1.0
    verdicts.append(ok)
    out(f"   {'bearing':<16} {result['qmax']:>10.2f} {allowable:>10.2f} "
        f"{ratio:>8.2f}  {'OK' if ok else 'FAILS'}")
    out(f"   {'':<16} qmin {result['qmin']:.2f} kPa, eccentricity "
        f"{result['ecc']:.4f} m")

out()
out("3  REINFORCEMENT")
out("-" * 76)
out(f"   stem  {result['as_wall_req']:>9.1f} mm2/m")
out(f"   base  {result['as_base_req']:>9.1f} mm2/m")
out(f"   crack widths within the code limit: {result['crack_ok']}")
out(f"     worst stem {max(result['wall_cw']):.4f} mm, "
    f"worst base {max(result['base_cw']):.4f} mm")
out(f"   bending schedule, {len(result['bs_zones'])} zones:")
for index, zone in enumerate(result["bs_zones"], start=1):
    out(f"     zone {index:>2}  {zone}")
out()
out("4  CONCLUSION")
out("-" * 76)
out(f"   {'THE WALL IS ADEQUATE' if all(verdicts) else 'THE WALL IS NOT ADEQUATE'} "
    f"against the required factors above.")
out("=" * 76)

sheet = Path("wall_stability_sheet.txt")
sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
recovered = sheet.read_text(encoding="utf-8").splitlines()
print(f"\nWritten: {sheet.resolve()}")
print(f"  {len(recovered)} line(s), "
      f"{'identical on re-read' if recovered == lines else 'DIFFERENT'}")

# ── The section, drawn from the same eight numbers ─────────────────────
figure, (section, pressure) = plt.subplots(
    1, 2, figsize=(12, 6.5), gridspec_kw={"width_ratios": [1.3, 1.0]})

toe = WALL["b"]
stem = WALL["ab"]
heel = WALL["d"]
base_thickness = WALL["c"]
stem_top = WALL["at"]
height = WALL["h1"]
batter = WALL["x"]

# The base slab.
section.add_patch(plt.Rectangle((0.0, 0.0), base_width, base_thickness,
                                facecolor="0.82", edgecolor="0.25",
                                linewidth=1.6))
# The stem: battered on the retained face.
stem_left = toe
outline = [(stem_left, base_thickness),
           (stem_left + stem, base_thickness),
           (stem_left + stem - batter, base_thickness + height),
           (stem_left + stem - batter - stem_top, base_thickness + height)]
section.add_patch(plt.Polygon(outline, closed=True, facecolor="0.82",
                              edgecolor="0.25", linewidth=1.6))
# The shear key.
if WALL["f"] > 0:
    key_x = base_width - WALL["xf"]
    section.add_patch(plt.Rectangle((key_x - 0.15, -WALL["f"]), 0.30,
                                    WALL["f"], facecolor="0.7",
                                    edgecolor="0.25", linewidth=1.2))
# The retained fill, hatched, and the water table.
fill = [(stem_left + stem, base_thickness),
        (base_width, base_thickness),
        (base_width, base_thickness + height
         + (base_width - stem_left - stem) * 0.176),
        (stem_left + stem - batter, base_thickness + height)]
section.add_patch(plt.Polygon(fill, closed=True, facecolor="none",
                             edgecolor="0.55", hatch="///", linewidth=0.8))
if WALL["hw"] > 0:
    section.plot([stem_left + stem, base_width],
                 [WALL["hw"], WALL["hw"]],
                 color="#2a6fb0", linewidth=1.6, linestyle="-.")
    section.text(base_width, WALL["hw"] + 0.08, "water table",
                 fontsize=8, ha="right", color="#2a6fb0")

section.annotate("", xy=(0.0, -0.55), xytext=(toe, -0.55),
                 arrowprops=dict(arrowstyle="<->", color="0.3"))
section.text(toe / 2.0, -0.72, f"toe b\n{toe:.2f}", fontsize=8,
             ha="center", va="top")
section.annotate("", xy=(toe + stem, -0.55), xytext=(base_width, -0.55),
                 arrowprops=dict(arrowstyle="<->", color="0.3"))
section.text(toe + stem + heel / 2.0, -0.72, f"heel d\n{heel:.2f}",
             fontsize=8, ha="center", va="top")

section.set_aspect("equal")
section.set_xlim(-0.6, base_width + 1.2)
section.set_ylim(-1.4, base_thickness + height + 1.4)
section.set_xlabel("m")
section.set_ylabel("m")
section.set_title(f"Section as analysed - base {base_width:.2f} m overall",
                  fontsize=10)
section.grid(True, linewidth=0.3, color="0.9")

# The pressure diagram under the base, from qmax and qmin.
pressure.fill_between([0.0, base_width],
                      [0.0, 0.0],
                      [result["qmax"], result["qmin"]],
                      color="#b9d4ec", edgecolor="#2a6fb0", linewidth=1.6)
pressure.axhline(allowable, color="#b03030", linestyle="--", linewidth=1.4)
pressure.text(base_width, allowable + 6.0,
              f"allowable {allowable:.0f} kPa",
              fontsize=8, ha="right", color="#b03030")
pressure.text(0.06, result["qmax"] + 6.0, f"qmax {result['qmax']:.1f}",
              fontsize=9)
pressure.text(base_width - 0.06, result["qmin"] + 6.0,
              f"qmin {result['qmin']:.1f}", fontsize=9, ha="right")
pressure.set_xlim(-0.2, base_width + 0.2)
pressure.set_xlabel("along the base (m), toe at left")
pressure.set_ylabel("bearing pressure (kPa)")
pressure.set_title("Bearing pressure under the base", fontsize=10)
pressure.grid(True, linewidth=0.3, color="0.9")

figure.suptitle(
    f"Retaining wall - {WALL['concrete_code']}  |  "
    f"overturning {result['sf_overturning']:.2f}, "
    f"sliding {result['sf_sliding']:.2f}, "
    f"qmax {result['qmax']:.1f} kPa  |  "
    f"{'ADEQUATE' if all(verdicts) else 'NOT ADEQUATE'}",
    fontsize=10)
figure.tight_layout()

drawing = Path("wall_section.png")
figure.savefig(drawing, dpi=140)
plt.close(figure)

size = drawing.stat().st_size
print(f"Written: {drawing.resolve()}")
print(f"  {size} bytes, "
      f"{'a real image' if size > 20_000 else 'SUSPICIOUSLY SMALL'}")

print()
print("The section is drawn from the SAME eight numbers the engine was")
print("given, so it is a check on the input and not an illustration of the")
print("output. A wall drawn with the toe and heel swapped analyses")
print("perfectly and looks obviously wrong.")
