from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import easyocr
import numpy as np
from PIL import Image
import io

app = FastAPI(title="OCR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 起動時に一度だけロード（日本語＋英語）
reader = easyocr.Reader(["ja", "en"], gpu=False)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="jpeg/png/webp のみ対応")

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    img_array = np.array(image)

    results = reader.readtext(img_array)

    # [(bbox, text, confidence), ...] を整形
    extracted = [
        {
            "text": text,
            "confidence": round(conf, 3),
            "bbox": bbox
        }
        for bbox, text, conf in results
    ]

    full_text = " ".join([r["text"] for r in extracted])

    return {
        "full_text": full_text,
        "details": extracted
    }
