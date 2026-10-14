# ---
# Example:  How much prestress? The balanced-load sweep, and what it costs
# Feature:  prestressed_concrete (C02 Captain)
# Verified: yes - 2026-09-02 - the desktop's own example model reproduces its pinned punching veff triple; every sweep row measured on prokon-automation.exe
# ---
# The first decision on any post-tensioned floor is HOW MUCH PRESTRESS.
# It is usually expressed as a percentage of the dead load "balanced" by
# the cable's upward force, and the conventional answer is "60 to 100 %".
# That range is wide enough to hide a lot of steel and a lot of camber.
#
#   1. the balanced-load sweep: stresses, deflection, cable and rebar
#   2. bonded against unbonded, on the same layout
#   3. transfer - the stage that usually governs, and the one people skip
#   4. the SLS stress check, done properly against the engine's own limits
#
# ⚠ THE STAGE THAT GOVERNS IS OFTEN TRANSFER, NOT SERVICE. At transfer the
# concrete is young (fci, not fcu) and the full prestress is on with none
# of the live load to balance it. Section 3 shows where that bites, and it
# is why the sweep in section 1 reports both stages side by side.

import prokon.v5

# The desktop program's own default example, which is the anchor.
DEFAULT = dict(
    design_code="BS8110 - 1997",
    title="DEFAULT EXAMPLE",
    fcu=19.2, fy=450.0, fyv=250.0, fci=14.4,
    ec=26e6, est=206e6, density=24.0,
    top_cover=25.0, bottom_cover=25.0,
    attached_torsional_members=True, edge_beam=True,
    redistribution_pct=10.0,
)

TENDON = {
    "no": 1, "bond": "Unbonded", "strength": 260.7, "max_stress_pct": 80,
    "dia": 18, "area": 140, "k": 0.0015, "u": 0.05, "pullin": 5,
    "relax": 2, "est": 195e6, "min_harp_radius": 1.0,
}

print("HOW MUCH PRESTRESS?")

# ── The anchor ──────────────────────────────────────────────────────────
# The desktop's own example, cables and all, with the punching columns that
# make its perimeter-1 veff triple the pinned value.
anchor = prokon.v5.prestressed_concrete.analyse(
    **DEFAULT,
    tendon_properties=[TENDON],
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
    punching_columns=[
        {"no": number, "slope_y": slope, "pcy": 280, "cable_type": 1,
         "nc_x": nc_x, "nc_y": [1, 1, 2, 2], "ast_x": ast_x,
         "ast_y": ast_y}
        for number, slope, nc_x, ast_x, ast_y in (
            (1, 0.05, [4, 5, 6, 7], [402, 402, 603, 804], [565] * 4),
            (2, 0.06, [5, 6, 7, 8], [942] * 4, [804] * 4),
            (3, 0.05, [4, 5, 6, 7], [402, 402, 603, 804], [565] * 4))
    ],
)["result"]

PINNED_VEFF = (537.0024640743725, 575.0436234065779, 469.57376394972823)
measured = tuple(column["perimeters"][0]["veff"]
                 for column in anchor["punching"])
print(f"\n  anchor: the desktop's own DEFAULT EXAMPLE, 8.0 + 7.5 m")
for number, (value, pin) in enumerate(zip(measured, PINNED_VEFF), start=1):
    print(f"    column {number} perimeter-1 veff {value!r:22} pinned {pin!r}")
print(f"    -> {'EXACT on all three' if measured == PINNED_VEFF else 'DRIFTED'}")

# ── A simpler model for the sweep ──────────────────────────────────────
# The anchor's hand-laid cable sets are the point of the anchor. For a
# sweep, GENERATED cables are the right tool: balanced_dead_load_pct and
# cable_sets are mutually exclusive, and exactly one must be supplied.
SPANS = (9.0, 11.0, 9.0)
WIDTH = 3000.0        # mm of slab strip
DEPTH = 280.0         # mm
LIVE = 3.0            # kPa
FINISHES = 1.2        # kPa


