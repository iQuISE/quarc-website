from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from datetime import datetime

from conference.models import QuARCConference, QuARCQSECMembers, Attendee, ProgramEvent
from conference.forms import AttendeeForm, AbstractForm

from logistics.models import Acceptance
from logistics.forms import MARCForm

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
            marc_form.instance.latest = True

            abstract_form.instance.attendee = attendee

            if marc_form.is_valid() and abstract_form.is_valid():
                attendee = attendee_form.save()
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
            marc_form.instance.latest = True

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

def program(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    program_data = ProgramEvent.objects.filter(quarc=conf)

    return render(request, 'program.html',
                  {'conference': conf, 'show_countdown': True, 'program_data': program_data})
