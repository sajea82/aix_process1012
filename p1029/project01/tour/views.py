from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse
from django.db.models import Sum
from django.templatetags.static import static
from tour.models import Tour
from tour.regions import REGIONS

def tlist(request):
    return HttpResponse('tour 연결 확인')


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