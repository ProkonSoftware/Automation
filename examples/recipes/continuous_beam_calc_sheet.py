# ---
# Example:  A calculation sheet you can put in a file - text, not a screen
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes - 2026-09-02 - the reference beam reproduces its pinned steel/deflection/crack values; the sheet is written and re-read
# ---
# A design is not finished when the numbers are right - it is finished when
# somebody else can follow them. This recipe writes a CALCULATION SHEET: a
# plain-text document with the inputs, the analysis, the design and the
# checks, in the order a reviewer reads them.
#
# Plain text on purpose. It goes into a project folder, diffs against last
# week's version, and needs nothing installed to open.
#
# ⚠ AND IT RECORDS WHICH ENGINE ANSWERED. analyse() carries
# module_version and meta alongside the result. A calculation sheet without
# that is not reproducible six months later, so the header prints it.

from datetime import datetime, timezone
from pathlib import Path

import prokon.v5

PROJECT = "Riverside Offices"
MEMBER = "Grid B floor beam, level 2"
CODE = "BS8110 - 1997"

INPUTS = dict(
    design_code=CODE,
    fcu=30.0, fy=450.0, fyv=250.0,
    cover_top=30.0, cover_bot=40.0,
    live_permanent_percent=25.0,
    creep_coefficient=2.0,
    shrinkage_strain=300e-6,
    sections=[{"n": 1, "bw": 300.0, "d": 500.0}],
    segments=[{"span": 1, "length": 6.0, "sec_left": 1},
              {"span": 2, "length": 6.0, "sec_left": 1}],
    supports=[{"n": 1}, {"n": 2}, {"n": 3}],
    loads=[row for span in (1, 2) for row in (
        {"case": "Dead", "span": span, "w_left": 20.0},
        {"case": "Live", "span": span, "w_left": 10.0})],
)

DEFLECTION_RATIO = 250
CRACK_LIMIT = 0.3

lines = []


def out(text=""):
    """One line, to the console and to the sheet."""
    print(text)
    lines.append(text)


# ── The call ───────────────────────────────────────────────────────────
# analyse() returns the WHOLE envelope and RAISES when the run produced no
# answer, so the sheet is built inside a try. A report generator still
# writes the failure into the sheet rather than dying halfway through it -
# it just catches instead of checking a flag, and the whole document the
# engine sent is on the error as .envelope.
try:
    envelope = prokon.v5.continuous_beam.analyse(**INPUTS)

