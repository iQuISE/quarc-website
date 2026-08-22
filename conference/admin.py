from django.contrib import admin
from django.db import models
from django.template.response import TemplateResponse

from conference.models import QuARCConference, QSECMember, QuARCQSECMembers, Attendee, Abstract, ProgramEvent
from conference.forms import AbstractForm
from conference.admin_filters import *

from logistics.models import Acceptance, MARC, HousingPreferences, HousingAssignments, Dinner, Activities, Swag, Bus
from logistics.admin_filters import AttendeeQuARCFilter, AcceptedFilter, DroppedFilter

from datetime import datetime

# The admin panel for creating and managing conference objects
admin.site.register(QuARCConference)

class QuARCAdmin(admin.ModelAdmin):
    list_filter = [QuARCFilter]

admin.site.register(QuARCQSECMembers, QuARCAdmin)
admin.site.register(ProgramEvent, QuARCAdmin)

@admin.action(description="Add QSEC members to QuARC conference")
def add_qsec_to_quarc(modeladmin, request, queryset):
    if 'post' in request.POST:
        # Second call to this form, so we can now add the QSEC members
        quarc = QuARCConference.objects.filter(year=int(request.POST['quarc']))[0]
        for qsec_member in queryset:
            QuARCQSECMembers.objects.create(quarc=quarc, qsec_member=qsec_member)
        return None

    quarcs = QuARCConference.objects.order_by('year')

    context = {
        **modeladmin.admin_site.each_context(request), 'title': f'Add QSEC to QuARC',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'queryset': queryset, 'quarcs': quarcs,
        'module_name': modeladmin.opts.verbose_name_plural, 'opts': modeladmin.opts
    }

    return TemplateResponse(request, 'admin/add_qsec_view.html', context)

class QuARCQSECMembersAdmin(admin.ModelAdmin):
    actions = [add_qsec_to_quarc]

# For storing QSEC members; also has a function to associate them to a QuARC
admin.site.register(QSECMember, QuARCQSECMembersAdmin)

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

class AbstractAdmin(admin.ModelAdmin):
    list_filter = [AttendeeQuARCFilter, AcceptedFilter, DroppedFilter]
    readonly_fields = ('attendee',)
    form = AbstractForm

# Abstract admin panel: uses a nicer form to view abstracts
admin.site.register(Abstract, AbstractAdmin)
