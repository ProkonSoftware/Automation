# Example verification ledger

Every example script in this tree is listed here. **No script ships
silently unverified**: a script's header and this ledger must agree.

They cannot disagree, because the table below is **generated from the
headers** by `_tools/build-ledger.py`. Everything outside the generated
block is hand-written.

## The header every script carries

```python
# ---
# Example:  <title>
# Feature:  <feature name(s)> (<program name(s)>)
# Verified: yes - <date> - <what the results were checked against>
# ---
```

or, before verification:

```python
# Verified: no - results not yet checked; do not rely on the numbers
```

A multi-engine script names every engine it calls on the `Feature:` line,
and may add a `Repeats:` line saying how it differs from another script
that uses the same engines.

## What "verified" means

The script was **executed against the built 5.4 automation surface** and
its numeric output was checked against at least one of:

- a value pinned in the feature's own test suite (parity fixtures /
  golden tests), cited by file;
- a run of the desktop program on the same inputs;
- a published worked example.

"Runs without error" is **not** verification.

### How the 2026-09-02 wave was verified

Every script in this tree now runs against **one executable**:
`prokon-automation.exe`, the twelve-engine host. The verification had three
parts.

**1. The pinned values, re-measured to the last binary digit.**
`_tools/check-pinned-values.py` runs each quickstart with
`prokon.v5.<module>.analyse` intercepted, and compares 40 named result values
against the figures pinned in the engines' own test suites - with `==`, not
a tolerance. **40 of 40 exact, across all twelve engines.** The inputs are
never transcribed: the tool runs the example and reads the example's own
call, so the pins cannot drift away from the scripts they describe. It also
carries `--self-test`, which proves it can FAIL: a value wrong by one ULP
must be rejected, an indexed path must resolve, and an out-of-range index
must report missing. That control exists because the first version of the
path resolver silently reported 18 of 40 pins as drifted when the fault was
entirely its own.

**2. Every new script carries its own anchor.** Each of the 47 scripts added
on 2026-09-02 begins by running the pinned reference case for its engine and
printing the comparison. If the engine on the machine is not the engine the
pins came from, the script says so in its first few lines - before any of
its own numbers are worth reading.

**3. Every claim in the prose was measured, and several were retracted.**
The findings below were all found by a script whose conclusion contradicted
its own output.

### How the 2026-09-04 `charts-and-plotting` wave was verified

Twelve more scripts, one per engine, each drawing a matplotlib figure. They
were verified the same three ways as the wave above, plus two a chart needs
and prose does not.

**1. Every one carries its engine's pinned anchor** and prints the
comparison before it draws anything. All twelve reproduce their pins
exactly, with `==`.

**2. Both halves of "save AND show" were measured.** Every script writes a
PNG and then calls `plt.show()`, and the branch is chosen by asking
matplotlib which backend is live - **no script calls
`matplotlib.use("Agg")`**, because that call is precisely what stops a
script drawing into Spyder's Plots pane. Under `MPLBACKEND=Agg` the figure
is written and closed with no warning; under Spyder's own
`module://matplotlib_inline.backend_inline` the `plt.show()` branch is
reached and reports the backend it used. Both arms were run.

**3. Every one was run a SECOND time in the Spyder installation** - a
different interpreter (CPython 3.12.11, conda-forge, matplotlib 3.10.9), a
different `prokon` package (the one installed into
`spyder-6\envs\spyder-runtime`), and a different copy of the engine
(`spyder-6\prokon-engine\prokon-automation.exe`). That copy reports the
same build as the sealed runtime's, and the anchors reproduce there too.
Nothing of the build tree is on the path for that run, so it says something
about the shipped product rather than about the workspace.

**4. Several claims were refuted by their own controls, and the retractions
are in the scripts.** A chart makes a wrong claim look authoritative, so
every conclusion in this wave is computed from the sweep it describes
rather than written beside it. Three were rewritten after the control
disagreed:

- the slab's cost minimum was going to be attributed to the self-weight
  feedback; freezing the self weight still gives an interior minimum, so
  the feedback *moves* the optimum rather than creating it;
- the beam's cheapest section was going to be attributed to the shear
  ceiling; it runs at 60 % of that ceiling and is stopped by the edge of
  the priced range instead;
- the retaining wall's negative-`qmax` trap reported *"0 of 0 bad cells"*
  on the first grid, which is not evidence of anything - the heel range
  was extended until the phenomenon actually occurred.

**5. These twelve are the slowest scripts in the tree, and deliberately
so.** A contour needs a grid, and a grid is engine calls: 916 for the
rosette, 377 for the interaction map, 345 for the cost surface. Measured
at four in flight, the wave takes **556 s wall** and the rosette alone
takes 502 s of it - against a 600 s per-script timeout. Nothing here is
waiting on anything; it is arithmetic that a chart cannot do without. If
that becomes a nuisance in the gate, coarsen a grid rather than delete a
control.

### How the 2026-09-09 `carbon-and-cost` wave was verified

Twelve scripts, one per engine, all asking one question: **which design
that actually passes has the lowest embodied carbon?** The whole folder
runs under the gate (`MPLBACKEND=Agg`, `PYTHONIOENCODING=cp437`): 12 of
12 exit 0 and every one writes a PNG over 20 kB.

**The carbon factors are published, cited and pinned in every script.**
A1-A3 embodied carbon factors, kgCO2e/kg, from the table of example UK
factors in IStructE, *A brief guide to calculating embodied carbon*, **The
Structural Engineer, July 2020**:

| material | specification | ECF | source |
|---|---|---|---|
| concrete, in situ | C30/37 UK average ready-mix | 0.103 | MPA, 2018 |
| concrete, in situ | C32/40, 25 / 50 / 75 % GGBS | 0.120 / 0.089 / 0.063 | ICE V3 |
| concrete, in situ | C40/50, 25 / 50 / 75 % GGBS | 0.138 / 0.102 / 0.072 | ICE V3 |
| reinforcement bar | UK, BRC EPD | 0.684 | BRC, 2019 |
| reinforcement bar | world average | 1.99 | ICE V3 |
| PT strand | "assume the same as reinforcement bars" | 0.684 | the guide |

**Every script carries the same two-line control**, and it is a real
published-worked-example check rather than a self-consistency one: the
guide's own worked example states that 116.6 m3 of concrete is 279.8 t and
that 90 kg/m3 of bar over it is 10.5 t, and both `assert` lines reproduce
those figures. If a density is ever edited, twelve scripts fail at import.

**`beam_section_carbon_vs_depth.py` additionally asserts the fleet's
pinned value** - the 300 x 500 reference section reproducing
`mu = 295.18197048179997` - before it sweeps anything, so a changed engine
stops the script rather than quietly moving every carbon figure in it.

**Units were measured, not assumed, and four of them were not obvious.**
Getting any of these wrong changes an answer rather than breaking a script,
which is why each is recorded in the example that depends on it:

- `beam_section.asv` and `continuous_beam.envelopes.asv_required` are
  **Asv/Sv in mm2/mm**, not areas. Confirmed against the engine's own bar
  suggestion: `2Y8@300` is reported as 0.3351, and 2 x 50.265 / 300 =
  0.3351.
- `punching_shear.critical_perimeters[i].asv` **is** a total area in mm2.
  Confirmed the same way: 6941 comes back as `35Y16`, and 35 x 201 = 7037.
  So the same field name means different things on two engines.
- **`pad_footing`'s thickness is `yf`, not `z`.** Confirmed by
  back-calculating the steel from the engine's own `mdes_x`: with `yf` read
  as the thickness the reported `as_x` reproduces to within **0.5 %**, and
  no other reading is close.
- `prestressed_concrete.quantities` is the one set of **masses in kg** in
  the fleet, with `slab_area` in m2. Confirmed because `slab_area` came
  back as exactly 40.0 for a 5.0 x 8.0 m slab.

**Three planned scripts were rewritten because the measurement killed the
premise.** Each is worth recording, because each would have shipped a
plausible-looking optimisation that does nothing:

1. `rectangular_column`'s several bar arrangements have **identical steel
   area** - they are one area offered in different bar diameters - so there
   is no lowest-carbon arrangement to find. The script now measures that
   and says so, and its `preferred` field was **`None`**, so code that
   assumes it names an option is wrong too.
2. `prestressed_concrete` at a **fixed** strand count is not a trade-off:
   thinning the slab simply failed SLS, and the steel column read `-0.0`
   at every depth. The script now searches for the fewest strands that meet
   both SLS limits at each depth, which is the actual engineering question.
3. `retaining_wall`'s first grid passed **20 of 20** combinations, so it
   discriminated nothing. Retuned until bearing governs - it now fails 8 of
   24 - because a sweep where everything passes measures the sweep, not the
   wall.

**Two claims were retracted at the point of measurement**, both mine and
both in printed output rather than in comments: that a 1100 mm beam on
75 % GGBS came in under a 450 mm beam on 25 % (it does not - 54.7 against
48.0, so the sentence was replaced by a computed break-even depth), and
that the peak-times-length steel shortcut "roughly doubles" the answer (it
overstates by 3.36x to 3.55x here, now computed rather than asserted).

**One label of mine was wrong and is fixed in all twelve**: the diagnosis
key started as `reached_the_engine` and printed `True` for a refusal that
reached the **host** and never an engine. It is `has_envelope` now.

**What these scripts deliberately do NOT count**, stated in every header:
formwork, transport (A4), construction (A5), laps and curtailment,
excavation and backfill, and the knock-on self-weight a deeper member
sends to the foundations. Each header also says which way its omissions
lean, so a reader knows whether the answer is conservative.


### What changed in the twelve `going-deeper` error-handling scripts

All twelve taught `MISSING_REQUIRED_INPUT` by omitting an argument. The
shipped `prokon` package declares one real keyword-only parameter per
engine input, so **Python now refuses that before any engine launches** -
with the parameter named, and usually a spelling suggestion. The scripts
now teach both mechanisms, because both are real and they are met in
different ways:

| how the input went missing | who refuses | what you get |
|---|---|---|
| the argument is omitted | Python | `TypeError: analyse() missing 1 required keyword-only argument: 'fcu'` |
| the name is misspelled | Python | `TypeError: ... unexpected keyword argument 'fcux'. Did you mean 'fcu'?` |
| the value is `None` | the engine | `invalid_input` / `MISSING_REQUIRED_INPUT` |

