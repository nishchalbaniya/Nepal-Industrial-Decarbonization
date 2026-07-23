"""Day 14 -- global replace of remaining old-name references."""
from pathlib import Path

REPO = Path(r"C:\Users\TG\.minimax\workspace\nepal-decarb-build\repo")

# All remaining (old, new) pairs
PAIRS = [
    # Function names
    ("planta()",          "planta()"),
    ("plantb()",         "plantb()"),
    ("plantc()",   "plantc()"),
    ("plantc()",   "plantc()"),
    ("plantd()",          "plantd()"),
    # Constant / preset names (uppercase variant)
    ("PLANT_A_PRESET",     "PLANT_A_PRESET"),
    ("PLANT_B_PRESET",    "PLANT_B_PRESET"),
    ("PLANT_C_PRESET", "PLANT_C_PRESET"),
    ("PLANT_D_PRESET",     "PLANT_D_PRESET"),
    # Variable-name variants
    ("PlantA_preset",     "PlantA_preset"),
    # Identifier in f-strings
    ("PlantA ",           "PlantA "),  # trailing space to avoid Hongshi
    ("PlantA_",           "PlantA_"),
    ("PlantA)",           "PlantA)"),
    ("PlantA.",           "PlantA."),
    ("PlantA,",           "PlantA,"),
    ("PlantA:",           "PlantA:"),
    ("PlantA/",           "PlantA/"),
    ("Hetauda\"",           "PlantA\""),
    # plantc (uppercase) -> plantc
    ("def plantc",         "def plantc"),
    ("\"plantc\"",         "\"plantc\""),
    ("'plantc'",           "'plantc'"),
    ("\"PlantD\"",         "\"plantd\""),
    ("'plantd'",           "'plantd'"),
    # "_PRESET" + plantc
    ("plantc_preset",      "plantc_preset"),
    ("plantd_preset",      "plantd_preset"),
]

# Files to scan (text only)
TEXT_EXT = {".py", ".md", ".txt", ".html", ".json", ".yaml", ".yml", ".toml",
            ".sh", ".ps1", ".bat", ".cmd", ".csv", ".tsv", ".svg", ".ino",
            ".gitignore", ".gitattributes", ".dockerignore", ".editorconfig",
            ".css", ".js", ".ts", ".tsx", ".jsx", ".cfg", ".ini", ".env",
            ".step", ".stp", ".rst", ".tex", ".xml"}

SKIP = {".git", "__pycache__", "node_modules", ".venv", ".venv_live", "dist"}

total_files = 0
total_subs = 0
for root, dirs, files in REPO.walk() if hasattr(REPO, "walk") else [(str(p), [], p.iterdir()) for p in [REPO]]:
    pass

import os
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        p = Path(root) / f
        if p.suffix.lower() not in TEXT_EXT and p.name not in TEXT_EXT:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        orig = text
        for old, new in PAIRS:
            if old in text:
                count = text.count(old)
                text = text.replace(old, new)
                total_subs += count
        if text != orig:
            p.write_text(text, encoding="utf-8")
            total_files += 1

print(f"modified {total_files} files, {total_subs} substitutions total")
