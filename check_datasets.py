import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
django.setup()

from apps.evaluation.models import EvalDataset, EvalQuestion

lines = ['=== 所有评估数据集 ===']
for ds in EvalDataset.objects.all():
    qs = EvalQuestion.objects.filter(dataset=ds)
    lines.append(f'  id={ds.id}')
    lines.append(f'  name={ds.name}')
    lines.append(f'  question_count={ds.question_count}')
    lines.append(f'  实际问题数={qs.count()}')
    lines.append('')

with open('check_datasets.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('done')
