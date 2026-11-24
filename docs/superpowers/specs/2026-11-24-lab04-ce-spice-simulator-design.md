# Design — Lab 04: BJT CE Amplifier Simulator v1 (ngspice)

## Intent
ต่อยอด Flask app จาก Lab 3 (repo เดิม `transistor-simulator`) เป็น simulator วงจร
Common-Emitter Voltage Divider **อ้างอิงหนึ่งวงจร** ที่รันจริงด้วย ngspice
ครบ 3 การวิเคราะห์ `.op` / `.ac` / `.tran` โดยResults/กราฟต้องมาจาก output จริง
และต้องไม่ทำให้ DC Bias 3 โหมดเดิมเสีย

## Goals
- คง `dc_bias.py`, `/calculate`, validation และ 24 tests เดิมแบบไม่เปลี่ยนผล
- เพิ่ม `spice_engine.py`: adapter สร้าง netlist → เรียก ngspice → parse ผล → คืนโครงสร้างพร้อมหน่วย
- เพิ่ม route ใหม่ `/simulate` สำหรับ SPICE แยกจาก `/calculate` (ไม่กระทบ regression)
- UI มี Analysis Mode (Analytical / SPICE: DC / AC / Transient), ฟอร์มมีหน่วยชัด,
  engine status (Running/Success/Error), provenance (`ngspice` vs `dc_bias.py`)
- กราฟ AC (Frequency–Gain dB/Phase) และ Transient (Time–Vin/Vout) วาดจากข้อมูลรันจริง
  มีแกน/หน่วย/legend ไม่ใช่ภาพ hard-code
- แยกป้าย Analytical Reference กับ SPICE Result ให้ชัด (ไม่บังคับตัวเลขตรงทุกหลัก)
- ใช้ Impeccable critique/polish เฉพาะ UI + บันทึก before/after
- ตรวจ B1–B8, บันทึก `docs/validation.md`, อัปเดต README, commit + push

## Non-goals / Anti-goals
- ไม่สร้างโปรเจกต์ใหม่, ไม่แทนที่ `dc_bias.py`, ไม่ย้ายสมการไป HTML/JS
- ไม่ทำ AC ทุก bias mode, FET, drag-and-drop editor, ต่อวงจรอิสระ, SPICE solver เอง
- ไม่ทำ emitter bypass capacitor ใน baseline, ไม่ทำ animated overlay, ไม่ deploy ภายนอก
- ห้าม hard-code gain/cutoff/waveform หรือโชว์กราฟเก่าพร้อมสถานะ Success
- ถ้า `-3 dB` ไม่มีในช่วง sweep ให้เขียน `not determined in sweep range`
- ไม่รวม `.venv/`, token, ไฟล์ run ชั่วคราวขนาดใหญ่ลง git

## Constraints / สภาพแวดล้อมที่ตรวจแล้ว
- Python 3.14.2, repo สะอาดที่ commit `64a34e0`
- ngspice **47** (portable) ใช้ได้ที่
  `C:\Users\B6829681\AppData\Local\Temp\opencode\ngspice-47\Spice64\bin\ngspice_con.exe`
- Node **26.13.1** + npm 11.20.0 (portable) ใช้ได้ที่
  `C:\Users\B6829681\AppData\Local\Temp\opencode\node-portable\node-v26.13.1-win-x64`
- Impeccable ติดตั้ง project scope แล้ว อยู่ใน `.opencode/` (ยังไม่ commit)
- Playwright MCP ยังต้องตรวจ visibility ตอนทดสอบ; ถ้า OpenCode มองไม่เห็นให้บันทึก
  `NOT RUN` พร้อมเหตุผล แล้วใช้ OpenCode Browser แทนตามที่ handout อนุญาต
- **Starter Kit จากอาจารย์ยังไม่ปรากฏใน repo** — ต้องอ่าน netlist/BJT model/adapter
  ก่อนเขียนโค้ดจริง ห้ามเดาค่า model เอง

