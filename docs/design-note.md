# Design Note — Lab 02: BJT DC Bias Web App

ENG29 2121 · Computer Programming for Electrical Engineers · 2/2569

## Intent / เป้าหมาย

Web Application สำหรับคำนวณ DC Operating Point ของวงจรขยาย **BJT Common Emitter
แบบ Voltage-Divider Bias** โดยให้ Python Backend คำนวณจริงผ่าน Flask — เพื่อให้
นักศึกษาเห็นความแตกต่างของ Frontend (Template/CSS) / Backend (Route) /
Engineering Module (สมการ) และผ่านเกณฑ์ตรวจรับ A1–A7 ภายในคาบเดียว

## Goals

- เปิดผ่าน `http://127.0.0.1:5000/` ได้ (A1)
- ฟอร์มรับ `VCC [V]`, `R1, R2, RC, RE [kΩ]`, `β`, `VBE [V]` → `POST /calculate`
- คำนวณด้วย `dc_bias.py` (Python ล้วน ไม่รู้จัก HTML/HTTP) แล้ว render ผลกลับ (A2)
- แสดง `VB, VE, VC, VCE [V]`, `IC [mA]`, `IB [µA]`, `IE [mA]` พร้อมหน่วย (A3)
- Validation: non-numeric / ค่าหาย / R≤0 / β≤0 / VCC≤0 → ข้อความ error ชัดเจน
  หน้าเว็บไม่ล้ม (A4)
- Region Warning: Cutoff (VTH≤VBE) / Saturation (VCE ต่ำ) → แจ้งข้อจำกัดของ
  Forward-Active Approximation (A5)
- Automated Tests: ≥3 unit tests (engineering math) + ≥1 Flask test-client test (A6)
- คลอน repo แล้วรันตาม README ได้ (A7)

## Non-goals (ขอบเขต Week 2)

- ไม่ทำ AC Small-Signal / Bode / Transient / Signal Generator / Overlay Animation
- ไม่ทำ Bias Types อื่น (Fixed Bias, Emitter Bias — สัปดาห์หน้า)
- ไม่สร้าง SPICE Solver เอง, ไม่มี FET
- ไม่ต้องลอก UI จากภาพ concept ทุกพิกเซล

## Constraints

- Flask Debug Server ใช้เฉพาะเครื่องพัฒนา ไม่เปิดสู่เครือข่ายสาธารณะ
- ไม่ commit `.venv/`, `.env`, API keys, credentials
- Python 3.14 (`py` launcher) บน Windows

## สมการอ้างอิง (Forward-Active Approximation: β, VBE คงที่)

```
VTH = VCC × R2 / (R1 + R2)
RTH = R1×R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)×RE)
IC  = β × IB
IE  = (β+1) × IB
VE  = IE × RE
VB  = VE + VBE
VC  = VCC − IC × RC
VCE = VC − VE
```

**ข้อมูลทดลองอ้างอิง:** VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ,
β=100, VBE=0.70 V → ค่าอ้างอิง (คำนวณอิสระ, ใช้ตรวจ A3):
VTH=2.16393 V, RTH=18.0328 kΩ, IB≈12.2986 µA, IC≈1.22986 mA, IE≈1.24216 mA,
VE≈1.24216 V, VB≈1.94216 V, VC≈9.29431 V, VCE≈8.05215 V → Forward-Active ✓

## Approaches — ทางเลือกที่พิจารณา

| แนวทาง | ผลลัพธ์ | เลือก? |
|---|---|---|
| **HTML form POST → Flask route → Jinja render ผล** | ตรงโครงสร้าง templates/static ของ Lab, test ผ่าน Flask test client ตรง ๆ, จบใน timebox | ✅ เลือก |
| JSON API + JavaScript fetch | ยืดหยุ่นกว่าสำหรับสัปดาห์ถัดไป แต่เพิ่มงาน JS นอกขอบเขตคาบนี้ | ✗ |

## การตัดสินใจ (ของ AI — ผู้ใช้แก้ไขได้)

- หน่วยอินพุต: ตัวต้านทานเป็น **kΩ** (แปลงเป็น Ω ใน backend ก่อนคำนวณ),
  แรงดันเป็น V, β ไม่มีหน่วย — แสดง IC เป็น mA, IB เป็น µA, IE เป็น mA
- Routes: `GET /` → ฟอร์ม, `POST /calculate` → ผลลัพธ์
- ภาษา UI: ไทย (โจทย์/ผู้ใช้ใช้ไทย)
- Validation ทำใน `dc_bias.py` เป็นหลัก (raise `ValueError` พร้อมข้อความไทย),
  route จับ exception → แสดง error ในหน้าเดิม (HTTP 200, หน้าไม่ล้ม)
- Saturation Warning เกณฑ์: `VCE < 0.2 V` หรือ `VC ≤ VE` ·
  Cutoff: `IB ≤ 0` (VTH ≤ VBE)
- โครงสร้างไฟล์ตาม Lab Handout: `app.py`, `dc_bias.py`,
  `templates/index.html`, `static/style.css`, `tests/`, `requirements.txt`,
  `README.md`, `docs/`

## สิ่งที่เหลือให้ผู้สร้าง (builder)

- จำนวนน้อย: การจัดหน้า/สีของ `style.css` (แนวทางคือสะอาด อ่านง่าย
  ตารางผลลัพธ์ชัดเจน), รูปแบบการแสดงตัวเลข (3–4 ตำแหน่งสำคัญ)
