"""เทสต์ presets — save/list/update/delete + 'งานเดิม' ครบวงจร (apply -> stamp ตรงกับที่เซฟ)"""
from __future__ import annotations

import io
import time
import zipfile

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def logo_id(client):
    from PIL import Image
    img = Image.new("RGBA", (300, 120), (0, 100, 200, 255))
    buf = io.BytesIO(); img.save(buf, "PNG")
    r = client.post("/api/logos", files={"file": ("brand.png", buf.getvalue(), "image/png")})
    return r.json()["id"]


@pytest.fixture
def pdf_id(client):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595.28, 841.89))
    for i in range(2):
        c.drawString(60, 700, f"P{i}")
        c.showPage()
    c.save()
    r = client.post("/api/pdfs", files={"files": ("doc.pdf", buf.getvalue(), "application/pdf")})
    return r.json()[0]["id"]


FULL_OPTIONS = {
    "logo_width_mm": 28, "margin_top_mm": 7, "margin_right_mm": 7, "opacity": 0.55,
    "page_scope": "all", "rotation_degrees": 15, "include_text": True,
    "text_template": "ฉบับที่ {n}", "text_color": "#CC0000", "text_size_mm": 5.5,
    "text_font": "Sarabun-Bold", "copies": 4,
}


def _save(client, name, logo_id, options=FULL_OPTIONS, pid=None):
    body = {"name": name, "logo_id": logo_id, "options": options}
    if pid:
        body["id"] = pid
    return client.post("/api/presets", json=body)


def test_save_and_list_roundtrip_exact(client, logo_id):
    r = _save(client, "งานเช่าเครื่อง GPO", logo_id)
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["name"] == "งานเช่าเครื่อง GPO" and p["logo_id"] == logo_id
    # options ต้องกลับมา exact ทุกฟิลด์ (รวมถึง mm, font, copies)
    for k, v in FULL_OPTIONS.items():
        assert p["options"][k] == v, k
    lst = client.get("/api/presets").json()
    assert any(x["id"] == p["id"] for x in lst)
    # schema default ที่ไม่ส่งไป ต้องถูกเติมค่า default (logo_height_mm=None)
    assert p["options"]["logo_height_mm"] is None


def test_newest_first_ordering(client, logo_id):
    a = _save(client, "golder", logo_id).json()["id"]
    time.sleep(0.02)
    b = _save(client, "newest", logo_id).json()["id"]
    names = [x["name"] for x in client.get("/api/presets").json()]
    assert names.index("newest") < names.index("golder")


def test_update_in_place_keeps_created(client, logo_id):
    r = _save(client, "v1", logo_id)
    pid, created = r.json()["id"], r.json()["created_at"]
    time.sleep(0.02)
    opts = dict(FULL_OPTIONS, copies=10)
    r2 = _save(client, "v2", logo_id, opts, pid=pid)
    assert r2.status_code == 200
    p = r2.json()
    assert p["id"] == pid and p["name"] == "v2" and p["created_at"] == created
    assert p["updated_at"] >= created
    # ต้องไม่มีรายการซ้ำ
    assert sum(1 for x in client.get("/api/presets").json() if x["id"] == pid) == 1


def test_apply_preset_then_stamp_matches_saved(client, logo_id, pdf_id):
    """ครบวงจร 'งานเดิม': save preset -> apply options -> stamp -> ได้ 4 สำเนา ฉบับที่ N"""
    p = _save(client, "งานเดิม 4 ฉบับ", logo_id).json()
    r = client.post("/api/stamp", json={"pdf_ids": [pdf_id], "logo_id": p["logo_id"],
                                        "options": p["options"]})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert len(zf.namelist()) == 4
    for i, n in enumerate(zf.namelist(), 1):
        t = PdfReader(io.BytesIO(zf.read(n))).pages[0].extract_text() or ""
        assert f"ฉบับที่ {i}" in t, (n, t)


def test_invalid_options_rejected_422(client, logo_id):
    r = _save(client, "bad", logo_id, dict(FULL_OPTIONS, text_font="Comic"))
    assert r.status_code == 422


def test_update_missing_id_404(client, logo_id):
    r = _save(client, "x", logo_id, pid="deadbeef0000")
    assert r.status_code == 404


def test_delete_preset(client, logo_id):
    pid = _save(client, "to-delete", logo_id).json()["id"]
    assert client.delete(f"/api/presets/{pid}").json() == {"deleted": True}
    assert not any(x["id"] == pid for x in client.get("/api/presets").json())
    assert client.delete(f"/api/presets/{pid}").status_code == 404


def test_preset_survives_logo_deletion(client, logo_id):
    """preset เก็บ id ของโลโก้ — โลโก้ถูกลบ preset ยัง list ได้ (UI จะเตือนตอน apply)"""
    pid = _save(client, "ref-orphan", logo_id).json()["id"]
    assert client.delete(f"/api/logos/{logo_id}").status_code == 200
    p = client.get("/api/presets").json()
    got = [x for x in p if x["id"] == pid][0]
    assert got["logo_id"] == logo_id  # ยังจำ id เดิมไว้
    client.delete(f"/api/presets/{pid}")
