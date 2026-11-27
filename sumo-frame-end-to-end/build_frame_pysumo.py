# build_frame_pysumo.py - builds and solves a 4-storey, 3-bay reinforced-concrete frame in Sumo.
#
# This is a PySumo script: it runs INSIDE Sumo (Sumo's own CPython 3.10, with PySumo and rf), not in your
# Python, and it cannot import prokon.v5. design_frame.py beside it runs it for you, through
#     prokon-automation sumo pysumo --inputs-from-stdin
# with {"script": <this file's text>, "material_db": ..., "section_db": ..., "save_project": ...} on stdin.
# An MCP client can run it the same way, as the script argument of the tool prokon_sumo_pysumo.
#
# Units are metres and kN; Y is vertical. It emits the frame's size and {case ID: name} for its load cases.
import PySumo as P
import rf

V = lambda x, y, z: P.IwVector3d(float(x), float(y), float(z))
model = P.current_model()
BAYS, STOREYS, BAY, STOREY = 3, 4, 6.0, 3.5

mdb = P.SoMaterialDB(); mdb.Read()
conc = mdb.Search("30 MPa", P.SoMaterial.eType.Concrete)
if conc is None:
    rf.fail("invalid_input", "30 MPa concrete is not in the material catalogue")
conc.SetName("C30")
model.add(conc)

col = P.SoSection.CreateRectangular(conc, 0.4, 0.4)
bm = P.SoSection.CreateRectangular(conc, 0.3, 0.6)
for s in (col, bm):
    model.add(s)

dead = P.SoLoadCase.Create("DL", "Self weight + finishes")
dead.SetSelfWeightCase(True)
live = P.SoLoadCase.Create("LL", "Imposed")
for c in (dead, live):
    model.add(c)

def member(a, b, sec):
    m = P.SoBeam.Create()
    m.SetCurve(P.SoLine.Create(V(*a), V(*b)))
    m.SetSection_1(sec)
    model.add(m)
    return m

def udl(host, case, w):
    u = P.SoBeamDistributedLoad.Create()
    u.SetHost(host); u.SetLoadCase(case)
    u.SetDirection(P.SoLoad.eLoadDirection.DIR_Y)
    u.SetStartLoad(-w); u.SetEndLoad(-w)
    model.add(u)

layout = {"columns": [], "beams": []}
for i in range(BAYS + 1):
    for j in range(STOREYS):
        member((i * BAY, j * STOREY, 0), (i * BAY, (j + 1) * STOREY, 0), col)
        layout["columns"].append([i, j + 1])
for j in range(1, STOREYS + 1):
    roof = j == STOREYS
    for i in range(BAYS):
        x0, xm, x1, y = i * BAY, i * BAY + BAY / 2, (i + 1) * BAY, j * STOREY
        for a, b in (((x0, y, 0), (xm, y, 0)), ((xm, y, 0), (x1, y, 0))):
            m = member(a, b, bm)
            udl(m, dead, 18.0 if roof else 25.0)   # kN/m superimposed dead (slab, finishes)
            udl(m, live, 6.0 if roof else 15.0)    # kN/m imposed
        layout["beams"].append([i + 1, j])

for i in range(BAYS + 1):
    base = P.SoPointSupport.Create()
    base.SetPoint(V(i * BAY, 0, 0))
    model.add(base)          # a new point support is fixed in all six directions

uls = P.SoLoadCombination.Create(); uls.SetName("ULS")
model.add(uls)
sls = P.SoLoadCombination.Create(); sls.SetName("SLS")
model.add(sls)
for combo, fd, fl in ((uls, 1.4, 1.6), (sls, 1.0, 1.0)):
    for case, f in ((dead, fd), (live, fl)):
        it = P.SoLoadCaseItem.Create()
        it.SetLoadCase(case); it.SetULSFactor(f); it.SetSLSFactor(f)
        combo.Add(it, combo, True)
    combo.SetActive(True)

cases = {o.GetID().GetValue(): o.GetName() for o in model.objects()
         if isinstance(o, (P.SoLoadCase, P.SoLoadCombination))}
rf.emit({"bays": BAYS, "storeys": STOREYS, "bay_m": BAY, "storey_m": STOREY, "cases": cases,
         "column_count": len(layout["columns"]), "beam_count": len(layout["beams"])})
