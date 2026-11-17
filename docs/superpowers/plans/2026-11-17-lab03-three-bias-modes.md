# Lab 03 Three Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ต่อยอด Flask app Lab 2 ให้คำนวณ Fixed Bias และ Emitter Bias ได้ โดย Divider เดิมให้ผลเดิม และตรวจ A1–A5 ผ่าน browser จริง

**Architecture:** สมการอยู่ใน `dc_bias.py` เพิ่มฟังก์ชันคู่ขนานกับ `analyze()` เดิม; `app.py` เลือกฟังก์ชันตาม `circuit` แล้วส่งผลรูปแบบเดิมให้ Jinja แสดง; ตรวจผลด้วย OpenCode Browser (Playwright MCP = NOT RUN เพราะไม่มี node/npx) แล้วบันทึกหลักฐานใน docs

**Tech Stack:** Python 3.14, Flask 3.1, unittest, OpenCode Browser tools, Git/GitHub Desktop

**Spec:** `docs/superpowers/specs/2026-11-17-lab03-three-bias-modes-design.md`

## Global Constraints

- ใช้ repo `transistor-simulator` เดิม ทำงานบน `main`; 13 tests เดิมต้องผ่านตลอด
- kΩ → Ω ภายในฟังก์ชันครั้งเดียว; ผลเป็น SI (V, A) ใช้ชื่อคีย์เดิม `vb,ve,vc,vce,ib,ic,ie,region,warnings`
- อินพุตผิด (ว่าง/ไม่ใช่เลข/ไม่จำกัด/ค่าบวก ≤ 0) → `BiasError` ข้อความไทย; อินพุตถูกแต่ IB ≤ 0 หรือ VCE ≤ 0.2 → warning
- ไม่ใส่สมการใน HTML, ไม่ rebuild โปรเจกต์, ไม่ทำ AC/SPICE/DC Load Line
- `circuit` ที่รับได้: `divider` (default), `fixed`, `emitter`; ค่าอื่น → error
- อินพุตร่วม A1–A5: VCC=12 V, RC=2.2 kΩ, β=100, VBE=0.70 V

## Review Focus

- `circuit=unknown` ต้อง error ไม่แอบไปเป็น Divider → test ใน Task 2
- A5: Fixed `RB=0` พร้อมค่าอื่นครบ ต้อง error และไม่แสดงผลรอบก่อน → test ใน Task 2
- `"nan"`, `"1e400"` ต้องถูกปฏิเสธ (parse_field เดิม + test เดิม) → รันซ้ำใน Task 1
- เปลี่ยน RE จาก 1→2 kΩ ใน Emitter ต้องทำให้ IC ลด (1.0263 → 0.9401 mA) → test ใน Task 1
- VCE ≤ 0.2 (Fixed RB=100 kΩ) ต้องมี warning ไม่ใช่ผลเขียวเงียบ → test ใน Task 1

---

### Task 1: ฟังก์ชันคำนวณ Fixed/Emitter ใน `dc_bias.py`

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces:
  - `analyze_fixed(vcc: float, rb: float, rc: float, beta: float, vbe: float) -> dict`
  - `analyze_emitter(vcc: float, rb: float, rc: float, re: float, beta: float, vbe: float) -> dict`
  - ทั้งคู่คืนคีย์ชุดเดิม (`vth/rth` เฉพาะ Divider ไม่บังคับ); resistor kΩ, ผล SI

- [ ] **Step 1: เขียน failing tests** ใน `tests/test_dc_bias.py` (import ฟังก์ชันใหม่):
  - `test_fixed_reference`: `analyze_fixed(12, 1000, 2.2, 100, 0.7)` → `ic*1e3 ≈ 1.1300` mA, `vce ≈ 9.5140` V, `vb ≈ 0.7`, `ve == 0`, region `Forward-Active`, warnings ว่าง (delta 0.001)
  - `test_emitter_reference`: `analyze_emitter(12, 1000, 2.2, 1, 100, 0.7)` → `ic*1e3 ≈ 1.0263` mA, `vce ≈ 8.7055` V, `ve ≈ 1.0366` V
  - `test_emitter_more_re_lower_ic`: RE=2 → `ic*1e3 ≈ 0.9401` mA และน้อยกว่า case RE=1
  - `test_fixed_rejects_zero_rb`: `analyze_fixed(12, 0, ...)` → `BiasError` มี "RB ต้องมากกว่า 0"
  - `test_fixed_saturation_warning`: `analyze_fixed(12, 100, 2.2, 100, 0.7)` → warnings ไม่ว่าง (VCE ≤ 0.2) และทุกค่ finite

