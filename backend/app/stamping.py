"""stamp logic หลัก — วาง watermark (โลโก้ + ข้อความสำเนา) มุมขวาบนของทุกหน้า PDF

หลักการ:
- PDF ใช้ origin มุมล่างซ้าย หน่วย point (pt) โดย 1 mm = 72/25.4 pt ≈ 2.8346 pt
- "มุมขวาบน" = ขอบบนลบ margin_top, ขอบขวาลบ margin_right
- watermark = กลุ่ม (โลโก้ + ข้อความสีแดงใต้โลโก้) ตรึงด้วย anchor มุมขวาบนของกล่อง
  แล้ว rotate รอบ anchor ได้ (ค่าบวก = ตามเข็ม) — เป็นการ merge overlay ทับหน้าเดิม
  ไม่ได้แก้ไขเนื้อหาเดิมของ PDF
- หน้าที่มี /Rotate จะ normalize ด้วย transfer_rotation_to_content() ก่อน
  เพื่อให้ anchor มุมขวาบนตรงกับภาพที่ผู้ใช้เห็นจริง

ตัวอย่าง (A4 = 595.28 x 841.89 pt, โลโก้กว้าง 30 mm สัดส่วน 2:1, ข้อความ auto):
    anchor      = (595.28-8*2.8346, 841.89-8*2.8346) = (572.6, 819.4)
    logo        = 85.0 x 42.5 pt วาดที่ (-85.0, -42.5) เทียบ anchor
    text_size   = 30*0.16 = 4.8 mm = 13.6 pt, gap = 4.1 pt
    baseline    = -42.5 - 4.1 - 0.72*13.6 = -56.4 เทียบ anchor
    หมึกทั้งกลุ่มอยู่ใต้ anchor ซ้อนเป็นชั้น (overlay) บนหน้าเดิม
"""
from __future__ import annotations

import io
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

MM_TO_PT: float = 72.0 / 25.4
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
TEXT_GAP_RATIO = 0.30      # ระยะห่างโลโก้→ข้อความ เทียบกับความสูงตัวอักษร
CAP_HEIGHT_RATIO = 0.72    # ความสูงตัวพิมพ์ใหญ่เทียบ fontsize (Helvetica)
DEFAULT_TEXT_SIZE_RATIO = 0.16  # auto text height = logo_width_mm * ratio
TEXT_FONT = "Helvetica-Bold"


@dataclass(frozen=True)
class StampOptions:
    """พารามิเตอร์ watermark (หน่วย mm/องศา เพื่อให้คุมงานพิมพ์ได้ตรง)

    ตัวอย่าง: StampOptions(logo_width_mm=32, opacity=0.6, rotation_degrees=12,
                        include_text=True, text_template="COPY No.{n}")
    """

    logo_width_mm: float = 30.0          # ความกว้างโลโก้บนหน้า (ย่อ/ขยาย)
    margin_top_mm: float = 8.0           # ระยะจากขอบบน
    margin_right_mm: float = 8.0         # ระยะจากขอบขวา
    opacity: float = 1.0                 # 0.0–1.0 (1 = ทึบ, 0.5 = มองทะลุแบบ watermark)
    logo_height_mm: float | None = None  # ถ้าใส่ = ไม่คงสัดส่วน (บังคับสูง)
    rotation_degrees: float = 0.0        # เอียงทั้งกลุ่ม รอบ anchor ขวาบน (บวก = ตามเข็ม)
    include_text: bool = False           # วางข้อความใต้โลโก้ด้วยไหม
    text_template: str = "COPY No.{n}"   # {n} = เลขสำเนา (copy_number)
    text_color: str = "#CC0000"          # สีข้อความ (default แดง)
    text_size_mm: float | None = None    # ความสูงข้อความ; None = auto = กว้าง*0.16

    def validate(self) -> None:
        if self.logo_width_mm <= 0:
            raise ValueError("logo_width_mm ต้องมากกว่า 0")
        if self.margin_top_mm < 0 or self.margin_right_mm < 0:
            raise ValueError("margin ต้องไม่ติดลบ")
        if not 0.0 < self.opacity <= 1.0:
            raise ValueError("opacity ต้องอยู่ในช่วง (0.0, 1.0]")
        if abs(self.rotation_degrees) > 180:
            raise ValueError("rotation_degrees ต้องอยู่ระหว่าง -180 ถึง 180")
        if self.include_text:
            if "{n}" not in self.text_template:
                raise ValueError("text_template ต้องมี placeholder {n}")
            if not self.text_template.strip():
                raise ValueError("text_template ห้ามว่าง")
            if not HEX_COLOR_RE.match(self.text_color):
                raise ValueError(f"text_color ต้องเป็น #RRGGBB: {self.text_color}")
            if self.text_size_mm is not None and self.text_size_mm <= 0:
                raise ValueError("text_size_mm ต้องมากกว่า 0")


