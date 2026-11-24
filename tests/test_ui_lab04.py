"""Task 6 — UI แยก Analytical/SPICE ชัดเจน และกราฟต้องวาดจากผล ngspice จริง."""

import os
import unittest

from app import create_app

NGSPICE = (
    r"C:\Users\B6829681\AppData\Local\Temp\opencode"
    r"\ngspice-47\Spice64\bin\ngspice_con.exe"
)

SIM = {
    "analysis": "spice", "spice_mode": "dc",
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
    "rl": "10", "cin": "10", "cout": "10",
    "amplitude": "0.01", "frequency": "1000",
}


class TestUiLab04(unittest.TestCase):
    def setUp(self):
        os.environ["NGSPICE_EXE"] = NGSPICE
        self.client = create_app().test_client()

    def test_spice_page_labels_sources_and_units(self):
        html = self.client.get("/?analysis=spice").get_data(as_text=True)
        for token in ('name="analysis"', "ngspice", "dc_bias.py", "Hz", "dB"):
            with self.subTest(token=token):
                self.assertIn(token, html)
        self.assertNotIn('action="/calculate"', html)

    def test_analytical_page_keeps_lab03_form(self):
        html = self.client.get("/?analysis=analytical").get_data(as_text=True)
        self.assertIn("Analytical: dc_bias.py", html)
        self.assertIn('action="/calculate"', html)
        self.assertNotIn('action="/simulate"', html)

    def test_ac_result_draws_gain_and_phase_svg(self):
        html = self.client.post(
            "/simulate", data=dict(SIM, spice_mode="ac")
        ).get_data(as_text=True)
        self.assertIn("<svg", html)
        self.assertIn("<polyline", html)
        self.assertIn("Frequency (Hz)", html)
        self.assertIn("Gain (dB)", html)
        self.assertIn("Phase (°)", html)
        self.assertGreaterEqual(html.count("<svg"), 2)

    def test_tran_result_draws_two_waveforms_with_axis_labels(self):
        html = self.client.post(
            "/simulate", data=dict(SIM, spice_mode="tran")
        ).get_data(as_text=True)
        self.assertGreaterEqual(html.count("<polyline"), 2)
        for token in ("Time (s)", "Vin (V)", "Vout (V)", "Success"):
            with self.subTest(token=token):
                self.assertIn(token, html)


if __name__ == "__main__":
    unittest.main()
