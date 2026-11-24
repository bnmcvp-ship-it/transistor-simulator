# ENG29 2121 — Lab 02 → Lab 04: BJT CE Amplifier (Analytical + SPICE)

เว็บแอป Flask เดียว มี **2 แหล่งผลลัพธ์ที่แยกป้ายชัดเจน**:

| แถบ | แหล่งผล | สิ่งที่คำนวณ |
|---|---|---|
| `Analytical: dc_bias.py` | สมการวิศวกรรม in-house | DC Bias 3 โหมด (Voltage-Divider / Fixed / Emitter) |
| `SPICE: ngspice` | `ngspice-47` รันจริงผ่าน `subprocess.run([...])` | `.op`, `.ac`, `.tran` ของวงจร Voltage Divider |

ผล/กราฟทั้งหมดมาจากการรันจริง (ไม่มี gain/cutoff/waveform hard-code ใน HTML)
และแยก provenance ทุกครั้ง: `Source: ngspice-47 · model: QBC547B · provenance: ngspice`

## การติดตั้งและรัน

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

ต้องมี ngspice (ทดสอบกับ **ngspice 47**) สองทางเลือก:

```powershell
# A) ติดตั้งแล้วอยู่ใน PATH — ไม่ต้องตั้งอะไรเพิ่ม
ngspice -v

# B) portable / อยู่ที่อื่น — ชี้ NGSPICE_EXE ไปตัว executable
$env:NGSPICE_EXE = "C:\Users\<user>\AppData\Local\Temp\opencode\ngspice-47\Spice64\bin\ngspice_con.exe"
```

จากนั้นรัน server แล้วเปิด `http://127.0.0.1:5001/`:

```powershell
py -m flask --app app run --port 5001 --no-debug
```

หน้า `/?analysis=analytical` = ฟอร์ม Lab 03 เดิม, `/?analysis=spice` = ฟอร์มจำลอง
ลิงก์ในแถบด้านบนโหลดฟอร์มใหม่โดยไม่ใช้ JavaScript

## ฝั่ง Analytical (`dc_bias.py` — ไม่แตะ SPICE)

| โหมด (`circuit`) | ช่องที่ใช้ | สมการหลัก |
|---|---|---|
| `divider` (default) | VCC, R1, R2, RC, RE, β, VBE | VTH=VCC·R2/(R1+R2), RTH=R1∥R2, IB=(VTH−VBE)/(RTH+(β+1)RE) |
| `fixed` | VCC, RB, RC, β, VBE | IB=(VCC−VBE)/RB |
| `emitter` | VCC, RB, RC, RE, β, VBE | IB=(VCC−VBE)/(RB+(β+1)RE) |

IC=β·IB, IE=(β+1)IB, VE=IE·RE (Fixed: VE=0), VB=VE+VBE,
VC=VCC−IC·RC, VCE=VC−VE — สมการอยู่ใน `dc_bias.py` เท่านั้น

อินพุตเป็น **kΩ** แล้วแปลงใน route; RB=0 → `[Fixed Bias] RB ต้องมากกว่า 0`
หน้าไม่ล้มและไม่โชว์ผลรอบก่อน

## ฝั่ง SPICE (`spice_engine.py` + `app.py`)

เลือก **Analysis** ในฟอร์ม:

| `spice_mode` | การรันจริง | ผลที่แสดง |
|---|---|---|
| `dc` | `.op` | VB, VE, VC, VCE, IC, IB + status + model/engine |
| `ac` | `.ac dec 141 1 10Meg` | Gain สูงสุด, f_L/f_H ที่ −3 dB, phase, กราฟ Gain/Phase vs **Frequency [Hz]** (แกนวาด log10) |
| `tran` | `.tran` ที่ความถี่ Vin | Vin/Vout peak, กราฟสัญญาณ vs **Time [s]** |

หน่วยในฟอร์ม: VCC/Vin = **V**, R*/RL = **kΩ**, CIN/COUT = **µF** → แปลงเป็น SI
ก่อนเขียน netlist (R×1e3, C×1e−6) ห้ามส่งค่าดิบจากฟอร์มลง netlist

