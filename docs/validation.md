# Validation — Lab 03: หนึ่งเว็บ สามวงจรไบอัส

ตรวจ **DC Operating Point** ผ่าน browser จริง เทียบกับค่าที่คำนวณด้วยมือ
(อิสระจากโค้ด) ภายใต้แบบจำลอง Forward-Active Approximation เดียวกัน

## เครื่องมือที่ใช้ตรวจ

| เครื่องมือ | สถานะ | หมายเหตุ |
|---|---|---|
| Playwright MCP (`browser_navigate`, `browser_snapshot`, `browser_fill_form`, `browser_click`) | **NOT RUN** | ไม่มี `node` / `npx` ในเครื่อง จึงไม่สามารถตั้ง MCP server ได้ |
| **OpenCode Browser** (tool ของ OpenCode desktop: `tabs.open`, `snapshot`, `fill_form`, `click`, `wait`, `screenshot`) | **PASS** | ใช้ตามข้อยกเว้นที่ handout อนุญาตเมื่อ Playwright MCP ไม่พร้อม — เกณฑ์การตรวจผลเท่ากัน (เปิดหน้าเว็บจริง กรอกฟอร์มจริง อ่าน snapshot หลังส่งจริง) |

> หมายเหตุบทบาท MCP: MCP คือ "สะพาน" ให้ AI เรียกเครื่องมือ browser จากภายนอก
> (เช่น Playwright) — ไม่ได้เป็นตัวคำนวณหรือตรวจผลเอง ผลที่ตัดสินจึงมาจาก
> snapshot ของหน้าเว็บที่ส่งฟอร์มจริง แล้วเทียบกับค่าคำนวณมือด้านล่าง

## ค่าคาดหมายอิสระ (คำนวณมือก่อนรัน)

อินพุตร่วมทุกกรณี: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V

- **Divider** (R1=100 kΩ, R2=22 kΩ, RE=1 kΩ): VTH=2.1639 V, RTH=18.033 kΩ,
  IB=12.2986 µA → **IC=1.2299 mA**, VE=1.2422 V, **VCE=8.0522 V**
- **Fixed** (RB=1000 kΩ): IB=(12−0.7)/1M=**11.3000 µA**, IC=**1.1300 mA**,
  VE=**0 V**, VC=12−1.130m×2.2k=**9.5140 V**, VCE=9.5140 V
- **Emitter** (RB=1000 kΩ, RE=1 kΩ): IB=11.3/(1M+101×1k)=10.2634 µA,
  IC=**1.0263 mA**, IE=1.0366 mA, VE=**1.0366 V**, VC=9.7421 V,
  VCE=**8.7055 V**
- **Emitter** (RB=1000 kΩ, RE=2 kΩ): IB=11.3/(1M+101×2k)=9.4010 µA,
  IC=**0.9401 mA** (ลดจาก RE=1 kΩ เพราะตัวหารเพิ่ม), VE=1.8990 V,
  VCE=**8.0328 V** — **IC ต้องลดลง**เมื่อ RE เพิ่ม
- **Fixed** (RB=0): ตัวหาร RB=0 → ต้อง error ทันที "RB ต้องมากกว่า 0"

**เกณฑ์ tolerance:** |IC ที่เห็น − ค่ามือ| ≤ 0.01 mA, |VCE ที่เห็น − ค่ามือ| ≤ 0.02 V
(หน้าเว็บแสดง 2 ทศนิยม จึงเทียบผลที่แสดงจริง ไม่ใช่ค่าดิบในโค้ด)

## ผลตรวจ A1–A5 (ผ่าน OpenCode Browser จริง)

