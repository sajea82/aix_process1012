
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.urls import reverse
from django.http import HttpResponseForbidden

from member.models import Member
from .models import Question, CommunityPost, CommunityComment


# =====================================
# 로그인 회원 조회
# =====================================

def get_login_member(request):
    member_id = request.session.get('session_id')

    if not member_id:
        return None

    return Member.objects.filter(id=member_id).first()


def get_member_name(member):
    if member is None:
        return ''
    return str(member.nickname)


# =====================================
# 관리자 및 작성자 확인
# =====================================

def is_admin(request):
    return bool(
        request.user.is_authenticated
        and request.user.is_staff
    )


def is_post_owner(post, member):
    if member is None or not post.member_id:
        return False

    return str(post.member_id) == str(member.id)


def is_question_owner(question, member):
    if member is None or not question.member_id:
        return False

    return str(question.member_id) == str(member.id)


def can_view_question(request, question, member):
    return (
        is_admin(request)
        or is_question_owner(question, member)
    )


# =====================================
# 커뮤니티 + 1:1 문의 메인
# =====================================

def index(request):
    login_member = get_login_member(request)

    # 로그인 여부와 관계없이 모든 문의 조회
    questions = Question.objects.all().order_by('-id')

    question_keyword = request.GET.get(
        'question_q', ''
    ).strip()

    if question_keyword:
        questions = questions.filter(
            Q(title__icontains=question_keyword) |
            Q(content__icontains=question_keyword)
        )

    # 기존 커뮤니티 목록
    keyword = request.GET.get('q', '').strip()

    posts = CommunityPost.objects.annotate(
        comment_count=Count('comments')
    ).order_by('-id')

    if keyword:
        posts = posts.filter(
            Q(title__icontains=keyword) |
            Q(content__icontains=keyword)
        )

    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    selected_post = None
    comments = []
    is_owner = False

    post_id = request.GET.get('post')

    if post_id and post_id.isdigit():
        selected_post = get_object_or_404(
            CommunityPost,
            id=int(post_id)
        )

        comments = selected_post.comments.all().order_by(
            'created_at', 'id'
        )

        is_owner = is_post_owner(
            selected_post, login_member
        )

    context = {
        'questions': questions,
        'page_obj': page_obj,
        'keyword': keyword,
        'question_keyword': question_keyword,
        'selected_post': selected_post,
        'comments': comments,
        'login_member': login_member,
        'login_member_name': get_member_name(login_member),
        'is_owner': is_owner,
    }

    return render(request, 'qna.html', context)


# =====================================
# 1:1 문의 상세
# =====================================

def qview(request, qno):
    question = get_object_or_404(Question, id=qno)
    login_member = get_login_member(request)

    return render(
        request,
        'qview.html',
        {
            'question': question,
            'is_question_owner': is_question_owner(
                question, login_member
            ),
        }
    )


# =====================================
# 1:1 문의 작성
# =====================================

@require_POST
def ask(request):
    login_member = get_login_member(request)

    if login_member is None:
        return HttpResponseForbidden(
            '로그인 후 문의를 작성할 수 있습니다.'
        )

    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()

    if title and content:
        question = Question.objects.create(
            title=title[:200],
            author=get_member_name(login_member)[:50],
            member_id=str(login_member.id),
            content=content,
        )

        return redirect(
            'qna:qview',
            qno=question.id
        )

    return redirect(
        reverse('qna:index') + '#question-panel'
    )


# =====================================
# 1:1 문의 수정
# =====================================

@require_POST
def question_edit(request, qno):
    login_member = get_login_member(request)
    question = get_object_or_404(Question, id=qno)

    if not is_question_owner(question, login_member):
        return HttpResponseForbidden(
            '본인이 작성한 문의만 수정할 수 있습니다.'
        )

    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()

    if title and content:
        question.title = title[:200]
        question.content = content
        question.save(update_fields=['title', 'content'])

    return redirect('qna:qview', qno=question.id)


# =====================================
# 1:1 문의 삭제
# =====================================

@require_POST
def question_delete(request, qno):
    login_member = get_login_member(request)
    question = get_object_or_404(Question, id=qno)

    if not is_question_owner(question, login_member):
        return HttpResponseForbidden(
            '본인이 작성한 문의만 삭제할 수 있습니다.'
        )

    question.delete()

    return redirect(
        reverse('qna:index') + '#question-panel'
    )


# =====================================
# 커뮤니티 게시글 작성 (기존 유지)
# =====================================

@require_POST
def community_write(request):
    login_member = get_login_member(request)

    if login_member is None:
        return HttpResponseForbidden(
            '로그인 후 게시글을 작성할 수 있습니다.'
        )

    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()

    if title and content:
        post = CommunityPost.objects.create(
            title=title[:200],
            author=get_member_name(login_member)[:50],
            member_id=str(login_member.id),
            content=content,
        )

        return redirect(
            reverse('qna:index') + f'?post={post.id}'
        )

    return redirect('qna:index')


# =====================================
# 커뮤니티 게시글 상세 (기존 유지)
# =====================================

def community_detail(request, post_id):
    get_object_or_404(CommunityPost, id=post_id)

    return redirect(
        reverse('qna:index') + f'?post={post_id}'
    )


# =====================================
# 커뮤니티 게시글 수정 (기존 유지)
# =====================================

@require_POST
def community_edit(request, post_id):
    login_member = get_login_member(request)
    post = get_object_or_404(CommunityPost, id=post_id)

    if not is_post_owner(post, login_member):
        return HttpResponseForbidden(
            '본인이 작성한 게시글만 수정할 수 있습니다.'
        )

    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()

    if title and content:
        post.title = title[:200]
        post.content = content
        post.save(update_fields=['title', 'content'])

    return redirect(
        reverse('qna:index') + f'?post={post.id}'
    )


# =====================================
# 커뮤니티 게시글 삭제 (기존 유지)
# =====================================

@require_POST
def community_delete(request, post_id):
    login_member = get_login_member(request)
    post = get_object_or_404(CommunityPost, id=post_id)

    if not is_post_owner(post, login_member):
        return HttpResponseForbidden(
            '본인이 작성한 게시글만 삭제할 수 있습니다.'
        )

    post.delete()
    return redirect('qna:index')


# =====================================
# 커뮤니티 댓글 등록 (기존 유지)
# =====================================

@require_POST
def community_comment(request, post_id):
    login_member = get_login_member(request)

    if login_member is None:
        return HttpResponseForbidden(
            '로그인 후 댓글을 작성할 수 있습니다.'
        )

    post = get_object_or_404(
        CommunityPost, id=post_id
    )

    content = request.POST.get(
        'content', ''
    ).strip()

    if content:
        CommunityComment.objects.create(
            post=post,
            author=get_member_name(login_member)[:50],
            content=content,
        )

    return redirect(
        reverse('qna:index') + f'?post={post.id}'
    )
