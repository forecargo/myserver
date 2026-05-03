import numpy as np

from parser import GuidelineChunk


class GuidelineSearcher:
    def __init__(self, chunks: list[GuidelineChunk], embeddings: np.ndarray):
        self.chunks = chunks
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-9, norms)
        self.normalized = embeddings / norms

    def search(self, query_vec: np.ndarray, top_k: int) -> list[tuple[GuidelineChunk, float]]:
        q = query_vec / max(float(np.linalg.norm(query_vec)), 1e-9)
        scores = self.normalized @ q
        top_k = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[int(i)], float(scores[i]) * 100) for i in top_indices]
