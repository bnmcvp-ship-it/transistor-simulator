"""Task 3 — netlist, .op run และ parser ผล DC จริง."""

import os
import unittest
from pathlib import Path

from spice_engine import build_netlist, load_starter, parse_op_log, run

NGSPICE = (
    r"C:\Users\B6829681\AppData\Local\Temp\opencode"
    r"\ngspice-47\Spice64\bin\ngspice_con.exe"
)
BASE = {"vcc": 12.0, "r1": 100e3, "r2": 22e3, "rc": 2.2e3}


class TestSpiceDc(unittest.TestCase):
    def test_parse_op_log_reads_real_values(self):
        sample = (Path(__file__).parent / "fixtures" / "op_sample.log").read_text(encoding="utf-8")
        result = parse_op_log(sample)
        self.assertAlmostEqual(result["vb"], 2.081437, places=6)
        self.assertAlmostEqual(result["ve"], 1.435581, places=6)
        self.assertAlmostEqual(result["vc"], 8.851787, places=6)
        self.assertAlmostEqual(result["vce"], 8.851787 - 1.435581, places=6)
        self.assertAlmostEqual(result["ic"], 0.00143101, places=9)
        self.assertAlmostEqual(result["ib"], 4.57487e-06, places=10)

    def test_build_netlist_contains_requested_re(self):
        text = build_netlist("dc", {**BASE, "re": 2e3}, load_starter())
        self.assertTrue(text.startswith("*"))
        self.assertIn(".op", text)
        self.assertIn("RE VE 0 2000", text)

    def test_changing_re_changes_ic(self):
        os.environ["NGSPICE_EXE"] = NGSPICE
        starter = load_starter()
        low = run("dc", {**BASE, "re": 1e3}, starter)
        high = run("dc", {**BASE, "re": 2e3}, starter)
        self.assertLess(high["scalars"]["ic"], low["scalars"]["ic"])
