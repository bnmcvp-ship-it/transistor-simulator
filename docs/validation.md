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

## หลักฐานภาพหน้าจอ

- `docs/screenshots/lab03-a4-emitter.png` — หน้าผล Emitter Bias กรณี RE=2 kΩ (IC=0.94 mA, VCE=8.03 V)
- `docs/screenshots/lab03-a5-error.png` — หน้า error Fixed Bias RB=0 (ไม่มีตารางผล)

## Automated Tests

`py -m unittest discover -s tests -v` → **24 tests OK** (ดู `docs/test-log.txt`)

- 18 tests ใน `tests/test_dc_bias.py` — สมการ Divider เดิม + Fixed/Emitter ใหม่,
  validation, warning region
- 6 tests ใน `tests/test_web.py` — GET ฟอร์มตามโหมด, POST Fixed/Emitter,
  unknown circuit → error, RB=0 → ไม่มี stale result
- 4 tests เดิมของ Lab 02 ยังผ่านทุกตัว (Divider ไม่เปลี่ยนผล)
