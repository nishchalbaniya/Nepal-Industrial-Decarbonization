import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# WP6 fix: the test suite historically had two nepal_decarb_pro packages
# coexisting (pro/nepal_decarb_pro/ for the markets/standards package, and
# pro/src/nepal_decarb_pro/ for the FastAPI server). The Day 10 server
# test (test_server.py) and Day 11 setup test (test_setup.py) depend on
# the pro/src/ layout. Putting pro/src/ on sys.path here lets both
# coexist for testing; the install itself uses pro/nepal_decarb_pro/
# (per pyproject.toml where = ["."]).
_PRO_SRC = Path(__file__).parent.parent / "src"
if _PRO_SRC.exists():
    sys.path.insert(0, str(_PRO_SRC))

# WP6: optional-dependency skips. The sim.process_flows module requires
# matplotlib, and reporting.pdf requires reportlab. These are not core
# dependencies, so we skip tests that import them when the optional
# package is not installed.
import pytest


def pytest_collection_modifyitems(config, items):
    """Skip tests that require optional dependencies when those are missing."""
    skip_reasons = {}

    try:
        import matplotlib  # noqa: F401
        skip_reasons["matplotlib"] = False
    except ImportError:
        skip_reasons["matplotlib"] = pytest.mark.skip(
            reason="matplotlib not installed (optional dep for sim.process_flows)"
        )

    try:
        import reportlab  # noqa: F401
        skip_reasons["reportlab"] = False
    except ImportError:
        skip_reasons["reportlab"] = pytest.mark.skip(
            reason="reportlab not installed (optional dep for reporting.pdf)"
        )

    try:
        import folium  # noqa: F401
        skip_reasons["folium"] = False
    except ImportError:
        skip_reasons["folium"] = pytest.mark.skip(
            reason="folium not installed (optional dep for geo features)"
        )

    for item in items:
        # Inspect the source file path to decide which skip marker to apply
        path = str(item.fspath)
        if "sim" in path.lower() or "test_sim" in path.lower():
            if skip_reasons.get("matplotlib"):
                item.add_marker(skip_reasons["matplotlib"])
        if "report" in path.lower() or "test_report" in path.lower():
            if skip_reasons.get("reportlab"):
                item.add_marker(skip_reasons["reportlab"])

