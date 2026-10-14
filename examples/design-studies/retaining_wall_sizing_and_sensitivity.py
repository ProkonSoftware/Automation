# ---
# Example:  Sizing a retaining wall, and what the answer is sensitive to
# Feature:  retaining_wall (C14 Retaining Wall) - all FOUR of its commands
# Verified: yes - 2026-09-18 - the parity wall reproduces its pinned stability values; every sweep row and every find_* result measured on prokon-automation.exe; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example
# ---
# C14 is the only engine here with more than one command. Besides analyse
# it publishes three SIZING commands that bisect a dimension for you:
#
#   find_base_width    the TOE projection b
#   find_base_depth    the HEEL projection d
#   find_footing_depth the shear key depth f
#
# ⚠ AND THE PYTHON PACKAGE ONLY EXPOSES analyse. The three find_* commands
# are on the typed CLI and on the MCP surface, but `prokon.v5.retaining_wall`
# has just analyse - section 2 shows how to reach the
# others through the CLI and the envelope, which is the same route the
# package itself uses.
#
#   1. sizing by hand, with analyse in a sweep - always available
#   2. the three find_* commands, through the CLI
#   3. what the answer is SENSITIVE to: theta, surcharge, water
#   4. seismic, and the inputs that are only read when it is on

import json
import subprocess

import prokon.v5

# The parity wall from the C14 test suite: the anchor for everything below.
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

print("SIZING A RETAINING WALL, AND WHAT THE ANSWER DEPENDS ON")

# ── The anchor ──────────────────────────────────────────────────────────
PINNED = (4.477940718035636, 1.6341314510288516, 97.26517611421157,
          915.8514440593759, 791.8667235080961)
anchor = prokon.v5.retaining_wall.analyse(**WALL)["result"]
measured = (anchor["sf_overturning"], anchor["sf_sliding"], anchor["qmax"],
            anchor["as_wall_req"], anchor["as_base_req"])
print(f"\n  anchor: the C14 desktop-parity wall")
for name, value, pin in zip(("sf_overturning", "sf_sliding", "qmax",
                             "as_wall_req", "as_base_req"), measured, PINNED):
    print(f"    {name:<16} {value!r:22} pinned {pin!r}")
print(f"    -> {'EXACT on all five' if measured == PINNED else 'DRIFTED'}")

# ── 1. Sizing by hand, with analyse ────────────────────────────────────
# A sweep over the heel is the route that is always available from Python.
# It is also the route that shows you the WHOLE curve rather than one root.
print(f"\n1. SIZING THE HEEL WITH analyse   sweep d, watch the factors")
print(f"   {'heel d':>8} {'ovt SF':>8} {'sld SF':>8} {'qmax':>8} "
      f"{'ovt/req':>8} {'sld/req':>8}  verdict")

first_adequate = None
for heel in [1.0 + 0.25 * step for step in range(13)]:
    result = prokon.v5.retaining_wall.analyse(**{**WALL, "d": heel})["result"]
    ok = (result["overturning_ratio"] >= 1.0
          and result["sliding_ratio"] >= 1.0
          and 0.0 < result["bearing_ratio"] <= 1.0)
    print(f"   {heel:>8.2f} {result['sf_overturning']:>8.3f} "
          f"{result['sf_sliding']:>8.3f} {result['qmax']:>8.1f} "
          f"{result['overturning_ratio']:>8.2f} "
          f"{result['sliding_ratio']:>8.2f}  {'OK' if ok else 'no'}")
    if ok and first_adequate is None:
        first_adequate = heel

if first_adequate is not None:
    print(f"   -> the smallest heel that satisfies all three: "
          f"{first_adequate:.2f} m")
print("   A sweep costs more calls than a bisection and tells you more: you")
print("   can see WHICH check is binding and how steep the curve is there.")

# ── 2. The three find_* commands, through the CLI ──────────────────────
# The Python package exposes analyse only. The other three commands live on
# the typed CLI, and the `prokon` package's own transport is exactly this:
# spawn the executable, read one JSON envelope off stdout. So reaching them
# is four lines, and the envelope is the same contract either way.
EXECUTABLE = prokon.v5.retaining_wall.executable


