import base64
import io
import json
import logging
import os
import uuid

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from PIL import Image
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY が設定されていません")
client = OpenAI(api_key=api_key)

app = FastAPI(title="GPT Image 2 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# マルチターンセッション管理（インメモリ）
sessions: dict[str, dict] = {}

VALID_QUALITIES = {"low", "medium", "high", "auto"}
VALID_FORMATS = {"png", "jpeg", "webp"}
MAX_SIDE = 3840
MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
MAX_IMAGE_BYTES = 50 * 1024 * 1024  # 50MB


# --- ユーティリティ ---

def validate_size(size: str) -> None:
    if size == "auto":
        return
    try:
        w_str, h_str = size.split("x")
        w, h = int(w_str), int(h_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"size の形式が不正です: {size}")
    if w % 16 != 0 or h % 16 != 0:
        raise HTTPException(status_code=400, detail="size は両辺とも 16px の倍数である必要があります")
    if not (16 <= w <= MAX_SIDE and 16 <= h <= MAX_SIDE):
        raise HTTPException(status_code=400, detail=f"size の各辺は 16〜{MAX_SIDE}px の範囲にしてください")
    if max(w, h) / min(w, h) > 3.0:
        raise HTTPException(status_code=400, detail="size の長辺と短辺の比率は 3:1 以内にしてください")
    pixels = w * h
    if not (MIN_PIXELS <= pixels <= MAX_PIXELS):
        raise HTTPException(
            status_code=400,
            detail=f"総ピクセル数は {MIN_PIXELS:,}〜{MAX_PIXELS:,} の範囲にしてください",
        )


def rgba_to_rgb_bytes(file_bytes: bytes) -> tuple[bytes, bool]:
    img = Image.open(io.BytesIO(file_bytes))
    if img.mode not in ("RGBA", "LA"):
        return file_bytes, False
    bg = Image.new("RGB", img.size, (255, 255, 255))
    if img.mode == "RGBA":
        bg.paste(img, mask=img.split()[3])
    else:
        bg.paste(img.convert("RGBA"), mask=img.split()[1])
    buf = io.BytesIO()
    bg.save(buf, format="PNG")
    return buf.getvalue(), True


def extract_b64_from_response(response) -> list[str]:
    images = []
    for item in response.data:
        if hasattr(item, "b64_json") and item.b64_json:
            images.append(item.b64_json)
    return images


def extract_b64_from_responses_api(response) -> list[str]:
    images = []
    for block in response.output:
        if block.type == "image_generation_call":
            images.append(block.result)
    return images


# --- Pydantic モデル ---

class GenerateRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    quality: str = "auto"
    n: int = 1
    output_format: str = "png"


class SessionCreateRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    quality: str = "auto"
    output_format: str = "png"


class SessionContinueRequest(BaseModel):
    session_id: str
    prompt: str


# --- エンドポイント ---

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok", "model": "gpt-image-2"}


@app.post("/generate")
async def generate(req: GenerateRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt が空です")
    if req.quality not in VALID_QUALITIES:
        raise HTTPException(status_code=400, detail=f"quality は {VALID_QUALITIES} のいずれかです")
    if req.output_format not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"output_format は {VALID_FORMATS} のいずれかです")
    validate_size(req.size)

    logger.info("generate: prompt=%s size=%s quality=%s n=%d", req.prompt[:60], req.size, req.quality, req.n)
    try:
        response = client.images.generate(
            model="gpt-image-2",
            prompt=req.prompt,
            size=req.size,
            quality=req.quality,
            n=req.n,
            output_format=req.output_format,
        )
    except Exception as e:
        logger.error("generate failed: %s", e)
        raise HTTPException(status_code=502, detail=f"OpenAI API エラー: {e}")

    images = extract_b64_from_response(response)
    logger.info("generate complete: %d 枚", len(images))
    return {"images": images, "format": req.output_format}


@app.post("/edit")
async def edit(
    prompt: str = Form(...),
    size: str = Form("1024x1024"),
    n: int = Form(1),
    output_format: str = Form("png"),
    images: list[UploadFile] = File(...),
):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt が空です")
    if not images:
        raise HTTPException(status_code=400, detail="images が空です")
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="images は最大 10 枚です")
    if output_format not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"output_format は {VALID_FORMATS} のいずれかです")
    validate_size(size)

    image_b64s: list[str] = []
    image_mimes: list[str] = []
    converted: list[str] = []

    for upload in images:
        if not (upload.content_type or "").startswith("image/"):
            raise HTTPException(status_code=415, detail=f"{upload.filename} は画像ファイルではありません")
        raw = await upload.read()
        if len(raw) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail=f"{upload.filename} が 50MB を超えています")
        processed, was_converted = rgba_to_rgb_bytes(raw)
        if was_converted:
            converted.append(upload.filename or "unknown")
        image_b64s.append(base64.b64encode(processed).decode())
        image_mimes.append("image/png")

    # Responses API で参照画像付き生成（images.edit は gpt-image-2 非対応のため）
    content: list[dict] = []
    for b64, mime in zip(image_b64s, image_mimes):
        content.append({"type": "input_image", "image_url": f"data:{mime};base64,{b64}"})
    content.append({"type": "input_text", "text": prompt})

    logger.info("edit: prompt=%s images=%d size=%s", prompt[:60], len(image_b64s), size)
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[{"role": "user", "content": content}],
            tools=[{"type": "image_generation", "size": size}],
        )
    except Exception as e:
        logger.error("edit failed: %s", e)
        raise HTTPException(status_code=502, detail=f"OpenAI API エラー: {e}")

    result_images = extract_b64_from_responses_api(response)
    logger.info("edit complete: %d 枚", len(result_images))
    return {"images": result_images, "format": output_format, "rgba_converted": converted}


