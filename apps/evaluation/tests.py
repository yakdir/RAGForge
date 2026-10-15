"""Tests for evaluation metrics."""
import pytest
from apps.evaluation.metrics import (
    recall_at_k,
    reciprocal_rank,
    dcg_at_k,
    ndcg_at_k,
    evaluate_run,
)


class TestRecallAtK:
    """测试 Recall@K 指标"""

    def test_recall_all_hit(self):
        """全部命中"""
        retrieved = ['doc1', 'doc2', 'doc3']
        relevant = ['doc1', 'doc2']
        assert recall_at_k(retrieved, relevant, k=3) == 1.0

    def test_recall_partial_hit(self):
        """部分命中"""
        retrieved = ['doc1', 'doc4', 'doc5']
        relevant = ['doc1', 'doc2']
        assert recall_at_k(retrieved, relevant, k=3) == 0.5

    def test_recall_no_hit(self):
        """完全没命中"""
        retrieved = ['doc3', 'doc4', 'doc5']
        relevant = ['doc1', 'doc2']
        assert recall_at_k(retrieved, relevant, k=3) == 0.0

    def test_recall_k_less_than_results(self):
        """K 比结果数小"""
        retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        relevant = ['doc1', 'doc2']
        assert recall_at_k(retrieved, relevant, k=2) == 1.0

    def test_recall_empty_relevant(self):
        """相关文档为空"""
        retrieved = ['doc1', 'doc2']
        relevant = []
        assert recall_at_k(retrieved, relevant, k=3) == 0.0


class TestReciprocalRank:
    """测试 MRR / Reciprocal Rank"""

    def test_first_hit(self):
        """第一个就命中"""
        retrieved = ['doc1', 'doc2', 'doc3']
        relevant = ['doc1']
        assert reciprocal_rank(retrieved, relevant) == 1.0

    def test_second_hit(self):
        """第二个命中"""
        retrieved = ['doc_other', 'doc1', 'doc3']
        relevant = ['doc1']
        assert reciprocal_rank(retrieved, relevant) == 0.5

    def test_third_hit(self):
        """第三个命中"""
        retrieved = ['doc_other1', 'doc_other2', 'doc1']
        relevant = ['doc1']
        assert reciprocal_rank(retrieved, relevant) == pytest.approx(1/3)

    def test_no_hit(self):
        """没命中"""
        retrieved = ['doc3', 'doc4', 'doc5']
        relevant = ['doc1']
        assert reciprocal_rank(retrieved, relevant) == 0.0

    def test_multiple_relevant(self):
        """多个相关文档，取第一个命中的"""
        retrieved = ['doc_other', 'doc2', 'doc1']
        relevant = ['doc1', 'doc2']
        assert reciprocal_rank(retrieved, relevant) == 0.5


class TestDCGAtK:
    """测试 DCG@K"""

    def test_perfect_relevance(self):
        """全部最相关"""
        scores = [1.0, 1.0, 1.0]
        dcg = dcg_at_k(scores, k=3)
        assert dcg > 0

    def test_zero_relevance(self):
        """全部不相关"""
        scores = [0.0, 0.0, 0.0]
        assert dcg_at_k(scores, k=3) == 0.0

    def test_partial_relevance(self):
        """部分相关"""
        scores = [1.0, 0.0, 1.0]
        dcg = dcg_at_k(scores, k=3)
        # 第一个贡献 1.0/log2(2) = 1.0
        # 第三个贡献 (2^1-1)/log2(4) = 1/2 = 0.5
        assert dcg == pytest.approx(1.0 + 0.5)


class TestNDCGAtK:
    """测试 NDCG@K"""

    def test_perfect_ordering(self):
        """完美排序，NDCG=1"""
        retrieved = ['doc1', 'doc2', 'doc3']
        relevance_map = {'doc1': 1.0, 'doc2': 1.0, 'doc3': 1.0}
        assert ndcg_at_k(retrieved, relevance_map, k=3) == 1.0

    def test_worst_ordering(self):
        """最差排序，NDCG<1"""
        retrieved = ['doc3', 'doc2', 'doc1']
        relevance_map = {'doc1': 1.0, 'doc2': 0.5, 'doc3': 0.0}
        ndcg = ndcg_at_k(retrieved, relevance_map, k=3)
        assert ndcg < 1.0
        assert ndcg > 0

    def test_empty_relevance(self):
        """相关文档为空"""
        retrieved = ['doc1', 'doc2']
        relevance_map = {}
        assert ndcg_at_k(retrieved, relevance_map, k=3) == 0.0


class TestEvaluateRun:
    """测试完整评估函数"""

    def test_evaluate_all_metrics(self):
        """测试所有指标都算出来了"""
        retrieved = ['doc1', 'doc2', 'doc3']
        relevant = ['doc1', 'doc2']
        metrics = evaluate_run(retrieved, relevant)

        assert 'recall@1' in metrics
        assert 'recall@3' in metrics
        assert 'recall@5' in metrics
        assert 'recall@10' in metrics
        assert 'mrr' in metrics
        assert 'ndcg@5' in metrics
        assert 'ndcg@10' in metrics

    def test_evaluate_values(self):
        """测试指标值正确"""
        retrieved = ['doc1', 'doc_other', 'doc2']
        relevant = ['doc1', 'doc2']
        metrics = evaluate_run(retrieved, relevant)

        # recall@1 = 1/2 = 0.5
        assert metrics['recall@1'] == 0.5
        # recall@3 = 2/2 = 1.0
        assert metrics['recall@3'] == 1.0
        # mrr = 1/1 = 1.0
        assert metrics['mrr'] == 1.0

    def test_evaluate_no_hits(self):
        """测试完全没命中的情况"""
        retrieved = ['doc3', 'doc4', 'doc5']
        relevant = ['doc1', 'doc2']
        metrics = evaluate_run(retrieved, relevant)

        assert metrics['recall@1'] == 0.0
        assert metrics['mrr'] == 0.0
        assert metrics['ndcg@5'] == 0.0
