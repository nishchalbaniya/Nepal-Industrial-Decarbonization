"""
Day 10 -- server smoke tests. Exercise the FastAPI app via
TestClient (httpx-backed, no live server required).
"""
import json
import os
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PRO_SRC = _HERE.parent / "src"
_REPO_ROOT = _PRO_SRC.parent.parent
# Put pro/src/ FIRST so it shadows the pre-existing pro/nepal_decarb_pro/
# (which is a different package, for the previous toolset).
for p in (str(_PRO_SRC),
          str(_REPO_ROOT / "tools" / "02-kiln-dynamics-simulator" / "src"),
          str(_REPO_ROOT / "tools" / "03-cooler-grate-simulator" / "src")):
    sys.path.insert(0, p)
# Drop any pre-loaded nepal_decarb_pro so the new one (pro/src/...) wins
for mod_name in list(sys.modules):
    if mod_name == "nepal_decarb_pro" or mod_name.startswith("nepal_decarb_pro."):
        del sys.modules[mod_name]

from fastapi.testclient import TestClient
from nepal_decarb_pro.server import app


class ServerSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_version(self):
        r = self.client.get("/api/version")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body.get("nepal_decarb_pro"), "0.7.0")
        self.assertIn("nepal_cooler_sim", body)
        self.assertIn("nepal_kiln_sim", body)

    def test_status(self):
        r = self.client.get("/api/status")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("python", body)
        self.assertIn("numpy", body)
        self.assertIn("scipy", body)
        self.assertIn("pydantic", body)
        self.assertIn("fastapi", body)

    def test_plants(self):
        r = self.client.get("/api/plants")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("cooler", body)
        self.assertIn("kiln", body)
        self.assertIn("hetauda", body["cooler"])

    def test_cooler_run(self):
        r = self.client.post("/api/cooler/run", json={"plant": "hetauda"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        out = body["outputs"]
        # expected v0.3.2 default-preset numbers (Hetauda)
        self.assertAlmostEqual(out["secondary_air_outlet_c"], 559.3, delta=2.0)
        self.assertAlmostEqual(out["first_law_imbalance"], 0.0, delta=1e-9)
        self.assertGreater(out["cooler_efficiency"], 0.5)

    def test_kiln_run(self):
        r = self.client.post("/api/kiln/run", json={"plant": "hetauda"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        out = body["outputs"]
        # burning zone ~1450 C is the cement-clinker formation temperature
        self.assertGreater(out["t_burning_zone_c"], 1300.0)

    def test_cooler_run_bad_plant(self):
        r = self.client.post("/api/cooler/run", json={"plant": "no-such-plant"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("unknown plant", r.json()["detail"])

    def test_index_page(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.text
        self.assertIn("nepal-decarb", body)
        self.assertIn("dashboard", body.lower())

    def test_calibrate_synthetic(self):
        r = self.client.post("/api/cooler/calibrate",
                             json={"target": "synthetic", "out": "pro/demo-output"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        # Day 5 v0.5.0: loss 233 -> 5; n_bands_pass in {3, 4, 5, 6}
        self.assertGreater(body["n_bands_pass"], 0)
        self.assertLess(body["loss_posterior"], 50.0)


if __name__ == "__main__":
    unittest.main()
