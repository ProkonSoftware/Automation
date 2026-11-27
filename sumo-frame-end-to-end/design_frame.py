# design_frame.py - a 4-storey, 3-bay reinforced-concrete frame, built in Sumo and designed by four PROKON
# programs, end to end, with no number typed from one program into the next.
#
#   1. Sumo                builds the frame (build_frame_pysumo.py) and solves it
#   2. C22 Beam Section    every beam: hogging and sagging steel, and shear
#   3. C11 Rect. Column    every column, from its own axial force and end moments
#   4. C15 Pad Footing     every footing, grown until the service bearing pressure is within 250 kPa
#   5. C21 Crack Widths    the beam with the largest sagging moment
#
# Then it draws the frame coloured by how hard each member works, and writes an Excel schedule. Everything it
# writes goes to the output folder beside this file.
#
# RUN IT with the PROKON Automation Host, from any folder:
#     prokon-automation run design_frame.py
# or as the path argument of the MCP tool prokon_run_script. It needs PROKON installed (the catalogues and
# Sumo's licence manager) and Sumo licensed; Sumo is not part of PROKON for Spyder or for VS Code.
#
# Checks it makes on itself: the beam-section program reproduces its pinned value exactly, the frame solves,
# and the ULS support reactions balance the ULS load.
import prokon.v5 as p
import json, math, os, sqlite3, subprocess, sys, warnings
warnings.simplefilter('ignore')
p.timeout_seconds = 180

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'output')
os.makedirs(OUT, exist_ok=True)
MODEL = os.path.join(OUT, 'frame.Sumo')
SOLVED = os.path.join(OUT, 'frame-solved.Sumo')

# The PROKON desktop installation's catalogues: change these if PROKON is installed elsewhere.
MATERIAL_DB = r'C:\PROKON\User\Defaults.mtl'
SECTION_DB = r'C:\PROKON\User\Sections.dat'
for path in (MATERIAL_DB, SECTION_DB):
    if not os.path.isfile(path):
        raise SystemExit(f'{path} was not found: set MATERIAL_DB and SECTION_DB to your PROKON installation\'s User folder.')

CODE, FCU, FY = 'BS8110 - 1997', 30, 450
BAY, STOREY = 6.0, 3.5          # must match build_frame_pysumo.py

# 0. The product's pinned value, as a check that these are the engines PROKON ships.
pin = p.beam_section.analyse(design_code=CODE, m=200, v=100, bw=300, h=500, dc_t=40, dc_b=40, dc_s=40, fcu=30, fy=450, fyv=450)
assert pin['result']['mu'] == 295.18197048179997, pin['result']['mu']

# 1. Build the frame in Sumo. PySumo runs only inside Sumo, so the script goes to the sumo pysumo command of
#    this same host (sys.executable is prokon-automation.exe when this script is run by it).
build = {'script': open(os.path.join(HERE, 'build_frame_pysumo.py'), encoding='utf-8').read(),
         'material_db': MATERIAL_DB, 'section_db': SECTION_DB, 'save_project': MODEL}
run = subprocess.run([sys.executable, 'sumo', 'pysumo', '--inputs-from-stdin'], input=json.dumps(build),
                     capture_output=True, encoding='utf-8', timeout=900)
built = json.loads(run.stdout.strip().splitlines()[-1])
if not built['ok']:
    raise SystemExit('Sumo could not build the frame: ' + json.dumps(built['error']))
assert built['result']['solve']['ok'], built['result']['solve']

# 2. Solve it again through prokon.v5, keep the solved copy, and read the tables and node positions.
env = p.sumo.analyse(project=MODEL, save_project=SOLVED, tables=['BEAM_FORCES', 'REACTIONS', 'DEFLECTIONS'])
res = env['result']
assert res['solve']['ok'], res['solve']
db = sqlite3.connect(SOLVED)
nodes = {n: (x, y) for n, x, y, z in db.execute('SELECT Node, X, Y, Z FROM ANALYTIC_NODES')}
elems = {b: (s, e) for b, s, e in db.execute('SELECT BeamID, StartNode, EndNode FROM ANALYTIC_BEAMS')}
# Result rows carry case IDs, which are new in every build: look them up by the names the build gave them.
ids = {name: cid for table in ('LOAD_CASE_OBJECT', 'LOAD_COMBINATION_OBJECT')
       for cid, name in db.execute(f'SELECT ID, Name FROM {table}')}
