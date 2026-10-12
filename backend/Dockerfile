FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

# ติดตั้ง deps ก่อน (layer cache) — pypdfium2/reportlab/pillow มี wheel สำหรับ 3.12
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# run เป็น non-root + volume สำหรับคลัง logo/pdf
ENV DATA_DIR=/app/data PORT=9010
RUN useradd -m appuser && mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

EXPOSE 9010
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9010"]
