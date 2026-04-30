FROM python:3.11-slim

WORKDIR /app

# EasyOCRの依存（OpenCV等）
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# EasyOCRのモデルを事前ダウンロード（起動高速化）
RUN python -c "import easyocr; easyocr.Reader(['ja','en'], gpu=False)"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
