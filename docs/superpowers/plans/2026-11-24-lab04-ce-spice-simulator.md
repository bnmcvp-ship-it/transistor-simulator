# Lab 04 CE SPICE Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ต่อยอด Flask Lab 3 เป็น CE Voltage Divider simulator ที่รัน ngspice `.op/.ac/.tran` จริง โดยไม่ทำลาย DC Bias 3 โหมดเดิม

**Architecture:** คง `/calculate` และ `dc_bias.py` ไว้ตรง ๆ เพิ่ม route `/simulate` และโมดูล `spice_engine.py` เป็น adapter เดียวที่สร้าง netlist เรียก ngspice ด้วย `subprocess.run` และ parse ผล ส่วนหน้าเว็บเพิ่ม Analysis Mode + กราฟ SVG จากข้อมูลที่ server ส่งมา

**Tech Stack:** Python 3.14.2, Flask ≥3.0, unittest, ngspice 47 (portable), Node 26.13.1 + npx Impeccable, OpenCode Browser

**Spec:** `docs/superpowers/specs/2026-11-24-lab04-ce-spice-simulator-design.md`

## Global Constraints

- ใช้ repo เดิม `transistor-simulator`; commit ก่อนเริ่มคือ `64a34e0`
- 24 tests เดิมต้องผ่านทุก task (`py -m unittest discover -v`)
- ห้ามใช้ `shell=True`; ต้องใช้ `subprocess.run([...], timeout=..., cwd=run_dir, capture_output=True, text=True)`
- ต้องตรวจ `returncode`, log ว่าง, timeout และ parse fail; error ต้องไม่โชว์ผล/กราฟเก้า
- ต้องไม่ hard-code ค่า gain/cutoff/waveform; ทุกตัวเลขต้องตาม ngspice output จริง
- ngspice ที่ใช้จริง: `C:\Users\B6829681\AppData\Local\Temp\opencode\ngspice-47\Spice64\bin\ngspice_con.exe` (version 47)
- Node/npx ที่ใช้จริง: `C:\Users\B6829681\AppData\Local\Temp\opencode\node-portable\node-v26.13.1-win-x64`
- ทุกคำสั่ง npx ต้อง prefix PATH ด้วย path Node ข้างบน
- Input fixture: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, Cin/Cout 10 µF, source 10 mV peak @ 1 kHz
- BJT model ต้องมาจาก Starter Kit ของอาจารย์ ห้ามเดาค่าเอง
- Baseline ไม่มี emitter bypass capacitor
- ไม่ commit `.venv/`, `.env`, token หรือไฟล์ run ชั่วคราว Large

## Review Focus

- **RE = 0 / amplitude = 0 / frequency ≤ 0** → ต้อง error พร้อมชื่อฟิลด์ และไม่มีผลเก่า → ทดสอบใน Task 2 + Task 5
- **ngspice หาย / returncode ≠ 0 / timeout / log ว่าง** → ต้องแสดง Error ไม่ใช่ Success → ทดสอบใน Task 3 + Task 5
- **เปลี่ยน RE หรือ amplitude แล้วผลต้องเปลี่ยน** → พิสูจน์ว่าไม่ใช่กราฟ Hard-code → ทดสอบใน Task 4
- **จุดวัด Vin สำหรับ Gain/Phase ต้องชัด** → ต้องระบุ node คู่เดียวกันใน netlist และ legends → ทดสอบใน Task 1 + Task 4
- **Desktop/mobile ตัดแกนกราฟหรือปุ่ม** → ต้องอ่านหน่วย/สถานะได้ทั้ง 1280 px และ 390 px → ทดสอบใน Task 6 + Task 7

---

### Task 1: Inspector Starter Kit + ตรวจ ngspice smoke

**Files:**
- Create: `docs/superpowers/starter-inventory.md`
- Create: `tests/test_spice_smoke.py`
- Create/Modify: `spice_engine.py` (เฉพาะ `SpiceError`, `find_ngspice`, `load_starter`, constants)

