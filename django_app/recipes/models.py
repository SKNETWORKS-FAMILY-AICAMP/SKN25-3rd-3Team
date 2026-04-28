"""레시피 즐겨찾기 모델.

레시피 본 데이터는 MongoDB Atlas에 있으므로 Django ORM에는 ID + 캐시 필드만
저장합니다. 이렇게 하면:
- MongoDB의 원본이 바뀌어도 즐겨찾기 카드에는 저장 시점 정보가 남음
- 즐겨찾기 페이지 렌더링 시 MongoDB에 별도 쿼리 안 해도 카드 표시 가능
"""
from django.conf import settings
from django.db import models


class Favorite(models.Model):
    """사용자별 레시피 즐겨찾기.

    동일 사용자가 같은 레시피를 두 번 저장 못 하도록 unique_together.
    mongo_recipe_id가 비어있는 경우(웹 검색 / LLM 일반지식 결과)도 허용.
    """

    SOURCE_CHOICES = [
        ("db", "DB"),
        ("web", "웹 검색"),
        ("llm", "LLM 추정"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    # MongoDB ObjectId 문자열. 빈 문자열이면 비-DB 레시피(웹/LLM).
    mongo_recipe_id = models.CharField(max_length=64, blank=True, default="")

    # 카드 표시용 캐시 필드
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=1000, blank=True, default="")
    ingredients_summary = models.TextField(blank=True, default="")
    answer_snippet = models.TextField(
        blank=True, default="", help_text="LLM 답변 일부(저장 시점 미리보기)"
    )
    source = models.CharField(
        max_length=8, choices=SOURCE_CHOICES, default="db"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # mongo_recipe_id가 있는 경우 (DB 레시피) 중복 저장 방지
            models.UniqueConstraint(
                fields=["user", "mongo_recipe_id"],
                condition=~models.Q(mongo_recipe_id=""),
                name="uniq_user_recipe_when_id_present",
            ),
        ]
        verbose_name = "즐겨찾기 레시피"
        verbose_name_plural = "즐겨찾기 레시피들"

    def __str__(self):
        return f"{self.user.username} ★ {self.title}"

    def to_dict(self):
        return {
            "id": self.id,
            "mongo_recipe_id": self.mongo_recipe_id,
            "title": self.title,
            "url": self.url,
            "ingredients_summary": self.ingredients_summary,
            "answer_snippet": self.answer_snippet,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
        }
