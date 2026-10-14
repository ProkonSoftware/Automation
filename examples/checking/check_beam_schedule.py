# ---
# Example:  Independent check of a beam schedule off a drawing
# Feature:  continuous_beam + beam_section (C01 Continuous Beam + C22 Beam Section)
# Verified: yes - 2026-09-02 - the reference beam reproduces the pinned steel/deflection/crack values; every schedule row measured on prokon-automation.exe
# ---
# A THIRD-PARTY CHECK IS A DIFFERENT JOB FROM A DESIGN. You are not asked
# what the steel should be - you are given what is on the drawing and asked
# whether it works. The answer has to be defensible, so it has to be
# reproducible, so it has to be a script.
#
# The schedule below is the input: member, section, spans, loads, and the
# BARS SOMEONE ELSE CHOSE. For each row this script asks two engines:
#
#   C01  analyse the beam: what does it actually need?
#   C22  check the critical section: does the section have the capacity?
#
# and then compares the provided steel against both.
#
# ⚠ THE PROVIDED AREA IS COMPUTED HERE, NOT BY THE ENGINE. A bar
# description on a drawing - "4Y25" - is a count and a diameter; turning
# that into mm2 is arithmetic, and it is written out below so a checker can
# see it rather than trust it.

import math

import prokon.v5

CODE = "BS8110 - 1997"
FCU = 30.0
FY = 450.0
FYV = 250.0
CONCRETE = 25.0
CRACK_LIMIT = 0.3
DEFLECTION_RATIO = 250

# ── The schedule, as it comes off the drawing ──────────────────────────
# (member, bw, depth, spans, dead kN/m, live kN/m, bottom bars, top bars)
SCHEDULE = (
    ("B1", 300.0, 500.0, (6.0, 6.0), 20.0, 10.0, "5Y16", "5Y20"),
    ("B2", 300.0, 450.0, (5.0, 5.0), 18.0, 12.0, "4Y16", "4Y20"),
    ("B3", 350.0, 600.0, (7.0, 8.0, 7.0), 28.0, 15.0, "6Y20", "5Y25"),
    ("B4", 250.0, 400.0, (4.5,), 14.0, 8.0, "3Y16", "2Y12"),
    ("B5", 400.0, 700.0, (9.0, 9.0), 40.0, 20.0, "5Y25", "6Y32"),
    ("B6", 300.0, 550.0, (6.5, 6.5), 45.0, 25.0, "4Y20", "4Y20"),
)


def bar_area(description):
    """mm2 from a drawing's own notation, e.g. '4Y25' -> 1963.5.

    Written out rather than assumed: a checker has to be able to see that
    the area being compared is the area the drawing describes.
    """
    count, _, diameter = description.partition("Y")
    return int(count) * math.pi * float(diameter) ** 2 / 4.0


print("INDEPENDENT CHECK OF A BEAM SCHEDULE")
print(f"  {CODE}, fcu {FCU:.0f}, fy {FY:.0f}, crack limit {CRACK_LIMIT} mm, "
      f"deflection span/{DEFLECTION_RATIO}")

# ── The anchor ──────────────────────────────────────────────────────────
# B1 is the pinned reference beam, so the check starts by proving the
# engine on this machine is the engine the pins were taken from.
PINNED = (805.0209555473922, 1235.4393480298781, 12.446682698091044,
          0.11738993516717798)
anchor = prokon.v5.continuous_beam.analyse(
    design_code=CODE, fcu=FCU, fy=FY, fyv=FYV,
    cover_top=30.0, cover_bot=40.0,
    live_permanent_percent=25.0, creep_coefficient=2.0,
    shrinkage_strain=300e-6,
    sections=[{"n": 1, "bw": 300.0, "d": 500.0}],
    segments=[{"span": 1, "length": 6.0, "sec_left": 1},
              {"span": 2, "length": 6.0, "sec_left": 1}],
    supports=[{"n": 1}, {"n": 2}, {"n": 3}],
    loads=[row for span in (1, 2) for row in (
        {"case": "Dead", "span": span, "w_left": 20.0},
        {"case": "Live", "span": span, "w_left": 10.0})],
)["result"]
measured = (anchor["spans"][0]["max_bottom_steel"],
            anchor["spans"][0]["max_top_steel"],
            anchor["max_deflection"], anchor["max_crack_width"])
print(f"\n  engine check: B1's inputs are the pinned reference beam")
print(f"    {'':<14} {'measured':>22} {'pinned':>22}")
for name, value, pin in zip(("As bot", "As top", "deflection", "crack"),
                            measured, PINNED):
    print(f"    {name:<14} {value!r:>22} {pin!r:>22}")
print(f"    -> {'EXACT - this engine is the one the pins came from' if measured == PINNED else 'DRIFTED - resolve this before checking anything'}")

# ── The check ───────────────────────────────────────────────────────────
print(f"\n{'member':<7} {'section':>10} {'spans':>14} "
      f"{'As bot req':>11} {'prov':>9} {'As top req':>11} {'prov':>9} "
      f"{'defl':>7} {'crack':>7}  verdict")
