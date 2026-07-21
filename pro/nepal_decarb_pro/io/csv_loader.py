"""CSV I/O for plant data."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import csv
import json


def load_plant_data(path: Path) -> List[Dict]:
    """Load plant operating data from a CSV file."""
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_results(results: List[Dict], path: Path) -> None:
    """Save calculation results to a CSV file."""
    if not results:
        return
    keys = list(results[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)


def save_json(data: Dict, path: Path) -> None:
    """Save data as JSON."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
