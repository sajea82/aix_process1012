from django.urls import path
from . import views

app_name = 'tour'
urlpatterns = [
    path('', views.tlist, name='tlist'),
    # 지역 페이지 : /tour/region/seoul/
    path('region/<str:code>/', views.region, name='region'),
    # 세대맞춤 통계 ajax : /tour/generation/?age=20
    path('generation/', views.generation, name='generation'),
    #top10데이터 
    path('top10-data/', views.top10_data, name='top10_data'),
]