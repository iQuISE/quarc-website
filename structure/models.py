from django.db import models

'''Proxy models for aspects of the conference and logistics
that are part of the structure of the conference, rather than operations.'''

from conference.models import QuARCConference, QSECMember, QuARCQSECMembers, ConferenceEvent, ResearchArea, ResearchGoal
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

class ConferenceEventProxy(ConferenceEvent):
    class Meta:
        proxy = True
        verbose_name = 'Conference Event'
        verbose_name_plural = 'Conference Events'

class ResearchAreaProxy(ResearchArea):
    class Meta:
        proxy = True
        verbose_name = 'Research Area'
        verbose_name_plural = 'Research Areas'

class ResearchGoalProxy(ResearchGoal):
    class Meta:
        proxy = True
        verbose_name = 'Research Goal'
        verbose_name_plural = 'Research Goals'

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
