"""Day 14 -- fix the remaining plantc references in plants.py."""
from pathlib import Path
p = Path(r"C:\Users\TG\.minimax\workspace\nepal-decarb-build\repo\tools\03-cooler-grate-simulator\src\nepal_cooler_sim\plants.py")
text = p.read_text(encoding="utf-8")
# Critical fix: PRESETS dict at line 282
text = text.replace('"plantc":  plantc,', '"plantc":  plantc,')
# Docstring consistency (optional but nice)
text = text.replace("plantc Cement (modern BAT reference)", "plantc cement (modern BAT reference)")
text = text.replace("\"plantc Cement Industries, Sarlahi / Nawalparasi, Nepal.\"",
                   "\"plantc cement industries, Sarlahi / Nawalparasi, Nepal.\"")
text = text.replace("\"plantc-class 5000 tpd\"", "\"plantc-class 5000 tpd\"")
# Line 12 (the docstring at the top of plants.py)
text = text.replace("- plantc     : 208 t/h (5000 tpd), ~250 m altitude (inner Terai).",
                   "- plantc     : 208 t/h (5000 tpd), ~250 m altitude (inner Terai).")
p.write_text(text, encoding="utf-8")
print("done")
