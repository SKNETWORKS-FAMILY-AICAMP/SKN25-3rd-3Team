from django.apps import AppConfig


class RecipesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recipes"
    verbose_name = "냉털봇 레시피 추천"

    def ready(self):
        """앱 로드 시점에 RecipeAgent를 미리 초기화 (지연 로딩 방지).

        runserver 자동 reload 시 두 번 호출되지 않도록 RUN_MAIN 가드 사용.
        무거운 외부 클라이언트(MongoDB, OpenAI)가 첫 요청에서만 늦어지는 현상을 방지.
        """
        import os

        if os.environ.get("RUN_MAIN") != "true":
            # 자동 리로더의 부모 프로세스에서는 초기화를 건너뜁니다.
            return
        # 임포트 자체로 모듈 로딩 (RecipeAgent 인스턴스화는 views.py에서)
        try:
            from recipes.rag import pipeline  # noqa: F401
        except Exception as e:
            print(f"⚠️ RAG 파이프라인 로드 실패: {e}")
