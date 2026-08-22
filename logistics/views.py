from django.shortcuts import render
from django.db import models

from conference.views import get_conference
from conference.models import Attendee

from logistics.models import Acceptance, HousingPreferences, DinnerOptions, Dinner, Activities, SwagOptions, Swag, Bus
from logistics.forms import HousingPreferencesForm, DinnerForm, ActivitiesForm, SwagForm, BusForm

from datetime import datetime

def logistics_page_get_attendee(conference, POST):
    # Check email is provided
    if 'email' not in POST:
        return (None, 'Email was not provided.', '')
    attendee_email = POST['email']

    # Check the email is a registered attendee
    attendees = Attendee.objects.filter(quarc=conference).filter(email__iexact=attendee_email)
    if len(attendees) != 1:
        return (None, 'The email you provided is not one of an accepted QuARC attendee. Please check for errors.', attendee_email)
    attendee = attendees[0]

    # Check attendee is accepted
    try:
        acceptance = Acceptance.objects.filter(attendee=attendee).latest('edit_time')
    except:
        return (None, 'The email you provided is not one of an accepted QuARC attendee. Please check for errors.', attendee_email)
    if not acceptance.accepted:
        return (None, 'The email you provided is not one of an accepted QuARC attendee. Please check for errors.', attendee_email)

    return (attendee, None, attendee_email)

def logistics_page(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    if not conf.logistics_form_active:
        return logistics_closed(request, year)

    if request.method == 'POST':
        # Try to get an attendee object
        attendee, email_error, attendee_email = logistics_page_get_attendee(conf, request.POST)
        if email_error is not None:
            return render(request, 'logistics_landing.html',
                          {'conference': conf, 'show_countdown': False,
                           'attendee_email': attendee_email, 'email_error': email_error})

        # Check if they have already filled out logistics
        if (HousingPreferences.objects.filter(attendee=attendee).count() > 0
            or Dinner.objects.filter(attendee=attendee).count() > 0
            or Activities.objects.filter(attendee=attendee).count() > 0
            or Swag.objects.filter(attendee=attendee).count() > 0
            or Bus.objects.filter(attendee=attendee).count() > 0):
            email_error = 'You have already filled out the logistics form.'
            return render(request, 'logistics_landing.html',
                          {'conference': conf, 'show_countdown': False,
                           'attendee_email': attendee_email, 'email_error': email_error})

        # Get options to populate the form
        needs_roommate = (attendee.status == Attendee.Status.Student
                          or attendee.status == Attendee.Status.Postdoctoral_Researcher)
        roommate_options = [(a.attendee.pk, a.attendee.first_name + ' ' + a.attendee.last_name)
                            for a in (Acceptance.objects
                                      .filter(latest=True, accepted=True)
                                      .filter(~models.Q(attendee=attendee))
                                      .order_by('attendee__last_name'))]
        dinner_options = [(do.pk, do.option) for do in DinnerOptions.objects.filter(quarc=conf)]
        swag_options = [(so.pk, so.option) for so in SwagOptions.objects.filter(quarc=conf)]

        if request.POST.get('landing_page', False):
            # If they came from the landing page, give them a blank form
            housing_form = HousingPreferencesForm()
            dinner_form = DinnerForm()
            activities_form = ActivitiesForm()
            swag_form = SwagForm()
            bus_form = BusForm()
        else:
            # Otherwise, process the form
            housing_form = HousingPreferencesForm(data=request.POST)
            dinner_form = DinnerForm(data=request.POST)
            activities_form = ActivitiesForm(data=request.POST)
            swag_form = SwagForm(data=request.POST)
            bus_form = BusForm(data=request.POST)

            all_forms = [housing_form, dinner_form, activities_form, swag_form, bus_form]

            housing_form.instance.needs_roommate = needs_roommate
            for form in all_forms:
                form.instance.attendee = attendee
                form.instance.edit_time = datetime.now()
                form.instance.latest = True

            if all([form.is_valid() for form in all_forms]):
                for form in all_forms:
                    form.save()

                return render(request, 'logistics_success.html',
                              {'conference': conf, 'show_countdown': True})

        return render(request, 'logistics_form.html',
                      {'conference': conf, 'show_countdown': False,
                       'attendee': attendee,
                       'needs_roommate': needs_roommate,
                       'roommate_options': roommate_options,
                       'dinner_options': dinner_options,
                       'swag_options': swag_options,
                       'housing_form': housing_form,
                       'dinner_form': dinner_form,
                       'activities_form': activities_form,
                       'swag_form': swag_form,
                       'bus_form': bus_form})

    return render(request, 'logistics_landing.html',
                  {'conference': conf, 'show_countdown': False,
                   'attendee_email': '', 'email_error': ''})

def logistics_closed(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    if conf.logistics_form_active:
        return logistics_page(request, year)

    return render(request, 'logistics_closed.html',
                  {'conference': conf, 'show_countdown': False})
