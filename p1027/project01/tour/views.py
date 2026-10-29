from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse
from django.db.models import Sum
from django.templatetags.static import static
from tour.models import Tour
from tour.regions import REGIONS
import csv
from pathlib import Path
from django.conf import settings
from django.templatetags.static import static
from django.http import JsonResponse


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
            image_file = Path(settings.BASE_DIR) / 'static' / 'images' / 'tour' / code / filename
            img = f'images/tour/{code}/{filename}' if image_file.exists() else 'images/tour/noimage.jpg'
            tours.append({'rank': rank, 'name': name, 'sigungu': row['시군구'],
                        'category': row['구분'], 'ratio': ratio, 'lat': lat,
                        'lng': lng, 'img': static(img)})
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