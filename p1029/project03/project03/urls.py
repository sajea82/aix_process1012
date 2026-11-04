from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('member/', include('member.urls')),
    path('tour/', include('tour.urls')),
    path('chat/', include('chatbot.urls')),
    path('qna/', include('qna.urls')),
    path('custom/', include('custom.urls')),

]
