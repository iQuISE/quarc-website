from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from datetime import datetime

from conference.models import QuARCConference, QuARCQSECMembers, Attendee, Acceptance, DinnerOptions, SwagOptions, LogisticsHousingPreferences, LogisticsDinner, LogisticsActivities, LogisticsSwag, LogisticsBus
from conference.forms import AttendeeForm, LogisticsMARCForm, AbstractForm, LogisticsHousingPreferencesForm, LogisticsDinnerForm, LogisticsActivitiesForm, LogisticsSwagForm, LogisticsBusForm

def get_conference(year):
    conferences = QuARCConference.objects.filter(year=year)
    if len(conferences) == 0:
        raise ValueError(f'No QuARC found for {year}')
    return conferences[0]

def index(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    return render(request, 'index.html',
                  {'conference': conf, 'show_countdown': True})

def qsec_membership(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    qsec_year_founders = QuARCQSECMembers.objects.filter(quarc=conf, qsec_member__founder=True)
    qsec_year_members = QuARCQSECMembers.objects.filter(quarc=conf, qsec_member__founder=False)

    qsec_founders = [member.qsec_member.company_name for member in qsec_year_founders]
    qsec_members = [member.qsec_member.company_name for member in qsec_year_members]

    return render(request, 'qsec_membership.html',
                  {'conference': conf, 'show_countdown': True,
                   'founding_members': qsec_founders,
                   'members': qsec_members})

def attend(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    return render(request, 'attend.html',
                  {'conference': conf, 'show_countdown': True})

def registration_abstract_submission(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    if not conf.abstract_submission_active:
        return registration_closed(request, year)

    if request.method == 'POST':
        attendee_form = AttendeeForm(data=request.POST)
        marc_form = LogisticsMARCForm(data=request.POST)
        abstract_form = AbstractForm(data=request.POST)

        attendee_form.instance.quarc = conf

        if attendee_form.is_valid():
            attendee = attendee_form.save(commit=False)

            marc_form.instance.attendee = attendee
            marc_form.instance.edit_time = datetime.now()

            abstract_form.instance.attendee = attendee

            if marc_form.is_valid() and abstract_form.is_valid():
                attendee_form.save()
                marc_form.save()
                abstract_form.save()
                return render(request, 'registration_success.html',
                              {'conference': conf, 'show_countdown': False})
    else:
        attendee_form = AttendeeForm()
        marc_form = LogisticsMARCForm()
        abstract_form = AbstractForm()

    return render(request, 'registration_abstract.html',
                  {'conference': conf, 'show_countdown': False,
                   'attendee_form': attendee_form,
                   'status_choices': Attendee.Status.choices,
                   'marc_form': marc_form,
                   'abstract_form': abstract_form})

def registration_university_industry(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    if not conf.university_industry_registration_active:
        return registration_closed(request, year)

    if request.method == 'POST':
        attendee_form = AttendeeForm(data=request.POST)
        marc_form = LogisticsMARCForm(data=request.POST)

        attendee_form.instance.quarc = conf

        if attendee_form.is_valid():
            attendee = attendee_form.save(commit=False)

            marc_form.instance.attendee = attendee
            marc_form.instance.edit_time = datetime.now()

            if marc_form.is_valid():
                attendee_form.save()
                marc_form.save()
                return render(request, 'registration_success.html',
                              {'conference': conf, 'show_countdown': False})
    else:
        attendee_form = AttendeeForm()
        marc_form = LogisticsMARCForm()

    return render(request, 'registration_university_industry.html',
                  {'conference': conf, 'show_countdown': False,
                   'attendee_form': attendee_form,
                   'status_choices': Attendee.Status.choices,
                   'marc_form': marc_form})

def registration_closed(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    if conf.abstract_submission_active:
        return registration_abstract_submission(request, year)

    will_open = datetime.now() < conf.registration_start

    return render(request, 'registration_closed.html',
                  {'conference': conf, 'show_countdown': False,
                   'will_open': will_open})

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
        if (LogisticsHousingPreferences.objects.filter(attendee=attendee).count() > 0
            or LogisticsDinner.objects.filter(attendee=attendee).count() > 0
            or LogisticsActivities.objects.filter(attendee=attendee).count() > 0
            or LogisticsSwag.objects.filter(attendee=attendee).count() > 0
            or LogisticsBus.objects.filter(attendee=attendee).count() > 0):
            email_error = 'You have already filled out the logistics form.'
            return render(request, 'logistics_landing.html',
                          {'conference': conf, 'show_countdown': False,
                           'attendee_email': attendee_email, 'email_error': email_error})

        # Get options to populate the form
        needs_roommate = (attendee.status == Attendee.Status.Student
                          or attendee.status == Attendee.Status.Postdoctoral_Researcher)
        roommate_options = [(a.attendee.pk, a.attendee.first_name + ' ' + a.attendee.last_name)
                          for a in Acceptance.objects.filter(accepted=True).filter(~models.Q(attendee=attendee)).order_by('attendee__last_name')]
        dinner_options = [(do.pk, do.option) for do in DinnerOptions.objects.filter(quarc=conf)]
        swag_options = [(so.pk, so.option) for so in SwagOptions.objects.filter(quarc=conf)]

        if request.POST.get('landing_page', False):
            # If they came from the landing page, give them a blank form
            housing_form = LogisticsHousingPreferencesForm()
            dinner_form = LogisticsDinnerForm()
            activities_form = LogisticsActivitiesForm()
            swag_form = LogisticsSwagForm()
            bus_form = LogisticsBusForm()
        else:
            # Otherwise, process the form
            housing_form = LogisticsHousingPreferencesForm(data=request.POST)
            dinner_form = LogisticsDinnerForm(data=request.POST)
            activities_form = LogisticsActivitiesForm(data=request.POST)
            swag_form = LogisticsSwagForm(data=request.POST)
            bus_form = LogisticsBusForm(data=request.POST)

            all_forms = [housing_form, dinner_form, activities_form, swag_form, bus_form]

            housing_form.instance.needs_roommate = needs_roommate
            for form in all_forms:
                form.instance.attendee = attendee
                form.instance.edit_time = datetime.now()

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
