"""Unit tests for dc_bias engineering module.

ค่าอ้างอิงอิสระ (คำนวณด้วยมือจากสมการใน docs/design-note.md):
  VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V
  VTH = 12×22/(100+22)          = 2.163934 V
  RTH = 100k×22k/(100k+22k)     = 18032.79 Ω
  IB  = (VTH−VBE)/(RTH+101×RE)  = 1.463934/119032.79 = 12.2986 µA
  IC  = 100×IB                  = 1.22986 mA
  IE  = 101×IB                  = 1.24216 mA
  VE  = IE×RE                   = 1.24216 V
  VB  = VE+VBE                  = 1.94216 V
  VC  = VCC−IC×RC               = 9.29431 V
  VCE = VC−VE                   = 8.05215 V
"""

import math
import unittest

from dc_bias import (
    BiasError, analyze, analyze_emitter, analyze_fixed, parse_field,
)


class TestReferenceCase(unittest.TestCase):
    """A3: ผลต้องตรงกับการคำนวณอิสระภายใต้แบบจำลองเดียวกัน"""

    def test_reference_case(self):
        result = analyze(
            vcc=12.0, r1=100.0, r2=22.0, rc=2.2, re=1.0,
            beta=100.0, vbe=0.70,
        )
        self.assertAlmostEqual(result["vb"], 1.942157, delta=0.001)
        self.assertAlmostEqual(result["ve"], 1.242157, delta=0.001)
        self.assertAlmostEqual(result["vc"], 9.294312, delta=0.001)
        self.assertAlmostEqual(result["vce"], 8.052155, delta=0.001)
        self.assertAlmostEqual(result["ic"] * 1e3, 1.229858, delta=0.001)  # mA
        self.assertAlmostEqual(result["ib"] * 1e6, 12.298581, delta=0.001)  # µA
        self.assertEqual(result["region"], "Forward-Active")
        self.assertEqual(result["warnings"], [])


class TestParseField(unittest.TestCase):
    """A4: ค่าว่าง/ไม่ใช่ตัวเลข → BiasError พร้อมชื่อฟิลด์"""

    def test_parse_field_rejects_empty(self):
        with self.assertRaises(BiasError) as ctx:
            parse_field("", "VCC")
        self.assertIn("VCC", str(ctx.exception))

    def test_parse_field_rejects_none(self):
        with self.assertRaises(BiasError):
            parse_field(None, "VCC")

    def test_parse_field_rejects_non_numeric(self):
        with self.assertRaises(BiasError) as ctx:
            parse_field("12a", "R1")
        self.assertIn("R1", str(ctx.exception))

    def test_parse_field_rejects_non_finite(self):
        for bad in ("nan", "inf", "-inf", "infinity", "1e400"):
            with self.assertRaises(BiasError, msg=bad):
                parse_field(bad, "VCC")


class TestAnalyzeValidation(unittest.TestCase):
    """A4: R≤0, β≤0, VCC≤0 → BiasError ก่อนคำนวณ"""

    def test_analyze_rejects_invalid_values(self):
        with self.assertRaises(BiasError):
            analyze(vcc=0, r1=100, r2=22, rc=2.2, re=1, beta=100, vbe=0.7)
        with self.assertRaises(BiasError):
            analyze(vcc=12, r1=100, r2=22, rc=2.2, re=1, beta=-5, vbe=0.7)
        with self.assertRaises(BiasError):
            analyze(vcc=12, r1=0, r2=22, rc=2.2, re=1, beta=100, vbe=0.7)
        with self.assertRaises(BiasError):
            analyze(vcc=12, r1=100, r2=22, rc=2.2, re=0, beta=100, vbe=0.7)

    def test_analyze_resistor_validation(self):
        # ค่าบวกเล็กมาก (0.001 kΩ = 1 Ω) ผ่านเกณฑ์ R>0
        result = analyze(
            vcc=12.0, r1=100.0, r2=22.0, rc=0.001, re=1.0,
            beta=100.0, vbe=0.70,
        )
        self.assertIn("region", result)
        # ค่า 0 และค่าติดลบไม่ผ่าน
        with self.assertRaises(BiasError):
            analyze(vcc=12, r1=100, r2=22, rc=0, re=1, beta=100, vbe=0.7)
        with self.assertRaises(BiasError):
            analyze(vcc=12, r1=100, r2=22, rc=2.2, re=-1, beta=100, vbe=0.7)


