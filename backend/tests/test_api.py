"""เทสต์ API end-to-end ผ่าน TestClient — อัปโหลด logo/pdf, preview, stamp เดียว+zip"""
from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas


def make_pdf_bytes(n: int = 2) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595.28, 841.89))
    for i in range(n):
        c.setFont("Helvetica", 20)
        c.drawString(60, 700, f"PAGE {i + 1}")
        c.showPage()
    c.save()
    return buf.getvalue()


def make_logo_bytes() -> bytes:
    img = Image.new("RGBA", (300, 120), (0, 100, 200, 255))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def logo_id(client):
    r = client.post("/api/logos", files={"file": ("brand.png", make_logo_bytes(), "image/png")})
    assert r.status_code == 200, r.text
    return r.json()["id"]


@pytest.fixture
def pdf_id(client):
    r = client.post("/api/pdfs", files={"files": ("doc.pdf", make_pdf_bytes(2), "application/pdf")})
    assert r.status_code == 200, r.text
    return r.json()[0]["id"]


OPTIONS = {"logo_width_mm": 30, "margin_top_mm": 8, "margin_right_mm": 8,
           "opacity": 1.0, "page_scope": "all"}


def test_stamp_copies_200_zip_numbered(client, logo_id):
    """1 PDF × 2 copies -> zip 2 ไฟล์ ชื่อแนบเลข + เนื้อในมี COPY No.N ของตัวเอง"""
    r0 = client.post("/api/pdfs", files={"files": ("memo.pdf", make_pdf_bytes(1), "application/pdf")})
    pid = r0.json()[0]["id"]
    opts = dict(OPTIONS, include_text=True, copies=2)
    r = client.post("/api/stamp", json={"pdf_ids": [pid], "logo_id": logo_id, "options": opts})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert names == ["memo_COPY_No.1.pdf", "memo_COPY_No.2.pdf"]
    for i, n in enumerate(names, start=1):
        page = PdfReader(io.BytesIO(zf.read(n))).pages[0]
        txt = (page.extract_text() or "").replace(" ", "")
        assert f"COPYNo.{i}" in txt, (n, txt)


def test_stamp_copies_within_limit(client, logo_id):
    """200 copies ของ PDF 1 หน้า — ไม่เกิน default cap 1000 ไฟล์"""
    r0 = client.post("/api/pdfs", files={"files": ("small.pdf", make_pdf_bytes(1), "application/pdf")})
    pid = r0.json()[0]["id"]
    opts = dict(OPTIONS, include_text=True, copies=200)
    r = client.post("/api/stamp", json={"pdf_ids": [pid], "logo_id": logo_id, "options": opts})
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert len(zf.namelist()) == 200


def test_stamp_copies_over_limit_400(client, logo_id):
    """เกิน MAX_OUTPUT_FILES -> 400 พร้อมข้อความอธิบาย"""
    r0 = client.post("/api/pdfs", files={"files": ("big.pdf", make_pdf_bytes(1), "application/pdf")})
    pid = r0.json()[0]["id"]
    import app.routers.stamp as stamp_mod
    old = stamp_mod.MAX_OUTPUT_FILES
    stamp_mod.MAX_OUTPUT_FILES = 100
    try:
        opts = dict(OPTIONS, copies=200)
        r = client.post("/api/stamp", json={"pdf_ids": [pid], "logo_id": logo_id, "options": opts})
        assert r.status_code == 400
        assert "เกินสูงสุด" in r.json()["detail"]
    finally:
        stamp_mod.MAX_OUTPUT_FILES = old


def test_preview_with_copy_number(client, logo_id, pdf_id):
    r = client.post("/api/preview", json={"pdf_id": pdf_id, "logo_id": logo_id,
                                          "page_index": 1, "copy_number": 7,
                                          "options": dict(OPTIONS, include_text=True)})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"


def test_preview_page_index_over_limit_400(client, logo_id, pdf_id):
    r = client.post("/api/preview", json={"pdf_id": pdf_id, "logo_id": logo_id,
                                          "page_index": 99, "options": OPTIONS})
    assert r.status_code == 400


def test_options_color_validation_422(client, logo_id, pdf_id):
    r = client.post("/api/stamp", json={"pdf_ids": [pdf_id], "logo_id": logo_id,
                                        "options": dict(OPTIONS, text_color="red")})
    assert r.status_code == 422  # pattern #[0-9a-fA-F]{6}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "version": "1.3.0"}


def test_upload_logo_metadata(client):
    r = client.post("/api/logos", files={"file": ("brand.png", make_logo_bytes(), "image/png")})
    body = r.json()
    assert body["width_px"] == 300 and body["height_px"] == 120
    assert body["url"] == f"/api/logos/{body['id']}/image"
    # ดึงภาพกลับได้
    assert client.get(body["url"]).status_code == 200