def sweep_model(balanced, bond="Bonded", **overrides):
    settings = dict(
        design_code="BS8110 - 1997", title=f"{balanced:.0f} % balanced",
        fcu=40.0, fy=450.0, fyv=250.0, fci=30.0,
        ec=30e6, est=200e6, density=24.0,
        top_cover=30.0, bottom_cover=30.0,
        permanent_live_load_pct=25.0, creep=2.0,
        balanced_dead_load_pct=balanced,
        generated_profile="Parabolic",
    )
    settings.update(overrides)
    return prokon.v5.prestressed_concrete.analyse(
        **settings,
        tendon_properties=[{**TENDON, "bond": bond}],
        sections=[{"name": "strip", "bw": WIDTH, "d": DEPTH}],
        span_segments=[{"span": n + 1, "length": length,
                        "sec_left": "strip"}
                       for n, length in enumerate(SPANS)],
        supports=[{"no": n + 1, "d_below": 400, "b_below": 400,
                   "h_below": 3.2, "code_below": "F"}
                  for n in range(len(SPANS) + 1)],
        loads=[row for n, _ in enumerate(SPANS) for row in (
            {"case": "D", "span": n + 1, "wl": FINISHES * WIDTH / 1000.0},
            {"case": "L", "span": n + 1, "wl": LIVE * WIDTH / 1000.0})],
    )["result"]


def stages(result):
    """SLS and transfer stress extremes, with the engine's own limits."""
    return dict(
        sls_max=max(result["sls"]["svsma"]),
        sls_min=min(result["sls"]["svsmi"]),
        sls_compression=result["sls"]["fcc"] / 1e6,
        sls_tension=-result["sls"]["fct"] / 1e6,
        transfer_max=max(result["transfer"]["svtma"]),
        transfer_min=min(result["transfer"]["svtmi"]),
        transfer_compression=result["transfer"]["fcct"] / 1e6,
        transfer_tension=-result["transfer"]["fctt"] / 1e6,
    )


# ── 1. The sweep ───────────────────────────────────────────────────────
print(f"\n1. THE BALANCED-LOAD SWEEP   {SPANS} m, "
      f"{WIDTH:.0f} x {DEPTH:.0f} mm strip")
print(f"   {'balanced':>9} {'cable kN':>9} {'defl':>8} {'SLS min':>9} "
      f"{'SLS max':>9} {'tr min':>8} {'tr max':>8} {'rebar kg':>9}")

results = {}
for balanced in (40.0, 60.0, 80.0, 100.0, 120.0, 140.0):
    try:
        result = sweep_model(balanced)
    except prokon.v5.ProkonError as refusal:
        print(f"   {balanced:>9.0f}  {refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:50]}")
        continue
    results[balanced] = result
    stage = stages(result)
    print(f"   {balanced:>9.0f} {result['cables']['pax'][0]:>9.0f} "
          f"{max(abs(v) for v in result['deflections']['ditot']):>8.2f} "
          f"{stage['sls_min']:>9.2f} {stage['sls_max']:>9.2f} "
          f"{stage['transfer_min']:>8.2f} {stage['transfer_max']:>8.2f} "
          f"{result['quantities']['main_rebar_mass']:>9.1f}")

if results:
    first = min(results)
    limits = stages(results[first])
    print(f"   limits: SLS {limits['sls_tension']:.2f} to "
          f"{limits['sls_compression']:.2f} MPa, transfer "
          f"{limits['transfer_tension']:.2f} to "
          f"{limits['transfer_compression']:.2f} MPa")

# ── 2. And which stage actually binds ──────────────────────────────────
print(f"\n2. WHICH STAGE GOVERNS   the same sweep, as utilisations")
print(f"   {'balanced':>9} {'SLS comp':>10} {'SLS tens':>10} "
      f"{'tr comp':>9} {'tr tens':>9}  governs")