The third row is the one that bites in practice: a blank spreadsheet cell
reads as `None`, and PROKON refuses rather than substituting a default.

Python's suggestion is a heuristic and gives up on a long enough mangling -
`fcux` suggests `fcu`, `SECTION` suggests nothing - so the scripts say
"usually suggests", measured.

### A console guard, added because five shipped scripts failed it

`_tools/run-all-examples.py` runs every example with
`PYTHONIOENCODING=cp437`, the code page a default Windows console still
starts in. Measured 2026-09-02: five scripts printed a literal em dash, and
under cp437 one of them exited 1 with
`UnicodeEncodeError: 'charmap' codec can't encode character '—'` -
mid-report, where a reader sees a traceback instead of an answer. An
ASCII-only control (`quickstarts/beam_section_quickstart.py`) exited 0 under
utf-8, cp1252 **and** cp437, so the failure is the character and not the
setting. Under cp1252 the em dash survives, which is exactly why a sweep on
this machine's own default would have missed all five.

All five are fixed, and the gate is mutation-tested: putting one em dash
back makes the sweep fail with that exact error, and removing it makes it
pass. A matplotlib chart caption is exempt - it is drawn into a PNG and
never written to a console.

## Findings worth carrying forward

Each of these was measured while writing an example, and each is written
into the example that found it.

**A pure-tension crack width can read exactly zero, with all-clear.**
`crack_widths` with `m = 0` and `t` set returns
`governing_crack_width` of exactly `0.0000` and `meets_all_criteria` `True`
on BS8007 - 1987, HK Concrete - 2020, ACI224.1 - 07, IS456 - 2000 and
SANS 51992-1-1:2025. NZ 3101 - 2006 (0.1022) and SP 63.13330.2018 (0.2888)
do compute it; Eurocode 2 - 2023, AS3600 - 2018 and GB 50010 - 2010 return
no arrangements at all; Eurocode 2 and CSA A23.3:24 refuse with
`internal` / `ENGINE_OUTPUT_NOT_COMPUTED`. Five behaviours from one input.
The control that makes it a finding: the same five codes compute normally
once a moment is supplied. See `design-studies/crack_widths_code_behaviour.py`.

**Torsion steel of exactly zero can mean "impossible", not "not needed".**
`beam_section` reports `asvt1 = 0` once `vv + vt1` passes 4.3818 MPa -
measured identically on 300x600, 400x600, 300x800 and 450x900, which is
0.8*sqrt(30), the BS8110 combined ceiling. `torsion.solved` cannot
distinguish the cases: it is `False` for **every** non-zero torsion,
including values that do report steel. `vtu` does not locate the cut-off
either - it reads 4.1428 at h = 600 and 4.3818 at h = 800. The dependable
test is `tor > 0 and asvt1 == 0` meaning **over the ceiling**. See
`design-studies/beam_section_design_charts.py`.

**Three `crack_widths` inputs are inert alone and bite only together.**
`restraint_factor`, `shrinkage_strain`, `thermal_expansion`, `t1`, `t2`,
`creep_factor` and `short_term_load` each change **nothing** on their own -
ten probes, all returning 0.222417 mm bit-identical. `t1` **and**
`restraint_factor` **and** `thermal_expansion` together move it to
0.238732, and doubling either doubles the thermal term. An input that reads
as ignored is usually one companion short. Measured with a **fixed**
arrangement (`user_slab_bars`), because "the lightest option" is a moving
target that made the first version of the table read non-monotonic. See
`design-studies/crack_widths_code_behaviour.py`.

**A biaxial envelope is a dish on a square and monotonic on a rectangle.**
`rectangular_column` under 200 kNm rotated from X to Y: the 400x400 square
needs its LEAST steel on the 45-degree diagonal (1395 mm2 against 2044 at
either axis, spread 1.47x) - so checking the two axes separately is
conservative there. A 600x300 is monotonic with a 4.17x spread, and an
800x250 4.78x; on those, checking only the strong axis is wrong by a factor
of four. See `design-studies/rectangular_column_interaction.py`.

**Steel is not monotonic in axial load.** A lightly loaded column carrying a
moment is tension-governed, so axial load HELPS until the balance point.
`circular_column` at 350 mm needs 724 mm2 at 420 kN and 572 mm2 at 840 kN.
A column schedule that designs only the bottom storey misses it. See
`workflows/column_schedule_whole_building.py` and
`recipes/circular_column_design_chart.py`.

**Two engines, two methods, the same answer.** `continuous_beam`'s
`max_top_steel` and `beam_section`'s `ast` are the same number to the last
binary digit - 738.2981992840653 - on the same section, difference exactly
0.0. And `pile_cap`'s strut-and-tie tie steel (4898 mm2) and
`beam_section`'s beam-theory steel (4904 mm2) agree to 0.1% on the same cap.
Different libraries, different methods, one answer. See
`workflows/frame_gravity_take_down.py` and
`workflows/piled_foundation_core_column.py`.

**`find_base_width` refuses over much of its input space.** Of C14's four
commands, `find_base_width` returns
`no_solution` / `ENGINE_REFUSED: "BonbekendSize: convergence failed"` on
most ordinary walls. On a plain cantilever it converges at
`delta` = 0, 1, 2 degrees and refuses from 3; with toe soil and a water
table it converges to 5 and refuses from 8; on the parity wall (seismic on,
three load cases) it converges only at 18 degrees and above, 3 of 10 probes.
The control: `find_base_depth` and `find_footing_depth` converge on the
identical inputs, 10 of 10. A real design uses `delta` near two-thirds of
`theta`. **And the Python package exposes only `analyse`** - the three
sizing commands are reachable from the typed CLI and from MCP, so the
example reaches them by spawning the executable and reading the envelope.
See `design-studies/retaining_wall_sizing_and_sensitivity.py`.

**C16 refuses six of seven single-input unit errors, by name.** Typing one
`pile_cap` length in millimetres instead of metres is refused with a
specific geometry message for `column_dim_x`, `pile_dia`, `pile_spacing`,
`pile_tolerance`, `cap_thickness` and `bottom_rebar_depth`. Only
`cap_overhang` gets through, and it moves the cap plan from 3.00 m to
602.40 m. So one assertion on the cap plan closes the whole class. See
`going-deeper/units_and_sign_conventions.py`.

**C15's bar inputs move only the crack widths.** The bearing pressure, the
steel demand and the shear capacities are bit-identical whether the bars are
Y25@100, Y16@200, Y10@300 or `0.016 @ 0.2` (metres by mistake). With no bars
at all the crack widths come back as **null**, not zero - the engine
distinguishing "not computed" from "computed as zero". So a bar-unit error
is invisible in every number a reviewer checks first. Same file.

**C14's bearing pressure goes negative in `qmax`, not `qmin`.** As the heel
shrinks, `qmax` turns negative (-577.84, -123.58, -59.64 kPa) and
`bearing_ratio` follows it, while `qmin` stays at 0 throughout. A script
watching `qmin` for the sign change never sees it. The test that works is
`qmax > 0 and 0 < bearing_ratio <= 1`. Same file.

**999999.99 is a sentinel, not a safety factor.** `pad_footing` publishes it
for `sf_ovt` and `sf_sliding` when the destabilising action is exactly zero.
With 0.001 kNm of moment the same pad reads 486450 - a real, enormous
number - so the sentinel marks the divide-by-zero case specifically. See
`checking/check_foundation_schedule.py`.

**`vcp = 0` means the punching check never ran.** A pad too small for its own
critical perimeter publishes `vp = vcp = 0`, and `vp <= vcp` reads `0 <= 0`.
Test `vcp > 0` first, always. Measured across
`design-studies/pad_footing_sensitivity.py`,
`checking/check_foundation_schedule.py` and three workflows.

**Uplift is a refusal, not a flag.** `pile_cap`'s `has_uplift` stays `False`
right up to the point where the engine refuses: bisected, the reference cap
designs at `mx = 3741.42` kNm with a least pile reaction of **exactly
0.00 kN**, and refuses from 3741.42. The flag never turns true on the way
out. See `design-studies/pile_cap_layout_and_codes.py`.

**A per-position array can carry a value that is not the quantity.**
`prestressed_concrete`'s `crack_widths.cwt` returned 152.1475 mm at the
interior support on one model, with 0.019 mm at the positions 250 mm either
side - and the reference model peaks at the same kind of position with a
smooth, plausible 0.414 mm. Adding bonded top steel over the support leaves
it **bit-identical**, which refutes the first explanation worth trying. The
technique, not the diagnosis, is the lesson: compare a peak with its
neighbours. **And the neighbour is not adjacent by index**: C02 duplicates
every support position at an offset of 0.1 mm (8 and 8.0001), so `==` on
positions never finds the twin. Both were real bugs in this example set
before they were findings. See
`workflows/post_tensioned_versus_rc_floor.py` and
`going-deeper/reading_nested_results_safely.py`.

**C02 publishes no support reactions, and the derivation is provable.** The
reaction is the jump in the shear envelope across a support - taking the
NEGATIVE envelope on the left and the POSITIVE on the right, and the
outward envelope at an end support. Using the positive envelope on both
sides double-counts one side, which showed up as asymmetric reactions on a
symmetric bridge. The derivation is validated inside the example by running
it against `continuous_beam`, which publishes `reaction_ultimate` directly:
**all four reactions reproduce to 0.0000%**. See
`workflows/pt_bridge_deck_and_piers.py`.

**The command line binds long before the engine's own limit.**
`rectangular_column` advertises 5000 load cases; measured, 476 launch and
477 do not, because every input travels as a command-line argument.
`continuous_beam`'s table limits are the engine's own and refuse by name
("At most 60 supports"). And when recombining a batch, re-derive the
summary: the steel to provide is the **worst** of the batch minima, not the
minimum of the minima. See `going-deeper/limits_timeouts_and_batching.py`.

**The two column engines do not offer the same code list.**
`rectangular_column` has 23 codes, `circular_column` 21, with 19 in common.
`ACI 318 - 2019` is a C11 code and C12 refuses it, so a schedule with round
columns cannot be reviewed against it at all. Compute the intersection
rather than remembering it. See
`checking/check_column_schedule_second_code.py`.

