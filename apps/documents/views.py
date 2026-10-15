"""Document views."""
from django.shortcuts import get_object_or_404, redirect, render

from .models import Document, DocumentCollection
from .tasks import process_document_sync


def document_list(request):
    documents = Document.objects.all()
    collections = DocumentCollection.objects.all()
    return render(request, 'documents/list.html', {
        'documents': documents,
        'collections': collections,
    })


def document_upload(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        file = request.FILES.get('file')

        if not file:
            return render(request, 'documents/upload.html', {'error': '请选择文件'})

        ext = file.name.split('.')[-1].lower()
        if ext not in ['pdf', 'docx', 'md', 'txt']:
            return render(request, 'documents/upload.html', {'error': '不支持的格式，仅支持 pdf/docx/md/txt'})

        # 自动关联到默认知识库
        default_collection, _ = DocumentCollection.objects.get_or_create(
            name='默认知识库',
            defaults={'chroma_collection_name': 'default_collection'}
        )

        doc = Document.objects.create(
            title=title or file.name,
            file=file,
            file_type=ext,
            file_size=file.size,
            status='pending',
            collection=default_collection,
        )

        # 同步处理：解析 → 分块 → 向量化
        process_document_sync(str(doc.id))

        return redirect('documents:list')

    return render(request, 'documents/upload.html')


def document_detail(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    chunks = doc.chunks.all()[:20]
    return render(request, 'documents/detail.html', {
        'doc': doc,
        'chunks': chunks,
    })


def document_delete(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if request.method == 'POST':
        doc.delete()
    return redirect('documents:list')
