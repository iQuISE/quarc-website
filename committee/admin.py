from django.contrib import admin

from .models import CommitteeMember, CommitteeRole

admin.site.register(CommitteeMember)
admin.site.register(CommitteeRole)
