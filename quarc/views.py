from django.shortcuts import redirect
from django.urls import reverse

from datetime import datetime

from conference.models import QuARCConference

def index(request):
    '''
    Direct visitors to the top level site to the most recent QuARC conference.
    '''
    most_recent_quarc = QuARCConference.objects.order_by('year').last()
    if most_recent_quarc is not None:
        return redirect(reverse('conference_home', args=[most_recent_quarc.year]))
    year = datetime.now().year
    if datetime.now().month > 2:
        year += 1
    return redirect(reverse('conference_home', args=[str(year)]))

def perm_redirect(request, url):
    return redirect(url, permanent=False, preserve_request=False)
