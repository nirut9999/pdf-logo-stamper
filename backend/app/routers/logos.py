"""API จัดการคลังโลโก้: อัปโหลด / รายการ / ดึงภาพ / ลบ"""
from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image

from .. import config, storage
from ..schemas import Logo

router = APIRouter(prefix="/api/logos", tags=["logos"])


def _to_logo(m: storage.LogoMeta) -> Logo:
    return Logo(id=m.id, filename=m.filename, width_px=m.width_px,
                height_px=m.height_px, url=m.url())


@router.post("", response_model=Logo)
async def upload_logo(file: UploadFile) -> Logo:
    """รับไฟล์ภาพโลโก้ PNG/JPG/WEBP -> บันทึกลงคลัง คืน metadata"""
    ext = Path(file.filename or "logo.png").suffix.lower()
    if ext not in config.ALLOWED_LOGO_EXT:
        raise HTTPException(400, f"นามสกุลไม่รองรับ: {ext} (ใช้ {sorted(config.ALLOWED_LOGO_EXT)})")
    content = await file.read()
    if len(content) > config.MAX_LOGO_BYTES:
        raise HTTPException(413, f"โลโก้ใหญ่เกิน {config.MAX_LOGO_BYTES} bytes")
    try:
        with Image.open(io.BytesIO(content)) as im:
            im.verify()  # ตรวจว่าเป็นภาพจริง
        with Image.open(io.BytesIO(content)) as im:
            w, h = im.size
    except Exception:
        raise HTTPException(400, "ไฟล์ไม่valid เป็นรูปภาพ")
    meta = storage.save_logo(content, file.filename or "logo.png", w, h)
    return _to_logo(meta)


@router.get("", response_model=list[Logo])
async def get_logos() -> list[Logo]:
    return [_to_logo(m) for m in storage.list_logos()]


@router.get("/{cid}/image")
async def get_logo_image(cid: str) -> FileResponse:
    m = storage.get_logo(cid)
    if not m or not Path(m.path).exists():
        raise HTTPException(404, "ไม่พบโลโก้")
    return FileResponse(m.path, filename=m.filename)


@router.delete("/{cid}")
async def remove_logo(cid: str) -> dict[str, bool]:
    if not storage.delete_logo(cid):
        raise HTTPException(404, "ไม่พบโลโก้")
    return {"deleted": True}
