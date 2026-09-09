from django.shortcuts import render

from django.template.loader import render_to_string
from django.views.defaults import page_not_found

from .models import CommitteeAssignment
from conference.models import QuARCConference
from conference.views import get_conference

def index(request, year):
    try:
        conf = get_conference(year)
    except ValueError:
        return page_not_found(request, '')

    committee_year = (CommitteeAssignment.objects.filter(quarc=conf)
                      .order_by('role__sort_order'))
    committee_members = [{'profile_image': cr.member.profile_image,
                          'first_name': cr.member.first_name,
                          'last_name': cr.member.last_name,
                          'role': cr.role.role,
                          'email': cr.member.email,
                          'status': cr.member.status,
                          'group': cr.member.group} for cr in committee_year]
    return render(request, 'committee.html',
                  {'conference': conf, 'show_countdown': True,
                   'members': committee_members})
