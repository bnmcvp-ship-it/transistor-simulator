"""Task 4 — AC Bode และ Transient ต้องเป็นข้อมูลจาก ngspice จริง."""

import os
import unittest

from spice_engine import load_starter, parse_series, run

NGSPICE = (
    r"C:\Users\B6829681\AppData\Local\Temp\opencode"
    r"\ngspice-47\Spice64\bin\ngspice_con.exe"
)
BASE = {"vcc": 12.0, "r1": 100e3, "r2": 22e3, "rc": 2.2e3, "re": 1e3}


class TestSpiceSeries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["NGSPICE_EXE"] = NGSPICE
        cls.starter = load_starter()

    def test_ac_series_has_gain_phase_and_units(self):
        result = run("ac", BASE, self.starter)
        series = result["series"]
        self.assertEqual(series["unit_x"], "Hz")
        self.assertEqual(series["unit_y"], "dB")
        self.assertGreater(len(series["x"]), 10)
        self.assertIn("phase", series["series"])
        self.assertEqual(len(series["series"]["phase"]), len(series["x"]))

    def test_ac_cutoff_labels_match_sweep(self):
        series = run("ac", BASE, self.starter)["series"]
        self.assertIsInstance(series["cutoff_low"], float)
        self.assertGreater(series["cutoff_low"], series["x"][0])
        self.assertEqual(series["cutoff_high"], "not determined in sweep range")
        self.assertEqual(series["cutoff"], series["cutoff_low"])

    def test_tran_series_has_vin_vout_and_time(self):
        result = run(
            "tran",
            {**BASE, "amplitude": 0.010, "frequency": 1000.0},
            self.starter,
        )
        series = result["series"]
        self.assertEqual(series["unit_x"], "s")
        self.assertEqual(series["unit_y"], "V")
        self.assertIn("vin", series["series"])
        self.assertIn("vout", series["series"])
        self.assertGreater(len(series["x"]), 10)

    def test_changing_amplitude_changes_output_waveform(self):
        low = run(
            "tran",
            {**BASE, "amplitude": 0.010, "frequency": 1000.0},
            self.starter,
        )["series"]
        high = run(
            "tran",
            {**BASE, "amplitude": 0.020, "frequency": 1000.0},
            self.starter,
        )["series"]
        self.assertGreater(
            max(abs(v) for v in high["series"]["vout"]),
            max(abs(v) for v in low["series"]["vout"]) * 1.5,
        )
