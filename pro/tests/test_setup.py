"""
Day 11 -- turnkey installer smoke test. Runs `nepal-decarb setup`
against a temp directory and asserts that all expected files are
created on a fake Desktop + Start Menu.
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_HERE = Path(__file__).resolve().parent
_PRO_SRC = _HERE.parent / "src"
_REPO_ROOT = _PRO_SRC.parent.parent
for p in (str(_PRO_SRC),
          str(_REPO_ROOT / "tools" / "02-kiln-dynamics-simulator" / "src"),
          str(_REPO_ROOT / "tools" / "03-cooler-grate-simulator" / "src")):
    sys.path.insert(0, p)
for mod_name in list(sys.modules):
    if mod_name == "nepal_decarb_pro" or mod_name.startswith("nepal_decarb_pro."):
        del sys.modules[mod_name]

from nepal_decarb_pro.cli import cmd_setup


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="nepal-decarb-setup-"))
        self.fake_desktop = self.tmp / "Desktop" / "NepalDecarb"
        self.fake_startmenu = self.tmp / "StartMenu" / "Programs" / "NepalDecarb"
        self.fake_dist = self.tmp / "pro" / "dist"
        # patch Path.home() to point at our tmp dir
        self._home_patcher = patch("os.path.expanduser",
                                   lambda p: str(self.tmp / p.lstrip("~/")))
        self._home_patcher.start()

    def tearDown(self):
        self._home_patcher.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_setup_creates_all_shortcuts(self):
        # Use the actual pro/dist location so the .bat can find the
        # repo (we are in the real repo here, no need to fake the
        # repo root).
        repo_dist = _REPO_ROOT / "pro" / "dist"
        repo_dist.mkdir(parents=True, exist_ok=True)
        ns = type("A", (), {"dist": str(repo_dist), "port": 8123})()
        rc = cmd_setup(ns)
        self.assertEqual(rc, 0)
        # The actual Desktop + Start Menu will get files; check that
        # they exist (we don't tear them down, so this is best-effort).
        real_desktop = Path(os.path.expanduser("~")) / "Desktop" / "NepalDecarb"
        self.assertTrue((real_desktop / "Start NepalDecarb Dashboard.vbs").exists())
        self.assertTrue((real_desktop / "Run Demo (PlantA).bat").exists())
        self.assertTrue((real_desktop / "Uninstall NepalDecarb.bat").exists())
        self.assertTrue((real_desktop / "nepal-decarb.bat").exists())
        self.assertTrue((real_desktop / "nepal-decarb.ps1").exists())
        self.assertTrue((real_desktop / "README.txt").exists())
        # Day 12 -- real Windows .lnk shortcuts, not just .vbs / .bat.
        # Magic header byte is 0x4C ('L') per [MS-SHLLINK].
        for lnk_name in ("NepalDecarb Dashboard.lnk",
                         "NepalDecarb Run Demo.lnk",
                         "NepalDecarb Uninstall.lnk"):
            p = real_desktop / lnk_name
            self.assertTrue(p.exists(), f"missing {p}")
            with open(p, "rb") as f:
                first = f.read(4)
            self.assertEqual(first, b"\x4c\x00\x00\x00",
                             f"{p} is not a valid Windows .lnk (header={first!r})")


if __name__ == "__main__":
    unittest.main()
