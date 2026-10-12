"""API งานหลัก: preview watermark + stamp หลายไฟล์ × หลายสำเนา (COPY No.1..N)"""
from __future__ import annotations

import io
import os
import re
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from urllib.parse import quote

from .. import config, storage
from ..fonts import ALLOWED_TEXT_FONTS
from ..render import page_to_png
from ..schemas import PreviewRequest, StampRequest
from ..stamping import resolve_page_indices, stamp_pdf

router = APIRouter(prefix="/api", tags=["stamp"])


@router.get("/fonts")
async def get_fonts() -> list[str]:
    """รายชื่อ font ที่วาดข้อความได้ (Sarabun = รองรับภาษาไทย)"""
    return list(ALLOWED_TEXT_FONTS)

# ผลรวมไฟล์ส่งออกสูงสุด กัน zip ใหญ่เกินเหตุ (เช่น 10 pdf x 200 copies)
MAX_OUTPUT_FILES = int(os.getenv("MAX_OUTPUT_FILES", "1000"))


def _logo_path(logo_id: str) -> Path:
    m = storage.get_logo(logo_id)
    if not m or not Path(m.path).exists():
        raise HTTPException(404, f"ไม่พบโลโก้ id={logo_id}")
    return Path(m.path)


_UNSAFE_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f]+')  # อักขระต้องห้ามของ path/zip (ไทย+วรรณยุกต์ผ่านได้)


def _safe_stem(name: str) -> str:
    """ชื่อไฟล์สำหรับ zip/download — ตัดเฉพาะอักขระต้องห้าม คงภาษาไทย+วรรณยุกต์ครบ

    ตัวอย่าง: _safe_stem('รายงาน/เล่ม 2568.pdf') -> 'รายงาน_เล่ม 2568'
    """
    stem = Path(name).stem
    return _UNSAFE_RE.sub('_', stem)[:80].strip() or "doc"


def _disposition(name: str) -> str:
    """Content-Disposition แบบ RFC 5987 — รองรับชื่อไทย (header เป็น latin-1 ไม่ได้)

    ตัวอย่าง: _disposition('วิธี COPY_No.1.pdf')
      -> 'attachment; filename="____ COPY_No.1.pdf"; filename*=UTF-8\'\'%E0%B8%A2...COPY_No.1.pdf'
    """
    ascii_fallback = re.sub(r"[^A-Za-z0-9._\-]+", "_", name).strip("_") or "document.pdf"
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{quote(name)}'


@router.post("/preview")
async def preview(req: PreviewRequest) -> Response:
    """วาง watermark เฉพาะหน้าที่ขอแล้ว rasterize เป็น PNG (ตรงกับผลลัพธ์จริง)"""
    opts = req.options.to_stamp_options()
    logo_path = _logo_path(req.logo_id)
    m = storage.get_pdf(req.pdf_id)
    if not m or not Path(m.path).exists():
        raise HTTPException(404, f"ไม่พบ PDF id={req.pdf_id}")
    if req.page_index > m.page_count:
        raise HTTPException(400, f"page_index {req.page_index} เกินจำนวนหน้า ({m.page_count})")
    try:
        stamped = stamp_pdf(Path(m.path), logo_path, opts,
                            page_indices=[req.page_index], copy_number=req.copy_number)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    png = page_to_png(stamped, req.page_index, dpi=config.PREVIEW_DPI)
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "no-store"})


@router.post("/stamp")
async def stamp(req: StampRequest) -> Response:
    """วาง watermark ทุกไฟล์ที่เลือก × copies สำเนา (เลข {n} = 1..N)

    - ผลลัพธ์ 1 ไฟล์ -> application/pdf
    - มากกว่านั้น   -> application/zip (ชื่อไฟล์แนบเลขสำเนา เช่น doc_COPY_No.3.pdf)
    - overlay ทับหน้าเดิม ไม่แก้ไขเนื้อหา PDF ต้นฉบับ
    """
    logo_path = _logo_path(req.logo_id)
    opts = req.options.to_stamp_options()
    copies = req.options.copies

    pdf_ids = list(dict.fromkeys(req.pdf_ids))  # uniq รักษาลำดับ
    total = len(pdf_ids) * copies
    if total > MAX_OUTPUT_FILES:
        raise HTTPException(400, f"จำนวนไฟล์ผลลัพธ์ {total} เกินสูงสุด {MAX_OUTPUT_FILES}")

    files: list[tuple[str, bytes]] = []
    for pid in pdf_ids:
        m = storage.get_pdf(pid)
        if not m or not Path(m.path).exists():
            raise HTTPException(404, f"ไม่พบ PDF id={pid}")
        try:
            indices = resolve_page_indices(req.options.page_scope, m.page_count)
        except ValueError as exc:
            raise HTTPException(400, f"{m.filename}: {exc}")
        stem = _safe_stem(m.filename)
        for n in range(1, copies + 1):
            try:
                data = stamp_pdf(Path(m.path), logo_path, opts,
                                 page_indices=indices, copy_number=n)
            except ValueError as exc:
                raise HTTPException(400, f"{m.filename}: {exc}")
            name = f"{stem}_logo.pdf" if copies == 1 else f"{stem}_COPY_No.{n}.pdf"
            files.append((name, data))

    if len(files) == 1:
        name, data = files[0]
        return Response(content=data, media_type="application/pdf",
                        headers={"Content-Disposition": _disposition(name)})

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        used: set[str] = set()
        for name, data in files:
            uniq = name
            i = 1
            while uniq in used:
                pth = Path(name)
                uniq = f"{pth.stem}_{i}{pth.suffix}"
                i += 1
            used.add(uniq)
            zf.writestr(uniq, data)
    return Response(content=buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": _disposition("stamped_logos.zip")})
