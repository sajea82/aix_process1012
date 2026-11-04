
from django.db import models


# =====================================
# 1:1 문의
# =====================================

class Question(models.Model):

    title = models.CharField(max_length=200)

    # 화면에 표시할 작성자 닉네임
    author = models.CharField(max_length=50)

    # 실제 작성자 회원 ID
    member_id = models.CharField(
        max_length=30,
        blank=True,
        default='',
        db_index=True,
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # 관리자 답변 (기존 기능 유지)
    answer = models.TextField(blank=True, default='')

    def __str__(self):
        return self.title


# =====================================
# 커뮤니티 게시글
# =====================================

class CommunityPost(models.Model):

    title = models.CharField(max_length=200)

    author = models.CharField(max_length=50)

    member_id = models.CharField(
        max_length=30,
        blank=True,
        default='',
        db_index=True,
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.title


# =====================================
# 커뮤니티 댓글
# =====================================

class CommunityComment(models.Model):

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.CharField(max_length=50)

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author}: {self.content[:20]}"
