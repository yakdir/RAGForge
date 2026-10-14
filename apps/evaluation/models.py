"""Evaluation models: dataset, questions, runs, results."""
import uuid
from django.db import models
from apps.documents.models import TimeStampedModel


class EvalDataset(TimeStampedModel):
    """评估数据集"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    collection = models.ForeignKey(
        'documents.DocumentCollection',
        on_delete=models.CASCADE,
    )
    auto_generated = models.BooleanField(default=True)
    question_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'eval_datasets'

    def __str__(self):
        return self.name


class EvalQuestion(TimeStampedModel):
    """评估问题及标准答案"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(
        EvalDataset,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    question = models.TextField()
    ground_truth_answer = models.TextField()
    relevant_chunk_ids = models.JSONField(default=list)
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('simple', '简单事实'),
            ('multi_hop', '多跳推理'),
            ('adversarial', '对抗性'),
        ],
        default='simple',
    )

    class Meta:
        db_table = 'eval_questions'

    def __str__(self):
        return self.question[:50]


class EvalRun(TimeStampedModel):
    """一次评估运行"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(EvalDataset, on_delete=models.CASCADE)
    config = models.ForeignKey('retrieval.RetrievalConfig', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待运行'),
            ('running', '运行中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='pending',
        db_index=True,
    )
    # 汇总指标
    recall_at_1 = models.FloatField(null=True)
    recall_at_3 = models.FloatField(null=True)
    recall_at_5 = models.FloatField(null=True)
    recall_at_10 = models.FloatField(null=True)
    mrr = models.FloatField(null=True)
    ndcg_at_5 = models.FloatField(null=True)
    ndcg_at_10 = models.FloatField(null=True)
    avg_latency_ms = models.FloatField(null=True)

    class Meta:
        db_table = 'eval_runs'
        ordering = ['-created_at']

    def __str__(self):
        return f"EvalRun {self.id[:8]} ({self.status})"


class EvalResult(TimeStampedModel):
    """每个问题的评估结果"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(
        EvalRun,
        on_delete=models.CASCADE,
        related_name='results',
    )
    question = models.ForeignKey(EvalQuestion, on_delete=models.CASCADE)
    retrieved_chunk_ids = models.JSONField(default=list)
    recall_at_k = models.JSONField(default=dict)
    reciprocal_rank = models.FloatField(null=True)
    ndcg = models.FloatField(null=True)
    latency_ms = models.FloatField(default=0)

    class Meta:
        db_table = 'eval_results'