- [ ] **Step 2: รันยืนยัน RED** — `py -m unittest discover -s tests -v` → 5 tests ใหม่ fail (ImportError/NameError), 13 เก่ายัง ok

- [ ] **Step 3: implement** ใน `dc_bias.py`:
  - helper ภายในสำหรับ validation + แปลง kΩ→Ω + คำนวณผลร่วม (IC=βIB, IE=(β+1)IB, VE=IE·RE หรือ 0 สำหรับ Fixed, VB=VE+VBE, VC=VCC−IC·RC, VCE=VC−VE)
  - `analyze_fixed`: `IB=(VCC−VBE)/RBΩ`
  - `analyze_emitter`: `IB=(VCC−VBE)/(RBΩ+(β+1)·REΩ)`
  - `analyze()` เดิมห้ามเปลี่ยนสมการ; ใช้ helper ร่วมได้ถ้าผลทดสอบเดิมไม่เปลี่ยน

- [ ] **Step 4: รันยืนยัน GREEN** — `py -m unittest discover -s tests -v` → 18 tests OK

- [ ] **Step 5: Commit** — `git add dc_bias.py tests/test_dc_bias.py && git commit -m "feat: add fixed and emitter bias equations"`

### Task 2: เลือกโหมดและปรับฟอร์มใน Flask

**Files:**
- Modify: `app.py`, `templates/index.html`, `tests/test_web.py`

**Interfaces:**
- Consumes: `analyze_fixed`, `analyze_emitter`, `analyze`, `parse_field`, `BiasError` จาก Task 1
- Produces: GET `/` รับ query `circuit` (default `divider`); POST `/calculate` อ่าน `circuit`; ตัวแปร template `circuit, circuit_label, fields, form, rows, region, warnings, error`

- [ ] **Step 1: เขียน failing tests** ใน `tests/test_web.py`:
  - `test_get_fixed_form`: GET `/?circuit=fixed` → 200, มี `name="rb"` และไม่มี `name="r1"`; มีคำว่า "Fixed Bias"
  - `test_get_emitter_form`: GET `/?circuit=emitter` → 200, มี `name="rb"` และ `name="re"`
  - `test_post_fixed_reference`: POST `circuit=fixed, vcc=12, rb=1000, rc=2.2, beta=100, vbe=0.7` → 200, มี "Fixed Bias", "1.13", "9.51"
  - `test_post_emitter_reference`: POST `circuit=emitter, ..., rb=1000, re=1` → "Emitter Bias", "1.03", "8.71"
  - `test_post_unknown_circuit`: POST `circuit=bogus` + ค่าครบ → 200, มีข้อความ error เรื่องโหมด, ไม่มีตารางผล
  - `test_post_fixed_zero_rb_no_stale_result`: POST `circuit=fixed, rb=0` + `r1=100` (ค่าค้างจาก Divider) → error "RB ต้องมากกว่า 0" และไม่มี "DC Bias Results"

- [ ] **Step 2: รันยืนยัน RED** — `py -m unittest tests.test_web -v` → 6 ใหม่ fail, 4 เก่ายัง ok

- [ ] **Step 3: implement `app.py`**:
  - `CIRCUITS = {"divider": (...), "fixed": (...), "emitter": (...)}` เก็บ label และรายชื่อ field ที่ใช้
  - `index()`: อ่าน `request.args.get("circuit", "divider")`; validate ถ้าไม่รู้จัก → error template; ส่ง field list ตามโหมด
  - `calculate()`: อ่าน `circuit` จาก form; unknown → error; parse/ตรวจเฉพาะ field ของโหมด; เรียก `analyze`/`analyze_fixed`/`analyze_emitter` ด้วย `if/elif`; ส่ง `circuit_label` ติดไปกับผล/error; ไม่ส่ง rows ตอน error
  - `app = create_app()` คงเดิม
