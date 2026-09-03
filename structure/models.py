from django.db import models

'''Proxy models for aspects of the conference and logistics
that are part of the structure of the conference, rather than operations.'''

from conference.models import QuARCConference, QSECMember, QuARCQSECMembers, ProgramEvent
from logistics.models import DinnerOptions, SwagOptions

class QuARCConferenceProxy(QuARCConference):
    class Meta:
        proxy = True
        verbose_name = 'QuARC Conference'
        verbose_name_plural = 'QuARC Conferences'

class QSECMemberProxy(QSECMember):
    class Meta:
        proxy = True
        verbose_name = 'QSEC Member'
        verbose_name_plural = 'QSEC Members'

class QuARCQSECMembersProxy(QuARCQSECMembers):
    class Meta:
        proxy = True
        verbose_name = 'QSEC for QuARC'
        verbose_name_plural = 'QSEC for QuARC'

class ProgramEventProxy(ProgramEvent):
    class Meta:
        proxy = True
        verbose_name = 'QuARC Event'
        verbose_name_plural = 'QuARC Events'

class DinnerOptionsProxy(DinnerOptions):
    class Meta:
        proxy = True
        verbose_name = 'Dinner Option'
        verbose_name_plural = 'Dinner Options'

class SwagOptionsProxy(SwagOptions):
    class Meta:
        proxy = True
        verbose_name = 'Swag Option'
        verbose_name_plural = 'Swag Options'
