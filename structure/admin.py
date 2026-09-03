from django.contrib import admin
from django.template.response import TemplateResponse

from structure.models import QuARCConferenceProxy, QSECMemberProxy, QuARCQSECMembersProxy, ProgramEventProxy, DinnerOptionsProxy, SwagOptionsProxy

from conference.admin import QuARCAdmin

# Conference Proxies
admin.site.register(QuARCConferenceProxy)

admin.site.register(QuARCQSECMembersProxy, QuARCAdmin)
admin.site.register(ProgramEventProxy, QuARCAdmin)

@admin.action(description="Add QSEC members to QuARC conference")
def add_qsec_to_quarc(modeladmin, request, queryset):
    if 'post' in request.POST:
        # Second call to this form, so we can now add the QSEC members
        quarc = QuARCConferenceProxy.objects.filter(year=int(request.POST['quarc']))[0]
        for qsec_member in queryset:
            QuARCQSECMembersProxy.objects.create(quarc=quarc, qsec_member=qsec_member)
        return None

    quarcs = QuARCConferenceProxy.objects.order_by('year')

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
admin.site.register(QSECMemberProxy, QuARCQSECMembersAdmin)

# Logistics Proxies
admin.site.register(DinnerOptionsProxy, QuARCAdmin)
admin.site.register(SwagOptionsProxy, QuARCAdmin)
