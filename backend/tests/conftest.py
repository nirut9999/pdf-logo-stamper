"""Fixtures สำหรับเทสต์ stamping — สร้าง PDF/โลโก้ของจริงไม่ต้องพึ่งไฟล์ภายนอก"""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

# แยก DATA_DIR สำหรับเทสต์ ก่อน module app/config ถูก import (ป้องกันปนกับ data จริง)
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="stamper_test_"))

import pytest
from PIL import Image
from reportlab.pdfgen import canvas


def _solid_logo(tmp_path: Path, w: int, h: int, name: str,
                rgb=(255, 0, 0), corner_alpha: int | None = None) -> Path:
    p = tmp_path / name
    img = Image.new("RGBA", (w, h), (rgb[0], rgb[1], rgb[2], 255))
    if corner_alpha is not None:
        img.putpixel((0, 0), (0, 0, 0, corner_alpha))  # โปร่งใส 1 มุม
    img.save(p)
    return p


@pytest.fixture
def logo_path(tmp_path: Path) -> Path:
    """โลโก้ PNG ไม่จตุรัส 200x80 สีแดงทึบ (ทดสอบสัดส่วน +ตำแหน่ง)"""
    return _solid_logo(tmp_path, 200, 80, "logo.png")


@pytest.fixture
def alpha_logo_path(tmp_path: Path) -> Path:
    """โลโก้ที่มีพิกเซลโปร่งใส 1 จุด (ทดสอบ mask='auto' ไม่กลืนเป็นกล่องทึบ)"""
    return _solid_logo(tmp_path, 100, 50, "alpha_logo.png", corner_alpha=0)


@pytest.fixture
def blue_logo_path(tmp_path: Path) -> Path:
    """โลโก้สีน้ำเงิน (แยกจากข้อความสีแดงได้ตอนตรวจ pixel)"""
    return _solid_logo(tmp_path, 200, 80, "blue.png", rgb=(0, 90, 200))


def _make_pdf(tmp_path: Path, name: str, n: int, rotate_last: int = 0) -> Path:
    """สร้าง PDF พื้นขาว n หน้า (A4) หน้าสุดท้ายใส่ /Rotate ได้"""
    p = tmp_path / name
    c = canvas.Canvas(str(p), pagesize=(595.28, 841.89))
    for i in range(n):
        c.setFont("Helvetica", 24)
        c.drawString(60, 700, f"PAGE {i + 1}")
        c.showPage()
    c.save()
    if rotate_last:
        from pypdf import PdfReader, PdfWriter

        r = PdfReader(str(p))
        w = PdfWriter()
        for pg in r.pages:
            w.add_page(pg)
        w.pages[-1].rotate(rotate_last)
        with open(p, "wb") as fh:
            w.write(fh)
    return p


@pytest.fixture
def two_page_pdf(tmp_path: Path) -> Path:
    return _make_pdf(tmp_path, "doc2.pdf", 2)


@pytest.fixture
def rotated_pdf(tmp_path: Path) -> Path:
    return _make_pdf(tmp_path, "docrot.pdf", 2, rotate_last=90)
