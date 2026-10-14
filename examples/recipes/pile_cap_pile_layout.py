# ---
# Example:  Pile cap — choose the pile layout for a column load
# Feature:  pile_cap (C16 Pile Cap)
# Verified: yes — 2026-09-02 — every row measured against the built C16 surface; the CSA reference cap's pinned values reproduce; exact on prokon-automation.exe
# ---
# The desktop program designs ONE cap at a time, so choosing the layout is
# guesswork and retyping: how many piles, how far apart, and is the cap
# still adequate afterwards? A script sweeps the whole grid in one run.
#
# The brief: a 600 x 600 column carrying 3000 kN dead and 900 kN live,
# with 150/60 kNm of moment about X, on 600 mm bored piles whose
# ALLOWABLE ULS reaction is 1500 kN each (your geotechnical number - C16
# does not know it, so the script applies it).
#
# We want the smallest cap that satisfies BOTH:
#   * the pile reactions stay inside the allowable, and
#   * every strut and every bearing node has a safety factor of 1 or more.

import prokon.v5

DESIGN_CODE = "CSA-A23.3:2019"
COLUMN = 0.6             # square column, each way [m]
PILE_DIA = 0.6           # [m]
CAP_THICKNESS = 1.3      # [m]
CAP_OVERHANG = 0.30      # [m]
FC, FY = 30.0, 450.0     # [MPa]

ALLOWABLE_PILE_LOAD = 1500.0   # kN per pile at ULS - your geotechnical limit

# Two rows, ONE combination: an empty name continues the previous row, so
# these are summed with their factors into a single ULS case of
# 1.2 x 3000 + 1.5 x 900 = 4950 kN and 1.2 x 150 + 1.5 x 60 = 270 kNm.
LOADS = [
    {"name": "ULS", "load_factor": 1.2, "p": 3000.0, "mx": 150.0},
    {"name": "",    "load_factor": 1.5, "p":  900.0, "mx":  60.0},
]


def analyse(n_piles, spacing):
    return prokon.v5.pile_cap.analyse(
        design_code=DESIGN_CODE,
        column_dim_x=COLUMN, column_dim_y=COLUMN,
        no_of_piles=n_piles, pile_dia=PILE_DIA, pile_spacing=spacing,
        pile_tolerance=0.05,
        cap_thickness=CAP_THICKNESS, cap_overhang=CAP_OVERHANG,
        bottom_rebar_depth=0.1,
        fc=FC, fy=FY, load_cases=LOADS,
    )["result"]


def worst_factor(r):
    """The smallest strut / column-node / pile-node safety factor in the result."""
    return min(
        [lc["sf"] for e in r["strut_results"] for lc in e["load_cases"]]
        + [lc["sf"] for lc in r["column_node"]["load_cases"]]
        + [lc["sf"] for nd in r["pile_nodes"] for lc in nd["load_cases"]]
    )


print(f"{'piles':>5} {'spacing':>8} {'cap [m]':>13} {'volume':>8} "
      f"{'Pmax [kN]':>10} {'worst SF':>9}  verdict")

best = None
for n_piles in (2, 3, 4, 5):
    for spacing in (1.5, 1.8, 2.1, 2.4, 2.7, 3.0):
        try:
            r = analyse(n_piles, spacing)
        except prokon.v5.ProkonError as e:
            # Not a typo: the engine requires a cap at least half the pile
            # spacing deep, so a 1.3 m cap runs out of geometry past 2.6 m
            # centres. The sweep reports it and moves on.
            print(f"{n_piles:>5} {spacing:>8.1f}   -- {e.message.strip()}")
            continue

        p_max = max(f["p"] for pile in r["pile_forces"] for f in pile)
        volume = r["cap_dim_x"] * r["cap_dim_y"] * CAP_THICKNESS
        sf = worst_factor(r)
        piles_ok = p_max <= ALLOWABLE_PILE_LOAD
        overhang_ok = CAP_OVERHANG >= r["overhang_min_required"]
        ok = piles_ok and sf >= 1.0 and overhang_ok and not r["has_uplift"]

        why = "ok" if ok else ("pile overloaded" if not piles_ok else "cap inadequate")
        print(f"{n_piles:>5} {spacing:>8.1f} {r['cap_dim_x']:>6.2f} x{r['cap_dim_y']:>5.2f} "
              f"{volume:>7.2f}m3 {p_max:>10.0f} {sf:>9.3f}  {why}")

        if ok and (best is None or volume < best[0]):
            best = (volume, n_piles, spacing, r)

volume, n_piles, spacing, r = best
print(f"\nSmallest adequate cap: {n_piles} piles at {spacing:.1f} m centres "
      f"-> {r['cap_dim_x']:.2f} x {r['cap_dim_y']:.2f} x {CAP_THICKNESS:.2f} m "
      f"({volume:.2f} m3 of concrete)")
print(f"  worst pile reaction  {max(f['p'] for pile in r['pile_forces'] for f in pile):.0f} kN "
      f"of {ALLOWABLE_PILE_LOAD:.0f} kN allowable")
print(f"  worst safety factor  {worst_factor(r):.3f}")
print(f"  minimum overhang     {r['overhang_min_required']:.3f} m of {CAP_OVERHANG:.3f} m provided")

# Something a single desktop run cannot show you: across this whole
# sweep the strut and node factors never moved. They are set by the
# COLUMN face and the concrete grade, not by the pile layout - the layout
# only changes how the load is shared between piles. Shrink the column
# and the concrete checks are what fail, at any layout:
narrow = prokon.v5.pile_cap.analyse(
    design_code=DESIGN_CODE,
    column_dim_x=0.5, column_dim_y=0.5,
    no_of_piles=n_piles, pile_dia=PILE_DIA, pile_spacing=spacing, pile_tolerance=0.05,
    cap_thickness=CAP_THICKNESS, cap_overhang=CAP_OVERHANG, bottom_rebar_depth=0.1,
    fc=FC, fy=FY, load_cases=LOADS,
)["result"]
print(f"\nThe same layout under a 500 mm column: worst factor "
      f"{worst_factor(narrow):.3f} -> "
      f"{'OK' if worst_factor(narrow) >= 1.0 else 'the concrete, not the piles, now governs'}")
