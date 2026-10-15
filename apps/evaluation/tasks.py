"""Celery async evaluation tasks."""
import logging
import time

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


def _avg(values):
    return sum(values) / len(values) if values else 0.0


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_evaluation(self, eval_run_id: str):
    """异步执行一次评估运行。"""
    from apps.documents.models import Chunk
    from apps.evaluation.metrics import evaluate_run
    from apps.evaluation.models import EvalResult, EvalRun
    from apps.retrieval.services import RetrieverFactory

    try:
        eval_run = EvalRun.objects.select_related(
            'dataset', 'config'
        ).get(id=eval_run_id)

        eval_run.status = 'running'
        eval_run.save(update_fields=['status'])

        collection = eval_run.dataset.collection
        questions = eval_run.dataset.questions.all()

        chunks = Chunk.objects.filter(
            document__collection=collection
        ).values('id', 'content')
        corpus = [{'id': str(c['id']), 'content': c['content']} for c in chunks]

        total_metrics = {
            'recall@1': [], 'recall@3': [], 'recall@5': [], 'recall@10': [],
            'mrr': [], 'ndcg@5': [], 'ndcg@10': [],
        }
        total_latency = 0

        for question in questions:
            start = time.time()

            results = RetrieverFactory.retrieve_with_pipeline(
                config=eval_run.config,
                collection_name=collection.chroma_collection_name,
                corpus=corpus,
                query=question.question,
            )

            latency_ms = (time.time() - start) * 1000
            total_latency += latency_ms

            retrieved_ids = [r.chunk_id for r in results]

            relevance_map = None
            if question.relevant_chunk_ids:
                relevance_map = {cid: 2.0 for cid in question.relevant_chunk_ids}

            metrics = evaluate_run(
                retrieved_ids=retrieved_ids,
                relevant_ids=question.relevant_chunk_ids,
                relevance_map=relevance_map,
            )

            EvalResult.objects.create(
                run=eval_run,
                question=question,
                retrieved_chunk_ids=retrieved_ids,
                recall_at_k={k: v for k, v in metrics.items() if k.startswith('recall')},
                reciprocal_rank=metrics['mrr'],
                ndcg=metrics.get('ndcg@5', 0),
                latency_ms=latency_ms,
            )

            for key in total_metrics:
                if key in metrics:
                    total_metrics[key].append(metrics[key])

        with transaction.atomic():
            eval_run.recall_at_1 = _avg(total_metrics['recall@1'])
            eval_run.recall_at_3 = _avg(total_metrics['recall@3'])
            eval_run.recall_at_5 = _avg(total_metrics['recall@5'])
            eval_run.recall_at_10 = _avg(total_metrics['recall@10'])
            eval_run.mrr = _avg(total_metrics['mrr'])
            eval_run.ndcg_at_5 = _avg(total_metrics['ndcg@5'])
            eval_run.ndcg_at_10 = _avg(total_metrics['ndcg@10'])
            eval_run.avg_latency_ms = total_latency / len(questions) if questions else 0
            eval_run.status = 'completed'
            eval_run.save()

        logger.info(f"EvalRun {eval_run_id} completed: MRR={eval_run.mrr:.4f}")

    except Exception as exc:
        logger.exception(f"EvalRun {eval_run_id} failed")
        EvalRun.objects.filter(id=eval_run_id).update(status='failed')
        raise self.retry(exc=exc)


@shared_task
def run_grid_search(collection_id: str, configs: list):
    """网格搜索——批量运行多组配置"""
    from apps.evaluation.models import EvalDataset, EvalRun
    from apps.retrieval.models import RetrievalConfig

    dataset = EvalDataset.objects.filter(collection_id=collection_id).first()
    if not dataset:
        return

    for config_data in configs:
        config = RetrievalConfig.objects.create(**config_data)
        eval_run = EvalRun.objects.create(dataset=dataset, config=config)
        run_evaluation.delay(str(eval_run.id))


