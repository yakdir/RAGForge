"""Evaluation views."""
from django.shortcuts import get_object_or_404, redirect, render

from apps.documents.models import Chunk, DocumentCollection
from apps.retrieval.models import RetrievalConfig

from .models import EvalDataset, EvalQuestion, EvalRun
from .tasks import run_evaluation_sync


def dataset_list(request):
    datasets = EvalDataset.objects.all()
    collections = DocumentCollection.objects.all()
    return render(request, 'evaluation/datasets.html', {
        'datasets': datasets,
        'collections': collections,
    })


def dataset_delete(request, dataset_id):
    dataset = get_object_or_404(EvalDataset, id=dataset_id)
    if request.method == 'POST':
        dataset.delete()
    return redirect('evaluation:datasets')


def dataset_create(request):
    """自动生成评估数据集（从 chunk 生成问题）"""
    if request.method == 'POST':
        collection_id = request.POST.get('collection_id')
        name = request.POST.get('name', '测试数据集')
        num_questions = int(request.POST.get('num_questions', 10))

        collection = get_object_or_404(DocumentCollection, id=collection_id)

        # 创建数据集
        dataset = EvalDataset.objects.create(
            name=name,
            collection=collection,
            auto_generated=True,
        )

        # 随机选 chunk 生成问题
        chunks = Chunk.objects.filter(document__status='ready', document__collection=collection).order_by('?')[:num_questions]

        for chunk in chunks:
            EvalQuestion.objects.create(
                dataset=dataset,
                question=f"请总结以下内容：{chunk.content[:50]}...",
                ground_truth_answer=chunk.content,
                relevant_chunk_ids=[str(chunk.id)],
                question_type='simple',
            )

        dataset.question_count = chunks.count()
        dataset.save()

        return redirect('evaluation:datasets')

    collections = DocumentCollection.objects.all()
    return render(request, 'evaluation/dataset_create.html', {'collections': collections})


def run_list(request):
    runs = EvalRun.objects.select_related('dataset', 'config').all()
    return render(request, 'evaluation/runs.html', {'runs': runs})


def run_create(request):
    """创建并运行一次评估"""
    if request.method == 'POST':
        dataset_id = request.POST.get('dataset_id')
        retrieval_type = request.POST.get('retrieval_type', 'dense')
        top_k = int(request.POST.get('top_k', 5))

        dataset = get_object_or_404(EvalDataset, id=dataset_id)

        # 创建检索配置
        config = RetrievalConfig.objects.create(
            name=f"{dataset.name} - {retrieval_type}",
            retrieval_type=retrieval_type,
            top_k=top_k,
        )

        # 创建评估运行
        run = EvalRun.objects.create(
            dataset=dataset,
            config=config,
            status='pending',
        )

        # 同步跑评估（开发环境）
        run_evaluation_sync(str(run.id))

        return redirect('evaluation:run_detail', run_id=run.id)

    datasets = EvalDataset.objects.all()
    return render(request, 'evaluation/run_create.html', {'datasets': datasets})


def run_detail(request, run_id):
    run = get_object_or_404(EvalRun.objects.select_related('dataset', 'config'), id=run_id)
    results = run.results.select_related('question').all()
    return render(request, 'evaluation/run_detail.html', {
        'run': run,
        'results': results,
    })


def run_delete(request, run_id):
    run = get_object_or_404(EvalRun, id=run_id)
    if request.method == 'POST':
        run.delete()
    return redirect('evaluation:runs')


def grid_search(request):
    """网格搜索——自动跑多组配置对比"""
    if request.method == 'POST':
        dataset_id = request.POST.get('dataset_id')
        dataset = get_object_or_404(EvalDataset, id=dataset_id)

        # 定义要测试的配置组合
        configs = [
            {'name': '稠密 Top5', 'retrieval_type': 'dense', 'top_k': 5},
            {'name': 'BM25 Top5', 'retrieval_type': 'bm25', 'top_k': 5},
            {'name': '混合 Top5', 'retrieval_type': 'hybrid', 'top_k': 5},
            {'name': '混合 Top5 + Reranker', 'retrieval_type': 'hybrid', 'top_k': 10, 'use_reranker': True},
        ]

        runs = []
        for cfg in configs:
            config = RetrievalConfig.objects.create(**cfg)
            run = EvalRun.objects.create(
                dataset=dataset,
                config=config,
                status='pending',
            )
            run_evaluation_sync(str(run.id))
            run.refresh_from_db()
            runs.append(run)

        return render(request, 'evaluation/grid_result.html', {
            'dataset': dataset,
            'runs': runs,
        })

    datasets = EvalDataset.objects.all()
    return render(request, 'evaluation/grid_search.html', {'datasets': datasets})
