from django.shortcuts import render
from tour.models import Tour
from tour.regions import REGIONS

def index(request):
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

    context = {'regions': regions}
    return render(request, 'index.html', context)