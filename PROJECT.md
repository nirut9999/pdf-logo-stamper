# PROJECT.md — PDF Logo Stamper

## 1. Overview
Web app สำหรับวาง watermark "โลโก้ + ข้อความสำเนา (COPY No.N)" มุมขวาบนของทุกหน้า PDF — อัปโหลดโลโก้/PDF ผ่านเบราว์เซอร์, ปรับ layout (ขนาด/ระยะขอบ/ความจาง/เอียง), สร้าง N สำเนาต่อไฟล์ (เช่น 200 ชุด เลข 1..N) ดาวน์โหลดเป็น ZIP — overlay ทับไม่แก้เนื้อหาเดิม

## 1.5. Before Starting Work — Skills to Load
`pdf` (stamp/overlay patterns), `docker-compose`, `frontend-spa-modification` / `static-frontend-deploy` (Vue+nginx), `test-driven-development`, `verification-before-completion`

## 2. Snapshot
- 🟢 v1.3.0 (2026-10-12) — สดที่ :8090; ใหม่: **presets** (บันทึกงานเดิม + auto-restore ค่าตั้งล่าสุด, validate ตอนเซฟด้วย engine stamp); e2e ผ่านกับไฟล์จริงผู้ใช้ (โลโก้ อภ. + PDF ไทย 8 หน้า, "ฉบับที่ 1..5" ×50 preset)
- 54 backend tests green · frontend `vite build` clean

## 3. Changelog
ดู CHANGELOG.md — v1.0.0 logo-only stamper · v1.1.0 +COPY No.N text, rotation, 200-copies mode, WYSIWYG preview ผ่าน API · **v1.2.0 โลโก้→หน้า(ซ้าย)ข้อความ แถวเดียวกัน, ขนาดข้อความอิสระ, font เลือกได้ (Sarabun = ไทย), แก้ชื่อไฟล์ไทย 500 (RFC 5987)**

## 4. Plan & Roadmap
- [ ] range สำเนาเริ่มต้น/จบ (เช่น No.101..300) ถ้าผู้ใช้ต้องการ numbering ต่อชุด
- [ ] ตำแหน่งมุมอื่น (ซ้ายบน/กลางบน) ถ้า demand มา — engine รองรับแล้ว ขาดแค่ UI anchor select
- [x] push ขึ้น remote — **public** @ github.com/nirut9999/pdf-logo-stamper (2026-10-14)

## 5. Architecture
```
Browser (Vue3/Pinia) ──nginx :8090──┬─ /        static SPA dist
                                     └─ /api/* → backend uvicorn :9010 (FastAPI)
                                                app/stamping.py  = core (pypdf overlay + reportlab canvas)
                                                app/render.py      = preview raster (pypdfium2)
                                                app/storage.py     = file + .json sidecar ใน volume stamper_data
```
preview เรียก stamping จริงแล้ว rasterize → ภาพที่เห็น = ไฟล์ที่ได้ (single source of truth ฝั่ง geometry)

## 6. Tech Stack
Python 3.12-slim · FastAPI · pypdf 6.10 · reportlab 5.0 · pypdfium2 · Pillow | Vue 3 + Pinia + Tailwind 3.4 + Vite 5 | nginx 1.27-alpine | Docker Compose v2

## 7. Data Model
ไม่มี DB — ไฟล์บนดิสก์: `data/logos/{id}.png + {id}.json` (filename, w/h px), `data/pdfs/{id}.pdf + {id}.json` (filename, page_count, size, pages[{index,width_pt,height_pt}]); id = uuid4 hex12

## 8. Dev Environment
`docker compose up -d --build` (prod) · `docker compose -f docker-compose.dev.yml up` (hot-reload) · tests: `cd backend && python3 -m pytest -q` · UI dev: `cd frontend && npm run dev`

## 9. Environment & Secrets
ไม่มี secrets (single-user, on-prem) — env: `DATA_DIR, PORT, CORS_ORIGINS, PREVIEW_DPI, MAX_PDF_BYTES, MAX_LOGO_BYTES, MAX_PAGES_PER_DOC, MAX_OUTPUT_FILES, FRONTEND_PORT, BACKEND_PORT` (ดู .env.example)

## 10. CI/CD
ยังไม่ตั้ง — candidates: GitHub Actions รัน pytest + vite build (ตาม pattern PME)

## 11. Decisions
- mm เป็นหน่วย input (งานพิมพ์ตรงกว่า px) · opacity default 0.6 (nature = watermark)
- layout v1.2: [โลโก้ | gap | ข้อความ] แนวนอน ขอบบนชิด — ผู้ใช้สั่ง "logo ต้องอยู่หน้าตัวหนังสือ"
- rotation pivot = center ของกลุ่ม (ไม่ใช่ anchor — เคยทำให้ข้อความหลุดขอบบน)
- text size เป็นอิสระจาก logo width (slider ของใครของมัน); ข้อความไทยบังคับ font TTF (Sarabun) — validate ที่ StampOptions
- backend preview (ไม่ใช่ pdf.js ฝั่ง client) เพื่อ WYSIWYG 100%
- copies จำกัด 200/ไฟล์, ผลรวม ≤1000 ไฟล์ต่อ request
- Sarabun TTF embed ใน repo (OFL license อนุญาต) — ไม่พึ่ง font บนเครื่อง
- ⚠️ project CLAUDE.md เป็น protected file ของ harness — แก้ต้อง approvals จาก owner; notes ใหม่เก็บที่นี่/CHANGELOG ไปก่อน

## 12. Risks & Open Items
- ไฟล์อัปโหลดค้างใน volume ถ้าไม่ลบผ่าน UI — ผู้ใช้จัดการเอง (on-prem trusted)
- PDF ถูกเข้ารหัส = reject 400 (ตั้งใจ — ไม่รับ password)
- หน้า /Rotate แปลกๆ (ไม่ใช่ 90 step) ยังไม่ coverage เต็ม

## 13. People
Owner/ผู้ใช้งาน: คุณนิรุตต์ · Dev/agent: Hermes

## 14. Links
UI: http://localhost:8090 · API docs: http://127.0.0.1:9012/docs · Repo: github.com/nirut9999/pdf-logo-stamper (private)