def test_upload_pdf_dims(client):
    r = client.post("/api/pdfs", files={"files": ("doc.pdf", make_pdf_bytes(2), "application/pdf")})
    doc = r.json()[0]
    assert doc["page_count"] == 2
    assert round(doc["pages"][0]["width_pt"], 1) == 595.3
    assert round(doc["pages"][0]["height_pt"], 1) == 841.9


def test_preview_returns_png(client, logo_id, pdf_id):
    r = client.post("/api/preview", json={"pdf_id": pdf_id, "logo_id": logo_id,
                                           "page_index": 1, "options": OPTIONS})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(r.content))
    assert img.width > 100


def test_stamp_single_pdf(client, logo_id, pdf_id):
    r = client.post("/api/stamp", json={"pdf_ids": [pdf_id], "logo_id": logo_id, "options": OPTIONS})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    reader = PdfReader(io.BytesIO(r.content))
    assert len(reader.pages) == 2
    assert "doc_logo.pdf" in r.headers["content-disposition"]


def test_stamp_multiple_returns_zip(client, logo_id):
    ids = []
    for _ in range(2):
        rr = client.post("/api/pdfs", files={"files": ("doc.pdf", make_pdf_bytes(1), "application/pdf")})
        ids.append(rr.json()[0]["id"])
    r = client.post("/api/stamp", json={"pdf_ids": ids, "logo_id": logo_id, "options": OPTIONS})
    assert r.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert len(names) == 2
    for n in names:
        assert PdfReader(io.BytesIO(zf.read(n)))  # แต่ละไฟล์เป็น PDF ที่อ่านได้


def test_stamp_page_scope_first(client, logo_id, pdf_id):
    opts = dict(OPTIONS, page_scope="first")
    r = client.post("/api/stamp", json={"pdf_ids": [pdf_id], "logo_id": logo_id, "options": opts})
    assert r.status_code == 200
    assert len(PdfReader(io.BytesIO(r.content)).pages) == 2  # จำนวนหน้าคงเดิม


def test_reject_bad_logo_ext(client):
    r = client.post("/api/logos", files={"file": ("x.gif", b"GIF89a....", "image/gif")})
    assert r.status_code == 400


def test_reject_non_pdf(client):
    r = client.post("/api/pdfs", files={"files": ("a.txt", b"hello not a pdf", "text/plain")})
    assert r.status_code == 400


def test_preview_missing_pdf_404(client, logo_id):
    r = client.post("/api/preview", json={"pdf_id": "nope", "logo_id": logo_id,
                                          "page_index": 1, "options": OPTIONS})
    assert r.status_code == 404


def test_stamp_thai_filename_uses_rfc5987(client, logo_id):
    """ชื่อไฟล์ไทยต้องไม่พัง header (latin-1) — response มี filename*=UTF-8''"""
    thai_name = "วิธีการตั้งค่าเครื่องไทย.pdf"
    r0 = client.post("/api/pdfs", files={"files": (thai_name, make_pdf_bytes(1), "application/pdf")})
    pid = r0.json()[0]["id"]
    opts = dict(OPTIONS, include_text=True)
    r = client.post("/api/stamp", json={"pdf_ids": [pid], "logo_id": logo_id, "options": opts})
    assert r.status_code == 200, r.text
    cd = r.headers["content-disposition"]
    assert "filename*=UTF-8''" in cd, cd
    from urllib.parse import unquote
    fn = unquote(cd.split("filename*=UTF-8''")[1])
    assert fn.startswith("วิธีการตั้งค่าเครื่องไทย"), fn


def test_stamp_thai_copies_zip(client, logo_id):
    """copies + ชื่อไทย -> zip entries ชื่อไทยครบ"""
    r0 = client.post("/api/pdfs", files={"files": ("สัญญาเช่า.pdf", make_pdf_bytes(1), "application/pdf")})
    pid = r0.json()[0]["id"]
    opts = dict(OPTIONS, include_text=True, copies=3)
    r = client.post("/api/stamp", json={"pdf_ids": [pid], "logo_id": logo_id, "options": opts})
    assert r.status_code == 200, r.text
    names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert len(names) == 3 and any("สัญญาเช่า" in n for n in names), names


def test_stamp_bad_page_scope_400(client, logo_id, pdf_id):
    opts = dict(OPTIONS, page_scope="99")  # นอกช่วงหน้า
    r = client.post("/api/stamp", json={"pdf_ids": [pdf_id], "logo_id": logo_id, "options": opts})
    assert r.status_code == 400
