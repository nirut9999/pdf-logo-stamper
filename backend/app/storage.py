"""storage — บันทึกไฟล์ logo/PDF ที่อัปโหลด พร้อม metadata (json sidecar) ใต้ DATA_DIR"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import config


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------- LOGO ----------------
@dataclass
class LogoMeta:
    id: str
    filename: str
    width_px: int
    height_px: int
    path: str  # ในรูป path จริง (เก็บเฉพาะชื่อไฟล์ก็พอ เพราะ dir ถูกล็อก)

    def url(self) -> str:
        return f"/api/logos/{self.id}/image"


def save_logo(content: bytes, original_name: str, width_px: int, height_px: int) -> LogoMeta:
    """บันทึกโลโก้ลงดิสก์ คืน LogoMeta

    ตัวอย่าง: save_logo(png_bytes, 'brand.png', 512, 128)
    """
    cid = _new_id()
    ext = Path(original_name).suffix.lower() or ".png"
    config.LOGO_DIR.mkdir(parents=True, exist_ok=True)
    fpath = config.LOGO_DIR / f"{cid}{ext}"
    fpath.write_bytes(content)
    meta = LogoMeta(cid, original_name, width_px, height_px, str(fpath))
    (config.LOGO_DIR / f"{cid}.json").write_text(json.dumps(asdict(meta), ensure_ascii=False))
    return meta


def list_logos() -> list[LogoMeta]:
    out: list[LogoMeta] = []
    for jp in sorted(config.LOGO_DIR.glob("*.json")):
        try:
            out.append(LogoMeta(**json.loads(jp.read_text())))
        except Exception:
            continue
    return out


def get_logo(cid: str) -> LogoMeta | None:
    jp = config.LOGO_DIR / f"{cid}.json"
    if not jp.exists():
        return None
    return LogoMeta(**json.loads(jp.read_text()))


def delete_logo(cid: str) -> bool:
    jp = config.LOGO_DIR / f"{cid}.json"
    if not jp.exists():
        return False
    meta = LogoMeta(**json.loads(jp.read_text()))
    Path(meta.path).unlink(missing_ok=True)
    jp.unlink(missing_ok=True)
    return True


# ---------------- PDF ----------------
@dataclass
class PdfMeta:
    id: str
    filename: str
    page_count: int
    size_bytes: int
    path: str
    pages: list[dict] = field(default_factory=list)  # [{index,width_pt,height_pt}]


def save_pdf(content: bytes, original_name: str, pages: list) -> PdfMeta:
    """บันทึก PDF + ขนาดหน้า (list[PageInfo]) ลงดิสก์"""
    cid = _new_id()
    config.PDF_DIR.mkdir(parents=True, exist_ok=True)
    fpath = config.PDF_DIR / f"{cid}.pdf"
    fpath.write_bytes(content)
    meta = PdfMeta(
        id=cid,
        filename=original_name,
        page_count=len(pages),
        size_bytes=len(content),
        path=str(fpath),
        pages=[{"index": p.index, "width_pt": p.width_pt, "height_pt": p.height_pt} for p in pages],
    )
    (config.PDF_DIR / f"{cid}.json").write_text(json.dumps(asdict(meta), ensure_ascii=False))
    return meta


def get_pdf(cid: str) -> PdfMeta | None:
    jp = config.PDF_DIR / f"{cid}.json"
    if not jp.exists():
        return None
    return PdfMeta(**json.loads(jp.read_text()))


def list_pdfs() -> list[PdfMeta]:
    out: list[PdfMeta] = []
    for jp in sorted(config.PDF_DIR.glob("*.json")):
        try:
            out.append(PdfMeta(**json.loads(jp.read_text())))
        except Exception:
            continue
    return out


def delete_pdf(cid: str) -> bool:
    jp = config.PDF_DIR / f"{cid}.json"
    if not jp.exists():
        return False
    meta = PdfMeta(**json.loads(jp.read_text()))
    Path(meta.path).unlink(missing_ok=True)
    jp.unlink(missing_ok=True)
    return True
