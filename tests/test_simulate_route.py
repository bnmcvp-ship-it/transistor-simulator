"""Task 5 — /simulate ต้องแยกจาก /calculate ของ Lab 03 และไม่โชว์ผลเก่าตอน error."""

import os
import unittest
from unittest.mock import patch

from app import create_app
from spice_engine import SpiceError

NGSPICE = (
    r"C:\Users\B6829681\AppData\Local\Temp\opencode"
    r"\ngspice-47\Spice64\bin\ngspice_con.exe"
)

VALID_SIM = {
    "analysis": "spice",
    "spice_mode": "dc",
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
    "rl": "10", "cin": "10", "cout": "10",
    "amplitude": "0.01", "frequency": "1000",
}

REFERENCE_INPUT = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.7",
}


class TestSimulateRoute(unittest.TestCase):
    def setUp(self):
        os.environ["NGSPICE_EXE"] = NGSPICE
        self.client = create_app().test_client()

    def test_get_spice_form_has_sim_fields_without_analytical_fields(self):
        html = self.client.get("/?analysis=spice").get_data(as_text=True)
        self.assertIn('name="amplitude"', html)
        self.assertIn('name="frequency"', html)
        self.assertIn('action="/simulate"', html)
        self.assertNotIn('name="beta"', html)

    def test_invalid_re_shows_error_without_success_or_plot(self):
        response = self.client.post("/simulate", data=dict(VALID_SIM, re="0"))
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("RE ต้องมากกว่า 0", html)
        self.assertIn('class="error"', html)
        self.assertNotIn("Success", html)
        self.assertNotIn("<svg", html)

    def test_engine_error_clears_stale_result(self):
        with patch("spice_engine.run", side_effect=SpiceError("ngspice timeout")):
            response = self.client.post("/simulate", data=VALID_SIM)
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ngspice timeout", html)
        self.assertNotIn("Success", html)
        self.assertNotIn("<svg", html)

    def test_real_ngspice_result_shows_provenance(self):
        html = self.client.post("/simulate", data=VALID_SIM).get_data(as_text=True)
        self.assertIn("ngspice-47", html)
        self.assertIn("QBC547B", html)
        self.assertIn("1.43", html)  # IC ≈ 1.431 mA จาก ngspice จริง
        self.assertNotIn('class="error"', html)

    def test_calculate_reference_still_works(self):
        html = self.client.post("/calculate", data=REFERENCE_INPUT).get_data(as_text=True)
        self.assertIn("8.05", html)
        self.assertIn("1.23", html)


if __name__ == "__main__":
    unittest.main()