**Interfaces:**
- Consumes: Starter Kit ที่ผู้ใช้จะวางใน repo (ยังไม่มีตอนเขียน plan นี้)
- Produces: `spice_engine.SpiceError`, `find_ngspice(explicit: str | None = None) -> str`,
  `load_starter() -> dict` ที่มี keys `model`, `nodes`, `decks`, `model_file`,
  `run(mode: str, values: dict[str, float], starter: dict | None = None,
  exe: str | None = None) -> dict`, และ inventory file ที่ระบุชื่อไฟล์/node/directive จริง

- [ ] **Step 1: ตรวจมี Starter Kit ใน repo**

Run: `rg --files | rg -i '\.(cir|ckt|net|mod|lib|raw|spice|zip)$'`
Expected: เจอไฟล์อย่างน้อย 1 ชุด ถ้าไม่เจอให้หยุด task นี้แล้วแจ้งผู้ใช้ (ห้ามเดา model เอง)

- [ ] **Step 2: อ่าน Starter Kit ทุกไฟล์แล้วเขียน inventory**

เขียน `docs/superpowers/starter-inventory.md` ให้ระบุ: ชื่อ BJT model + ที่มาของ model,
node ของ Vin/Vout/ground, directive ที่ใช้จริงสำหรับ `.op/.ac/.tran`,
และว่าต้องแก้ netlist อะไรบ้างให้รับค่า RE/amplitude/frequency ได้

- [ ] **Step 3: เขียน failing smoke test**

```python
class TestNgspiceSmoke(unittest.TestCase):
    def test_op_runs_real_ngspice(self):
        from spice_engine import find_ngspice, load_starter, run
        self.assertIsNotNone(find_ngspice())
        result = run("dc", {"vcc": 12.0, "r1": 100e3, "r2": 22e3,
                            "rc": 2.2e3, "re": 1e3}, load_starter())
        self.assertEqual(result["status"], "success")
        self.assertIn("vb", result["scalars"])
        self.assertGreater(result["scalars"]["ic"], 0)
```

- [ ] **Step 4: รัน test ให้ fail ก่อน**

Run: `py -m unittest tests.test_spice_smoke -v`
Expected: FAIL (`ModuleNotFoundError: spice_engine`)

- [ ] **Step 5: implement minimal `spice_engine.py` ตาม interface ข้างบน**

`find_ngspice` อ่าน `NGSPICE_EXE` ก่อนแล้วค่อย PATH; `load_starter` อ่าน inventory
ที่ pin ไว้; `run` ยังทำเฉพาะ `.op` และใช้ `subprocess.run` ตาม Global Constraints

- [ ] **Step 6: รัน smoke test ให้ผ่าน**

Run: `py -m unittest tests.test_spice_smoke -v`
Expected: PASS พร้อม `ngspice_version` มีคำว่า `47`

- [ ] **Step 7: commit**

```bash
git add spice_engine.py tests/test_spice_smoke.py docs/superpowers/starter-inventory.md
git commit -m "feat: inspect starter kit and smoke-test real ngspice .op"
```

---

### Task 2: Input validation และ error contract

**Files:**
- Create: `tests/test_spice_validation.py`
- Modify: `spice_engine.py`

**Interfaces:**
- Consumes: `spice_engine.SpiceError` จาก Task 1
- Produces: `parse_spice_form(value: str | None, label: str, *, minimum: float = 0.0) -> float`

- [ ] **Step 1: เขียน failing tests** (empty, None, `"12a"`, `"nan"`, `"inf"`, `"0"` สำหรับ RE/amplitude/frequency, และ `"1e400"`)

Assert ทุกกรณี raise `SpiceError` และ `str(exc)` มีชื่อ label

- [ ] **Step 2: รันให้ fail**

Run: `py -m unittest tests.test_spice_validation -v`
Expected: FAIL (`parse_spice_form` ไม่มี)

- [ ] **Step 3: implement `parse_spice_form`**

