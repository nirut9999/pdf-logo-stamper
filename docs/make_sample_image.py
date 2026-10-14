#!/usr/bin/env python3
"""สร้างตัวอย่าง watermark สะอาด (จาก asset ทดสอบ ไม่ใช่เอกสารผู้ใช้) สำหรับประกอบคู่มือ

usage: python3 make_sample_image.py -> docs/images/sample_watermark.png
"""
from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "backend"
sys.path.insert(0, str(BACKEND))

import pypdfium2 as pdfium  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from app.stamping import StampOptions, stamp_pdf  # noqa: E402


def main() -> None:
    d = Path(tempfile.mkdtemp())
    # เอกสารทดสอบ A4 3 หน้า มีข้อความเหมือนจริง
    pdfp = d / "contract.pdf"
    c = canvas.Canvas(str(pdfp), pagesize=(595.28, 841.89))
    for i in (1, 2, 3):
        c.setFont("Helvetica", 16)
        c.drawString(70, 762, f"ACME CONTRACT - PAGE {i}")
        c.setFont("Helvetica", 10)
        for ln in range(24):
            c.drawString(70, 720 - ln * 24,
                         f"Clause {ln + 1}. This is sample body text of the contract page.")
        c.showPage()
    c.save()
    # โลโก้ทดสอบ (PNG โปร่งใส น้ำเงิน/ทอง แบบองค์กร)
    logo = d / "logo.png"
    img = Image.new("RGBA", (600, 240), (0, 0, 0, 0))
    dd = ImageDraw.Draw(img)
    dd.rounded_rectangle([0, 0, 599, 239], 30, fill=(20, 60, 120, 255))
    dd.ellipse([30, 60, 180, 180], fill=(217, 162, 39, 255))
    dd.text((210, 90), "ACME OFFICE", fill=(255, 255, 255, 255))
    img.save(logo)

    opts = StampOptions(logo_width_mm=30, margin_top_mm=8, margin_right_mm=8,
                        opacity=0.55, include_text=True, text_template="COPY No.{n}",
                        text_font="Helvetica-Bold", text_size_mm=5.5)
    out = stamp_pdf(pdfp, logo, opts, copy_number=2)

    doc = pdfium.PdfDocument(out)
    page = doc[1].render(scale=200 / 72).to_pil().convert("RGB")
    W, H = page.size
    crop = page.crop((int(W * 0.40), 0, W, int(H * 0.185)))  # จบบรรทัดข้อความที่ 2 พอดี
    dest = HERE / "images"
    dest.mkdir(exist_ok=True)
    crop.save(dest / "sample_watermark.png", optimize=True)
    print("saved:", dest / "sample_watermark.png", crop.size)


if __name__ == "__main__":
    main()
