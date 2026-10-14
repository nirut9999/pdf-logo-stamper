#!/usr/bin/env python3
"""build_manual.py — สร้าง PDF "คู่มือติดตั้ง Docker บน Windows" สำหรับ PDF Logo Stamper

ใช้ reportlab platypus + ฟอนต์ Sarabun (ไทย) ที่ฝังใน backend/app/fonts
rungs: python3 docs/build_manual.py  ->  docs/คู่มือติดตั้ง-Docker-Windows.pdf
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image, NextPageTemplate, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle, XPreformatted,
)

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "backend" / "app" / "fonts"
OUT = HERE / "คู่มือติดตั้ง-Docker-Windows.pdf"

# --- palette (ตรงกับธีมแอป) ---
FOREST = colors.HexColor("#1E3A2F")
FOREST_LT = colors.HexColor("#2E5243")
BRASS = colors.HexColor("#B08D3C")
BRASS_LT = colors.HexColor("#E9DFC8")
IVORY = colors.HexColor("#FAF6EC")
CODE_BG = colors.HexColor("#F1EEE3")
INK = colors.HexColor("#26221B")
RED = colors.HexColor("#CC0000")

pdfmetrics.registerFont(TTFont("Sarabun", str(FONTS / "Sarabun-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Sarabun-Bold", str(FONTS / "Sarabun-Bold.ttf")))
pdfmetrics.registerFontFamily("Sarabun", normal="Sarabun", bold="Sarabun-Bold",
                              italic="Sarabun", boldItalic="Sarabun-Bold")

BODY = ParagraphStyle("body", fontName="Sarabun", fontSize=10.5, leading=16,
                      textColor=INK, wordWrap="CJK", spaceAfter=5)
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=14, bulletIndent=2,
                        spaceAfter=3)
H1 = ParagraphStyle("h1", fontName="Sarabun-Bold", fontSize=16, leading=22,
                    textColor=FOREST, spaceBefore=14, spaceAfter=6)
H2 = ParagraphStyle("h2", fontName="Sarabun-Bold", fontSize=12.5, leading=18,
                    textColor=FOREST_LT, spaceBefore=8, spaceAfter=4)
TITLE = ParagraphStyle("title", fontName="Sarabun-Bold", fontSize=26, leading=34,
                       textColor=colors.white)
SUBTITLE = ParagraphStyle("subtitle", fontName="Sarabun", fontSize=13, leading=20,
                          textColor=BRASS_LT)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=9, leading=13,
                       textColor=colors.HexColor("#5C564A"))
CAPTION = ParagraphStyle("caption", parent=SMALL, alignment=1)
CODE = ParagraphStyle("code", fontName="Courier", fontSize=9.5, leading=13.5,
                      textColor=colors.HexColor("#1D3226"), wordWrap="CJK",
                      backColor=CODE_BG, borderColor=BRASS_LT, borderWidth=0.7,
                      borderPadding=6, leftIndent=6, spaceAfter=8)
TCELL = ParagraphStyle("tcell", parent=BODY, fontSize=9.5, leading=14, spaceAfter=0)
TCELL_B = ParagraphStyle("tcellb", parent=TCELL, fontName="Sarabun-Bold",
                         textColor=colors.white)


def th(*cells: str) -> list:
    """แถว header ตาราง (ขาวบนเขียว)"""
    return [Paragraph(c, TCELL_B) if i == 0 else Paragraph(c, TCELL_B)
            for i, c in enumerate(cells)]


def row(*cells: str) -> list:
    return [Paragraph(c, TCELL) for c in cells]


def table(header: list, rows: list, widths: list) -> Table:
    t = Table([header] + rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, IVORY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9BFA8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def code(text: str) -> XPreformatted:
    return XPreformatted(text, CODE)


def note(text: str) -> Table:
    """กล่องหมายเหตุเหลืองแกมทอง"""
    p = Paragraph(f"<b>หมายเหตุ:</b> {text}", BODY)
    t = Table([[p]], colWidths=[168 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF3DC")),
        ("LINEBEFORE", (0, 0), (0, -1), 3, BRASS),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def bullets(items: list) -> list:
    return [Paragraph(f"<bullet>•</bullet>{i}", BULLET) for i in items]


def cover(canvas, doc):  # หน้าปกเขียวทั้งหน้า
    canvas.saveState()
    canvas.setFillColor(FOREST)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(BRASS)
    canvas.rect(20 * mm, 262 * mm, 60 * mm, 1.2 * mm, fill=1, stroke=0)
    canvas.setFont("Sarabun-Bold", 11)
    canvas.setFillColor(BRASS_LT)
    canvas.drawString(20 * mm, A4[1] - 24 * mm, "PDF LOGO STAMPER  •  v1.3.0")
    canvas.restoreState()


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BRASS_LT)
    canvas.setLineWidth(0.6)
    canvas.line(20 * mm, 14 * mm, A4[0] - 20 * mm, 14 * mm)
    canvas.setFont("Sarabun", 8)
    canvas.setFillColor(colors.HexColor("#8A8371"))
    canvas.drawString(20 * mm, 10 * mm, "PDF Logo Stamper — คู่มือติดตั้ง Docker บน Windows")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"หน้า {doc.page}")
    canvas.restoreState()


def build() -> None:
    doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title="PDF Logo Stamper — คู่มือติดตั้ง Docker บน Windows",
                            author="Hermes")
    W = 170 * mm
    el: list = []

    # ---------- ปก ----------
    el.append(Spacer(1, 60 * mm))
    el.append(Paragraph("คู่มือติดตั้ง", TITLE))
    el.append(Paragraph("PDF Logo Stamper บน Windows ด้วย Docker", TITLE))
    el.append(Spacer(1, 8 * mm))
    el.append(Paragraph("สำหรับติดตั้งบนเครื่อง Windows อื่นเพื่อให้ทั้งทีมใช้ร่วมกัน",
                        SUBTITLE))
    el.append(Spacer(1, 40 * mm))
    el.append(Paragraph(f"เวอร์ชันแอป 1.3.0 &nbsp;|&nbsp; จัดทำวันที่ "
                        f"{date.today().strftime('%d/%m/%Y')} &nbsp;|&nbsp; "
                        f"ต้องใช้อย่างน้อย: Windows 10/11 64-bit + Docker Desktop (WSL2)",
                        ParagraphStyle("cvsmall", parent=SUBTITLE, fontSize=10)))
    el.append(PageBreak())

    # ---------- 1. ภาพรวม ----------
    el.append(Paragraph("1. ภาพรวมระบบ", H1))
    el.append(Paragraph(
        "PDF Logo Stamper คือเว็บแอปสำหรับ <b>วาง watermark (โลโก้ + ข้อความ เช่น "
        "COPY No.1) ทับมุมขวาบนของทุกหน้า PDF</b> โดยไม่แก้ไขเนื้อหาต้นฉบับ "
        "รองรับหลายไฟล์พร้อมกัน สร้างได้สูงสุด 200 สำเนาต่อรอบ "
        "บันทึกการตั้งค่าเป็น “งาน” ไว้ใช้ซ้ำกับงานเดิมได้ "
        "ทำงานเป็น 2 container ผ่าน Docker Compose:", BODY))
    el.append(Spacer(1, 2))
    el.append(table(
        th("บริการ", "หน้าที่", "พอร์ต"),
        [row("frontend", "หน้าจอเว็บ (nginx) — เปิดใช้จริงที่พอร์ตนี้", "8090"),
         row("backend", " engine วาง watermark (FastAPI) — เข้าถึงผ่านหน้าเว็บเท่านั้น",
            "9010 (ภายใน) / 9012 (เฉพาะเครื่องตัวเอง)"),
         row("volume: stamper_data", "เก็บโลโก้ ไฟล์ PDF และงานที่บันทึกไว้ — "
            "อยู่ข้ามการ restart/upgrade", "—")],
        [42 * mm, 92 * mm, 36 * mm]))
    el.append(Spacer(1, 6))
    el.append(Paragraph(
        "ผลลัพธ์ตัวอย่าง — โลโก้ + ข้อความสีแดง โปร่งจาง มองทะลุเนื้อหาได้ "
        "(ปรับสี/ขนาด/ความจาง/เอียงได้ในหน้าเว็บ):", BODY))
    img = Image(str(HERE / "images" / "sample_watermark.png"))
    w = 140 * mm
    img.drawWidth, img.drawHeight = w, w * img.imageHeight / img.imageWidth
    img.hAlign = "CENTER"
    el.append(HRFlowable(width=W, color=BRASS, thickness=1, spaceBefore=2, spaceAfter=6))
    el.append(img)
    el.append(Paragraph("ตัวอย่าง watermark จริงมุมขวาบนของเอกสาร (สร้างจาก engine "
                        "เดียวกับที่ใช้งาน)", CAPTION))
    el.append(HRFlowable(width=W, color=BRASS, thickness=1, spaceBefore=6, spaceAfter=2))

    # ---------- 2. เตรียมเครื่อง ----------
    el.append(Paragraph("2. เตรียมเครื่อง Windows", H1))
    el.append(Paragraph("2.1 สเปกขั้นต่ำ", H2))
    el.append(table(
        th("หัวข้อ", "ขั้นต่ำ", "แนะนำ"),
        [row("ระบบปฏิบัติการ", "Windows 10 64-bit (21H2+) หรือ Windows 11", "Windows 11"),
         row("หน่วยความจำ", "4 GB", "8 GB"),
         row("ดิสก์ว่าง", "5 GB (Docker Desktop + image)", "SSD, 10 GB"),
         row("อื่น ๆ", "เปิด virtualization ใน BIOS (VT-x / AMD-V)", "—")],
        [34 * mm, 70 * mm, 66 * mm]))
    el.append(Paragraph("2.2 ติดตั้ง WSL2 (ถ้ายังไม่มี)", H2))
    el.append(Paragraph("เปิด <b>PowerShell (Administrator)</b> แล้วรัน:", BODY))
    el.append(code("wsl --install\n# reboot when prompted, then reopen PowerShell\nwsl --version"))
    el.append(Paragraph("2.3 ติดตั้ง Docker Desktop", H2))
    el.append(Paragraph("1) ดาวน์โหลดจาก <font color='#26418E'>https://www.docker.com/"
                        "products/docker-desktop/</font> แล้วรันตัวติดตั้ง", BODY))
    el.append(Paragraph("2) เปิด Docker Desktop รอจนมุมล่างขวาขึ้น <b>“Engine running”</b> "
                        "(ครั้งแรกอาจให้ Sign in — ข้ามได้)", BODY))
    el.append(Paragraph("3) ตรวจว่าพร้อมใช้ โดยรันใน PowerShell:", BODY))
    el.append(code("docker --version\ndocker compose version\ndocker run --rm hello-world"))
    el.append(Paragraph("ถ้า hello-world ขึ้น “Hello from Docker!” = พร้อมติดตั้งแอป "
                        "ถ้า error เรื่อง virtualization/WSL กลับข้อ 2.2", BODY))

    # ---------- 3. copy โปรเจค ----------
    el.append(Paragraph("3. นำไฟล์โปรเจคมาไว้บนเครื่อง", H1))
    el.append(Paragraph("ยังไม่มี git remote — ส่งไฟล์กันด้วย ZIP จากเครื่องต้นทาง "
                        "(macOS/Linux รันใน Terminal):", BODY))
    el.append(code("cd ~/Workspace/projects\nzip -r pdf-logo-stamper.zip pdf-logo-stamper \\\n"
        "    -x \"*/node_modules/*\" \"*/.git/*\" \"*/__pycache__/*\" \"*/dist/*\"\n"
        "# -> pdf-logo-stamper.zip  (copy to Windows: USB / shared drive)"))
    el.append(Paragraph("ฝั่ง Windows: คลิกขวา zip → <b>Extract All…</b> เช่นได้เป็น "
                        "<font face='Courier'>C:\\pdf-logo-stamper</font> "
                        "โฟลเดอร์นี้จะมี docker-compose.yml, backend/, frontend/ "
                        "— ข้อมูลผู้ใช้งานไม่ได้มากับ zip (เก็บใน volume ของเครื่องเดิม "
                        "ถ้าต้องการย้ายงานที่บันทึกไว้ด้วย ดูข้อ 7)", BODY))
    el.append(note("เมื่อ repo ขึ้น GitHub แล้ว วิธีที่ถูกต้องคือ "
                   "<font face='Courier'>git clone &lt;url&gt;</font> แทนการ zip"))

    # ---------- 4. ติดตั้ง+เริ่ม ----------
    el.append(Paragraph("4. ติดตั้งและเปิดใช้งานครั้งแรก", H1))
    el.append(Paragraph("ใน PowerShell:", BODY))
    el.append(code("cd C:\\pdf-logo-stamper\ndocker compose up -d --build"))
    el.append(Paragraph("ครั้งแรก build image (ดาวน์โหลด Python/Node + ติดตั้ง lib) "
                        "ใช้เวลาประมาณ 3–10 นาทีแล้วแต่เน็ต — ระหว่างรอจอจะวิ่ง "
                        "เสร็จแล้วตรวจว่าทั้ง 2 ตัว <b>healthy</b>:", BODY))
    el.append(code("docker compose ps\n"
        "# STATUS must be Up (healthy) for BOTH backend and frontend"))
    el.append(Paragraph("เปิดเบราว์เซอร์ที่:", BODY))
    el.append(code("http://localhost:8090"))
    el.append(Paragraph("เห็นหน้าเว็บธีมเขียว “PDF Logo Stamper” = สำเร็จ ✓ "
                        "ทดสอบเต็มระบบ: อัปโหลดโลโก้ PNG → อัปโหลด PDF → ตั้งค่า → "
                        "ดู preview → กด Stamp → ดาวน์โหลดผล", BODY))

    # ---------- 5. ให้ทีมใช้ ----------
    el.append(Paragraph("5. เปิดให้เครื่องอื่นในวง LAN เข้าใช้", H1))
    el.append(Paragraph("ตรวจ IP ของเครื่องที่ติดตั้ง (PowerShell):", BODY))
    el.append(code("ipconfig | findstr IPv4\n# e.g. 192.168.1.50"))
    el.append(Paragraph("เปิดไฟร์วอลล์ Windows สำหรับพอร์ต 8090 "
                        "(PowerShell as Administrator):", BODY))
    el.append(code('New-NetFirewallRule -DisplayName "PDF Logo Stamper"\n'
        '    -Direction Inbound -Protocol TCP -LocalPort 8090 -Action Allow'))
    el.append(Paragraph("เครื่องอื่นในวง LAN เดียวกันเปิด: "
                        "<font face='Courier'>http://192.168.1.50:8090</font>", BODY))
    el.append(note("เว็บนี้ยังไม่มีระบบ login — ให้เปิดเฉพาะวง LAN ที่ไว้ใจได้ "
                   "หรือตั้ง Windows Firewall ให้อนุญาตเฉพาะกั้น subnet ที่ใช้จริง"))

    # ---------- 6. ชีวิตประจำวัน ----------
    el.append(Paragraph("6. สั่งเปิด/ปิด/รีสตาร์ท", H1))
    el.append(table(
        th("ต้องการ", "คำสั่ง (ในโฟลเดอร์โปรเจค)"),
        [row("เปิดใช้ (หลังบูตเครื่องใหม่)", "docker compose start"),
         row("ปิดชั่วคราว (ข้อมูลอยู่ครบ)", "docker compose stop"),
         row("แก้ code/อัปเดต แล้ว build ใหม่", "docker compose up -d --build"),
         row("รีสตาร์ทเฉพาะ backend", "docker compose restart backend"),
         row("เลิกใช้งานถาวร + ลบข้อมูล", "docker compose down -v &nbsp; <b>⚠ ลบข้อมูลทั้งหมด</b>")],
        [62 * mm, 108 * mm]))
    el.append(Paragraph("ตั้งค่าให้ Docker Desktop เริ่มเองตอนบูต: Docker Desktop → "
                        "Settings → General → “Start Docker Desktop when you sign in” "
                        "และใส่โฟลเดอร์โปรเจคเป็น shortcut auto-start ได้ "
                        "(Settings → General → “Open Docker Desktop at startup” "
                        "หรือ Task Scheduler รัน <font face='Courier'>docker compose "
                        "start</font> ตอนล็อกอิน)", BODY))

    # ---------- 7. ข้อมูล/สำรอง ----------
    el.append(Paragraph("7. ข้อมูลและการสำรอง (backup)", H1))
    el.append(Paragraph("โลโก้, ไฟล์ PDF และ “งานที่บันทึกไว้” (presets) เก็บใน volume "
                        "ชื่อ <font face='Courier'>pdf-logo-stamper_stamper_data</font> "
                        "— ไม่หายตอน restart/update แต่หายตอน <font face='Courier'>down "
                        "-v</font> ควร backup เป็นประจำ:", BODY))
    el.append(code("# backup -> stamper-backup.tgz in current folder\n"
        "docker run --rm -v pdf-logo-stamper_stamper_data:/data -v ${PWD}:/backup `\n"
        "    alpine tar czf /backup/stamper-backup.tgz -C /data .\n\n"
        "# restore onto a new machine (before the first up -d is fine)\n"
        "docker volume create pdf-logo-stamper_stamper_data\n"
        "docker run --rm -v pdf-logo-stamper_stamper_data:/data -v ${PWD}:/backup `\n"
        '    alpine sh -c "cd /data &amp;&amp; tar xzf /backup/stamper-backup.tgz"'))
    el.append(note("ชื่อย่อของ volume ขึ้นกับชื่อโฟลเดอร์โปรเจค — ตรวจชื่อจริงด้วย "
                   "<font face='Courier'>docker volume ls</font>"))

    # ---------- 8. ปรับพารามิเตอร์ ----------
    el.append(Paragraph("8. ปรับพอร์ตและค่าต่าง ๆ ผ่าน .env", H1))
    el.append(Paragraph("สร้างไฟล์ <font face='Courier'>.env</font> ในโฟลเดอร์โปรเจค "
                        "(ถ้าพอร์ต 8090 ชนกับของอื่นหรืออยากเปลี่ยน):", BODY))
    el.append(code("FRONTEND_PORT=8090      # web port the team uses\n"
        "BACKEND_DEBUG_PORT=9012 # API /docs port (only this machine)\n"
        "PREVIEW_DPI=110         # preview resolution (110-200)\n"
        "MAX_PDF_MB=50           # max PDF size per file\n"
        "MAX_COPIES=200          # max copies per stamp run"))
    el.append(Paragraph("หลังแก้ .env ให้รัน <font face='Courier'>docker compose up -d</font> "
                        "ใหม่ (ไม่ต้อง --build)", BODY))

    # ---------- 9. แก้ปัญหา ----------
    el.append(Paragraph("9. แก้ปัญหาที่พบบ่อย", H1))
    el.append(table(
        th("อาการ", "สาเหตุ/วิธีแก้"),
        [row("เปิด http://localhost:8090 ไม่ได้เลย",
             "Docker Desktop ยังไม่รัน หรือ container ไม่ขึ้น — "
             "รัน <font face='Courier'>docker compose ps</font> ถ้าว่าง/ลงไม่ได้ "
             "ให้ <font face='Courier'>docker compose up -d --build</font> แล้วดู log: "
             "<font face='Courier'>docker compose logs backend</font>"),
         row("error เรื่อง port 8090 ถูกใช้",
             "ตั้ง <font face='Courier'>FRONTEND_PORT=8091</font> ใน .env แล้ว "
             "<font face='Courier'>docker compose up -d</font>"),
         row("build ไม่ผ่าน / โหลดช้ามาก",
             "เน็ตถูกบล็อก/ช้า — ลองใหม่ หรือตั้งค่า proxy ใน Docker Desktop "
             "→ Settings → Resources → Proxies"),
         row("docker compose ไม่รู้จักคำสั่ง / WSL error",
             "Docker Desktop เก่า — อัปเดตเป็นเวอร์ชันล่าสุด, รัน "
             "<font face='Courier'>wsl --update</font>, เปิด virtualization ใน BIOS"),
         row("เครื่องอื่นเข้า LAN ไม่ได้",
             "ยังไม่ได้เปิดไฟร์วอลล์ (ข้อ 5) หรือคนละวง LAN — ทดสอบ ping ก่อน"),
         row("หน้าเว็บเก่าค้าง (อัปเดตแล้วภาพไม่เปลี่ยน)",
             "กด Ctrl+F5 (hard refresh) ที่เบราว์เซอร์"),
         row("อัปโหลดไฟล์แล้วไม่ขึ้น preview",
             "ตรวจ <font face='Courier'>docker compose ps</font> ว่า backend healthy, "
             "ดู log ตามข้อบน"),
         row("ข้อมูลงานเดิมหาย",
             "ไม่เคยทำ backup แล้วเผลอ <font face='Courier'>down -v</font> — "
             "กู้จากไฟล์ backup.tgz (ข้อ 7) เท่านั้น")],
        [52 * mm, 118 * mm]))

    # ---------- 10. checklist ----------
    el.append(Paragraph("10. Checklist หลังติดตั้งเสร็จ", H1))
    for i, t in enumerate([
            "Docker Desktop ขึ้น “Engine running”",
            "<font face='Courier'>docker compose ps</font> — ทั้ง 2 ตัว Up (healthy)",
            "เปิด http://localhost:8090 เห็นหน้าเว็บ",
            "อัปโหลดโลโก้ + PDF ทดลอง → preview เห็น watermark ตรงตามตั้ง",
            "กด Stamp ได้ดาวน์โหลดไฟล์ PDF/ZIP ผลลัพธ์ถูกต้อง",
            "บันทึกงาน (preset) → reload → chip ยังอยู่",
            "(ถ้าใช้ทั้งทีม) เครื่องอื่นเข้าผ่าน http://&lt;ip&gt;:8090 ได้",
            "ตั้งเวลา/นิสัย backup volume สม่ำเสมอ"], 1):
        el.append(Paragraph(f"<font face='Courier'>[&nbsp;&nbsp;]</font> {t}", BULLET))
    el.append(Spacer(1, 8))
    el.append(Paragraph("—— จบคู่มือ — มีปัญหาที่แก้ตามนี้ไม่ได้อัดหน้าจอ error "
                        "พร้อมผลของ <font face='Courier'>docker compose logs backend</font> "
                        "ส่งให้ Hermes ได้เลยครับ ——", SMALL))

    doc.build(el, onFirstPage=cover, onLaterPages=footer)
    print("built:", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    build()
