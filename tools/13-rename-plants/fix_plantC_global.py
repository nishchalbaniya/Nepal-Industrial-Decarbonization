"""Day 14 -- last global pass for any remaining plantc (uppercase) refs."""
from pathlib import Path
import os

REPO = Path(r"C:\Users\TG\.minimax\workspace\nepal-decarb-build\repo")
TEXT_EXT = {".py", ".md", ".txt", ".html", ".json", ".yaml", ".yml", ".toml",
            ".sh", ".ps1", ".bat", ".cmd", ".csv", ".tsv", ".svg", ".ino",
            ".gitignore", ".gitattributes", ".dockerignore", ".editorconfig",
            ".css", ".js", ".ts", ".tsx", ".jsx", ".cfg", ".ini", ".env",
            ".step", ".stp", ".rst", ".tex", ".xml"}
SKIP = {".git", "__pycache__", "node_modules", ".venv", ".venv_live", "dist"}

# Only plantc (uppercase) -> plantc (lowercase)
# PlantD wasn't affected because the dict key was "plantd" with lowercase
PAIRS = [
    ("plantc",  "plantc"),  # but this is too broad -- will catch "plantc" anywhere
]

# But we also need to preserve "plantc-class 5000 tpd" if I made it lowercase before
# (I did). So this is safe.

n_files = 0
n_subs = 0
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
                n_subs += count
        if text != orig:
            p.write_text(text, encoding="utf-8")
            n_files += 1

print(f"modified {n_files} files, {n_subs} substitutions")
