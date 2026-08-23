from django.contrib import admin

from conference.models import QuARCConference

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

class SessionQuARCFilter(QuARCFilter):
    filter_column = 'session__quarc__year'
