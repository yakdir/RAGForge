import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
django.setup()

from apps.evaluation.models import EvalRun

lines = ['=== 评估运行记录 ===']
for run in EvalRun.objects.select_related('config').filter(status='completed'):
    lines.append(f"配置: {run.config.name}")
    lines.append(f"  Recall@5: {run.recall_at_5:.3f}")
    lines.append(f"  nDCG@5: {run.ndcg_at_5:.3f}")
    lines.append(f"  MRR: {run.mrr:.3f}")
    lines.append(f"  延迟: {run.avg_latency_ms:.0f}ms")
    lines.append('')

with open('eval_data.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done')
