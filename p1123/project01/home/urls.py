from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.cover, name='cover'),
    path('index/', views.index, name='index'),
]
