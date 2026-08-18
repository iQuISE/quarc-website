from django.contrib import admin

from .models import QuARCConference, QSECMember, QuARCQSECMembers, Attendee, LogisticsMARC, LogisticsHousingPreferences, LogisticsHousingAssignments, DinnerOptions, LogisticsDinner, LogisticsActivities, SwagOptions, LogisticsSwag, LogisticsBus, Acceptance, Abstract

class QuARCAdmin(admin.ModelAdmin):
    list_filter = ['quarc__year']

class LogisticsAdmin(admin.ModelAdmin):
    list_filter = ['attendee__quarc__year']

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
admin.site.register(Abstract, LogisticsAdmin)