**Ten of C12's codes refuse `deltas` below 1.** Every ACI 318, CSA A23.3 and
AS3600 variant returns `no_solution` / `ENGINE_REFUSED: "ds must be >= 1"`;
the other ten accept 0. That is why `deltas` is required with no default -
no single value is valid for every code the command advertises. A re-check
with `deltas` left at 0 comes back as a refusal, not as different numbers.
See `design-studies/circular_column_slenderness.py`.

**Four of C04's twenty-nine codes design nothing.** BS8007 - 1987,
ACI224.1 - 07, BG50010 - 2010 and CSA A23.3:24 are crack-width codes with no
flexural rules: they return success, `mu = 0` in every direction, and `ast`
values around 1e-312 - unwritten memory. The reliable detector is
`max(mu) == 0`. Across the 25 that do design, the same slab's bottom steel
in x ranges from 780.8 to 964.6 mm2/m, a 1.235x spread. See
`design-studies/rectangular_slab_all_codes.py`.

**C04's own bar suggestion can be short of its own requirement.** On the
pinned reference panel, `bars.x_bot` suggests `Y12@250 + Y10@250` providing
766.55 mm2/m against 836.66 required. And below the detailing floor
`bars[face]` is **`None`**, not a dict with an empty description. See
`recipes/rectangular_slab_reinforcement_schedule.py`.

**Crack width is not a function of steel area.** In a 41-cell diameter x
spacing grid on one section, **124 pairs** exist where the arrangement with
LESS steel has the NARROWER crack. The starkest: Y10@250 at 314 mm2/m cracks
0.0820 mm, while Y20@300 at 1047 mm2/m cracks 0.2672 mm - 3.3x the steel and
3.3x the crack. Ranking arrangements by area ranks them wrongly. See
`recipes/crack_widths_selection_table.py`.

**A propped retaining wall publishes nulls, and `==` on engine floats means
nothing.** `wall_type = "ProppedCantilever"` returns `sf_sliding`,
`sliding_ratio`, `ecc` and `pm1` as **null** - a prop carries the thrust, so
a sliding factor has no meaning - and `m_base` carries 39 nulls of 55
positions. Propping leaves the stem steel the same to within -2.27e-13
mm2/m on a 920 mm2/m number, which `==` reports as different and means
nothing by. See `workflows/reservoir_wall_crack_control.py`.

**A frame and its columns are coupled, and the biggest change is not at the
biggest load.** Re-running a PT transfer slab with the column its own
design produced (1200x400 instead of 600x250) moved the END reactions
**+9.3%** while the worst reaction moved only -3.5%. A convergence check
that watches the worst reaction reports "one pass is enough" and misses the
columns that were actually under-designed. See
`workflows/pt_transfer_slab_over_basement.py`.

**C02's report file is cp1252, not UTF-8.** `report_path` writes the
desktop's own CAPTAIN.OUT (780 lines, 44 KB here) in the engine's code page,
and it contains `0xb2` - a superscript two. Reading it as UTF-8 with
`errors="replace"` turns real characters into U+FFFD and then reports them
as "non-ASCII in the report", which is the reader lying about the file. See
`recipes/prestressed_concrete_tendon_profile.py`.

**A circular column's punching perimeter is the bounding square.**
`punching_shear` with `col_breadth = 0` (or negative) returns
`uo = 4 x col_width` - 5600 mm for a 1400 mm pier - never `pi x D` (4398).
With a positive breadth it is `2(w + b)`. And an edge inside the outermost
perimeter cuts `uo` further, which is what a 2800 mm reading turned out to
be. See `workflows/pt_bridge_deck_and_piers.py` and
`design-studies/punching_shear_remedies.py`.

**A failed column FACE has no reinforcement remedy, proved rather than
asserted.** Eight times the flexural steel leaves `vu` and `vcu` bit-
identical while the perimeter demands fall from 6608 to 1147 mm2. `vcu` is a
ceiling on the face stress, not a capacity. See
`design-studies/punching_shear_remedies.py`.

**Long-term inputs that default to zero carry three quarters of a
deflection.** On a 2 x 8 m, 300x700 beam, C01's own breakdown gives elastic
3.645 mm of a 14.903 mm total - **24%**. The other 76% comes from
`live_permanent_percent`, `creep_coefficient` and `shrinkage_strain`, all
zero when omitted. A beam analysed without them is not optimistic; it is
answering a different question. See
`design-studies/continuous_beam_span_depth.py`.

### Found while drawing the 2026-09-04 charts

**A numpy scalar is not a float, and the engine says so by name.**
`np.float64(48.7)` was refused with `invalid_input` /
`INPUT_VALUE_MALFORMED` - *"np.float64(48.7)" cannot be read as the
declared kind of "mx_top"*. The identical value as a plain `float` was
accepted; that control is what made the refusal about the TYPE and nothing
else. It mattered because every sweep in `charts-and-plotting/` builds its
grid with `np.arange`, arithmetic on a numpy scalar stays a numpy scalar,
and inside a `try/except` it turned a whole sweep into blank cells - which
is how it was found.

> **⛔ RETRACTED 2026-09-10, and the retraction is the useful part.**
> Re-measured through the current package: **`np.float64` is accepted and
> returns the identical answer to the same value as a plain `float`**, on
> `rectangular_slab.analyse`. The `float()` wrapping the charts carry is
> therefore no longer load-bearing, and the warning above describes
> behaviour that no longer reproduces. It is kept rather than deleted
> because the input it was measured on - `mx_top` - was removed in the same
> release, so a reader who finds an old script failing this way needs to
> know which of the two changes bit them.

**A small crack width on a section that cannot carry the load is the most
convincing wrong number C21 produces.** 23 of 54 arrangements on one
section cannot reach the ultimate moment, and C21 still reports a crack
width for each - a NARROW one, because a section that never develops the
stress never develops the crack. Left in, the "crack width is not a
function of steel area" analysis reports Y10@300 at 262 mm2/m cracking
0.053 mm against Y16@275 at 731 mm2/m at 0.467 mm, which is 8.8x the crack
for 2.8x the steel - and Y10@300 carries 32.4 kNm/m against a demand of
135.0. Filtered to the 31 arrangements that do carry the load the effect
survives (40 inverted pairs against 425 ordered) and the headline becomes
honest. See `charts-and-plotting/crack_widths_selection_map.py`.

**C11 saturates at exactly 15.4 %, and it is a ceiling rather than an
answer.** Measured identical on 600x400, 500x500 and 900x300 under 20 MN.
Positive control: at 4.5 MN with 500 kNm the same three sections return
2.95, 3.20 and 1.47 %, so the reading is not frozen. On the 600x400 the
heaviest REAL design anywhere on a 377-point (N, M) grid is 5.39 % - below
BS8110's 6 % maximum - so the code limit never binds there and the map
steps from 5.39 % straight to the ceiling with nothing between. See
`charts-and-plotting/rectangular_column_interaction_map.py`.

**C13's capacity factor does not carry the SIGN of the moment.** On a
400 mm square with all eight bars crowded against one face - where the two
senses cannot physically be equal - the factor at 0 and at 180 degrees is
identical to the last binary digit (0.7409577611290454), and so are 90 and
270. Control: 0 and 90 do differ (0.741 against 0.964), so the reading is
alive. A biaxial capacity rosette drawn from C13 is therefore centrally
symmetric BY CONSTRUCTION, and must be read as one capacity per axis of
bending. See `charts-and-plotting/general_column_capacity_rosette.py`.

**C16's safety factors do not respond to the cap geometry at all, and its
design boundary is a refusal.** Over the valid part of a (thickness,
spacing) grid the strut force Cf and its capacity Cr both move a long way
and their ratio stays at exactly 1.3200; the column node stays at 1.036 and
the pile nodes at 3.584. The only reading the geometry moves is the tie
steel. Control: changing the design code moves the governing factor - 1.036
on CSA-A23.3:2019, 0.717 on ACI 318 - 2019, 0.660 on Eurocode 2 - 2004,
0.563 on SABS 0100 - 2000. The edge of the map is C16 declining the layout
outright (*"Pile cap depth:pile spacing smaller than 1:2"*), so a script
that catches exceptions only to skip them throws away the one sentence that
says where the edge is. See
`charts-and-plotting/pile_cap_strut_and_tie_map.py`.

**Two of C15's shear checks silently do not run.** On a 247-footing grid,
one-way shear was not checked on 39 footings and punching on 91: the
critical section or the perimeter falls outside the footing, the engine
publishes zero for both demand and capacity, and `v <= vc` reads `0 <= 0`
and passes. Test the CAPACITY for zero before dividing by it. The same
script re-reads one sweep against six allowable bearing pressures with no
extra engine calls, which is sound only because C15 derives nothing from
the allowable you supply - verified by tripling it and comparing the
reported pressure with `==`. See
`charts-and-plotting/pad_footing_feasible_region.py`.

**C23's critical perimeters are exactly rectangular, and one of three
levers cannot touch the face check.** `ucrit` equals `2((w+2r)+(b+2r))` on
all five rings to the digit, while the rounded-corner alternative differs
by 600 to 1900 mm - which is the control that makes the match a match, and
what licenses drawing the head to scale. On a failing head, adding flexural
steel leaves vu/vcu at 1.631 across its entire range, unchanged to three
decimals, while thickening the slab and enlarging the column both move it.
And the link steel per ring is not monotonic: 2441, 1196, 1487, 0, 0 mm2 -
detailing outward and stopping at the first light ring stops one ring too
early. See `charts-and-plotting/punching_shear_perimeter_plan.py`.

**A cost sweep returns the thinnest web you let it consider.** The cheapest
beam section on a 345-point (width, depth) grid sits on the narrow EDGE of
the priced range at 150 mm, running at only 60 % of the shear ceiling - so
the engine is not what stopped it, the grid is. Held at a buildable 300 mm
web the cheapest is 300 x 675 mm at +13.5 %, and at that width every depth
from 600 to 775 mm is within 2 % of the best. The number worth taking to a
meeting is the second one. See
`charts-and-plotting/beam_section_cost_surface.py`.

**BS8110's basic span/depth ratio is thin on every span measured.** For
25 + 15 kN/m on a 300 mm web over three equal spans, the depth that
actually meets span/250 exceeds span/26 by 158 mm at 5 m and by 362 mm at
14 m - ten spans out of ten. The basic ratio is meant to be multiplied by a
tension-steel modification factor, and this comparison deliberately uses it
the way a first size is sketched, unmodified. See
`charts-and-plotting/continuous_beam_span_depth_chart.py`.

