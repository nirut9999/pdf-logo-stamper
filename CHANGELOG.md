# Changelog — PDF Logo Stamper

## 2026-10-14 (docs)
- 🔓 เปลี่ยน repo เป็น **public** (สแกน history ทั้งสาย — ไม่มี PII/secret/upload ในทุก commit เลย) · คู่มือข้อ 3 = clone ไม่ต้องล็อกอิน, README/PROJECT อัปเดตตาม

- 🔒 สร้าง **private GitHub repo** `github.com/nirut9999/pdf-logo-stamper` — push ทั้งโปรเจกต์ (ไม่มี PII: uploads อยู่ในโลกของ docker volume เท่านั้น)
- 📕 **คูมือ PDF เขียนใหม่ด้วย WeasyPrint (Pango/HarfBuzz shaping)** — เวอร์ชัน reportlab เดิมวางวรรณยุกต์ไทยผิดตำแหน่งทั้งเล่ม (ไม่ทำ text shaping); สร้างใหม่ด้วย `docs/build_manual.py` (ต้องมี weasyprint)
- 📕 คูมือเปลี่ยนวิธีขนโค้ดเป็น `git clone` (Git for Windows + GCM login) แทน ZIP, ZIP เป็น fallback, หัวข้อ 8 ทำตารางอธิบายตัวแปร .env, เก็บ `docs/_manual.html` พ้น git

## v1.3.0 (2026-10-12)
- feat: **บันทึกการตั้งค่า (presets)** — เซฟชุดค่าตั้งทั้งก้อน (โลโก้+ขนาด/ระยะขอบ/ความจาง/เอียง/ข้อความ/font/copies/ขอบเขตหน้า) ตั้งชื่อได้ เก็บใน volume (ข้ามบราวเซอร์/restart อยู่)
      `POST/GET/DELETE /api/presets` — validate ตอนเซฟด้วย StampOptions เดียวกับตอน stamp (config ใช้ไม่ได้ = 422 ตั้งแต่ต้น)
- feat: UI "งานที่บันทึกไว้" เป็น chip คลิกใช้ทันที + บันทึกทับของเดิม (จำ created_at) + "+ ค่าตั้งใหม่" + ลบด้วย ×
- feat: auto-restore ค่าตั้งล่าสุดผ่าน localStorage — reload แล้วงานเดิมกลับมาเอง
- fix: deep-watch ของ config เขียน default ทับ LS ก่อน restore ตอน init → เพิ่ม gate `_ready` เปิดหลัง restore จบ (เจอจาก e2e จริงใน browser)
- tests: 54 ผ่าน (+presets CRUD, apply→stamp ครบวงจร "ฉบับที่ 1..5")

## v1.2.0 (2026-10-12)
- **layout ใหม่**: โลโก้ *หน้า* (ซ้าย) ตัวหนังสือ — เป็นแถวเดียวกัน, ข้อความถูกดันไปทางซ้าย, ขอบบนชิดกัน
- feat: ขนาดข้อความปรับอิสระจากโลโก้ (slider 2–30mm)
- feat: เลือก font ได้ — `GET /api/fonts` (10 ตัว); embed **Sarabun / Sarabun-Bold** (TTF, OFL license) สำหรับข้อความไทย
      Helvetica/Times/Courier ไม่มีตัวไทย → ข้อความไทย+font ต่างชาติ = 400 พร้อมแนะนำ Sarabun
- fix: stamp ไฟล์ชื่อไทยพัง 500 (Content-Disposition latin-1) → RFC 5987 `filename*=UTF-8''`; frontend อ่านชื่อไทยถูกต้อง
- fix: `_safe_stem` ตัดวรรณยุกต์ไทย (Python `\w` ไม่ครอบ combining mark) → mask เฉพาะอักขระต้องห้าม path/zip
- tests: 46 ผ่าน (แนวนอน logo→text order, Sarabun ไทย, ชื่อไทย zip/header)

## v1.1.0 (2026-10-12)
- feat: ข้อความ watermark ใต้โลโก้ (`COPY No.{n}`, สี/ขนาดกำหนดได้, default แดง)
- feat: **copies mode** — N สำเนาต่อไฟล์ (ถึง 200) เลข 1..N, ดาวน์โหลด ZIP ชื่อไฟล์แนบเลข
- feat: เอียง watermark ±180° — pivot จุดศูนย์กลางกลุ่ม, ขวาบนตรึงที่ anchor
- feat: preview เลือกเลขสำเนาตัวอย่าง (เลขในภาพ = เลขที่จะ stamp จริง)
- fix: alpha ของข้อความถูกรีเซ็ตโดย drawImage(mask) — re-apply หลังวาดโลโก้
- fix: rotation แบบ anchor-pivot ทำข้อความหลุดขอบบนหน้า → เปลี่ยนเป็น center-pivot bbox
- tests: 39 tests (geometry pixel-level + API flow + copies integrity)

## v1.0.0 (2026-10-12)
- โลโก้ PNG/JPG มุมขวาบนทุกหน้า (mm scale, margins, opacity, page scope)
- FastAPI + Vue3/Pinia/Tailwind + nginx/Docker Compose, WYSIWYG preview จาก engine จริง
