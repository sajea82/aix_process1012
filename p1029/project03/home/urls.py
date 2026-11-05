from django.urls import path
from . import views

app_name = ''
urlpatterns = [
    path('', views.index, name='index'),
    path('main/', views.main, name='main'),
    path('api/recommendation-places/',views.recommendation_places,name='recommendation_places'),
]
