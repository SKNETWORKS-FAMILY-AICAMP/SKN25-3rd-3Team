"""Django admin 등록."""
from django.contrib import admin

from recipes.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "source", "created_at")
    list_filter = ("source", "created_at")
    search_fields = ("user__username", "title")
    readonly_fields = ("created_at",)
