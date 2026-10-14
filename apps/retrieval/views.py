"""Retrieval views."""
from django.shortcuts import render
from apps.documents.models import DocumentCollection, Chunk
from .services import DenseRetriever, BM25Retriever, HybridRetriever, RerankerService


def search_page(request):
    results = []
    query = ''
    retrieval_type = 'dense'
    use_reranker = False

    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        top_k = int(request.POST.get('top_k', 5))
        retrieval_type = request.POST.get('retrieval_type', 'dense')
        use_reranker = request.POST.get('use_reranker') == 'on'

        if query:
            collection = DocumentCollection.objects.first()
            if collection:
                chunks = Chunk.objects.filter(document__status='ready').values('id', 'content')
                corpus = [{'id': str(c['id']), 'content': c['content']} for c in chunks]

                # 先召回 top_k * 2 条，rerank 后再取 top_k
                recall_k = top_k * 2 if use_reranker else top_k

                if retrieval_type == 'dense':
                    retriever = DenseRetriever(collection.chroma_collection_name)
                    results = retriever.retrieve(query, top_k=recall_k)
                elif retrieval_type == 'bm25':
                    retriever = BM25Retriever(corpus)
                    results = retriever.retrieve(query, top_k=recall_k)
                elif retrieval_type == 'hybrid':
                    retriever = HybridRetriever(
                        collection.chroma_collection_name,
                        corpus,
                        dense_weight=0.7,
                        bm25_weight=0.3,
                    )
                    results = retriever.retrieve(query, top_k=recall_k)

                # 重排序
                if use_reranker and results:
                    results = RerankerService.rerank(query, results, top_k=top_k)

    return render(request, 'retrieval/search.html', {
        'query': query,
        'results': results,
        'retrieval_type': retrieval_type,
        'use_reranker': use_reranker,
    })
