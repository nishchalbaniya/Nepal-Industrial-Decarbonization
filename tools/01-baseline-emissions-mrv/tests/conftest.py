"""Pytest config: add src/ to path so tests can import nepal_mrv without install."""
import sys
from pathlib import Path

src = Path(__file__).parent.parent / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))
