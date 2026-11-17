# ENG29 2121 — Lab 02 → Lab 03: BJT DC Bias Web App

Web Application คำนวณ **DC Operating Point** ของวงจรขยาย BJT Common Emitter
3 แบบในเว็บเดียว: **Voltage-Divider Bias**, **Fixed Bias** และ **Emitter Bias**
— รับค่าผ่านฟอร์มใน Browser แล้วให้ Python Backend (Flask) คำนวณและส่งผลกลับ
มาแสดง (ไม่ใช่ค่าฮาร์ดโคดใน HTML)

## การติดตั้งและรัน

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell (Linux/macOS: source .venv/bin/activate)
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิด `http://127.0.0.1:5000/` ใน Browser แล้วเลือกโหมดจากแถบด้านบน
(ลิงก์โหลดฟอร์มใหม่ตามโหมดโดยไม่ต้องใช้ JavaScript)

## สามโหมดการคำนวณ

| โหมด (`circuit`) | ช่องที่ใช้ | สมการหลัก |
|---|---|---|
| `divider` (default) | VCC, R1, R2, RC, RE, β, VBE | VTH=VCC·R2/(R1+R2), RTH=R1∥R2, IB=(VTH−VBE)/(RTH+(β+1)RE) |
| `fixed` | VCC, RB, RC, β, VBE | IB=(VCC−VBE)/RB |
| `emitter` | VCC, RB, RC, RE, β, VBE | IB=(VCC−VBE)/(RB+(β+1)RE) |

ทุกโหมดใช้ IC=β·IB, IE=(β+1)IB, VE=IE·RE (Fixed: VE=0), VB=VE+VBE,
VC=VCC−IC·RC, VCE=VC−VE — สมการทั้งหมดอยู่ใน `dc_bias.py` เท่านั้น

ตัวอย่าง VCC=12 V, RC=2.2 kΩ, β=100, VBE=0.70 V:

| โหมด | อินพุตเพิ่ม | IC | VCE |
|---|---|---|---|
| Divider | R1=100, R2=22, RE=1 kΩ | 1.23 mA | 8.05 V |
| Fixed | RB=1000 kΩ | 1.13 mA | 9.51 V |
| Emitter | RB=1000 kΩ, RE=1 kΩ | 1.03 mA | 8.71 V |
| Emitter | RB=1000 kΩ, RE=2 kΩ | 0.94 mA | 8.03 V |

RB=0 → error `[Fixed Bias] RB ต้องมากกว่า 0 (หน่วย kΩ)` หน้าไม่ล้ม และไม่โชว์ผลรอบก่อน

## การทดสอบ

```powershell
py -m unittest discover -s tests -v
```

**24 tests** ครอบคลุม: สมการ 3 โหมด, input validation, region warnings,
เลือกโหมดผ่าน HTTP, error ไม่โชว์ stale result — ผ่าน Flask test client
ผลจริงดูได้ใน `docs/test-log.txt`

## การตรวจผลผ่าน Browser

ตาราง A1–A5, วิธีตรวจ, และสถานะเครื่องมืออยู่ใน `docs/validation.md`
(ใช้ **OpenCode Browser** เพราะไม่มี node/npx สำหรับ Playwright MCP —
บันทึก `NOT RUN` พร้อมเหตุผลตาม handout)
ภาพหน้าจออยู่ใน `docs/screenshots/`

## โครงสร้าง

```
├── app.py                  # Flask routes — เลือกโหมด + ตรวจ field ตามโหมด
├── dc_bias.py              # สมการวิศวกรรม 3 โหมด — ไม่รู้จัก HTML/HTTP
├── templates/index.html    # ฟอร์ม + แถบเลือกโหมด + ผลลัพธ์ (Jinja)
├── static/style.css        # หน้าตาเว็บ
├── tests/                  # test_dc_bias.py + test_web.py
├── requirements.txt
└── docs/                   # design-note, validation, reflection, test-log, screenshots
```

## ส่งงาน / GitHub

- **Repo (public):** https://github.com/bnmcvp-ship-it/transistor-simulator
- **Branch:** `main`
- **Lab 03 commit SHA:**
  - `9c5f00e` — feat: add fixed and emitter bias equations
  - `af12cea` — feat: select bias circuit mode in Flask form
  - `0a2ee1e` — docs: record Lab 03 A1–A5 browser validation and screenshots
  - (commit ล่าสุดหลังอัปเดต-section นี้ดูได้จากหน้า repo — HEAD ตรงกับ remote แล้ว)
- **ส่วนที่ AI ช่วยเขียน:** ฟังก์ชันใหม่ใน `dc_bias.py`, mode dispatch ใน `app.py`,
  แถบเลือกโหมดใน template, test ใหม่ 11 ตัว และเอกสาร — สรุปบทบาทอยู่ใน
  `docs/reflection.md` ข้อ 7; นักศึกษาตรวจอิสระด้วยค่าคำนวณมือและ browser จริงตาม
  `docs/validation.md`

## ข้อจำกัดของแบบจำลอง

ใช้ **Forward-Active Approximation** (β, VBE คงที่) — ไม่ใช่ SPICE
ผลที่อยู่นอกสมมติฐาน (Cutoff: IB≤0 / VTH≤VBE, Saturation: VCE<0.2 V) จะแสดง
คำเตือน และไม่ควรนับว่าเป็นค่าจำลองที่แม่นยำ