@dataclass
class PageInfo:
    index: int            # 1-based
    width_pt: float
    height_pt: float


def _mm(v: float) -> float:
    return v * MM_TO_PT


def resolve_text(template: str, copy_number: int) -> str:
    """แทนที่ {n} ใน template ด้วยเลขสำเนา

    ตัวอย่าง: resolve_text("COPY No.{n}", 7) -> "COPY No.7"
    """
    return template.replace("{n}", str(copy_number))


def _logo_size_pt(logo_path: Path, opts: StampOptions, page_w: float, page_h: float) -> tuple[float, float]:
    """คำนวณขนาดโลโก้ (pt) คงสัดส่วนจากภาพต้นฉบับ (mask='auto' ใช้ alpha ของ PNG)"""
    from PIL import Image

    with Image.open(logo_path) as im:
        iw, ih = im.size
    if iw <= 0 or ih <= 0:
        raise ValueError("ภาพโลโก้ขนาดไม่ถูกต้อง")
    w = _mm(opts.logo_width_mm)
    h = _mm(opts.logo_height_mm) if opts.logo_height_mm is not None else w * ih / iw
    # clamp ไม่ให้ใหญ่เกินหน้า (กัน watermark กลืนทั้งหน้า)
    max_w = page_w - _mm(opts.margin_right_mm) - 2.0
    max_h = page_h - _mm(opts.margin_top_mm) - 2.0
    scale = min(1.0, max_w / w if w > 0 else 1.0, max_h / h if h > 0 else 1.0)
    return w * scale, h * scale


def _text_metrics(opts: StampOptions, logo_w_mm: float, text: str) -> tuple[float, float]:
    """คืน (font size pt, ความกว้างข้อความ pt) — auto size = logo_width * ratio

    ตัวอย่าง: text 'COPY No.1' ที่ 30mm logo -> fs=13.6pt, tw≈56pt (ประมาณ 0.55*fs/char)
    """
    size_mm = opts.text_size_mm if opts.text_size_mm else max(2.2, logo_w_mm * DEFAULT_TEXT_SIZE_RATIO)
    fs = _mm(size_mm)
    from reportlab.pdfbase import pdfmetrics
    tw = pdfmetrics.stringWidth(text, TEXT_FONT, fs)
    return fs, tw


