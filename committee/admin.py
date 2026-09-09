from django.contrib import admin

from .models import CommitteeMember, CommitteeRole, CommitteeAssignment

admin.site.register(CommitteeMember)
admin.site.register(CommitteeRole)
admin.site.register(CommitteeAssignment)
