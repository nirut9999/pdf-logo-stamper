"""เทสต์ watermark composite — โลโก้ + ข้อความ COPY No.N สีแดง, rotation, copies, opacity"""
from __future__ import annotations

import io

import pypdfium2 as pdfium
import pytest
from PIL import Image
from pypdf import PdfReader

from app.stamping import (
    StampOptions, make_copies, resolve_page_indices, resolve_text, stamp_pdf,
)

DPI = 150
PX_MM = DPI / 25.4


def render(pdf_bytes: bytes, page_i: int = 0) -> Image.Image:
    doc = pdfium.PdfDocument(pdf_bytes)
    return doc[page_i].render(scale=DPI / 72.0).to_pil().convert("RGB")


def is_red(px) -> bool:
    r, g, b = px[:3]
    return r > 140 and g < 100 and b < 100


def red_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    """(left, top, right, bottom) ของพิกเซลแดง — None ถ้าไม่มี"""
    px = img.load()
    xs, ys = [], []
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if is_red(px[x, y]):
                xs.append(x); ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


# ---------- ข้อความ COPY No.N ----------

def test_text_template_resolves_copy_number():
    assert resolve_text("COPY No.{n}", 7) == "COPY No.7"
    assert resolve_text("ฉบับที่ {n}/10", 3) == "ฉบับที่ 3/10"


def test_copy_number_text_appears_in_pdf(two_page_pdf, blue_logo_path):
    """extract_text ต้องเห็น 'COPY No.3' ทุกหน้า (ไม่แก้เนื้อหาเดิม แต่ overlay มี text จริง)"""
    opts = StampOptions(logo_width_mm=30, include_text=True, text_template="COPY No.{n}")
    out = stamp_pdf(two_page_pdf, blue_logo_path, opts, copy_number=3)
    reader = PdfReader(io.BytesIO(out))
    assert len(reader.pages) == 2
    for page in reader.pages:
        txt = (page.extract_text() or "").replace(" ", "")
        assert "COPYNo.3" in txt, txt


