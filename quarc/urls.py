from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('quarc2022/', views.perm_redirect, {'url': 'https://cqe.mit.edu/quarc2022'},
         name='quarc2022_redirect'),
    path('quarc2023/', views.perm_redirect, {'url': 'https://cqe.mit.edu/quarc2023'},
         name='quarc2023_redirect'),
    path('quarc2024/', views.perm_redirect, {'url': 'https://cqe.mit.edu/quarc2024'},
         name='quarc2024_redirect'),
    path('quarc2025/', views.perm_redirect, {'url': 'https://cqe.mit.edu/quarc2025'},
         name='quarc2025_redirect'),
    path('quarc2026/', views.perm_redirect, {'url': 'https://cqe.mit.edu/quarc2026'},
         name='quarc2026_redirect'),
    path('', views.index, name='base_url'),
    path('', include('conference.urls')),
    path('', include('committee.urls')),
    path('', include('logistics.urls')),
    path('admin/', admin.site.urls),
]

handler500 = 'conference.views.error_handler'
handler404 = 'conference.views.page_not_found'