| รายการ | โหมด / อินพุตที่ส่ง | ค่าคาดหมาย (คำนวณมือ) | ผลที่เห็นจาก snapshot จริง | วิธีตรวจ | Status |
|---|---|---|---|---|---|
| **A1** Divider เดิมยังให้ผลเดิม | `Voltage-Divider Bias` — VCC=12, R1=100, R2=22, RC=2.2, RE=1, β=100, VBE=0.7 | IC=1.2299 mA, VCE=8.0522 V | `IC = 1.23 mA`, `VCE = 8.05 V`, heading `Voltage-Divider Bias — DC Bias Results`, region Forward-Active | `snapshot` หลังกด Calculate (POST /calculate) | **PASS** (ΔIC=0.0001 mA, ΔVCE=0.0022 V) |
| **A2** Fixed Bias | คลิก link `Fixed Bias` → ฟอร์มเหลือ 5 ช่อง (ไม่มี R1/R2) → RB=1000 | IB=11.30 µA, IC=1.1300 mA, VE=0 V, VCE=9.5140 V | `IB = 11.30 µA`, `IC = 1.13 mA`, `VE = 0.00 V`, `VCE = 9.51 V`, heading `Fixed Bias — DC Bias Results` | `snapshot` หลัง `fill_form` + `click` | **PASS** (ΔIC=0.0000 mA, ΔVCE=0.0040 V) |
| **A3** Emitter Bias | คลิก link `Emitter Bias` → มีช่อง RB และ RE → RB=1000, RE=1 | IC=1.0263 mA, VE=1.0366 V, VCE=8.7055 V | `IC = 1.03 mA`, `VE = 1.04 V`, `VCE = 8.71 V`, heading `Emitter Bias — DC Bias Results` | `snapshot` หลัง `fill_form` + `click` | **PASS** (ΔIC=0.0037 mA, ΔVCE=0.0045 V) |
| **A4** RE เพิ่ม → IC ลด | เฉพาะ RE: 1 → 2 kΩ (ค่าอื่นคงเดิม) | IC=0.9401 mA **< A3**, VCE=8.0328 V | `IC = 0.94 mA` (< 1.03 mA ใน A3), `VCE = 8.03 V`, `IB = 9.40 µA` | `snapshot` หลัง `fill` เฉพาะ RE + `click`; ตรวจค่า input ใน DOM ด้วย `evaluate` ว่า `re=2` | **PASS** (ΔIC=0.0001 mA, ΔVCE=0.0028 V) |
| **A5** Fixed RB=0 → error | โหมด `Fixed Bias`, RB=0 พร้อม VCC/RC/β/VBE ครบ | error ต้องระบุ RB และต้องไม่โชว์ผลรอบก่อน | `[Fixed Bias] RB ต้องมากกว่า 0 (หน่วย kΩ)` — ไม่มี `DC Bias Results` ปรากฏใน snapshot | `snapshot` หลัง `fill_form` + `click` (HTTP 200 หน้าไม่ล้ม) | **PASS** |

### หมายเหตุการอ่านผล A4

ครั้งแรกที่อ่านหลังกด Calculate ได้ค่าของ A3 (1.03 mA) เพราะคำว่า
"DC Bias Results" ยังอยู่ในหน้าจากรอบก่อนทำให้ `wait` กลับมาก่อน POST เสร็จ
— แก้โดยรอข้อความ **`0.94`** ซึ่งเป็นค่าของรอบใหม่แทน แล้วอ่าน snapshot อีกครั้ง
ได้ผลตามตาราง นี่คือหลักฐานว่าอ่านผล "รอบที่เพิ่งส่ง" จริง ไม่ใช่ผลค้าง

### ที่มาของ error ใน A5

ข้อความมาจาก **ฝั่ง Flask** (`BiasError` ใน `dc_bias.py` → route `/calculate`
จับแล้วส่งกลับ template) ไม่ใช่ native validation ของ browser: ฟอร์มส่ง POST สำเร็จ
(URL เปลี่ยนเป็น `/calculate`) แล้วหน้าแสดง `[Fixed Bias] ...` ซึ่งเป็น prefix
ที่ template ใส่ให้ตามโหมด — การที่ browser ไม่บล็อกการส่งจึงพิสูจน์ว่า Flask
เป็นฝ่ายตรวจค่าเอง ตรงตามข้อกำหนดของ handout

## หลักฐานภาพหน้าจอ (ก่อนใส่ค่า / หลังใส่ค่า)

แคปคู่ภาพทุกกรณีตามภาพ `before` / `after` ใน handout — `before` คือฟอร์มที่
เคลียร์ช่อง input ให้ว่างก่อนกรอก, `after` คือหน้าหลังกรอกค่าครบแล้วกด Calculate
(HTTP POST จริง) เก็บใน `docs/screenshots/`:

| กรณี | ก่อนใส่ค่า | หลังใส่ค่า |
|---|---|---|
| A1 Divider | `lab03-A1-before.png` | `lab03-A1-after.png` (IC=1.23 mA, VCE=8.05 V) |
| A2 Fixed | `lab03-A2-before.png` | `lab03-A2-after.png` (IC=1.13 mA, VCE=9.51 V) |
| A3 Emitter RE=1k | `lab03-A3-before.png` | `lab03-A3-after.png` (IC=1.03 mA, VCE=8.71 V) |
| A4 Emitter RE=2k | `lab03-A4-before.png` | `lab03-A4-after.png` (IC=0.94 mA, VCE=8.03 V) |
| A5 Fixed RB=0 | `lab03-A5-before.png` | `lab03-A5-after.png` (`[Fixed Bias] RB ต้องมากกว่า 0`, ไม่มีตารางผล) |

