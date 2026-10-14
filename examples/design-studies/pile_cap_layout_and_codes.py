# ---
# Example:  Pile caps - pile count, spacing, depth and the four codes
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes - 2026-09-02 - the CSA reference cap reproduces its pinned strut/node values; every layout row measured on prokon-automation.exe
# ---
# A pile cap by strut and tie has four levers and they interact:
#
#   pile COUNT      2 to 5, and the cap plan follows from it
#   pile SPACING    wider spreads the load, deeper struts, bigger cap
#   cap THICKNESS   steeper struts, better nodes, more concrete
#   design CODE     four of them, and they disagree by a factor of two
#
# This script maps all four, then covers the two behaviours that catch a
# script out: UPLIFT (which arrives as a REFUSAL, not a flag) and the
# strut-and-tie result shape.
#
# ⚠ C16 WORKS IN METRES. Every length below is metres - cap, piles and
# column alike - matching the desktop's own input page. It is the only
# engine in this set that does, and mixing it with the mm engines is the
# easiest mistake in a multi-engine script.

import prokon.v5

REFERENCE = dict(
    design_code="CSA-A23.3:2019",
    column_dim_x=0.5, column_dim_y=0.5,
    no_of_piles=4, pile_dia=0.6, pile_spacing=1.8, pile_tolerance=0.05,
    cap_thickness=1.2, cap_overhang=0.3, bottom_rebar_depth=0.1,
    fc=30.0, fy=400.0,
)
LOAD = [{"name": "ULS", "load_factor": 1.0, "p": 4000.0}]

print("PILE CAPS - LAYOUT, DEPTH AND THE FOUR CODES")

# ── The anchor ──────────────────────────────────────────────────────────
PINNED_CR = 2064.6284818393965
PINNED_PR = 4143.75
PINNED_OVERHANG = 0.226
anchor = prokon.v5.pile_cap.analyse(**REFERENCE, load_cases=LOAD)["result"]
measured = (anchor["strut_results"][0]["load_cases"][0]["cr"],
            anchor["column_node"]["load_cases"][0]["pr"],
            anchor["overhang_min_required"])
print(f"\n  anchor: the CSA reference cap, 4 piles at 1.8 m under 4000 kN")
print(f"    strut Cr            {measured[0]!r}")
print(f"    pinned              {PINNED_CR!r}")
print(f"    column node Pr      {measured[1]!r}")
print(f"    pinned              {PINNED_PR!r}")
print(f"    overhang required   {measured[2]!r}  pinned {PINNED_OVERHANG!r}")
print(f"    cap {anchor['cap_dim_x']:.2f} x {anchor['cap_dim_y']:.2f} m")
print(f"    -> {'EXACT on all three' if measured == (PINNED_CR, PINNED_PR, PINNED_OVERHANG) else 'DRIFTED'}")


def cap(load_cases=None, **overrides):
    """(result, None) or (None, reason). Uplift arrives as a REFUSAL."""
    try:
        return prokon.v5.pile_cap.analyse(
            **{**REFERENCE, **overrides},
            load_cases=load_cases or LOAD)["result"], None
    except prokon.v5.ProkonError as refusal:
        return None, refusal.message.encode("ascii", "replace").decode()


def worst_factor(result):
    """The governing safety factor and where it is.

    ⚠ TIES DO NOT PUBLISH AN sf - only cf/cr/sf for struts and pf/pr/sf
    for the two node families. A tie gives tf and as_required, and its
    'check' is whether you provide that steel. Guarding a tie loop with
    `if "sf" in entry` would skip every tie silently, so ties are simply
    not in this list and are read separately.
    """
    factors = [(s["load_cases"][0]["sf"], f"strut {s['element_index']}")
               for s in result["strut_results"]]
    factors.append((result["column_node"]["load_cases"][0]["sf"],
                    "column node"))
    factors += [(n["load_cases"][0]["sf"], f"pile node {n['index']}")
                for n in result["pile_nodes"]]
    return min(factors)


def governing_tie(result):
    """The tie the engine nominated. design_tie is an ELEMENT index."""
    by_element = {tie["element_index"]: tie for tie in result["tie_results"]}
    entry = by_element[result["design_tie"]]["load_cases"][0]
    return entry["tf"], entry["as_required"]


