"""Task 2 — ตรวจฟอร์ม SPICE ก่อนสร้าง netlist."""

import unittest

from spice_engine import SpiceError, parse_spice_form


class TestParseSpiceForm(unittest.TestCase):
    def test_rejects_invalid_values_with_field_name(self):
        cases = [
            ("", "RE"),
            (None, "RE"),
            ("12a", "RE"),
            ("nan", "RE"),
            ("inf", "RE"),
            ("-inf", "RE"),
            ("1e400", "RE"),
            ("0", "RE"),
            ("-1", "amplitude"),
            ("0", "frequency"),
        ]
        for value, label in cases:
            with self.subTest(value=value, label=label):
                with self.assertRaises(SpiceError) as ctx:
                    parse_spice_form(value, label)
                self.assertIn(label, str(ctx.exception))

    def test_accepts_positive_finite_value(self):
        self.assertEqual(parse_spice_form("1.5", "RE"), 1.5)
        self.assertEqual(parse_spice_form("1e-3", "amplitude"), 1e-3)
