from django.db import models

from logistics.models import Attendee, HousingPreferences, HousingAssignments

from datetime import datetime

def attendees_needing_housing(quarc):
    needs_housing = (HousingPreferences.objects
                     .filter(attendee__quarc=quarc, latest=True, overnight_required=True)
                     .exclude(attendee__assigned_roommate__isnull=False))
    assigned_housing = (HousingAssignments.objects
                        .filter(latest=True, attendee__in=needs_housing.values('attendee')))
    return needs_housing.exclude(attendee__in=assigned_housing.values('attendee'))

def assign_housing(quarc):
    # First, assign rooms to those who don't need roommates
    needs_housing = attendees_needing_housing(quarc)
    if len(needs_housing) == 0:
        # Done!
        return

    edit_time = datetime.now()
    for entry in needs_housing.filter(needs_roommate=False):
        nights = 1
        if entry.attendee.status == Attendee.Status.Organizing_Committee:
            nights = 2

        HousingAssignments.objects.create(attendee=entry.attendee, edit_time=edit_time,
                                          latest=True, roommate=None, nights=nights)

    # Second, find mutual pairs
    needs_housing = attendees_needing_housing(quarc)
    if len(needs_housing) == 0:
        return
    for entry in needs_housing:
        nights = 1
        if entry.attendee.status == Attendee.Status.Organizing_Committee:
            nights = 2

        if HousingAssignments.objects.filter(attendee=entry.attendee).exists():
            continue
        if needs_housing.filter(attendee=entry.preferred_roommate,
                                preferred_roommate=entry.attendee).exists():
            HousingAssignments.objects.create(attendee=entry.attendee, edit_time=edit_time,
                                              latest=True, roommate=entry.preferred_roommate,
                                              nights=nights)

    # Third, find one directional preferences that are gender compatible
    needs_housing = attendees_needing_housing(quarc)
    if len(needs_housing) == 0:
        return
    for entry in needs_housing:
        nights = 1
        if entry.attendee.status == Attendee.Status.Organizing_Committee:
            nights = 2

        if HousingAssignments.objects.filter(attendee=entry.attendee).exists():
            continue
        if needs_housing.filter(attendee=entry.preferred_roommate,
                                preferred_roommate_gender=entry.gender).exists():
            HousingAssignments.objects.create(attendee=entry.attendee, edit_time=edit_time,
                                              latest=True, roommate=entry.preferred_roommate,
                                              nights=nights)

    # Fourth, find gender compatible pairs
    needs_housing = attendees_needing_housing(quarc)
    if len(needs_housing) == 0:
        return
    for entry in needs_housing:
        nights = 1
        if entry.attendee.status == Attendee.Status.Organizing_Committee:
            nights = 2

        if HousingAssignments.objects.filter(attendee=entry.attendee).exists():
            continue
        for second_entry in needs_housing.filter(gender=entry.preferred_roommate_gender,
                                                 preferred_roommate_gender=entry.gender):
            if entry == second_entry:
                continue
            if HousingAssignments.objects.filter(attendee=second_entry.attendee).exists():
                continue
            HousingAssignments.objects.create(attendee=entry.attendee,
                                              edit_time=edit_time, latest=True,
                                              roommate=second_entry.attendee, nights=nights)