def run_command(command, **overrides):
    """One CLI call, one envelope. Returns (result, error) - one is None."""
    inputs = {**WALL, **overrides}
    arguments = []
    for name, value in inputs.items():
        if isinstance(value, bool):
            arguments.append(f"--{name}={'true' if value else 'false'}")
        elif isinstance(value, (list, dict)):
            arguments.append(f"--{name}={json.dumps(value)}")
        else:
            arguments.append(f"--{name}={value}")

    completed = subprocess.run(
        [EXECUTABLE, "retaining_wall", command] + arguments,
        capture_output=True, text=True, encoding="utf-8", timeout=120,
        # ⚠ CLOSE THE CHILD'S STDIN. A spawned engine that inherits an open
        # stdin can block on it forever; the shipped package does the same.
        stdin=subprocess.DEVNULL,
    )
    envelope = json.loads(completed.stdout)
    if envelope["ok"]:
        return envelope["result"], None
    return None, envelope["error"]


print(f"\n2. THE THREE find_* COMMANDS   reached over the CLI + envelope")
print(f"   executable: {EXECUTABLE}")
print(f"   the package exposes: "
      f"{[n for n in dir(prokon.v5.retaining_wall) if n.startswith('analyse')]}")
print(f"   {'command':<20} {'found_dimension':>16} {'ovt SF':>8} "
      f"{'sld SF':>8}  outcome")

for command in ("find_base_width", "find_base_depth", "find_footing_depth"):
    result, error = run_command(command)
    if result is None:
        print(f"   {command:<20} {'-':>16} {'-':>8} {'-':>8}  "
              f"{error['category']}/{error['code']}: "
              f"{error['message'].encode('ascii', 'replace').decode()}")
        continue
    print(f"   {command:<20} {result['found_dimension']:>16.4f} "
          f"{result['sf_overturning']:>8.3f} {result['sf_sliding']:>8.3f}  "
          f"converged")

# ── 2b. AND ONE OF THEM REFUSES ON MANY WELL-FORMED WALLS ─────────────
# find_base_width returns no_solution / ENGINE_REFUSED - "BonbekendSize:
# convergence failed" - on a large part of the ordinary input space. This
# section MAPS that rather than explaining it, because the boundary is not
# a simple property of any one input:
#
#   * on a plain cantilever wall (no water table, no toe soil, no shear
#     key, no seismic) it converges at delta = 0, 1 and 2 degrees and
#     refuses from 3 up;
#   * on that wall with the toe soil and water table added it converges up
#     to 5 and refuses from 8;
#   * on THIS wall, which also has seismic on and three load cases, the
#     table below shows a different pattern again.
#
# THE CONTROL that makes this a property of the command and not of the
# script: find_base_depth is run on the IDENTICAL inputs in the same loop,
# and converges throughout. Same wall, same transport, same envelope.
print(f"\n2b. find_base_width REFUSES OVER MUCH OF THE INPUT SPACE")
print(f"   {'delta':>7}  {'find_base_width':<24} {'find_base_depth':<24}")

width_ok = depth_ok = 0
for delta in (0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 18.0, 20.0, 25.0):
    row = []
    for command in ("find_base_width", "find_base_depth"):
        result, error = run_command(command, delta=delta)
        if result is not None:
            row.append(f"found {result['found_dimension']:.4f}")
            if command == "find_base_width":
                width_ok += 1
            else:
                depth_ok += 1
        else:
            row.append(f"REFUSED ({error['code']})")
    print(f"   {delta:>7.1f}  {row[0]:<24} {row[1]:<24}")

print(f"\n   find_base_width converged {width_ok} of 10; "
      f"find_base_depth {depth_ok} of 10.")
print("   -> a real design takes delta at roughly two-thirds of theta, so")
print("      18 to 20 degrees. Whether find_base_width answers there is")
print("      not something to assume - CHECK IT on your own wall, and fall")
print("      back to section 1's sweep, which always works and shows you")
print("      the whole curve rather than one root.")

