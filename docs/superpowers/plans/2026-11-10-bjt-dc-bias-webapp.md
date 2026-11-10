# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Flask web app คำนวณ DC Operating Point ของวงจร BJT Common Emitter (Voltage-Divider Bias) จากอินพุต VCC, R1, R2, RC, RE, β, VBE

**Architecture:** แยก 3 ชั้น — `dc_bias.py` (Python ล้วน: คำนวณ+validate ไม่รู้จัก HTML/HTTP), `app.py` (Flask routes: GET / และ POST /calculate จับ error), `templates/index.html` + `static/style.css` (แสดงผล) ผ่าน Jinja

**Tech Stack:** Python 3.14 (`py`), Flask, Jinja2, unittest (ไม่ใช้ pytest — ไม่ต้องติดตั้งเพิ่มนอก requirements)

**Spec:** `docs/design-note.md`

## Global Constraints

- ตัวต้านทานอินพุตเป็น **kΩ** — แปลงเป็น Ω ภายในก่อนคำนวณ
- แสดงผล: VB/VE/VC/VCE [V], IC [mA], IB [µA], IE [mA]
- Validation ทั้งหมดอยู่ใน `dc_bias.py` ผ่าน exception `BiasError(ValueError)` พร้อมข้อความไทย
- ค่าผิด (non-numeric, หาย, R≤0, β≤0, VCC≤0) → หน้า HTML error ชัดเจน **ไม่ใช้ 500**
- Warning ไม่ทำให้คำนวณไม่ได้: Cutoff (`IB≤0` / `VTH≤VBE`), Saturation (`VCE<0.2` หรือ `VC≤VE`)
- ค่าอ้างอิงเป้าหมาย (VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.7):
  VB≈1.94420 V, VE≈1.24420 V, VC≈9.28987 V, VCE≈8.04567 V, IC≈1.23188 mA,
  IB≈12.3188 µA, IE≈1.24420 mA, region="Forward-Active", warnings=[]
- UI ภาษาไทย, ไม่มี JavaScript
- ทุก task จบด้วย `git commit` บน branch `main`

## Review Focus

1. ฟิลด์ว่าง (empty string) → error "กรุณากรอกค่า" ไม่ใช่ crash — test ใน Task 1
2. อินพุตไทย/ตัวหนังสือปน ("12a") → error ชัดเจน ไม่ใช่ 500 — test ใน Task 3
3. POST /calculate โดยไม่มีฟิลด์เลย (form ว่าง) → error ไม่ใช่ 500 — test ใน Task 3
4. kΩ→Ω: ผู้ใช้พิมพ์ "0.001" (ต้องการ 1 Ω) → error เพราะ ≤0 เกณฑ์ ไม่ใช่ผลลัพธ์พันเท่า — test ใน Task 1
5. Saturation จริง (RC ใหญ่ จน VC ต่ำกว่า VE) → warning ไม่ใช่ตัวเลขติดลบลอย ๆ — test ใน Task 2

---

### Task 1: Engineering Module `dc_bias.py` — คำนวณ + Validation

**Files:**
- Create: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces:
  - `class BiasError(ValueError)` — ข้อความไทย
  - `def analyze(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict`
    รับค่า **kΩ** (แปลงเป็น Ο ภายใน) คืน dict:
    `{"vth": V, "rth": Ω, "ib": A, "ic": A, "ie": A, "vb": V, "ve": V, "vc": V, "vce": V, "region": str, "warnings": [str]}`
  - `def parse_field(raw: str | None, name: str) -> float` — แปลง string→float, error ถ้าว่าง/ไม่ใช่เลข

- [ ] **Step 1: เขียน failing tests** — 5 test:
  1. `test_reference_case` — อินพุตอ้างอิง Global Constraints → ทุกค่าใกล้เคียง ±0.001 (เทียบ VB, VE, VC, VCE, IC*1e3=mA, IB*1e6=µA), region="Forward-Active", warnings ว่าง
  2. `test_parse_field_rejects_empty` — `parse_field("", "VCC")` → `BiasError` ที่มีชื่อ "VCC" ในข้อความ
  3. `test_parse_field_rejects_non_numeric` — `parse_field("12a", "R1")` → `BiasError`
  4. `test_analyze_rejects_invalid_values` — `analyze(vcc=0, ...)` → `BiasError`; `analyze(beta=-5, ...)` → `BiasError`; `analyze(r1=0, ...)` → `BiasError`
  5. `test_analyze_rejects_tiny_resistor_kohm` — `analyze(..., rc=0.001, ...)` (0.001 kΩ = 1 Ω > 0 จึง **ผ่าน** ถ้าเกณฑ์เป็น ≤0) — ยืนยันพฤติกรรม: ค่าบวกจิตผ่าน ค่า 0/ลบไม่ผ่าน
- [ ] **Step 2: รัน test ยืนยัน fail** — `py -m unittest discover -s tests -v` → FAIL (no module `dc_bias`)
- [ ] **Step 3: สร้าง `tests/__init__.py` (ไฟล์ว่าง) และเขียน `dc_bias.py`** — ตาม Interfaces; สมการตาม Spec; region/warnings:
  - `IB≤0` หรือ `VTH≤VBE` → region="Cutoff", warning "VTH ≤ VBE — ทรานซิสเตอร์ไม่นำกระแส (Cutoff) แบบจำลอง Forward-Active ใช้ไม่ได้"
  - `VCE<0.2` หรือ `VC≤VE` → region="Saturation", warning "VCE ต่ำ — ทรานซิสเตอร์เข้าสู่ Saturation แบบจำลอง Forward-Active ใช้ไม่ได้"
  - ไม่งั้น region="Forward-Active", warnings=[]
  - ค่าที่คำนวณใน Cutoff/Saturation ยังคืนพร้อม warning (ไม่โกหกว่าแม่น)