## Automated Tests

`py -m unittest discover -s tests -v` → **24 tests OK** (ดู `docs/test-log.txt`)

- 18 tests ใน `tests/test_dc_bias.py` — สมการ Divider เดิม + Fixed/Emitter ใหม่,
  validation, warning region
- 6 tests ใน `tests/test_web.py` — GET ฟอร์มตามโหมด, POST Fixed/Emitter,
  unknown circuit → error, RB=0 → ไม่มี stale result
- 4 tests เดิมของ Lab 02 ยังผ่านทุกตัว (Divider ไม่เปลี่ยนผล)

---

# Validation — Lab 04: CE Voltage Divider SPICE Simulator

รัน `ngspice-47` **จริง** ผ่าน `subprocess.run([...])` (ไม่ `shell=True`, มี `timeout`,
แยก `TemporaryDirectory` ต่อรอบ) แล้วอ่านผลจาก log ที่ simulator พิมพ์ออกมา
ไม่มี gain/cutoff/waveform ใดถูก hard-code

## เครื่องมือที่ใช้ตรวจ Lab 04

| เครื่องมือ | สถานะ | หมายเหตุ |
|---|---|---|
| Playwright MCP | **NOT RUN** | ไม่มี MCP server ใน session นี้ — บันทึกตาม handout ห้ามอ้างว่าใช้ MCP |
| Impeccable skill | **NOT RUN** | `Unable to load skill impeccable` — ใช้ manual critique แทน (ดู `docs/superpowers/impeccable-lab04.md`) |
| **OpenCode Browser** | **PASS** | ใช้ตรวจ B1–B7 จริง: `tabs.open`, `find`, `fill`, `select`, `click`, `wait`, `evaluate`, `snapshot`, `screenshot` |
| Playwright CLI (`npx playwright`) | **PASS (เสริม)** | ใช้เฉพาะจับภาพ B8 ที่ viewport 1280px/390px จริง เพราะ OpenCode Browser ไม่มี tool ปรับ viewport (CLI ≠ MCP) |

## ผลรันจริงที่ใช้เป็นEvidence

- **Engine:** `ngspice-47` (จาก `completed.stdout + log`), model `QBC547B` จาก
  `starter/bc547b.mod` (copy จาก ngspice 47 official example — ดู
  `docs/superpowers/starter-inventory.md`)
- **DC (RE=1 kΩ):** VB=2.081 V, VE=1.436 V, VC=8.852 V, VCE=7.416 V,
  IC=1.431 mA, IB=4.57 µA
- **AC ตารางจริง 141 จุด (1 Hz–10 MHz):** gain สูงสุด ≈ 4.92 dB (RE=1 kΩ),
  f_L=1.584893 Hz, f_H=`not determined in sweep range` (ที่ 10 MHz gain ยัง ~4.86 dB
  จึงไม่แต่งตัวเลข)
- **Transient 5006 จุด @ 10 mV, 1 kHz:** Vin peak=0.0100 V, Vout peak=0.0088 V,
  covariance ของ polyline Vin/Vout = −3412.5 → สัญญาณกลับเฟสตาม CE

## ตาราง B1–B8 (Method / Input / Expected / Observed / Evidence / Status)

