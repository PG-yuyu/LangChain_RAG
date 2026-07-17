"""候选块重排 —— 基于关键词重叠率和位置加权的简单重排算法。

V1 策略（无需额外 LLM 调用）：
1. 计算查询与 chunk 的关键词重叠率
2. 位置加权（靠前的 chunk 略微加权）
3. 归一化排序
4. 返回 top_k

V2 可升级为 LLM-based 打分。
"""

import logging
import re

from contracts.models import RetrievedChunk
from rag.config import Settings, get_settings

logger = logging.getLogger("rag.reranker")


class Reranker:
    """基于关键词重叠率的重排器。"""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.top_k = self.settings.rerank_top_k

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """对候选块重新排序，返回 top_k 个。

        Args:
            query: 查询文本。
            chunks: 候选文档块列表。

        Returns:
            重排后的 top_k 个块。
        """
        if not chunks:
            logger.info("Reranking: no chunks to rerank")
            return []

        if len(chunks) <= self.top_k:
            logger.info("Reranking: %d chunks (≤ top_k=%d), returning as-is", len(chunks), self.top_k)
            # 但仍需要计算分数
            for chunk in chunks:
                chunk.score = self._compute_score(query, chunk)
            return sorted(chunks, key=lambda c: c.score, reverse=True)

        # 提取查询关键词
        query_keywords = self._tokenize(query)

        # 计算每个 chunk 的分数
        total = len(chunks)
        for idx, chunk in enumerate(chunks):
            chunk_keywords = self._tokenize(chunk.content)
            overlap_score = self._keyword_overlap(query_keywords, chunk_keywords)
            position_bonus = 1.0 - (idx / total) * 0.1  # 靠前略加权 (0.9-1.0)
            chunk.score = overlap_score * position_bonus

        # 按分数降序排列
        sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)
        top_chunks = sorted_chunks[:self.top_k]

        logger.info(
            "Reranking: %d → %d chunks (top score=%.3f, bottom score=%.3f)",
            len(chunks), len(top_chunks),
            top_chunks[0].score if top_chunks else 0,
            top_chunks[-1].score if top_chunks else 0,
        )
        return top_chunks

    # ── 评分算法 ────────────────────────────────────────────

    @staticmethod
    def _keyword_overlap(
        query_keywords: set[str],
        chunk_keywords: set[str],
    ) -> float:
        """计算关键词 Jaccard 相似度。"""
        if not query_keywords:
            return 0.0
        intersection = query_keywords & chunk_keywords
        return len(intersection) / len(query_keywords)

    @staticmethod
    def _compute_score(query: str, chunk: RetrievedChunk) -> float:
        """计算单个 chunk 的分数。"""
        qk = Reranker._tokenize(query)
        ck = Reranker._tokenize(chunk.content)
        return Reranker._keyword_overlap(qk, ck)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """简单的中英文分词：提取中文 2-gram 和英文单词。"""
        tokens: set[str] = set()

        # 英文单词
        english_words = re.findall(r"[a-zA-Z]+", text.lower())
        tokens.update(w for w in english_words if len(w) >= 2)

        # 中文 2-gram（字符级）
        chinese_text = re.sub(r"[^一-鿿]", "", text)
        for i in range(len(chinese_text) - 1):
            tokens.add(chinese_text[i:i + 2])
        # 也加入单字（用于短查询）
        tokens.update(chinese_text)

        return tokens
