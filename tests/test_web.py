"""HTTP route tests ผ่าน Flask test client (เกณฑ์ A6: ≥1 test ผ่าน test client)."""

import unittest

from app import create_app

REFERENCE_INPUT = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.7",
}


class TestWebRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_get_index(self):
        """A1: GET / ต้อง 200 และมีฟอร์มครบทั้ง 7 ช่อง"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Calculate DC Bias", html)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', html)

    def test_post_calculate_reference(self):
        """A2/A3: POST ค่าอ้างอิง → ผล DC Bias จาก Python (ไม่ใช่ค่าฮาร์ดโคด)"""
        response = self.client.post("/calculate", data=dict(REFERENCE_INPUT))
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Forward-Active", html)
        self.assertIn("8.05", html)   # VCE ≈ 8.052 V
        self.assertIn("1.23", html)   # IC ≈ 1.230 mA

    def test_post_invalid_value(self):
        """A4: R1 ติดลบ → 200 พร้อมข้อความ error หน้าไม่ล้ม"""
        bad = dict(REFERENCE_INPUT)
        bad["r1"] = "-5"
        response = self.client.post("/calculate", data=bad)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", response.get_data(as_text=True))

    def test_post_missing_fields(self):
        """A4: ฟอร์มว่างเปล่า (ไม่มีฟิลด์ vcc) → 200 พร้อมข้อความ error"""
        response = self.client.post("/calculate", data={})
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอกค่า VCC", response.get_data(as_text=True))


FIXED_INPUT = {
    "circuit": "fixed", "vcc": "12", "rb": "1000", "rc": "2.2",
    "beta": "100", "vbe": "0.7",
}
EMITTER_INPUT = dict(FIXED_INPUT, circuit="emitter", re="1")


class TestBiasModes(unittest.TestCase):
    """Lab 03 — เลือกโหมดผ่าน circuit field; ตรวจเฉพาะช่องที่โหมดใช้"""

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_get_fixed_form(self):
        html = self.client.get("/?circuit=fixed").get_data(as_text=True)
        self.assertIn("Fixed Bias", html)
        self.assertIn('name="rb"', html)
        self.assertNotIn('name="r1"', html)

    def test_get_emitter_form(self):
        html = self.client.get("/?circuit=emitter").get_data(as_text=True)
        self.assertIn("Emitter Bias", html)
        self.assertIn('name="rb"', html)
        self.assertIn('name="re"', html)
        self.assertNotIn('name="r1"', html)

    def test_post_fixed_reference(self):
        html = self.client.post("/calculate", data=FIXED_INPUT).get_data(as_text=True)
        self.assertIn("Fixed Bias", html)
        self.assertIn("1.13", html)   # IC mA (คำนวณมือ)
        self.assertIn("9.51", html)   # VCE V

    def test_post_emitter_reference(self):
        html = self.client.post("/calculate", data=EMITTER_INPUT).get_data(as_text=True)
        self.assertIn("Emitter Bias", html)
        self.assertIn("1.03", html)   # IC mA
        self.assertIn("8.71", html)   # VCE V

    def test_post_unknown_circuit(self):
        data = dict(FIXED_INPUT, circuit="bogus")
        html = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("โหมดวงจรไม่ถูกต้อง", html)
        self.assertNotIn("DC Bias Results", html)

    def test_post_fixed_zero_rb_no_stale_result(self):
        # rb=0 พร้อม r1 ค้างจาก Divider → ต้อง error RB และไม่โชว์ผลรอบก่อน
        data = dict(FIXED_INPUT, rb="0", r1="100")
        html = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("RB ต้องมากกว่า 0", html)
        self.assertNotIn("DC Bias Results", html)


if __name__ == "__main__":
    unittest.main()
