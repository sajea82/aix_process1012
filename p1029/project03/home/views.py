from django.shortcuts import render
from tour.models import Tour
from tour.regions import REGIONS
from chatbot import ai
from member.models import Member
from tour.models import Tour  # tour 앱의 Tour 모델 임포트
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse

# 1. 온보딩(index) 뷰
def index(request):
    regions = [
        "서울", "경기", "인천", "강원", "충북", "충남", "대전", "세종", 
        "전북", "전남", "광주", "경북", "경남", "대구", "울산", "부산", "제주"
    ]
    
    # 세션에 저장된 닉네임 및 로그인 여부 추출
    session_id = request.session.get('session_id') or request.session.get('member_id')
    session_nickname = request.session.get('session_nickname')
    
    if not session_nickname and session_id:
        member = Member.objects.filter(id=session_id).first()
        if member:
            session_nickname = member.nickname

    context = {
        'regions': regions,
        'is_authenticated': bool(session_id),
        'session_nickname': session_nickname,
    }
    return render(request, 'index.html', context)




def main(request):
    regions = []
    for code, name in REGIONS:
        # 그 지역에서 비율이 높은 순서로 정렬
        qs = Tour.objects.filter(region=code).order_by('-ratio')

        # 사진이 있는 관광지 중 가장 인기 있는 곳을 대표로
        rep = qs.first()
        for t in qs:
            if 'noimage' not in t.img:
                rep = t
                break

        regions.append({'code': code, 'name': name, 'img': rep.img, 'spot': rep.name})

    context = {
        'regions': regions,
        'history': request.session.get('chat', []),   # 챗봇 이전 대화
        'quick': ai.QUICK_START,                       # 챗봇 추천질문
        'ai_ready': ai.ai_ready(),
    }
    return render(request, 'main.html', context)
