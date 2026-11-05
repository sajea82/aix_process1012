from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse
from django.db.models import Sum
from django.templatetags.static import static
from tour.models import Tour
from tour.regions import REGIONS
import csv
from pathlib import Path
from django.conf import settings
import json

#두번째 페이지 top10데이터
def tlist(request):
    return render(request, 'tlist.html', {
        'regions': REGIONS,
        'selected_code': request.GET.get('region', 'seoul'),
    })

def top10_data(request):
    code = request.GET.get('region', 'seoul')
    try:
        age = int(request.GET.get('age', '20'))
    except (TypeError, ValueError):
        return JsonResponse({'error': '잘못된 연령대'}, status=400)
    region_names = dict(REGIONS)
    if code not in region_names or age not in (20, 30, 40, 50, 60):
        return JsonResponse({'error': '잘못된 지역 또는 연령대'}, status=400)
    #데이터 주소 연결
    csv_path = Path(settings.BASE_DIR) / 'data' / f'total_{age}_corrected.csv'
    if not csv_path.exists():
        return JsonResponse({'error': 'CSV 파일이 없습니다.'}, status=404)

    tours = []
    with csv_path.open('r', encoding='utf-8-sig', newline='') as file:
        for row in csv.DictReader(file):
            if row['지역코드'] != code:
                continue
            try:
                rank = int(row['순위'])
                lat, lng = float(row['위도']), float(row['경도'])
                ratio = float(row['비율'])
            except (ValueError, TypeError):
                continue
            if rank > 10:
                continue
            name = row['관심지점명']
            filename = name.replace(' ', '') + '.jpg'

            # Tour 모델의 img 프로퍼티 로직과 동일하게 맞춤
            folder = Path(settings.BASE_DIR) / 'static' / 'images' / 'tour' / code
            if (folder / filename).exists():
                img_path = f'images/tour/{code}/{filename}'
            else:
                # 한글 깨짐 대응 파일명 체크 (모델과 동일)
                filename2 = ''.join(c if ord(c) < 128 else f'#U{ord(c):04x}' for c in filename)
                if (folder / filename2).exists():
                    img_path = f'images/tour/{code}/{filename2}'
                else:
                    img_path = 'images/tour/noimage.jpg'

            tours.append({
                'rank': rank, 'name': name, 'sigungu': row['시군구'],
                'category': row['구분'], 'ratio': ratio, 'lat': lat,
                'lng': lng, 'img': static(img_path) # 만약 다른 함수들과 형식을 맞춘다면 static()을 제거하고 템플릿에서 처리할 수도 있습니다.
            })
    tours.sort(key=lambda t: t['rank'])
    return JsonResponse({'region_name': region_names[code], 'tours': tours[:10]})


# 지역 페이지 : 연령대별 TOP10
def region(request, code):
    name = dict(REGIONS).get(code)
    if name is None:
        raise Http404('없는 지역입니다.')

    age = int(request.GET.get('age', 20))
    tours = Tour.objects.filter(region=code, age=age).order_by('rank')[:10]

    context = {
        'code': code, 'name': name, 'age': age,
        'ages': [20, 30, 40, 50, 60],
        'tours': tours,
    }
    return render(request, 'region.html', context)


# 세대맞춤 통계 - ajax (메인 8단계)
def generation(request):
    age = int(request.GET.get('age', 20))
    qs = Tour.objects.filter(age=age)

    # 1. 유형(구분)별 비율 합계 → 17개 지역 평균
    cats = qs.values('category').annotate(total=Sum('ratio')).order_by('-total')
    labels = [c['category'] for c in cats]
    values = [round(c['total'] / len(REGIONS), 1) for c in cats]

    # 2. 비율 높은 관광지 8곳 (지역마다 1곳씩)
    names = dict(REGIONS)
    top = []
    used = set()
    for t in qs.order_by('-ratio'):
        if t.region in used:
            continue
        used.add(t.region)
        top.append({
            'name': t.name,
            'code': t.region,
            'region': names[t.region],
            'sigungu': t.sigungu,
            'ratio': t.ratio,
            'img': static(t.img),
        })
        if len(top) == 8:
            break

    context = {'age': age, 'labels': labels, 'values': values, 'top': top}
    return JsonResponse(context)


