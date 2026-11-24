# Impeccable critique → polish → audit — Lab 04

## สถานะเครื่องมือ

| เครื่องมือ | สถานะ | เหตุผล |
|---|---|---|
| `skill impeccable` | **NOT RUN** | ไม่มี skill นี้ใน harness (`Unable to load skill impeccable`) |
| Playwright MCP | **NOT RUN** | ไม่มี MCP server ใน session; ใช้ OpenCode Browser แทนตาม handout และใช้ Playwright CLI เฉพาะเพื่อจับ viewport 390px (MCP ≠ CLI) |
| OpenCode Browser | **PASS** | ใช้ตรวจ B1–B7 จริง (open/snapshot/fill/select/click/wait/evaluate/screenshot) |
| Playwright CLI (`npx playwright`) | **PASS (เสริม)** | ใช้จับภาพ B8 ที่ viewport 1280px/390px จริงเพราะ OpenCode Browser ไม่มี tool ปรับ viewport |

## Critique ( Manual — ทดแทน skill ที่ไม่มี )

ตรวจหน้า `http://127.0.0.1:5001/?analysis=spice` และผล `/simulate` จาก ngspice จริง

1. **Input grouping** — ฟอร์ม SPICE มี 10 ช่องเรียงต่อเนื่อง ไม่มีความแยกbetween
   โครงข่าย DC (R1/R2/RC/RE/RL/CIN/COUT) กับแหล่งสัญญาณ AC (amplitude/frequency)
   → ผู้ใช้ต้องอ่าน label ทุกบรรทัดเพื่อหาช่องสัญญาณ
2. ** readability บนจอเล็ก** — `.axis-title`/`.tick` ใน SVG ไม่มี media-query
   ขนาดข้อความจะเล็กตามการย่อ `viewBox` เมื่อจอ 390px
3. **Error state** — ข้อความ error ชัด (`[SPICE] RE ต้องมากกว่า 0`) และไม่มี
   `Success`/`<svg>` ค้าง → ไม่ต้องแก้
4. **Provenance** — มี `Source: ngspice-47 · model: QBC547B · provenance: ngspice`
   แยกจาก `Analytical: dc_bias.py` → ไม่ต้องแก้
5. **Status** — badge `Success — AC Bode (.ac)` อยู่เหนือตารางผล → ไม่ต้องแก้

## Polish (เฉพาะ `static/style.css` — ห้ามแตะสูตร/ข้อมูลกราฟ)

- เพิ่มเส้นแบ่ง + หัวข้อ `AC source` ด้วย `label[for="sp-amplitude"]` แบบ CSS-only
  (ไม่แตะ template)
- แก้ legend bullet ที่เสียไปจากการเขียนไฟล์ด้วย PowerShell (`?` → `●`)
- ที่ `@media (max-width:480px)`: เพิ่ม `.axis-title` 16px, `.tick` 14px,
  `.plot-block` padding 8px, `.hint` line-height 1.5

## Audit หลัง polish

- `py -m unittest discover -v` → PASS ทุกตัว (ดู `docs/test-log.txt`)
- `git diff -- static/style.css` เฉพาะ CSS; ไม่มีไฟล์ `app.py`, `spice_engine.py`,
  `templates/_plot.html` เปลี่ยนในขั้นตอน polish
- ภาพก่อน: `docs/screenshots/lab04-ui-before.png` (OpenCode Browser, desktop)
- ภาพหลัง: `docs/screenshots/lab04-ui-after.png` (Playwright CLI, 1280px, AC + 2 plots)
- ภาพ B8 1280/390 หลัง polish: `docs/screenshots/lab04-B8-*.png`
- ตรวจ viewport จริง: desktop `scrollW=1280, clientW=1280, media390=false`;
  mobile `scrollW=390, clientW=390, media390=true` → ไม่มีเนื้อหาหลักถูกตัด

## ข้อจำกัด

ไม่สามารถอ้างว่าได้ critique จาก Impeccable skill หรือผลจาก Playwright MCP ได้
เพราะทั้งสองไม่พร้อม — รายงานนี้ใช้ manual critique ตามที่ handout อนุญาต
