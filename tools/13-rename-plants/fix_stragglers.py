"""Day 14 -- fix the 3 stragglers the main rename missed."""
from pathlib import Path

REPO = Path(r"C:\Users\TG\.minimax\workspace\nepal-decarb-build\repo")

FIXES = {
    "pro/deploy/vps/mosquitto/acl": [
        ("user plant_hetauda", "user plant_a"),
        ("topic write nepal/hetauda/#", "topic write nepal/planta/#"),
    ],
    "pro/nepal_decarb_pro/firmware/esp32_sensor.ino": [
        ('PLANT_ID = "hetauda"', 'PLANT_ID = "planta"'),
    ],
    "tools/03-cooler-grate-simulator/day-03-PRs/data-scientist-uq/test_outputs.py": [
        ("PLANT_A_PRESET = dict(", "PLANT_A_PRESET = dict("),
        ("# UCIL is at ~300 m, similar duty", "# PlantB is at ~300 m, similar duty"),
        ("PLANT_B_PRESET = dict(PLANT_A_PRESET)", "PLANT_B_PRESET = dict(PLANT_A_PRESET)"),
        ("PLANT_C_PRESET = dict(", "PLANT_C_PRESET = dict("),
        ("    PLANT_A_PRESET,", "    PLANT_A_PRESET,"),
        ("PLANT_D_PRESET = dict(PLANT_A_PRESET)", "PLANT_D_PRESET = dict(PLANT_A_PRESET)"),
        ('("planta", PLANT_A_PRESET),', '("planta", PLANT_A_PRESET),'),
        ('("plantb", PLANT_B_PRESET),', '("plantb", PLANT_B_PRESET),'),
    ],
}

for rel, pairs in FIXES.items():
    p = REPO / rel
    text = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new)
            print(f"  fixed: {old[:60]!r}")
        else:
            print(f"  NOT FOUND: {old[:60]!r}")
    p.write_text(text, encoding="utf-8")

print("done")
