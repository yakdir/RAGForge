from django.contrib import admin
from .models import EvalDataset, EvalQuestion, EvalRun, EvalResult


@admin.register(EvalDataset)
class EvalDatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'collection', 'question_count', 'auto_generated']
    search_fields = ['name']


@admin.register(EvalQuestion)
class EvalQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'dataset', 'question_type']
    list_filter = ['question_type']


@admin.register(EvalRun)
class EvalRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'dataset', 'config', 'status', 'recall_at_5', 'mrr', 'created_at']
    list_filter = ['status']
    readonly_fields = ['recall_at_1', 'recall_at_3', 'recall_at_5', 'recall_at_10',
                       'mrr', 'ndcg_at_5', 'ndcg_at_10', 'avg_latency_ms']


@admin.register(EvalResult)
class EvalResultAdmin(admin.ModelAdmin):
    list_display = ['run', 'question', 'reciprocal_rank', 'ndcg', 'latency_ms']