def _build_overlay_page(
    page_w: float, page_h: float, logo_path: Path, opts: StampOptions, text: str | None
):
    """สร้างหน้า PDF overlay 1 หน้า (ขนาด=page): กลุ่มโลโก้(+ข้อความ) เอียงรอบจุดศูนย์กลาง
    โดยมุมขวาบนของกล่อง (ที่หมุนแล้ว) ยังคงตรึงที่ anchor (page_w-margin_right, page_h-margin_top)

    local coords: กลุ่มทั้งก้อน center=(0,0), ขอบนอกสุด = (±hw, ±hh); anchor เดิม = ขวาบนของกลุ่ม
    deg=0 จะให้ผลตรงกับตำแหน่งแบบไม่หมุนทุกประการ (backward-compatible)
    """
    lw, lh = _logo_size_pt(logo_path, opts, page_w, page_h)
    ax = page_w - _mm(opts.margin_right_mm)   # anchor ขวาบน (PDF origin ล่าง-ซ้าย)
    ay = page_h - _mm(opts.margin_top_mm)

    # metrics ของข้อความ (ถ้ามี)
    fs = tw = gap = cap = desc = 0.0
    if opts.include_text and text:
        fs, tw = _text_metrics(opts, opts.logo_width_mm, text)
        gap = fs * TEXT_GAP_RATIO
        cap = fs * CAP_HEIGHT_RATIO
        desc = fs * 0.22  # ส่วนลงใต้ baseline (เช่น p, g)
    bw = max(lw, tw) if opts.include_text else lw
    bh = (lh + gap + cap + desc) if opts.include_text else lh
    hw, hh = bw / 2.0, bh / 2.0

    # pivot รอบ center ของกลุ่ม -> ครึ่งพื้นที่หลังจากเอียง (บวก=ตามเข็ม)
    t = abs(opts.rotation_degrees) * math.pi / 180.0
    exx = hw * math.cos(t) + hh * math.sin(t)
    exy = hw * math.sin(t) + hh * math.cos(t)
    pcx, pcy = ax - exx, ay - exy

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    c.saveState()
    try:
        c.setFillAlpha(opts.opacity)
        c.setStrokeAlpha(opts.opacity)
    except Exception:  # reportlab เก่ามากที่ไม่มี alpha
        pass
    c.translate(pcx, pcy)
    if opts.rotation_degrees:
        # reportlab rotate = ทวนเข็ม; ใช้ลบเพื่อให้ 'บวก = ตามเข็ม' ตามสัญชาตญาณผู้ใช้
        c.rotate(-opts.rotation_degrees)
    # วาดในพิกัด local: ขอบขวาบนของกลุ่ม = (hw, hh) จะไปตกที่ anchor
    c.drawImage(ImageReader_safe(logo_path), -lw / 2.0, hh - lh, width=lw, height=lh, mask="auto")
    if opts.include_text and text:
        c.setFillColor(HexColor(opts.text_color))
        # drawImage(mask=...) รีเซ็ต alpha ภายในของ reportlab เป็น 1 -> ต้องสั่งซ้ำก่อนวาดข้อความ
        try:
            c.setFillAlpha(opts.opacity)
            c.setStrokeAlpha(opts.opacity)
        except Exception:
            pass
        c.setFont(TEXT_FONT, fs)
        c.drawCentredString(0.0, -hh + desc, text)  # baseline: วัดจากขอบล่างของกลุ่ม
    c.restoreState()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def ImageReader_safe(logo_path: Path):  # noqa: N802 — helper name สั้น ชัด
    """wrap reportlab ImageReader (รองรับ PNG alpha)"""
    from reportlab.lib.utils import ImageReader
    return ImageReader(str(logo_path))


def resolve_page_indices(scope: str, page_count: int) -> list[int]:
    """แปลง page_scope ('all' | 'first' | '1-3,5') เป็น list เลขหน้า 1-based

    ตัวอย่าง: resolve_page_indices('1-3,5', 6) -> [1,2,3,5]
              resolve_page_indices('first', 4) -> [1]
    """
    scope = (scope or "all").strip().lower()
    if scope in ("all", ""):
        return list(range(1, page_count + 1))
    if scope in ("first", "1"):
        return [1]
    out: set[int] = set()
    try:
        for part in scope.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, _, b = part.partition("-")
                start = int(a) if a else 1
                end = int(b) if b else page_count
                out.update(range(start, end + 1))
            else:
                out.add(int(part))
    except ValueError:
        raise ValueError(f"page_scope ไม่ถูกต้อง: '{scope}' (ตัวอย่างที่ถูก: 1-3,5)")
    bad = [p for p in out if not 1 <= p <= page_count]
    if bad:
        raise ValueError(f"เลขหน้านอกช่วง 1-{page_count}: {sorted(bad)}")
    return sorted(out)


