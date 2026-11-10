# Validation — Lab 02

การตรวจสอบผล DC Bias กับการคำนวณอิสระ (มือ) ภายใต้แบบจำลองเดียวกัน
(Forward-Active Approximation)

## ค่าอ้างอิงอิสระ

อินพุต: VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V

| ปริมาณ | สมการ | คำนวณมือ | เว็บแสดง | ตรงกัน |
|---|---|---|---|---|
| VTH | 12×22/(100+22) | 2.1639 V | — (ภายใน) | ✓ |
| RTH | 100k×22k/122k | 18.033 kΩ | — (ภายใน) | ✓ |
| IB | (VTH−VBE)/(RTH+101×RE) | 12.2986 µA | 12.30 µA | ✓ |
| IC | β×IB | 1.22986 mA | 1.23 mA | ✓ |
| IE | 101×IB | 1.24216 mA | 1.24 mA | ✓ |
| VE | IE×RE | 1.24216 V | 1.24 V | ✓ |
| VB | VE+VBE | 1.94216 V | 1.94 V | ✓ |
| VC | VCC−IC×RC | 9.29431 V | 9.29 V | ✓ |
| VCE | VC−VE | 8.05215 V | 8.05 V | ✓ |

Region: Forward-Active (VCE 8.05 V > 0.2 V, IB > 0) — ไม่มีคำเตือน

## Automated Tests

`py -m unittest discover -s tests -v` → **12 tests OK**

- 6 unit tests (สมการ + validation + parse) ใน `tests/test_dc_bias.py`
- 2 warning-region tests (Cutoff, Saturation) ใน `tests/test_dc_bias.py`
- 4 HTTP tests ผ่าน Flask test client (GET /, POST อ้างอิง, POST ค่าผิด,
  POST ฟิลด์หาย) ใน `tests/test_web.py`

## การทดสอบด้วยตนเองผ่าน Browser (localhost)

- เปิด `http://127.0.0.1:5000/` → เห็นฟอร์ม 7 ช่อง ✓ (A1)
- กรอกค่าอ้างอิง → Calculate → ตารางผล + region Forward-Active ✓ (A2, A3)
- กรอก R1 = -5 → ข้อความ error "R1 ต้องมากกว่า 0" หน้าไม่ล้ม ✓ (A4)
- R2=1 → VTH≤VBE → คำเตือน Cutoff ✓ (A5)
- R1=R2=100k, RC=2.4k → VCE≈0.03 V → คำเตือน Saturation ✓ (A5)