**The self-weight loop MOVES a slab's economic thickness; it does not
create the minimum.** The obvious claim - freeze the load and the cost
curve falls forever - is wrong. With the self weight frozen the minimum is
still interior, because concrete traded against steel already produces one.
What the feedback does is shift the economic thickness thinner by one grid
step (25 mm) on each of three spans, because a thicker slab is charged for
its own extra weight. The control refuted the claim and produced the better
number. See `charts-and-plotting/rectangular_slab_thickness_economics.py`.

## The tooling

| Tool | What it does |
|---|---|
| `_tools/verify-everything.py` | **the master script.** Runs all four gates below in failure-legibility order and reports one verdict. An early gate failing does not stop the later ones |
| `_tools/run-example.py` | runs ONE example exactly as an engineer runs it - `import prokon.v5`, nothing else - in a temp working directory, under cp437 |
| `_tools/run-all-examples.py` | **the gate.** Runs every example, checks the header and this ledger, flags non-ASCII stdout, non-zero exit if anything fails |
| `_tools/check-pinned-values.py` | **the numeric oracle.** 40 pinned values across 12 engines, compared with `==`. `--self-test` proves it can fail |
| `_tools/build-ledger.py` | regenerates the table below from the script headers. `--check` fails if it is stale |

### Reading a run while it happens

A full pass is around fourteen minutes, nearly all of it the example
sweep, so the sweep reports **per script and as it happens**: each one
prints its own name and `running` the instant it starts, and its name again
with `PASS` or `FAIL` the instant it ends, in **completion order**. A
failure prints its cause immediately, underneath itself. While a long
script holds a job slot, a heartbeat line every thirty seconds names what
is still in flight and how long it has been going.

**Measured 2026-09-08, and the reason the sweep was rewritten.** It used to
collect results with `ThreadPoolExecutor.map`, which yields in *submission*
order, so a finished script was withheld until every script submitted ahead
of it had also finished. On the twelve chart examples at `--jobs 6`:
`crack_widths_selection_map.py` finished at 67.6 s and printed at 194.3 s;
eight scripts finished before 460.6 s and all eight printed at 460.6 s; the
first result line arrived at 194.3 s. One slow script silenced the other
eleven. A full run produced **no progress line of any kind** - 0 `running`
lines and 0 heartbeats against 119 and 27 now.

Two smaller faults went with it, both measured with one planted script that
had no `Verified:` header and printed a cp437-encodable non-ASCII
character: the per-script note was *assigned* rather than appended when the
header was bad, erasing an already-recorded non-ASCII flag from the line;
and `nonascii` fed the exit code while having no end-of-run section, so a
script offending only on the ASCII rule made the sweep exit 1 with the word
"ASCII" appearing nowhere in its output.

`--timeout` is reachable from the master script for a measured reason:
`charts-and-plotting/general_column_capacity_rosette.py` runs 460.6 s alone
and exceeds the sweep's 600 s default under a full run's contention for six
job slots, timing out at exactly 600.0 s in two independent full runs.
Raising the limit is the honest response to a slow script; nothing here
lets a script be skipped. `--filter` narrows the sweep for testing the
harness itself, and a filtered run deliberately prints a verdict that is
**not** the words a passing full run prints, so it can never be read as a
pass for the tree.

```bash
# every gate, one verdict - the way to run this tree
<sealed-runtime>/python.exe _tools/verify-everything.py --jobs 6 --timeout 900

# the whole tree, as a reader's console would run it
<sealed-runtime>/python.exe _tools/run-all-examples.py --jobs 6

# the numbers, to the last binary digit
<sealed-runtime>/python.exe _tools/check-pinned-values.py
<sealed-runtime>/python.exe _tools/check-pinned-values.py --self-test

# this file
python _tools/build-ledger.py --check
```

## Execution notes

Every script in this tree was run through `_tools/run-example.py` on the
sealed Prokon Python runtime (CPython 3.13.15 with numpy 2.5.2, pandas
3.0.5, openpyxl 3.1.5 and matplotlib 3.11.1), importing the **shipped
`prokon` package** and resolving the engine through that package's own
declared sibling layout - no environment variable, exactly as an installed
copy resolves it. The 95 scripts outside `charts-and-plotting/` were run on
**2026-09-02**; the twelve inside it on **2026-09-04**.

The engine was **`prokon-automation.exe`**, the twelve-engine host, built at
Prokon.CLI `718fd5f` (`meta.producer_version`
`1.0.0+718fd5f52ba38b9e94a68b49d8949bf7f4933b1d`). The engine assemblies it
carries report their own versions independently - `beam_section`
`1.0.0-local+272acd6b`, `continuous_beam` `1.0.0-local+a155063c`, and so on
per module - which is the distinction `going-deeper/the_whole_envelope.py`
exists to make: `module_version` is the ENGINE's and `producer_version` is
the HOST's, and a calculation record needs the first one.

Sweep result: **95 scripts, 95 passed, 0 failed** on 2026-09-02, and
**12 scripts, 12 passed, 0 failed** on 2026-09-04 - every one ASCII-clean
under cp437. Pinned values: **40 of 40 exact.**

The twelve charts were additionally run in the **Spyder installation** -
CPython 3.12.11 (conda-forge) with matplotlib 3.10.9, the `prokon` package
installed into `spyder-6\envs\spyder-runtime`, and the engine at
`spyder-6\prokon-engine\prokon-automation.exe`. That copy reports the same
build (`beam_section 1.0.0-local+272acd6b`) and reproduces the anchors, so
the charts are verified against the SHIPPED pair as well as the build
tree's.

The historical per-engine build pins for the 2026-08-28/29 wave (which
verified each script against its own `c<nn>-*.exe`) are in this file's git
history at commit `0623f0d`. They are superseded: every script now runs on
the single binary, and the pinned values reproduce unchanged.

## Ledger

<!-- BEGIN GENERATED LEDGER -->

<!-- Generated by _tools/build-ledger.py from the scripts'
     own headers. Do not hand-edit this block: run the tool.
     The prose outside it is hand-written and never touched. -->

**172 example scripts.** Every row below is read out of that script's
own header, so the ledger cannot disagree with the file.

