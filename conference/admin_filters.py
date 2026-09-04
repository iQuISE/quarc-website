from django.contrib import admin
from django.db import models

from conference.models import QuARCConference, Session, SessionAbstract

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
        if quarcs.count() == 0:
            return queryset
        if self.value() == None:
            year = quarcs.order_by('year').last().year
        else:
            year = self.value()

        return queryset.filter(**{self.filter_column: year})

class SessionQuARCFilter(QuARCFilter):
    filter_column = 'session__quarc__year'

class AbstractSessionFilter(admin.SimpleListFilter):
    title = 'Session'
    parameter_name = 'session'
    filter_column = 'pk__in'

    def lookups(self, request, model_admin):
        base_list = [('not_assigned', 'Not Assigned'),
                     ('assigned', 'Assigned')]

        conf = None
        if request.GET is not None and 'quarc' in request.GET:
            try:
                conf = get_conference(request.GET['quarc'])
            except ValueError:
                return base_list
        if conf is None:
            try:
                conf = QuARCConference.objects.latest('year')
            except ObjectDoesNotExist:
                return base_list

        sessions = Session.objects.filter(quarc=conf)

        return base_list + [(s.pk, f'In {str(s)}') for s in sessions]

    def queryset(self, request, queryset):
        if self.value() == 'not_assigned':
            assigned_abstracts = SessionAbstract.objects.values('abstract__pk')
            return queryset.filter(~models.Q(**{self.filter_column: assigned_abstracts}))
        elif self.value() == 'assigned':
            assigned_abstracts = SessionAbstract.objects.values('abstract__pk')
            return queryset.filter(**{self.filter_column: assigned_abstracts})
        elif self.value() is not None:
            assigned_abstracts = (SessionAbstract.objects
                                  .filter(session__pk=self.value()).values('abstract__pk'))
            return queryset.filter(**{self.filter_column: assigned_abstracts})
        return queryset

class AttendeeAbstractSessionFilter(AbstractSessionFilter):
    filter_column = 'authored_abstract__pk__in'
