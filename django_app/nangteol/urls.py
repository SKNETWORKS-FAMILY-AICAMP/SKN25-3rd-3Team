"""프로젝트 루트 URL 설정.

/admin/  — Django 관리자
/        — recipes 앱 라우트 (UI + /api/chat/)
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("recipes.urls")),
]
