from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class Footnote(BaseModel):
    ref: str
    text: str


class SearchResult(BaseModel):
    section_id: str
    title: str
    text: str
    snippet: str
    similarity_score: float
    requirement_type: str  # "basic" | "desirable" | "general"
    breadcrumb: str
    footnotes: list[Footnote]


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    total_chunks: int
