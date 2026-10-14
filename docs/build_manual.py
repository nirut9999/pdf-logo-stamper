#!/usr/bin/env python3
"""build_manual.py — สร้าง PDF "คูมือติดตั้ง Docker บน Windows" สำหรับ PDF Logo Stamper

ใช้ WeasyPrint (Pango/HarfBuzz) เพื่อจัดวางสระ-วรรณยุกต์ไทยให้ถูกต้อง
(เวอร์ชันเก่าใช้ reportlab ซึ่งวาดทีละ codepoint ไม่ทำ text shaping → วรรณยุกต์ไทยผิดตำแหน่ง)

rungs: python3 docs/build_manual.py  ->  docs/คูมือติดตั้ง-Docker-Windows.pdf
ต้องติดตั้งก่อน: python3 -m pip install weasyprint
"""
from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

from weasyprint import HTML

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "backend" / "app" / "fonts"
OUT = HERE / "คูมือติดตั้ง-Docker-Windows.pdf"

CSS = """
@font-face { font-family: Sarabun; src: url('%(sar)s'); font-weight: normal }
@font-face { font-family: Sarabun; src: url('%(sarb)s'); font-weight: bold }

@page {
  size: A4; margin: 18mm 20mm 20mm 20mm;
  @bottom-left  { content: "PDF Logo Stamper — คูมือติดตั้ง Docker บน Windows";
                  font: 8pt Sarabun; color: #8A8371 }
  @bottom-right { content: "หน้า " counter(page); font: 8pt Sarabun; color: #8A8371 }
}
@page cover {
  margin: 0; background: #1E3A2F;
  @bottom-left { content: ""; } @bottom-right { content: ""; }
}
html { font-family: Sarabun; font-size: 10.5pt; line-height: 1.6; color: #26221B }
h1 { font-size: 15.5pt; color: #1E3A2F; border-bottom: 1.2pt solid #B08D3C;
     padding-bottom: 2mm; margin: 8mm 0 3mm 0; break-after: avoid }
h2 { font-size: 12pt; color: #2E5243; margin: 4mm 0 1.5mm 0; break-after: avoid }
p  { margin: 0 0 2.2mm 0 }
b  { color: #1E3A2F }
ul { margin: 0 0 2.5mm 0; padding-left: 5mm }
li { margin-bottom: 0.8mm }
table { width: 100%%; border-collapse: collapse; font-size: 9.5pt;
        margin: 1mm 0 3mm 0; break-inside: avoid }
th { background: #1E3A2F; color: #FAF6EC; text-align: left; font-weight: bold;
     padding: 1.6mm 2.4mm; border: 0.5pt solid #C9BFA8 }
td { padding: 1.6mm 2.4mm; border: 0.5pt solid #C9BFA8; vertical-align: top }
tr:nth-child(even) td { background: #FAF6EC }
pre { font-family: Courier, monospace; font-size: 9pt; color: #1D3226;
      background: #F1EEE3; border: 0.7pt solid #E9DFC8; padding: 2.2mm 3mm;
      margin: 1mm 0 3mm 0; white-space: pre-wrap; break-inside: avoid }
code { font-family: Courier, monospace; font-size: 9.2pt }
.note { background: #FBF3DC; border-left: 3pt solid #B08D3C; padding: 2mm 3.5mm;
        margin: 1mm 0 3mm 0; break-inside: avoid }
.note b { color: #6B5518 }
.figure { text-align: center; margin: 2mm 0 }
.figure img { width: 140mm; border: 0.7pt solid #E9DFC8 }
.caption { font-size: 8.5pt; color: #5C564A; text-align: center; margin-bottom: 2mm }
.rule { border-bottom: 1pt solid #B08D3C; margin: 1mm 0 3mm 0 }
.box { display: inline-block; width: 3.4mm; height: 3.4mm; border: 0.8pt solid #1E3A2F;
       margin-right: 2mm; vertical-align: -0.3mm }
.cover { page: cover; width: 210mm; height: 297mm; box-sizing: border-box;
         padding: 30mm 22mm; color: #FFFFFF; break-after: always }
.cover .eyebrow { color: #E9DFC8; font-size: 11pt; letter-spacing: 0.5pt }
.cover .rule { border-bottom: 1.6pt solid #B08D3C; width: 60mm; margin: 3mm 0 8mm 0 }
.cover h1.t { font-size: 27pt; color: #FFFFFF; border: none; margin: 0 0 2mm 0;
              line-height: 1.3 }
.cover .sub { color: #E9DFC8; font-size: 13pt; margin-top: 6mm }
.cover .meta { color: #CFE0D4; font-size: 9.5pt; margin-top: 70mm; line-height: 2 }
"""


