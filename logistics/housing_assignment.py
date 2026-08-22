from logistics.models import Attendee, HousingPreferences, HousingAssignments

from datetime import datetime

def assign_housing(quarc):
    needs_housing = (HousingPreferences.objects
                     .filter(latest=True, overnight_required=True)
                     .exclude(attendee__assigned_roommate__isnull=False))

    if not needs_housing.exists():
        # Done!
        return
    edit_time = datetime.now()
    # First, assign rooms to those who don't need roommates
    for entry in needs_housing.filter(needs_roommate=False):
        HousingAssignments.objects.create(attendee=entry.attendee, edit_time=edit_time,
                                          latest=True, roommate=None)
    needs_housing = needs_housing.exclude(needs_roommate=False)

    # Second, find mutual pairs
    for entry in needs_housing:
        if HousingAssignments.objects.filter(attendee=entry.attendee).exists():
            continue
        if needs_housing.filter(attendee=entry.preferred_roommate,
                                preferred_roommate=entry.attendee).exists():
            HousingAssignments.objects.create(attendee=entry.attendee, edit_time=edit_time,
                                              latest=True, roommate=entry.preferred_roommate)

    # Third, find one directional preferences that are gender compatible
    for entry in needs_housing:
        if HousingAssignments.objects.filter(attendee=entry.attendee).exists():
            continue
        if needs_housing.filter(attendee=entry.preferred_roommate,
                                preferred_roommate_gender=entry.gender).exists():
            HousingAssignments.objects.create(attendee=entry.attendee, edit_time=edit_time,
                                              latest=True, roommate=entry.preferred_roommate)

    # Fourth, find gender compatible pairs
    for entry in needs_housing:
        if HousingAssignments.objects.filter(attendee=entry.attendee).exists():
            continue
        if needs_housing.filter(gender=entry.preferred_roommate_gender,
                                preferred_roommate_gender=entry.gender).exists():
            HousingAssignments.objects.create(attendee=entry.attendee,
                                              edit_time=edit_time, latest=True,
                                              roommate=entry.preferred_roommate)
