from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpResponse
from django.template import Template, RequestContext
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from wsgiref.util import FileWrapper

from conference.models import Attendee, Abstract, Session, SessionAbstract, AttendeeEmail
from conference.forms import AbstractForm
from conference.admin_filters import *
from conference.utils import email_attendee

from logistics.models import Acceptance, MARC, HousingPreferences, HousingAssignments, Dinner, Activities, Swag, Buses, Bus
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
@admin.action(description="Remove session assignment")
def remove_attendee_session_assignment(modeladmin, request, queryset):
    SessionAbstract.objects.filter(abstract__pk__in=queryset.values('authored_abstract__pk')).delete()
@admin.action(description="Delete attendees logistics")
def delete_attendee_logistics(modeladmin, request, queryset):
    MARC.objects.filter(attendee__pk__in=queryset.values('pk')).update(latest=False)
    HousingPreferences.objects.filter(attendee__pk__in=queryset.values('pk')).update(latest=False)
    Dinner.objects.filter(attendee__pk__in=queryset.values('pk')).update(latest=False)
    Activities.objects.filter(attendee__pk__in=queryset.values('pk')).update(latest=False)
    Swag.objects.filter(attendee__pk__in=queryset.values('pk')).update(latest=False)
    Bus.objects.filter(attendee__pk__in=queryset.values('pk')).update(latest=False)
@admin.action(description='Email attendees')
def email_attendees(modeladmin, request, queryset):
    if 'post' in request.POST:
        # Second call to this form, so we can now add the QSEC members
        subject = request.POST['subject']

        email_template = Template(request.POST['message'])

        for attendee in queryset:
            context = RequestContext(request, {'attendee': attendee})
            message = email_template.render(context)

            email_attendee(attendee, subject, message)

        return None

    context = {
        **modeladmin.admin_site.each_context(request), 'title': f'Email attendees',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'queryset': queryset, 'module_name': modeladmin.opts.verbose_name_plural,
        'opts': modeladmin.opts
    }

    return TemplateResponse(request, 'admin/email_attendees.html', context)

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

@admin.display(description='Abstract Session')
def abstract_session(abstract):
    ses_abs = SessionAbstract.objects.filter(abstract=abstract).first()
    if ses_abs is not None:
        return '{}, Poster #{}'.format(ses_abs.session.name, ses_abs.number)

class AttendeeAbstractInline(admin.StackedInline):
    extra = 0
    max_num = 0 # Don't create an abstract
    show_change_link = True
    exclude = ('author_list', 'funding_sources', 'publications', 'figure', 'figure_caption',
               'seeking_internships', 'seeking_positions', 'elevator_pitch', 'oral_presentation',
               'cqe_feature', 'resume', 'graduation_date')
    readonly_fields = ('title', 'abstract', 'research_group', abstract_session)
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
class AttendeeLogisticsBusLeaderInline(admin.TabularInline):
    model = Buses
    fk_name = 'leader'
    extra = 0
    max_num = 1
    show_change_link = False
    exclude = ('quarc', 'capacity')
    readonly_fields = ('type', 'number', 'leader_phone_number')
    verbose_name = 'Bus Leader'
    verbose_name_plural = 'Bus Leader'

    def has_add_permission(self, request, obj=None):
        return False
class AttendeeEmailInline(admin.TabularInline):
    def admin_link(self, instance):
        '''Need special admin link because AttendeeEmail is in structure, not conference.'''
        url = reverse('admin:structure_attendeeemailproxy_change', args=(instance.id,))
        return format_html(f'<a href="{url}">View</a>')

    model = AttendeeEmail
    extra = 0
    show_change_link = False
    exclude = ('html_message', 'text_message')
    readonly_fields = ('admin_link', 'timestamp', 'subject')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.display(description='Research Group')
def abstract_research_group(attendee):
    if attendee.authored_abstract:
        return attendee.authored_abstract.research_group
    else:
        return ''

@admin.display(description='Abstract Title')
def abstract_title(attendee):
    if attendee.authored_abstract:
        return attendee.authored_abstract.title
    else:
        return attendee.abstract_title

