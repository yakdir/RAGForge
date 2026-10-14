"""Retrieval services: dense, BM25, hybrid, and reranker."""
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    chunk_id: str
    content: str
    score: float
    source: str  # 'dense', 'bm25', 'hybrid'


class DenseRetriever:
    """稠密检索——基于 ChromaDB 向量相似度"""

    def __init__(self, collection_name: str, embedding_model: str = 'BAAI/bge-m3'):
        import chromadb
        from django.conf import settings
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_model = embedding_model

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        from apps.documents.services import EmbeddingService
        query_embedding = EmbeddingService.encode([query], self.embedding_model)[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances'],
        )

        retrieval_results = []
        if results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]
                similarity = 1 - distance  # cosine distance -> similarity
                retrieval_results.append(RetrievalResult(
                    chunk_id=chunk_id,
                    content=results['documents'][0][i],
                    score=similarity,
                    source='dense',
                ))

        return retrieval_results


class BM25Retriever:
    """BM25 稀疏检索（纯 Python 实现）"""

    def __init__(self, corpus: List[Dict[str, str]]):
        from rank_bm25 import BM25Okapi
        import jieba

        self.corpus = corpus
        self.tokenized = [list(jieba.cut(doc['content'])) for doc in corpus]
        self.bm25 = BM25Okapi(self.tokenized) if self.tokenized else None

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if not self.bm25:
            return []

        import jieba
        import numpy as np

        tokenized_query = list(jieba.cut(query))
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append(RetrievalResult(
                    chunk_id=self.corpus[idx]['id'],
                    content=self.corpus[idx]['content'],
                    score=float(scores[idx]),
                    source='bm25',
                ))

        return results


class HybridRetriever:
    """混合检索——稠密 + BM25，分数归一化后加权融合"""

    def __init__(
        self,
        collection_name: str,
        corpus: List[Dict[str, str]],
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
        embedding_model: str = 'BAAI/bge-m3',
    ):
        self.dense = DenseRetriever(collection_name, embedding_model)
        self.bm25 = BM25Retriever(corpus)
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        dense_results = self.dense.retrieve(query, top_k=top_k * 2)
        bm25_results = self.bm25.retrieve(query, top_k=top_k * 2)

        def normalize(results):
            if not results:
                return []
            scores = [r.score for r in results]
            min_s, max_s = min(scores), max(scores)
            if max_s == min_s:
                return [(r, 1.0) for r in results]
            return [(r, (r.score - min_s) / (max_s - min_s)) for r in results]

        dense_norm = normalize(dense_results)
        bm25_norm = normalize(bm25_results)

        score_map: Dict[str, Dict[str, Any]] = {}

        for r, norm_score in dense_norm:
            if r.chunk_id not in score_map:
                score_map[r.chunk_id] = {'content': r.content, 'dense': 0, 'bm25': 0}
            score_map[r.chunk_id]['dense'] = norm_score

        for r, norm_score in bm25_norm:
            if r.chunk_id not in score_map:
                score_map[r.chunk_id] = {'content': r.content, 'dense': 0, 'bm25': 0}
            score_map[r.chunk_id]['bm25'] = norm_score

        merged = []
        for chunk_id, info in score_map.items():
            final_score = (
                self.dense_weight * info['dense']
                + self.bm25_weight * info['bm25']
            )
            merged.append(RetrievalResult(
                chunk_id=chunk_id,
                content=info['content'],
                score=final_score,
                source='hybrid',
            ))

        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:top_k]


class RerankerService:
    """Reranker 服务——对初筛结果重新排序"""

    _model = None

    @classmethod
    def get_model(cls, model_name: str = 'BAAI/bge-reranker-v2-m3'):
        if cls._model is None:
            from FlagEmbedding import FlagReranker
            cls._model = FlagReranker(model_name, use_fp16=True)
        return cls._model

    @classmethod
    def rerank(
        cls,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 3,
    ) -> List[RetrievalResult]:
        if not results:
            return []

        model = cls.get_model()
        pairs = [[query, r.content] for r in results]
        scores = model.compute_score(pairs, normalize=True)

        for i, r in enumerate(results):
            r.score = float(scores[i])
            r.source = 'reranked'

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]


class RetrieverFactory:
    """检索器工厂——根据配置创建对应检索器"""

    @staticmethod
    def create(config, collection_name: str, corpus: List[Dict]):
        if config.retrieval_type == 'dense':
            return DenseRetriever(collection_name)
        elif config.retrieval_type == 'bm25':
            return BM25Retriever(corpus)
        elif config.retrieval_type == 'hybrid':
            return HybridRetriever(
                collection_name,
                corpus,
                dense_weight=config.dense_weight,
                bm25_weight=config.bm25_weight,
            )
        else:
            raise ValueError(f"Unknown retrieval type: {config.retrieval_type}")

    @staticmethod
    def retrieve_with_pipeline(config, collection_name, corpus, query) -> List[RetrievalResult]:
        """完整检索管线：检索 → 可选 rerank"""
        retriever = RetrieverFactory.create(config, collection_name, corpus)

        results = retriever.retrieve(
            query,
            top_k=config.top_k * 2 if config.use_reranker else config.top_k
        )

        if config.use_reranker and results:
            results = RerankerService.rerank(query, results, top_k=config.top_k)

        return results[:config.top_k]
