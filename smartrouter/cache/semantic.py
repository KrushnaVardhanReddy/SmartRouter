import math


class SemanticCache:
    def __init__(self) -> None:
        self.cache: list[tuple[list[float], str]] = []

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def get_cached_response(
        self, query_embedding: list[float], threshold: float = 0.95
    ) -> str | None:
        best_match_response: str | None = None
        best_similarity = -1.0

        for cached_embedding, response in self.cache:
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_response = response

        if best_similarity >= threshold:
            return best_match_response

        return None

    async def add_to_cache(self, query_embedding: list[float], response: str) -> None:
        self.cache.append((query_embedding, response))
