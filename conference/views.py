from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from datetime import datetime

from conference.models import QuARCConference, QuARCQSECMembers, Attendee, ConferenceEvent, Session, SessionAbstract, Abstract, ResearchArea, ResearchGoal
from conference.forms import AttendeeForm, AbstractForm
from conference.utils import get_conference

from logistics.models import Acceptance
from logistics.forms import MARCForm

import re

def index(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

    return render(request, 'index.html',
                  {'conference': conf, 'show_countdown': True})

def qsec_membership(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

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
        return page_not_found(request, None)

    return render(request, 'attend.html',
                  {'conference': conf, 'show_countdown': True})

def registration_abstract_submission(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

    if not conf.abstract_submission_active:
        return registration_closed(request, year)

    if request.method == 'POST':
        attendee_form = AttendeeForm(data=request.POST)
        marc_form = MARCForm(data=request.POST)
        abstract_form = AbstractForm(data=request.POST)

        attendee_form.instance.quarc = conf

        if not attendee_form.is_valid():
            if '__all__' in attendee_form.errors:
                if 'is already attending QuARC' in str(attendee_form.errors['__all__'][0]):
                    # They already submitted, reset their entry and allow re-submit
                    email = attendee_form.cleaned_data['email']
                    Attendee.objects.filter(quarc=conf, email__iexact=email).delete()
                    attendee_form = AttendeeForm(data=request.POST)

        if attendee_form.is_valid():
            attendee = attendee_form.save(commit=False)

            marc_form.instance.attendee = attendee
            marc_form.instance.edit_time = datetime.now()
            marc_form.instance.latest = True

            abstract_form.instance.attendee = attendee

            if marc_form.is_valid() and abstract_form.is_valid():
                if abstract_form.instance.research_area == 'other':
                    abstract_form.instance.research_area = request.POST['research_area_other']

                attendee = attendee_form.save()
                marc_form.save()
                abstract = abstract_form.save()

                # Link authored abstract to attendee
                attendee.authored_abstract = abstract
                attendee.save()

                return render(request, 'registration_success.html',
                              {'conference': conf, 'show_countdown': False})
    else:
        attendee_form = AttendeeForm()
        marc_form = MARCForm()
        abstract_form = AbstractForm()

    return render(request, 'registration_abstract.html',
                  {'conference': conf, 'show_countdown': False,
                   'attendee_form': attendee_form,
                   'status_choices': Attendee.Status.choices,
                   'research_areas': ResearchArea.objects.filter(quarc=conf),
                   'research_goals': ResearchGoal.objects.filter(quarc=conf),
                   'marc_form': marc_form,
                   'abstract_form': abstract_form})

def registration_university_industry(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

    if not conf.university_industry_registration_active:
        return registration_closed(request, year)

    if request.method == 'POST':
        attendee_form = AttendeeForm(data=request.POST)
        marc_form = MARCForm(data=request.POST)

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
        marc_form = MARCForm()

    return render(request, 'registration_university_industry.html',
                  {'conference': conf, 'show_countdown': False,
                   'attendee_form': attendee_form,
                   'status_choices': Attendee.Status.choices,
                   'marc_form': marc_form})

def registration_closed(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

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
        return page_not_found(request, None)

    program_data = ConferenceEvent.objects.filter(quarc=conf)

    return render(request, 'program.html',
                  {'conference': conf, 'show_countdown': True, 'program_data': program_data})

def abstracts(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

    session_data = Session.objects.filter(quarc=conf)
    session_list = []

    for session in session_data:
        abstracts = SessionAbstract.objects.filter(session=session)
        session_list.append({'name': session.name,
                             'abstracts': [{'pk': a.abstract.pk, 'title': a.abstract.title,
                                            'author': str(a.abstract.attendee),
                                            'research_area': a.abstract.research_area}
                                           for a in abstracts]})

    return render(request, 'abstract_list.html',
                  {'conference': conf, 'show_countdown': True, 'sessions': session_list})

def abstract(request, year, abstract_id):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, None)

    try:
        abstract = Abstract.objects.filter(attendee__quarc=conf, pk=abstract_id).last
    except Exception:
        return page_not_found(request, None)

    return render(request, 'abstract.html',
                  {'conference': conf, 'show_countdown': True, 'abstract': abstract})

def error_handler(request, exception=None, status_code=404):
    year = None
    year_match = re.search(r'quarc(\d+)/', request.path)
    if year_match:
        try:
            year = int(year_match.group(1))
        except ValueError:
            pass

    if year:
        conf = get_conference(year)
    else:
        # Default to most recent QuARC
        # This might fail, but in that case we should just show the user the error
        conf = QuARCConference.objects.order_by('-year').first()

    error_code_strs = {
        400: 'Bad Request',
        403: 'Forbidden',
        404: 'Page Not Found',
        413: 'Content Too Large',
        500: 'Server Error',
    }

    error_message = error_code_strs.get(status_code, 'Error')

    return render(request, 'error.html',
                  {'conference': conf, 'show_countdown': False,
                   'error_code': status_code, 'error_message': error_message})

def page_not_found(request, exception):
    return error_handler(request, exception)