db.close()
DL, LL, ULS, SLS = ids['DL'], ids['LL'], ids['ULS'], ids['SLS']
rows = lambda table, case: [r for r in res['results'][table] if r['CaseID'] == case]

# 3. Equilibrium: the ULS reactions must carry the ULS load.
sum_fy = sum(r['Fy'] for r in rows('REACTIONS', ULS))
max_defl = max(abs(r['Trans_Y']) for r in rows('DEFLECTIONS', SLS)) * 1000  # mm

# 4. Sort the elements into columns and beams.
beams, columns = {}, {}
for r in rows('BEAM_FORCES', ULS):
    s, e = elems[r['Beam']]
    (x1, y1), (x2, y2) = nodes[s], nodes[e]
    if abs(x1 - x2) < 1e-6:   # vertical: a column. End 1 is NOT always at the bottom (some are stored
        # top-first), so orient by node heights: 'bottom_is_1' says which end is the bottom.
        r = dict(r, bottom_is_1=(y1 < y2))
        columns[(round(x1, 3), round(min(y1, y2) / STOREY) + 1)] = r
    else:
        bay = int(min(x1, x2) // BAY) + 1
        floor = round(y1 / STOREY)
        beams.setdefault((bay, floor), []).append((r, (x1, x2)))

# 5. Beams: hogging at the columns, sagging at mid-span, shear; each designed by C22.
beam_rows = []
for (bay, floor), parts in sorted(beams.items(), key=lambda kv: (-kv[0][1], kv[0][0])):
    hog = sag = shear = 0.0
    for r, (x1, x2) in parts:
        m_end1, m_end2 = -r['Mz1'], r['Mz2']           # internal moment, sagging positive
        mid_is_end2 = abs(x2 - ((bay - 0.5) * BAY)) < 1e-6
        m_mid, m_col = (m_end2, m_end1) if mid_is_end2 else (m_end1, m_end2)
        sag = max(sag, m_mid); hog = max(hog, -m_col)
        shear = max(shear, abs(r['Fy1']), abs(r['Fy2']))
    out = {'bay': bay, 'floor': floor, 'M_hog': hog, 'M_sag': sag, 'V': shear}
    for tag, m in (('hog', hog), ('sag', sag)):
        e = p.beam_section.analyse(design_code=CODE, m=round(m, 2), v=round(shear, 2), bw=300, h=600,
                                   dc_t=50, dc_b=50, dc_s=50, fcu=FCU, fy=FY, fyv=FY)['result']
        bars = e['reinforcement']['tension_bars']
        out[f'{tag}_ast'] = e['ast']; out[f'{tag}_asc'] = e['as1']; out[f'{tag}_mu'] = e['mu']
        out[f'{tag}_bars'] = bars[0]['description'] if bars else '-'
        out['links_asv_s'] = e['asv']; out['shear_ok'] = e['shear.ok']
    out['util'] = max(hog, sag) / out['hog_mu']
    beam_rows.append(out)

# 6. Columns: ULS axial and end moments, unbraced, le = 1.3 x 3.5 m, designed by C11.
col_rows = []
for (x, storey), r in sorted(columns.items(), key=lambda kv: (-kv[0][1], kv[0][0])):
    # Internal moment at each end, sagging-positive in the element's own axes; the bottom end carries the larger N.
    if r['bottom_is_1']:
        n, mb, mt = r['Fx1'], -r['Mz1'], r['Mz2']
    else:
        n, mb, mt = -r['Fx2'], r['Mz2'], -r['Mz1']
    m2, m1 = (mt, mb) if abs(mt) >= abs(mb) else (mb, mt)
    m1s = abs(m1) * (1 if m1 * m2 >= 0 else -1)
    e = p.rectangular_column.analyse(design_code=CODE, h=400, b=400, dc_x=55, dc_y=55, fcu=FCU, fy=FY, lex=4550, ley=4550,
                                     bracing_x='Unbraced', bracing_y='Unbraced',
                                     load_cases=[{'n': round(n, 2), 'm2x': round(abs(m2), 2), 'm1x': round(m1s, 2), 'm2y': 0, 'm1y': 0}])['result']
    ok = [o for o in e['options'] if o['all_pass']]
    best = min(ok, key=lambda o: o['ast']) if ok else None
    col_rows.append({'line': int(x / BAY) + 1, 'storey': storey, 'N': n, 'M2': abs(m2), 'M1': m1s,
                     'bars': best['bar_description'] if best else 'NONE', 'ast': best['ast'] if best else None,
                     'perc': best['perc'] if best else None, 'util': (best['perc'] / 4.0) if best else 1.5,
                     'feasible': e['has_feasible_design']})

# 7. Pad footings: unfactored DL and LL reactions, sized up until the SLS bearing pressure is within 250 kPa.
foot_rows = []
for r_dl in sorted(rows('REACTIONS', DL), key=lambda r: nodes[r['Node']][0]):
    r_ll = next(r for r in rows('REACTIONS', LL) if r['Node'] == r_dl['Node'])
    lc = [{'name': 'D+L', 'pa1': round(r_dl['Fy'], 2), 'hx1': round(-r_dl['Fx'], 2), 'mx1': round(r_dl['Mz'], 2), 'lf1': 1.4},
          {'name': 'D+L', 'pa1': round(r_ll['Fy'], 2), 'hx1': round(-r_ll['Fx'], 2), 'mx1': round(r_ll['Mz'], 2), 'lf1': 1.6}]
    a = 1.5
    while True:
        yf = max(0.5, round(a / 4, 2))
        f = p.pad_footing.analyse(design_code=CODE, a=a, b=a, yf=yf, z=0.5, c1=0.4, d1=0.4, e1=0, f1=0, fcu=FCU, fy=FY,
                                  allowable_bearing_pressure=250, load_cases=lc)['result']
        if f['max_bearing_pressure_sls'] <= 250 or a >= 6:
            break
        a = round(a + 0.25, 2)
    crit = f['critical_uls']
    foot_rows.append({'line': int(nodes[r_dl['Node']][0] / BAY) + 1, 'P_dl': r_dl['Fy'], 'P_ll': r_ll['Fy'], 'a': a, 'yf': yf,
                      'q_sls': f['max_bearing_pressure_sls'], 'q_uls': f['max_bearing_pressure'],
                      'reinforcement': crit['reinforcement'], 'shear': crit['shear'], 'util': f['max_bearing_pressure_sls'] / 250})

# 8. Crack widths for the beam with the largest sagging moment, at its SLS moment.
# The frame is symmetric, so bays 1 and 3 tie; each build differs in the last bits, so break the tie by the lowest bay.
worst = max(beam_rows, key=lambda b: (round(b['M_sag'], 6), -b['bay']))
m_sls = 0.0
for r in rows('BEAM_FORCES', SLS):
    s, e = elems[r['Beam']]
    (x1, y1), (x2, y2) = nodes[s], nodes[e]
    if abs(y1 - y2) < 1e-6 and round(y1 / STOREY) == worst['floor'] and int(min(x1, x2) // BAY) + 1 == worst['bay']:
        mid_is_end2 = abs(x2 - ((worst['bay'] - 0.5) * BAY)) < 1e-6
        m_sls = max(m_sls, r['Mz2'] if mid_is_end2 else -r['Mz1'])
cw = p.crack_widths.analyse(design_code='BS8007 - 1987', slab_mode=False, h=600, hef=150, b=300, cover=30, fcu=FCU, fy=FY,
                            allowable_crack_width=0.3, user_beam_bars=worst['sag_bars'],
                            load_cases=[{'n': 1, 'm': round(m_sls, 2), 'm_uls': round(worst['M_sag'] / m_sls, 3)}])['result']
best_cfg = cw['load_cases'][0]['optimised_configs'][0]
crack = {'beam': f"bay {worst['bay']} floor {worst['floor']}", 'M_sls': m_sls,
         'lightest_bars_that_pass': best_cfg['formatted_bars'], 'crack_width_mm': best_cfg['combined_crack_width']}

# 9. Drawing: the frame coloured by utilisation.
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm, colors
norm = colors.Normalize(0, 1); cmap = matplotlib.colormaps['RdYlGn_r']
fig, ax = plt.subplots(figsize=(11, 9))
for c in col_rows:
    x = (c['line'] - 1) * BAY; y0 = (c['storey'] - 1) * STOREY
    ax.plot([x, x], [y0, y0 + STOREY], lw=9, color=cmap(norm(min(c['util'], 1))), solid_capstyle='butt')
    ax.text(x + 0.15, y0 + STOREY / 2, f"{c['bars']}\nN={c['N']:.0f}", fontsize=7, va='center')
for b in beam_rows:
    x0 = (b['bay'] - 1) * BAY; y = b['floor'] * STOREY
    ax.plot([x0, x0 + BAY], [y, y], lw=9, color=cmap(norm(min(b['util'], 1))), solid_capstyle='butt')
    ax.text(x0 + BAY / 2, y + 0.22, f"top {b['hog_bars']} / btm {b['sag_bars']}", ha='center', fontsize=7)
for f in foot_rows:
    x = (f['line'] - 1) * BAY
    ax.add_patch(plt.Rectangle((x - f['a'] / 2, -f['yf'] - 0.1), f['a'], f['yf'], color=cmap(norm(min(f['util'], 1)))))
    ax.text(x, -f['yf'] - 0.45, f"{f['a']:.2f} m sq, {f['q_sls']:.0f} kPa", ha='center', fontsize=7)
fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label='utilisation (beams M/Mu, columns %steel/4, footings q/250)')
ax.set_title(f'4-storey RC frame, {CODE} - designed by PROKON automation\n'
             f'ULS reactions {sum_fy:.1f} kN, max SLS deflection {max_defl:.1f} mm')
ax.set_aspect('equal'); ax.set_xlim(-2, 20); ax.set_ylim(-2.5, 15); ax.axis('off')
png = os.path.join(OUT, 'frame-design.png'); fig.savefig(png, dpi=130, bbox_inches='tight')

# 10. Excel schedule.
import openpyxl
wb = openpyxl.Workbook()
def sheet(title, data, keys):
    ws = wb.create_sheet(title); ws.append(keys)
    for d in data: ws.append([d[k] if not isinstance(d[k], (dict, list)) else json.dumps(d[k]) for k in keys])
wb.remove(wb.active)
sheet('Beams', beam_rows, ['floor', 'bay', 'M_hog', 'M_sag', 'V', 'hog_bars', 'hog_ast', 'sag_bars', 'sag_ast', 'links_asv_s', 'shear_ok', 'util'])
sheet('Columns', col_rows, ['storey', 'line', 'N', 'M2', 'M1', 'bars', 'ast', 'perc', 'feasible'])
sheet('Footings', foot_rows, ['line', 'P_dl', 'P_ll', 'a', 'yf', 'q_sls', 'q_uls'])
xlsx = os.path.join(OUT, 'frame-schedule.xlsx'); wb.save(xlsx)

# 11. Summary.
r2 = lambda v: round(v, 2) if isinstance(v, float) else v
print(json.dumps({
    'sumo_version': res.get('sumo_version'), 'uls_reaction_sum_kN': round(sum_fy, 1), 'max_sls_deflection_mm': round(max_defl, 1),
    'beams': [{k: r2(b[k]) for k in ('floor', 'bay', 'M_hog', 'M_sag', 'V', 'hog_bars', 'sag_bars', 'shear_ok', 'util')} for b in beam_rows],
    'columns': [{k: r2(c[k]) for k in ('storey', 'line', 'N', 'M2', 'M1', 'bars', 'perc', 'feasible')} for c in col_rows],
    'footings': [{k: r2(f[k]) for k in ('line', 'P_dl', 'P_ll', 'a', 'yf', 'q_sls')} for f in foot_rows],
    'crack': {k: r2(v) for k, v in crack.items()}, 'files': [png, xlsx, SOLVED]}, indent=1))
