"""Task 1 — ตรวจว่า ngspice จริงรัน .op ได้จาก Starter ที่สร้างขึ้นเอง."""

import os
import unittest

NGSPICE = (
    r"C:\Users\B6829681\AppData\Local\Temp\opencode"
    r"\ngspice-47\Spice64\bin\ngspice_con.exe"
)


class TestNgspiceSmoke(unittest.TestCase):
    def test_op_runs_real_ngspice(self):
        os.environ["NGSPICE_EXE"] = NGSPICE

        from spice_engine import find_ngspice, load_starter, run

        self.assertIsNotNone(find_ngspice())
        starter = load_starter()
        result = run(
            "dc",
            {
                "vcc": 12.0,
                "r1": 100e3,
                "r2": 22e3,
                "rc": 2.2e3,
                "re": 1e3,
            },
            starter,
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("vb", result["scalars"])
        self.assertGreater(result["scalars"]["ic"], 0)
        self.assertIn("47", result["ngspice_version"])