ใช้ `float()` + `math.isfinite()` + ตรวจ `> minimum`; ห้ามส่งข้อความฟอร์มเข้า netlist โดยตรง

- [ ] **Step 4: รันให้ผ่าน + regression**

Run: `py -m unittest tests.test_spice_validation -v` แล้ว `py -m unittest discover -v`
Expected: PASS ทั้ง 2 คำสั่ง (24 tests เดิมยังผ่าน)

- [ ] **Step 5: commit**

```bash
git add spice_engine.py tests/test_spice_validation.py
git commit -m "feat: validate SPICE form inputs before netlist generation"
```

---

### Task 3: Netlist + run + parse DC operating point

**Files:**
- Create: `tests/test_spice_dc.py`
- Modify: `spice_engine.py`

**Interfaces:**
- Consumes: `load_starter()`, `parse_spice_form()`, `SpiceError`
- Produces: `build_netlist(mode: str, values: dict[str, float], starter: dict) -> str`,
  `parse_op_log(log_text: str) -> dict[str, float]` (SI: V และ A),
  `run(...)` คืน `scalars` สำหรับ mode `"dc"`

- [ ] **Step 1: เขียน failing tests**

สองกรณี: (a) `parse_op_log` กับตัวอย่าง log จริงจาก Task 1 ต้องคืน
`vb,ve,vc,vce,ic,ib` เป็น float; (b) `run("dc", ... RE=1k)` แล้ว `run("dc", ... RE=2k)`
ต้องได้ `ic` ต่างกัน

- [ ] **Step 2: รันให้ fail**

Run: `py -m unittest tests.test_spice_dc -v`
Expected: FAIL

- [ ] **Step 3: implement `build_netlist` + `parse_op_log` + ขยาย `run`**

ทุกรอบใช้ `tempfile.TemporaryDirectory()`; log/raw/cir อยู่ใน cwd นั้น;
ตรวจ `returncode != 0` หรือ log ว่างหรือ parse ไม่ได้ → raise `SpiceError`

- [ ] **Step 4: รันให้ผ่าน + regression**

Run: `py -m unittest tests.test_spice_dc -v` แล้ว `py -m unittest discover -v`
Expected: PASS; `ic(RE=2k) < ic(RE=1k)`

- [ ] **Step 5: commit**

```bash
git add spice_engine.py tests/test_spice_dc.py
git commit -m "feat: generate netlist, run .op and parse real DC output"
```

---

### Task 4: AC และ Transient series

**Files:**
- Create: `tests/test_spice_series.py`
- Modify: `spice_engine.py`

**Interfaces:**
- Consumes: `build_netlist()`, `run()`, `load_starter()`
- Produces: `parse_series(log_text: str, mode: str) -> dict` ที่คืน
  `{"x": list[float], "unit_x": str, "y": list[float], "unit_y": str,
     "series": dict[str, list[float]]}`; `run("ac"|"tran", ...)` ใส่ key `series`

- [ ] **Step 1: เขียน failing tests**

(a) `run("ac", ...)` → `unit_x == "Hz"`, `unit_y == "dB"`, มี `phase` ใน `series`, `len(x) > 10`
(b) `run("tran", amplitude=0.010, frequency=1000)` → `unit_x == "s"`, มี `vin` และ `vout`
(c) run ซ้ำด้วย `amplitude=0.020` → `max(abs(vout))` เปลี่ยนตามจริง (ไม่ hard-code)

- [ ] **Step 2: รันให้ fail**

Run: `py -m unittest tests.test_spice_series -v`
Expected: FAIL

- [ ] **Step 3: implement `.ac/.tran` netlist + `parse_series`**

ใช้ directive จาก Starter Kit; พิมพ์ค่า Vin ที่ node เดียวกับ Vout เสมอ;
phase เป็น degree; ถ้า sweep ไม่มี -3 dB ให้คืน `cutoff: "not determined in sweep range"` ห้ามแต่งตัวเลข

- [ ] **Step 4: รันให้ผ่าน + regression**