@admin.display(description='Abstract Session')
def attendee_abstract_session(attendee):
    if attendee.authored_abstract:
        return abstract_session(attendee.authored_abstract)
    else:
        return ''

@admin.display(description='Abstract Content')
def abstract_content(attendee):
    if attendee.authored_abstract:
        return attendee.authored_abstract.abstract
    else:
        return ''

def logistics_complete(attendee, model):
    return len(model.objects.filter(latest=True, attendee=attendee)) > 0
@admin.display(description='Housing Logistics', boolean=True)
def housing_logistics_complete(attendee):
    return logistics_complete(attendee, HousingPreferences)
@admin.display(description='Dinner Logistics', boolean=True)
def dinner_logistics_complete(attendee):
    return logistics_complete(attendee, Dinner)
@admin.display(description='Activities Logistics', boolean=True)
def activities_logistics_complete(attendee):
    return logistics_complete(attendee, Activities)
@admin.display(description='Swag Logistics', boolean=True)
def swag_logistics_complete(attendee):
    return logistics_complete(attendee, Swag)
@admin.display(description='Bus Logistics', boolean=True)
def bus_logistics_complete(attendee):
    return logistics_complete(attendee, Bus)
@admin.display(description='MARC Logistics', boolean=True)
def marc_logistics_complete(attendee):
    return logistics_complete(attendee, MARC)

@admin.display(description='Housing Assigned', boolean=True)
def housing_assigned(attendee):
    return logistics_complete(attendee, HousingAssignments)
@admin.display(description='Bus To Assigned', boolean=True)
def bus_to_assigned(attendee):
    return len(Bus.objects.filter(latest=True, bus_to_assignment__isnull=False,
                                  attendee=attendee)) > 0
@admin.display(description='Bus From Assigned', boolean=True)
def bus_from_assigned(attendee):
    return len(Bus.objects.filter(latest=True, bus_from_assignment__isnull=False,
                                  attendee=attendee)) > 0

class AttendeeAdmin(admin.ModelAdmin):
    list_filter = [QuARCFilter, AttendeeAcceptedFilter, AttendeeDroppedFilter, 'status',
                   AttendeeLogisticsFilter, AttendeeAbstractSessionFilter]
    list_display = ['first_name', 'last_name', 'email', 'affiliation',
                    abstract_research_group, abstract_title, attendee_abstract_session, abstract_content]
    list_display_links = ['first_name', 'last_name']
    fields = ['quarc', ('first_name', 'middle_name', 'last_name', 'suffix'),
              'email', ('status', 'affiliation'), 'authored_abstract', 'abstract_title',
              (housing_logistics_complete, dinner_logistics_complete,
               activities_logistics_complete, swag_logistics_complete,
               bus_logistics_complete, marc_logistics_complete),
              (housing_assigned, bus_to_assigned, bus_from_assigned)]
    readonly_fields = (housing_logistics_complete, dinner_logistics_complete,
                       activities_logistics_complete, swag_logistics_complete,
                       bus_logistics_complete, marc_logistics_complete,
                       housing_assigned, bus_to_assigned, bus_from_assigned)
    actions = [accept_attendees, reject_attendees, remove_attendee_session_assignment,
               delete_attendee_logistics, email_attendees]
    inlines = (AttendeeAbstractInline,
               AttendeeAcceptanceInline,
               AttendeeLogisticsDinnerInline,
               AttendeeLogisticsHousingPreferencesInline,
               AttendeeLogisticsHousingAssignmentsInline,
               AttendeeLogisticsSwagInline,
               AttendeeLogisticsBusInline,
               AttendeeLogisticsBusLeaderInline,
               AttendeeLogisticsActivitiesInline,
               AttendeeLogisticsMARCInline,
               AttendeeEmailInline)
    change_form_template = 'admin/attendee_change_form.html'

    def get_actions(self, request):
        def assign_session_gen(session):
            def assign_session(self, request, queryset):
                idx = 0
                for attendee in queryset:
                    abstract = attendee.authored_abstract
                    if abstract is None:
                        continue
                    while idx < 1000:
                        idx += 1
                        try:
                            SessionAbstract.objects.create(session=session,
                                                           abstract=abstract, number=idx)
                            break
                        except ValidationError:
                            continue
            return assign_session

        actions = super().get_actions(request)

        sessions = Session.objects.all()

        conf = None
        if request.GET is None or 'quarc' not in request.GET:
            try:
                conf = QuARCConference.objects.latest('year')
            except ObjectDoesNotExist:
                pass
        elif 'quarc' in request.GET:
            try:
                conf = get_conference(request.GET['quarc'])
            except ValueError:
                pass
        if conf is not None:
            sessions = sessions.filter(quarc=conf)

        for session in sessions:
            name = 'add_to_{}'.format(session.pk)
            actions[name] = (assign_session_gen(session), name, 'Add to {}'.format(session))

        return actions

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
@admin.action(description="Remove session assignment")
def remove_abstract_session_assignment(modeladmin, request, queryset):
    SessionAbstract.objects.filter(abstract__pk__in=queryset.values('pk')).delete()

