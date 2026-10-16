# PROKON Automation

Design with PROKON from Python. Write a script, call a PROKON program, get its answer back as
ordinary Python data — and do with it whatever Python can: loop over a hundred sections, chart
the results, write them to Excel, or feed one program's output into the next.

```python
import prokon.v5

beam = prokon.v5.beam_section.analyse(
    design_code="BS8110 - 1997",
    m=200, v=100,              # moment (kNm) and shear (kN)
    bw=300, h=500,             # width and depth (mm)
    dc_t=40, dc_b=40, dc_s=40, # cover to the centre of the top, bottom and side bars (mm)
    fcu=30, fy=450, fyv=450,   # concrete and steel strengths (MPa)
)

print(beam["result"]["mu"])    # 295.18197048179997  (moment capacity, kNm)
```

The calculation behind every call is the one the PROKON desktop program performs, so the
numbers your script gets are the numbers the desktop gives.

---

## 1. Pick your setup

There are three ways in. Each has its own installer and its own step-by-step guide.

**PROKON for Spyder** — *the easiest start.* Installs a ready-to-use Python editor with
PROKON already inside it. Nothing else to set up.
→ [Installing PROKON for Spyder](https://prokonsoftware.github.io/Automation/guide/installing-prokon-for-spyder.html)

**PROKON for VS Code** — *for people who already use Python.* Adds PROKON to a Python you
installed yourself, and you write scripts in VS Code.
→ [Installing PROKON for VS Code](https://prokonsoftware.github.io/Automation/guide/installing-prokon-for-vscode.html)

**PROKON Automation Host** — *to let an AI assistant do the design work.* Connects PROKON to
an AI tool such as Claude Code or OpenCode, so you can ask for a design in plain English.
→ [Installing the PROKON Automation Host](https://prokonsoftware.github.io/Automation/guide/installing-prokon-automation-host.html)

Whichever you choose, you need a Windows PC and a PROKON licence for the programs you want to
use, signed in through the PROKON License Manager.

## 2. Learn the basics

[Writing PROKON-Python scripts](https://prokonsoftware.github.io/Automation/guide/writing-prokon-python-scripts.html) covers the handful
of ideas every script relies on, and walks through the examples.

## 3. Run an example

The [`examples/`](examples/) folder holds 172 ready-to-run scripts. Open one, run it, and read
what it prints. Every script starts with a short note describing what it does and how its
results were checked.

Begin with [`quickstarts/`](examples/quickstarts/): one short, fully explained script for each
PROKON program. After that, browse by what you want to do:

| To… | Look in |
|---|---|
| Get everyday jobs done — find an economical section, run a batch, produce a schedule or an Excel sheet | [`recipes/`](examples/recipes/) |
| Design a whole element, passing results from one program to the next | [`workflows/`](examples/workflows/) |
| Explore a design — charts, interaction envelopes, slenderness, alternatives | [`design-studies/`](examples/design-studies/) |
| Draw a graph of a result | [`charts-and-plotting/`](examples/charts-and-plotting/) |
| Compare SANS/SABS with Eurocode on the same element | [`design-code-comparisons/`](examples/design-code-comparisons/) |
| Weigh the embodied carbon of different design choices | [`carbon-and-cost/`](examples/carbon-and-cost/) |
| Check a design someone else has done | [`checking/`](examples/checking/) |
| Handle errors, warnings, units and large batches properly | [`going-deeper/`](examples/going-deeper/) |
| Run the desktop programs' own example files and compare with their calcsheets | [`built-in-desktop-examples/`](examples/built-in-desktop-examples/) |
| Study continuous-beam reinforcement from desktop save files | [`cb-reinforcement-study/`](examples/cb-reinforcement-study/) |

Besides PROKON, the examples use only numpy, pandas, matplotlib, openpyxl and Python's
standard library.

How each script was checked is recorded in [`examples/VERIFICATION.md`](examples/VERIFICATION.md).

## The PROKON programs you can script

In a script, each program is reached by its Python name — `prokon.v5.<python name>`.

| PROKON program | Python name |
|---|---|
| Beam Section (C22) | `beam_section` |
| Captain - prestressed concrete (C02) | `prestressed_concrete` |
| Circular Column (C12) | `circular_column` |
| Continuous Beam (C01) | `continuous_beam` |
| Crack Widths (C21) | `crack_widths` |
| General Column (C13) | `general_column` |
| Pad Footing (C15) | `pad_footing` |
| Pile Cap (C16) | `pile_cap` |
| Punching Shear (C23) | `punching_shear` |
| Rectangular Column (C11) | `rectangular_column` |
| Rectangular Slab (C04) | `rectangular_slab` |
| Retaining Wall (C14) | `retaining_wall` |

## Licence

Use of this repository is governed by [LICENSE.md](LICENSE.md).
