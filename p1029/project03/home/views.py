from django.shortcuts import render
from tour.models import Tour
from tour.regions import REGIONS
from chatbot import ai
from member.models import Member
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse
from urllib.parse import quote
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

@ensure_csrf_cookie
@never_cache
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



@never_cache
def main(request):
    # 🔒 로그인이 안 되어 있거나 쿠키가 삭제되었다면 로그인 페이지로 강제 이동!
    session_id = request.session.get('session_id') or request.session.get('member_id')
    if not session_id:
        return redirect('member:login')  # 로그인 페이
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

        session_id = request.session.get('session_id') or request.session.get('member_id')
        session_nickname = request.session.get('session_nickname')
            
        if not session_nickname and session_id:
            member = Member.objects.filter(id=session_id).first()
            if member:
                session_nickname = member.nickname

    context = {
        'regions': regions,
        'history': request.session.get('chat', []),   # 챗봇 이전 대화
        'quick': ai.QUICK_START,                       # 챗봇 추천질문
        'ai_ready': ai.ai_ready(),
        'is_authenticated': bool(session_id),
        'session_nickname': session_nickname,
    }
    return render(request, 'main.html', context)


# ==========================================
# TravelMate 맞춤 여행 추천용 관광지 API
# ==========================================

from django.views.decorators.http import require_GET
# 여기에 VISITOR_DATA_2510 전체 데이터 추가
VISITOR_DATA_2510 = {
    "20대": {
        "서울": 35031393, "경기": 25307352, "강원": 4269308,
        "부산": 8533383, "대구": 6048716, "인천": 4753981,
        "광주": 3513890, "대전": 4033452, "울산": 2119868,
        "세종": 567811, "충북": 3724190, "충남": 4591009,
        "전북": 3667118, "전남": 3975707, "경북": 5358587,
        "경남": 5509596, "제주": 1578626
    },
    "30대": {
        "서울": 40112850, "경기": 33898286, "강원": 4632996,
        "부산": 9647880, "대구": 6538082, "인천": 5889558,
        "광주": 3435714, "대전": 4089330, "울산": 2571088,
        "세종": 613173, "충북": 4375926, "충남": 5621221,
        "전북": 4103279, "전남": 4465109, "경북": 5985225,
        "경남": 6629604, "제주": 2085575
    },
    "40대": {
        "서울": 31190780, "경기": 30143600, "강원": 4625191,
        "부산": 8827971, "대구": 5537484, "인천": 5055879,
        "광주": 3032127, "대전": 3429655, "울산": 2353869,
        "세종": 536213, "충북": 4141602, "충남": 5648823,
        "전북": 4149253, "전남": 4770137, "경북": 5938088,
        "경남": 6647238, "제주": 1813435
    },
    "50대": {
        "서울": 32561187, "경기": 33514849, "강원": 5654332,
        "부산": 10209916, "대구": 6862085, "인천": 5834118,
        "광주": 3746860, "대전": 4066102, "울산": 2848048,
        "세종": 572816, "충북": 5282501, "충남": 6631264,
        "전북": 5498481, "전남": 6293078, "경북": 7465441,
        "경남": 8191258, "제주": 1901368
    },
    "60대": {
        "서울": 27068730, "경기": 27922825, "강원": 5192958,
        "부산": 10205368, "대구": 5810093, "인천": 5177050,
        "광주": 3158952, "대전": 3477823, "울산": 2397839,
        "세종": 447053, "충북": 4481026, "충남": 5517481,
        "전북": 4466489, "전남": 5078020, "경북": 6257806,
        "경남": 7069795, "제주": 1541581
    }
}


@require_GET
def recommendation_places(request):

    # 선택한 연령대
    age = request.GET.get('age', '30')

    try:
        age = int(age)
    except (ValueError, TypeError):
        age = 30

    if age not in [20, 30, 40, 50, 60]:
        age = 30

    # 전국 17개 시도 코드
    region_names = {
        'seoul': '서울',
        'busan': '부산',
        'daegu': '대구',
        'incheon': '인천',
        'gj': '광주',
        'daejeon': '대전',
        'ulsan': '울산',
        'sejong': '세종',
        'gg': '경기',
        'gw': '강원',
        'cb': '충북',
        'cn': '충남',
        'jb': '전북',
        'jn': '전남',
        'gb': '경북',
        'gn': '경남',
        'jj': '제주'
    }

    tours = Tour.objects.filter(age=age).order_by(
        'region', 'rank'
    )

    places = []

    for tour in tours:

        region_code = tour.region.lower().strip()

        if region_code not in region_names:
            continue

        places.append({
            'id': tour.id,
            'region_code': region_code,
            'region': region_names[region_code],
            'sigungu': tour.sigungu,
            'title': tour.name,
            'category': tour.category,
            'rank': tour.rank,
            'ratio': tour.ratio,
            'base_visitors': int(round(VISITOR_DATA_2510.get(f'{age}대', {}).get(region_names[region_code], 0) * (tour.ratio / 100.0)
                        )),
            'lat': tour.lat,
            'lng': tour.lng,
            'img_url': '/static/' + quote(tour.img, safe='/')
        })

    return JsonResponse({
        'status': 'success',
        'age': age,
        'count': len(places),
        'places': places
    })
