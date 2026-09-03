from django.db import models

from conference.models import QuARCConference, Attendee

from datetime import datetime

class LogisticsModel(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE)
    edit_time = models.DateTimeField()
    edit_reason = models.CharField(max_length=256, blank=True)
    latest = models.BooleanField(null=False, blank=False)

    class Meta:
        abstract = True

    def validate_unique(self, exclude=None):
        if self.latest:
            attendee_pk = self.attendee.pk
            logistics_pk = self.pk
            # Ensure there is only one latest entry.
            conflict = self.__class__.objects.filter(attendee_id=attendee_pk, latest=True).exclude(pk=logistics_pk)
            if conflict.exists():
                raise ValidationError('{} already has latest entry.'.format(self.attendee))

    def _object_matches_db(self):
        db_objs = self.__class__.objects.filter(pk=self.pk)
        if len(db_objs) > 0:
            for field in self._meta.get_fields():
                if getattr(self, field.name) != getattr(db_objs[0], field.name):
                    return False
            return True
        return False
        
    def save(self, *args, **kwargs):
        # If unchanged and latest, just keep it
        if self.pk is not None and self.latest:
            if self._object_matches_db():
                super().save(*args, **kwargs)
                return
        # Otherwise, mark others not the latest and ensure new entry created.
        self.__class__.objects.filter(attendee=self.attendee).update(latest=False)
        self.pk = None # Ensure new entry is created
        self.latest = True
        self.edit_time = datetime.now()
        super().save(*args, **kwargs)

class Acceptance(LogisticsModel):
    accepted = models.BooleanField(null=False)
    acceptance_comment = models.CharField(max_length=256, blank=True)
    dropped = models.BooleanField(null=True)

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

class MARC(LogisticsModel):
    attending_marc = models.BooleanField(null=True)

    def __str__(self):
        if self.attending_marc:
            return ('%s %s is attending MARC'
                    % (self.attendee.first_name, self.attendee.last_name))
        else:
            return ('%s %s is not attending MARC'
                    % (self.attendee.first_name, self.attendee.last_name))

    class Meta:
        verbose_name = 'MARC Logistics'
        verbose_name_plural = 'MARC Logistics'

class HousingPreferences(LogisticsModel):
    overnight_required = models.BooleanField(null=False)
    needs_roommate = models.BooleanField(null=False, blank=True)
    preferred_roommate = models.ForeignKey(Attendee, on_delete=models.SET_NULL, null=True,
                                           related_name='preferred_roommate', blank=True)
    preferred_roommate_name = models.CharField(max_length=64, blank=True)
    gender = models.CharField(max_length=32, blank=True)
    preferred_roommate_gender = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

    class Meta:
        verbose_name = 'Housing Preferences Logistics'
        verbose_name_plural = 'Housing Preferences Logistics'

