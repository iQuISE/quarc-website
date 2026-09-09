from django.urls import path

from . import views, api

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
    # API
    path('api<int:year>/attendees/', api.export_attendees, name='api_export_attendees'),
    path('api<int:year>/housing_preferences/', api.export_housing_preferences, name='api_export_housing_preferences'),
    path('api<int:year>/dinner/', api.export_dinner, name='api_export_dinner'),
    path('api<int:year>/activities/', api.export_activities, name='api_export_activities'),
    path('api<int:year>/swag/', api.export_swag, name='api_export_swag'),
    path('api<int:year>/bus/', api.export_bus, name='api_export_bus'),
    path('api<int:year>/housing_assignments/', api.export_housing_assignments, name='api_export_housing_assignments'),
]
