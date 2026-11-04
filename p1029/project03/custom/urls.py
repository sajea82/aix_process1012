from django.urls import path
from . import views

app_name = 'custom'
urlpatterns = [
    path('t_custom/', views.t_custom, name='t_custom'), 
]
