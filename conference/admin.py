from django.conf import settings
from django.contrib import admin
from django.db import models
from django.http import HttpResponse
from wsgiref.util import FileWrapper

from conference.models import Attendee, Abstract, Session, SessionAbstract
from conference.forms import AbstractForm
from conference.admin_filters import *

from logistics.models import Acceptance, MARC, HousingPreferences, HousingAssignments, Dinner, Activities, Swag, Bus
from logistics.admin_filters import AttendeeQuARCFilter, AcceptedFilter, DroppedFilter

import csv
from datetime import datetime
import os
import tempfile, zipfile

# The admin panel for creating and managing conference objects
class QuARCAdmin(admin.ModelAdmin):
    list_filter = [QuARCFilter]

def add_attendee_acceptance(modeladmin, request, queryset, accepted):
    Acceptance.objects.filter(attendee__in=queryset.all()).update(latest=False)
    for attendee in queryset.all():
        Acceptance.objects.create(attendee=attendee, latest=True, edit_time=datetime.now(),
                                  accepted=accepted)
@admin.action(description="Accept attendees")
def accept_attendees(modeladmin, request, queryset):
    add_attendee_acceptance(modeladmin, request, queryset, True)
@admin.action(description="Reject attendees")
def reject_attendees(modeladmin, request, queryset):
    add_attendee_acceptance(modeladmin, request, queryset, False)

class AttendeeAcceptedFilter(AcceptedFilter):
    filter_param = 'pk__in'
class AttendeeDroppedFilter(DroppedFilter):
    filter_param = 'pk__in'

class AttendeeLogisticsFilter(admin.SimpleListFilter):
    title = 'Logistics'
    parameter_name = 'Logistics'

    def lookups(self, request, model_admin):
        return [('complete', 'Complete'), ('partial', 'Partial'), ('none', 'None')]

    def queryset(self, request, queryset):
        if self.value() == 'complete':
            ids = []
            ids.append(HousingPreferences.objects.filter(latest=True).values('attendee_id'))
            ids.append(Dinner.objects.filter(latest=True).values('attendee_id'))
            ids.append(Activities.objects.filter(latest=True).values('attendee_id'))
            ids.append(Swag.objects.filter(latest=True).values('attendee_id'))
            ids.append(Bus.objects.filter(latest=True).values('attendee_id'))
            return queryset.filter(**{'pk__in': id_list for id_list in ids})
        elif self.value() == 'partial':
            ids = []
            ids += HousingPreferences.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Dinner.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Activities.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Swag.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Bus.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids = list(set(ids))
            return queryset.filter(pk__in=ids)
        elif self.value() == 'none':
            ids = []
            ids += HousingPreferences.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Dinner.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Activities.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Swag.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids += Bus.objects.filter(latest=True).values_list('attendee_id', flat=True)
            ids = list(set(ids))
            return queryset.exclude(pk__in=ids)
        else:
            return queryset

class AttendeeAbstractInline(admin.StackedInline):
    extra = 0
    max_num = 0 # Don't create an abstract
    show_change_link = True
    exclude = ('author_list', 'funding_sources', 'publications', 'figure', 'figure_caption',
               'seeking_internships', 'seeking_positions', 'elevator_pitch', 'oral_presentation',
               'cqe_feature', 'resume', 'graduation_date')
    readonly_fields = ('title', 'abstract', 'research_group')
    model = Abstract

class AttendeeLogisticsInline(admin.TabularInline):
    extra = 0
    max_num = 1 # Edit existing, unless it doesn't exist
    show_change_link = True
    exclude = ('latest',)
    readonly_fields = ('edit_time',)

    def get_queryset(self, request):
        '''We want to list only the latest logistics for each attendee.'''
        return super().get_queryset(request).filter(latest=True)

class AttendeeAcceptanceInline(AttendeeLogisticsInline):
    model = Acceptance
class AttendeeLogisticsMARCInline(AttendeeLogisticsInline):
    model = MARC
class AttendeeLogisticsHousingPreferencesInline(AttendeeLogisticsInline):
    model = HousingPreferences
    fk_name = 'attendee'
