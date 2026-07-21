"""
DEPLOYMENT VERIFICATION
=======================
After running deploy.sh, run this to confirm everything is live.
Usage:  python scripts/verify_deployment.py [API_URL]
"""
from __future__ import annotations

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
UI_URL = API_URL.replace(":8000", ":8501")


def check(name: str, url: str, expect: int = 200, timeout: int = 5) -> bool:
    """Hit URL and check status code."""
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        ok = r.status == expect
        status = "OK" if ok else f"FAIL (got {r.status})"
    except urllib.error.URLError as e:
        status = f"FAIL ({e})"
        ok = False
    except Exception as e:
        status = f"FAIL ({e})"
        ok = False
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name:30s}  {url:60s}  {status}")
    return ok


def check_json_field(url: str, field: str, timeout: int = 5) -> bool:
    """Fetch JSON and confirm field exists."""
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        data = json.loads(r.read().decode())
        ok = field in data
        status = f"OK ({field}={data.get(field)})" if ok else f"FAIL (no {field})"
    except Exception as e:
        status = f"FAIL ({e})"
        ok = False
    icon = "✅" if ok else "❌"
    print(f"  {icon} {url:60s}  {status}")
    return ok


def main() -> int:
    print(f"=== nepal_decarb_pro deployment verification @ {datetime.now().isoformat()} ===")
    print(f"API: {API_URL}")
    print(f"UI:  {UI_URL}\n")

    failures = 0

    print("[1] Health endpoints")
    failures += not check("API health",       f"{API_URL}/health")
    failures += not check("API docs",         f"{API_URL}/docs")
    failures += not check("Streamlit health", f"{UI_URL}/_stcore/health")
    failures += not check("Streamlit main",   f"{UI_URL}/")

    print("\n[2] API metadata")
    failures += not check_json_field(f"{API_URL}/", "name")
    failures += not check_json_field(f"{API_URL}/", "version")
    failures += not check_json_field(f"{API_URL}/", "endpoints")

    print("\n[3] LLM advisor")
    failures += not check("Advisor example",  f"{API_URL}/api/v1/advisor/example-questions?language=en")

    print("\n[4] Standards coverage")
    try:
        r = urllib.request.urlopen(f"{API_URL}/api/v1/standards", timeout=5)
        data = json.loads(r.read().decode())
        n = len(data.get("standards", []))
        ok = n >= 11
        status = f"OK ({n} standards)" if ok else f"FAIL ({n} < 11)"
        icon = "✅" if ok else "❌"
        print(f"  {icon} Standards count: {n}")
        if not ok:
            failures += 1
    except Exception as e:
        print(f"  ❌ Standards list failed: {e}")
        failures += 1

    print(f"\n=== {('PASS' if failures == 0 else 'FAIL')} ({failures} failures) ===")
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
