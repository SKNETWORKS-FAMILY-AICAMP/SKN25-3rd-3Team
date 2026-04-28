"""WSGI 진입점 — gunicorn/uwsgi 등 동기 서버 배포용."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nangteol.settings")

application = get_wsgi_application()
