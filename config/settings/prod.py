"""Production settings."""
from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['ragforge.example.com'])

# 安全设置
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 静态文件收集
STATIC_ROOT = BASE_DIR / 'staticfiles'