รายละเอียดการรัน: `subprocess.run([...], timeout=...)` ไม่ใช้ `shell=True`,
แยก `TemporaryDirectory` ต่อรอบ, อ่าน version จาก `stdout + log`,
model มาจาก `starter/bc547b.mod` (copy จาก ngspice 47 official example —
ดู `docs/superpowers/starter-inventory.md`)

ข้อควรระวังเรื่องผล:

- `f_H` ที่ RE=1 kΩ อยู่นอก sweep 10 MHz → แสดง `not determined in sweep range`
  (ห้ามตีความเป็น 0 หรือแต่งตัวเลข)
- AC ตาราง `.print` ถูก ngspice แบ่งหน้า → parser รวมตาม `Index`
- กราฟ SVG วาดจาก polyline ของข้อมูลจริงเท่านั้น

## ความคลาดเคลื่อน Analytical vs SPICE (คนละแบบจำลอง)

`dc_bias.py` ใช้ **Forward-Active Approximation** (β=100, VBE=0.70 V คงที่)
→ Divider RE=1 kΩ ได้ IC≈1.23 mA
ngspice ใช้ **BC547B Gummel-Poon** (BF≈294, VBE แปรตามกระแส) → IC≈1.431 mA
ต่าง ~16% **ไม่ใช่ bug** — หน้าเว็บแยกป้ายทั้งสองเสมอ อย่านำค่าสองชุดมาเทียบ
ราวกับเป็น solver เดียวกัน

## การทดสอบ

```powershell
py -m unittest discover -v
```

**43 tests OK** (24 เดิม Lab 02/03 + 19 ใหม่ Lab 04) — ครอบสมการ/validation,
route เดิม, engine จริง dc/ac/tran, `/simulate`, error ไม่โชว์ stale result,
และ UI มี status/provenance/กราฟ/rank ของหน่วย

ผลจริงและตารางรับมาตรฐาน B1–B8 อยู่ใน `docs/validation.md`
(before/after + ภาพ B8 1280px/390px อยู่ใน `docs/screenshots/`;
critique/polish/audit อยู่ใน `docs/superpowers/impeccable-lab04.md`)

เครื่องมือตรวจ: ใช้ **OpenCode Browser** เป็นหลัก เพราะไม่มี Playwright MCP ใน session
(บันทึก `NOT RUN`) ส่วน viewport 390px ใช้ Playwright CLI จับภาพ — CLI ไม่ใช่ MCP

## โครงสร้าง

```
├── app.py                  # Flask: /calculate (Lab 03) + /simulate (Lab 04)
├── dc_bias.py              # สมการ 3 โหมด — ไม่รู้จัก HTML/HTTP/SPICE
├── spice_engine.py         # build_netlist / run / parse op + series จาก ngspice จริง
├── starter/bc547b.mod      # BC547B model จาก ngspice 47 official example
├── templates/index.html    # ฟอร์ม 2 ชุด + status + provenance + แถบเลือก
├── templates/_plot.html    # SVG polyline จากข้อมูล ngspice จริง
├── static/style.css        # หน้าตา + Impeccable polish
├── tests/                  # 43 tests (unittest)
└── docs/                   # design/plan/spec, validation, screenshots, inventory
```

## ส่งงาน / GitHub

- **Repo (public):** https://github.com/bnmcvp-ship-it/transistor-simulator
- **Branch:** `lab04`
- **Lab 04 commits:**
  - `99944b5` — starter/model + smoke test
  - `c779ddd` — validation ของฟอร์ม SPICE
  - `c787896` — netlist + `.op` + parser จริง
  - `4c1c868` — parser `.ac`/`.tran`
  - `2939771` — route `/simulate` แยกจาก `/calculate`
  - `d8cc052` — ฟอร์ม/status/provenance/SVG
  - `72e3bce` — Impeccable polish + ภาพ before/after
- **ส่วนที่ AI ช่วยเขียน:** netlist/parser/route/template/test/docs ตาม plan ใน
  `docs/superpowers/plans/2026-11-24-lab04-ce-spice-simulator.md`; นักศึกษาตรวจอิสระ
  ด้วย browser จริงตาม `docs/validation.md` (B1–B8)
