import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai

from embedder import embed_query, load_or_generate
from models import Footnote, SearchRequest, SearchResponse, SearchResult
from parser import parse_guideline
from searcher import GuidelineSearcher

GUIDELINE_PATH = str(
    Path(__file__).parent / "金融分野におけるサイバーセキュリティに関するガイドライン（Markdown版）.md"
)

app = FastAPI(title="Guideline Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
searcher: GuidelineSearcher | None = None
total_chunks: int = 0


@app.on_event("startup")
async def startup():
    global searcher, total_chunks
    chunks = parse_guideline(GUIDELINE_PATH)
    total_chunks = len(chunks)
    print(f"Parsed {total_chunks} chunks from guideline.")
    embeddings = load_or_generate(chunks, client, GUIDELINE_PATH)
    searcher = GuidelineSearcher(chunks, embeddings)
    print("Search index ready.")


@app.get("/health")
def health():
    return {"status": "ok", "chunks": total_chunks}


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if searcher is None:
        raise HTTPException(status_code=503, detail="Search index not ready")

    try:
        query_vec = embed_query(client, req.query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embedding API error: {e}")

    results = searcher.search(query_vec, req.query, req.top_k)

    return SearchResponse(
        results=[
            SearchResult(
                section_id=chunk.section_id,
                title=chunk.title,
                text=chunk.text,
                snippet=chunk.snippet,
                similarity_score=round(score, 1),
                requirement_type=chunk.requirement_type,
                breadcrumb=chunk.breadcrumb,
                footnotes=[Footnote(ref=fn["ref"], text=fn["text"]) for fn in chunk.footnotes],
            )
            for chunk, score in results
        ],
        query=req.query,
        total_chunks=total_chunks,
    )
