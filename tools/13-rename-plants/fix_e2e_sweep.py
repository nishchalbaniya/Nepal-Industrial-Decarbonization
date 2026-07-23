"""Day 14 -- fix the e2e 4-plant sweep script (staging + repo)."""
from pathlib import Path

PAIRS = [
    ('"hetauda"',       '"planta"'),
    ('"udayapur"',      '"plantb"'),
    ('"hongshi-shivam"', '"plantc"'),
    ('"ghorahi"',       '"plantd"'),
    ("nepal_cooler_sim.hetauda",        "nepal_cooler_sim.planta"),
    ("nepal_cooler_sim.udayapur",       "nepal_cooler_sim.plantb"),
    ("nepal_cooler_sim.hongshi_shivam", "nepal_cooler_sim.plantc"),
    ("nepal_cooler_sim.ghorahi",        "nepal_cooler_sim.plantd"),
    ('PLANTS = ["hetauda", "udayapur", "hongshi-shivam", "ghorahi"]',
     'PLANTS = ["planta", "plantb", "plantc", "plantd"]'),
]

# Files to fix
files = [
    Path(r"C:\Users\TG\.mavis\workspace\nepal-decarb-build\demo-e2e\04_4plant_sweep.py"),
    Path(r"C:\Users\TG\.minimax\workspace\nepal-decarb-build\repo\release\v1.0-e2e\04_4plant_sweep.py"),
    Path(r"C:\Users\TG\.mavis\workspace\nepal-decarb-build\demo-e2e\DEPLOY-AND-SELL.md"),
    Path(r"C:\Users\TG\.minimax\workspace\nepal-decarb-build\repo\release\v1.0-e2e\DEPLOY-AND-SELL.md"),
]

for p in files:
    if not p.exists():
        print(f"  MISSING: {p}")
        continue
    text = p.read_text(encoding="utf-8")
    for old, new in PAIRS:
        text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print(f"  fixed: {p.name}")
print("done")
