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


# ---------------- PRESET (ชุดการตั้งค่าที่บันทึกไว้) ----------------
@dataclass
class PresetMeta:
    id: str
    name: str
    logo_id: str | None          # โลโก้ที่เลือกไว้ (อาจถูกลบไปแล้ว — apply แล้วเตือน)
    options: dict                # body 'options' ทั้งก้อนจาก API
    created_at: str
    updated_at: str


PRESET_DIR_NAME = "presets"


def _preset_dir():
    from . import config  # import ใน function — config resolve DATA_DIR จาก env ตอน import app ครั้งเดียว
    return config.PRESET_DIR


def save_preset(name: str, logo_id: str | None, options: dict, pid: str | None = None) -> PresetMeta:
    """บันทึก/อัปเดต preset — คืน metadata (id ใหม่หรือเดิมถ้า given pid)

    ตัวอย่าง: save_preset('งานสัญญาเช่า GPO', 'cb84', {'logo_width_mm': 28, 'copies': 50})
    """
    from datetime import datetime, timezone
    d = _preset_dir()
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cid = pid or _new_id()
    old = get_preset(cid) if pid else None
    meta = PresetMeta(cid, name.strip()[:120] or "preset", logo_id, options,
                      old.created_at if old else now, now)
    (d / f"{cid}.json").write_text(json.dumps(asdict(meta), ensure_ascii=False))
    return meta


def list_presets() -> list[PresetMeta]:
    d = _preset_dir()
    if not d.exists():
        return []
    out: list[PresetMeta] = []
    for jp in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            out.append(PresetMeta(**json.loads(jp.read_text())))
        except Exception:
            continue
    return out


def get_preset(cid: str) -> PresetMeta | None:
    jp = _preset_dir() / f"{cid}.json"
    if not jp.exists():
        return None
    return PresetMeta(**json.loads(jp.read_text()))


def delete_preset(cid: str) -> bool:
    jp = _preset_dir() / f"{cid}.json"
    if not jp.exists():
        return False
    jp.unlink()
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