Run: `py -m unittest tests.test_spice_series -v` แล้ว `py -m unittest discover -v`
Expected: PASS; ข้อ (c) ต้องต่างกันอย่างชัดเจน

- [ ] **Step 5: commit**

```bash
git add spice_engine.py tests/test_spice_series.py
git commit -m "feat: add AC Bode and transient series from ngspice output"
```

---

### Task 5: Flask `/simulate` route

**Files:**
- Modify: `app.py`
- Create: `tests/test_simulate_route.py`

**Interfaces:**
- Consumes: `spice_engine.run`, `SpiceError`, `parse_spice_form`
- Produces: `SPICE_FIELDS`, `GET /?analysis=spice`, `POST /simulate`,
  context ที่ส่งให้ template: `analysis`, `spice_result`, `plot`, `engine_status`

- [ ] **Step 1: เขียน failing tests**

(a) `GET /?analysis=spice` → 200 และมี `name="amplitude"`, `name="frequency"`, no `name="beta"`
(b) `POST /simulate` with RE=0 → 200, มีคำว่า `error`, ไม่มีคำว่า `Success`, ไม่มี `<svg`
(c) monkeypatch ให้ `spice_engine.run` raise `SpiceError("ngspice timeout")` → ไม่มีผลเก่า
(d) `POST /calculate` ชุด REFERENCE_INPUT ยังได้ `8.05` และ `1.23`

- [ ] **Step 2: รันให้ fail**

Run: `py -m unittest tests.test_simulate_route -v`
Expected: FAIL (route ไม่มี)

- [ ] **Step 3: implement route**

คง `/calculate` เดิมทุกบรรทัด; `/simulate` validate ทุก field ด้วย `parse_spice_form` ก่อนเรียก `run`;
`SpiceError` ทุกกรณี return `render(... spice_result=None, plot=None, engine_status="error")`

- [ ] **Step 4: รันให้ผ่าน + regression**

Run: `py -m unittest discover -v`
Expected: PASS ทุก test รวม 24 เดิม

- [ ] **Step 5: commit**

```bash
git add app.py tests/test_simulate_route.py
git commit -m "feat: add /simulate route isolated from Lab 3 /calculate"
```

---

### Task 6: UI form, provenance และ SVG plots

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Create: `templates/_plot.html`
- Test: `tests/test_ui_lab04.py`

**Interfaces:**
- Consumes: `analysis`, `spice_result`, `plot`, `engine_status` จาก Task 5
- Produces: หน้าเดียวมี 2 analysis group, status badge, provenance badge, axis labels

- [ ] **Step 1: เขียน failing tests**

Assert HTML มี `name="analysis"`, `ngspice`, `dc_bias.py`, `Hz`, `dB`, `Time (s)`, `Vin (V)`, `Vout (V)`;
และเมื่อมี `plot` ต้องมี `<polyline` + `<text` สำหรับแกน

- [ ] **Step 2: รันให้ fail**

Run: `py -m unittest tests.test_ui_lab04 -v`
Expected: FAIL

- [ ] **Step 3: implement template + SVG partial**

ใช้ลิงก์ GET `/?analysis=analytical|spice` แบบเดิม (ไม่เพิ่ม JS);
วาด polyline จาก `plot["series"]` โดย normalize ไม่เพิ่ม chart library;
แสดงป้าย `Source: ngspice 47 · model: <ชื่อจาก Starter>` กับ `Analytical: dc_bias.py` แยกกัน

- [ ] **Step 4: รันให้ผ่าน + regression + browser smoke**

Run: `py -m unittest discover -v` และเปิด `http://127.0.0.1:5000/?analysis=spice`
Expected: PASS; เห็นฟอร์ม SPICE พร้อมหน่วย/status/ป้ายแหล่งผล

- [ ] **Step 5: commit**

```bash
git add templates/index.html templates/_plot.html static/style.css tests/test_ui_lab04.py
git commit -m "feat: add SPICE form, status badges and real-data SVG plots"
```

