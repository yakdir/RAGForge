from django.contrib import admin
from .models import RetrievalConfig


@admin.register(RetrievalConfig)
class RetrievalConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'retrieval_type', 'top_k', 'use_reranker', 'created_at']
    list_filter = ['retrieval_type', 'use_reranker']
    search_fields = ['name']