def p(text: str) -> str:
    return f"<p>{text}</p>"


def code(text: str) -> str:
    return f"<pre>{escape(text)}</pre>"


def table(header: list[str], rows: list[list[str]]) -> str:
    h = "".join(f"<th>{c}</th>" for c in header)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{h}</tr>{body}</table>"


def note(text: str) -> str:
    return f'<div class="note"><b>หมายเหตุ:</b> {text}</div>'


def checks(items: list[str]) -> str:
    lis = "".join(f"<li><span class='box'></span>{i}</li>" for i in items)
    return f"<ul style='list-style:none;padding-left:0'>{lis}</ul>"


def build() -> None:
    today = date.today().strftime("%d/%m/%Y")
    body = f"""
<div class="cover">
  <div class="eyebrow">PDF LOGO STAMPER &nbsp;•&nbsp; เวอร์ชันแอป 1.3.0</div>
  <div class="rule"></div>
  <h1 class="t">คูมือติดตั้งบน Windows<br>ด้วย Docker</h1>
  <p class="sub">สำหรับนำไปติดตั้งบนเครื่องอื่นเพื่อให้ทั้งทีมใช้งานร่วมกัน</p>
  <div class="meta">
    จัดทำเมื่อ {today} &nbsp;|&nbsp; ต้องใช้อย่างน้อย: Windows 10/11 (64-bit),
    Docker Desktop แบบ WSL2, RAM 4 GB, พื้นที่ดิสก์ว่าง 5 GB<br>
    ระบบจัดเก็บข้อมูลไว้ในเครื่องเท่านั้น ไม่ส่งออกนอกเครือข่าย
  </div>
</div>

<h1>1. ระบบทำงานอย่างไร</h1>
{p('PDF Logo Stamper คือเว็บแอปสำหรับ <b>วาง watermark (โลโก้ + ข้อความ เช่น "COPY No.1") '
    'ที่มุมขวาบนของ PDF ทุกหน้า</b> โดยไม่แก้ไขเนื้อหาต้นฉบับ รองรับหลายไฟล์พร้อมกัน '
    'สร้างสำเนาได้สูงสุด 200 ชุดต่อรอบ และบันทึกชุดการตั้งค่าไว้ใช้ซ้ำกับงานเดิมได้')}
{p("ระบบรันด้วย Docker Compose ประกอบด้วย 2 คอนเทนเนอร์:")}
{table(["บริการ", "หน้าที่", "พอร์ต"], [
    ["frontend", "หน้าจอเว็บสำหรับใช้งาน (nginx) — เปิดใช้งานจริงที่พอร์ตนี้", "8090"],
    ["backend", "ระบบคำนวณและวาง watermark (FastAPI) — ทำงานภายในเท่านั้น",
     "9010 (ภายใน)<br>9012 (เฉพาะเครื่องที่ติดตั้ง)"],
    ["stamper_data<br>(volume)",
     "เก็บโลโก้ ไฟล์ PDF และงานที่บันทึกไว้ — ข้อมูลอยู่ต่อเมื่อรีสตาร์ทหรืออัปเดตเวอร์ชัน", "—"],
])}
{p("ตัวอย่างผลลัพธ์จริง — โลโก้และข้อความสีแดงวางทับมุมขวาบน โปร่งจางจนอ่านเนื้อหาผ่านได้ "
    "(ปรับสี ขนาด ความจาง และความเอียงได้ที่หน้าจอ):")}
<div class="rule"></div>
<div class="figure"><img src="{HERE / 'images' / 'sample_watermark.png'}"></div>
<p class="caption">ตัวอย่าง watermark มุมขวาบนของเอกสาร สร้างด้วยระบบเดียวกับที่ใช้จริง</p>
<div class="rule"></div>

<h1>2. เตรียมเครื่อง Windows</h1>
<h2>2.1 สิ่งที่เครื่องต้องมี</h2>
{table(["หัวข้อ", "ขั้นต่ำ", "แนะนำ"], [
    ["ระบบปฏิบัติการ", "Windows 10 64-bit (รุ่น 21H2 ขึ้นไป) หรือ Windows 11", "Windows 11"],
    ["หน่วยความจำ (RAM)", "4 GB", "8 GB"],
    ["พื้นที่ดิสก์ว่าง", "5 GB สำหรับ Docker Desktop และอิมเมจของแอป", "SSD, 10 GB"],
    ["อื่น ๆ", "เปิดใช้งาน virtualization ใน BIOS (VT-x หรือ AMD-V)", "—"],
])}
<h2>2.2 ติดตั้ง WSL2 (ถ้ายังไม่มี)</h2>
{p("เปิด <b>PowerShell (Administrator)</b> แล้วรันคำสั่งด้านล่าง "
   "(เครื่องอาจรีสตาร์ทเองหรือสั่งให้รีสตาร์ท แล้วกลับมาเปิด PowerShell ใหม่):")}
{code("wsl --install\n# reboot when prompted, then reopen PowerShell\nwsl --version")}
<h2>2.3 ติดตั้ง Docker Desktop</h2>
<ul>
  <li>ดาวน์โหลดตัวติดตั้งจาก <b>docker.com/products/docker-desktop</b> แล้วติดตั้งตามขั้นตอน</li>
  <li>เปิด Docker Desktop และรอจนมุมล่างขวาของหน้าจอแสดง <b>“Engine running”</b>
      (ครั้งแรกอาจขอให้ Sign in — กดข้ามได้)</li>
  <li>ตรวจความพร้อมด้วย PowerShell:</li>
</ul>
{code("docker --version\ndocker compose version\ndocker run --rm hello-world")}
{p("ถ้าเห็นข้อความ “Hello from Docker!” แสดงว่าเครื่องพร้อมติดตั้งแอปแล้ว "
   "หากขึ้น error เรื่อง virtualization หรือ WSL ให้กลับไปทำข้อ 2.2")}

<h1>3. ดึงโค้ดจาก GitHub (public repository)</h1>
{p("โค้ดเก็บไว้ที่ <b>github.com/nirut9999/pdf-logo-stamper</b> (public) — "
   "ดาวน์โหลดได้ทันที ไม่ต้องใช้บัญชี GitHub หรือขออนุญาต")}
{p("บนเครื่อง Windows: ติดตั้ง <b>Git for Windows</b> จาก <b>git-scm.com</b> ก่อน "
   "(มาพร้อม Git Credential Manager) แล้วเปิด PowerShell:")}
{code("cd C:\\\ngit clone https://github.com/nirut9999/pdf-logo-stamper.git\ncd pdf-logo-stamper")}
{p("เมื่อ clone เสร็จจะได้โฟลเดอร์ <code>pdf-logo-stamper</code> พร้อมใช้ "
   "ครั้งถัดไปเมื่อต้องการรับเวอร์ชันใหม่ ก็เพียงรัน <code>git pull</code> ในโฟลเดอร์เดิม") }
{note("กรณีเครื่องไม่มี Git หรือเน็ตถูกบล็อก ใช้วิธี ZIP จากเครื่องต้นทางแทน "
      "(<code>zip -r pdf-logo-stamper.zip pdf-logo-stamper -x \"*/node_modules/*\" "
      "\"*/.git/*\" \"*/__pycache__/*\" \"*/dist/*\"</code> แล้ว Extract All บน Windows) — "
      "ข้อมูลโลโก้/เอกสารผู้ใช้ไม่มากับทั้ง ZIP และ repo (เก็บใน volume ของเครื่องเดิม) "
      "ถ้าต้องการย้ายงานที่บันทึกไว้ไปด้วยให้ทำ backup ตามข้อ 7")}

<h1>4. ติดตั้งและเปิดใช้งานครั้งแรก</h1>
{p("เปิด PowerShell แล้วรัน (ปรับ path ตามที่แตกไฟล์ไว้):")}
{code("cd C:\\pdf-logo-stamper\ndocker compose up -d --build")}
{p("การ build ครั้งแรกต้องดาวน์โหลดฐาน Python/Node และไลบรารี ใช้เวลาประมาณ 3–10 นาที "
   "ตามความเร็วอินเทอร์เน็ต โดยมี log แสดงความคืบหน้าตลอด")}
{p("เมื่อเสร็จให้ตรวจสถานะ — ทั้งสองตัวต้องเป็น Up (healthy):")}
{code("docker compose ps")}
{p("จากนั้นเปิดเบราว์เซอร์ที่ <b>http://localhost:8090</b> — "
   "ถ้าเห็นหน้าจอ PDF Logo Stamper แสดงว่าติดตั้งสำเร็จ ✓ "
   "ทดลองใช้งานจริง: อัปโหลดโลโก้ PNG → อัปโหลดไฟล์ PDF → ปรับค่า → "
   "ดูตัวอย่าง preview → กด Stamp & ดาวน์โหลด")}

<h1>5. ให้เครื่องอื่นในวง LAN ใช้ร่วมกัน</h1>
{p("ดู IP ของเครื่องที่ติดตั้ง (PowerShell):")}
{code("ipconfig | findstr IPv4\n# e.g. 192.168.1.50")}
{p("เปิด firewall ของ Windows สำหรับพอร์ต 8090 (PowerShell as Administrator):")}
{code('New-NetFirewallRule -DisplayName "PDF Logo Stamper"\n'
      '    -Direction Inbound -Protocol TCP -LocalPort 8090 -Action Allow')}
{p("เครื่องอื่นในวง LAN เดียวกันเปิด <code>http://192.168.1.50:8090</code> ได้ทันที")}
{note("แอปนี้ยังไม่มีระบบล็อกอิน — ควรเปิดให้เฉพาะวง LAN ที่ไว้ใจได้ "
      "หรือปรับ firewall ให้อนุญาตเฉพาะวง subnet ที่ใช้งานจริง")}

<h1>6. การหยุดและเริ่มระบบ</h1>
{table(["ต้องการ", "คำสั่ง (รันในโฟลเดอร์โปรเจกต์)"], [
    ["เปิดใช้งานอีกครั้งหลังรีสตาร์ทเครื่อง", "docker compose start"],
    ["หยุดชั่วคราว (ข้อมูลอยู่ครบ)", "docker compose stop"],
    ["อัปเดตเป็นเวอร์ชันใหม่ (build ซ้ำ)", "docker compose up -d --build"],
    ["รีสตาร์ทเฉพาะฝั่ง backend", "docker compose restart backend"],
    ["ลบระบบและข้อมูลทั้งหมด", "docker compose down -v &nbsp; "
     "<b style='color:#CC0000'>⚠ ข้อมูลโลโก้ งานที่บันทึกไว้ และไฟล์ต่าง ๆ จะถูกลบถาวร</b>"],
])}
{p("ตั้งค่าให้ Docker Desktop เริ่มเองเมื่อลงชื่อเข้าเครื่อง: "
   "Docker Desktop → Settings → General → <b>“Start Docker Desktop when you sign in</b>” "
   "จากนั้นเพิ่มงานใน <b>Task Scheduler</b> ให้รัน <code>docker compose start</code> "
   "(Action: Start a program, Start in: ระบุโฟลเดอร์โปรเจกต์) "
   "เพื่อให้แอปพร้อมใช้ทุกครั้งหลังเปิดเครื่อง")}

<h1>7. สำรองข้อมูลและกู้คืน</h1>
{p("โลโก้ ไฟล์ PDF ที่อัปโหลด และงานที่บันทึกไว้ (presets) เก็บใน volume ชื่อ "
   "<code>pdf-logo-stamper_stamper_data</code> — ชื่อจริงจะขึ้นต้นด้วยชื่อโฟลเดอร์โปรเจกต์ "
   "ตรวจได้ด้วยการรัน <code>docker volume ls</code> ข้อมูลไม่หายไปเมื่อรีสตาร์ทหรืออัปเดต "
   "แต่จะถูกลบเมื่อใช้ <code>down -v</code> จึงควรมีไฟล์สำรองเสมอ:")}
{code("# backup -> stamper-backup.tgz in current folder\ndocker run --rm "
      "-v pdf-logo-stamper_stamper_data:/data -v ${PWD}:/backup `\n"
      "    alpine tar czf /backup/stamper-backup.tgz -C /data .\n\n"
      "# restore onto a new machine (before the first up -d is fine)\n"
      "docker volume create pdf-logo-stamper_stamper_data\n"
      "docker run --rm "
      "-v pdf-logo-stamper_stamper_data:/data -v ${PWD}:/backup `\n"
      '    alpine sh -c "cd /data && tar xzf /backup/stamper-backup.tgz"')}
{note("ควรเก็บไฟล์ backup ไว้บน drive อื่นหรือ shared drive ไม่ใช่โฟลเดอร์เดียวกับโปรเจกต์")}

<h1>8. การปรับค่าผ่านไฟล์ .env</h1>
{p("สร้างไฟล์ชื่อ <code>.env</code> ในโฟลเดอร์โปรเจกต์ (ถ้ายังไม่มีให้สร้างใหม่เอง) "
   "เพื่อเปลี่ยนพอร์ตหรือค่าต่าง ๆ ของระบบ:")}
{code("FRONTEND_PORT=8090\nBACKEND_DEBUG_PORT=9012\nPREVIEW_DPI=110\n"
      "MAX_PDF_MB=50\nMAX_COPIES=200")}
{table(["ตัวแปร", "ความหมาย", "ค่าเริ่มต้น"], [
    ["FRONTEND_PORT", "พอร์ตของหน้าเว็บที่ทีมใช้งาน (เปลี่ยนถ้าชนกับโปรแกรมอื่น)", "8090"],
    ["BACKEND_DEBUG_PORT", "พอร์ตเอกสาร API (/docs) — เข้าถึงจากเครื่องที่ติดตั้งเท่านั้น", "9012"],
    ["PREVIEW_DPI", "ความละเอียดของภาพตัวอย่างในหน้าเว็บ (110–200)", "110"],
    ["MAX_PDF_MB", "ขนาดไฟล์ PDF สูงสุดต่อไฟล์ (MB)", "50"],
    ["MAX_COPIES", "จำนวนสำเนาสูงสุดต่อครั้ง", "200"],
])}
{p("หลังแก้ไขไฟล์ .env ให้รัน <code>docker compose up -d</code> อีกครั้ง "
   "(ไม่ต้องใช้ --build)")}

<h1>9. แก้ปัญหาที่พบบ่อย</h1>
{table(["อาการ", "สาเหตุและการแก้ไข"], [
    ["เปิด http://localhost:8090 ไม่ได้",
     "Docker Desktop ยังไม่ทำงาน หรือคอนเทนเนอร์ยังไม่เริ่ม — รัน "
     "<code>docker compose ps</code> เพื่อตรวจสถานะ ถ้ายังไม่ได้ให้รัน "
     "<code>docker compose up -d --build</code> แล้วดู log ที่ "
     "<code>docker compose logs backend</code>"],
    ["error เรื่องพอร์ต 8090 ถูกใช้งานอยู่แล้ว",
     "เปลี่ยน <code>FRONTEND_PORT=8091</code> ในไฟล์ .env แล้วรัน "
     "<code>docker compose up -d</code>"],
    ["build ไม่ผ่าน หรือดาวน์โหลดช้ามาก",
     "อินเทอร์เน็ตช้าหรือถูกจำกัด — ลองใหม่อีกครั้ง หรือตั้ง proxy ที่ "
     "Docker Desktop → Settings → Resources → Proxies"],
    ["คำสั่ง docker compose ไม่ทำงาน / WSL error",
     "Docker Desktop เวอร์ชันเก่า — อัปเดตเป็นเวอร์ชันล่าสุด รัน "
     "<code>wsl --update</code> และตรวจว่าเปิด virtualization ใน BIOS แล้ว"],
    ["เครื่องอื่นเข้าผ่าน LAN ไม่ได้",
     "ยังไม่ได้เปิด firewall ตามข้อ 5, อยู่คนละวง LAN กับเครื่องที่ติดตั้ง, "
     "หรือ IP เปลี่ยน — ตรวจด้วยคำสั่ง ping ก่อน"],
    ["อัปเดตแอปแล้วหน้าเว็บยังเป็นแบบเดิม",
     "เบราว์เซอร์จำหน้าเก่าไว้ — กด <b>Ctrl+F5</b> (hard refresh)"],
    ["อัปโหลดไฟล์แล้ว preview ไม่แสดง",
     "ตรวจ <code>docker compose ps</code> ว่า backend สถานะ Up (healthy) "
     "แล้วดู log ตามข้อแรก"],
    ["ข้อมูลงานเดิมหายไป",
     "เกิดจากการใช้ <code>down -v</code> — กู้คืนได้จากไฟล์ "
     "stamper-backup.tgz ตามข้อ 7 เท่านั้น"],
])}

<h1>10. รายการตรวจรับหลังติดตั้ง</h1>
{checks([
    "Docker Desktop แสดง “Engine running”",
    "<code>docker compose ps</code> ทั้ง backend และ frontend อยู่ในสถานะ Up (healthy)",
    "เปิด <code>http://localhost:8090</code> แล้วเห็นหน้าจอแอป",
    "อัปโหลดโลโก้และไฟล์ PDF ทดลอง แล้วเห็น watermark ตรงตามที่ตั้งไว้ใน preview",
    "กด Stamp แล้วดาวน์โหลดได้ไฟล์ PDF/ZIP ครบถ้วนถูกต้อง (ชื่อไฟล์ภาษาไทยใช้ได้)",
    "บันทึกงาน (preset) แล้ว reload หน้าเว็บ — ชื่องานยังคงอยู่",
    "(กรณีใช้ทั้งทีม) เครื่องอื่นเปิดผ่าน <code>http://&lt;ip&gt;:8090</code> ได้",
    "จัดตารางสำรองข้อมูล (backup volume) เป็นประจำ",
])}
{p('<span style="color:#5C564A;font-size:9pt">—— จบคูมือ —— หากแก้ตามนี้แล้วยังไม่หาย '
   'กรุณาบันทึกภาพหน้าจอที่แสดง error พร้อมผลของคำสั่ง '
   '<code>docker compose logs backend</code> ส่งให้ทีมพัฒนาระบบ ——</span>')}
"""
    html = (f"<html><head><meta charset='utf-8'><title>PDF Logo Stamper — คูมือติดตั้ง Docker บน Windows</title>"
            f"<style>{CSS % {'sar': FONTS / 'Sarabun-Regular.ttf', 'sarb': FONTS / 'Sarabun-Bold.ttf'}}</style>"
            f"</head><body>{body}</body></html>")
    (HERE / "_manual.html").write_text(html, encoding="utf-8")
    HTML(string=html, base_url=str(HERE)).write_pdf(str(OUT))
    print("built:", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    build()