- [ ] **Step 4: implement `templates/index.html`**: แถบลิงก์เลือกโหมด (`/?circuit=divider|fixed|emitter`, โหมดปัจจุบันทำเครื่องหมาย), loop field ตามโหมด, ปุ่ม "Calculate DC Bias", หัวข้อผล/error มี `circuit_label` อยู่ด้วย

- [ ] **Step 5: รันยืนยัน GREEN** — `py -m unittest discover -s tests -v` → 24 tests OK

- [ ] **Step 6: Commit** — `git add app.py templates/index.html tests/test_web.py && git commit -m "feat: select bias circuit mode in Flask form"`

### Task 3: ตรวจ A1–A5 ใน browser + เอกสาร + Push

**Files:**
- Modify: `docs/validation.md`, `README.md`, `docs/reflection.md` (เพิ่มคำตอบคำถามปิด Lab), `docs/test-log.txt`

**Interfaces:**
- Consumes: แอปที่รันได้จาก Task 2; ค่าคาดหมายอิสระในหัวข้อ Global Constraints/Review Focus และ spec

- [ ] **Step 1: รัน server** — `py -m flask --app app run --debug` background; เปิด `http://127.0.0.1:5000/` ด้วย OpenCode Browser; ตรวจ snapshot เห็นหัวข้อและช่องจริง ≥2 ช่อง พร้อมระบุชื่อเครื่องมือที่ใช้
- [ ] **Step 2: รัน A1–A5 ผ่าน browser จริง** — ใช้ค่าคาดหมายจาก spec (ห้ามเอาค่าจากโค้ดมาเป็นคำตอบอ้างอิง): A1 Divider, A2 Fixed RB=1000 kΩ, A3 Emitter RB=1000 kΩ/RE=1 kΩ, A4 Emitter เฉพาะ RE=2 kΩ, A5 Fixed RB=0; อ่าน snapshot หลังส่งทุกครั้ง; เก็บ screenshot อย่างน้อย 1 กรณี
- [ ] **Step 3: เขียนผลจริงลง `docs/validation.md`** — ตาราง A1–A5 มี input/current mode/c่าคาดหมาย/ผลที่เห็น+หน่วย/วิธีตรวจ (`OpenCode Browser`)/status; บันทึก Playwright MCP = `NOT RUN` พร้อมเหตุผล "ไม่มี node/npx ในเครื่อง"; อธิบายบทบาท MCP สั้น ๆ
- [ ] **Step 4: อัปเดต README** — วิธีรัน, 3 โหมด, ตัวอย่างอินพุต/ผล, หมายเหตุ tool ที่ใช้ตรวจ; อัปเดต reflection คำถามปิด Lab
- [ ] **Step 5: รัน test สุดท้าย + บันทึก log** — `py -m unittest discover -s tests -v > docs/test-log.txt`; ต้อง 24 tests OK
- [ ] **Step 6: ตรวจ staged diff** — `git diff` และ `git diff --staged`; ห้าม stage `.venv`, `.env`, credentials
- [ ] **Step 7: Commit + Push** — commit เอกสาร; push origin ด้วย credential ที่เก็บไว้; ยืนยัน remote HEAD = local HEAD; ปิด server หลังเก็บหลักฐาน

## Self-Review

- ครบ spec: 3 ฟังก์ชัน/เลือกโหมด/ตรวจเฉพาะช่อง/error กับ warning/ฟอร์ม/เอกสาร/push ✓
- ประเภทตรงกัน: `analyze_fixed`/`analyze_emitter` ใช้ชื่อเดียวกันทุก task ✓
- Review Focus ทั้ง 5 มี test รับผิดชอบ ✓
- ขนาด plan ใกล้เคียง spec ไม่ได้เขียนโค้ดแทน ✓