# ── 1. Pile count and spacing ──────────────────────────────────────────
print(f"\n1. PILE COUNT AND SPACING   4000 kN, 1.2 m cap")
print(f"   {'piles':>6} {'spacing':>8} {'cap plan':>15} {'per pile':>9} "
      f"{'worst SF':>9} {'tie As':>9}  governing")

for count in (2, 3, 4, 5):
    for spacing in (1.5, 1.8, 2.4, 3.0):
        result, reason = cap(no_of_piles=count, pile_spacing=spacing)
        if result is None:
            print(f"   {count:>6} {spacing:>8.1f} {'-':>15} {'-':>9} "
                  f"{'-':>9} {'-':>9}  {reason[:34]}")
            continue
        loads = [pile[0]["p"] for pile in result["pile_forces"]]
        factor, where = worst_factor(result)
        _, steel = governing_tie(result)
        print(f"   {count:>6} {spacing:>8.1f} "
              f"{result['cap_dim_x']:>6.2f} x {result['cap_dim_y']:<6.2f} "
              f"{max(loads):>9.0f} {factor:>9.3f} {steel:>9.0f}  {where}")

print("   -> more piles share the load but the cap grows, and a WIDER")
print("      spacing flattens the struts, which the nodes feel. The")
print("      governing element moves between the column node and the")
print("      struts as the geometry changes - so a script must check all")
print("      of them, not the one that governed last time.")

# ── 2. Cap thickness ───────────────────────────────────────────────────
print(f"\n2. CAP THICKNESS   4 piles at 1.8 m, 4000 kN")
print(f"   {'thick':>7} {'d:spacing':>10} {'worst SF':>9} {'tie tf':>10} "
      f"{'tie As':>9} {'concrete m3':>12}  governing")

for thickness in (0.6, 0.8, 1.0, 1.2, 1.5, 1.8, 2.1):
    result, reason = cap(cap_thickness=thickness)
    if result is None:
        print(f"   {thickness:>7.2f}  {reason[:60]}")
        continue
    factor, where = worst_factor(result)
    force, steel = governing_tie(result)
    volume = result["cap_dim_x"] * result["cap_dim_y"] * thickness
    print(f"   {thickness:>7.2f} {thickness / 1.8:>10.3f} {factor:>9.3f} "
          f"{force:>10.1f} {steel:>9.0f} {volume:>12.2f}  {where}")

print("   -> depth is the strongest lever: it steepens the struts, which")
print("      cuts the TIE force directly. Note the refusals at the shallow")
print("      end - the engine enforces a depth-to-spacing ratio, and says")
print("      so rather than answering a strut-and-tie model that does not")
print("      apply.")

# ── 3. The four codes ──────────────────────────────────────────────────
print(f"\n3. THE FOUR CODES   the reference cap, unchanged except the code")
print(f"   {'code':<22} {'worst SF':>9} {'where':<14} {'tie As':>9} "
      f"{'strut Cr':>10} {'node Pr':>10}")

by_code = {}
for code in prokon.v5.pile_cap.DESIGN_CODE_VALUES:
    extra = {}
    if code == "Eurocode 2 - 2004":
        # The EC2 group travels together: country, gamma_c, gamma_s and
        # alpha_cc, or none of them. A partial set cannot be expressed.
        extra = dict(eu_country="UnitedKingdom", gamma_c=1.5,
                     gamma_s=1.15, alpha_cc=0.85)
    result, reason = cap(design_code=code, **extra)
    if result is None:
        print(f"   {code:<22}  {reason[:56]}")
        continue
    factor, where = worst_factor(result)
    _, steel = governing_tie(result)
    by_code[code] = factor
    print(f"   {code:<22} {factor:>9.3f} {where:<14} {steel:>9.0f} "
          f"{result['strut_results'][0]['load_cases'][0]['cr']:>10.1f} "
          f"{result['column_node']['load_cases'][0]['pr']:>10.1f}")

if len(by_code) > 1:
    best = max(by_code, key=by_code.get)
    worst = min(by_code, key=by_code.get)
    print(f"   -> most generous {best} ({by_code[best]:.3f}), "
          f"strictest {worst} ({by_code[worst]:.3f}),")
    print(f"      a ratio of {by_code[best] / by_code[worst]:.2f}x on the "
          f"SAME cap. Strut-and-tie node")
    print(f"      strengths are a code choice, not a physical constant.")

