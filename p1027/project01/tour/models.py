from django.db import models
from django.conf import settings

class Tour(models.Model):
    region = models.CharField(max_length=20)    # 지역코드 gw, seoul...
    rank = models.IntegerField()                # 순위
    tid = models.CharField(max_length=50)       # 관광지ID
    sigungu = models.CharField(max_length=30)   # 시군구
    name = models.CharField(max_length=100)     # 관심지점명
    category = models.CharField(max_length=30)  # 구분
    age = models.IntegerField()                 # 연령대 20~60
    ratio = models.FloatField()                 # 비율
    lat = models.FloatField()                   # 위도
    lng = models.FloatField()                   # 경도

    def __str__(self):
        return f'{self.region},{self.age},{self.rank},{self.name}'

    # 사진경로 : 사진이 있으면 그 사진, 없으면 noimage
    @property
    def img(self):
        fname = self.name.replace(' ', '') + '.jpg'
        path = settings.BASE_DIR / 'static' / 'images' / 'tour' / self.region / fname
        if path.exists():
            return f'images/tour/{self.region}/{fname}'
        return 'images/tour/noimage.jpg'
