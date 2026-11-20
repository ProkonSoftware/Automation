# ---
# Example:  Every engine under stress - one script that pushes all twelve to their limits
# Feature:  beam_section + circular_column + continuous_beam + crack_widths
#           + general_column + pad_footing + pile_cap + prestressed_concrete
#           + punching_shear + rectangular_column + rectangular_slab + retaining_wall
#           (C22 + C12 + C01 + C21 + C13 + C15 + C16 + C02 + C23 + C11 + C04 + C14)
# Verified: yes - 2026-11-20 - anchor mu exact (==); Spyder (CPython 3.12) and VS Code (CPython 3.15) byte-identical, and prokon-automation run identical except the 'unknown input name' rows
# ---
# A stress test, not a design. It drives all twelve engines as hard as a
# script can from an engineer's own Python, and prints ONLY what must come
# out the same wherever it runs - so the same script run in Spyder, in
# VS Code and through prokon-automation.exe must print byte-identical text.
# Compare the three outputs: one differing line is a finding.
#
# What it does to every engine, in eight stages:
#   1  anchor       the pinned beam_section value, compared with ==
#   2  determinism  the same call three times must give the same answer
#   3  sweep        one input walked from nothing to absurd, through the
#                   region where the engine must start refusing
#   4  bad inputs   typos, None, text for numbers, NaN, infinity, 1e300,
#                   negatives, zeros, unknown names, empty and garbage tables
#   5  round trip   save_file to awkward file names (spaces, '&', Greek,
#                   Chinese, 150 characters), load_file, analyse again
#   6  big tables   100 load cases in one call
#   7  threads      every engine at once, then 16 calls to one engine at once,
#                   each compared with the same call made alone
#   8  chains       one engine's answer fed to the next
#
# A refusal is NOT a failure of this script. Most of stages 3 and 4 exist to
# be refused, and the script prints what came back. The only things that
# should never happen are: an exception other than prokon.v5.ProkonError or
# a Python argument error, two answers to one question, and output that
# differs between the three routes.
#
# ONE DIFFERENCE BETWEEN THE ROUTES IS EXPECTED, and it is in stage 4's
# "unknown input name" row. In Spyder and VS Code each analyse() has real
# keyword parameters, so Python itself refuses a name it does not have - a
# TypeError, before any engine starts. Through prokon-automation run the
# call is passed on and the engine refuses it - a ProkonError,
# invalid_input/COMMAND_LINE_MALFORMED. Both refuse; they refuse differently.
# So those twelve rows, the totals and the ledger digest differ between the
# IDEs and the host, and nothing else may. (A script that must survive a
# misspelled name on every route catches both TypeError and ProkonError.)
#
# The digests themselves are not pinned here: they change whenever an
# engine's numbers do. What must hold is that every route prints the same.
#
# What it prints, and why nothing else: results are summarised as a short
# SHA-256 digest of the full result (every key, every digit), and refusals as
# category/code. It never prints a time, a path or Python's own exception
# text - those legitimately differ between interpreters and machines, and
# would hide the differences that matter.
#
# Warnings are COUNTED, not shown. Engines warn on save_file and load_file
# (what a file format cannot carry), and how a warning reaches the screen is
# up to the route: plain Python prints it on stderr, prokon-automation run
# folds stderr into its stdout. So every call records how many ProkonWarnings
# it raised, and the count - which must be the same everywhere - is printed.
#
# Expect it to take about three minutes: it makes about 380 engine calls.

import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import tempfile
import warnings

import prokon.v5

LEDGER = []          # every analyse outcome, in order: the final digest is over this
NASTY_NAMES = [
    "plain",
    "with spaces & an ampersand",
    "greek στρεσς and chinese 压力",
    "x" * 150,
]


# ---------------------------------------------------------------- helpers

