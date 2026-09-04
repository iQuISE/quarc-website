from django import forms
from django.contrib import admin
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse, path

from logistics.models import Acceptance, MARC, HousingPreferences, HousingAssignments, Dinner, Activities, Swag, Buses, Bus
from logistics.admin_filters import *
from logistics.housing_assignment import assign_housing

from conference.models import QuARCConference, Attendee
from conference.admin_filters import QuARCFilter

import csv
from datetime import datetime
from functools import update_wrapper

class QuARCAdmin(admin.ModelAdmin):
    list_filter = [QuARCFilter]

class BusesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.fields['leader'].queryset = Attendee.objects.filter(quarc=self.instance.quarc)

    class Meta:
        model = Buses
        fields = '__all__'

class BusesAdmin(QuARCAdmin):
    readonly_fields = ('leader_email', 'passengers')
    fields = ['quarc', ('type', 'number'), ('capacity', 'passengers'),
              ('leader', 'leader_email', 'leader_phone_number')]

    list_display = ['quarc', 'type', 'number', 'capacity', 'passengers',
                    'leader', 'leader_email', 'leader_phone_number']

    form = BusesForm

    def leader_email(self, bus):
        if bus.leader:
            return bus.leader.email
        else:
            return ''

    def passengers(self, bus):
        if bus.type == Buses.BusOption.Early or bus.type == Buses.BusOption.Late:
            return Bus.objects.filter(latest=True, bus_to_assignment=bus).count()
        elif bus.type == Buses.BusOption.Return:
            return Bus.objects.filter(latest=True, bus_from_assignment=bus).count()
        else:
            return 0

admin.site.register(Buses, BusesAdmin)

@admin.action(description='Export logistics to CSV')
def export_logistics_to_csv(modeladmin, request, queryset):
    RM_FIELDS = ['ID', 'attendee', 'latest', 'edit_time']
    opts = modeladmin.model._meta
    filename = opts.verbose_name
    response = HttpResponse(content_type='text/csv',
                            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'})
    writer = csv.writer(response)

    attendee_fields = [Attendee._meta.get_field('first_name'),
                       Attendee._meta.get_field('last_name'),
                       Attendee._meta.get_field('email')]
    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    fields = [field for field in fields if field.name not in RM_FIELDS]
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in attendee_fields + fields])
    # Write data rows
    for obj in queryset:
        data_row = []
        for field in attendee_fields:
            value = getattr(obj.attendee, field.name)
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d')
            data_row.append(value)
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d')
            data_row.append(value)
        writer.writerow(data_row)

    return response

