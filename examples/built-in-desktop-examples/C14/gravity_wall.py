# ---
# Example:  Built-in desktop example - Gravity wall
# Feature:  retaining_wall (C14 Retaining Wall)
# Verified: no - the engine refuses this file (its design code is stored as "BS0110 - 1997"), so no result can be compared with the desktop
# ---
# The desktop program's own Examples-menu case "Gravity wall", run from
# Python. No result of this example can be compared with the desktop, and
# this script shows why.
#
# The desktop's own example writes its design code as "BS0110 - 1997", a
# misspelling of "BS8110 - 1997" in the desktop's built-in example data. The
# desktop does not notice: it keeps the misspelt name as a label and silently
# designs to whatever code was selected before the file was opened, so its
# calcsheet prints "REINFORCEMENT TO BS0110 - 1997" over BS8110 steel. The
# engine behind this script refuses the file instead of guessing the code.
# Both are recorded in the C14 repo's desktop-parity.json (genuineExamples,
# "gravitywallexample-2026-09-09") with the desktop calcsheet export as
# evidence (DLL/VerificationExamples/desktop-parity-2026-09-09/
# GravityWallExample-W5.3.06.json, Wall.exe 5.3.6.0).
#
# The save file is kept exactly as the desktop wrote it; it is not "fixed".

import os
import prokon.v5

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "GravityWallExample-W5.3.06.C14")

print(f"Example     : Gravity wall  ({os.path.basename(SAVE_FILE)})\n")

matched = known = differed = 0
try:
    prokon.v5.retaining_wall.load_file(path=SAVE_FILE)
    verdict, differed = "DIFFERS: the file loaded, but it was expected to be refused", 1
except Exception as error:
    if getattr(error, "code", None) == "FILE_CONTENT_NOT_SUPPORTED":
        verdict, known = "known difference: design code BS0110 - 1997 is refused", 1
    else:
        verdict, differed = f"DIFFERS: unexpected failure {error}", 1
    print(f"load_file   : {error}\n")

print(f"Design code : {verdict}")
print("-" * 82)
print(f"{matched} of 1 results match the desktop; "
      f"{known} are known differences; {differed} unexpected.")