@app.post("/edit/mask")
async def edit_mask(
    prompt: str = Form(...),
    size: str = Form("auto"),
    n: int = Form(1),
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt が空です")
    validate_size(size)

    image_raw = await image.read()
    mask_raw = await mask.read()

    # マスクは RGBA PNG である必要がある
    try:
        mask_img = Image.open(io.BytesIO(mask_raw))
        if mask_img.mode != "RGBA":
            raise HTTPException(status_code=400, detail="mask は RGBA PNG である必要があります")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="mask の読み込みに失敗しました")

    image_bytes, _ = rgba_to_rgb_bytes(image_raw)
    image_b64 = base64.b64encode(image_bytes).decode()

    # マスク（透明=編集領域）を可視化した説明をプロンプトに付加
    augmented_prompt = f"{prompt}（画像の透明部分を書き換えてください。他の部分は保持してください）"

    content = [
        {"type": "input_image", "image_url": f"data:image/png;base64,{image_b64}"},
        {"type": "input_text", "text": augmented_prompt},
    ]

    logger.info("edit/mask: prompt=%s size=%s", prompt[:60], size)
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[{"role": "user", "content": content}],
            tools=[{"type": "image_generation", "size": size}],
        )
    except Exception as e:
        logger.error("edit/mask failed: %s", e)
        raise HTTPException(status_code=502, detail=f"OpenAI API エラー: {e}")

    result_images = extract_b64_from_responses_api(response)
    logger.info("edit/mask complete: %d 枚", len(result_images))
    return {"images": result_images, "format": "png"}


@app.get("/generate/stream")
async def generate_stream(
    prompt: str = Query(...),
    size: str = Query("1024x1024"),
    quality: str = Query("auto"),
    n: int = Query(1),
    partial_images: int = Query(2),
    output_format: str = Query("png"),
):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt が空です")
    if quality not in VALID_QUALITIES:
        raise HTTPException(status_code=400, detail=f"quality は {VALID_QUALITIES} のいずれかです")
    if output_format not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"output_format は {VALID_FORMATS} のいずれかです")
    validate_size(size)

    async def event_generator():
        try:
            stream = client.images.generate(
                model="gpt-image-2",
                prompt=prompt,
                size=size,
                quality=quality,
                n=n,
                stream=True,
                partial_images=partial_images,
                output_format=output_format,
            )
            for event in stream:
                if event.type == "image_generation.partial_image":
                    payload = json.dumps({
                        "type": "partial",
                        "index": event.partial_image_index,
                        "b64": event.b64_json,
                        "image_index": getattr(event, "image_index", 0),
                    })
                    yield f"data: {payload}\n\n"
                elif event.type == "image_generation.completed":
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error("stream failed: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/session/create")
async def session_create(req: SessionCreateRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt が空です")
    if req.quality not in VALID_QUALITIES:
        raise HTTPException(status_code=400, detail=f"quality は {VALID_QUALITIES} のいずれかです")
    validate_size(req.size)

    session_id = str(uuid.uuid4())
    logger.info("session/create: session_id=%s prompt=%s", session_id, req.prompt[:60])
    try:
        response = client.responses.create(
            model="gpt-5.5",
            input=req.prompt,
            tools=[{
                "type": "image_generation",
                "size": req.size,
                "quality": req.quality,
            }],
        )
    except Exception as e:
        logger.error("session/create failed: %s", e)
        raise HTTPException(status_code=502, detail=f"OpenAI API エラー: {e}")

    images = extract_b64_from_responses_api(response)
    sessions[session_id] = {"response_id": response.id, "turn": 1}
    logger.info("session/create complete: session_id=%s images=%d", session_id, len(images))
    return {
        "session_id": session_id,
        "response_id": response.id,
        "images": images,
        "turn": 1,
    }


@app.post("/session/continue")
async def session_continue(req: SessionContinueRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt が空です")
    session = sessions.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session_id が存在しません")

    previous_response_id = session["response_id"]
    logger.info("session/continue: session_id=%s turn=%d prompt=%s", req.session_id, session["turn"] + 1, req.prompt[:60])
    try:
        response = client.responses.create(
            model="gpt-5.5",
            input=req.prompt,
            previous_response_id=previous_response_id,
            tools=[{"type": "image_generation"}],
        )
    except Exception as e:
        logger.error("session/continue failed: %s", e)
        raise HTTPException(status_code=502, detail=f"OpenAI API エラー: {e}")

    images = extract_b64_from_responses_api(response)
    turn = session["turn"] + 1
    sessions[req.session_id] = {"response_id": response.id, "turn": turn}
    logger.info("session/continue complete: session_id=%s images=%d", req.session_id, len(images))
    return {
        "session_id": req.session_id,
        "response_id": response.id,
        "images": images,
        "turn": turn,
    }
