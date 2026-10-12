"""render — rasterize หน้าที่ stamp แล้วเป็น PNG ด้วย pypdfium2 (preview ตรงกับไฟล์จริง)"""
from __future__ import annotations

import io

import pypdfium2 as pdfium


def page_to_png(pdf_bytes: bytes, page_index: int, dpi: int = 110) -> bytes:
    """แปลงหน้า (1-based) ของ pdf_bytes เป็น PNG bytes

    ตัวอย่าง: page_to_png(stamped_pdf, 1, dpi=110)
    """
    doc = pdfium.PdfDocument(pdf_bytes)
    n = len(doc)
    if not 1 <= page_index <= n:
        raise ValueError(f"page_index {page_index} นอกช่วง 1-{n}")
    bmp = doc[page_index - 1].render(scale=dpi / 72.0)
    pil = bmp.to_pil().convert("RGB")
    buf = io.BytesIO()
    pil.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