| Script | Example | Feature | Verified | Date | Checked against |
|---|---|---|---|---|---|
| `built-in-desktop-examples/C01/four_span_slab.py` | Built-in desktop example - Four span slab | continuous_beam (C01 Continuous Beam) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Cb.exe 5.3.14.28); long-term deflection differs as recorded in F-C01-13 and is labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C01/two_span_beam.py` | Built-in desktop example - Two span beam | continuous_beam (C01 Continuous Beam) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Cb.exe 5.3.14.28); deflection and crack width differ as recorded in F-C01-13 and are labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C02/five_span_bridge_deck.py` | Built-in desktop example - Five span bridge deck | prestressed_concrete (C02 Captain - prestressed concrete) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Captain.exe 5.3.6.0); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C02/two_span.py` | Built-in desktop example - Two span | prestressed_concrete (C02 Captain - prestressed concrete) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Captain.exe 5.3.6.0); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C02/verification.py` | Built-in desktop example - Verification | prestressed_concrete (C02 Captain - prestressed concrete) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Captain.exe 5.3.6.0); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C04/default_example.py` | Built-in desktop example - Default example | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Slab.exe 5.3.3.0); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C04/garage_slab.py` | Built-in desktop example - Garage slab | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Slab.exe 5.3.3.0); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C04/only_columns.py` | Built-in desktop example - Only columns | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Slab.exe 5.3.3.0); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C11/braced_slender_biaxial.py` | Built-in desktop example - Braced slender column with bi-axial bending | rectangular_column (C11 Rectangular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (RecCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C11/cantilever_biaxial.py` | Built-in desktop example - Cantilever column with bi-axial bending | rectangular_column (C11 Rectangular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (RecCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C11/short_column_axial_load.py` | Built-in desktop example - Short column with axial load | rectangular_column (C11 Rectangular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (RecCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C11/short_column_uniaxial_bending.py` | Built-in desktop example - Short column with uni-axial bending | rectangular_column (C11 Rectangular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (RecCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C11/unbraced_slender_biaxial.py` | Built-in desktop example - Unbraced slender column with bi-axial bending | rectangular_column (C11 Rectangular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (RecCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C12/braced_slender_column_with_biaxial_moment.py` | Built-in desktop example - Braced slender column with bi-axial moment | circular_column (C12 Circular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (CirCol.exe 5.4.0.0, Ver W5.4.00); load case 2's steel area differs because the desktop's summary table prints the critical case's steel on that row (a recorded desktop calcsheet defect) and is labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C12/cantilever_column_with_biaxial_bending.py` | Built-in desktop example - Cantilever column with bi-axial bending | circular_column (C12 Circular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (CirCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C12/short_column_with_axial_load.py` | Built-in desktop example - Short column with axial load | circular_column (C12 Circular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (CirCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C12/short_column_with_biaxial_moment.py` | Built-in desktop example - Short column with bi-axial moment | circular_column (C12 Circular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (CirCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C12/unbraced_column_with_biaxial_moment.py` | Built-in desktop example - Unbraced column with bi-axial moment | circular_column (C12 Circular Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (CirCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C13/semi_circle_example.py` | Built-in desktop example - Default Example 2 | general_column (C13 General Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (GenCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C13/u_shaped_example.py` | Built-in desktop example - Default Example 1 | general_column (C13 General Column) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (GenCol.exe 5.4.0.0, Ver W5.4.00); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C14/cantilever_wall.py` | Built-in desktop example - Cantilever wall | retaining_wall (C14 Retaining Wall) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Wall.exe 5.3.6.0, W5.3.06); the six stability and steel results differ because the desktop printed them with soil Poisson ratio 0 instead of the file's 0.5 (DEF-46), and are labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C14/gravity_wall.py` | Built-in desktop example - Gravity wall | retaining_wall (C14 Retaining Wall) | **MISSING** |  | (no Verified: line) |
| `built-in-desktop-examples/C14/propped_cantilever_wall.py` | Built-in desktop example - Propped cantilever wall | retaining_wall (C14 Retaining Wall) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Wall.exe 5.3.6.0, W5.3.06); sliding safety factor, both soil pressures and both steel areas differ because the desktop export predates the DevOps 10408 fix, and are labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C14/reservoir_wall.py` | Built-in desktop example - Reservoir wall | retaining_wall (C14 Retaining Wall) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Wall.exe 5.3.6.0, W5.3.06); the overturning safety factor differs because the desktop export predates the DevOps 10408 fix, and is labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C15/double_column.py` | Built-in desktop example - Double Column | pad_footing (C15 Pad Footing) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Base.exe 5.3.8.0, Ver W5.3.08 - 04 Aug 2026); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C15/uls_stability_checks.py` | Built-in desktop example - Single column: ULS stability checks | pad_footing (C15 Pad Footing) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Base.exe 5.3.8.0, Ver W5.3.08 - 04 Aug 2026); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C15/working_load_stability_checks.py` | Built-in desktop example - Single column: Working load stability checks | pad_footing (C15 Pad Footing) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Base.exe 5.3.8.0, Ver W5.3.08 - 04 Aug 2026); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C16/reference_example.py` | Built-in desktop example - Reference Example | pile_cap (C16 Pile Cap) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (PileCap.exe 5.3.8.0, Ver W5.3.08 - 12 Aug 2026); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C16/three_pile_example.py` | Built-in desktop example - Three Pile Example | pile_cap (C16 Pile Cap) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (PileCap.exe 5.3.8.0, Ver W5.3.08 - 12 Aug 2026); strut resistances (Nu) differ as recorded in F-C16-1 (the engine uses alpha_cc 1.0 where the desktop uses the UK Eurocode 0.85) and are labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C16/uls_example.py` | Built-in desktop example - ULS Example | pile_cap (C16 Pile Cap) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (PileCap.exe 5.3.8.0, Ver W5.3.08 - 12 Aug 2026); strut resistances (Nu) differ as recorded in F-C16-1 (the engine uses alpha_cc 1.0 where the desktop uses the UK Eurocode 0.85) and are labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C21/beam_example.py` | Built-in desktop example - Beam Example | crack_widths (C21 Crack Widths) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (CrWidth.exe 5.3.7.0, W5.3.07); Ro %, tension capacity and the beam optimum steel stresses differ as recorded in F-C21-1, F-C21-2 and F-C21-3 and are labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C21/slab_example.py` | Built-in desktop example - Slab Example | crack_widths (C21 Crack Widths) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (CrWidth.exe 5.3.7.0, W5.3.07); Ro %, tension capacity and the Opt1/Opt2 bar arrangements chosen under the user-defined Ro critical differ as recorded in F-C21-1, F-C21-2 and F-C21-4 and are labelled as such; exact on prokon-automation.exe |
| `built-in-desktop-examples/C22/rectangular_beam.py` | Built-in desktop example - Rectangular beam | beam_section (C22 Beam Section) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (ConSec.exe 5.3.5.0, Ver W5.3.05); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C22/t_beam.py` | Built-in desktop example - T-beam | beam_section (C22 Beam Section) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (ConSec.exe 5.3.5.0, Ver W5.3.05); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C23/column_head_example.py` | Built-in desktop example - Column head example | punching_shear (C23 Punching Shear) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Punch.exe 5.3.6.0, Ver W5.3.06 - 26 Aug 2026); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C23/corner_column_example.py` | Built-in desktop example - Corner column example | punching_shear (C23 Punching Shear) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Punch.exe 5.3.6.0, Ver W5.3.06 - 26 Aug 2026); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C23/edge_column_example.py` | Built-in desktop example - Edge column example | punching_shear (C23 Punching Shear) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Punch.exe 5.3.6.0, Ver W5.3.06 - 26 Aug 2026); no differences; exact on prokon-automation.exe |
| `built-in-desktop-examples/C23/internal_column_example.py` | Built-in desktop example - Internal column example (imperial units) | punching_shear (C23 Punching Shear) | **MISSING** |  | (no Verified: line) |
| `built-in-desktop-examples/C23/standard_example.py` | Built-in desktop example - Default Example | punching_shear (C23 Punching Shear) | **yes** | 2026-10-02 | every result checked against the desktop calcsheet export of this save file (Punch.exe 5.3.6.0, Ver W5.3.06 - 26 Aug 2026); no differences; exact on prokon-automation.exe |
| `carbon-and-cost/beam_section_carbon_vs_depth.py` | The lowest-carbon beam - and why the depth is not the lever | beam_section (C22 Beam Section) | **yes** | 2026-09-09 | the pinned 300 x 500 reference reproduces mu = 295.18197048179997; carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/circular_column_carbon_of_concrete_grade.py` | Does a higher concrete grade lower the carbon? Column edition | circular_column (C12 Circular Column) | **yes** | 2026-09-09 | carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/continuous_beam_carbon_take_off.py` | A real quantity take-off - integrating a beam's steel envelope | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-09 | carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/crack_widths_carbon_of_durability.py` | What durability costs - the carbon price of a crack limit | crack_widths (C21 Crack Widths) | **yes** | 2026-09-09 | carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/general_column_carbon_of_the_shape.py` | Same area, different shape - which column shape is lowest carbon? | general_column (C13 General Column) | **yes** | 2026-09-09 | carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/pad_footing_carbon_wide_or_thick.py` | Wide and thin, or small and thick? A footing's carbon map | pad_footing (C15 Pad Footing) | **yes** | 2026-09-09 | the `yf` thickness reading confirmed by back-calculation from the engine's own mdes_x to within 0.5 %; carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/pile_cap_carbon_how_many_piles.py` | How many piles? The cap grows faster than you expect | pile_cap (C16 Pile Cap) | **yes** | 2026-09-09 | carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/prestressed_concrete_carbon_of_a_pt_slab.py` | A post-tensioned slab's carbon - the engine weighs it for you | prestressed_concrete (C02 Captain) | **yes** | 2026-09-09 | the `quantities` units confirmed by slab_area = 5.0 x 8.0 m; carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/punching_shear_carbon_thicken_or_reinforce.py` | Thicken the slab or add links? The carbon answer | punching_shear (C23 Punching Shear) | **yes** | 2026-09-09 | the asv units confirmed against the engine's own bar suggestion (6941 mm2 -> 35Y16); carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/rectangular_column_carbon_where_it_is_not.py` | Where a column's carbon is NOT - and one sweep that is wasted | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-09 | carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/rectangular_slab_carbon_per_square_metre.py` | The slab is the carbon - kgCO2e per square metre, by thickness | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | the carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `carbon-and-cost/retaining_wall_carbon_base_or_stem.py` | A retaining wall's carbon - spend it on the base or the stem? | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-09 | carbon arithmetic reproduces the published IStructE worked example (in-script assert); every engine figure measured on prokon-automation.exe |
| `cb-reinforcement-study/cb1_live_load_sweep.py` | CB1 live-load sweep - required reinforcement, two design codes | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-18 | CB1.C01 and CB2.C01 differ ONLY in the loads they store (live 10 against 50 kN/m) and this script discards stored loads, so the two must give IDENTICAL results - measured 2026-09-18, stored loads differ and every envelope comes back identical, which makes the pair a control that can respond rather than a coincidence; the anchor reproduces its pinned values; every sweep point measured on prokon-automation.exe |
| `cb-reinforcement-study/cb1_steel_tonnage_vs_live_load.py` | CB1 - total tonnage of reinforcing steel against live load | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-18 | CB1.C01 and CB2.C01 differ ONLY in the loads they store (live 10 against 50 kN/m) and this script discards stored loads, so the two must give IDENTICAL results - measured 2026-09-18, stored loads differ and every envelope comes back identical, which makes the pair a control that can respond rather than a coincidence; the anchor reproduces its pinned values; every sweep point measured on prokon-automation.exe; the link length is pinned too, being the one number that would move if the layout were read wrongly while the analysis still succeeded |
| `charts-and-plotting/beam_section_cost_surface.py` | The cost surface of a beam - and how flat the floor of the valley is | beam_section (C22 Beam Section) | **yes** | 2026-09-04 | the pinned 300 x 500 reference section reproduces its mu/ast; every one of the 345 priced sections measured on prokon-automation.exe |
| `charts-and-plotting/circular_column_slenderness_map.py` | Where slenderness starts to cost money - a map, and the crossover chart | circular_column (C12 Circular Column) | **yes** | 2026-09-04 | the desktop's own short-column example reproduces its pinned total_as; every one of the 273 columns measured on prokon-automation.exe |
| `charts-and-plotting/continuous_beam_span_depth_chart.py` | The span/depth chart every engineer wants - drawn from real deflections | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-04 | the pinned two-span beam reproduces its steel/deflection/crack quadruple; every one of the 180 beams measured on prokon-automation.exe |
| `charts-and-plotting/crack_widths_selection_map.py` | The crack-width selection map - and the trap inside it | crack_widths (C21 Crack Widths) | **yes** | 2026-09-04 | the pinned reference slab reproduces its triple; every arrangement, cover and code measured on prokon-automation.exe, with each arrangement's capacity checked before its crack width was believed |
| `charts-and-plotting/general_column_capacity_rosette.py` | The biaxial capacity rosette - four shapes, same concrete, same steel | general_column (C13 General Column) | **yes** | 2026-09-08 | the pinned 400 mm square reproduces both Case factors; every rosette point measured on prokon-automation.exe, with the square's four-fold and the rectangle's two-fold symmetry as the search's own controls. Batched 2026-09-08 (916 engine calls to 61, 489 s to 31 s) and re-verified by diffing the whole printed report against the one-call-at-a-time run: every computed number byte-identical, only the call counts differ |
| `charts-and-plotting/pad_footing_feasible_region.py` | The feasible region of a pad footing - four checks, one cost map | pad_footing (C15 Pad Footing) | **yes** | 2026-09-04 | the golden 2.5 x 2.5 x 0.6 m footing reproduces its pinned sls.pm and vcx; every footing in the map measured on prokon-automation.exe |
| `charts-and-plotting/pile_cap_strut_and_tie_map.py` | The pile cap as a truss - the strut-and-tie plan and the design boundary | pile_cap (C16 Pile Cap) | **yes** | 2026-09-04 | the CSA reference cap reproduces its pinned strut/node/overhang triple; every cap, code and refusal measured on prokon-automation.exe |
| `charts-and-plotting/prestressed_concrete_stress_window.py` | The post-tensioned floor, drawn - tendon profile, stress envelopes, design window | prestressed_concrete (C02 Captain) | **yes** | 2026-09-04 | the desktop's own DEFAULT EXAMPLE reproduces its pinned punching veff triple; every strip in the design window measured on prokon-automation.exe |
| `charts-and-plotting/punching_shear_perimeter_plan.py` | The column head, drawn to scale - five perimeters and three levers | punching_shear (C23 Punching Shear) | **yes** | 2026-09-04 | the pinned 400 sq head reproduces its uo and perimeter-1 Asv; every head measured on prokon-automation.exe, and every drawn perimeter checked against the engine's own ucrit |
| `charts-and-plotting/rectangular_column_interaction_map.py` | The N-M interaction chart, drawn from the engine instead of a handbook | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-04 | the pinned SABS 400 x 400 column reproduces its ast and perc; every one of the 377 interaction points measured on prokon-automation.exe |
| `charts-and-plotting/rectangular_slab_thickness_economics.py` | How thick should the slab be? The self-weight loop, drawn | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | the anchor reproduces the desktop calcsheet for its own Default Example (689 / 349 / 1106 / 566); the 143-cell map, the frozen-self-weight control and all 29 codes measured on prokon-automation.exe |
| `charts-and-plotting/retaining_wall_section_and_sizing.py` | The wall drawn to scale - section, pressures, and the sizing map | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-18 | the C14 desktop-parity wall reproduces its pinned five; every wall in the sizing map measured on prokon-automation.exe; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example |
| `checking/check_beam_schedule.py` | Independent check of a beam schedule off a drawing | continuous_beam + beam_section (C01 Continuous Beam + C22 Beam Section) | **yes** | 2026-09-02 | the reference beam reproduces the pinned steel/deflection/crack values; every schedule row measured on prokon-automation.exe |
| `checking/check_column_schedule_second_code.py` | Re-checking a column schedule against a second design code | rectangular_column + circular_column (C11 + C12) | **yes** | 2026-09-02 | both reference columns reproduce their pinned values; every schedule row measured on prokon-automation.exe |
| `checking/check_flat_slab_bay.py` | Independent check of a flat-slab bay, steel and column head | rectangular_slab + punching_shear (C04 Rectangular Slab + C23 Punching Shear) | **yes** | 2026-09-10 | the slab anchor reproduces the desktop calcsheet for its own Default Example (689 / 349 / 1106 / 566) and the head anchor its pinned uo/Asv; every bay measured on prokon-automation.exe |
| `checking/check_foundation_schedule.py` | Independent check of a foundation schedule - pads and pile caps | pad_footing + pile_cap (C15 Pad Footing + C16 Pile Cap) | **yes** | 2026-09-02 | both references reproduce their pinned values; every schedule row measured on prokon-automation.exe |
| `checking/check_pt_beam_and_odd_column.py` | Checking a PT beam and the odd-shaped column under it | prestressed_concrete + general_column (C02 Captain + C13 General Column) | **yes** | 2026-09-02 | the desktop's own PT example reproduces its pinned punching triple, and the Case A column its pinned factor; every variant measured on prokon-automation.exe |
| `checking/check_retaining_wall_and_cracks.py` | Independent check of a retaining wall - stability and cracking | retaining_wall + crack_widths (C14 Retaining Wall + C21 Crack Widths) | **yes** | 2026-09-18 | the parity wall reproduces its pinned stability values and the reference slab its pinned triple; every wall measured on prokon-automation.exe; the wall pair re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example (the C21 crack triple is untouched) |
| `design-code-comparisons/beam_section_sabs_vs_eurocode_moment.py` | One beam section, a growing moment - and two codes that cap the neutral axis differently | beam_section (C22 Beam Section) | **yes** | 2026-09-07 | the pinned 300 x 500 section reproduces its mu and ast exactly at the sweep's m = 200 kNm point; every moment measured on prokon-automation.exe |
| `design-code-comparisons/circular_column_sabs_vs_eurocode_length.py` | One circular column, growing taller - and two codes that measure slenderness differently | circular_column (C12 Circular Column) | **yes** | 2026-09-07 | the pinned 220 mm column reproduces its total_as exactly at the sweep's L = 2250 mm point; every length measured on prokon-automation.exe |
| `design-code-comparisons/continuous_beam_sabs_vs_eurocode_span.py` | Two spans, growing longer - the codes agree on flexure, disagree on shear, and disagree in DIRECTION on cracking | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-07 | the pinned two-span beam reproduces all five of its pinned values exactly at the sweep's 6 m point; every span measured on prokon-automation.exe |
| `design-code-comparisons/crack_widths_sans_vs_eurocode_moment.py` | One slab section, a growing service moment - the national adoption is worth 0.6 %, the generation change 30 % | crack_widths (C21 Crack Widths) | **yes** | 2026-09-07 | the pinned reference slab reproduces its crack width, steel area and moment capacity exactly at the sweep's m = 50 kNm/m point; every moment measured on prokon-automation.exe |
| `design-code-comparisons/general_column_sabs_vs_eurocode_length.py` | One general column, growing taller - and two codes that disagree about WHICH load case governs | general_column (C13 General Column) | **yes** | 2026-09-07 | the pinned 400 mm square reproduces both capacity factors and all three section values exactly at the sweep's 3 m point; every length measured on prokon-automation.exe |
| `design-code-comparisons/pad_footing_sabs_vs_eurocode_size.py` | One pad footing, growing wider - where the code matters and where the soil has already decided | pad_footing (C15 Pad Footing) | **yes** | 2026-09-07 | the golden 2.5 x 2.5 x 0.6 m footing reproduces its pinned sls pressure, uls pressure and vcx exactly at the sweep's 2.5 m point; every size measured on prokon-automation.exe |
| `design-code-comparisons/pile_cap_sabs_vs_eurocode_load.py` | One pile cap, a growing load - and three checks that favour OPPOSITE codes | pile_cap (C16 Pile Cap) | **yes** | 2026-09-07 | the CSA reference cap reproduces its pinned overhang, strut capacity, both node capacities and its minimum tie steel exactly; every load measured on prokon-automation.exe |
| `design-code-comparisons/prestressed_concrete_sabs_vs_eurocode_load.py` | One post-tensioned floor, a growing live load - and a code change that only touches the EDGE columns | prestressed_concrete (C02 Captain) | **yes** | 2026-09-07 | the desktop's own DEFAULT EXAMPLE reproduces all three pinned punching veff values exactly at the sweep's 15 kN/m point; every load measured on prokon-automation.exe |
| `design-code-comparisons/punching_shear_sabs_vs_eurocode_load.py` | One column head, a growing load - and two codes that measure a different perimeter | punching_shear (C23 Punching Shear) | **yes** | 2026-09-07 | the pinned 400 sq head reproduces its uo and perimeter-1 asv exactly; each code's drawn control perimeter reproduces the engine's own ucrit; every load measured on prokon-automation.exe |
| `design-code-comparisons/rectangular_column_sabs_vs_eurocode_length.py` | One column, growing taller - the old South African code against the new one's parent | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-07 | the pinned SABS 400 x 400 column IS the L = 4000 mm point of this sweep and reproduces its ast and perc exactly; every length measured on prokon-automation.exe |
| `design-code-comparisons/rectangular_slab_sabs_vs_eurocode_moment.py` | One slab panel, a growing load - what the design code changes, and what it does not | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | the identical-moments control asserted in-script on all four faces at two loads; the ten-point load sweep and the h = 150.5 mm designability threshold measured on prokon-automation.exe |
| `design-code-comparisons/retaining_wall_sabs_vs_eurocode_height.py` | One retaining wall, growing taller - and the concrete code that does not touch the stability | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-18 | the pinned wall reproduces all five of its pinned values exactly at the sweep's h1 = 5.0 m point; every height measured on prokon-automation.exe; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example |
| `design-studies/beam_section_design_charts.py` | Beam section design charts - depth, flange and torsion | beam_section (C22 Beam Section) | **yes** | 2026-09-02 | the 300x500 BS8110 anchor reproduces the pinned mu/ast; every other row measured on prokon-automation.exe |
| `design-studies/circular_column_slenderness.py` | Slenderness limits - twenty-one codes disagree, and by a lot | circular_column (C12 Circular Column) | **yes** | 2026-09-02 | the reference column reproduces the pinned total_as; every code and length measured on prokon-automation.exe |
| `design-studies/continuous_beam_span_depth.py` | Span/depth ratios, and what really drives a deflection | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-02 | the reference beam reproduces the pinned steel/deflection/crack values; every sweep row measured on prokon-automation.exe |
| `design-studies/crack_widths_code_behaviour.py` | Crack widths - what the thirteen codes actually do | crack_widths (C21 Crack Widths) | **yes** | 2026-09-02 | the reference slab reproduces the pinned triple; every code cell measured on prokon-automation.exe |
| `design-studies/general_column_shape_study.py` | Does the SHAPE pay? Six sections of identical area, compared | general_column (C13 General Column) | **yes** | 2026-09-02 | the 400 mm square anchor reproduces the pinned Case A factor; every shape measured on prokon-automation.exe |
| `design-studies/pad_footing_sensitivity.py` | What actually sizes a pad footing | pad_footing (C15 Pad Footing) | **yes** | 2026-09-02 | the reference footing reproduces the pinned sls.pm / vcx; every sweep row measured on prokon-automation.exe |
| `design-studies/pile_cap_layout_and_codes.py` | Pile caps - pile count, spacing, depth and the four codes | pile_cap (C16 Pile Cap) | **yes** | 2026-09-02 | the CSA reference cap reproduces its pinned strut/node values; every layout row measured on prokon-automation.exe |
| `design-studies/prestressed_concrete_balanced_load.py` | How much prestress? The balanced-load sweep, and what it costs | prestressed_concrete (C02 Captain) | **yes** | 2026-09-02 | the desktop's own example model reproduces its pinned punching veff triple; every sweep row measured on prokon-automation.exe |
| `design-studies/punching_shear_remedies.py` | Punching shear - the four remedies, priced against each other | punching_shear (C23 Punching Shear) | **yes** | 2026-09-02 | the reference head reproduces the pinned uo and perimeter-1 Asv; every remedy row measured on prokon-automation.exe |
| `design-studies/rectangular_column_interaction.py` | Biaxial interaction and slenderness, mapped | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-02 | the SABS anchor reproduces the pinned 4521.0 mm2 / 2.825 %; every cell measured on prokon-automation.exe |
| `design-studies/rectangular_slab_all_codes.py` | One slab panel, twenty-nine design codes | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | the BS8110 anchor reproduces the desktop's own calcsheet for its Default Example (689 / 349 / 1106 / 566); every code cell and both annex groups measured on prokon-automation.exe |
| `design-studies/retaining_wall_sizing_and_sensitivity.py` | Sizing a retaining wall, and what the answer is sensitive to | retaining_wall (C14 Retaining Wall) - all FOUR of its commands | **yes** | 2026-09-18 | the parity wall reproduces its pinned stability values; every sweep row and every find_* result measured on prokon-automation.exe; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example |
| `going-deeper/a_batch_that_never_dies.py` | A batch that finishes - every failure mode, handled | circular_column + general_column (C12 + C13) - the pattern, not one engine | **yes** | 2026-09-09 | every failure mode, and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/beam_section_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | beam_section (C22 Beam Section) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/circular_column_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | circular_column (C12 Circular Column) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/continuous_beam_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/crack_widths_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | crack_widths (C21 Crack Widths) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/general_column_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | general_column (C13 General Column) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/limits_timeouts_and_batching.py` | Limits - how big a call can be, and how long it may take | rectangular_column + continuous_beam (C11 + C01) - the transport | **yes** | 2026-09-09 | every limit and refusal, and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/pad_footing_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | pad_footing (C15 Pad Footing) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/pile_cap_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | pile_cap (C16 Pile Cap) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/prestressed_concrete_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | prestressed_concrete (C02 Captain) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/punching_shear_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | punching_shear (C23 Punching Shear) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/reading_nested_results_safely.py` | Reading a deeply nested result without tripping over it | crack_widths + prestressed_concrete (C21 + C02) - the deepest results here | **yes** | 2026-09-02 | every shape and hazard measured on prokon-automation.exe |
| `going-deeper/rectangular_column_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/rectangular_slab_error_handling.py` | Error handling - what a failed call looks like, and how to branch on it | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | behavioural: every printed category/code/hint, the transposed direction message measured BOTH ways, and all four silent successes measured on prokon-automation.exe |
| `going-deeper/retaining_wall_error_handling.py` | Error handling — what a failed call looks like, and how to branch on it | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-09 | behavioural: every printed category/code/hint and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/the_whole_envelope.py` | The whole envelope - everything analyse() hands you | beam_section + punching_shear + rectangular_slab (C22 + C23 + C04) - the transport, not any one engine | **yes** | 2026-09-10 | every field and behaviour, and the envelope on ProkonError measured for all three failure states, on prokon-automation.exe |
| `going-deeper/units_and_sign_conventions.py` | Units and signs - the mistakes that produce plausible answers | pile_cap + pad_footing + retaining_wall (C16 + C15 + C14) | **yes** | 2026-09-02 | every unit and sign behaviour measured on prokon-automation.exe |
| `quickstarts/beam_section_quickstart.py` | Beam section — your first analysis | beam_section (C22 Beam Section) | **yes** | 2026-09-02 | mu/ast match values pinned in the C22 test suite; exact on prokon-automation.exe |
| `quickstarts/circular_column_quickstart.py` | Circular column — your first analysis | circular_column (C12 Circular Column) | **yes** | 2026-09-02 | As matches the value pinned in the C12 test suite and the desktop calcsheet; exact on prokon-automation.exe |
| `quickstarts/continuous_beam_quickstart.py` | Continuous beam — your first analysis | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-02 | steel/deflection/crack values match the C01 goldens AND the desktop calcsheet transcription; exact on prokon-automation.exe |
| `quickstarts/crack_widths_quickstart.py` | Crack widths — your first analysis | crack_widths (C21 Crack Widths) | **yes** | 2026-09-02 | crack width and steel area match values pinned in the C21 test suite; exact on prokon-automation.exe |
| `quickstarts/general_column_quickstart.py` | General column — your first analysis | general_column (C13 General Column) | **yes** | 2026-09-02 | case 1 matches the values pinned in the C13 test suite; exact on prokon-automation.exe |
| `quickstarts/pad_footing_quickstart.py` | Pad footing — your first analysis | pad_footing (C15 Pad Footing) | **yes** | 2026-09-02 | bearing pressure, As and shear match the C15 goldens and the desktop parity probe; exact on prokon-automation.exe |
| `quickstarts/pile_cap_quickstart.py` | Pile cap — your first analysis | pile_cap (C16 Pile Cap) | **yes** | 2026-09-02 | cap size, pile reaction, strut and node values match the C16 test suite; exact on prokon-automation.exe |
| `quickstarts/prestressed_concrete_quickstart.py` | Prestressed concrete — your first analysis | prestressed_concrete (C02 Captain) | **yes** | 2026-09-02 | every printed value matches the desktop program's own; exact on prokon-automation.exe |
| `quickstarts/punching_shear_quickstart.py` | Punching shear — your first column head | punching_shear (C23 Punching Shear) | **yes** | 2026-09-02 | perimeter-1 Asv matches the value pinned in the C23 test suite; exact on prokon-automation.exe |
| `quickstarts/rectangular_column_quickstart.py` | Rectangular column — your first design | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-02 | Ast/% match the value pinned against the desktop in the C11 test suite; exact on prokon-automation.exe |
| `quickstarts/rectangular_slab_quickstart.py` | Rectangular slab - your first panel | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | this is the desktop program's OWN Default Example; all four ast values and all four moments reproduce the ENVELOPE MAXIMUM row of its calcsheet, saved in Slab.exe 5.3.3.0 |
| `quickstarts/retaining_wall_quickstart.py` | Retaining wall — your first analysis | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-18 | re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example. They agree with the envelope C14 re-pinned to (4.476/1.634/97.29, steel 916.53/792.46) to 0.008-0.075%; exact on prokon-automation.exe |
| `recipes/beam_section_bar_bending_schedule.py` | A bar bending schedule, straight to CSV | beam_section (C22 Beam Section) | **yes** | 2026-09-02 | the 300x500 BS8110 anchor reproduces the pinned mu/ast; every schedule row measured on prokon-automation.exe |
| `recipes/beam_section_batch_to_excel.py` | Beam section — a batch of load cases to Excel | beam_section (C22 Beam Section) | **yes** | 2026-09-02 | the 300x500 BS8110 row matches values pinned in the C22 test suite; exact on prokon-automation.exe |
| `recipes/beam_section_optimal_depth.py` | Beam section — goal-seek the most economical depth | beam_section (C22 Beam Section) | **yes** | 2026-09-02 | Mu at h=400/500/600/700 match values pinned in the C22 test suite; exact on prokon-automation.exe |
| `recipes/circular_column_batch_to_excel.py` | Circular column — a whole column schedule to Excel | circular_column (C12 Circular Column) | **yes** | 2026-09-02 | the C1 reference row matches the value pinned in the C12 test suite; exact on prokon-automation.exe |
| `recipes/circular_column_design_chart.py` | A design chart for the office wall - diameter against load | circular_column (C12 Circular Column) | **yes** | 2026-09-02 | the reference column reproduces its pinned total_as; every chart point measured on prokon-automation.exe |
| `recipes/circular_column_smallest_diameter.py` | Circular column — goal-seek the smallest diameter that works | circular_column (C12 Circular Column) | **yes** | 2026-09-02 | every sweep row measured against the built 5.4 surface; exact on prokon-automation.exe |
| `recipes/continuous_beam_batch_to_excel.py` | Continuous beam — a beam schedule to Excel | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-02 | the B1 row matches the C01 goldens and the desktop calcsheet transcription; exact on prokon-automation.exe |
| `recipes/continuous_beam_calc_sheet.py` | A calculation sheet you can put in a file - text, not a screen | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-02 | the reference beam reproduces its pinned steel/deflection/crack values; the sheet is written and re-read |
| `recipes/continuous_beam_envelope_chart.py` | Continuous beam — plot the moment and shear envelopes | continuous_beam (C01 Continuous Beam) | **yes** | 2026-09-02 | envelope extremes match the C01 goldens; chart written and checked; exact on prokon-automation.exe |
| `recipes/crack_widths_bar_selection.py` | Crack widths — pick the lightest bar arrangement that meets a 0.2 mm limit | crack_widths (C21 Crack Widths) | **yes** | 2026-09-02 | the engine's Y10@75 row is the value pinned in the C21 test suite; every catalogue row measured; exact on prokon-automation.exe |
| `recipes/crack_widths_batch_to_excel.py` | Crack widths — a reservoir's whole element schedule to Excel | crack_widths (C21 Crack Widths) | **yes** | 2026-09-02 | the W1 row matches values pinned in the C21 test suite; spreadsheet re-read; exact on prokon-automation.exe |
| `recipes/crack_widths_selection_table.py` | A bar-selection lookup table for the office wall | crack_widths (C21 Crack Widths) | **yes** | 2026-09-02 | the reference slab reproduces its pinned triple; every cell measured on prokon-automation.exe |
| `recipes/general_column_batch_to_excel.py` | General column — a batch of columns to Excel | general_column (C13 General Column) | **yes** | 2026-09-02 | column C1 matches the value pinned in the C13 test suite; exact on prokon-automation.exe |
| `recipes/general_column_section_drawing.py` | Draw the section you just analysed | general_column (C13 General Column) | **yes** | 2026-09-02 | the Case A section reproduces its pinned capacity factor and gross area; the drawing is written and re-read |
| `recipes/general_column_smallest_section.py` | General column — goal-seek the smallest square column that works | general_column (C13 General Column) | **yes** | 2026-09-02 | the 400 mm row matches the value pinned in the C13 test suite; exact on prokon-automation.exe |
| `recipes/pad_footing_batch_to_excel.py` | Pad footing — a schedule of footings to Excel | pad_footing (C15 Pad Footing) | **yes** | 2026-09-02 | the F1 reference row matches the bearing pressure and steel areas pinned in the C15 golden and desktop-parity suites; exact on prokon-automation.exe |
| `recipes/pad_footing_schedule_to_csv.py` | A foundation schedule for the site engineer, as CSV | pad_footing (C15 Pad Footing) | **yes** | 2026-09-02 | the reference footing reproduces its pinned sls.pm / as_x / as_y / vcx; every mark measured on prokon-automation.exe |
| `recipes/pad_footing_smallest_plan_size.py` | Pad footing — goal-seek the smallest plan size that works | pad_footing (C15 Pad Footing) | **yes** | 2026-09-02 | the sweep's shear capacity matches the value pinned in the C15 golden suite; the answer re-measured on the built surface; exact on prokon-automation.exe |
| `recipes/pile_cap_batch_to_excel.py` | Pile cap — a schedule of caps to Excel | pile_cap (C16 Pile Cap) | **yes** | 2026-09-02 | PC1 matches the values pinned in the C16 test suite; the rest measured; exact on prokon-automation.exe |
| `recipes/pile_cap_pile_layout.py` | Pile cap — choose the pile layout for a column load | pile_cap (C16 Pile Cap) | **yes** | 2026-09-02 | every row measured against the built C16 surface; the CSA reference cap's pinned values reproduce; exact on prokon-automation.exe |
| `recipes/pile_cap_strut_tie_diagram.py` | Draw the strut-and-tie model the engine actually used | pile_cap (C16 Pile Cap) | **yes** | 2026-09-02 | the CSA reference cap reproduces its pinned strut Cr and node Pr; the diagram is written and re-read |
| `recipes/prestressed_concrete_balanced_load_sweep.py` | Prestressed concrete — how much prestress is enough? | prestressed_concrete (C02 Captain) | **yes** | 2026-09-02 | the reference model's envelope and tendon force match; exact on prokon-automation.exe |
| `recipes/prestressed_concrete_batch_to_excel.py` | Prestressed concrete — a batch of design variants to Excel | prestressed_concrete (C02 Captain) | **yes** | 2026-09-02 | the S1 row matches the desktop-pinned C02 parity; exact on prokon-automation.exe |
| `recipes/prestressed_concrete_tendon_profile.py` | The tendon profile and the desktop's own report, from one call | prestressed_concrete (C02 Captain) | **yes** | 2026-09-02 | the desktop's own example reproduces its pinned punching veff triple; the report and the chart are written and re-read |
| `recipes/punching_shear_batch_to_excel.py` | Punching shear — a floor's column heads to Excel | punching_shear (C23 Punching Shear) | **yes** | 2026-09-02 | the C1 row matches the Asv value pinned in the C23 test suite; exact on prokon-automation.exe |
| `recipes/punching_shear_drop_panel_depth.py` | Punching shear — how deep must the drop panel be? | punching_shear (C23 Punching Shear) | **yes** | 2026-09-02 | the sweep reproduces the depth-vs-Asv ladder pinned in the C23 test suite; exact on prokon-automation.exe |
| `recipes/punching_shear_link_layout.py` | A shear-link layout for the column heads, perimeter by perimeter | punching_shear (C23 Punching Shear) | **yes** | 2026-09-02 | the reference head reproduces its pinned uo and perimeter-1 Asv; every head measured on prokon-automation.exe |
| `recipes/rectangular_column_code_comparison.py` | Rectangular column — the same column through twelve design codes | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-02 | six of the twelve rows match values pinned against the desktop in the C11 test suite; exact on prokon-automation.exe |
| `recipes/rectangular_column_schedule_to_excel.py` | A column schedule a detailer can work from | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-02 | the reference column reproduces its pinned 4521.0 mm2 / 2.825 %; every level measured on prokon-automation.exe |
| `recipes/rectangular_column_smallest_section.py` | Rectangular column — goal-seek the smallest column that works | rectangular_column (C11 Rectangular Column) | **yes** | 2026-09-02 | the 400 mm row's Ast matches the value pinned against the desktop in the C11 test suite; exact on prokon-automation.exe |
| `recipes/rectangular_slab_batch_to_excel.py` | Rectangular slab - a schedule of panels to Excel | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | S1 is the desktop program's own Default Example and reproduces its calcsheet quadruple 689 / 349 / 1106 / 566 mm2/m; every other row measured on prokon-automation.exe |
| `recipes/rectangular_slab_minimum_thickness.py` | Rectangular slab - goal-seek the thinnest workable slab | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | every sweep row measured on prokon-automation.exe, including the declined-face boundary (both y faces declined at h = 110 and 120 mm, designed from 130 mm up) |
| `recipes/rectangular_slab_reinforcement_schedule.py` | A slab reinforcement schedule, ready for the drawing | rectangular_slab (C04 Rectangular Slab) | **yes** | 2026-09-10 | S1 is the desktop program's own Default Example and reproduces its calcsheet quadruple 689 / 349 / 1106 / 566; every other panel measured on prokon-automation.exe |
| `recipes/retaining_wall_base_stability.py` | Retaining wall — grow the base until the wall stands up | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-02 | the d = 2.50 m row matches the C14 desktop-parity calcsheet; exact on prokon-automation.exe |
| `recipes/retaining_wall_batch_to_excel.py` | Retaining wall — a schedule of walls to Excel | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-02 | the W1 row matches the C14 desktop-parity calcsheet; exact on prokon-automation.exe |
| `recipes/retaining_wall_stability_sheet.py` | A wall stability sheet, with the section drawn to scale | retaining_wall (C14 Retaining Wall) | **yes** | 2026-09-18 | the parity wall reproduces its pinned stability values; the sheet and the drawing are written and re-read; re-pinned 2026-09-18 after C14 DevOps 10408 (seismic active pressure below the water table); the fixed engine is desktop-verified by C14 refdata ff33d43 - seven calcsheet exports taken 2026-09-17 from a Wall.exe rebuilt with the fix, read out of machine-readable JSON - but these values were NOT re-taken from a desktop run of THIS example |
| `workflows/basement_wall_propped_by_slab.py` | Basement wall propped by the ground-floor slab | retaining_wall + rectangular_slab + continuous_beam + punching_shear (C14 Retaining Wall + C04 Rectangular Slab + C01 Continuous Beam + C23 Punching Shear) | **yes** | 2026-09-10 | every number measured on prokon-automation.exe across C14, C04, C01 and C23 |
| `workflows/bridge_pier_and_foundation.py` | Bridge pier - circular column, then piles against a spread base | circular_column + pile_cap + crack_widths + pad_footing (C12 Circular Column + C16 Pile Cap + C21 Crack Widths + C15 Pad Footing) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; both foundations take the same pier load |
| `workflows/buried_reservoir_structure.py` | A buried reservoir - perimeter wall, pilaster, centre column, PT roof | retaining_wall + general_column + circular_column + prestressed_concrete (C14 Retaining Wall + C13 General Column + C12 Circular Column + C02 Captain) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; each element takes the one above it |
| `workflows/column_schedule_whole_building.py` | A whole building's column schedule, six storeys, three column types | rectangular_column + circular_column + general_column + pad_footing (C11 Rectangular Column + C12 Circular Column + C13 General Column + C15 Pad Footing) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; loads accumulate floor by floor in-script |
| `workflows/flat_slab_load_path.py` | Flat-slab office bay — the whole load path, slab to founding | rectangular_slab + punching_shear + rectangular_column + pad_footing (C04 Rectangular Slab + C23 Punching Shear + C11 Rectangular Column + C15 Pad Footing) | **yes** | 2026-09-10 | every number measured on prokon-automation.exe across all four engines; load path asserted in-script |
| `workflows/frame_gravity_take_down.py` | Gravity load take-down - floor beam to column to footing | continuous_beam + beam_section + rectangular_column + pad_footing (C01 Continuous Beam + C22 Beam Section + C11 Rectangular Column + C15 Pad Footing) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; the reactions are C01's own |
| `workflows/piled_foundation_core_column.py` | L-shaped core column on a pile cap - shape, strut-and-tie, cracks | general_column + pile_cap + crack_widths + beam_section (C13 General Column + C16 Pile Cap + C21 Crack Widths + C22 Beam Section) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; the cap load is C13's own |
| `workflows/post_tensioned_versus_rc_floor.py` | Value engineering - a post-tensioned floor against an RC one | prestressed_concrete + continuous_beam + punching_shear + rectangular_slab (C02 Captain + C01 Continuous Beam + C23 Punching Shear + C04 Rectangular Slab) | **yes** | 2026-09-10 | every number measured on prokon-automation.exe across C02, C23 and C04 |
| `workflows/pt_bridge_deck_and_piers.py` | Post-tensioned bridge deck on circular piers and pile caps | prestressed_concrete + circular_column + pile_cap + punching_shear (C02 Captain + C12 Circular Column + C16 Pile Cap + C23 Punching Shear) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; the pier loads are C02's own |
| `workflows/pt_transfer_slab_over_basement.py` | A post-tensioned transfer slab over a piled basement box | prestressed_concrete + general_column + pile_cap + retaining_wall (C02 Captain + C13 General Column + C16 Pile Cap + C14 Retaining Wall) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; the column load is C02's own reaction |
| `workflows/reservoir_wall_crack_control.py` | Water-retaining reservoir wall - stability, steel, crack control | retaining_wall + crack_widths + rectangular_slab + beam_section (C14 Retaining Wall + C21 Crack Widths + C04 Rectangular Slab + C22 Beam Section) | **yes** | 2026-09-10 | every number measured on prokon-automation.exe across C14, C21, C04 and C22 |
| `workflows/transfer_beam_under_columns.py` | Transfer beam carrying two columns off a car-park grid | rectangular_column + continuous_beam + beam_section + crack_widths (C11 Rectangular Column + C01 Continuous Beam + C22 Beam Section + C21 Crack Widths) | **yes** | 2026-09-02 | every number measured on prokon-automation.exe; the point loads are C11's own |

### Coverage by engine

One row per engine, one column per category. The point of the
table is the TOTAL column: no engine is better documented
than another.

| Engine | quickstarts | going-deeper | recipes | workflows | design-studies | design-code-comparisons | checking | charts-and-plotting | carbon-and-cost | cb-reinforcement-study | built-in-desktop-examples | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `beam_section` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 2 | **17** |
| `circular_column` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 5 | **20** |
| `continuous_beam` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 2 | 2 | **19** |
| `crack_widths` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 2 | **17** |
| `general_column` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 2 | **17** |
| `pad_footing` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 3 | **18** |
| `pile_cap` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 3 | **18** |
| `prestressed_concrete` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 3 | **18** |
| `punching_shear` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 5 | **20** |
| `rectangular_column` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 5 | **20** |
| `rectangular_slab` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 3 | **18** |
| `retaining_wall` | 1 | 2 | 3 | 4 | 1 | 1 | 1 | 1 | 1 | 0 | 4 | **19** |
| **engine appearances** | 12 | 24 | 36 | 48 | 12 | 12 | 12 | 12 | 12 | 2 | 39 | **221** |

Minimum 17, maximum 20, spread 3.

<!-- END GENERATED LEDGER -->
