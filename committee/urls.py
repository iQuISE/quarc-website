from django.urls import path

from . import views

urlpatterns = [
    path('quarc<int:year>/committee/', views.index, name='conference_committee'),
]