| รายการ | Method | Input | Expected | Observed จริง | Evidence | Status |
|---|---|---|---|---|---|---|
| **B1 Regression** | OpenCode Browser — เปิด `/?analysis=analytical&circuit=...` แล้วกด Calculate | ชุดอ้างอิง Lab 03 ทั้ง 3 โหมด | ผลเดิมตรง 8.05/1.23, 9.51/1.13, 8.71/1.03 | Divider `VCE 8.05 V, IC 1.23 mA`; Fixed `9.51 V, 1.13 mA`; Emitter `8.71 V, 1.03 mA` | snapshot หลัง POST `/calculate` | **PASS** |
| **B2 DC SPICE** | เลือก `analysis=spice`, `spice_mode=dc`, กด Run ngspice | VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, RL=10k, CIN=COUT=10µF | VB/VE/VC/VCE/IC จาก ngspice + model + status | `Success — DC Operating Point (.op)`, `Source: ngspice-47 · model: QBC547B`, VB 2.081, VE 1.436, VC 8.852, VCE 7.416 V, IC 1.431 mA | snapshot หลัง POST `/simulate` | **PASS** |
| **B3 Change RE** | แก้เฉพาะ RE แล้ว Run ซ้ำ | RE 1 kΩ → 2 kΩ | Operating point/Gain เปลี่ยน ไม่ใช่ค่าค้าง | IC `1.431 → 0.745 mA`, VB `2.081 → 2.122 V`, VC `8.852 → 10.361 V` | evaluate ข้อความตารางรอบใหม่ | **PASS** |
| **B4 AC** |เลือก `ac` แล้ว Run | ค่าเดิม (RE=2 kΩ จาก B3) | Frequency axis/Gain/Phase พร้อมหน่วย ไม่ hard-code | `Gain สูงสุด −0.93 dB`, `f_L 1.778 Hz`, `f_H not determined in sweep range`, `Phase 2.67°`; 2 `<svg.plot>` 2 `<polyline>` แกน `Frequency (Hz)`, `Gain (dB)`, `Phase (°)` | evaluate DOM + snapshot | **PASS** |
| **B5 Transient** |เลือก `tran` แล้ว Run | amplitude 0.010 V peak, 1 kHz | Vin/Vout ตามเวลา + ป้ายหน่วย + กลับเฟส | 5006 จุดต่อสัญญาณ, `Vin peak 0.0100 V`, `Vout peak 0.0088 V`, covariance −3412.5 → inverted | evaluate polyline + snapshot | **PASS** |
| **B6 Change Source** | แก้เฉพาะ amplitude แล้ว Run ซ้ำ | 0.010 → 0.020 V peak | waveform เปลี่ยนตามจริง | `Vin peak 0.0200 V`, `Vout peak 0.0088 → 0.0177 V` (~2×) | evaluate ตารางรอบใหม่ | **PASS** |
| **B7 Invalid/Fail** | ใส่ RE=0 แล้ว Run | RE=0 พร้อมค่าอื่นครบ | error ชัด ไม่ค้าง ไม่มี Success ปลอม | `[SPICE] RE ต้องมากกว่า 0`, `Success=false`, `svg.plot=0` | evaluate DOM + snapshot | **PASS** |
| **B8 UI** | Playwright CLI จับ viewport จริง 1280×900 / 390×844 | หน้า `/?analysis=spice` หลัง Run AC | กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่ตัดเนื้อหา | desktop `scrollW=1280, clientW=1280, media390=false`; mobile `scrollW=390, clientW=390, media390=true`, svg=2 ทั้งสอง | `lab04-B8-desktop.png`, `lab04-B8-mobile.png` | **PASS** |

## ความคลาดเคลื่อน Analytical vs SPICE (ต้องอ่าน)

- `dc_bias.py` ใช้ **Forward-Active Approximation** β=100, VBE=0.70 V คงที่ →
  Divider RE=1 kΩ ได้ IC≈1.23 mA
- ngspice ใช้ **BC547B Gummel-Poon** (BF=294.3, VBE แปรตามกระแส) → IC≈1.431 mA
- ผลต่าง ~16% **ไม่ใช่ bug** — คนละ model คนละสมมติฐาน หน้าเว็บแยกป้าย
  `Analytical: dc_bias.py` กับ `Source: ngspice-47 · model: QBC547B` เสมอ
- `f_H` อยู่นอก sweep 10 MHz จึงแสดงข้อความว่าไม่พบในช่วงที่รัน ห้ามตีความเป็น 0

## Automated Tests (Lab 04)

`py -m unittest discover -v` → **43 tests OK** (24 เดิมจาก Lab 02/03 + 19 ใหม่จาก Lab 04)

- `test_dc_bias.py` (14) + `test_web.py` (10) — สมการ/validation 3 โหมด + route เดิม
- `test_spice_smoke.py` (1), `test_spice_validation.py` (2), `test_spice_dc.py` (3),
  `test_spice_series.py` (4) — engine จริง 10 กรณี
- `test_simulate_route.py` (5), `test_ui_lab04.py` (4) — route/test client + UI 9 กรณี

## ภาพ Lab 04

| จุดประสงค์ | ไฟล์ |
|---|---|
| before/after (Impeccable) | `lab04-ui-before.png`, `lab04-ui-after.png` |
| B8 desktop 1280px | `lab04-B8-desktop.png` |
| B8 mobile 390px | `lab04-B8-mobile.png` |
