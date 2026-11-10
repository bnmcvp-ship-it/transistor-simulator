# ENG29 2121 — Lab 02: BJT DC Bias Web App

Web Application คำนวณ **DC Operating Point** ของวงจรขยาย BJT Common Emitter
แบบ **Voltage-Divider Bias** — รับค่าผ่านฟอร์มใน Browser แล้วให้ Python
Backend (Flask) คำนวณและส่งผลกลับมาแสดง (ไม่ใช่ค่าฮาร์ดโคดใน HTML)

## การติดตั้งและรัน

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell (Linux/macOS: source .venv/bin/activate)
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิด `http://127.0.0.1:5000/` ใน Browser

## การทดสอบ

```powershell
py -m unittest discover -s tests -v
```

12 tests ครอบคลุม: สมการวิศวกรรม, input validation, region warnings,
และ Flask HTTP routes ผ่าน test client

## อินพุต / เอาต์พุต

- **อินพุต:** VCC [V], R1, R2, RC, RE [kΩ], β, VBE [V]
- **เอาต์พุต:** VB, VE, VC, VCE [V], IC [mA], IB [µA], IE [mA]
  + Operating Region และคำเตือนเมื่อออกนอก Forward-Active

ข้อมูลทดลองอ้างอิง: VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ,
β=100, VBE=0.70 V → VB=1.94 V, VE=1.24 V, VC=9.29 V, VCE=8.05 V, IC=1.23 mA

## โครงสร้าง

```
├── app.py                  # Flask routes (GET /, POST /calculate)
├── dc_bias.py              # สมการวิศวกรรม — ไม่รู้จัก HTML/HTTP
├── templates/index.html    # ฟอร์ม + ผลลัพธ์ (Jinja)
├── static/style.css        # หน้าตาเว็บ
├── tests/                  # test_dc_bias.py + test_web.py
├── requirements.txt
└── docs/                   # design-note, validation, reflection
```

## ข้อจำกัดของแบบจำลอง

ใช้ **Forward-Active Approximation** (β, VBE คงที่) — ไม่ใช่ SPICE
ผลที่อยู่นอกสมมติฐาน (Cutoff: VTH≤VBE, Saturation: VCE<0.2 V) จะแสดง
คำเตือน และไม่ควรนับว่าเป็นค่าจำลองที่แม่นยำ
