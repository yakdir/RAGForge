from django.contrib import admin

from .models import Chunk, Document, DocumentCollection


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'status', 'chunk_count', 'created_at']
    list_filter = ['status', 'file_type']
    search_fields = ['title']


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'strategy', 'chunk_size', 'char_count']
    list_filter = ['strategy']


@admin.register(DocumentCollection)
class DocumentCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'embedding_model', 'chunk_strategy', 'chunk_size', 'document_count']
    search_fields = ['name']
