# PROKON Automation

Guides and runnable examples for scripting PROKON's design engines from Python:

```python
import prokon.v5

answer = prokon.v5.beam_section.analyse(
    design_code="BS8110 - 1997",
    m=200, v=100, bw=300, h=500,
    dc_t=40, dc_b=40, dc_s=40,
    fcu=30, fy=450, fyv=450,
)

print(answer["result"]["mu"])   # 295.18197048179997 kNm
```

Each call runs the same engine as the PROKON desktop program, so a script's numbers are the
desktop's numbers.

## Start here: choose how you want to work

| You want | Install | Guide |
|---|---|---|
| Something that works straight out of the box | **PROKON for Spyder** | [Installing PROKON for Spyder](guide/installing-prokon-for-spyder.html) |
| To use VS Code with your own Python | **PROKON for VS Code** | [Installing PROKON for VS Code](guide/installing-prokon-for-vscode.html) |
| An AI assistant (Claude Code or OpenCode) doing PROKON design work for you | **PROKON Automation Host** | [Installing the PROKON Automation Host](guide/installing-prokon-automation-host.html) |

Then read [Writing PROKON-Python scripts](guide/writing-prokon-python-scripts.html). It
explains the few ideas every script uses and tours the examples.

The guides are HTML pages. Open them in a browser from a downloaded copy of this repository,
so the links between them and into `examples/` work.

## What you need

- Windows.
- A PROKON licence for the engines you use, through the PROKON License Manager.
- One of the three installers above.

## The engines

| Python name | PROKON program |
|---|---|
| `continuous_beam` | C01 Continuous Beam |
| `prestressed_concrete` | C02 Captain (prestressed concrete) |
| `rectangular_slab` | C04 Rectangular Slab |
| `rectangular_column` | C11 Rectangular Column |
| `circular_column` | C12 Circular Column |
| `general_column` | C13 General Column |
| `retaining_wall` | C14 Retaining Wall |
| `pad_footing` | C15 Pad Footing |
| `pile_cap` | C16 Pile Cap |
| `crack_widths` | C21 Crack Widths |
| `beam_section` | C22 Beam Section |
| `punching_shear` | C23 Punching Shear |

## The examples

172 scripts in [`examples/`](examples/). Each runs as it is, prints its results, and opens
with a header saying what it shows and how its numbers were checked. They use only Python's
standard library plus numpy, pandas, matplotlib and openpyxl.

| Folder | Scripts | What you will find |
|---|---|---|
| [`quickstarts/`](examples/quickstarts/) | 12 | **Start here.** One short, fully commented script per engine |
| [`recipes/`](examples/recipes/) | 36 | Everyday tasks: economical designs, batch runs, schedules, calculation sheets, Excel output |
| [`workflows/`](examples/workflows/) | 12 | Complete multi-engine jobs, each engine fed by the last |
| [`design-studies/`](examples/design-studies/) | 12 | Design charts, interaction envelopes, slenderness, comparing remedies |
| [`charts-and-plotting/`](examples/charts-and-plotting/) | 12 | One matplotlib figure per engine, saved as a PNG |
| [`design-code-comparisons/`](examples/design-code-comparisons/) | 12 | The same element to SABS/SANS and to Eurocode |
| [`carbon-and-cost/`](examples/carbon-and-cost/) | 12 | The embodied carbon of design choices |
| [`checking/`](examples/checking/) | 6 | Independent checks of someone else's design |
| [`going-deeper/`](examples/going-deeper/) | 17 | Error handling, warnings, units, limits, robust batches |
| [`built-in-desktop-examples/`](examples/built-in-desktop-examples/) | 39 | The desktop programs' own example files, run from Python and compared with the desktop calcsheets |
| [`cb-reinforcement-study/`](examples/cb-reinforcement-study/) | 2 | A continuous-beam study driven from desktop files |

[`examples/VERIFICATION.md`](examples/VERIFICATION.md) records how every script was checked.
[`examples/_tools/`](examples/_tools/) holds the scripts that verify the examples themselves.

## Repository layout

```
guide/       the four guides (HTML)
examples/    the runnable example scripts, with their verification ledger
```
