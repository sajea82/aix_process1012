from django.urls import path,include
from . import views

app_name=''
urlpatterns = [
    path('', views.index, name='index'),
    path('sample/', views.sample, name='sample'),
    path('detail/', views.detail, name='detail'),
]
