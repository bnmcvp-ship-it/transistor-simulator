# Reflection — Lab 02 (คำถามรายบุคคล)

## 1. เหตุใดการเปิด templates/index.html ตรง ๆ จึงไม่เท่ากับการรัน Flask?

การ double-click เปิดไฟล์ผ่าน `file://` คือการเปิด "ภาพจำลอง" ของหน้าเว็บ —
browser อ่าน HTML แล้วแสดงตามตัวอักษรเท่านั้น ปุ่ม Calculate กดแล้วไม่มี
อะไรเกิดขึ้น เพราะไม่มี server คอยรับ request ส่วนการรัน Flask คือการเปิด
**local web server** ที่ port 5000 — browser ส่ง HTTP request ไปที่ server,
Flask route รับ, เรียก `dc_bias.py` คำนวณด้วย Python แล้ว render ผลกลับมา
เป็น HTML ใหม่ นอกจากนี้ template มี Jinja syntax (`{% for %}`, `{{ }}`)
ที่ browser เข้าใจไม่ได้เอง ต้องมี Flask แปลงให้ก่อน

## 2. ฟอร์มส่งข้อมูลไป Python อย่างไร?

ฟอร์มมี `method="post" action="/calculate"` — เมื่อกดปุ่ม submit,
browser สร้าง **HTTP POST request** พร้อม body เก็บค่าทุกช่อง input
(name=vcc, r1, ...) ส่งไปที่ `http://127.0.0.1:5000/calculate`.
Flask route `@app.route("/calculate", methods=["POST"])` รับ request,
ดึงค่าด้วย `request.form.get("vcc")` เป็น string, แปลงเป็น float ด้วย
`parse_field` แล้วส่งเข้า `analyze()` ผลลัพธ์ถูกใส่กลับ template และตอบ
กลับเป็น HTML (HTTP response) ที่ browser แสดงแทนหน้าเดิม

## 3. แก้สมการใน dc_bias.py แล้วต้องแก้ HTML หรือไม่?

**ไม่ต้อง** — template ไม่มีสมการฟิสิกส์ฝังอยู่เลย มันแค่ "แสดง" ตัวแปร
ที่ route ส่งมาให้ (`{{ value }}`) การแยกหน้าที่แบบนี้คือประเด็นหลักของ
Lab: แก้วิศวกรรมที่ `dc_bias.py`, แก้หน้าตาที่ `static/style.css`,
แก้เนื้อหาหน้าที่ `templates/index.html` — ไม่ปนกัน และ tests ของ
สมการอยู่ใน `tests/test_dc_bias.py` ตรวจให้เองโดยไม่แตะ HTML

## 4. ทำไมผลใน Region ที่แบบจำลองใช้ไม่ได้ต้องมี Warning?

แบบจำลอง Forward-Active ตั้งสมมติฐานไว้ว่า junction ทรานซิสเตอร์ bias
อยู่ใน active region (β คงที่, VBE คงที่) — สมการจึงให้ผลเชื่อถือได้เฉพาะ
เมื่อสมมติฐานจริง ถ้าอินพุตทำให้ VTH≤VBE (Cutoff — ไม่มีกระแสเลย) หรือ
VCE ต่ำกว่า ~0.2 V (Saturation — β ตกฮวบ, ไม่คงที่) ค่าที่คำนวณได้จะผิด
จากวงจรจริงอย่างมีนัยสำคัญ การแสดงตัวเลขลอย ๆ โดยไม่บอกเงื่อนไขคือ
**รายงานผิดจริง** — วิศวกรที่ดีต้องแจ้งข้อจำกัดของตัวเอง ไม่ใช่แค่ตัวเลข
Warning จึงบังคับให้ผู้ใช้รู้ว่าต้องเปลี่ยนอินพุต หรือใช้ solver ที่แม่นกว่า
(SPICE ใน Lab ถัดไป)

---

# Reflection — Lab 03 (หนึ่งเว็บ สามวงจรไบอัส)

## 5. ค่า R_E ใน A4 เดินทางถึงสมการอย่างไร? (ทวนเส้นทางข้อมูล)