def test_red_text_pixels_right_of_logo(two_page_pdf, blue_logo_path):
    """layout แนวนอน: กลุ่ม [โลโก้|gap|ข้อความ] ตรึงขวาบน — ข้อความแดงทางขวาของโลโก้"""
    opts = StampOptions(logo_width_mm=30, margin_top_mm=8, margin_right_mm=8, include_text=True)
    img = render(stamp_pdf(two_page_pdf, blue_logo_path, opts))
    W, H = img.size
    bb = red_bbox(img)
    assert bb, "ไม่พบข้อความแดงเลย"
    left, top, right, bot = bb
    anchor_x = W - round(8 * PX_MM)
    # ink ของ glyph ตัวสุดท้ายมี right side bearing — ต้อง 'ใกล้' แต่ 'ไม่เกิน' anchor
    assert right <= anchor_x + 2, f"ข้อความล้นเกิน anchor: {bb}"
    assert anchor_x - right <= 14, f"ข้อความต้องชิด anchor (bearing ≤~2.4mm): {bb}"
    # ข้อความต้องอยู่ครึ่งขวาของภาพเสมอ (โลโก้ 30mm+ข้อความ ≤60mm กลุ่มทั้งหมดทางขวา)
    assert left > W // 2, f"ข้อความควรอยู่ฝั่งขวา: {bb} (W={W})"
    # ฝั่งซ้ายของภาพ (ตำแหน่งเนื้อหาเดิม) ต้องไม่มี red ink
    band = img.crop((0, 0, W // 2, H))
    px = band.load()
    reds_left = sum(1 for y in range(band.size[1]) for x in range(band.size[0]) if is_red(px[x, y]))
    assert reds_left == 0, "ฝั่งซ้ายต้องไม่มีข้อความ"


def test_logo_left_of_text_order(two_page_pdf, blue_logo_path):
    """ตรวจลำดับ: blue ink ต้องเริ่ม (leftmost) ก่อน red ink — 'logo หน้าตัวหนังสือ'"""
    opts = StampOptions(logo_width_mm=30, include_text=True)
    img = render(stamp_pdf(two_page_pdf, blue_logo_path, opts))
    px = img.load()

    def first_x(pred):
        for x in range(img.size[0]):
            for y in range(round(8 * PX_MM), round(24 * PX_MM)):
                if pred(px[x, y]):
                    return x
        return img.size[0]

    def is_blue(p):
        r, g, b = p[:3]
        return b > 140 and r < 110 and g < 150
    x_blue = first_x(is_blue)
    x_red = first_x(is_red)
    assert x_blue < x_red, f"โลโก้ (x={x_blue}) ต้องอยู่ซ้ายของข้อความ (x={x_red})"


def test_text_size_independent_of_logo(two_page_pdf, blue_logo_path):
    """text ใหญ่ขึ้น -> ink กว้างขึ้น; ขวาบนกลุ่มยังตรึง anchor + ขอบบนโลโก้คงที่
    (โลโก้ถูกดันซ้ายเมื่อกลุ่มกว้างขึ้น = พฤติกรรมถูกต้องของ anchor-right layout)"""
    small = StampOptions(logo_width_mm=30, include_text=True, text_size_mm=4)
    big = StampOptions(logo_width_mm=30, include_text=True, text_size_mm=9)
    img_s = render(stamp_pdf(two_page_pdf, blue_logo_path, small))
    img_b = render(stamp_pdf(two_page_pdf, blue_logo_path, big))

    def red_width(img):
        bb = red_bbox(img)
        return (bb[2] - bb[0]) if bb else 0
    assert red_width(img_b) > red_width(img_s) * 1.5, "ขนาดข้อความต้องปรับได้อิสระ"

    W = img_s.size[0]
    anchor_x = W - round(8 * PX_MM)
    for img, tag in ((img_s, "small"), (img_b, "big")):
        bb = red_bbox(img)
        assert anchor_x - bb[2] <= 14, f"{tag}: ขวาข้อความต้องตรึงที่ anchor"

    def blue_x_extent(img):
        """ขอบซ้าย-ขวา ของ ink โลโก้ (น้ำเงิน) ในแถวบนขวา"""
        px = img.load()
        xs = []
        for x in range(W - 1, 0, -1):
            for y in range(round(6 * PX_MM), round(24 * PX_MM)):
                r, g, b = px[x, y][:3]
                if b > 140 and r < 110 and g < 150:
                    xs.append(x)
                    break
        return (max(xs), min(xs)) if xs else (0, 0)
    right_s, left_s = blue_x_extent(img_s)
    right_b, left_b = blue_x_extent(img_b)
    assert abs(right_s - right_b) > 20, "โลโก้ต้องถูกดันซ้ายเมื่อข้อความใหญ่ขึ้น (กลุ่มกว้างขึ้น)"
    assert right_b < right_s
    # ขอบบนโลโก้คงที่ (top-aligned ที่ margin_top) ทั้งสองกรณี
    def blue_top(img):
        px = img.load()
        for y in range(round(12 * PX_MM)):
            for x in range(img.size[0] // 2, img.size[0]):
                r, g, b = px[x, y][:3]
                if b > 140 and r < 110 and g < 150:
                    return y
        return 12 * PX_MM
    assert round(6 * PX_MM) <= blue_top(img_s) <= round(10 * PX_MM)
    assert round(6 * PX_MM) <= blue_top(img_b) <= round(10 * PX_MM)


def test_sarabun_font_draws_thai(two_page_pdf, blue_logo_path):
    """Sarabun-Bold ต้องวาด 'ฉบับที่ {n}' ภาษาไทยได้ (extract text + ink จริง)"""
    opts = StampOptions(logo_width_mm=30, include_text=True, text_template="ฉบับที่ {n}",
                        text_font="Sarabun-Bold")
    out = stamp_pdf(two_page_pdf, blue_logo_path, opts, copy_number=5)
    from pypdf import PdfReader
    import io
    t = (PdfReader(io.BytesIO(out)).pages[0].extract_text() or "")
    assert "ฉบับที่ 5" in t, t
    img = render(out)
    assert red_bbox(img), "ต้องมี ink ข้อความไทย"


def test_helvetica_rejects_thai_glyphs(two_page_pdf, blue_logo_path):
    """Helvetica ไม่มีไทย -> 400 พร้อมแนะนำ Sarabun"""
    opts = StampOptions(logo_width_mm=30, include_text=True, text_template="ฉบับที่ {n}",
                        text_font="Helvetica-Bold")
    import pytest
    with pytest.raises(ValueError):
        stamp_pdf(two_page_pdf, blue_logo_path, opts)


def test_unknown_font_raises(two_page_pdf, blue_logo_path):
    import pytest
    with pytest.raises(ValueError):
        stamp_pdf(two_page_pdf, blue_logo_path, StampOptions(include_text=True, text_font="Comic-Neue"))


def test_custom_text_color(two_page_pdf, blue_logo_path):
    opts = StampOptions(logo_width_mm=40, include_text=True, text_color="#006600")
    img = render(stamp_pdf(two_page_pdf, blue_logo_path, opts))
    px = img.load()
    W, _ = img.size
    greens = 0
    # ข้อความอยู่แถวบนขวา — scan มุมขวาบนทั้งแถบ
    for y in range(round(6 * PX_MM), round(24 * PX_MM)):
        for x in range(round(150 * PX_MM), W - round(4 * PX_MM)):
            r, g, b = px[x, y][:3]
            if g > 90 and r < 90 and b < 90:
                greens += 1
    assert greens > 100, "ข้อความควรเป็นสีเขียวตาม text_color"


# ---------- copies หลายชุด ----------

def test_make_copies_unique_numbers_each_file(two_page_pdf, blue_logo_path):
    opts = StampOptions(logo_width_mm=30, include_text=True)
    copies = make_copies(two_page_pdf, blue_logo_path, opts, n_copies=3)
    assert [n for n, _ in copies] == [1, 2, 3]
    for n, data in copies:
        reader = PdfReader(io.BytesIO(data))
        assert len(reader.pages) == 2  # จำนวนหน้าต้นฉบับคงเดิมทุกสำเนา
        txt = (reader.pages[0].extract_text() or "").replace(" ", "")
        assert f"COPYNo.{n}" in txt, f"สำเนา {n} ต้องมีเลขของตัวเอง: {txt}"


def test_make_copies_rejects_zero(two_page_pdf, blue_logo_path):
    with pytest.raises(ValueError):
        make_copies(two_page_pdf, blue_logo_path, StampOptions(include_text=True), n_copies=0)


# ---------- การเอียง (rotation) ----------

def test_rotation_changes_vertical_extent(two_page_pdf, logo_path):
    """โลโก้แบนๆ (200x80) เอียง 40° -> กินแนวตั้งมากกว่าเดิมชัดเจน (ยืนยันว่า rotate จริง)"""
    flat = render(stamp_pdf(two_page_pdf, logo_path, StampOptions(logo_width_mm=40, rotation_degrees=0)))
    tilt = render(stamp_pdf(two_page_pdf, logo_path, StampOptions(logo_width_mm=40, rotation_degrees=40)))
    fb, tb = red_bbox(flat), red_bbox(tilt)
    assert fb and tb
    h_flat = fb[3] - fb[1]
    h_tilt = tb[3] - tb[1]
    assert h_tilt > h_flat * 1.8, f"rotate ควรขยายแนวตั้ง: flat={h_flat} tilt={h_tilt}"
    # anchor ขวาบนคงที่: ขอบขวาของ bbox ทั้งสองต้องใกล้เคียงกัน
    W = flat.size[0]
    assert abs(fb[2] - tb[2]) <= 6, "ขอบขวา (anchor) ต้องไม่เลื่อน"


def test_negative_rotation_counter_clockwise(two_page_pdf, logo_path):
    """+องศา = ตามเข็ม (เอียงลงทางขวา), -องศา = ทวนเข็ม — ตรวจจากทิศการไหลของหมึก"""
    def tilt_sign(img: Image.Image) -> float:
        bbox = red_bbox(img)
        assert bbox
        left, top, right, bot = bbox
        h = bot - top
        px = img.load()

        def mean_x_at(y):
            xs = [x for x in range(right - 6, left - 1, -1) if is_red(px[x, y])]
            return sum(xs) / len(xs) if xs else None
        tx, bx = mean_x_at(top + int(h * 0.15)), mean_x_at(bot - int(h * 0.15))
        return (tx - bx) if (tx and bx) else 0.0

    cw = render(stamp_pdf(two_page_pdf, logo_path, StampOptions(logo_width_mm=40, rotation_degrees=25)))
    ccw = render(stamp_pdf(two_page_pdf, logo_path, StampOptions(logo_width_mm=40, rotation_degrees=-25)))
    s_cw, s_ccw = tilt_sign(cw), tilt_sign(ccw)
    assert s_cw < -5 < s_ccw, f"ทิศเอียงผิด: cw={s_cw:.1f} ccw={s_ccw:.1f}"


# ---------- opacity ของข้อความ (มองทะลุ) ----------

def test_text_opacity_transparent(two_page_pdf, blue_logo_path):
    """opacity 0.35 -> หมึกข้อความต้องเจือขาวชัด (เฉลี่ย g ของพิกเซลที่ไม่ใช่พื้นขาว)"""
    solid = render(stamp_pdf(two_page_pdf, blue_logo_path,
                             StampOptions(logo_width_mm=30, include_text=True, opacity=1.0)))
    faint = render(stamp_pdf(two_page_pdf, blue_logo_path,
                             StampOptions(logo_width_mm=30, include_text=True, opacity=0.35)))
    def avg_green_of_ink(img):
        W, _ = img.size
        # band เฉพาะโซนข้อความ (ขวาของโลโก้): text auto ~20mm กว้าง ตรึงขวาที่ 8mm
        band = img.crop((W - round(23 * PX_MM), round(7 * PX_MM), W - round(2 * PX_MM), round(22 * PX_MM)))
        px = band.load()
        vals = [px[x, y][1] for y in range(band.size[1]) for x in range(band.size[0])
                if any(c < 245 for c in px[x, y])]  # ink เท่านั้น
        return sum(vals) / len(vals) if vals else -1
    gs, gf = avg_green_of_ink(solid), avg_green_of_ink(faint)
    assert gs >= 0 and gf >= 0, "ต้องพบหมึกข้อความทั้งสองภาพ"
    assert gf > gs + 50, f"ข้อความจางต้องเจือขาว: solid_g={gs:.0f} faint_g={gf:.0f}"


# ---------- validation ----------

def test_invalid_text_options_raise(two_page_pdf, blue_logo_path):
    with pytest.raises(ValueError):
        stamp_pdf(two_page_pdf, blue_logo_path, StampOptions(include_text=True, text_template="COPY No."))
    with pytest.raises(ValueError):
        stamp_pdf(two_page_pdf, blue_logo_path, StampOptions(include_text=True, text_color="red"))
    with pytest.raises(ValueError):
        stamp_pdf(two_page_pdf, blue_logo_path, StampOptions(rotation_degrees=181))


def test_resolve_page_indices_bad_format_raises():
    with pytest.raises(ValueError):
        resolve_page_indices("abc", 5)
