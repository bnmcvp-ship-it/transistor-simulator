# ENG29 2121 — Lab 02: BJT DC Bias Web App

ไฟล์รายวิชา ENG29 2121 (Computer Programming for Electrical Engineers) 2/2569

Web Application สำหรับคำนวณ DC Bias ของวงจรขยาย BJT Common Emitter
แบบ Voltage-Divider Bias ด้วย Python Flask

- **Input:** VCC, R1, R2, RC, RE, β, VBE
- **Output:** VB, VE, VC, VCE, IC (DC Operating Point) พร้อม Validation และ Region Warning
- **เทคโนโลยี:** Flask · Jinja Templates · unittest

> สถานะ: เริ่มต้นโปรเจกต์ — รายละเอียดการออกแบบจะเพิ่มหลังผ่านขั้นตอน Brainstorming

## วิธีรัน (จะอัปเดตเมื่อพัฒนาจริง)

```bash
py -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิด `http://127.0.0.1:5000/` ใน Browser

## โครงสร้างเป้าหมาย (ตาม Lab Handout)

```
transistor-simulator/
├── app.py                  # Flask application & HTTP routes
├── dc_bias.py              # independent engineering calculations
├── templates/index.html    # input form + DC results (Jinja)
├── static/style.css        # responsive layout
├── tests/                  # unit + Flask HTTP tests
├── requirements.txt
├── README.md
└── docs/                   # design-note, validation, reflection
```
