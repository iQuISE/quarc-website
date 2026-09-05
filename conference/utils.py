from django.core.mail import send_mail

from datetime import datetime

from conference.models import QuARCConference, AttendeeEmail

def get_conference(year):
    conferences = QuARCConference.objects.filter(year=year)
    if len(conferences) == 0:
        raise ValueError(f'No QuARC found for {year}')
    return conferences[0]

def email_attendee(attendee, subject, text_msg, html_msg=None):
    subject = '[QuARC {}] '.format(attendee.quarc.year) + subject
    exec_email = 'quarc{}-exec@mit.edu'.format(attendee.quarc.year)

    if html_msg is None:
        send_mail(subject, text_msg, exec_email, [attendee.email])
        html_msg = ''
    else:
        send_mail(subject, text_msg, exec_email, [attendee.email], html_message=html_msg)
    # Log sent email in database
    AttendeeEmail.objects.create(attendee=attendee, timestamp=datetime.now(),
                                 subject=subject, text_message=text_msg, html_message=html_msg)
