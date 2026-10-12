"""API จัดการไฟล์ PDF: อัปโหลด (หลายไฟล์) / รายการ / ลบ"""
from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pypdf import PdfReader

from .. import config, storage
from ..schemas import PageDim, PdfDoc
from ..stamping import PageInfo

router = APIRouter(prefix="/api/pdfs", tags=["pdfs"])


def _to_doc(m: storage.PdfMeta) -> PdfDoc:
    return PdfDoc(
        id=m.id, filename=m.filename, page_count=m.page_count, size_bytes=m.size_bytes,
        pages=[PageDim(**p) for p in m.pages],
    )


def _validate_pdf(content: bytes, name: str):
    if len(content) > config.MAX_PDF_BYTES:
        raise HTTPException(413, f"{name}: ใหญ่เกิน {config.MAX_PDF_BYTES} bytes")
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception:
        raise HTTPException(400, f"{name}: ไม่ใช่ไฟล์ PDF ที่อ่านได้")
    if reader.is_encrypted:
        raise HTTPException(400, f"{name}: ไฟล์ถูกเข้ารหัส (password) — ถอดรหัสก่อน")
    if len(reader.pages) == 0:
        raise HTTPException(400, f"{name}: ไม่มีหน้า")
    if len(reader.pages) > config.MAX_PAGES_PER_DOC:
        raise HTTPException(400, f"{name}: จำนวนหน้าเกิน {config.MAX_PAGES_PER_DOC}")


@router.post("", response_model=list[PdfDoc])
async def upload_pdfs(files: list[UploadFile]) -> list[PdfDoc]:
    """รับหลายไฟล์ PDF พร้อมกัน -> validate + บันทึก metadata (ขนาดหน้า) คืนรายการ"""
    out: list[PdfDoc] = []
    for f in files:
        ext = Path(f.filename or "doc.pdf").suffix.lower()
        if ext not in config.ALLOWED_PDF_EXT:
            raise HTTPException(400, f"{f.filename}: ต้องเป็น .pdf")
        content = await f.read()
        _validate_pdf(content, f.filename or "doc.pdf")
        pages = _pages_of(content)
        meta = storage.save_pdf(content, f.filename or "doc.pdf", pages)
        out.append(_to_doc(meta))
    return out


def _pages_of(content: bytes):
    """อ่านขนาดหน้าจาก bytes โดยไม่เขียนลงดิสก์ก่อน"""
    reader = PdfReader(io.BytesIO(content))
    infos = []
    for idx, page in enumerate(reader.pages, start=1):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        if (page.rotation or 0) in (90, 270):
            w, h = h, w
        infos.append(type("P", (), {"index": idx, "width_pt": w, "height_pt": h})())
    return infos


@router.get("", response_model=list[PdfDoc])
async def get_pdfs() -> list[PdfDoc]:
    return [_to_doc(m) for m in storage.list_pdfs()]


@router.get("/{cid}", response_model=PdfDoc)
async def get_pdf(cid: str) -> PdfDoc:
    m = storage.get_pdf(cid)
    if not m:
        raise HTTPException(404, "ไม่พบ PDF")
    return _to_doc(m)


@router.delete("/{cid}")
async def remove_pdf(cid: str) -> dict[str, bool]:
    if not storage.delete_pdf(cid):
        raise HTTPException(404, "ไม่พบ PDF")
    return {"deleted": True}
