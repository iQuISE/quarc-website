from django.forms import ModelForm, EmailField, ValidationError

from conference.models import Attendee, Abstract, LogisticsMARC, LogisticsHousingPreferences, LogisticsDinner, LogisticsActivities, LogisticsSwag, LogisticsBus

class AttendeeForm(ModelForm):
    email_confirm = EmailField(required=False)

    class Meta:
        model = Attendee
        fields = ['first_name',
                  'middle_name',
                  'last_name',
                  'suffix',
                  'email',
                  'status',
                  'affiliation']

    def clean(self):
        cleaned_data = super(AttendeeForm, self).clean()
        email = cleaned_data.get('email')
        email_confirm = cleaned_data.get('email_confirm')
        print('{} and {}'.format(email, email_confirm))
        if email != email_confirm:
            self.add_error('email', 'Emails do not catch')

class AbstractForm(ModelForm):
    class Meta:
        model = Abstract
        fields = ['title',
                  'author_list',
                  'funding_sources',
                  'publications',
                  'figure',
                  'figure_caption',
                  'abstract',
                  'seeking_internships',
                  'seeking_positions',
                  'elevator_pitch',
                  'oral_presentation',
                  'research_area',
                  'research_group',
                  'cqe_feature',
                  'resume',
                  'graduation_date']

class LogisticsMARCForm(ModelForm):
    class Meta:
        model = LogisticsMARC
        fields = ['attending_marc']

class LogisticsHousingPreferencesForm(ModelForm):
    class Meta:
        model = LogisticsHousingPreferences
        fields = ['overnight_required',
                  'preferred_roommate',
                  'preferred_roommate_name',
                  'gender',
                  'preferred_roommate_gender']

class LogisticsDinnerForm(ModelForm):
    class Meta:
        model = LogisticsDinner
        fields = ['dinner_required',
                  'vegetarian',
                  'vegan',
                  'gluten_free',
                  'kosher',
                  'halal',
                  'other_restriction',
                  'dinner_option']

class LogisticsActivitiesForm(ModelForm):
    class Meta:
        model = LogisticsActivities
        fields = ['winter_activities']

class LogisticsSwagForm(ModelForm):
    class Meta:
        model = LogisticsSwag
        fields = ['swag_option']

class LogisticsBusForm(ModelForm):
    class Meta:
        model = LogisticsBus
        fields = ['bus_to_required',
                  'bus_to_type',
                  'bus_from_required']
