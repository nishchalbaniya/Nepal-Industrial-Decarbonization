"""
Day 12 demo -- save the verify report as JSON. We split this from
the FreeCAD run because FreeCAD writes to stderr/stdout only.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

FREECAD = r"C:\Users\TG\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe"
SCRIPT  = "C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/08_verify.py"
OUT     = "C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/json/08_verify_report.json"

proc = subprocess.run([FREECAD, SCRIPT], capture_output=True, text=True, timeout=120)
# FreeCAD prints to stderr; the JSON we want is in stdout
stdout = proc.stdout
# Find the { ... } block
start = stdout.find("{")
end = stdout.rfind("}")
if start < 0 or end < 0:
    print("no JSON found in output")
    print("stdout:", stdout[:500])
    print("stderr:", proc.stderr[:500])
    sys.exit(1)
data = json.loads(stdout[start:end+1])
Path(OUT).write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"wrote {OUT}")
print(json.dumps(data, indent=2))