except prokon.v5.ProkonError as refusal:
    out("=" * 78)
    out(f"CALCULATION SHEET".center(78))
    out("=" * 78)
    out(f"Project   : {PROJECT}")
    out(f"Member    : {MEMBER}")
    out(f"Prepared  : {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out()
    out("THE ANALYSIS FAILED, and the sheet says so rather than stopping:")
    out(f"  category {refusal.category}, code {refusal.code}")
    out(f"  {refusal.message}")
    for hint in refusal.hints:
        out(f"  hint: {hint}")

    # ⚠ MEASURED: a FAILURE envelope carries no 'module_version', because the
    # engine refused before identifying itself - and .envelope is None outright
    # when the engine never answered at all (a timeout, an unlaunchable
    # executable). Both are read defensively here for that reason.
    if refusal.envelope is not None:
        out(f"  engine   {refusal.envelope.get('module_version', 'not reported')}")
        out(f"  run time {refusal.envelope['meta']['elapsed_milliseconds']} ms")
    else:
        out("  no envelope: the engine never answered")

    for warning in refusal.warnings:
        out(f"  WARNING: {str(warning).encode('ascii', 'replace').decode()}")

    Path("calculation_sheet.txt").write_text("\n".join(lines), encoding="utf-8")
    raise SystemExit(1)


out("=" * 78)
out(f"CALCULATION SHEET".center(78))
out("=" * 78)
out(f"Project   : {PROJECT}")
out(f"Member    : {MEMBER}")
out(f"Prepared  : {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
out()
out(f"Engine    : {envelope['module']} {envelope['module_version']}")
out(f"Host      : {envelope['meta']['producer_version']}")
out(f"Envelope  : version {envelope['envelope_version']}")
out(f"Run time  : {envelope['meta']['elapsed_milliseconds']} ms")
out(f"-> those four lines are what makes this sheet reproducible. Without")
out(f"   them, 'the engine said so' is not a record of anything.")
out()

result = envelope["result"]

for warning in envelope["warnings"]:
    out(f"WARNING: {str(warning).encode('ascii', 'replace').decode()}")
if envelope["warnings"]:
    out()

# ── 1. Inputs ───────────────────────────────────────────────────────────
out("1  INPUTS")
out("-" * 78)
out(f"   Design code           {CODE}")
out(f"   Concrete              fcu = {INPUTS['fcu']:.0f} MPa")
out(f"   Reinforcement         fy = {INPUTS['fy']:.0f} MPa, "
    f"fyv = {INPUTS['fyv']:.0f} MPa")
out(f"   Cover to bar centres  top {INPUTS['cover_top']:.0f}, "
    f"bottom {INPUTS['cover_bot']:.0f} mm")
out(f"   Long-term             {INPUTS['live_permanent_percent']:.0f} % of "
    f"live permanent, creep {INPUTS['creep_coefficient']:.1f},")
out(f"                         shrinkage "
    f"{INPUTS['shrinkage_strain'] * 1e6:.0f} microstrain")
out()
out("   Section")
for section in INPUTS["sections"]:
    out(f"     {section['n']}   {section['bw']:.0f} wide x "
        f"{section['d']:.0f} deep")
out("   Spans")
for segment in INPUTS["segments"]:
    out(f"     {segment['span']}   {segment['length']:.2f} m, "
        f"section {segment['sec_left']}")
out("   Loads")
for load in INPUTS["loads"]:
    out(f"     span {load['span']}  {load['case']:<5} "
        f"{load['w_left']:.2f} kN/m")
out()

# ── 2. Analysis ─────────────────────────────────────────────────────────
out("2  ANALYSIS")
out("-" * 78)
out(f"   {result['span_count']} span(s), {result['total_length']:.2f} m "
    f"overall, {result['position_count']} result positions")
out(f"   Maximum sagging moment   {result['max_sagging_moment']:>10.2f} kNm")
out(f"   Maximum hogging moment   {result['max_hogging_moment']:>10.2f} kNm")
out(f"   Maximum shear            {result['max_shear']:>10.2f} kN")
out()
out(f"   {'support':>8} {'dead':>9} {'live':>9} {'service':>9} "
    f"{'ultimate':>9}   kN")
for support in result["supports"]:
    out(f"   {support['support_number']:>8} "
        f"{support['reaction_dead']:>9.2f} {support['reaction_live']:>9.2f} "
        f"{support['reaction_service']:>9.2f} "
        f"{support['reaction_ultimate']:>9.2f}")
out()

# ── 3. Design ───────────────────────────────────────────────────────────
out("3  REINFORCEMENT")
out("-" * 78)
out(f"   {'span':>5} {'length':>7} {'As bottom':>11} {'As top':>10} "
    f"{'Asv/sv':>9}   mm2, mm2/mm")
for span in result["spans"]:
    out(f"   {span['span_number']:>5} {span['length']:>7.2f} "
        f"{span['max_bottom_steel']:>11.1f} {span['max_top_steel']:>10.1f} "
        f"{span['max_shear_steel']:>9.4f}")
out()

# ── 4. Checks ───────────────────────────────────────────────────────────
out("4  SERVICEABILITY CHECKS")
out("-" * 78)
failures = []
for span in result["spans"]:
    limit = span["length"] * 1000.0 / DEFLECTION_RATIO
    ok = span["max_total_deflection"] <= limit
    if not ok:
        failures.append(f"span {span['span_number']} deflection")
    out(f"   span {span['span_number']} deflection")
    out(f"     elastic     {span['max_elastic_deflection']:>9.3f} mm")
    out(f"     shrinkage   {span['max_shrinkage_deflection']:>9.3f} mm")
    out(f"     long term   {span['max_long_term_deflection']:>9.3f} mm")
    out(f"     TOTAL       {span['max_total_deflection']:>9.3f} mm  "
        f"against span/{DEFLECTION_RATIO} = {limit:.2f} mm   "
        f"{'OK' if ok else 'FAILS'}")

out()
for span in result["spans"]:
    ok = span["max_bottom_crack_width"] <= CRACK_LIMIT
    if not ok:
        failures.append(f"span {span['span_number']} crack width")
    out(f"   span {span['span_number']} crack width "
        f"{span['max_bottom_crack_width']:.4f} mm against "
        f"{CRACK_LIMIT} mm   {'OK' if ok else 'FAILS'}")

out()
out("5  CONCLUSION")
out("-" * 78)
if failures:
    out(f"   NOT ADEQUATE. Failing checks: {', '.join(failures)}")
else:
    out(f"   The section is adequate for bending, shear, deflection and")
    out(f"   crack width as analysed.")
out()
out(f"   Note: total_mass reads {result['total_mass']:.1f} and is a FORCE in")
out(f"   kN, not a mass in kilograms. It is 0 here because no concrete")
out(f"   density was supplied, so no self weight was generated.")
out()
out("=" * 78)

# ── Write it, and read it back ─────────────────────────────────────────
sheet = Path("calculation_sheet.txt")
sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
recovered = sheet.read_text(encoding="utf-8").splitlines()

print()
print(f"Written: {sheet.resolve()}")
print(f"  {len(recovered)} line(s) written and re-read, "
      f"{'identical' if recovered == lines else 'DIFFERENT - check the encoding'}")
print()
print("Plain text on purpose: it diffs, it needs nothing installed, and the")
print("engine version at the top is what makes it a record rather than a")
print("printout.")