def stamp_pdf(
    pdf_path: Path,
    logo_path: Path,
    opts: StampOptions,
    page_indices: Iterable[int] | None = None,  # 1-based; None = ทุกหน้า
    copy_number: int = 1,                        # เลขสำเนา สำหรับ {n}
    out_path: Path | None = None,
) -> bytes:
    """วาง watermark (โลโก้+ข้อความ) ทับมุมขวาบนทุกหน้าที่เลือก — ไม่แก้เนื้อหาเดิม

    คืน bytes ของ PDF ผลลัพธ์ (เขียนลง out_path ถ้ากำหนด)

    ตัวอย่าง: stamp_pdf(pdf, logo, StampOptions(include_text=True), copy_number=3)
              -> ทุกหน้ามีโลโก้ + 'COPY No.3' สีแดงใต้โลโก้
    """
    opts.validate()
    text = resolve_text(opts.text_template, copy_number) if opts.include_text else None
    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        raise ValueError("ไฟล์ PDF ถูกเข้ารหัส — ต้องถอดรหัสก่อน")
    targets = set(page_indices) if page_indices is not None else None

    overlay_cache: dict[tuple[float, float], object] = {}
    writer = PdfWriter()
    for idx, page in enumerate(reader.pages, start=1):
        writer.add_page(page)
        wp = writer.pages[-1]  # ทำงานบนหน้าที่ attach เข้า writer แล้ว (เลี่ยง deprecation)
        if targets is None or idx in targets:
            try:
                wp.transfer_rotation_to_content()  # normalize /Rotate ให้ anchor ตรงภาพที่เห็น
            except Exception:
                pass
            pw = float(wp.mediabox.width)
            ph = float(wp.mediabox.height)
            key = (round(pw, 1), round(ph, 1))
            if key not in overlay_cache:
                overlay_cache[key] = _build_overlay_page(pw, ph, logo_path, opts, text)
            wp.merge_page(overlay_cache[key])

    out = io.BytesIO()
    writer.write(out)
    data = out.getvalue()
    if out_path is not None:
        Path(out_path).write_bytes(data)
    return data


def make_copies(
    pdf_path: Path,
    logo_path: Path,
    opts: StampOptions,
    n_copies: int,
    page_indices: Iterable[int] | None = None,
) -> list[tuple[int, bytes]]:
    """สร้าง n_copies ชุด — ไฟล์ละ 1 เลขสำเนา (1..n) ฝัง {n} ในข้อความ

    คืน: [(copy_number, pdf_bytes), ...]
    ตัวอย่าง: make_copies(pdf, logo, opts, 200) -> 200 ไฟล์ COPY No.1..COPY No.200
    """
    if n_copies < 1:
        raise ValueError("n_copies ต้องอย่างน้อย 1")
    indices = list(page_indices) if page_indices is not None else None
    return [(i, stamp_pdf(pdf_path, logo_path, opts, page_indices=indices, copy_number=i))
            for i in range(1, n_copies + 1)]


def list_pages(pdf_path: Path) -> list[PageInfo]:
    """คืนขนาดหน้าที่ 'มองเห็นจริง' (pt) — สลับ กxย ตาม /Rotate โดยไม่แก้หน้า"""
    reader = PdfReader(str(pdf_path))
    infos: list[PageInfo] = []
    for idx, page in enumerate(reader.pages, start=1):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        if (page.rotation or 0) in (90, 270):
            w, h = h, w
        infos.append(PageInfo(idx, w, h))
    return infos
