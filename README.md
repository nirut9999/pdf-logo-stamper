# PDF Logo Stamper

วาง **watermark: โลโก้ (ซ้าย) + ข้อความ (ขวา) เช่น "COPY No.N" สีแดง** ทับมุมขวาบนของ **ทุกหน้า** ในไฟล์ PDF — ไม่แก้ไขเนื้อหาเดิม, มองทะลุได้, ปรับ layout ได้ครบ:

> 📕 คู่มือติดตั้งบนเครื่องอื่น (Windows + Docker) เป็น PDF: [`docs/คู่มือติดตั้ง-Docker-Windows.pdf`](docs/) — สร้างใหม่ได้ด้วย `python3 docs/build_manual.py`

- 🖼 **เลือกโลโก้จากเว็บ** — browse/drag รูป PNG (รองรับพื้นโปร่งใส)/JPG/WEBP, เก็บเป็นคลังเลือกสลับได้
- 📄 **เลือก PDF จากเว็บ** — browse ได้หลายไฟล์พร้อมกัน
- 🔢 **สำเนา numbered** — ตั้ง copies เช่น **200** → ได้ 200 ไฟล์ `COPY No.1 … COPY No.200` (โหลดเป็น ZIP)
- 🎛 **ปรับ layout**: ย่อ/ขยายโลโก้ (mm), **ขนาดข้อความอิสระ** (mm), **เลือก font** (Helvetica/Times/Courier + **Sarabun สำหรับไทย**), ระยะขอบบน/ขวา, ความจาง opacity, **เอียง ±180°**, สีข้อความ, `{n}` = เลขสำเนา, วางทุกหน้า/หน้าแรก/ช่วงหน้า
- 👁 **Preview สดตรงกับไฟล์จริง** — ภาพในเว็บ rasterize จาก engine ตัวเดียวกับที่ผลิตไฟล์ (เห็นคือได้)
- 💾 **บันทึกการตั้งค่าเป็น "งาน"** — เซฟทั้งชุด (โลโก้+layout+font+copies) ตั้งชื่อ คลิก chip = ใช้ทันที (เก็บฝั่งเซิร์ฟเวอร์), reload แล้วค่าตั้งล่าสุดกลับมาเอง

## รันด้วย Docker (แนะนำ)

```bash
docker compose up -d --build
# เปิด http://localhost:8090
```

วิธีใช้: ① คลังโลโก้ → browse รูป ② ไฟล์ PDF → browse เลือกไฟล์ ③ ตั้งค่า/copies ④ ดู preview → ปุ่ม **Stamp & ดาวน์โหลด**

## Dev (hot-reload)

```bash
docker compose -f docker-compose.dev.yml up
# UI: http://localhost:5173  backend: 127.0.0.1:9011  docs: http://127.0.0.1:9011/docs
```

## Tests

```bash
cd backend && pip install -r requirements.txt -r requirements-dev.txt
python3 -m pytest -q        # 46 tests — geometry pixel-level + API + copies + Sarabun/ไทย
```

## API (curl examples)

```bash
BASE=http://localhost:8090
curl -s $BASE/api/fonts          # -> ["Helvetica",...,"Sarabun","Sarabun-Bold"]
LOGO=$(curl -s -F file=@logo.png $BASE/api/logos | jq -r .id)
PDF=$(curl -s -F files=@doc.pdf $BASE/api/pdfs | jq -r '.[0].id')
# preview หน้า 1 ของสำเนาที่ 7 → PNG
curl -s -o p.png -H 'Content-Type: application/json' -d '{
  "pdf_id":"'$PDF'","logo_id":"'$LOGO'","page_index":1,"copy_number":7,
  "options":{"include_text":true,"opacity":0.6,"copies":200}}' $BASE/api/preview
# stamp 200 สำเนา → ZIP (ข้อความไทยใช้ "text_font":"Sarabun-Bold","text_template":"ฉบับที่ {n}")
curl -s -o out.zip -H 'Content-Type: application/json' -d '{
  "pdf_ids":["'$PDF'"],"logo_id":"'$LOGO'",
  "options":{"include_text":true,"opacity":0.6,"rotation_degrees":0,"copies":200}}' $BASE/api/stamp
# บันทึกชุดค่าตั้งไว้ใช้กับงานเดิม (ได้ id = update ทับ, ไม่มี id = create)
curl -s -H 'Content-Type: application/json' -d '{
  "name":"งานเช่าเครื่อง GPO","logo_id":"'$LOGO'","options":{"copies":50,"text_font":"Sarabun-Bold","text_template":"ฉบับที่ {n}"}}' $BASE/api/presets
```

## Limits

PDF ≤50 MB/ไฟล์, ≤500 หน้า · logo ≤8 MB · copies ≤200/ไฟล์ · ผลลัพธ์ ≤1000 ไฟล์/request · PDF เข้ารหัส(ไม่รับ)

ข้อมูลอัปโหลดเก็บใน docker volume `stamper_data` — ไม่ออกจากเครื่อง

รายละเอียดกฎโค้ด/geometry: ดู `CLAUDE.md`
