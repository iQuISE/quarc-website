from django.shortcuts import redirect
from django.urls import reverse

from conference.models import QuARCConference

def index(request):
    '''
    Direct visitors to the top level site to the most recent QuARC conference.
    '''
    most_recent_quarc = QuARCConference.objects.order_by('year').last()
    if most_recent_quarc is not None:
        return redirect(reverse('conference_home', args=[most_recent_quarc.year]))