def digest(value):
    """Twelve hex digits standing for the whole value - every key and every digit."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(text.encode("ascii")).hexdigest()[:12]


def attempt(engine, command, **inputs):
    """One engine call, reduced to what must be the same on every route:
    ("ok", result) | ("refused", "category/code") | ("python", ExceptionType)."""
    try:
        answer = getattr(getattr(prokon.v5, engine), command)(**inputs)
        return "ok", answer["result"]
    except prokon.v5.ProkonError as e:
        return "refused", f"{e.category}/{e.code}"
    except Exception as e:           # Python's own refusal (bad name, bad type)
        return "python", type(e).__name__


def call(engine, command, **inputs):
    """attempt(), plus how many ProkonWarnings the call raised - recorded, never shown.
    Main thread only: catch_warnings changes process-wide state, so stage 7's
    threads call attempt() directly, inside one catch_warnings of their own."""
    with warnings.catch_warnings(record=True) as raised:
        warnings.simplefilter("always")
        status, value = attempt(engine, command, **inputs)
    return status, value, sum(1 for w in raised if w.category.__name__ == "ProkonWarning")


def analyse(engine, stage, **inputs):
    status, value, warned = call(engine, "analyse", **inputs)
    shown = digest(value) if status == "ok" else value
    LEDGER.append((engine, stage, status, shown, warned))
    return status, value, shown


# ---------------------------------------------------------------- the twelve engines
# Base inputs are the quickstarts' own, which those scripts already prove valid.
# Each engine names: its file extension, one numeric input to send bad values to, its design-code
# input, a sweep (input, values, how to apply a value), and a load-case row maker
# for the big-table stage (None where the engine has no simple load table).

BEAM = dict(design_code="BS8110 - 1997", m=200.0, v=100.0, bw=300.0, h=500.0,
            dc_t=40.0, dc_b=40.0, dc_s=40.0, fcu=30.0, fy=450.0, fyv=450.0)


def continuous_beam_inputs(live):
    return dict(
        design_code="BS8110 - 1997",
        sections=[{"n": 1, "bw": 300, "d": 500}],
        segments=[{"span": 1, "length": 6, "sec_left": 1}, {"span": 2, "length": 6, "sec_left": 1}],
        supports=[{"n": 1}, {"n": 2}, {"n": 3}],
        loads=[{"case": "Dead", "span": 1, "w_left": 20}, {"case": "Dead", "span": 2, "w_left": 20},
               {"case": "Live", "span": 1, "w_left": live}, {"case": "Live", "span": 2, "w_left": live}],
        fyv=250.0, cover_top=30.0, cover_bot=40.0, live_permanent_percent=25.0,
        creep_coefficient=2.0, shrinkage_strain=0.0003)


def prestressed_inputs(live):
    return dict(
        design_code="BS8110 - 1997", title="STRESS TEST", fcu=19.2, fy=450.0, fyv=250.0, fci=14.4,
        ec=26000000.0, est=206000000.0, density=24.0, top_cover=25.0, bottom_cover=25.0,
        attached_torsional_members=True, edge_beam=True, redistribution_pct=10.0,
        tendon_properties=[{"no": 1, "bond": "Unbonded", "strength": 260.7, "max_stress_pct": 80,
                            "dia": 18, "area": 140, "k": 0.0015, "u": 0.05, "pullin": 5, "relax": 2,
                            "est": 195000000.0, "min_harp_radius": 1.0}],
        cable_sets=[
            {"n": 4, "prop": 1, "x_live": 0.0, "x_dead": 15.5,
             "spans": [{"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125, "b2": 34, "b3": 34},
                       {"span": 2, "lo": 0.4, "ro": 0.0, "b1": 34, "b2": 34, "b3": 125}]},
            {"n": 3, "prop": 1, "x_live": 15.5, "x_dead": 0.0,
             "spans": [{"span": 1, "lo": 0.0, "ro": 0.4, "b1": 125, "b2": 34, "b3": 34},
                       {"span": 2, "lo": 0.38, "ro": 0.0, "b1": 34, "b2": 34, "b3": 125}]}],
        sections=[{"name": "sec1", "bw": 5000, "d": 250}, {"name": "sec2", "bw": 5000, "d": 500},
                  {"name": "sec3", "bw": 2500, "d": 500}],
        span_segments=[{"span": 1, "length": 8.0, "sec_left": "sec1"},
                       {"span": 2, "length": 7.5, "sec_left": "sec1"}],
        supports=[{"no": 1, "d_below": 300, "b_below": 300, "h_below": 3.0, "code_below": "F",
                   "d_above": 300, "b_above": 300, "h_above": 3.0, "code_above": "F"},
                  {"no": 2, "d_below": 300, "h_below": 3.0, "code_below": "F"},
                  {"no": 3, "d_below": 300, "b_below": 300, "h_below": 3.0, "code_below": "F",
                   "d_above": 300, "b_above": 300, "h_above": 3.0, "code_above": "F"}],
        loads=[{"case": "D", "span": 1, "wl": 6}, {"span": 2, "wl": 6, "p": 10, "p_pos": 2, "m": 10, "m_pos": 4},
               {"case": "L", "span": 1, "wl": live}, {"span": 2, "wl": live}])


ENGINES = {
    "beam_section": dict(
        ext=".C22", code_key="design_code", bad_key="h", base=BEAM,
        sweep=("m", [0.0, 50.0, 200.0, 295.18197048179997, 400.0, 1000.0, 5000.0, -10.0]),
        row=None),
    "circular_column": dict(
        ext=".C12", code_key="design_code", bad_key="diameter",
        base=dict(design_code="BS8110 - 1997", diameter=220.0, cover=40.0, fcu=25.0, fy=450.0,
                  lex=2250.0, ley=2250.0, deltas=1.0, load_cases=[{"n": 700.0}]),
        sweep=("load_cases", [[{"n": n}] for n in (0.0, 100.0, 700.0, 1500.0, 3000.0, 1e5, -500.0)]),
        row=lambda i: {"n": 100.0 + 5 * i}),
    "continuous_beam": dict(
        ext=".C01", code_key="design_code", bad_key="fyv", base=continuous_beam_inputs(10),
        sweep=("live", [0, 10, 50, 200, 2000, -10]),
        row=None),
    "crack_widths": dict(
        ext=".C21", code_key="design_code", bad_key="h",
        base=dict(design_code="BS8007 - 1987", slab_mode=True, h=300.0, hef=200.0, b=1000.0, cover=40.0,
                  fcu=30.0, fy=450.0, ea=200.0, ec=26.0, allowable_crack_width=0.3, high_bond_bar=True,
                  short_term_load=True, load_cases=json.dumps([{"n": 1, "m": 50, "m_uls": 1.5}])),
        sweep=("load_cases", [json.dumps([{"n": 1, "m": m, "m_uls": 1.5}]) for m in (0, 10, 50, 150, 400, 5000, -50)]),
        row=lambda i: {"n": i + 1, "m": 10 + i, "m_uls": 1.5}),
    "general_column": dict(
        ext=".C13", code_key="design_code", bad_key="length",
        base=dict(design_code="BS8110 - 1997", length=3.0, fcu=30.0, fy=450.0,
                  section=[{"code": "+", "x": 0, "y": 0}, {"code": "L", "x": 400, "y": 0},
                           {"code": "L", "x": 400, "y": 400}, {"code": "L", "x": 0, "y": 400},
                           {"code": "+", "x": 42.5, "y": 42.5}, {"code": "B", "x": 25},
                           {"code": "+", "x": 357.5, "y": 42.5}, {"code": "B", "x": 25},
                           {"code": "+", "x": 357.5, "y": 357.5}, {"code": "B", "x": 25},
                           {"code": "+", "x": 42.5, "y": 357.5}, {"code": "B", "x": 25}],
                  load_cases=[{"axial": 1000, "moment_x_top": 50, "moment_x_bottom": 50},
                              {"axial": 2000, "moment_x_top": 90, "moment_y_top": 30,
                               "moment_x_bottom": 90, "moment_y_bottom": 30}]),
        sweep=("load_cases", [[{"axial": a, "moment_x_top": 50, "moment_x_bottom": 50}]
                              for a in (0, 500, 2000, 4000, 8000, 1e6, -1000)]),
        row=lambda i: {"axial": 500 + 10 * i, "moment_x_top": 20 + i % 30, "moment_x_bottom": 20}),
    "pad_footing": dict(
        ext=".C15", code_key="design_code", bad_key="a",
        base=dict(design_code="BS8110 - 1997", a=2.5, b=2.5, yf=0.6, z=0.5, c1=0.4, d1=0.4, e1=0.0, f1=0.0,
                  fcu=30.0, fy=450.0, allowable_bearing_pressure=200.0, bar_dia_x_bot=16.0,
                  bar_spacing_x_bot=200.0, bar_dia_y_bot=16.0, bar_spacing_y_bot=200.0, bar_dia_x_top=12.0,
                  bar_spacing_x_top=250.0, bar_dia_y_top=12.0, bar_spacing_y_top=250.0,
                  load_cases=[{"name": "LC1", "pa1": 600.0, "hx1": 30.0, "mx1": 20.0, "lf1": 1.4}]),
        sweep=("load_cases", [[{"name": "LC1", "pa1": p, "hx1": 30.0, "mx1": 20.0, "lf1": 1.4}]
                              for p in (0.0, 100.0, 600.0, 2000.0, 6000.0, 1e6, -600.0)]),
        row=lambda i: {"name": f"C{i:03d}", "pa1": 200.0 + 5 * i, "mx1": 10.0, "lf1": 1.4}),
    "pile_cap": dict(
        ext=".C16", code_key="design_code", bad_key="cap_thickness",
        base=dict(design_code="CSA-A23.3:2019", column_dim_x=0.5, column_dim_y=0.5, no_of_piles=4, pile_dia=0.6,
                  pile_spacing=1.8, pile_tolerance=0.05, cap_thickness=1.2, cap_overhang=0.3,
                  bottom_rebar_depth=0.1, fc=30.0, fy=400.0,
                  load_cases=[{"name": "ULS", "load_factor": 1.0, "p": 4000.0}]),
        sweep=("no_of_piles", [1, 2, 3, 4, 5, 6]),
        row=lambda i: {"name": f"L{i:03d}", "load_factor": 1.0, "p": 1000.0 + 20 * i}),
    "prestressed_concrete": dict(
        ext=".C02", code_key="design_code", bad_key="fcu", base=prestressed_inputs(15),
        sweep=("live", [0, 15, 40, 400, -15]),
        row=None),
    "punching_shear": dict(
        ext=".C23", code_key="design_code", bad_key="effective_depth",
        base=dict(design_code="BS8110 - 1997", col_width=400.0, col_breadth=400.0, effective_depth=200.0,
                  nearest_edge_x=10000.0, nearest_edge_y=10000.0, fcu=35.0, fy=500.0, fyv=500.0,
                  load_cases=[{"v": 800.0, "mx": 50.0, "my": 30.0}]),
        sweep=("load_cases", [[{"v": v, "mx": 50.0, "my": 30.0}] for v in (0.0, 200.0, 800.0, 2000.0, 1e5, -800.0)]),
        row=lambda i: {"v": 300.0 + 5 * i, "mx": 10.0, "my": 5.0}),
    "rectangular_column": dict(
        ext=".C11", code_key="design_code", bad_key="h",
        base=dict(design_code="SABS 0100 - 2000", h=400.0, b=400.0, dc_x=40.0, dc_y=40.0, fcu=30.0, fy=450.0,
                  lex=4000.0, ley=4000.0, bracing_x="Braced", bracing_y="Braced", betad=0.6, deltas=1.0,
                  load_cases=[{"n": 1500, "m2x": 250, "m1x": 150, "m2y": 150, "m1y": 90},
                              {"n": 2000, "m2x": 125, "m1x": 75, "m2y": 90, "m1y": 55}]),
        sweep=("load_cases", [[{"n": n, "m2x": 100, "m1x": 50}] for n in (0, 500, 1500, 3000, 6000, 1e6, -1500)]),
        row=lambda i: {"n": 500 + 10 * i, "m2x": 50 + i % 40, "m1x": 20}),
    "rectangular_slab": dict(
        ext=".C04", code_key="design_code", bad_key="lx",
        base=dict(design_code="BS8110 - 1997", lx=13.81, ly=8.21, h=250.0, dx=200.0, dy=220.0, fcu=25.0, fy=450.0,
                  edge_top="FixedAgainstVerticalDisplacementAndRotation",
                  edge_right="FixedAgainstVerticalDisplacementAndRotation",
                  edge_bottom="FixedAgainstVerticalDisplacementAndRotation",
                  edge_left="FixedAgainstVerticalDisplacement",
                  load_cases=[{"number": 1, "lf": 1.4, "udl": 2.0, "p": 4.0, "x": 4.19, "y": 6.45, "l": 4.1,
                               "x1": 2.44, "y1": 4.05, "x2": 10.03, "y2": 6.65},
                              {"lf": 1.6, "udl": 2.0, "p": 4.0, "x": 10.06, "y": 2.99, "l": 2.0,
                               "x1": 2.59, "y1": 2.62, "x2": 9.99, "y2": 4.61},
                              {"number": 2, "lf": 1.4, "udl": 1.0, "p": 12.0, "x": 3.28, "y": 6.6}],
                  envelope="1,2", density=24.0, self_weight_lf=1.4, poisson=0.2, creep_factor=2.0),
        sweep=("h", [20.0, 150.0, 250.0, 400.0, 1000.0, 10.0]),
        row=None),
    "retaining_wall": dict(
        ext=".C14", code_key="concrete_code", bad_key="h1",
        base=dict(concrete_code="BS8110 - 1997", h1=5.0, h2=0.7, h3=0.8, hw=2.8, b=0.55, d=2.5, c=0.4, f=0.7,
                  xf=3.05, at=0.3, ab=0.4, x=0.45, theta=27.0, alpha=9.0, delta=20.0, dg=18.0, db=25.0,
                  fcu=25.0, fy=450.0, sf_overturning=1.5, sf_sliding=1.5, dl_fac=1.4, ll_fac=1.6,
                  dl_fac_o=0.9, pmax=400.0, mu=0.5, cover_wall=50.0, cover_base=50.0, seismic=True,
                  kh=0.02, kv=0.01, seis_w_loads=True, allow_seep=True, toe_back_force=True,
                  load_cases=[{"name": "Default", "w": 1.0, "p": 1.0, "xp": 1.0, "lynl": 1.0, "xlv": 2.0, "ph": 0.5},
                              {"name": "Truck", "w": 2.0, "p": 0.5, "xp": 2.0, "lynl": 2.0, "xlv": 1.0, "ph": 3.0},
                              {"name": "Train", "w": 3.0, "lynl": 1.0, "xlv": 2.0}]),
        sweep=("h1", [0.5, 2.0, 5.0, 8.0, 15.0, 0.0]),
        row=lambda i: {"name": f"L{i:03d}", "w": 1.0 + (i % 10) / 10}),
}


def swept(engine, value):
    """The base inputs with the sweep input set to one value."""
    key, _ = ENGINES[engine]["sweep"]
    if key == "live" and engine == "continuous_beam":
        return continuous_beam_inputs(value)
    if key == "live" and engine == "prestressed_concrete":
        return prestressed_inputs(value)
    return {**ENGINES[engine]["base"], key: value}


def heading(text):
    print(f"\n{'=' * 78}\n{text}\n{'=' * 78}")


# ---------------------------------------------------------------- 1 anchor

heading("1  ANCHOR - the pinned beam_section value, compared with ==")
status, result, _ = analyse("beam_section", "anchor", **BEAM)
mu = result["mu"] if status == "ok" else None
print(f"mu = {mu!r}  ->  {'EXACT' if mu == 295.18197048179997 else 'NOT THE PINNED ENGINE - read nothing below'}")


# ---------------------------------------------------------------- 2 determinism

heading("2  DETERMINISM - the same call three times")
BASELINE = {}
for engine, spec in ENGINES.items():
    shots = [analyse(engine, "determinism", **spec["base"]) for _ in range(3)]
    BASELINE[engine] = shots[0][2]
    verdict = "same" if len({s[2] for s in shots}) == 1 else "DIFFERENT ANSWERS"
    print(f"{engine:22s} {shots[0][0]:8s} {shots[0][2]:14s} x3 {verdict}")


# ---------------------------------------------------------------- 3 sweep

heading("3  SWEEP - one input from nothing to absurd")
for engine, spec in ENGINES.items():
    key, values = spec["sweep"]
    print(f"{engine} - {key}:")
    for value in values:
        status, _, shown = analyse(engine, "sweep", **swept(engine, value))
        label = json.dumps(value)[:44]
        print(f"   {label:46s} {status:8s} {shown}")


# ---------------------------------------------------------------- 4 bad inputs

heading("4  BAD INPUTS - values no engineer should send")
for engine, spec in ENGINES.items():
    base, k = spec["base"], spec["bad_key"]
    good = base[k]
    cases = [
        ("design code typo", {spec["code_key"]: "Not A Code - 1066"}),
        (f"{k} = None", {k: None}),
        (f"{k} = text", {k: "thirty"}),
        (f"{k} = NaN", {k: math.nan}),
        (f"{k} = infinity", {k: math.inf}),
        (f"{k} = 1e300", {k: 1e300}),
        (f"{k} = negative", {k: -abs(good)}),
        (f"{k} = 0", {k: 0}),
        ("unknown input name", {"no_such_input": 1}),
    ]
    if "load_cases" in base:
        cases += [("load_cases empty", {"load_cases": [] if engine != "crack_widths" else "[]"}),
                  ("load_cases garbage", {"load_cases": "this is not a table"}),
                  ("load_cases row of nonsense", {"load_cases": [{"no_such_column": 1}]})]
    print(f"{engine}:")
    for label, change in cases:
        status, _, shown = analyse(engine, "bad inputs", **{**base, **change})
        print(f"   {label:30s} {status:8s} {shown}")


# ---------------------------------------------------------------- 5 round trip

heading("5  ROUND TRIP - save_file to awkward names, load_file, analyse again")
WORK = tempfile.mkdtemp(prefix="prokon-stress-")
try:
    for engine, spec in ENGINES.items():
        print(f"{engine}:")
        for name in NASTY_NAMES:
            path = os.path.join(WORK, name + spec["ext"])
            saved, why, save_warned = call(engine, "save_file", path=path, overwrite=True, **spec["base"])
            if saved != "ok":
                print(f"   {name[:28]:30s} save {saved}: {why}")
                continue
            loaded, answer, load_warned = call(engine, "load_file", path=path)
            if loaded != "ok":
                print(f"   {name[:28]:30s} load {loaded}: {answer}")
                continue
            LEDGER.append((engine, "file warnings", "warnings", save_warned, load_warned))
            status, _, shown = analyse(engine, "round trip", **answer["inputs"])
            same = "identical to the original" if shown == BASELINE[engine] else "DIFFERS from the original"
            print(f"   {name[:28]:30s} {status:8s} {shown:14s} {same if status == 'ok' else '':26s}"
                  f" warnings: save {save_warned}, load {load_warned}")
finally:
    shutil.rmtree(WORK, ignore_errors=True)


# ---------------------------------------------------------------- 6 big tables

heading("6  BIG TABLES - 100 load cases in one call")
for engine, spec in ENGINES.items():
    if spec["row"] is None:
        continue
    rows = [spec["row"](i) for i in range(100)]
    cases = json.dumps(rows) if engine == "crack_widths" else rows
    status, _, shown = analyse(engine, "big table", **{**spec["base"], "load_cases": cases})
    print(f"{engine:22s} {status:8s} {shown}")


# ---------------------------------------------------------------- 7 threads

heading("7  THREADS - concurrent calls must answer exactly as calls made alone")
with warnings.catch_warnings(), concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
    warnings.simplefilter("ignore")
    jobs = [(engine, pool.submit(attempt, engine, "analyse", **spec["base"]))
            for engine, spec in ENGINES.items() for _ in range(2)]
    for engine, job in jobs:
        status, value = job.result()
        shown = digest(value) if status == "ok" else value
        LEDGER.append((engine, "threads", status, shown))
    agree = sum(1 for engine, job in jobs if digest(job.result()[1]) == BASELINE[engine])
    print(f"all twelve engines at once, twice each: {agree} of {len(jobs)} match their solo answer")

moments = [50.0 + 25.0 * i for i in range(16)]
solo = {m: analyse("beam_section", "threads solo", **{**BEAM, "m": m})[2] for m in moments}
with warnings.catch_warnings(), concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    warnings.simplefilter("ignore")
    burst = {m: pool.submit(attempt, "beam_section", "analyse", **{**BEAM, "m": m}) for m in moments}
    together = {m: (digest(f.result()[1]) if f.result()[0] == "ok" else f.result()[1]) for m, f in burst.items()}
for m in moments:
    LEDGER.append(("beam_section", "threads burst", "ok", together[m]))
crossed = [m for m in moments if together[m] != solo[m]]
print(f"16 different beam_section calls at once: {16 - len(crossed)} of 16 match their solo answer"
      + (f"  - MISMATCHED: {crossed}" if crossed else ""))


# ---------------------------------------------------------------- 8 chains

heading("8  CHAINS - one engine's answer fed to the next")
status, beam_line, shown = analyse("continuous_beam", "chain", **continuous_beam_inputs(10))
if status == "ok":
    sag, hog, shear = beam_line["max_sagging_moment"], beam_line["max_hogging_moment"], beam_line["max_shear"]
    print(f"continuous_beam  sagging {sag!r}  hogging {hog!r}  shear {shear!r}")
    for where, m in (("midspan", sag), ("support", abs(hog))):
        status, section, shown = analyse("beam_section", "chain", **{**BEAM, "m": m, "v": shear})
        if status != "ok":
            print(f"beam_section at {where}: {status} {shown}")
            continue
        bars = section["reinforcement"]["tension_bars"][0]["description"]
        print(f"beam_section at {where}: ast {section['ast']!r}  first bars offered {bars}")
        crack = dict(ENGINES["crack_widths"]["base"], slab_mode=False, h=500.0, hef=250.0, b=300.0,
                     user_beam_bars=bars,
                     load_cases=json.dumps([{"n": 1, "m": m / 1.5, "m_uls": 1.5}]))
        status, cw, shown = analyse("crack_widths", "chain", **crack)
        print(f"crack_widths with {bars}: {status} {shown}")
else:
    print(f"continuous_beam: {status} {shown}")


# ---------------------------------------------------------------- the verdict

heading("VERDICT")
counts = {}
for entry in LEDGER:
    counts[entry[2]] = counts.get(entry[2], 0) + 1
print(f"ledger entries        : {len(LEDGER)}  (engine calls, plus one warnings count per round trip)")
for status in sorted(counts):
    print(f"   {status:8s} {counts[status]}")
print(f"ledger digest         : {digest(LEDGER)}")
print("Run this script on every route and compare the whole output: the ledger digest\n"
      "alone must match, and it changes if any one of the calls above answered differently.")
