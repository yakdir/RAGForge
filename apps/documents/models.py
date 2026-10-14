"""Document and Chunk models."""
import uuid
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Document(TimeStampedModel):
    """上传的文档"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/%Y/%m/')
    file_type = models.CharField(max_length=20)  # pdf, docx, md, txt
    file_size = models.BigIntegerField()  # bytes
    chunk_count = models.IntegerField(default=0)
    collection = models.ForeignKey(
        'DocumentCollection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('ready', '就绪'),
            ('failed', '失败'),
        ],
        default='pending',
        db_index=True,
    )

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Chunk(TimeStampedModel):
    """文档分块"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    content = models.TextField()
    chunk_index = models.IntegerField()  # 在文档中的顺序
    token_count = models.IntegerField(default=0)
    char_count = models.IntegerField(default=0)

    # 分块策略元数据
    strategy = models.CharField(max_length=50)  # fixed, recursive, semantic
    chunk_size = models.IntegerField()
    chunk_overlap = models.IntegerField(default=0)

    class Meta:
        db_table = 'chunks'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"


class DocumentCollection(TimeStampedModel):
    """文档集合（知识库）"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    chroma_collection_name = models.CharField(max_length=255, unique=True)
    embedding_model = models.CharField(max_length=100, default='bge-m3')
    chunk_strategy = models.CharField(max_length=50, default='recursive')
    chunk_size = models.IntegerField(default=512)
    chunk_overlap = models.IntegerField(default=64)
    document_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'document_collections'

    def __str__(self):
        return self.name