@shared_task
def generate_eval_questions(dataset_id: str, num_questions: int = 20):
    """从知识库自动生成评估问题"""
    from apps.documents.models import Chunk
    from apps.evaluation.models import EvalDataset, EvalQuestion

    dataset = EvalDataset.objects.get(id=dataset_id)
    chunks = Chunk.objects.filter(
        document__collection=dataset.collection
    ).order_by('?')[:num_questions]

    for chunk in chunks:
        EvalQuestion.objects.create(
            dataset=dataset,
            question=f"关于以下内容的问题：{chunk.content[:50]}...",
            ground_truth_answer=chunk.content[:200],
            relevant_chunk_ids=[str(chunk.id)],
            question_type='simple',
        )

    dataset.question_count = dataset.questions.count()
    dataset.save()


def run_evaluation_sync(eval_run_id: str):
    """同步执行评估（开发环境用，不走 Celery）"""
    import time

    from apps.documents.models import Chunk
    from apps.evaluation.metrics import evaluate_run
    from apps.evaluation.models import EvalResult, EvalRun
    from apps.retrieval.services import BM25Retriever, DenseRetriever, HybridRetriever

    eval_run = EvalRun.objects.select_related('dataset', 'config').get(id=eval_run_id)
    eval_run.status = 'running'
    eval_run.save(update_fields=['status'])

    collection = eval_run.dataset.collection
    questions = eval_run.dataset.questions.all()

    chunks = Chunk.objects.filter(document__collection=collection).values('id', 'content')
    corpus = [{'id': str(c['id']), 'content': c['content']} for c in chunks]

    total_metrics = {
        'recall@1': [], 'recall@3': [], 'recall@5': [], 'recall@10': [],
        'mrr': [], 'ndcg@5': [], 'ndcg@10': [],
    }
    total_latency = 0

    for question in questions:
        start = time.time()

        # 根据配置选择检索器
        config = eval_run.config
        if config.retrieval_type == 'dense':
            retriever = DenseRetriever(collection.chroma_collection_name)
            results = retriever.retrieve(question.question, top_k=config.top_k)
        elif config.retrieval_type == 'bm25':
            retriever = BM25Retriever(corpus)
            results = retriever.retrieve(question.question, top_k=config.top_k)
        elif config.retrieval_type == 'hybrid':
            retriever = HybridRetriever(
                collection.chroma_collection_name,
                corpus,
                dense_weight=config.dense_weight,
                bm25_weight=config.bm25_weight,
            )
            results = retriever.retrieve(question.question, top_k=config.top_k)
        else:
            results = []

        latency_ms = (time.time() - start) * 1000
        total_latency += latency_ms

        retrieved_ids = [r.chunk_id for r in results]

        relevance_map = None
        if question.relevant_chunk_ids:
            relevance_map = {cid: 2.0 for cid in question.relevant_chunk_ids}

        metrics = evaluate_run(
            retrieved_ids=retrieved_ids,
            relevant_ids=question.relevant_chunk_ids,
            relevance_map=relevance_map,
        )

        EvalResult.objects.create(
            run=eval_run,
            question=question,
            retrieved_chunk_ids=retrieved_ids,
            recall_at_k={k: v for k, v in metrics.items() if k.startswith('recall')},
            reciprocal_rank=metrics['mrr'],
            ndcg=metrics.get('ndcg@5', 0),
            latency_ms=latency_ms,
        )

        for key in total_metrics:
            if key in metrics:
                total_metrics[key].append(metrics[key])

    eval_run.recall_at_1 = _avg(total_metrics['recall@1'])
    eval_run.recall_at_3 = _avg(total_metrics['recall@3'])
    eval_run.recall_at_5 = _avg(total_metrics['recall@5'])
    eval_run.recall_at_10 = _avg(total_metrics['recall@10'])
    eval_run.mrr = _avg(total_metrics['mrr'])
    eval_run.ndcg_at_5 = _avg(total_metrics['ndcg@5'])
    eval_run.ndcg_at_10 = _avg(total_metrics['ndcg@10'])
    eval_run.avg_latency_ms = total_latency / len(questions) if questions else 0
    eval_run.status = 'completed'
    eval_run.save()

    logger.info(f"EvalRun {eval_run_id} completed: MRR={eval_run.mrr:.4f}")
