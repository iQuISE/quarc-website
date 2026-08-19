from django.forms import BooleanField, ModelForm, EmailField, ValidationError, CharField, Textarea

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

    abstract = CharField(widget=Textarea(attrs={'cols': 80, 'rows': 5}))

class LogisticsForm(ModelForm):
    def clean(self):
        '''Default bools to false, because checkboxes don't post'''
        cleaned_data = super().clean()
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField) and not field.required:
                if field_name not in self.data:
                    cleaned_data[field_name] = False
        return cleaned_data

class LogisticsMARCForm(LogisticsForm):
    class Meta:
        model = LogisticsMARC
        fields = ['attending_marc']

class LogisticsHousingPreferencesForm(LogisticsForm):
    class Meta:
        model = LogisticsHousingPreferences
        fields = ['overnight_required',
                  'preferred_roommate',
                  'preferred_roommate_name',
                  'gender',
                  'preferred_roommate_gender']

class LogisticsDinnerForm(LogisticsForm):
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

class LogisticsActivitiesForm(LogisticsForm):
    class Meta:
        model = LogisticsActivities
        fields = ['winter_activities']

class LogisticsSwagForm(LogisticsForm):
    class Meta:
        model = LogisticsSwag
        fields = ['swag_option']

class LogisticsBusForm(LogisticsForm):
    class Meta:
        model = LogisticsBus
        fields = ['bus_to_required',
                  'bus_to_type',
                  'bus_from_required']
