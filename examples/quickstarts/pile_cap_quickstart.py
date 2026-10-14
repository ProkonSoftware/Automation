# ---
# Example:  Pile cap — your first analysis
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes — 2026-09-02 — cap size, pile reaction, strut and node values match the C16 test suite; exact on prokon-automation.exe
# ---
# Design a four-pile cap by strut and tie, straight from Python. One call
# with named inputs, a plain dictionary of results back.
#
# NOTE: every length on this feature is in METRES — cap, piles and column
# alike — matching the desktop program's own input page.

import prokon.v5

# A 3.0 x 3.0 x 1.2 m cap on four 600 mm piles at 1.8 m centres, carrying
# a 500 x 500 column with 4000 kN of factored load, designed to
# CSA-A23.3:2019 in 30 MPa concrete.
result = prokon.v5.pile_cap.analyse(
    design_code="CSA-A23.3:2019",  # spelled exactly as the desktop names it
    column_dim_x=0.5,        # column size in X [m]
    column_dim_y=0.5,        # column size in Y [m]  (0 would mean CIRCULAR - see the feature page)
    no_of_piles=4,           # 2 to 5
    pile_dia=0.6,            # pile diameter [m]
    pile_spacing=1.8,        # centre-to-centre [m]
    pile_tolerance=0.05,     # setting-out tolerance [m]
    cap_thickness=1.2,       # overall cap depth [m]
    cap_overhang=0.3,        # beyond the pile face [m]
    bottom_rebar_depth=0.1,  # soffit to bottom-steel centroid [m]
    fc=30.0,                 # concrete strength [MPa]
    fy=400.0,                # reinforcement yield strength [MPa]
    # The load schedule is a list of dicts. "load_factor" is required on
    # every row - a factor of 0 DROPS the row, so send 1 for an
    # unfactored load rather than leaving it out.
    load_cases=[{"name": "ULS", "load_factor": 1.0, "p": 4000.0}],
)["result"]

# The cap plan size is derived from the layout you gave, not entered.
print(f"Cap size          {result['cap_dim_x']:.2f} x {result['cap_dim_y']:.2f} m")   # 3.00 x 3.00 m
print(f"Overhang needed   {result['overhang_min_required']:.3f} m "                   # 0.226 m
      f"(supplied 0.300 m)")

# Pile reactions - one row per pile, one entry per combined load case.
# Check these against your allowable pile load; C16 does not know it.
print("\nPile reactions:")
for index, pile in enumerate(result["pile_forces"]):
    print(f"  pile {index}:  P = {pile[0]['p']:.0f} kN")                              # 1000 kN each

# Struts and bearing nodes report an applied force, a capacity and their
# ratio. The section is adequate when every ratio is at least 1 - the
# engine reports the numbers and leaves that judgement to you.
strut = result["strut_results"][0]["load_cases"][0]
print(f"\nStrut     Cf = {strut['cf']:.0f} kN   Cr = {strut['cr']:.0f} kN   "         # 1564 / 2065
      f"SF = {strut['sf']:.3f}")                                                      # 1.320

node = result["column_node"]["load_cases"][0]
print(f"Column node   Pf = {node['pf']:.0f} kN   Pr = {node['pr']:.0f} kN   "         # 4000 / 4144
      f"SF = {node['sf']:.3f}")                                                       # 1.036

pile_node = result["pile_nodes"][0]["load_cases"][0]
print(f"Pile node     Pf = {pile_node['pf']:.0f} kN   Pr = {pile_node['pr']:.0f} kN   "
      f"SF = {pile_node['sf']:.3f}")                                                  # 1000 / 3584, 3.584

worst = min(
    [lc["sf"] for element in result["strut_results"] for lc in element["load_cases"]]
    + [lc["sf"] for lc in result["column_node"]["load_cases"]]
    + [lc["sf"] for node_ in result["pile_nodes"] for lc in node_["load_cases"]]
)
print(f"\nWorst factor over every strut and node: {worst:.3f}  ->  "                  # 1.036
      f"{'OK' if worst >= 1.0 else 'CAP INADEQUATE'}")

# Tie forces: ties are the NEGATIVE (tension) elements of the element
# grid. tie_results now carries real per-tie tf and as_required values as
# well (fixed 2026-08-28); the element-grid read below is the cross-check
# on them - see the feature page.
print("\nTie forces (tension):")
for element in result["tie_element_indices"]:
    tension = -min(result["element_forces"][element])
    print(f"  element {element}:  T = {tension:.1f} kN")                              # 850.3 kN each

print(f"\nCode minimum bottom reinforcement: "
      f"{result['tie_minim_reinforcement']:.0f} mm2/m")                               # 2400 mm2/m
