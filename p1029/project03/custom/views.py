from django.shortcuts import render
from tour.models import Tour

def t_custom(request):
    selected_region = request.GET.get('region', 'gw')
    selected_age = request.GET.get('age', '20')
    active_tab = request.GET.get('tab', 'stamp')
    
    try:
        age_val = int(selected_age)
    except ValueError:
        age_val = 20

    # 영문 지역 코드를 한글 이름으로 매핑하는 딕셔너리
    region_name_map = {
        'gw': '강원', 'gg': '경기', 'gn': '경남', 'gb': '경북',
        'dg': '대구', 'dj': '대전', 'bs': '부산', 'seoul': '서울',
        'sj': '세종', 'ulsan': '울산', 'ic': '인천', 'jb': '전북',
        'jj': '제주', 'cn': '충남', 'cb': '충북', 'gj': '광주', 'jn': '전남'
    }

    raw_regions = Tour.objects.values_list('region', flat=True).distinct()
    all_regions = [{'code': reg, 'name': region_name_map.get(reg, reg.upper())} for reg in raw_regions]

    # 선택된 지역과 연령대에 맞는 기본 쿼리셋
    base_qs = Tour.objects.filter(region=selected_region, age=age_val).order_by('rank')
    
    # 1. 혼자만의 힐링 여행 테마 (북적이는 상업·유흥시설 배제 + 사색, 예술, 자연, 전망 중심의 다채로운 장소)
    if active_tab == 'healing':
        exclude_keywords = ['영화', '시네마', '카지노', '쇼핑', '아울렛', '마트', '백화점', '경기장', '스피디움', '레저', '테마파크']
        healing_keywords = [
            '공원', '해변', '해수욕장', '수목원', '산', '둘레길', 
            '박물관', '미술관', '사찰', '절', '유적지', '고궁', 
            '전망대', '호수', '계곡', '섬', '휴양림', '산책'
        ]
        
        filtered_healing = []
        for t in base_qs:
            if any(ex in t.name or ex in t.category for ex in exclude_keywords):
                continue
            if any(kw in t.name or kw in t.category for kw in healing_keywords) or t.category in ['관광명소', '문화생활시설']:
                filtered_healing.append(t)
                
        tour_list = filtered_healing[:10] if filtered_healing else base_qs[:10]
        
    # 2. 부모님과 동반 여행 테마 (온천, 수목원, 호수, 전통문화, 편안한 명소 등 폭넓고 안심되는 코스)
    elif active_tab == 'parents':
        exclude_parents = ['카지노', '클럽', '바', '영화']
        parent_keywords = [
            '공원', '수목원', '식물원', '호수', '해변', '해수욕장', 
            '온천', '사찰', '절', '유적지', '고궁', '전통', '시장', 
            '관광명소', '명승지', '둘레길', '휴양림', '전망대'
        ]
        
        filtered_parents = []
        for t in base_qs:
            if any(ex in t.name for ex in exclude_parents):
                continue
            if any(kw in t.name or kw in t.category for kw in parent_keywords) or t.category in ['관광명소']:
                filtered_parents.append(t)
                
        tour_list = filtered_parents[:10] if filtered_parents else base_qs[:10]
        
    # 3. 도장 깨기 테마 (전체 Top 10)
    else:
        tour_list = base_qs[:10]

    age_list = ['20', '30', '40', '50', '60']

    context = {
        'all_regions': all_regions,
        'selected_region': selected_region,
        'selected_age': selected_age,
        'active_tab': active_tab,
        'tour_list': tour_list,
        'age_list': age_list,
    }
    
    return render(request, 't_custom.html', context)