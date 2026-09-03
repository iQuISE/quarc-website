from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from conference.admin_filters import QuARCFilter
from conference.models import QuARCConference
from conference.utils import get_conference

from logistics.models import Acceptance, Buses, HousingAssignments

class AttendeeQuARCFilter(QuARCFilter):
    filter_column = 'attendee__quarc__year'

class AcceptedFilter(admin.SimpleListFilter):
    title = 'Attendee Accepted'
    parameter_name = 'accepted'
    filter_param = 'attendee__in'

    def lookups(self, request, model_admin):
        return [('accepted', 'Accepted'), ('rejected', 'Rejected'), ('null', 'No decision')]

    def queryset(self, request, queryset):
        if self.value() == 'accepted':
            accept_type = True
        elif self.value() == 'rejected':
            accept_type = False
        elif self.value() == 'null':
            accept_type = None
            accepted_ids = Acceptance.objects.values('attendee_id')
            return queryset.filter(~models.Q(**{self.filter_param: accepted_ids}))
        else:
            return queryset

        accepted_ids = Acceptance.objects.filter(latest=True, accepted=accept_type).values('attendee_id')
        return queryset.filter(**{self.filter_param: accepted_ids})

class DroppedFilter(admin.SimpleListFilter):
    title = 'Attendee Dropped'
    parameter_name = 'dropped'
    filter_param = 'attendee__in'

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

        dropped_ids = Acceptance.objects.filter(latest=True, dropped=drop_type).values('attendee_id')
        return queryset.filter(**{self.filter_param: dropped_ids})

class LatestFilter(admin.SimpleListFilter):
    title = 'Latest Logistics'
    parameter_name = 'latest'

    def lookups(self, request, model_admin):
        return [(None, 'Latest'), ('all', 'All'), ('stale', 'Stale')]

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
        elif self.value() == 'stale':
            return queryset.filter(latest=False)
        return queryset.filter(latest=True)

class BusFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        base_list = [('not_required', 'Not Required'),
                     ('not_assigned', 'Not Assigned'),
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

        buses = Buses.objects.filter(quarc=conf, type__in=self.bus_types)

        return base_list + [(b.pk, f'On {str(b)}') for b in buses]

    def queryset(self, request, queryset):
        if self.value() == 'not_required':
            return queryset.filter(latest=True, **{self.parameter_name + '_required': False})
        elif self.value() == 'not_assigned':
            return queryset.filter(latest=True, **{self.parameter_name + '_required': True,
                                                   self.parameter_name + '_assignment': None})
        elif self.value() == 'assigned':
            return (queryset.filter(latest=True)
                    .filter(~models.Q(**{self.parameter_name + '_assignment': None})))
        elif self.value() is not None:
            print(self.value())
            return queryset.filter(latest=True,
                                   **{self.parameter_name + '_assignment': self.value()})
        return queryset

class BusToFilter(BusFilter):
    title = 'Bus To'
    parameter_name = 'bus_to'
    bus_types = [0, 1]
class BusFromFilter(BusFilter):
    title = 'Bus From'
    parameter_name = 'bus_from'
    bus_types = [2]

class DinnerRestrictionFilter(admin.SimpleListFilter):
    title = 'Dietary Restrictions'
    parameter_name = 'dietary_restrictions'

    def lookups(self, request, model_admin):
        return [('yes', 'Yes'), ('no', 'No')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(models.Q(latest=True) & (models.Q(vegetarian=True)
                                                            | models.Q(vegan=True)
                                                            | models.Q(gluten_free=True)
                                                            | models.Q(kosher=True)
                                                            | models.Q(halal=True)
                                                            | ~models.Q(other_restriction='')))
        elif self.value() == 'no':
            return queryset.filter(latest=True, vegetarian=False, vegan=False, gluten_free=False,
                                   kosher=False, halal=False, other_restriction='')
        return queryset

class HousingFilter(admin.SimpleListFilter):
    title = 'Housing'
    parameter_name = 'housing'

    def lookups(self, request, model_admin):
        return [('assigned', 'Housing Assigned'),
                ('required', 'Housing Unassigned'),
                ('needs_roommate', 'Needs Roommate'),
                ('has_roommate', 'Has Roommate'),
                ('not_overnight', 'Not Overnight')]

    def queryset(self, request, queryset):
        if self.value() == 'assigned':
            assigned_ids = (HousingAssignments.objects
                            .filter(latest=True).values('attendee_id'))
            return queryset.filter(attendee__in=assigned_ids)
        elif self.value() == 'required':
            assigned_ids = (HousingAssignments.objects
                            .filter(latest=True).values('attendee_id'))
            return (queryset.filter(latest=True, overnight_required=True)
                    .filter(~models.Q(attendee__in=assigned_ids)))
        elif self.value() == 'needs_roommate':
            needs_ids = (HousingAssignments.objects
                         .filter(latest=True, roommate__isnull=True)
                         .values('attendee_id'))
            return queryset.filter(latest=True, needs_roommate=True).filter(attendee__in=needs_ids)
        elif self.value() == 'has_roommate':
            has_roommate_ids = (HousingAssignments.objects
                                .filter(latest=True, roommate__isnull=False).values('attendee_id'))
            return queryset.filter(attendee__in=has_roommate_ids)
        elif self.value() == 'not_overnight':
            return queryset.filter(latest=True, overnight_required=False)
        else:
            return queryset
