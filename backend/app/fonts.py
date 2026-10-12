"""fonts — ลงทะเบียน font สำหรับวาดข้อความ watermark

- Type1 standard (Helvetica/Times/Courier) reportlab มีในbuilt-in — ไม่ต้อง embed
  แต่ *ไม่มีตัวอักษรไทย* -> ข้อความไทยจะขึ้นกล่องว่าง
- Sarabun (TTF, OFL license, bundled ใน app/fonts/) — รองรับไทย+ละติน embed ลง PDF
  source: https://github.com/google/fonts/tree/main/ofl/sarabun (v2.002 static)

ตัวอย่าง:
    from .fonts import text_width
    text_width("ฉบับที่ 3", "Sarabun-Bold", 14) -> 47.21 pt
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont

FONTS_DIR = Path(__file__).parent / "fonts"

# ชื่อ reportlab standard ที่ guarantee ว่ามี (Latin เท่านั้น)
STANDARD_FONTS: tuple[str, ...] = (
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique",
    "Times-Roman", "Times-Bold", "Times-Italic",
    "Courier", "Courier-Bold",
)

# bundled TTF: display label -> (font name, filename)
_BUNDLED: tuple[tuple[str, str], ...] = (
    ("Sarabun", "Sarabun-Regular.ttf"),
    ("Sarabun-Bold", "Sarabun-Bold.ttf"),
)

_registered: set[str] = set()


def _register_bundled() -> None:
    """embed TTF ที่ file มีจริง (ไม่ crash ถ้าหาย — UI จะเหลือแต่ standard fonts)"""
    for name, fname in _BUNDLED:
        if name in _registered:
            continue
        p = FONTS_DIR / fname
        if not p.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(p)))
            _registered.add(name)
        except Exception:
            continue


_register_bundled()

#: font ที่ใช้ได้ที่ frontend/Schema ควรแสดงเป็นตัวเลือก
ALLOWED_TEXT_FONTS: tuple[str, ...] = STANDARD_FONTS + tuple(
    n for n, _ in _BUNDLED if n in _registered
)


THAI_RE = re.compile(r"[\u0E00-\u0E7F]")


def font_supports_thai(font: str) -> bool:
    """ตรวจว่า font เป็น TTF ที่ embed ได้ (มีตัวไทย) — standard Type1 (Helvetica/Times/Courier) ไม่มี

    ตัวอย่าง: font_supports_thai("Sarabun-Bold") -> True
              font_supports_thai("Helvetica-Bold") -> False
    """
    try:
        f = pdfmetrics.getFont(font)
    except Exception:
        return False
    return f.__class__.__name__ == "TTFont"


def text_width(text: str, font: str, size_pt: float) -> float:
    """ความกว้างข้อความ (pt) — fallback เป็น Helvetica ถ้า font โหลดไม่สำเร็จ

    ตัวอย่าง: text_width("COPY No.3", "Helvetica-Bold", 13.6) -> ≈56.6 pt
    """
    try:
        pdfmetrics.getFont(font)
    except Exception:
        _register_bundled()
        try:
            pdfmetrics.getFont(font)
        except Exception:
            font = "Helvetica-Bold"
    return stringWidth(text, font, size_pt)


def has_font(font: str) -> bool:
    try:
        pdfmetrics.getFont(font)
        return True
    except Exception:
        return False
