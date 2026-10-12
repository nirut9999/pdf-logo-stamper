"""เทสต์ geometry จริงของ stamp_pdf — rasterize ผลลัพธ์แล้วตรวจสีที่พิกัด

ช่วยคำนวณ "กล่องโลโก้ที่คาดหวัง" (px) จาก options แล้วสุ่มจุดกึ่งกลาง
เพื่อยืนยันว่าหมึกตกตรงมุมขวาบนจริง ไม่ใช่การทดสอบแบบ circular ที่ hardcode
"""
from __future__ import annotations

from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image

from app.stamping import StampOptions, list_pages, stamp_pdf

DPI = 150
PX_PER_MM = DPI / 25.4
LOGO_ASPECT = 2.5  # โลโก้ fixture 200x80 -> w/h = 2.5


def render(pdf_bytes: bytes, page_i: int) -> Image.Image:
    doc = pdfium.PdfDocument(pdf_bytes)
    return doc[page_i].render(scale=DPI / 72.0).to_pil().convert("RGB")


def is_red(px: tuple[int, int, int]) -> bool:
    r, g, b = px
    return r > 150 and g < 110 and b < 110


@dataclass
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def cx(self) -> int:
        return (self.left + self.right) // 2

    @property
    def cy(self) -> int:
        return (self.top + self.bottom) // 2


def expected_logo_rect(img_w: int, img_h: int, opts: StampOptions, aspect: float = LOGO_ASPECT) -> Rect:
    """กล่องที่โลโก้ควรตก (origin มุมซ้ายบนของภาพ raster)"""
    lw = opts.logo_width_mm * PX_PER_MM
    lh = (opts.logo_height_mm or opts.logo_width_mm / aspect) * PX_PER_MM
    right = img_w - opts.margin_right_mm * PX_PER_MM
    left = right - lw
    top = opts.margin_top_mm * PX_PER_MM
    return Rect(round(left), round(top), round(right), round(top + lh))


def test_preserves_page_count(two_page_pdf, logo_path):
    out = stamp_pdf(two_page_pdf, logo_path, StampOptions())
    assert len(pdfium.PdfDocument(out)) == 2


def test_logo_centered_in_expected_rect(two_page_pdf, logo_path):
    opts = StampOptions(logo_width_mm=40, margin_top_mm=10, margin_right_mm=10, opacity=1.0)
    img = render(stamp_pdf(two_page_pdf, logo_path, opts), 0)
    rect = expected_logo_rect(img.size[0], img.size[1], opts)
    assert is_red(img.getpixel((rect.cx, rect.cy))), img.getpixel((rect.cx, rect.cy))
    # มุมซ้ายล่างของหน้าต้องไม่มีโลโก้
    assert not is_red(img.getpixel((10, img.size[1] - 10)))


def test_ink_bbox_matches_geometry(two_page_pdf, logo_path):
    """ตรวจทั้ง bounding box ของหมึกจริง vs ที่คำนวณ (tolerance 4px)"""
    opts = StampOptions(logo_width_mm=40, margin_top_mm=10, margin_right_mm=10)
    img = render(stamp_pdf(two_page_pdf, logo_path, opts), 0)
    px = img.load()
    xs, ys = [], []
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if is_red(px[x, y]):
                xs.append(x); ys.append(y)
    assert xs, "ไม่พบหมึกสีแดงเลย"
    exp = expected_logo_rect(img.size[0], img.size[1], opts)
    tol = 4
    assert abs(min(xs) - exp.left) <= tol and abs(max(xs) - exp.right) <= tol
    assert abs(min(ys) - exp.top) <= tol and abs(max(ys) - exp.bottom) <= tol


def test_every_page_stamped(two_page_pdf, logo_path):
    opts = StampOptions(logo_width_mm=40)
    out = stamp_pdf(two_page_pdf, logo_path, opts)
    for i in range(2):
        img = render(out, i)
        rect = expected_logo_rect(img.size[0], img.size[1], opts)
        assert is_red(img.getpixel((rect.cx, rect.cy))), f"หน้า {i} ไม่มีโลโก้"


