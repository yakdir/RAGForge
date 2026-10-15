import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
django.setup()

from apps.documents.models import Document, DocumentCollection

col, created = DocumentCollection.objects.get_or_create(
    name='默认知识库',
    defaults={'chroma_collection_name': 'default_collection'}
)

docs = Document.objects.filter(status='ready')
count = 0
for d in docs:
    d.collection = col
    d.save()
    count += 1

lines = [
    f'知识库: {col.name} (id={col.id})',
    f'已关联 {count} 个 ready 状态的文档',
    '',
    '=== 验证 ===',
]
for d in Document.objects.filter(status='ready'):
    lines.append(f'  {d.title} -> collection={d.collection_id}')

with open('fix_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('done')
