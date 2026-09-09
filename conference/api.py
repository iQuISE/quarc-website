from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.db import models
from django.views.decorators.csrf import csrf_exempt

from conference.models import Attendee
from conference.admin import export_attendees_to_csv
from conference.views import error_handler, page_not_found
from conference.utils import get_conference

from logistics.admin import export_logistics_to_csv
from logistics.models import MARC, HousingPreferences, Dinner, Activities, Swag, Bus, HousingAssignments

class LiteAdmin():
    def __init__(self, model):
        self.model = model

@csrf_exempt
def export_attendees(request, year):
    if (request.method == 'POST'
        and 'username' in request.POST and 'password' in request.POST):
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
    else:
        return error_handler(request, exception=None, status_code=403)

    if not user:
        return error_handler(request, exception=None, status_code=403)
    permission = '{}.view_{}'.format(Attendee._meta.app_label, Attendee._meta.model_name)
    if not user.has_perm(permission):
        return error_handler(request, exception=None, status_code=403)

    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

    queryset = Attendee.objects.filter(quarc=conf)

    return export_attendees_to_csv(LiteAdmin(Attendee), request, queryset)

def export_logistics(request, year, model):
    if (request.method == 'POST'
        and 'username' in request.POST and 'password' in request.POST):
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
    else:
        return error_handler(request, exception=None, status_code=403)

    if not user:
        return error_handler(request, exception=None, status_code=403)
    permission = '{}.view_{}'.format(model._meta.app_label, model._meta.model_name)
    if not user.has_perm(permission):
        return error_handler(request, exception=None, status_code=403)

    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

    queryset = model.objects.filter(attendee__quarc=conf, latest=True)

    return export_logistics_to_csv(LiteAdmin(model), request, queryset)

@csrf_exempt
def export_marc(request, year):
    return export_logistics(request, year, MARC)
@csrf_exempt
def export_housing_preferences(request, year):
    return export_logistics(request, year, HousingPreferences)
@csrf_exempt
def export_dinner(request, year):
    return export_logistics(request, year, Dinner)
@csrf_exempt
def export_activities(request, year):
    return export_logistics(request, year, Activities)
@csrf_exempt
def export_swag(request, year):
    return export_logistics(request, year, Swag)
@csrf_exempt
def export_bus(request, year):
    return export_logistics(request, year, Bus)
@csrf_exempt
def export_housing_assignments(request, year):
    return export_logistics(request, year, HousingAssignments)
