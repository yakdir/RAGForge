"""Retrieval config model."""
import uuid
from django.db import models
from apps.documents.models import TimeStampedModel


class RetrievalConfig(TimeStampedModel):
    """检索配置"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    retrieval_type = models.CharField(
        max_length=20,
        choices=[
            ('dense', '稠密检索'),
            ('bm25', 'BM25 检索'),
            ('hybrid', '混合检索'),
        ],
    )
    top_k = models.IntegerField(default=5)
    # 混合检索权重
    dense_weight = models.FloatField(default=0.7)
    bm25_weight = models.FloatField(default=0.3)
    # Reranker
    use_reranker = models.BooleanField(default=False)
    reranker_model = models.CharField(max_length=100, blank=True)
    reranker_top_k = models.IntegerField(default=3)

    class Meta:
        db_table = 'retrieval_configs'

    def __str__(self):
        return f"{self.name} ({self.retrieval_type})"
