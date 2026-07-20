"""Deterministic embedding implementations for local and test use."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable


class HashEmbeddingFunction:
    """Stable hash embedding used when no online model is configured."""

    def __init__(self, dimension: int = 384):
        if dimension <= 0:
            raise ValueError("embedding dimension must be positive")
        self.dimension = dimension

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        """Chroma-compatible callable interface."""

        return self.embed_documents(list(input))

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    def embed(self, text: str) -> list[float]:
        tokens = self._tokenize(text)
        vector = [0.0] * self.dimension
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            bucket = int.from_bytes(digest[:8], "big") % self.dimension
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            weight = 1.0 + digest[9] / 255.0
            vector[bucket] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        normalized = (text or "").lower()
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", normalized)
        return tokens or ["__empty__"]


def create_embedding_function(
    provider: str = "hash",
    dimension: int = 384,
) -> HashEmbeddingFunction:
    """Create an embedding function by provider name."""

    provider_name = (provider or "hash").lower()
    if provider_name != "hash":
        raise ValueError(
            f"unsupported embedding provider '{provider}'; only 'hash' is available now",
        )
    return HashEmbeddingFunction(dimension=dimension)
