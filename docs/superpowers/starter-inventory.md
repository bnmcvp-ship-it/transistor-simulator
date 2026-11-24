# Starter Inventory — Lab 04 CE Voltage Divider

## ที่มา / การตัดสินใจ
ไม่มี Starter Kit จากอาจารย์ในเครื่องตอนเริ่ม Task 1 จึงสร้าง Starter ขึ้นเองภายใต้ `starter/`
โดย **ไม่เดาค่าทรานซิสเตอร์**: ใช้ BC547B model ที่แนบมากับ ngspice 47 อย่างเป็นทางการ
(`Spice64/examples/tclspice/tcl-testbench3/FB14.cir` block `models/BC547B.spi`)
คัดลอกพารามิเตอร์มาใส่ `starter/bc547b.mod` แบบตรงตัว และระบุแหล่งที่มาในไฟล์/ในผลลัพธ์ทุกครั้ง

Ruling: การใช้ model จาก ngspice official example แทน Starter ของอาจารย์ — ทำเพราะผู้ใช้ขอให้ทำให้เอง
และ handout ห้ามเดาค่าเฉพาะรุ่น การอ้างแหล่งที่มาตรงตัวทำให้รันซ้ำได้
_cost_: ตัวเลขอาจต่างจาก model ที่อาจารย์เตรียมไว้ ต้องระบุชื่อ model ใน `docs/validation.md` ให้ชัด

## ไฟล์
- `starter/manifest.json` — node map, analysis directives, netlist template
- `starter/bc547b.mod` — BJT model card (source ด้านบน)
- `spice_engine.py` — adapter (`SpiceError`, `find_ngspice`, `load_starter`, `parse_op_log`, `run`)

## โหนดที่ใช้วัด
| สัญลักษณ์ | node ใน netlist | ความหมาย |
|---|---|---|
| Vin | `VIN` | ขาเข้าก่อน `CIN` (แหล่งสัญญาณ) — ใช้เป็น reference ของ Gain/Phase เสมอ |
| VB | `VB` | เบส หลังตัว divider |
| VE | `VE` | อิมิตเตอร์ |
| VC | `VC` | คอลเลกเตอร์ |
| Vout | `VOUT` | หลัง `COUT` บน `RL` |

## โครงวงจรและค่าตั้งต้น
`VCC=12 V`, `R1=100 kΩ`, `R2=22 kΩ`, `RC=2.2 kΩ`, `RE=1 kΩ`,
`RL=10 kΩ`, `CIN=COUT=10 µF`, source `10 mV peak @ 1 kHz`
DC: coupling capacitors เปิดวงจร automatically → ไม่มี DC ผ่าน `RL`
IC อ่านจาก `i(rc)` / BJT device section; VCE = VC − VE

## Analysis directives
- DC: `.op` (อ่าน node voltage table + BJT device currents จาก log)
  หมายเหตุ: `.print dc` ใช้กับ `.op` ไม่ได้ (ngspice report Error) จึงไม่ใส่บรรทัดนี้ใน deck DC
- AC: `.ac dec 20 1 10Meg` → พิมพ์ `vdb(vin) vdb(vout) vp(vin) vp(vout)`
- Transient: `.tran 5u 5m 0 1u` → พิมพ์ `v(vin) v(vout)`

## ข้อควรระวังที่เจอระหว่าง smoke test
1. บรรทัดแรกของ netlist ต้องเป็น comment (`* ...`) เพราะ SPICE ถือเป็น title
   ถ้าใส่ `VCC ...` ไว้บรรทัดแรก ngspice จะไม่สร้างแหล่งจ่าย → ทุก node เป็น 0
2. version string `ngspice-47` อยู่ใน **stdout ของ process** ไม่ใช่ไฟล์ `-o`
   ต้องอ่านจาก `completed.stdout + log_text`

## ผล smoke จริง (RE=1 kΩ)
`VB ≈ 2.0814 V`, `VE ≈ 1.4356 V`, `VC ≈ 8.8518 V`, `IC ≈ 1.4310 mA` — มาจาก ngspice log จริง
