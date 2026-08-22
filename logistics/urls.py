from django.urls import path

from . import views

urlpatterns = [
    path('quarc<int:year>/logistics-form/', views.logistics_page, name='logistics_page'),
    path('quarc<int:year>/logistics-closed/', views.logistics_closed, name='logistics_closed'),
]