for balanced, result in sorted(results.items()):
    stage = stages(result)
    utilisations = {
        "SLS compression": stage["sls_max"] / stage["sls_compression"],
        "SLS tension": (stage["sls_min"] / stage["sls_tension"]
                        if stage["sls_tension"] else 0.0),
        "transfer compression": (stage["transfer_max"]
                                 / stage["transfer_compression"]),
        "transfer tension": (stage["transfer_min"] / stage["transfer_tension"]
                             if stage["transfer_tension"] else 0.0),
    }
    governs = max(utilisations, key=utilisations.get)
    print(f"   {balanced:>9.0f} {utilisations['SLS compression']:>10.3f} "
          f"{utilisations['SLS tension']:>10.3f} "
          f"{utilisations['transfer compression']:>9.3f} "
          f"{utilisations['transfer tension']:>9.3f}  "
          f"{governs} ({utilisations[governs]:.2f})")

print("   -> read the GOVERNS column down the page. The stage that binds")
print("      changes as the prestress rises, and past a point it is")
print("      TRANSFER - young concrete, full prestress, no live load to")
print("      balance it. A design checked at service only is checked at")
print("      the wrong stage.")

# ── 3. Bonded against unbonded ─────────────────────────────────────────
print(f"\n3. BONDED AGAINST UNBONDED   the same layout, 100 % balanced")
print(f"   {'bond':<10} {'cable kN':>9} {'defl':>8} {'rebar kg':>9} "
      f"{'cable kg':>9} {'SLS max':>9} {'losses %':>9}")

for bond in ("Bonded", "Unbonded"):
    try:
        result = sweep_model(100.0, bond=bond)
    except prokon.v5.ProkonError as refusal:
        print(f"   {bond:<10}  {refusal.category}/{refusal.code}")
        continue
    print(f"   {bond:<10} {result['cables']['pax'][0]:>9.0f} "
          f"{max(abs(v) for v in result['deflections']['ditot']):>8.2f} "
          f"{result['quantities']['main_rebar_mass']:>9.1f} "
          f"{result['quantities']['cable_mass']:>9.1f} "
          f"{max(result['sls']['svsma']):>9.2f} "
          f"{100 * (1 - result['cables']['lossf']):>9.2f}")

print("   -> the bond choice is a detailing and demolition decision as much")
print("      as a structural one. Where the numbers move, it is worth")
print("      knowing by how much before the argument starts.")

# ── 4. And the two inputs that are mutually exclusive ──────────────────
# Exactly one of balanced_dead_load_pct and cable_sets must be supplied.
# Both, or neither, is refused - which is the behaviour you want, because
# either would mean the engine choosing a cable layout on your behalf.
print(f"\n4. GENERATED OR EXPLICIT CABLES - EXACTLY ONE")

MINIMAL = dict(
    design_code="BS8110 - 1997", fcu=40.0, fy=450.0, fyv=250.0, fci=30.0,
    ec=30e6, est=200e6, density=24.0, top_cover=30.0, bottom_cover=30.0,
    tendon_properties=[TENDON],
    sections=[{"name": "s", "bw": WIDTH, "d": DEPTH}],
    span_segments=[{"span": 1, "length": 9.0, "sec_left": "s"}],
    supports=[{"no": 1}, {"no": 2}],
    loads=[{"case": "D", "span": 1, "wl": 5.0},
           {"case": "L", "span": 1, "wl": 9.0}],
)
SET = [{"n": 4, "prop": 1, "x_live": 0.0, "x_dead": 9.0,
        "spans": [{"span": 1, "lo": 0.0, "ro": 0.0, "b1": 140,
                   "b2": 40, "b3": 140}]}]

for label, extra in (("neither supplied", {}),
                     ("balanced only", dict(balanced_dead_load_pct=90.0)),
                     ("cable_sets only", dict(cable_sets=SET)),
                     ("BOTH supplied", dict(balanced_dead_load_pct=90.0,
                                            cable_sets=SET))):
    try:
        result = prokon.v5.prestressed_concrete.analyse(**MINIMAL, **extra)["result"]
        print(f"   {label:<20} accepted - cable force "
              f"{result['cables']['pax'][0]:.0f} kN")
    except prokon.v5.ProkonError as refusal:
        print(f"   {label:<20} {refusal.category} / {refusal.code}")
        print(f"   {'':<20} "
              f"{refusal.message.encode('ascii', 'replace').decode()[:78]}")

print("   -> refusing BOTH is the important half. If the engine accepted")
print("      both it would have to pick one, and a cable layout chosen")
print("      silently is not a design.")
