"""FastAPI app — PDF Logo Stamper backend entrypoint"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .routers import logos, pdfs, stamp
from .schemas import HealthResponse

VERSION = "1.0.0"

app = FastAPI(title="PDF Logo Stamper", version=VERSION,
              description="วางโลโก้มุมขวาบนของทุกหน้า PDF (เลือกโลโก้ + ปรับ size/margin/opacity)")

# CORS: เปิดให้ dev frontend (vite) + อนุญาตเพิ่มผ่าน env CORS_ORIGINS (คั่นด้วย ,)
_default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080"
_origins = os.getenv("CORS_ORIGINS", _default_origins).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logos.router)
app.include_router(pdfs.router)
app.include_router(stamp.router)


@app.on_event("startup")
def _startup() -> None:
    config.ensure_dirs()


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=VERSION)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "9010")), reload=True)
