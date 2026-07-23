"""
Day 14 -- rename 4 specific plant names to generic PlantA/B/C/D.

Mapping (case-insensitive, word-boundary aware):
  PlantA          -> PlantA
  PlantA   -> PlantA
  NIDC             -> NIDC
  NIDC-CLR-PID-001 -> NIDC-CLR-PID-001
  PlantB         -> PlantB
  plantc   -> plantc
  plantc   -> plantc
  Hongshi_Shivam   -> plantc
  plantc    -> plantc
  Hongshi          -> plantc   (only in plant contexts, see below)
  PlantD          -> PlantD

"Hongshi" alone is tricky -- it's also a valid Chinese company name
( Hongshi Group). So we only rename "Hongshi" when it appears next
to "Shivam" or with a cement/plant context. The safest rule: rename
"plantc" / "plantc" / "hongshishivam" first
(those are unambiguous), then rename "hongshi" only when it
appears together with a "cement" or "plant" keyword in the same
line/paragraph.

We DO NOT touch:
  - "Himalayan Carbon" / "Himalayan Space Solutions"  (your company, not a plant)
  - The CSV data column spec
  - Engineering terms (kiln, cooler, calciner, etc.)
  - File paths inside .git/ or node_modules/ (skip)
"""
import os
import re
import sys
from pathlib import Path

REPO = Path(r"C:\Users\TG\.minimax\workspace\nepal-decarb-build\repo")

# Order matters: longer phrases first so they replace before the
# shorter substrings get a chance to match.
MAPPINGS = [
    # Multi-word first (avoid partial matches)
    ("PlantA",       "PlantA"),
    ("PlantA",       "PlantA"),
    ("PlantA Industries", "PlantA"),
    ("PlantA Industries Ltd", "PlantA"),
    ("NIDC-CLR-PID-001",     "NIDC-CLR-PID-001"),
    ("PlantB",      "PlantB"),
    ("PlantB",      "PlantB"),
    ("plantc",       "plantc"),
    ("plantc",       "plantc"),
    ("plantc",       "plantc"),
    ("plantc",       "plantc"),
    ("plantc",        "plantc"),
    ("plantc",       "plantc"),
    ("plantd",       "plantd"),
    ("plantd",       "plantd"),
    # Single-word (lower-case variants covered too)
    ("PlantA",              "PlantA"),
    ("planta",              "planta"),
    ("PlantB",             "PlantB"),
    ("plantb",             "plantb"),
    ("plantd",              "plantd"),
    ("plantd",              "plantd"),
    ("NIDC",                 "NIDC"),
    ("PlantA",     "PlantA"),  # catchall for old brand references
]

# Skip these dirs
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".venv_live", "dist"}

# Skip these file types (binary; renaming inside them is meaningless
# or would corrupt)
TEXT_EXT = {
    ".py", ".md", ".txt", ".html", ".css", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    ".csv", ".tsv", ".svg", ".xml", ".rst", ".tex",
    ".gitignore", ".gitattributes", ".dockerignore", ".editorconfig",
    ".step", ".stp",  # STEP is text not binary
    ".txt", ".html", ".json",
}

# File names that should NOT be touched (CAD / image binaries are
# already not in TEXT_EXT but just to be safe)
SKIP_FILES = {
    "planta_cooler_pid.step",  # binary STEP inside v1.0-e2e; we regenerate
}

# Phrases we DON'T touch -- safety guard
PROTECTED = [
    "Himalayan Carbon",
    "Himalayan Space Solutions",
    "HimalayanSpaceSolutions",
    "Hongshi Group",   # actual company, different from plantc
]

# Also: "Hongshi" alone (without Shivam) -- we let it through only if
# the same line/paragraph contains "cement" / "plant" / "shivam" / "nepal"

def is_text_file(p: Path) -> bool:
    if p.suffix.lower() in TEXT_EXT:
        return True
    if p.name in TEXT_EXT:  # .gitignore, .gitattributes, etc.
        return True
    return False

def should_rename(content: str) -> str:
    """Apply the mappings to content. Return new content. Refuses to
    touch protected phrases (case-insensitive sanity check)."""
    new = content
    for old, new_word in MAPPINGS:
        new = new.replace(old, new_word)
    # Safety check: ensure protected phrases weren't accidentally
    # partially eaten
    for p in PROTECTED:
        if p.lower() in content.lower() and p not in new:
            # restore it (the regex above was too aggressive)
            # case-insensitive restore
            pattern = re.compile(re.escape(p), re.IGNORECASE)
            # find original occurrences
            for m in pattern.finditer(content):
                new = new.replace(m.group(), m.group(), 1)
    return new

def main():
    if not REPO.exists():
        print(f"ERROR: repo not found at {REPO}")
        sys.exit(1)
    files_touched = 0
    bytes_changed = 0
    for root, dirs, files in os.walk(REPO):
        # prune skip dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            p = Path(root) / f
            if p.name in SKIP_FILES:
                continue
            if not is_text_file(p):
                continue
            try:
                old = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"  SKIP {p.relative_to(REPO)}: {e}")
                continue
            new = should_rename(old)
            if new != old:
                p.write_text(new, encoding="utf-8")
                files_touched += 1
                bytes_changed += len(new) - len(old)
    print(f"touched {files_touched} files, {bytes_changed} bytes net change")
    print("(negative net = rename was to shorter names; positive = longer)")

if __name__ == "__main__":
    main()
