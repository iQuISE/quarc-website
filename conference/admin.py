from django.contrib import admin
from django.db import models
from django.http import HttpResponse
from django.template.response import TemplateResponse

from .models import QuARCConference, QSECMember, QuARCQSECMembers, Attendee, LogisticsMARC, LogisticsHousingPreferences, LogisticsHousingAssignments, DinnerOptions, LogisticsDinner, LogisticsActivities, SwagOptions, LogisticsSwag, LogisticsBus, Acceptance, Abstract

import csv
from datetime import datetime

class QuARCFilter(admin.SimpleListFilter):
    '''
    Filters by QuARC year, defaulting to only showing most recent year.
    '''
    title = 'QuARC'
    parameter_name = 'quarc'
    filter_column = 'quarc__year'

    def lookups(self, request, model_admin):
        quarcs = QuARCConference.objects.order_by('-year')
        options = [(q.year, q) for q in quarcs]
        return [(None, 'Latest'), ('all', 'All')] + options


    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'all':
            return queryset

        quarcs = QuARCConference.objects
        if self.value() == None:
            year = quarcs.order_by('year').last().year
        else:
            year = self.value()

        return queryset.filter(**{self.filter_column: year})

class QuARCAdmin(admin.ModelAdmin):
    list_filter = [QuARCFilter]

@admin.action(description="Add QSEC members to QuARC conference")
def add_qsec_to_quarc(modeladmin, request, queryset):
    '''
    Adds multiple QSEC members to a QuARC conference.
    '''
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

def export_logistics_to_csv(modeladmin, request, queryset):
    '''
    Export a LogisticsAdmin to a csv file
    '''
    RM_FIELDS = ['ID', 'attendee', 'edit_time']
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

class AttendeeQuARCFilter(QuARCFilter):
    filter_column = 'attendee__quarc__year'

class AcceptedFilter(admin.SimpleListFilter):
    title = 'Attendee Accepted'
    parameter_name = 'accepted'

    def lookups(self, request, model_admin):
        return [('accepted', 'Accepted'), ('rejected', 'Rejected'), ('null', 'No decision')]

    def queryset(self, request, queryset):
        if self.value() == 'accepted':
            accept_type = True
        elif self.value() == 'rejected':
            accept_type = False
        elif self.value() == 'null':
            accept_type = None
        else:
            return queryset

        latest_edit_time = (Acceptance.objects.filter(attendee=models.OuterRef('attendee_id'))
                            .order_by('-edit_time').values('edit_time')[:1])
        accepted_ids = (Acceptance.objects.annotate(latest_edit_time=models.Subquery(latest_edit_time))
                                                    .filter(edit_time=models.F('latest_edit_time'))
                                                    .filter(accepted=accept_type)
                                                    .values('attendee_id'))
        return queryset.filter(attendee__in=accepted_ids)

class DroppedFilter(admin.SimpleListFilter):
    title = 'Attendee Dropped'
    parameter_name = 'dropped'

    def lookups(self, request, model_admin):
        return [('attending', 'Attending'), ('dropped', 'Dropped'), ('null', 'No decision')]

    def queryset(self, request, queryset):
        if self.value() == 'attending':
            drop_type = False
        elif self.value() == 'dropped':
            drop_type = True
        elif self.value() == 'null':
            drop_type = None
        else:
            return queryset

        latest_edit_time = (Acceptance.objects.filter(attendee=models.OuterRef('attendee_id'))
                            .order_by('-edit_time').values('edit_time')[:1])
        dropped_ids = (Acceptance.objects.annotate(latest_edit_time=models.Subquery(latest_edit_time))
                                                    .filter(edit_time=models.F('latest_edit_time'))
                                                    .filter(dropped=drop_type)
                                                    .values('attendee_id'))
        return queryset.filter(attendee__in=dropped_ids)

class LogisticsAdmin(admin.ModelAdmin):
    list_filter = [AttendeeQuARCFilter, AcceptedFilter, DroppedFilter]
    readonly_fields = ['edit_time']
    actions = [export_logistics_to_csv]

    def save_model(self, request, obj, form, change):
        '''
        We want to keep a record of logistics changes,
        so we delete the primary key to ensure a new entry is created.
        '''
        if len(form.changed_data) > 0:
            obj.pk = None
            obj.edit_time = datetime.now()
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        '''
        We want to list only the latest logistics for each attendee.
        The current method is pretty inefficient, but there doesn't seem to be a way to implement inner joins in Django.
        '''
        qs = super().get_queryset(request)
        latest_edit_time = (qs.filter(attendee=models.OuterRef('attendee_id'))
                            .order_by('-edit_time').values('edit_time')[:1])
        return qs.annotate(latest_edit_time=models.Subquery(latest_edit_time)).filter(edit_time=models.F('latest_edit_time'))

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


class AbstractAdmin(admin.ModelAdmin):
    list_filter = [AttendeeQuARCFilter, AcceptedFilter, DroppedFilter]

admin.site.register(QuARCConference)
class QuARCQSECMembersAdmin(admin.ModelAdmin):
    actions = [add_qsec_to_quarc]
admin.site.register(QSECMember, QuARCQSECMembersAdmin)
admin.site.register(QuARCQSECMembers, QuARCAdmin)

admin.site.register(Attendee, QuARCAdmin)
admin.site.register(LogisticsMARC, LogisticsAdmin)
admin.site.register(LogisticsHousingPreferences, LogisticsAdmin)
admin.site.register(LogisticsHousingAssignments, LogisticsAdmin)
admin.site.register(DinnerOptions, QuARCAdmin)
admin.site.register(LogisticsDinner, LogisticsAdmin)
admin.site.register(LogisticsActivities, LogisticsAdmin)
admin.site.register(SwagOptions, QuARCAdmin)
admin.site.register(LogisticsSwag, LogisticsAdmin)
admin.site.register(LogisticsBus, LogisticsAdmin)
admin.site.register(Acceptance, LogisticsAdmin)
admin.site.register(Abstract, AbstractAdmin)
