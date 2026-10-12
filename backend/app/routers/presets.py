"""API ชุดการตั้งค่าที่บันทึกไว้ (presets) — เซฟงานเดิมใช้ซ้ำได้ทันที"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import storage
from ..schemas import Options, Preset, PresetSaveRequest

router = APIRouter(prefix="/api/presets", tags=["presets"])


def _to_preset(m: storage.PresetMeta) -> Preset:
    return Preset(id=m.id, name=m.name, logo_id=m.logo_id,
                  options=Options.model_validate(m.options),
                  created_at=m.created_at, updated_at=m.updated_at)


@router.post("", response_model=Preset)
async def create_or_update(req: PresetSaveRequest) -> Preset:
    """บันทึก/อัปเดต preset จาก options ปัจจุบัน

    validate ด้วย StampOptions เดียวกับตอน stamp จริง -> preset ที่เซฟได้ = ใช้ stamp ได้ทันที
    (font ไม่รองรับข้อความไทย, template ไม่มี {n} ฯลฯ จะถูกปฏิเสธ 422 ตั้งแต่ตอนเซฟ)

    ตัวอย่าง payload:
        {"name": "งานเช่าเครื่อง GPO", "logo_id": "cb84", "options": {"copies": 50, "text_font": "Sarabun-Bold"}}
    """
    if req.id and not storage.get_preset(req.id):
        raise HTTPException(404, f"ไม่พบ preset id={req.id}")
    try:
        req.options.to_stamp_options().validate()
    except ValueError as exc:
        raise HTTPException(422, f"ค่าตั้งไม่valid — {exc}")
    meta = storage.save_preset(req.name, req.logo_id, req.options.model_dump(mode="json"), pid=req.id)
    return _to_preset(meta)


@router.get("", response_model=list[Preset])
async def get_presets() -> list[Preset]:
    """รายการ preset (ใหม่สุดก่อน) — ใช้ทำปุ่มลัด 'งานเดิม' ในหน้าเว็บ"""
    return [_to_preset(m) for m in storage.list_presets()]


@router.delete("/{cid}")
async def remove_preset(cid: str) -> dict[str, bool]:
    if not storage.delete_preset(cid):
        raise HTTPException(404, "ไม่พบ preset")
    return {"deleted": True}
