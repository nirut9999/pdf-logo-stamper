"""Pydantic v2 models — request/response ของ API (ใช้ response_model ทุก endpoint)"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .stamping import StampOptions


class Logo(BaseModel):
    id: str
    filename: str
    width_px: int
    height_px: int
    url: str


class PageDim(BaseModel):
    index: int
    width_pt: float
    height_pt: float


class PdfDoc(BaseModel):
    id: str
    filename: str
    page_count: int
    pages: list[PageDim]
    size_bytes: int


class Options(BaseModel):
    """พารามิเตอร์ watermark (หน่วย mm) — map เป็น StampOptions ฝั่ง core

    ตัวอย่าง: Options(logo_width_mm=25, rotation_degrees=12, opacity=0.6,
                      include_text=True, text_template="COPY No.{n}", copies=200)
    """
    logo_width_mm: float = Field(30.0, gt=0, le=300)
    logo_height_mm: float | None = Field(None, gt=0, le=300)
    margin_top_mm: float = Field(8.0, ge=0, le=200)
    margin_right_mm: float = Field(8.0, ge=0, le=200)
    opacity: float = Field(1.0, gt=0, le=1.0)
    page_scope: str = Field("all", description="'all' | 'first' | ช่วงเช่น '1-3,5' (1-based)")
    rotation_degrees: float = Field(0.0, ge=-180, le=180)
    include_text: bool = Field(True, description="วางข้อความใต้โลโก้ด้วย (เช่น COPY No.1)")
    text_template: str = Field("COPY No.{n}", description="{n} = เลขสำเนา")
    text_color: str = Field("#CC0000", pattern=r"^#[0-9a-fA-F]{6}$")
    text_size_mm: float | None = Field(None, gt=0, le=100, description="None = auto ตามขนาดโลโก้")
    copies: int = Field(1, ge=1, le=200, description="จำนวนสำเนา — N ชุด เลข 1..N")

    def to_stamp_options(self) -> StampOptions:
        return StampOptions(
            logo_width_mm=self.logo_width_mm,
            logo_height_mm=self.logo_height_mm,
            margin_top_mm=self.margin_top_mm,
            margin_right_mm=self.margin_right_mm,
            opacity=self.opacity,
            rotation_degrees=self.rotation_degrees,
            include_text=self.include_text,
            text_template=self.text_template,
            text_color=self.text_color,
            text_size_mm=self.text_size_mm,
        )


class PreviewRequest(BaseModel):
    pdf_id: str
    logo_id: str
    page_index: int = Field(1, ge=1)
    copy_number: int = Field(1, ge=1, le=200, description="เลขสำเนาที่ใช้ใน preview ({n})")
    options: Options


class StampRequest(BaseModel):
    pdf_ids: list[str] = Field(min_length=1)
    logo_id: str
    options: Options


class StampResultItem(BaseModel):
    source_filename: str
    output_filename: str
    pages_stamped: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str
    version: str