- [ ] **Step 4: รัน test ยืนยันผ่านทั้งหมด**
- [ ] **Step 5: Commit** — `git add dc_bias.py tests/` → `feat: add dc_bias engineering module with validation and region warnings`

### Task 2: Warning Scenarios — Cutoff/Saturation

**Files:**
- Modify: `tests/test_dc_bias.py` (เพิ่ม tests)

**Interfaces:**
- Consumes: `analyze()` จาก Task 1

- [ ] **Step 1: เขียน failing tests** — 2 test:
  1. `test_cutoff_case` — VCC=12, R1=100k, R2=1k (VTH≈0.119 V ≤ 0.7=VBE) → region="Cutoff", warnings ไม่ว่าง
  2. `test_saturation_case` — VCC=5, R1=100k, R2=22k, RC=10k, RE=1k, β=100, VBE=0.7 → VCE ต่ำมาก → region="Saturation", warnings ไม่ว่าง และ **ไม่มีค่าไหนเป็น NaN/inf**
- [ ] **Step 2: รันยืนยัน fail หรือผ่าน** — ถ้า Task 1 ถูกก็อาจผ่านเลย (นี่คือ regression pin)
- [ ] **Step 3: แก้ `dc_bias.py` ถ้า fail** — ตรวจสมการ
- [ ] **Step 4: รันยืนยันผ่าน**
- [ ] **Step 5: Commit** — `test: pin cutoff and saturation warning scenarios`

### Task 3: Flask App — routes + error handling

**Files:**
- Create: `app.py`, `templates/index.html`, `static/style.css`, `requirements.txt`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `analyze`, `parse_field`, `BiasError` จาก Task 1
- Produces: `create_app() -> Flask` (app factory, ใช้ test client ได้);
  route `GET /` → render ฟอร์ม; `POST /calculate` → render ฟอร์ม+ผล หรือ error

- [ ] **Step 1: เขียน failing tests** — 4 test ใช้ `app.test_client()`:
  1. `test_get_index` — GET / → 200, HTML มี "Calculate DC Bias" และช่อง input ทั้ง 7
  2. `test_post_calculate_reference` — POST ค่าอ้างอิง → 200, HTML มี "Forward-Active", ตัวเลข VCE ≈ "8.04", "1.23" (IC mA)
  3. `test_post_invalid_value` — POST ที่ R1="-5" → 200 (ไม่ใช่ 500), HTML มีข้อความ error
  4. `test_post_missing_fields` — POST แบบไม่มีฟิลด์ vcc → 200, HTML มีข้อความ error
- [ ] **Step 2: รันยืนยัน fail** — `py -m unittest discover -s tests -v` → 4 tests FAIL
- [ ] **Step 3: เขียน `requirements.txt`** (Flask เวอร์ชันปัจจุบัน) → `py -m pip install -r requirements.txt`
- [ ] **Step 4: เขียน `app.py`** — `create_app()` factory; POST /calculate: `parse_field` ทั้ง 7 ฟิลด์ (ชื่อฟิลด์: vcc, r1, r2, rc, re, beta, vbe) → `analyze(...)` → `render_template("index.html", result=..., form=...)`; `BiasError` → `render_template` พร้อม `error=ข้อความ`; ค่าแสดง: `ic_mA=ic*1000`, `ib_uA=ib*1e6`, `ie_mA=ie*1000`
- [ ] **Step 5: เขียน `templates/index.html`** — ฟอร์ม 7 ช่อง + ปุ่ม "Calculate DC Bias"; ถ้ามี result แสดงตาราง VB/VE/VC/VCE [V], IC [mA], IB [µA], IE [mA] + region + warnings (สีเหลือง/แดง); ถ้ามี error แสดงกล่องแดง; ค่าเดิมของฟอร์มคงอยู่หลัง submit
- [ ] **Step 6: เขียน `static/style.css`** — layout สะอาด อ่านง่าย (form บนซ้าย, ผลลัพธ์เป็นตาราง) ไม่ต้องสวยมาก
- [ ] **Step 7: รัน test ยืนยันผ่านทั้งหมด (Task 1–3)**
- [ ] **Step 8: รันเว็บจริงตรวจด้วยตา** — `py -m flask --app app run --debug` เปิด http://127.0.0.1:5000/ ทดลองค่าอ้างอิง + ค่าผิด แล้วปิด
- [ ] **Step 9: Commit** — `feat: add Flask app with form, results and error handling`

### Task 4: README + docs เตรียมส่ง

**Files:**
- Modify: `README.md` (แทนที่ section วิธีรัน)
- Create: `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: โครงสร้างไฟล์สุดท้ายจาก Task 1–3

- [ ] **Step 1: อัปเดต README** — คำสั่งจริง (`py -m venv .venv`, activate, install, `py -m flask --app app run --debug`, `py -m unittest discover -s tests -v`), สมการ, ข้อจำกัดแบบจำลอง
- [ ] **Step 2: เขียน `docs/validation.md`** — ตารางเทียบค่าอ้างอิงอิสระ (คำนวณมือ) กับผลจากเว็บ + ผล tests
- [ ] **Step 3: เขียน `docs/reflection.md`** — ตอบคำถามรายบุคคลจาก Lab Handout (เปิด index.html ตรง ๆ ≠ รัน Flask, ฟอร์มส่งข้อมูลไป Python อย่างไร, แก้ dc_bias.py ต้องแก้ HTML ไหม, ทำไม Region นอก Active ต้องมี Warning)
- [ ] **Step 4: รัน test สุดท้ายทั้งชุด** — `py -m unittest discover -s tests -v` → ผ่านหมด
- [ ] **Step 5: Commit** — `docs: add validation and reflection, update README run instructions`
