from django.shortcuts import render

from django.template.loader import render_to_string
from django.views.defaults import page_not_found

from .models import CommitteeRole
from conference.models import QuARCConference
from conference.views import get_conference

def index(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    committee_year = CommitteeRole.objects.filter(role_conference=conf).order_by('role_type')
    committee_members = [{'profile_image': cr.member.profile_image,
                          'first_name': cr.member.first_name,
                          'last_name': cr.member.last_name,
                          'role': cr.get_role_type_display(),
                          'email': cr.member.email,
                          'status': cr.member.status,
                          'group': cr.member.group} for cr in committee_year]
    return render(request, 'committee.html',
                  {'conference': conf, 'show_countdown': True,
                   'members': committee_members})
