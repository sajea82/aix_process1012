
from django.urls import path
from . import views

app_name = 'qna'

urlpatterns = [

    # 커뮤니티 + 1:1 문의 메인
    path('', views.index, name='index'),

    # =====================================
    # 1:1 문의
    # =====================================

    path(
        'ask/',
        views.ask,
        name='ask'
    ),

    path(
        'qview/<int:qno>/',
        views.qview,
        name='qview'
    ),

    path(
        'qview/<int:qno>/edit/',
        views.question_edit,
        name='question_edit'
    ),

    path(
        'qview/<int:qno>/delete/',
        views.question_delete,
        name='question_delete'
    ),

    # =====================================
    # 커뮤니티
    # =====================================

    path(
        'community/write/',
        views.community_write,
        name='community_write'
    ),

    path(
        'community/<int:post_id>/',
        views.community_detail,
        name='community_detail'
    ),

    path(
        'community/<int:post_id>/comment/',
        views.community_comment,
        name='community_comment'
    ),

    path(
        'community/<int:post_id>/edit/',
        views.community_edit,
        name='community_edit'
    ),

    path(
        'community/<int:post_id>/delete/',
        views.community_delete,
        name='community_delete'
    ),

]
