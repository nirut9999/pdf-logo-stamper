"""ค่า config กลาง —ไดเรกทอรีเก็บข้อมูลและขีดจำกัด (ปรับผ่าน env ได้)"""
from __future__ import annotations

import os
from pathlib import Path

# DATA_DIR: /app/data ใน container (mount volume เพื่อให้ logoคงอยู่ข้าม restart)
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
LOGO_DIR = DATA_DIR / "logos"
PDF_DIR = DATA_DIR / "pdfs"
PRESET_DIR = DATA_DIR / "presets"

# ขีดจำกัดความปลอดภัย
MAX_PDF_BYTES = int(os.getenv("MAX_PDF_BYTES", 50 * 1024 * 1024))     # 50 MB/ไฟล์
MAX_LOGO_BYTES = int(os.getenv("MAX_LOGO_BYTES", 8 * 1024 * 1024))     # 8 MB
MAX_PAGES_PER_DOC = int(os.getenv("MAX_PAGES_PER_DOC", 500))
PREVIEW_DPI = int(os.getenv("PREVIEW_DPI", 110))

ALLOWED_LOGO_EXT = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_PDF_EXT = {".pdf"}


def ensure_dirs() -> None:
    """สร้างโฟลเดอร์เก็บข้อมูลเมื่อเริ่ม app"""
    for d in (LOGO_DIR, PDF_DIR, PRESET_DIR):
        d.mkdir(parents=True, exist_ok=True)
