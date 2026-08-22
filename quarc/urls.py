from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='base_url'),
    path('', include('conference.urls')),
    path('', include('committee.urls')),
    path('', include('logistics.urls')),
    path('admin/', admin.site.urls),
]
