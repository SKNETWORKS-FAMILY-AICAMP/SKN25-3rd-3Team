"""recipes 앱 URL 설정."""
from django.urls import path

from recipes import views

app_name = "recipes"

urlpatterns = [
    # 페이지
    path("", views.index, name="index"),
    path("favorites/", views.favorites_page, name="favorites"),
    # 인증
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/signup/", views.signup_view, name="signup"),
    # 챗 API
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/prefs/", views.prefs_api, name="prefs_api"),
    path("api/reset/", views.reset_api, name="reset_api"),
    # 즐겨찾기 API
    path("api/favorites/", views.favorites_api, name="favorites_api"),
    path(
        "api/favorites/<int:fav_id>/",
        views.favorite_delete_api,
        name="favorite_delete_api",
    ),
]