class LogisticsAdmin(admin.ModelAdmin):
    list_filter = [AttendeeQuARCFilter, LatestFilter, AcceptedFilter, DroppedFilter]
    readonly_fields = ['attendee', 'latest', 'edit_time']
    actions = [export_logistics_to_csv]
    list_display = ('attendee', )

    def history_view(self, request, object_id, extra_context=None):
        "The 'history' admin view for this model."
        from django.contrib.admin.views.main import PAGE_VAR

        model = self.model
        obj = self.get_object(request, admin.utils.unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(
                request, model._meta, object_id
            )

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        fields = self.model._meta.fields
        action_list = self.model.objects.filter(attendee=obj.attendee).order_by('edit_time')

        field_names = [field.name.split('.')[-1] for field in fields]

        action_list_str = [[str(getattr(action, field)) for field in field_names]
                           for action in action_list]

        paginator = self.get_paginator(request, action_list_str, 100)
        page_number = request.GET.get(PAGE_VAR, 1)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(page_obj.number)

        context = {
            **self.admin_site.each_context(request), 'title': f'Change history: {obj.attendee}',
            'fields': field_names, 'action_list': page_obj,
            'page_range': page_range, 'page_var': PAGE_VAR, 'pagination_required': paginator.count > 100,
            'module_name': self.opts.verbose_name_plural, 'object': obj, 'opts': self.opts,
        }

        request.current_app = self.admin_site.name
        return TemplateResponse(request, 'admin/history_view.html', context)

class MARCAdmin(LogisticsAdmin):
    list_filter = LogisticsAdmin.list_filter + ['attending_marc']
    list_display = LogisticsAdmin.list_display + ('attending_marc',)
admin.site.register(MARC, MARCAdmin)

class HousingPreferencesAdmin(LogisticsAdmin):
    list_filter = LogisticsAdmin.list_filter + [HousingFilter]
    list_display = LogisticsAdmin.list_display + ('overnight_required', 'needs_roommate')
admin.site.register(HousingPreferences, HousingPreferencesAdmin)

class DinnerAdmin(LogisticsAdmin):
    list_filter = LogisticsAdmin.list_filter + ['dinner_required', DinnerRestrictionFilter]
    list_display = LogisticsAdmin.list_display + ('dinner_required', 'dinner_option',
                                                  'vegetarian', 'vegan', 'gluten_free',
                                                  'kosher', 'halal', 'other_restriction')
admin.site.register(Dinner, DinnerAdmin)

class ActivitiesAdmin(LogisticsAdmin):
    list_filter = LogisticsAdmin.list_filter + ['winter_activities']
    list_display = LogisticsAdmin.list_display + ('winter_activities',)
admin.site.register(Activities, ActivitiesAdmin)

class SwagAdmin(LogisticsAdmin):
    list_filter = LogisticsAdmin.list_filter + ['swag_option']
    list_display = LogisticsAdmin.list_display + ('swag_option',)
admin.site.register(Swag, SwagAdmin)

class BusAdmin(LogisticsAdmin):
    list_filter = LogisticsAdmin.list_filter + [BusToFilter, BusFromFilter]
    list_display = LogisticsAdmin.list_display + ('bus_to_required', 'bus_to_type', 'bus_to_assignment',
                                                  'bus_from_required', 'bus_from_assignment')

    def get_actions(self, request):
        def assign_to_bus_gen(bus):
            def assign_to_bus(self, request, queryset):
                queryset.update(bus_to_assignment=bus)
            return assign_to_bus

        def assign_from_bus_gen(bus):
            def assign_from_bus(self, request, queryset):
                queryset.update(bus_from_assignment=bus)
            return assign_from_bus

        actions = super().get_actions(request)

        to_buses = Buses.objects.filter(models.Q(type=Buses.BusOption.Early)
                                        | models.Q(type=Buses.BusOption.Late))
        from_buses = Buses.objects.filter(type=Buses.BusOption.Return)

        for to_bus in to_buses:
            name = 'add_to_{}'.format(to_bus.pk)
            actions[name] = (assign_to_bus_gen(to_bus), name, 'Add to {}'.format(to_bus))

        for from_bus in from_buses:
            name = 'add_from_{}'.format(from_bus.pk)
            actions[name] = (assign_from_bus_gen(from_bus), name, 'Add to {}'.format(from_bus))

        return actions

admin.site.register(Bus, BusAdmin)

admin.site.register(Acceptance, LogisticsAdmin)

class LogisticsHousingAssignmentsAdmin(LogisticsAdmin):
    readonly_fields = ['latest', 'edit_time']
    change_list_template = 'admin/housing_assignment_change_list.html'

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.opts.app_label, self.opts.model_name
        urls = [path('assign_housing/', wrap(self.assign_housing_view),
                     name='%s_%s_assign_housing' % info)]
        return urls + super().get_urls()

    def assign_housing_view(self, request):
        if 'post' in request.POST:
            # Second call to this form, so we can now generate housing
            quarc = QuARCConference.objects.filter(year=int(request.POST['quarc']))[0]
            assign_housing(quarc)
            info = self.opts.app_label, self.opts.model_name
            return HttpResponseRedirect(reverse('admin:%s_%s_changelist' % (info[0], info[1])))

        quarcs = QuARCConference.objects.order_by('-year')

        context = {**self.admin_site.each_context(request),
                   'title': f'Generate Housing Logistics',
                   'opts': self.opts, 'quarcs': quarcs,
                   }
        return TemplateResponse(request, 'admin/housing_assignment_view.html', context)

# Housing specific logistics (mostly automatic generation of room assignments)
admin.site.register(HousingAssignments, LogisticsHousingAssignmentsAdmin)
