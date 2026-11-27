# A frame built in Sumo and designed by four PROKON programs

A 4-storey, 3-bay reinforced-concrete frame, from nothing to a design schedule, with no number typed from one
program into the next:

1. **Sumo** builds the frame and solves it: `build_frame_pysumo.py`, a PySumo script that runs inside Sumo.
2. **Beam Section (C22)** designs every beam for hogging, sagging and shear.
3. **Rectangular Column (C11)** designs every column from its own axial force and end moments.
4. **Pad Footing (C15)** sizes every footing until the service bearing pressure is within 250 kPa.
5. **Crack Widths (C21)** checks the beam with the largest sagging moment.

`design_frame.py` runs all of it and writes a drawing of the frame, coloured by how hard each member works, and an
Excel schedule to `output/`. `verify_build.py` rebuilds the frame on its own and checks it against a hand
calculation of the loads.

## Running it

It needs the **PROKON Automation Host**, PROKON installed in `C:\PROKON` (for the material and section catalogues
and Sumo's licence manager), and a Sumo licence. Sumo is not part of PROKON for Spyder or PROKON for VS Code.

```
prokon-automation run design_frame.py
prokon-automation run verify_build.py
```

Run them from any folder. An MCP client can run them too, as the `path` of the `prokon_run_script` tool. If PROKON
is installed somewhere else, change `MATERIAL_DB` and `SECTION_DB` at the top of `design_frame.py` and in
`verify_build.py`.

## What it checks on itself

- The beam-section program reproduces its pinned value exactly.
- The frame solves.
- The ULS support reactions balance the ULS load: 4579.6 kN.