# 그래프 페이지 : /tour/graph_v1/
def graph_v1(request):
    return render(request, 'graph_v1.html')

#tour의 views.py 추가
def resv(request):
    # 필요한 필드만 가져와서 리스트로 변환 (순위순 정렬)
    tours = Tour.objects.values('region', 'name', 'lat', 'lng', 'rank').order_by('rank')

    # 연령대(age)별로 동일한 관광지가 중복 들어있으므로 (지역, 관광지명) 기준으로 중복 제거
    unique_spots = []
    seen = set()
    for t in tours:
        key = (t['region'], t['name'])
        if key not in seen and t['lat'] and t['lng']:
            seen.add(key)
            unique_spots.append({
                'region': str(t['region']).strip().lower(),
                'name': t['name'],
                'lat': float(t['lat']),
                'lng': float(t['lng'])
            })

    context = {
        # 템플릿의 자바스크립트에서 바로 쓸 수 있도록 JSON 문자열로 변환
        'db_spots_json': json.dumps(unique_spots, ensure_ascii=False)
    }
    return render(request, 'resv.html', context)


# =====================================================================
# 추천 알고리즘 API 뷰 (실제 Tour 모델 및 img 프로퍼티 연동)
# =====================================================================
def get_tour_recommendations(request):
    if request.method == 'GET':
        raw_age_param = request.GET.get('age', '30대')
        
        # 특수문자(+) 및 '이상' 등의 수식어를 제거하여 순수 숫자 및 대(代) 단위 추출 (예: '60대+' -> '60대')
        age_param = raw_age_param.replace('+', '').replace('이상', '').strip()
        
        # 연령대 키 정밀 매칭 (VISITOR_DATA_2510의 키: '20대', '30대', '40대', '50대', '60대')
        age_key = '30대'
        age_val = 30
        if '20' in age_param: 
            age_key = '20대'
            age_val = 20
        elif '30' in age_param: 
            age_key = '30대'
            age_val = 30
        elif '40' in age_param: 
            age_key = '40대'
            age_val = 40
        elif '50' in age_param: 
            age_key = '50대'
            age_val = 50
        elif '60' in age_param or '70' in age_param: 
            age_key = '60대'
            age_val = 60

        # 1. 25년 10월(index 1) 광역시도별·연령대별 방문자수 데이터 직접 내장 (파일 경로 오류로 인한 0명 출력 원천 차단)
        VISITOR_DATA_2510 = {
            "20대": {
                "서울": 35031393, "경기": 25307352, "강원": 4269308, "부산": 8533383,
                "대구": 6048716, "인천": 4753981, "광주": 3513890, "대전": 4033452,
                "울산": 2119868, "세종": 567811, "충북": 3724190, "충남": 4591009,
                "전북": 3667118, "전남": 3975707, "경북": 5358587, "경남": 5509596, "제주": 1578626
            },
            "30대": {
                "서울": 40112850, "경기": 33898286, "강원": 4632996, "부산": 9647880,
                "대구": 6538082, "인천": 5889558, "광주": 3435714, "대전": 4089330,
                "울산": 2571088, "세종": 613173, "충북": 4375926, "충남": 5621221,
                "전북": 4103279, "전남": 4465109, "경북": 5985225, "경남": 6629604, "제주": 2085575
            },
            "40대": {
                "서울": 31190780, "경기": 30143600, "강원": 4625191, "부산": 8827971,
                "대구": 5537484, "인천": 5055879, "광주": 3032127, "대전": 3429655,
                "울산": 2353869, "세종": 536213, "충북": 4141602, "충남": 5648823,
                "전북": 4149253, "전남": 4770137, "경북": 5938088, "경남": 6647238, "제주": 1813435
            },
            "50대": {
                "서울": 32561187, "경기": 33514849, "강원": 5654332, "부산": 10209916,
                "대구": 6862085, "인천": 5834118, "광주": 3746860, "대전": 4066102,
                "울산": 2848048, "세종": 572816, "충북": 5282501, "충남": 6631264,
                "전북": 5498481, "전남": 6293078, "경북": 7465441, "경남": 8191258, "제주": 1901368
            },
            "60대": {
                "서울": 27068730, "경기": 27922825, "강원": 5192958, "부산": 10205368,
                "대구": 5810093, "인천": 5177050, "광주": 3158952, "대전": 3477823,
                "울산": 2397839, "세종": 447053, "충북": 4481026, "충남": 5517481,
                "전북": 4466489, "전남": 5078020, "경북": 6257806, "경남": 7069795, "제주": 1541581
            }
        }
        
        visitor_map = dict(VISITOR_DATA_2510.get(age_key, VISITOR_DATA_2510["30대"]))

        # 2. DB 지역 코드 맵핑 딕셔너리 (사용자 작성본 유지 + db.sqlite3의 bs, dg, ic 약어 호환 추가)
        code_to_korean = {
            'seoul': '서울', 'SEOUL': '서울', '서울': '서울',
            'gg': '경기', 'GG': '경기', '경기': '경기', 'gyeonggi': '경기',
            'incheon': '인천', 'INCHEON': '인천', '인천': '인천', 'ic': '인천', 'IC': '인천',
            'gw': '강원', 'GW': '강원', '강원': '강원', 'gangwon': '강원',
            'cb': '충북', 'CB': '충북', '충북': '충북', 'chungbuk': '충북',
            'cn': '충남', 'CN': '충남', '충남': '충남', 'chungnam': '충남',
            'dj': '대전', 'daejeon': '대전', 'DAEJEON': '대전', '대전': '대전',
            'sj': '세종', 'SJ': '세종', '세종': '세종', 'sejong': '세종',
            'jb': '전북', 'JB': '전북', '전북': '전북', 'jeonbuk': '전북',
            'jn': '전남', 'JN': '전남', '전남': '전남', 'jeonnam': '전남',
            'gj': '광주', 'gwangju': '광주', 'GWANGJU': '광주', '광주': '광주',
            'gn': '경북', 'GN': '경북', '경북': '경북', 'gb': '경북', 'gyeongbuk': '경북',
            'gs': '경남', 'GS': '경남', '경남': '경남', 'gyeongnam': '경남',
            'daegu': '대구', 'DAEGU': '대구', '대구': '대구', 'dg': '대구', 'DG': '대구',
            'ulsan': '울산', 'ULSAN': '울산', '울산': '울산',
            'busan': '부산', 'BUSAN': '부산', '부산': '부산', 'bs': '부산', 'BS': '부산',
            'jj': '제주', 'JJ': '제주', '제주': '제주', 'jeju': '제주',
        }

        # 3. DB에서 사용자가 선택한 연령대(age=age_val) 데이터만 필터링하여 조회
        tours = Tour.objects.filter(age=age_val)
        if not tours.exists():
            tours = Tour.objects.all()

        # 4. 개별 관광지(장소)별 방문자수 계산: (광역시도 10월 방문자수) * (관광지 비율 % / 100)
        spot_list = []
        for t in tours:
            raw_reg = str(t.region).strip().lower()
            norm_region = code_to_korean.get(raw_reg, code_to_korean.get(str(t.region).strip(), str(t.region).strip()))
            
            # 해당 광역시도의 25년 10월 전체 방문자수
            region_total_visitors = visitor_map.get(norm_region, 0)
            
            # 장소별 방문자수 산출: 광역시도 방문자수 * (장소 비율 / 100)
            spot_visitors = int(round(region_total_visitors * (float(t.ratio) / 100.0)))

            spot_list.append({
                'region': norm_region,
                'sigungu': t.sigungu,
                'title': t.name,
                'category': t.category,
                'visitor_count': spot_visitors,
                'region_visitors': region_total_visitors,
                'ratio': t.ratio,
                'img_url': static(t.img),
                'description': f"{age_key} 방문객이 선호하는 {norm_region} {t.sigungu}의 인기 명소입니다.<br>(25년 10월 약 {spot_visitors:,}명 방문)"
            })

        # 5. 계산된 장소별 방문자수(visitor_count) 기준으로 전국 내림차순 정렬 후 TOP 3 추출
        sorted_spots = sorted(spot_list, key=lambda x: x['visitor_count'], reverse=True)
        results = sorted_spots[:3]

        return JsonResponse({'status': 'success', 'recommendations': results})

    return JsonResponse({'status': 'fail'}, status=400)

    
