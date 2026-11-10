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
