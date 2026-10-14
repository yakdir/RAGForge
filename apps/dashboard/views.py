"""Dashboard views."""
from django.shortcuts import render
from apps.documents.models import Document, DocumentCollection
from apps.evaluation.models import EvalRun


def index(request):
    context = {
        'document_count': Document.objects.count(),
        'collection_count': DocumentCollection.objects.count(),
        'eval_run_count': EvalRun.objects.count(),
        'completed_runs': EvalRun.objects.filter(status='completed').count(),
        'recent_runs': EvalRun.objects.select_related('dataset', 'config')
                       .filter(status='completed')[:10],
    }
    return render(request, 'dashboard/index.html', context)