## Approaches
1. **ต่อยอด repo เดิม + route ใหม่ (เลือก)** — แยก `/calculate` (Lab 3) กับ `/simulate`
   (Lab 4) ทำให้ regression ชัด เสี่ยงต่ำสุด
2. รวม `/calculate` กับ SPICE route เดียว — แก้โค้ดเดิมมากกว่า เสี่ยงทำให้ 24 tests เสีย
3. สร้างแอปใหม่ — ผิดข้อ “ยึด Project เดิม ไม่สร้างใหม่”

## การออกแบบ (calls ที่ตัดสินแล้ว)
- `app.py`
  - คง `CIRCUITS`, `FIELD_DEFS`, `_fields_for()`, `/calculate` เดิมทุกบรรทัดที่เกี่ยวกับผล
  - เพิ่ม `ANALYSES = {"analytical": ..., "dc": ..., "ac": ..., "tran": ...}`
  - `/simulate` รับฟิลด์ SPICE (R1,R2,RC,RE,RL,Cin,Cout,amplitude,frequency,model)
    validate เป็นตัวเลข/ช่วงบวก/ความถี่ > 0 ก่อนส่งเข้า adapter
  - error ทุกกรณีคืนหน้าแบบไม่มี `rows`/`plot` → ไม่โชว์ผลเก่า
- `spice_engine.py`
  - `find_ngspice()` ตรวจจาก `NGSPICE_EXE` หรือ PATH; ถ้าไม่เจอ → error ชัด
  - `run(mode, values, starter)` ใช้ `tempfile.TemporaryDirectory()` ต่อรอบ
    เรียก `subprocess.run([exe, "-b", "-o", log, "-r", raw, cir], timeout=..., cwd=run_dir,
    capture_output=True, text=True)` — **ไม่ใช้ `shell=True`**
  - ตรวจ `returncode`, log ว่าง/มี error, timeout, parse fail → raise `SpiceError`
  - คืน dict: `status`, `mode`, `model`, `ngspice_version`, `units`,
    `scalars` (.op) หรือ `series` (.ac/.tran), `log_excerpt`, `provenance="ngspice"`
  - netlist มาจาก Starter Kit ที่จะอ่านก่อน; ถ้า Starter ไม่มีฟิลด์ที่ต้องการ → หยุดและรายงาน
- ผล/หน่วย
  - `.op`: VB, VE, VC (V), VCE (V), IC (mA), IB (µA) อ่านจาก output จริง
  - `.ac`: frequency (Hz), `|Vout/Vin|` (dB), phase (degree) อ้าง Vin ที่จุดเดียวกันชัดเจน
  - `.tran`: time (s หรือ ms), Vin/Vout (V) พร้อม amplitude/frequency ที่ใช้รัน
- `templates/index.html` + `static/style.css`
  - เพิ่ม selector Analysis Mode, ฟอร์ม SPICE แยกกลุ่ม, status badge, provenance badge
  - กราฟเป็น SVG ที่ server ส่ง series มาให้ (ไม่เพิ่ม dependency ถ้าไม่จำเป็น)
  - Impeccable ใช้ critique/polish เฉพาะไฟล์ UI หลัง verdict ผ่านแล้ว
- `docs/validation.md`: ตาราง B1–B8 พร้อม Method/Input/Expected/Observed/Evidence/Status,
  ระบุ ngspice version + BJT model จริง
- `README.md`: วิธี set PATH ของ ngspice/Node แบบ portable, รัน server, ทดสอบซ้ำ

## สิ่งที่เหลือให้ builder
1. อ่าน Starter Kit ที่คุณจะวางใน repo → แก้ design นี้ถ้า netlist/model ต่างจากสมมติฐาน
2. ขอ approve อีกครั้งถ้ามีการเปลี่ยนโครงสร้างสำคัญ
3. Invoke `writing-plans` แยก task แบบ TDD แล้ว execute → verify → Impeccable → browser → commit
