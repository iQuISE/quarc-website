from django.forms import BooleanField, ModelForm, EmailField, ValidationError, CharField, Textarea

from conference.models import Attendee, Abstract

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
