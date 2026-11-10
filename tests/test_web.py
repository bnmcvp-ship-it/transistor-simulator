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


if __name__ == "__main__":
    unittest.main()
