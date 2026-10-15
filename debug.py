import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
django.setup()

from apps.documents.models import Document, DocumentCollection, Chunk

lines = []
lines.append('=== 知识库列表 ===')
for c in DocumentCollection.objects.all():
    lines.append(f'  id={c.id} name={c.name}')

lines.append('')
lines.append('=== 文档列表 ===')
for d in Document.objects.all():
    lines.append(f'  id={d.id} title={d.title} collection={d.collection_id} status={d.status}')

lines.append('')
lines.append(f'=== Chunk 总数: {Chunk.objects.count()} ===')

lines.append('')
lines.append('=== 查询：collection=默认知识库 的 chunk ===')
col = DocumentCollection.objects.first()
if col:
    chunks = Chunk.objects.filter(document__status='ready', document__collection=col)
    lines.append(f'  找到 {chunks.count()} 个 chunk')
    
    chunks2 = Chunk.objects.filter(document__status='ready')
    lines.append(f'  只按 status=ready 查：{chunks2.count()} 个 chunk')
    
    docs = Document.objects.filter(status='ready')
    lines.append(f'  ready 状态的文档：{docs.count()} 个')
    chunks3 = Chunk.objects.filter(document__in=docs)
    lines.append(f'  这些文档的 chunk：{chunks3.count()} 个')

with open('debug_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('done')
