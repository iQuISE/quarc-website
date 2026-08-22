from django.forms import BooleanField, ModelForm, EmailField, ValidationError, CharField, Textarea

from logistics.models import MARC, HousingPreferences, Dinner, Activities, Swag, Bus

class LogisticsForm(ModelForm):
    def clean(self):
        '''Default bools to false, because checkboxes don't post'''
        cleaned_data = super().clean()
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField) and not field.required:
                if field_name not in self.data:
                    cleaned_data[field_name] = False
        return cleaned_data

class MARCForm(LogisticsForm):
    class Meta:
        model = MARC
        fields = ['attending_marc']

class HousingPreferencesForm(LogisticsForm):
    class Meta:
        model = HousingPreferences
        fields = ['overnight_required',
                  'preferred_roommate',
                  'preferred_roommate_name',
                  'gender',
                  'preferred_roommate_gender']

class DinnerForm(LogisticsForm):
    class Meta:
        model = Dinner
        fields = ['dinner_required',
                  'vegetarian',
                  'vegan',
                  'gluten_free',
                  'kosher',
                  'halal',
                  'other_restriction',
                  'dinner_option']

class ActivitiesForm(LogisticsForm):
    class Meta:
        model = Activities
        fields = ['winter_activities']

class SwagForm(LogisticsForm):
    class Meta:
        model = Swag
        fields = ['swag_option']

class BusForm(LogisticsForm):
    class Meta:
        model = Bus
        fields = ['bus_to_required',
                  'bus_to_type',
                  'bus_from_required']
