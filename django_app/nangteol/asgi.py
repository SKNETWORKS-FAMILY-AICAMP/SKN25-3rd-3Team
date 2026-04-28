"""ASGI 진입점 — daphne/uvicorn 등 비동기 서버 배포용."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nangteol.settings")

application = get_asgi_application()
