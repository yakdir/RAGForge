"""Document processing — 同步版本（开发环境用）"""
import logging

logger = logging.getLogger(__name__)


def process_document_sync(document_id: str):
    """
    同步处理文档：解析 → 分块 → 向量化 → 存 ChromaDB
    （开发环境直接调用，不走 Celery）
    """
    from apps.documents.models import Chunk, Document, DocumentCollection
    from apps.documents.services import (
        ChunkingStrategy,
        DocumentParser,
        EmbeddingService,
    )

    doc = Document.objects.get(id=document_id)
    doc.status = 'processing'
    doc.save(update_fields=['status'])

    try:
        # 1. 解析文档
        file_path = doc.file.path
        logger.info(f"Processing document: {doc.title} ({file_path})")
        text = DocumentParser.parse(file_path, doc.file_type)

        # 2. 分块（recursive 策略，512 大小，64 overlap）
        chunks = ChunkingStrategy.recursive(text, size=512, overlap=64)
        logger.info(f"Split into {len(chunks)} chunks")

        if not chunks:
            raise ValueError("文件解析后内容为空，无法分块")

        # 3. 存 chunk 到数据库
        chunk_objs = []
        for i, content in enumerate(chunks):
            chunk_objs.append(Chunk(
                document=doc,
                content=content,
                chunk_index=i,
                strategy='recursive',
                chunk_size=512,
                chunk_overlap=64,
                char_count=len(content),
            ))
        Chunk.objects.bulk_create(chunk_objs)

        # 4. 向量化并存入 ChromaDB
        collection, _ = DocumentCollection.objects.get_or_create(
            name='默认知识库',
            defaults={
                'chroma_collection_name': 'default_collection',
                'description': '默认文档集合',
            }
        )

        chunk_texts = [c.content for c in chunk_objs]
        chunk_ids = [str(c.id) for c in chunk_objs]

        logger.info("Encoding embeddings with bge-m3...")
        embeddings = EmbeddingService.encode(chunk_texts)

        import chromadb
        from django.conf import settings
        client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
        chroma_collection = client.get_or_create_collection(
            name=collection.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        chroma_collection.upsert(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=[{'document_id': str(doc.id)} for _ in chunk_ids],
        )

        # 5. 更新状态
        doc.chunk_count = len(chunks)
        doc.status = 'ready'
        doc.save(update_fields=['chunk_count', 'status'])

        collection.document_count = Document.objects.filter(status='ready').count()
        collection.save(update_fields=['document_count'])

        logger.info(f"Document {doc.title} processed: {len(chunks)} chunks")

    except Exception:
        logger.exception(f"Failed to process document {document_id}")
        Document.objects.filter(id=document_id).update(status='failed')
        raise
