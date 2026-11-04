
from django.contrib import admin
from .models import Question, CommunityPost, CommunityComment


# =====================================
# 1:1 문의 관리자
# 기존 코드 유지
# =====================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'author',
        'created_at',
        'answer_status',
    )

    list_display_links = ('id', 'title')

    search_fields = ('title', 'author', 'content')

    readonly_fields = ('created_at',)

    def answer_status(self, obj):
        if obj.answer.strip():
            return '답변 완료'
        return '답변 대기'

    answer_status.short_description = '답변 상태'


# =====================================
# 커뮤니티 게시글 관리자
# =====================================

@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'author',
        'created_at',
    )

    list_display_links = ('id', 'title')

    search_fields = (
        'title',
        'author',
        'content',
    )

    readonly_fields = ('created_at',)

    ordering = ('-id',)


# =====================================
# 커뮤니티 댓글 관리자
# =====================================

@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'post',
        'author',
        'created_at',
    )

    list_display_links = ('id', 'post')

    search_fields = (
        'author',
        'content',
    )

    readonly_fields = ('created_at',)

    ordering = ('-id',)
