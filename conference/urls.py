from django.urls import path

from . import views

urlpatterns = [
    path('quarc<int:year>/', views.index, name='conference_home'),
    path('quarc<int:year>/program/', views.program, name='program'),
    path('quarc<int:year>/abstracts/', views.abstracts, name='abstracts'),
    path('quarc<int:year>/abstracts/<int:abstract_id>', views.abstract, name='abstract'),
    path('quarc<int:year>/attend/', views.attend, name='attend'),
    path('quarc<int:year>/qsec-membership/', views.qsec_membership, name='qsec_membership'),
    path('quarc<int:year>/abstract-submission/', views.registration_abstract_submission, name='registration_abstract_submission'),
    path('quarc<int:year>/university-and-industry-personnel/', views.registration_university_industry, name='registration_university_industry'),
    path('quarc<int:year>/abstract-submission-closed/', views.registration_closed, name='registration_closed'),
]