# ── 4. Uplift, which is a REFUSAL and not a flag ──────────────────────
# has_uplift is a RESULT key, so it only exists on a call that succeeded.
# Push the moment up and the call RAISES instead - there is no result to
# read the flag off. Branch on the exception.
print(f"\n4. UPLIFT   the moment raised until the engine refuses")
print(f"   {'mx (kNm)':>10} {'least pile':>11} {'has_uplift':>11}  outcome")

for moment in (0, 1000, 2000, 3000, 3500, 3700, 3741, 3742, 4000, 6000):
    result, reason = cap([{"name": "ULS", "load_factor": 1.0,
                           "p": 4000.0, "mx": float(moment)}])
    if result is None:
        print(f"   {moment:>10} {'-':>11} {'-':>11}  REFUSED: {reason[:40]}")
        continue
    loads = [pile[0]["p"] for pile in result["pile_forces"]]
    print(f"   {moment:>10} {min(loads):>11.2f} "
          f"{str(result['has_uplift']):>11}  designed")

# Bisect it, so the boundary is a measurement and not a guess between two
# table rows.
low, high = 1000.0, 20_000.0
for _ in range(24):
    middle = (low + high) / 2.0
    result, _ = cap([{"name": "ULS", "load_factor": 1.0,
                      "p": 4000.0, "mx": middle}])
    if result is not None:
        low = middle
    else:
        high = middle
edge, _ = cap([{"name": "ULS", "load_factor": 1.0, "p": 4000.0, "mx": low}])
least = min(pile[0]["p"] for pile in edge["pile_forces"])
print(f"\n   the boundary, bisected: designs at mx = {low:.2f} kNm, refuses")
print(f"   from {high:.2f}. At the boundary the least-loaded pile reads")
print(f"   {least:.2f} kN and has_uplift is {edge['has_uplift']}.")
print("   -> so has_uplift is FALSE right up to the refusal, and the last")
print("      answerable cap has a pile at EXACTLY zero. The flag never")
print("      turns true on the way out: the engine refuses instead. A")
print("      layout search must therefore catch ProkonError, and a script")
print("      that only reads has_uplift finds uplift never happens.")

# ── 5. The result shape, once, properly ───────────────────────────────
print(f"\n5. THE RESULT SHAPE   why the helpers above look the way they do")
result = anchor
print(f"   strut_element_indices {result['strut_element_indices']}")
print(f"   tie_element_indices   {result['tie_element_indices']}")
print(f"   design_strut {result['design_strut']}, "
      f"design_tie {result['design_tie']}, "
      f"design_pile {result['design_pile']}")
print(f"   len(strut_results) {len(result['strut_results'])}, "
      f"len(tie_results) {len(result['tie_results'])}, "
      f"len(pile_nodes) {len(result['pile_nodes'])}")
print(f"   -> design_tie is {result['design_tie']} and tie_results has only "
      f"{len(result['tie_results'])} entries, so")
print(f"      tie_results[design_tie] is an IndexError. The indices are")
print(f"      ELEMENT numbers in a strut-and-tie model, not list positions.")
print(f"   strut keys {sorted(result['strut_results'][0]['load_cases'][0])}")
print(f"   tie keys   {sorted(result['tie_results'][0]['load_cases'][0])}")
print(f"   node keys  {sorted(result['column_node']['load_cases'][0])}")
print(f"   -> and the tie has NO 'sf'. That is why worst_factor() above")
print(f"      leaves ties out deliberately instead of filtering them out")
print(f"      silently.")
print(f"   pile_forces[0] {result['pile_forces'][0]}")
print(f"   -> [pile][load case], and each entry is a DICT of p, hx, hy.")
print(f"      max(pile_forces) compares dicts and raises TypeError.")
print(f"   tie_minim_reinforcement {result['tie_minim_reinforcement']} mm2/m")
print(f"   -> a code MINIMUM to compare against, never a substitute for")
print(f"      as_required, which is {governing_tie(result)[1]:.1f} mm2 here.")