class AbstractAdmin(admin.ModelAdmin):
    list_filter = [AttendeeQuARCFilter, AcceptedFilter, DroppedFilter, AbstractSessionFilter]
    readonly_fields = ('attendee',)
    actions = [download_abstracts, remove_abstract_session_assignment]
    form = AbstractForm
    list_display = ('attendee', 'title', 'research_area', 'research_group', abstract_session, 'abstract')

    def get_actions(self, request):
        def assign_session_gen(session):
            def assign_session(self, request, queryset):
                idx = 0
                for abstract in queryset:
                    while idx < 1000:
                        idx += 1
                        try:
                            SessionAbstract.objects.create(session=session,
                                                           abstract=abstract, number=idx)
                            break
                        except ValidationError:
                            continue
            return assign_session

        actions = super().get_actions(request)

        sessions = Session.objects.all()

        conf = None
        if request.GET is None or 'quarc' not in request.GET:
            try:
                conf = QuARCConference.objects.latest('year')
            except ObjectDoesNotExist:
                pass
        elif 'quarc' in request.GET:
            try:
                conf = get_conference(request.GET['quarc'])
            except ValueError:
                pass
        if conf is not None:
            sessions = sessions.filter(quarc=conf)

        for session in sessions:
            name = 'add_to_{}'.format(session.pk)
            actions[name] = (assign_session_gen(session), name, 'Add to {}'.format(session))

        return actions
admin.site.register(Abstract, AbstractAdmin)

class SessionAbstractInlineForm(forms.ModelForm):
    '''Form to allow filtering abstracts by QuARC year.'''
    abstract_field = forms.ModelChoiceField(queryset=Abstract.objects.none())

    class Meta:
        model = SessionAbstract
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.instance, 'session'):
            return
        quarc = getattr(self.instance.session, 'quarc', None)
        qs = Abstract.objects.order_by('attendee', 'title')
        if quarc is not None:
            qs = qs.filter(attendee__quarc=quarc)
        self.fields['abstract_field'].queryset = qs
        current_abstract = Abstract.objects.filter(pk=self.instance.abstract.pk).first()
        self.fields['abstract_field'].initial = current_abstract

class SessionAbstractInline(admin.TabularInline):
    model = SessionAbstract
    extra = 0
    show_change_link = True

    fields = ('abstract_field', 'number')

    form = SessionAbstractInlineForm

class SessionAdmin(QuARCAdmin):
    list_display = ('name', 'quarc')

    inlines = [SessionAbstractInline]

admin.site.register(Session, SessionAdmin)

class SessionAbstractAdmin(admin.ModelAdmin):
    list_filter = [SessionQuARCFilter]
    list_display = ('abstract__attendee', 'abstract', 'session', 'number',
                    'abstract__research_area', 'abstract__abstract')

# admin.site.register(SessionAbstract, SessionAbstractAdmin)