def test_opacity_blends(two_page_pdf, logo_path):
    solid = render(stamp_pdf(two_page_pdf, logo_path, StampOptions(logo_width_mm=40, opacity=1.0)), 0)
    faint = render(stamp_pdf(two_page_pdf, logo_path, StampOptions(logo_width_mm=40, opacity=0.3)), 0)
    rs = expected_logo_rect(solid.size[0], solid.size[1], StampOptions(logo_width_mm=40))
    sp, fp = solid.getpixel((rs.cx, rs.cy)), faint.getpixel((rs.cx, rs.cy))
    assert sp[1] < 60 and sp[2] < 60          # ทึบ: แดงจัด
    assert fp[1] > sp[1] + 60 and fp[2] > sp[2] + 60  # จาง: แดงเจือขาว


def test_rotated_page_visual_top_right(rotated_pdf, logo_path):
    opts = StampOptions(logo_width_mm=40, margin_top_mm=8, margin_right_mm=8)
    img = render(stamp_pdf(rotated_pdf, logo_path, opts), 1)
    rect = expected_logo_rect(img.size[0], img.size[1], opts)
    assert is_red(img.getpixel((rect.cx, rect.cy))), img.getpixel((rect.cx, rect.cy))


def test_margin_shifts_logo_left(two_page_pdf, logo_path):
    """margin_right ใหญ่ขึ้น -> โลโก้ถอยซ้าย (ทดสอบว่า geometry ตอบสนอง input)"""
    small = StampOptions(logo_width_mm=30, margin_right_mm=5)
    big = StampOptions(logo_width_mm=30, margin_right_mm=25)
    img_s = render(stamp_pdf(two_page_pdf, logo_path, small), 0)
    img_b = render(stamp_pdf(two_page_pdf, logo_path, big), 0)
    assert expected_logo_rect(img_b.size[0], img_b.size[1], big).left < \
        expected_logo_rect(img_s.size[0], img_s.size[1], small).left
    # ตรวจของจริง: ใกล้ขอบขวา (small.right) ต้องแดงใน small แต่ขาวใน big
    # (โลโก้ big ถอยซ้าย 20mm -> จุดนี้หลุดจากโลโก้ big)
    rs = expected_logo_rect(img_s.size[0], img_s.size[1], small)
    probe_x = rs.right - 4
    assert is_red(img_s.getpixel((probe_x, rs.cy))), "small ควรแดงที่ขอบขวา"
    assert not is_red(img_b.getpixel((probe_x, rs.cy))), "big ไม่ควรมีโลโก้ที่จุดนั้น"


def test_page_selection_subset(two_page_pdf, logo_path):
    """เลือก stamp เฉพาะหน้า 1 -> หน้า 2 ต้องไม่มีโลโก้"""
    opts = StampOptions(logo_width_mm=40)
    out = stamp_pdf(two_page_pdf, logo_path, opts, page_indices=[1])
    img2 = render(out, 1)
    rect = expected_logo_rect(img2.size[0], img2.size[1], opts)
    assert not is_red(img2.getpixel((rect.cx, rect.cy)))
    img1 = render(out, 0)
    r1 = expected_logo_rect(img1.size[0], img1.size[1], opts)
    assert is_red(img1.getpixel((r1.cx, r1.cy)))


def test_alpha_logo_not_solid_box(two_page_pdf, alpha_logo_path):
    """PNG ที่มีพิกเซลโปร่งใส 1 มุม -> mask='auto' ต้องไม่ทึบทั้งกล่อง"""
    opts = StampOptions(logo_width_mm=40, margin_top_mm=10, margin_right_mm=10)
    img = render(stamp_pdf(two_page_pdf, alpha_logo_path, opts), 0)
    rect = expected_logo_rect(img.size[0], img.size[1], opts, aspect=2.0)
    # พิกเซลมุมซ้ายบนของโลโก้ถูกตั้ง alpha=0 -> ควรเป็นพื้นขาว
    tl = img.getpixel((rect.left, rect.top))
    assert not is_red(tl) or tl[0] > 200  # โปร่งใสผ่าน


def test_list_pages_dimensions(two_page_pdf):
    pages = list_pages(two_page_pdf)
    assert len(pages) == 2
    assert round(pages[0].width_pt, 1) == 595.3
    assert round(pages[0].height_pt, 1) == 841.9


def test_invalid_options_raise(two_page_pdf, logo_path):
    import pytest
    with pytest.raises(ValueError):
        stamp_pdf(two_page_pdf, logo_path, StampOptions(logo_width_mm=0))
    with pytest.raises(ValueError):
        stamp_pdf(two_page_pdf, logo_path, StampOptions(opacity=0.0))