print("-" * 118)

failures = []
for (member, width, depth, spans, dead, live,
     bottom_bars, top_bars) in SCHEDULE:

    beam = prokon.v5.continuous_beam.analyse(
        design_code=CODE, fcu=FCU, fy=FY, fyv=FYV,
        concrete_density=CONCRETE,
        cover_top=30.0, cover_bot=40.0,
        live_permanent_percent=25.0, creep_coefficient=2.0,
        shrinkage_strain=300e-6,
        sections=[{"n": 1, "bw": width, "d": depth}],
        segments=[{"span": n + 1, "length": length, "sec_left": 1}
                  for n, length in enumerate(spans)],
        supports=[{"n": n + 1} for n in range(len(spans) + 1)],
        loads=[row for n, _ in enumerate(spans) for row in (
            {"case": "Dead", "span": n + 1, "w_left": dead},
            {"case": "Live", "span": n + 1, "w_left": live})],
    )["result"]

    required_bottom = max(span["max_bottom_steel"] for span in beam["spans"])
    required_top = max(span["max_top_steel"] for span in beam["spans"])
    provided_bottom = bar_area(bottom_bars)
    provided_top = bar_area(top_bars)

    limit = min(spans) * 1000.0 / DEFLECTION_RATIO
    reasons = []
    if provided_bottom < required_bottom:
        reasons.append(f"bottom steel short by "
                       f"{required_bottom - provided_bottom:.0f} mm2")
    if provided_top < required_top:
        reasons.append(f"top steel short by "
                       f"{required_top - provided_top:.0f} mm2")
    if beam["max_deflection"] > limit:
        reasons.append(f"deflection {beam['max_deflection']:.1f} > "
                       f"{limit:.1f} mm")
    if beam["max_crack_width"] > CRACK_LIMIT:
        reasons.append(f"crack {beam['max_crack_width']:.3f} > "
                       f"{CRACK_LIMIT} mm")

    print(f"{member:<7} {f'{width:.0f}x{depth:.0f}':>10} "
          f"{str(spans):>14} "
          f"{required_bottom:>11.0f} {provided_bottom:>9.0f} "
          f"{required_top:>11.0f} {provided_top:>9.0f} "
          f"{beam['max_deflection']:>7.1f} {beam['max_crack_width']:>7.4f}  "
          f"{'PASS' if not reasons else 'FAIL'}")
    for reason in reasons:
        print(f"{'':<7} {'':<10} {'':<14} -> {reason}")
    if reasons:
        failures.append((member, reasons, beam, width, depth))

# ── The section check, on whatever failed ──────────────────────────────
# C01 says how much steel a beam needs. C22 answers a different question:
# does the SECTION have the capacity at all, and is the shear stress within
# the code's ceiling? A beam short of steel can be fixed with bars; a beam
# whose web crushes cannot.
print(f"\n{'-' * 118}")
if not failures:
    print("Every row passes. The schedule is adequate as drawn.")
else:
    print(f"{len(failures)} row(s) failed. Now the question a checker has to")
    print("answer next: is this fixable with bars, or is the SECTION wrong?")
    print(f"\n{'member':<7} {'M applied':>10} {'Mu':>9} {'v':>8} {'vc':>8} "
          f"{'vcu':>8}  diagnosis")

    for member, reasons, beam, width, depth in failures:
        section = prokon.v5.beam_section.analyse(
            design_code=CODE,
            m=abs(beam["max_hogging_moment"]) or beam["max_sagging_moment"],
            v=beam["max_shear"],
            bw=width, h=depth,
            dc_t=30.0, dc_b=40.0, dc_s=40.0,
            fcu=FCU, fy=FY, fyv=FYV,
        )["result"]
        applied = abs(beam["max_hogging_moment"]) or beam["max_sagging_moment"]

        if section["vv"] > section["vcu"]:
            diagnosis = "WEB CRUSHES - the section is wrong, not the bars"
        elif section["mu"] < applied:
            diagnosis = ("section short of capacity - compression steel or a "
                         "deeper beam")
        elif any("deflection" in reason for reason in reasons):
            diagnosis = "strength is fine; DEFLECTION governs - deepen it"
        elif any("crack" in reason for reason in reasons):
            diagnosis = "strength is fine; CRACK WIDTH governs - smaller bars"
        else:
            diagnosis = "fixable with more bars in the same section"

        print(f"{member:<7} {applied:>10.1f} {section['mu']:>9.1f} "
              f"{section['vv']:>8.3f} {section['vc']:>8.3f} "
              f"{section['vcu']:>8.3f}  {diagnosis}")

print(f"\n{'-' * 118}")
print("What makes this a CHECK rather than a design: the bars are an INPUT.")
print("The script never chooses them, so the answer is about the drawing")
print("and not about the checker's own preferences - which is exactly what")
print("a third party is being paid to establish.")