เปลี่ยน `RE` จาก 1 → 2 kΩ ในหน้า Emitter Bias แล้วกด Calculate เส้นทางคือ:
input `name="re"` → browser สร้าง POST body `re=2` ไป `/calculate` พร้อม
`circuit=emitter` → `app.py` อ่าน `request.form.get("re")` ได้ string `"2"` →
`parse_field` แปลงเป็น `2.0` → เพราะ `mode == "emitter"` จึงเรียก
`analyze_emitter(..., re=2.0, ...)` → ใน `dc_bias.py` แปลง kΩ→Ω ด้วย `re * 1e3`
= 2000 Ω แล้วใส่ในตัวหาร `(β+1)·RE` → IB ตกจาก 10.26 → 9.40 µA → IC ตก
1.03 → 0.94 mA ตามที่คำนวณมือ ผมตรวจซ้ำโดยอ่านค่า input ใน DOM ด้วย
`evaluate` เห็น `re=2` ก่อน แล้วค่อยอ่าน snapshot หลัง POST ว่าได้ 0.94 mA
— แปลว่าค่าไปถึงสมการจริง ไม่ใช่ผลค้างจากรอบก่อน

## 6. คำถามปิด Lab: ถ้าคำนวณมือถูกแต่เปลี่ยน R_E แล้วผลไม่เปลี่ยน จะตรวจอย่างไร?

ผมจะไล่ทีละจุดตามเส้นทางข้อมูล ไม่เดาสุ่ม:

1. **ที่ฟอร์ม:** ดู `name` ของช่องว่าเป็น `re` จริงไหม (ถ้าพิมพ์ name ผิด เช่น
   `r_e` Flask จะไม่รับ) และอ่านค่าจาก DOM ว่าเปลี่ยนเป็น 2 แล้วจริงหรือไม่ —
   ใน browser ใช้ `evaluate` อ่าน `input.value` ได้เลย
2. **ที่ request:** ดู body ของ POST ว่ามี `re=2` ส่งออกไปจริงไหม ไม่ใช่แค่
   แก้ในหน้าแล้วไม่ได้ submit
3. **ที่ Flask:** เช็ค `request.form.get("re")` ใน route ว่าอ่านชื่อเดียวกับ
   `name` ใน HTML และ `parse_field` แปลงเป็น float ถูก
4. **ที่การเลือกฟังก์ชัน:** เช็ค `circuit` ว่าเป็น `emitter` — ถ้าเป็น `divider`
   อยู่ route จะเรียก `analyze()` แทน แล้ว RE จะถูกอ่านแต่ไม่มีผลต่อ IB แบบเดิม
5. **ที่สมการ:** เช็คหน่วยว่า kΩ ถูกคูณ 1e3 ก่อนใส่ `(β+1)·RE` หรือเปล่า
   และเช็คว่าไม่ได้ไปแก้ใน template แทน (HTML ห้ามมีสมการ)
6. **ที่การแสดงผล:** รอผลรอบใหม่ก่อนอ่าน snapshot — ถ้า `wait` เจอคำว่า
   "DC Bias Results" ที่ค้างจากรอบเก่าจะอ่านค่าผิดได้ (เรื่องนี้เจอจริงใน A4
   แก้โดยรอค่าที่เปลี่ยน เช่น "0.94" แทน)

หลักการคือแยกตรวจ "ค่าส่งออกมา" กับ "ค่าที่เข้าไปในฟังก์ชัน" ให้ชัด เพื่อบอกได้
ว่าปัญหาอยู่ที่ฟอร์ม, route, หรือสมการ

## 7. ส่วนที่ AI ช่วย vs สิ่งที่ตรวจเอง

- AI เขียนโค้ด: `analyze_fixed`, `analyze_emitter`, `_assemble` ใน `dc_bias.py`,
  ตาราง `CIRCUITS` + dispatch ใน `app.py`, แถบเลือกโหมดใน `templates/index.html`,
  และ test ใหม่ 11 ตัว
- สิ่งที่ตรวจเอง: คำนวณ IC/VCE อิสระด้วยมือก่อนรัน (A1–A5 ใน `docs/validation.md`),
  เปิด browser จริงกรอกฟอร์มทุกโหมด, ทวนว่า A1 ผลไม่เปลี่ยน, A4 ผล IC ลดจริง,
  A5 error มาจาก Flask ไม่ใช่ browser, และรัน `unittest` 24 tests ให้ผ่าน
- จุดที่โค้ดเลือกฟังก์ชัน: `if mode == "divider" / elif "fixed" / else "emitter"`
  ใน `app.py`; จุดแปลงหน่วย: `rb * 1e3`, `re * 1e3` ใน `dc_bias.py`

