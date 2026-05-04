import re

import numpy as np
from rank_bm25 import BM25Okapi

from parser import GuidelineChunk

_STRIP_RE = re.compile(r'[\s　【】「」。、・（）()\[\]\^]')


def _tokenize(text: str) -> list[str]:
    """Character bigram tokenization for Japanese text."""
    text = _STRIP_RE.sub('', text)
    return [text[i:i+2] for i in range(len(text) - 1)] if len(text) > 1 else list(text)


class GuidelineSearcher:
    _RRF_K = 60

    def __init__(self, chunks: list[GuidelineChunk], embeddings: np.ndarray):
        self.chunks = chunks
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-9, norms)
        self.normalized = embeddings / norms
        corpus = [_tokenize(c.text) for c in chunks]
        self.bm25 = BM25Okapi(corpus)

    def search(self, query_vec: np.ndarray, query_text: str, top_k: int) -> list[tuple[GuidelineChunk, float]]:
        n = len(self.chunks)

        q = query_vec / max(float(np.linalg.norm(query_vec)), 1e-9)
        sem_scores = self.normalized @ q

        bm25_scores = self.bm25.get_scores(_tokenize(query_text))

        top_k = min(top_k, n)
        top_indices = np.argsort(sem_scores * bm25_scores)[::-1][:top_k]

        sem_max = float(np.max(sem_scores))
        sem_min = float(np.min(sem_scores))
        bm25_max = float(np.max(bm25_scores))
        bm25_min = float(np.min(bm25_scores))

        sem_range = sem_max - sem_min if sem_max != sem_min else 1.0
        bm25_range = bm25_max - bm25_min if bm25_max != bm25_min else 1.0

        results = []
        for i in top_indices:
            i = int(i)
            norm_sem = (sem_scores[i] - sem_min) / sem_range
            norm_bm25 = (bm25_scores[i] - bm25_min) / bm25_range
            combined = 0.5 * norm_sem + 0.5 * norm_bm25
            results.append((self.chunks[i], combined * 100.0))

        results.sort(key=lambda x: x[1], reverse=True)
        return results