# ── 3. What the answer is sensitive to ─────────────────────────────────
print(f"\n3. SENSITIVITY   one input moved at a time, from the anchor")
print(f"   {'input':<34} {'ovt SF':>8} {'sld SF':>8} {'qmax':>8} "
      f"{'as_wall':>9}")

print(f"   {'(the anchor)':<34} {anchor['sf_overturning']:>8.3f} "
      f"{anchor['sf_sliding']:>8.3f} {anchor['qmax']:>8.1f} "
      f"{anchor['as_wall_req']:>9.0f}")

PROBES = (
    ("theta 22 (weaker soil)", dict(theta=22.0)),
    ("theta 32 (stronger soil)", dict(theta=32.0)),
    ("alpha 0 (level fill)", dict(alpha=0.0)),
    ("alpha 20 (steep fill)", dict(alpha=20.0)),
    ("no water table", dict(hw=0.0)),
    ("water to the top", dict(hw=5.0)),
    ("surcharge 20 kPa", dict(load_cases=[{"name": "Surcharge", "w": 20.0}])),
    ("no shear key", dict(f=0.0, xf=0.0)),
    ("Rankine instead of Coulomb", dict(theory="Rankine")),
    ("soil 20 kN/m3", dict(dg=20.0)),
)

for label, overrides in PROBES:
    try:
        result = prokon.v5.retaining_wall.analyse(**{**WALL, **overrides})["result"]
    except prokon.v5.ProkonError as refusal:
        print(f"   {label:<34}  {refusal.category}/{refusal.code}: "
              f"{refusal.message.encode('ascii', 'replace').decode()[:30]}")
        continue

    def cell(value, spec):
        return "null" if value is None else format(value, spec)

    print(f"   {label:<34} {cell(result['sf_overturning'], '8.3f')} "
          f"{cell(result['sf_sliding'], '8.3f')} "
          f"{cell(result['qmax'], '8.1f')} "
          f"{cell(result['as_wall_req'], '9.0f')}")

print("   -> the WATER TABLE is the input that moves everything at once,")
print("      and it is the one a geotechnical report is least certain")
print("      about. On a wall this size the difference between a dry back")
print("      and a full one is the whole design.")

# ── 4. Seismic, and the inputs it gates ───────────────────────────────
# kh, kv and seis_w_loads are read ONLY when seismic is true. Set them
# without it and nothing happens - the same class of trap as the crack
# widths thermal path.
print(f"\n4. SEISMIC GATES THREE INPUTS")
print(f"   {'setting':<40} {'ovt SF':>8} {'sld SF':>8}  effect")

reference = prokon.v5.retaining_wall.analyse(
    **{**WALL, "seismic": False, "kh": 0.0, "kv": 0.0})["result"]
print(f"   {'seismic off, kh = 0':<40} {reference['sf_overturning']:>8.3f} "
      f"{reference['sf_sliding']:>8.3f}  baseline")

for label, overrides in (
        ("seismic OFF, kh = 0.20", dict(seismic=False, kh=0.20, kv=0.10)),
        ("seismic ON,  kh = 0.00", dict(seismic=True, kh=0.0, kv=0.0)),
        ("seismic ON,  kh = 0.10", dict(seismic=True, kh=0.10, kv=0.05)),
        ("seismic ON,  kh = 0.20", dict(seismic=True, kh=0.20, kv=0.10)),
        ("seismic ON,  kh = 0.20, no live", dict(seismic=True, kh=0.20,
                                                 kv=0.10,
                                                 seis_w_loads=False)),
):
    result = prokon.v5.retaining_wall.analyse(**{**WALL, **overrides})["result"]
    same = (result["sf_overturning"] == reference["sf_overturning"]
            and result["sf_sliding"] == reference["sf_sliding"])
    print(f"   {label:<40} {result['sf_overturning']:>8.3f} "
          f"{result['sf_sliding']:>8.3f}  "
          f"{'IDENTICAL to baseline' if same else 'moved'}")

print("   -> kh = 0.20 with seismic OFF is bit-identical to kh = 0. The")
print("      input is read only when the switch is on, so a script that")
print("      sets an acceleration and forgets the switch gets a static")
print("      answer and no warning at all.")
