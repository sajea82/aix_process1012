from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F
from django.core.paginator import Paginator
from customer.models import Board
from member.models import Member


# 목록 : 10개씩 페이지 나누기
def clist(request):
    qs = Board.objects.all().order_by('-bgroup', 'bstep')
    paginator = Paginator(qs, 10)                 # 한 페이지에 10개
    page = request.GET.get('page', 1)             # ?page=2 → 2, 없으면 1
    list = paginator.get_page(page)
    context = {'list': list}
    return render(request, 'clist.html', context)


# 글 보기 : 조회수 +1
def cview(request, bno):
    Board.objects.filter(bno=bno).update(bhit=F('bhit') + 1)
    board = get_object_or_404(Board, bno=bno)
    context = {'board': board}
    return render(request, 'cview.html', context)


# 글쓰기 : 로그인한 사람만
def cwrite(request):
    if not request.session.get('session_id'):     # 로그인 안 했으면
        return redirect('member:login')

    if request.method == 'GET':
        return render(request, 'cwrite.html')

    member = Member.objects.get(id=request.session['session_id'])
    board = Board.objects.create(
        member   = member,
        btitle   = request.POST.get('btitle', ''),
        bcontent = request.POST.get('bcontent', ''),
    )
    board.bgroup = board.bno                      # 답변달기용 그룹번호 = 자기 글번호
    board.save()
    return redirect('customer:cview', board.bno)


# 삭제 : 본인 글만
def cdelete(request, bno):
    board = get_object_or_404(Board, bno=bno)
    if board.member and board.member.id == request.session.get('session_id'):
        board.delete()
    return redirect('customer:clist')