---

### Task 7: Impeccable critique → polish → audit

**Files:**
- Modify: `static/style.css` (เท่านั้นถ้าเป็นปัญหา UI)
- Create: `docs/screenshots/lab04-ui-before.png`, `docs/screenshots/lab04-ui-after.png`
- Create: `docs/superpowers/impeccable-lab04.md`

**Interfaces:**
- Consumes: หน้า `/?analysis=spice` ที่รันจริงจาก Task 6
- Produces: รายงาน critique/audit สั้น + ภาพ before/after + diff ที่ไม่แตะสูตร/ข้อมูลกราฟ

- [ ] **Step 1: โหลด skill `impeccable` แล้ว critique หน้าที่รันอยู่**

Run: ใช้ skill tool โหลด `impeccable` จากนั้นขอ critique ที่ `http://127.0.0.1:5000/?analysis=spice`
Expected: ได้รายการปัญหาเรื่อง input group, readability, error state, responsive, provenance

- [ ] **Step 2: เก็บ before screenshot**

ใช้ OpenCode Browser viewport 1280px และ 390px บันทึกเป็น `lab04-ui-before.png`
(ถ้า Playwright MCP มองไม่เห็นให้บันทึก `NOT RUN` ในรายงาน แล้วใช้ OpenCode Browser แทน)

- [ ] **Step 3: polish เฉพาะ CSS ตามลำดับความสำคัญที่ critique ชี้**

ห้ามแก้ `app.py`, `spice_engine.py`, series/data, หรือแทนที่กราฟด้วยภาพนิ่ง

- [ ] **Step 4: เก็บ after screenshot + audit + regression**

Run: `py -m unittest discover -v`
Expected: PASS; ภาพ after มีอยู่จริง; diff มีเฉพาะ UI files

- [ ] **Step 5: commit**

```bash
git add static/style.css docs/screenshots/lab04-ui-*.png docs/superpowers/impeccable-lab04.md
git commit -m "style: apply Impeccable polish with before/after evidence"
```

---

### Task 8: Browser acceptance B1–B8, docs และ publish

**Files:**
- Modify: `docs/validation.md`
- Modify: `README.md`
- Create: `docs/screenshots/lab04-B*.png` ตามที่ใช้จริง

**Interfaces:**
- Consumes: ทุก task ก่อนหน้า
- Produces: ตาราง B1–B8 ที่มี Method/Input/Expected/Observed/Evidence/Status,
  README ที่รันซ้ำได้, commit SHA ใหม่บน GitHub

- [ ] **Step 1: ตรวจ Playwright MCP visibility**

ถ้า tool ไม่ปรากฏ → บันทึก `NOT RUN` พร้อมเหตุผล แล้วใช้ OpenCode Browser ตาม handout
ห้ามอ้างว่าเป็น Playwright MCP

- [ ] **Step 2: run B1–B8 จริง และ record ค่าที่อ่านได้**

ต้องมี B3 (เปลี่ยน RE), B6 (เปลี่ยน amplitude) แสดงผลต่างก่อน/หลัง
B7 ต้องเห็น error จริง; B8 ต้องมีภาพ 1280px + 390px

- [ ] **Step 3: เขียน `docs/validation.md` และอัปเดต `README.md`**

ระบุ ngspice 47, model จาก Starter Kit, วิธี set PATH portable, วิธีรัน server,
ข้อจำกัด/ความคลาดเคลื่อนระหว่าง Analytical กับ SPICE

- [ ] **Step 4: final verification**

Run: `py -m unittest discover -v`, `git status --short`, `git log -1 --oneline`
Expected: tests PASS, ไม่มีไฟล์ run ชั่วคราวค้าง, commit ใหม่พร้อม push

- [ ] **Step 5: commit + push**

```bash
git add docs/validation.md README.md docs/screenshots/
git commit -m "docs: Lab 04 validation B1-B8 and reproducible setup"
git push origin HEAD
```
