from django.shortcuts import redirect

def index(request):
    '''
    Direct visitors to the top level site to the most recent QuARC conference.
    '''
    latest_quarc = 2026
    return redirect(f'/quarc{latest_quarc}')
