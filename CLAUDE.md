# CLAUDE.md — PDF Logo Stamper

> Single source of truth — อ่านก่อนทำงานที่นี่

## Status (2026-10-12)

- 🟢 v1.1.0 — production-ready, 39 backend tests green, Docker verified e2e (200 copies)
- **Repo:** ยังไม่มี remote (owner ยังไม่ได้สั่ง push) — code อย่างเดียวปลอดภัย (uploads อยู่ใน docker volume ไม่ใช่ repo)

## 🎯 What this is

Web app วาง **watermark = โลโก้ + ข้อความ "COPY No.N" สีแดง** ทับมุมขวาบนของ **ทุกหน้า** PDF โดยไม่แก้ไขเนื้อหาเดิม (overlay merge)

- เลือกโลโก้จากคลังที่อัปโหลดผ่านเว็บ (browse/drag PNG/JPG/WEBP)
- เลือกไฟล์ PDF ผ่านเว็บ ได้หลายไฟล์พร้อมกัน (ทุกไฟล์เป็น .pdf เท่านั้น)
- **N สำเนาต่อไฟล์**: copies=200 → ZIP 200 ไฟล์ `*_COPY_No.1..200.pdf` — 1 ไฟล์เดียวคืนเป็น PDF ตรงๆ
- ปรับ layout: ย่อ/ขยาย (mm), ระยะขอบบน/ขวา, ความจาง opacity (มองทะลุ), **เอียง ±180°** (pivot = จุดศูนย์กลางกลุ่ม watermark, มุมขวาบนของกล่องที่หมุนแล้วตรึงที่ anchor), ข้อความ/สี/ขนาดตัวอักษร, ขอบเขตหน้า (all/first/custom ranges)
- Preview ในเว็บ rasterize จาก **engine เดียวกับ output จริง** (pypdfium2) — WYSIWYG

## 🏗 Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + pypdf + reportlab + pypdfium2 (Python 3.12-slim, non-root) |
| Frontend | Vue 3 (`<script setup>`) + Pinia + Tailwind (Deep Forest Green/Brass/Ivory) → nginx multi-stage |
| Deploy | Docker Compose — prod `docker-compose.yml`, dev hot-reload `docker-compose.dev.yml` |

## Ports

| Service | prod | dev |
|---------|------|-----|
| Frontend (nginx + /api proxy) | **8090** | 5173 |
| Backend (uvicorn) | 9010 (internal) | 9011 |

## Commands

```bash
docker compose up -d --build            # prod → http://localhost:8090
cd backend && python3 -m pytest -q      # 39 tests (ต้องใช้ deps: -r requirements-dev.txt)
cd frontend && npm run dev              # vite dev (proxy → VITE_PROXY_TARGET)
docker compose -f docker-compose.dev.yml up   # full dev hot-reload
```

## 📐 Core geometry rules (backend/app/stamping.py)

- หน่วย mm everywhere; `MM_TO_PT = 72/25.4`; PDF origin = ล่าง-ซ้าย; "มุมขวาบน" = (page_w - margin_right, page_h - margin_top)
- watermark กลุ่ม = โลโก้ + ข้อความ center-aligned ใต้โลโก้; box (±hw, ±hh) pivot รอบ center; ขวาบนของ rotated bbox ตกที่ anchor เสมอ → deg=0 ตรงกับตำแหน่งแบบไม่หมุน
- หน้าที่มี /Rotate → `transfer_rotation_to_content()` ก่อนวาง (มุมขวาบนต้องตรงกับตาเห็น)
- **Pitfall: `drawImage(mask='auto')` รีเซ็ต fill alpha ภายในของ reportlab เป็น 1** → ต้อง `setFillAlpha()` ซ้ำก่อนวาดข้อความ (มี test ค้ำ: `test_text_opacity_transparent`)
- **Pitfall pypdf 6.x:** `PdfWriter.write()` ไม่มี kwarg `compression`; add page เข้า writer ก่อน แล้ว merge บน `writer.pages[-1]` (เลี่ยง deprecation replace_contents)
- overlay cache ต่อ (page_w,page_h) — เอกสารผสมขนาดหน้ายังเร็ว

## API map (docs: README + /docs)

- `POST /api/logos` (multipart file) · `GET/DELETE /api/logos[/{id}]` · `GET /api/logos/{id}/image`
- `POST /api/pdfs` (multipart files[]) · `GET/DELETE /api/pdfs[/{id}]`
- `POST /api/preview` {pdf_id, logo_id, page_index, copy_number, options} → PNG
- `POST /api/stamp` {pdf_ids[], logo_id, options(+copies ≤200)} → PDF หรือ ZIP
- limits: PDF 50MB/ไฟล์, ≤500 หน้า, logo 8MB, ผลลัพธ์ ≤1000 ไฟล์ (`MAX_OUTPUT_FILES` env)

## Storage

`DATA_DIR=/app/data` (named volume `stamper_data`) — logos/ + pdfs/ พร้อม .json sidecar ต่อรายการ; ลบผ่าน UI ได้; ห้าม commit

## ⚠️ Things to Avoid

- ❌ อย่าแก้ geometry โดยไม่รัน `pytest tests/test_watermark.py tests/test_stamping.py` — มี pixel-level assertions (render จริงที่ 150dpi) ค้ำตำแหน่ง/alpha/rotation
- ❌ อย่าใส่ delegate/subagent ใน workflow (owner order 2026-10-09)
- ❌ อย่า push repo โดยไม่มี remote — รอ owner สั่ง; uploads/PII ห้ามเข้า git

## Testing philosophy

ทุกข้ออ้างเรื่องตำแหน่งต้องพิสูจน์ด้วย pixel ที่ render จากไฟล์จริง (bbox vs expected ±4px, ink direction สำหรับ ±องศา, text extraction สำหรับเลขสำเนา) — ไม่ใช่ assert ค่าพิกัดลอยๆ
