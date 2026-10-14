"""创建超级用户的一次性脚本"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.accounts.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ragforge.local', 'admin123')
    print('超级用户创建成功: admin / admin123')
else:
    print('超级用户已存在')
