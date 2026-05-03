import hashlib
import json
import time
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from parser import GuidelineChunk

EMBED_MODEL = "gemini-embedding-001"
CACHE_FILE = "embeddings_cache.json"


def _file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _embed_text(client: genai.Client, text: str, task_type: str) -> list[float]:
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return result.embeddings[0].values


def load_or_generate(
    chunks: list[GuidelineChunk],
    client: genai.Client,
    guideline_path: str,
) -> np.ndarray:
    source_hash = _file_hash(guideline_path)
    cache_path = Path(guideline_path).parent / CACHE_FILE

    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
        if cache.get("source_hash") == source_hash and len(cache.get("embeddings", [])) == len(chunks):
            print(f"Loaded {len(chunks)} embeddings from cache.")
            return np.array(cache["embeddings"], dtype=np.float32)

    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = []
    for i, chunk in enumerate(chunks):
        vec = _embed_text(client, chunk.embed_text, "RETRIEVAL_DOCUMENT")
        embeddings.append(vec)
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(chunks)} done")
        time.sleep(0.3)

    cache_data = {
        "source_hash": source_hash,
        "embeddings": [e for e in embeddings],
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f)
    print("Embeddings cached.")
    return np.array(embeddings, dtype=np.float32)


def embed_query(client: genai.Client, text: str) -> np.ndarray:
    vec = _embed_text(client, text, "RETRIEVAL_QUERY")
    return np.array(vec, dtype=np.float32)
