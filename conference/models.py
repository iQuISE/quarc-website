from django.db import models

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

class QuARCConference(models.Model):
    year = models.IntegerField(validators=[MinValueValidator(2000),
                                           MaxValueValidator(2100)], unique=True)
    ordinal = models.IntegerField(validators=[MinValueValidator(0),
                                              MaxValueValidator(100)], unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(blank=True)
    marc_start_date = models.DateField(blank=True)
    marc_end_date = models.DateField(blank=True)
    registration_start = models.DateField(blank=True)
    registration_end = models.DateField(blank=True)
    abstract_submission_active = models.BooleanField(null=False, default=False)
    university_industry_registration_active = models.BooleanField(null=False, default=False)
    logistics_form_active = models.BooleanField(null=False, default=False)
    logo = models.ImageField(upload_to='logos', blank=True)
    homepage_image = models.ImageField(upload_to='homepage_images', blank=True)

    def __str__(self):
        return 'QuARC %d' % self.year

    class Meta:
        verbose_name = 'QuARC Conference'
        verbose_name_plural = 'QuARC Conferences'

class Attendee(models.Model):
    class Status(models.IntegerChoices):
        Industry_Personnel = 0
        Student = 1
        Postdoctoral_Researcher = 2
        Research_Staff = 3
        University_Faculty = 4
        QuARC_Chair = 5
        Other = 100

    quarc = models.ForeignKey(QuARCConference, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=32, blank=True)
    middle_name = models.CharField(max_length=32, blank=True)
    last_name = models.CharField(max_length=32, blank=False)
    suffix = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=False, unique=True)
    status = models.IntegerField(choices=Status.choices, null=False)
    affiliation = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

    def validate_unique(self, exclude=None):
        # Same email and conference
        conflict = Attendee.objects.filter(quarc=self.quarc).filter(email__iexact=self.email).exclude(id=self.id)
        if conflict.exists():
            raise ValidationError('{} is already attending QuARC {}.'.format(self.email, self.quarc.year))

class LogisticsModel(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE)
    edit_time = models.DateTimeField()

    class Meta:
        abstract = True

class LogisticsMARC(LogisticsModel):
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

class LogisticsHousingPreferences(LogisticsModel):
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

class LogisticsHousingAssignments(LogisticsModel):
    roommate = models.ForeignKey(Attendee, on_delete=models.SET_NULL, null=True,
                                 related_name='assigned_roommate')

    def __str__(self):
        return ('%s %s and %s %s'
                % (self.attendee.first_name, self.attendee.last_name,
                   self.roommate.first_name, self.roommate.last_name))

    class Meta:
        verbose_name = 'Housing Assignment Logistics'
        verbose_name_plural = 'Housing Assignment Logistics'

        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_alphabetize_roommates',
                check=models.Q(attendee__lte=models.F('roommate')),
            )
        ]

class DinnerOptions(models.Model):
    quarc = models.ForeignKey(QuARCConference, on_delete=models.CASCADE)
    option = models.CharField(max_length=32, blank=False)

    def __str__(self):
        return '%s' % (self.option)

    class Meta:
        verbose_name = 'Dinner Option'
        verbose_name_plural = 'Dinner Options'

class LogisticsDinner(LogisticsModel):
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

    class Meta:
        verbose_name = 'Dinner Logistics'
        verbose_name_plural = 'Dinner Logistics'

class LogisticsActivities(LogisticsModel):
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

class LogisticsSwag(LogisticsModel):
    swag_option = models.ForeignKey(SwagOptions, null=False, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s: %s' % (self.attendee.first_name, self.attendee.last_name, self.swag_option.option)

    class Meta:
        verbose_name = 'Swag Logistics'
        verbose_name_plural = 'Swag Logistics'

class LogisticsBus(LogisticsModel):
    class BusOption(models.IntegerChoices):
        Early = 0
        Late = 1

    bus_to_required = models.BooleanField(null=False)
    bus_to_type = models.IntegerField(choices=BusOption.choices, null=True, blank=True)
    bus_from_required = models.BooleanField(null=False)

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

    class Meta:
        verbose_name = 'Bus Logistics'
        verbose_name_plural = 'Bus Logistics'

class Acceptance(LogisticsModel):
    accepted = models.BooleanField(null=False)
    acceptance_note = models.CharField(max_length=256, blank=True)
    dropped = models.BooleanField(null=True)

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

class Abstract(models.Model):    
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE)
    title = models.CharField(max_length=128, blank=False)
    author_list = models.CharField(max_length=512, blank=False)
    funding_sources = models.CharField(max_length=512, blank=False)
    publications = models.CharField(max_length=512, blank=False)
    figure = models.ImageField(upload_to='abstract_figures', blank=True)
    figure_caption = models.CharField(max_length=512, blank=False)
    abstract = models.CharField(max_length=2048, blank=False)
    seeking_internships = models.BooleanField(null=False)
    seeking_positions = models.BooleanField(null=False)
    elevator_pitch = models.BooleanField(null=False)
    oral_presentation = models.BooleanField(null=False)
    research_area = models.CharField(max_length=64)
    research_group = models.CharField(max_length=64)
    cqe_feature = models.BooleanField(null=False)
    resume = models.FileField(upload_to='resumes', blank=True)
    graduation_date = models.DateField(null=True)

    def __str__(self):
        return '%s %s' % (self.attendee.first_name, self.attendee.last_name)

class QSECMember(models.Model):
    company_name = models.CharField(max_length=64, blank=False)
    founder = models.BooleanField(null=False)

    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = 'QSEC Member'
        verbose_name_plural = 'QSEC Members'

class QuARCQSECMembers(models.Model):
    quarc = models.ForeignKey(QuARCConference, on_delete=models.CASCADE)
    qsec_member = models.ForeignKey(QSECMember, on_delete=models.CASCADE)

    def __str__(self):
        return 'QuARC %d, %s' % (self.quarc.year, self.qsec_member.company_name)

    def validate_unique(self, exclude=None):
        # Same QuARC and QSEC Member
        conflict = QuARCQSECMembers.objects.filter(quarc=self.quarc).filter(qsec_member=self.qsec_member).exclude(id=self.id)
        if conflict.exists():
            raise ValidationError('{} is already in QSEC for QuARC {}.'.format(self.qsec_member.company_name, self.quarc.year))

    class Meta:
        verbose_name = 'QSEC for QuARC'
        verbose_name_plural = 'QSEC for QuARC'
