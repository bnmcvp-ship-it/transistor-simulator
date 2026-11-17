# Design — Lab 03: หนึ่งเว็บ สามวงจรไบอัส

## Intent
ต่อยอด Flask app จาก Lab 2 (Voltage Divider Bias เดิม) ให้เลือกได้ 3 โหมด:
Fixed Bias, Emitter Bias (แหล่งจ่ายเดียว) และ Divider เดิม โดยค่าของ Divider
เมื่อกรอกอินพุตเดิมต้องไม่เปลี่ยน นักศึกษาตรวจสมการ หน่วย และผลหน้าเว็บเอง
ตามตาราง A1–A5 ใน handout

## Goals
- แยกฟังก์ชันคำนวณ Fixed/Emitter ใน `dc_bias.py` ส่ง `dict` ชื่อคีย์/หน่วยเดิม
- `app.py` เลือกฟังก์ชันด้วย `if/elif` ตามโหมด ตรวจเฉพาะช่องที่โหมดนั้นใช้
- ฟอร์มโหลดใหม่ตามโหมดที่เลือก (ไม่ต้อง JavaScript) แสดงเฉพาะช่องที่ใช้
  ผล/error ระบุโหมด และไม่โชว์ผลรอบก่อน
- ตรวจ A1–A5 ใน browser จริง บันทึกผล/หน่วย/วิธีตรวจ/status ลง `docs/validation.md`
- อัปเดต README, commit และ push GitHub (repo public เดิม)

## Non-goals / Anti-goals
- ไม่ทำ AC/Transient, SPICE, DC Load Line, bypass capacitor, unittest ใหม่ตาม handout
  (แต่ Superpowers TDD ยังใช้ได้ — เพิ่ม test เล็กน้อยสำหรับฟังก์ชัน/route ใหม่)
- ห้ามย้ายสมการไป HTML, ห้ามสร้างโปรเจกต์ใหม่ทับของเดิม
- ห้ามให้ Divider เปลี่ยนผล หรือให้โหมดที่ไม่รู้จักตกไปเป็น Divider

## Constraints
- แบบจำลอง DC Forward Active, β และ VBE คงที่; รับ kΩ แปลงเป็น Ω ครั้งเดียวตอนรับค่า
- อินพุตผิด (ว่าง/ไม่ใช่เลข/ไม่จำกัด/ค่าที่ต้องบวก ≤ 0) → error; อินพุตถูกแต่
  IB ≤ 0 หรือ VCE ≤ 0.2 V → warning ว่าแบบจำลองอาจใช้ไม่ได้ (ไม่ต้องหาค่าจริงใน cutoff/sat)
- 13 tests เดิมต้องยังผ่าน; ใช้ Python/Flask environment เดิม

## Approaches
1. **ต่อยอด repo เดิม (เลือก)** — ใช้ `dc_bias.py`, `app.py`, `templates/`, `tests/`
   เดิม เปลี่ยนน้อยสุด Divider ยังใช้โค้ดเดิม → เสี่ยงต่ำสุด ตรวจย้อนได้
2. สร้างโปรเจกต์ใหม่แยก Lab 3 — ตัดความต่อเนื่องและผิดข้อ "ใช้โค้ด Lab 2 เป็นจุดเริ่มต้น"
3. ใส่สมการใน template/JS — ผิดข้อห้ามและตรวจยาก

## ทางเลือกเครื่องมือตรวจ browser
- **ใช้ OpenCode Browser (เลือก)** — มีอยู่แล้ว ใช้งานได้; handout อนุญาต fallback
  เมื่อ Playwright MCP ไม่พร้อม ต้องบันทึก `NOT RUN` พร้อมเหตุผล (ไม่มี node/npx)
- ติดตั้ง Node + Playwright MCP — ตรงเส้นทางหลักของ handout แต่เพิ่มการติดตั้ง/รอ npm
  และคะแนนตรวจผลเท่ากัน จึงไม่คุ้มในคาบนี้

## การออกแบบ (calls ที่ตัดสินแล้ว)
- `dc_bias.py`: `analyze_fixed(vcc,rb,rc,beta,vbe)`, `analyze_emitter(vcc,rb,rc,re,beta,vbe)`
  คืนคีย์เดิม `vb,ve,vc,vce,ib,ic,ie,region,warnings`; `analyze()` เดิมไม่แตะสมการ
- หน่วย: resistor kΩ → Ω ในฟังก์ชัน; ผล V/A เก็บเป็น SI แล้วแปลงตอนแสดง (mA, µA)
- `app.py`: รับ `circuit` = `divider`|`fixed`|`emitter` (default `divider` เพื่อให้ test เก่าผ่าน)
  GET `/` รับ query `circuit` เพื่อโหลดฟอร์มใหม่; POST `/calculate` dispatch ตามโหมด
  unknown mode → error; ตรวจ field ตามโหมด; error/result ส่ง `circuit_label` ให้ template
- `templates/index.html`: แถบเลือกโหมดเป็นลิงก์ (GET `/?circuit=...`), แสดง label/unit ตามโหมด
- ค่าอ้างอิงอิสระ (คำนวณมือ ก่อนรัน ใช้ตัดสิน A1–A5):
  A1 Divider IC=1.2299 mA, VCE=8.0522 V
  A2 Fixed RB=1000 kΩ: IB=11.30 µA, IC=1.1300 mA, VE=0 V, VCE=9.5140 V
  A3 Emitter RB=1000 kΩ, RE=1 kΩ: IC=1.0263 mA, VCE=8.7055 V
  A4 Emitter RE=2 kΩ: IC=0.9401 mA (ลดจาก A3 เพราะตัวหารเพิ่ม), VCE=8.0328 V
  A5 Fixed RB=0 → error "RB ต้องมากกว่า 0"

## สิ่งที่เหลือให้ builder
เขียน plan แยก task ตาม TDD แล้ว execute; เก็บหลักฐาน browser ใส่ docs/validation.md
