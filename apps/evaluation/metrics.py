"""Evaluation metrics: Recall@K, MRR, NDCG@K."""
import math


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    """Recall@K：前 K 条结果中命中相关文档的比例。"""
    if not relevant_ids:
        return 0.0

    top_k = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    hits = top_k & relevant_set

    return len(hits) / len(relevant_set)


def reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: list[str],
) -> float:
    """RR：第一个相关结果的排名倒数。"""
    relevant_set = set(relevant_ids)
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def dcg_at_k(relevance_scores: list[float], k: int) -> float:
    """DCG@K：折扣累积增益。"""
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k]):
        dcg += (2 ** rel - 1) / math.log2(i + 2)
    return dcg


def ndcg_at_k(
    retrieved_ids: list[str],
    relevance_map: dict[str, float],
    k: int,
) -> float:
    """NDCG@K：归一化折扣累积增益。"""
    actual_relevance = [relevance_map.get(doc_id, 0.0) for doc_id in retrieved_ids[:k]]
    actual_dcg = dcg_at_k(actual_relevance, k)

    ideal_relevance = sorted(relevance_map.values(), reverse=True)[:k]
    ideal_dcg = dcg_at_k(ideal_relevance, k)

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def evaluate_run(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    relevance_map: dict[str, float] = None,
    k_values: list[int] = None,
) -> dict[str, float]:
    """对单次检索结果计算全部指标。"""
    if k_values is None:
        k_values = [1, 3, 5, 10]

    if relevance_map is None:
        relevance_map = {rid: 1.0 for rid in relevant_ids}

    metrics = {}

    for k in k_values:
        metrics[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)

    metrics["mrr"] = reciprocal_rank(retrieved_ids, relevant_ids)

    for k in [5, 10]:
        metrics[f"ndcg@{k}"] = ndcg_at_k(retrieved_ids, relevance_map, k)

    return metrics