class TestWarningScenarios(unittest.TestCase):
    """A5: อยู่นอก Active Region → warning ไม่รายงานว่า approximation ใช้ได้"""

    def test_cutoff_case(self):
        # R2=1k เล็กมาก → VTH = 12×1/101 ≈ 0.119 V ≤ VBE 0.70 V
        result = analyze(
            vcc=12.0, r1=100.0, r2=1.0, rc=2.2, re=1.0,
            beta=100.0, vbe=0.70,
        )
        self.assertEqual(result["region"], "Cutoff")
        self.assertTrue(len(result["warnings"]) > 0)
        # ค่าทั้งหมดต้องเป็นเลขจำกัด (ไม่ NaN/inf)
        for key in ("vth", "rth", "ib", "ic", "ie", "vb", "ve", "vc", "vce"):
            self.assertTrue(math.isfinite(result[key]), f"{key} not finite")

    def test_saturation_case(self):
        # R1=R2=100k, RC=2.4k → IC×RC ตัดจน VCE ≈ 0.031 V < 0.2 V
        result = analyze(
            vcc=12.0, r1=100.0, r2=100.0, rc=2.4, re=1.0,
            beta=100.0, vbe=0.70,
        )
        self.assertEqual(result["region"], "Saturation")
        self.assertTrue(len(result["warnings"]) > 0)
        # ค่าทั้งหมดต้องเป็นเลขจำกัด (ไม่ NaN/inf)
        for key in ("vth", "rth", "ib", "ic", "ie", "vb", "ve", "vc", "vce"):
            self.assertTrue(math.isfinite(result[key]), f"{key} not finite")
        self.assertLess(result["vce"], 0.2)


class TestFixedBias(unittest.TestCase):
    """Lab 03 — Fixed Bias: ค่าอ้างอิงคำนวณมือ IB=(VCC−VBE)/RB"""

    def test_fixed_reference(self):
        # IB = 11.3/1M = 11.30 µA, IC = 1.130 mA
        # VC = 12 − 1.130m×2.2k = 9.514 V, VE = 0, VCE = 9.514 V
        result = analyze_fixed(vcc=12, rb=1000, rc=2.2, beta=100, vbe=0.7)
        self.assertAlmostEqual(result["ib"] * 1e6, 11.30, delta=0.001)  # µA
        self.assertAlmostEqual(result["ic"] * 1e3, 1.130, delta=0.001)  # mA
        self.assertAlmostEqual(result["vce"], 9.514, delta=0.001)       # V
        self.assertAlmostEqual(result["vb"], 0.7, delta=0.001)
        self.assertEqual(result["ve"], 0.0)
        self.assertEqual(result["region"], "Forward-Active")
        self.assertEqual(result["warnings"], [])

    def test_fixed_rejects_zero_rb(self):
        with self.assertRaises(BiasError) as ctx:
            analyze_fixed(vcc=12, rb=0, rc=2.2, beta=100, vbe=0.7)
        self.assertIn("RB ต้องมากกว่า 0", str(ctx.exception))

    def test_fixed_saturation_warning(self):
        # RB=100k → IB=113 µA, IC=11.3 mA → IC×RC=24.86 V > VCC → VCE<0.2
        result = analyze_fixed(vcc=12, rb=100, rc=2.2, beta=100, vbe=0.7)
        self.assertEqual(result["region"], "Saturation")
        self.assertTrue(len(result["warnings"]) > 0)
        for key in ("ib", "ic", "ie", "vb", "ve", "vc", "vce"):
            self.assertTrue(math.isfinite(result[key]), f"{key} not finite")
        self.assertLess(result["vce"], 0.2)


class TestEmitterBias(unittest.TestCase):
    """Lab 03 — Emitter Bias: IB=(VCC−VBE)/(RB+(β+1)RE)"""

    def test_emitter_reference(self):
        # IB = 11.3/(1M+101×1k) = 10.2634 µA, IC = 1.0263 mA
        # IE = 1.0366 mA, VE = 1.0366 V, VC = 9.7421 V, VCE = 8.7055 V
        result = analyze_emitter(
            vcc=12, rb=1000, rc=2.2, re=1, beta=100, vbe=0.7,
        )
        self.assertAlmostEqual(result["ic"] * 1e3, 1.0263, delta=0.001)  # mA
        self.assertAlmostEqual(result["vce"], 8.7055, delta=0.001)       # V
        self.assertAlmostEqual(result["ve"], 1.0366, delta=0.001)        # V
        self.assertEqual(result["region"], "Forward-Active")
        self.assertEqual(result["warnings"], [])

    def test_emitter_more_re_lower_ic(self):
        # RE=2k → IB = 11.3/(1M+202k) = 9.401 µA → IC = 0.9401 mA
        result = analyze_emitter(
            vcc=12, rb=1000, rc=2.2, re=2, beta=100, vbe=0.7,
        )
        self.assertAlmostEqual(result["ic"] * 1e3, 0.9401, delta=0.001)  # mA
        self.assertAlmostEqual(result["vce"], 8.0328, delta=0.001)       # V
        less_re = analyze_emitter(
            vcc=12, rb=1000, rc=2.2, re=1, beta=100, vbe=0.7,
        )
        self.assertLess(result["ic"], less_re["ic"])


if __name__ == "__main__":
    unittest.main()
