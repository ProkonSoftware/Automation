# verify_build.py - rebuilds the frame from build_frame_pysumo.py and checks it against a hand calculation.
#
# RUN IT with the PROKON Automation Host, from any folder:
#     prokon-automation run verify_build.py
# or as the path argument of the MCP tool prokon_run_script. It writes output/frame-rebuilt.Sumo beside this file.
#
# The check: 16 columns, 12 beams, the model solves, and the ULS support reactions equal the ULS load, worked
# out by hand from the inputs of build_frame_pysumo.py with concrete at 25 kN/m3 (the catalogue's '30 MPa'):
#   floor beams  3 floors x 18 m x (1.4 x 25 + 1.6 x 15) kN/m   = 3186.0 kN
#   roof beams            18 m x (1.4 x 18 + 1.6 x 6)  kN/m     =  626.4 kN
#   beam weight  72 m x 0.3 x 0.6 m x 25 kN/m3 x 1.4            =  453.6 kN
#   column weight 56 m x 0.4 x 0.4 m x 25 kN/m3 x 1.4           =  313.6 kN
#                                                        total  = 4579.6 kN
import prokon.v5
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'output')
os.makedirs(OUT, exist_ok=True)
EXPECTED_ULS_KN = 3 * 18 * (1.4 * 25 + 1.6 * 15) + 18 * (1.4 * 18 + 1.6 * 6) + (72 * 0.3 * 0.6 + 56 * 0.4 * 0.4) * 25 * 1.4

build = {'script': open(os.path.join(HERE, 'build_frame_pysumo.py'), encoding='utf-8').read(),
         'material_db': r'C:\PROKON\User\Defaults.mtl', 'section_db': r'C:\PROKON\User\Sections.dat',
         'save_project': os.path.join(OUT, 'frame-rebuilt.Sumo'), 'tables': '["REACTIONS"]'}
# sys.executable is prokon-automation.exe when this script is run by it.
run = subprocess.run([sys.executable, 'sumo', 'pysumo', '--inputs-from-stdin'], input=json.dumps(build),
                     capture_output=True, encoding='utf-8', timeout=900)
envelope = json.loads(run.stdout.strip().splitlines()[-1])
if not envelope['ok']:
    raise SystemExit('Sumo could not build the frame: ' + json.dumps(envelope['error']))
result = envelope['result']
built = result['script_result']
uls = next(case_id for case_id, name in built['cases'].items() if name == 'ULS')
total = sum(row['Fy'] for row in result['results']['REACTIONS'] if row['CaseID'] == uls)

checks = {'solves': result['solve']['ok'],
          '16 columns': built['column_count'] == 16,
          '12 beams': built['beam_count'] == 12,
          f'ULS reactions {total:.1f} kN = hand calculation {EXPECTED_ULS_KN:.1f} kN': abs(total - EXPECTED_ULS_KN) < 0.05}
for name, passed in checks.items():
    print(('PASS  ' if passed else 'FAIL  ') + name)
print('saved', result['saved_project'])
if not all(checks.values()):
    raise SystemExit('the rebuilt frame does not match')
