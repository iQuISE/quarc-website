from conference.models import QuARCConference

def get_conference(year):
    conferences = QuARCConference.objects.filter(year=year)
    if len(conferences) == 0:
        raise ValueError(f'No QuARC found for {year}')
    return conferences[0]