class HousingAssignments(LogisticsModel):
    roommate = models.ForeignKey(Attendee, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_roommate')

    def __str__(self):
        if self.roommate is None:
            return '%s %s alone' % (self.attendee.first_name, self.attendee.last_name)
        return ('%s %s and %s %s'
                % (self.attendee.first_name, self.attendee.last_name,
                   self.roommate.first_name, self.roommate.last_name))

    def clean(self):
        if self.roommate is not None and self.roommate.quarc != self.attendee.quarc:
            raise ValidationError('Roommate QuARC does not match attendee QuARC')
        super().clean()

    class Meta:
        verbose_name = 'Housing Assignment Logistics'
        verbose_name_plural = 'Housing Assignment Logistics'

    def save(self, *args, **kwargs):
        '''This function ensures that we are our roommate's roommate and no one else's roommate'''
        # If the object is unchanged, just do a normal save
        if self.pk is not None and self.latest:
            if self._object_matches_db():
                super().save(*args, **kwargs)
                return

        # Get roommate from DB
        current_assignments = (HousingAssignments.objects
                               .filter(roommate=self.attendee, latest=True))

        # Save ourselves
        super().save(*args, **kwargs)

        # Remove ourselves from other roommates, except our new roommate
        matched = False
        for current_assignment in current_assignments:
            if current_assignment.attendee != self.roommate:
                current_assignment.roommate = None
                current_assignment.save()
            else:
                matched = True
        # If we are already with our new roommate, return
        if matched:
            return
        if self.roommate is None:
            return
        # Otherwise, add ourselves to our new roommate
        HousingAssignments.objects.create(attendee=self.roommate, roommate=self.attendee,
                                                   edit_time=datetime.now(), latest=True)

class DinnerOptions(models.Model):
    quarc = models.ForeignKey(QuARCConference, on_delete=models.CASCADE)
    option = models.CharField(max_length=32, blank=False)

    def __str__(self):
        return '%s' % (self.option)

    class Meta:
        verbose_name = 'Dinner Option'
        verbose_name_plural = 'Dinner Options'

class Dinner(LogisticsModel):
    dinner_required = models.BooleanField(null=False)
    vegetarian = models.BooleanField(null=True, blank=True)
    vegan = models.BooleanField(null=True, blank=True)
    gluten_free = models.BooleanField(null=True, blank=True)
    kosher = models.BooleanField(null=True, blank=True)
    halal = models.BooleanField(null=True, blank=True)
    other_restriction = models.CharField(max_length=64, blank=True)
    dinner_option = models.ForeignKey(DinnerOptions, null=True, on_delete=models.SET_NULL, blank=True)

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

    def clean(self):
        if self.dinner_option.quarc != self.attendee.quarc:
            raise ValidationError('Dinner option QuARC does not match attendee QuARC')
        super().clean()

    class Meta:
        verbose_name = 'Dinner Logistics'
        verbose_name_plural = 'Dinner Logistics'

class Activities(LogisticsModel):
    winter_activities = models.BooleanField(null=False)

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

    class Meta:
        verbose_name = 'Winter Activities Logistics'
        verbose_name_plural = 'Winter Activities Logistics'

class SwagOptions(models.Model):
    quarc = models.ForeignKey(QuARCConference, on_delete=models.CASCADE)
    option = models.CharField(max_length=32, blank=False)
    url = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return '%s' % (self.option)

    class Meta:
        verbose_name = 'Swag Option'
        verbose_name_plural = 'Swag Options'

class Swag(LogisticsModel):
    swag_option = models.ForeignKey(SwagOptions, null=False, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s: %s' % (self.attendee.first_name, self.attendee.last_name, self.swag_option.option)

    def clean(self):
        if self.swag_option.quarc != self.attendee.quarc:
            raise ValidationError('Swag QuARC does not match attendee QuARC')
        super().clean()

    class Meta:
        verbose_name = 'Swag Logistics'
        verbose_name_plural = 'Swag Logistics'

class Buses(models.Model):
    class BusOption(models.IntegerChoices):
        Early = 0
        Late = 1
        Return = 2

    quarc = models.ForeignKey(QuARCConference, on_delete=models.CASCADE)
    type = models.IntegerField(choices=BusOption.choices, null=False, blank=False)
    number = models.IntegerField(null=False, blank=False)
    capacity = models.IntegerField(null=True, blank=True)
    leader = models.ForeignKey(Attendee, on_delete=models.SET_NULL, null=True, blank=True)
    leader_phone_number = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return '%s Bus #%s' % (self.get_type_display(), self.number)

    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'

def validate_bus_to(bus):
    if bus.type != BusOption.Early or bus.type != BusOption.Late:
        raise ValidationError('%s is not a bus to QuARC' % bus)
def validate_bus_from(bus):
    if bus.type != BusOption.Return:
        raise ValidationError('%s is not a bus from QuARC' % bus)
def validate_bus_capacity(bus):
    if bus.type == BusOption.Early or bus.type == BusOption.Late:
        if Bus.objects.filter(bus_to_assignment=bus).count() >= bus.capacity():
            raise ValidationError('%s is full' % bus)
    elif bus.type == BusOption.Return:
        if Bus.objects.filter(bus_from_assignment=bus).count() >= bus.capacity():
            raise ValidationError('%s is full' % bus)

class Bus(LogisticsModel):
    bus_to_required = models.BooleanField(null=False)
    bus_to_type = models.IntegerField(choices=Buses.BusOption.choices, null=True, blank=True)
    bus_from_required = models.BooleanField(null=False)
    bus_to_assignment = models.ForeignKey(Buses, null=True, blank=True, on_delete=models.SET_NULL,
                                          related_name='bus_to',
                                          validators=[validate_bus_to, validate_bus_capacity])
    bus_from_assignment = models.ForeignKey(Buses, null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name='bus_from',
                                            validators=[validate_bus_from, validate_bus_capacity])

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

    def clean(self):
        if (self.bus_to_assignment is not None
            and self.bus_to_assignment.quarc != self.attendee.quarc):
            raise ValidationError('Bus to QuARC does not match attendee QuARC')
        if (self.bus_from_assignment is not None
            and self.bus_from_assignment.quarc != self.attendee.quarc):
            raise ValidationError('Bus from QuARC does not match attendee QuARC')
        super().clean()

    class Meta:
        verbose_name = 'Bus Logistics'
        verbose_name_plural = 'Bus Logistics'