class AttendeeLogisticsHousingAssignmentsInline(AttendeeLogisticsInline):
    model = HousingAssignments
    fk_name = 'attendee'
class AttendeeLogisticsDinnerInline(AttendeeLogisticsInline):
    model = Dinner
class AttendeeLogisticsActivitiesInline(AttendeeLogisticsInline):
    model = Activities
class AttendeeLogisticsSwagInline(AttendeeLogisticsInline):
    model = Swag
class AttendeeLogisticsBusInline(AttendeeLogisticsInline):
    model = Bus

class AttendeeAdmin(admin.ModelAdmin):
    list_filter = [QuARCFilter, AttendeeAcceptedFilter, AttendeeDroppedFilter, 'status',
                   AttendeeLogisticsFilter]
    actions = [accept_attendees, reject_attendees]
    inlines = (AttendeeAbstractInline, AttendeeAcceptanceInline,
               AttendeeLogisticsMARCInline, AttendeeLogisticsDinnerInline,
               AttendeeLogisticsHousingPreferencesInline, AttendeeLogisticsHousingAssignmentsInline,
               AttendeeLogisticsActivitiesInline,
               AttendeeLogisticsSwagInline, AttendeeLogisticsBusInline,)

# Attendee admin panel: slightly different filter rules and lots of inlines
admin.site.register(Attendee, AttendeeAdmin)

@admin.action(description='Download abstracts')
def download_abstracts(modeladmin, request, queryset):
    RM_FIELDS = ['ID', 'attendee', 'figure', 'resume']
    opts = modeladmin.model._meta
    filename = opts.verbose_name
    csv_tempfile = tempfile.TemporaryFile('w+')
    writer = csv.writer(csv_tempfile)

    attendee_fields = [Attendee._meta.get_field('first_name'),
                       Attendee._meta.get_field('last_name'),
                       Attendee._meta.get_field('email')]
    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    fields = [field for field in fields if field.name not in RM_FIELDS]
    # Prepare the zipfile of figures and resumes
    response = HttpResponse(content_type='application/zip',
                            headers={'Content-Disposition': 'attachment; filename=abstract_data.zip'})
    archive = zipfile.ZipFile(response, 'w', zipfile.ZIP_DEFLATED)
    # Write a first row with header information
    columns = [field.verbose_name for field in attendee_fields + fields] + ['figure', 'resume']
    print(columns)
    writer.writerow(columns)
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

        if len(obj.figure.name) > 0:
            path = obj.figure.name
            archive_filename = 'abstract_data/figures/{}{}'.format(obj.attendee.email, os.path.splitext(path)[1])
            archive.write(os.path.join(settings.MEDIA_ROOT, path), archive_filename)
            data_row.append(archive_filename)
        else:
            data_row.append('')

        if len(obj.resume.name) > 0:
            path = obj.resume.name
            archive_filename = 'abstract_data/resumes/{}{}'.format(obj.attendee.email, os.path.splitext(path)[1])
            archive.write(os.path.join(settings.MEDIA_ROOT, path), archive_filename)
            data_row.append(archive_filename)
        else:
            data_row.append('')

        writer.writerow(data_row)

    csv_tempfile.seek(0)
    archive.writestr('abstract_data/abstract_data.csv', csv_tempfile.read())
    archive.close()
    return response

class AbstractAdmin(admin.ModelAdmin):
    list_filter = [AttendeeQuARCFilter, AcceptedFilter, DroppedFilter]
    readonly_fields = ('attendee',)
    actions = [download_abstracts]
    form = AbstractForm
    list_display = ('attendee', 'title', 'research_area', 'research_group')

# Abstract admin panel: uses a nicer form to view abstracts
admin.site.register(Abstract, AbstractAdmin)

admin.site.register(Session, QuARCAdmin)

class SessionAbstractAdmin(admin.ModelAdmin):
    list_filter = [SessionQuARCFilter]

admin.site.register(SessionAbstract, SessionAbstractAdmin)

