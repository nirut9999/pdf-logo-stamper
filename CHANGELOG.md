# Changelog — PDF Logo Stamper

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
