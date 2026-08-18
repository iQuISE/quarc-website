from django.contrib import admin
from django.db import models
from django.template.response import TemplateResponse

from .models import QuARCConference, QSECMember, QuARCQSECMembers, Attendee, LogisticsMARC, LogisticsHousingPreferences, LogisticsHousingAssignments, DinnerOptions, LogisticsDinner, LogisticsActivities, SwagOptions, LogisticsSwag, LogisticsBus, Acceptance, Abstract

from datetime import datetime

class QuARCAdmin(admin.ModelAdmin):
    list_filter = ['quarc__year']

class LogisticsAdmin(admin.ModelAdmin):
    list_filter = ['attendee__quarc__year']
    readonly_fields = ['edit_time']

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
            **self.admin_site.each_context(request),
            'title': f'Change history: {obj.attendee}',
            'fields': field_names,
            'action_list': page_obj,
            'page_range': page_range,
            'age_var': PAGE_VAR,
            'pagination_required': paginator.count > 100,
            'module_name': self.opts.verbose_name_plural,
            'object': obj,
            'opts': self.opts,
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/history_view.html',
            context,
        )

class AbstractAdmin(admin.ModelAdmin):
    list_filter = ['attendee__quarc__year', 'accepted', 'dropped']

admin.site.register(QuARCConference)
admin.site.register(QSECMember)
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
