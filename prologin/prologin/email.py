from djmail.template_mail import TemplateMail


def send_email(template_name, to, context, attachements=[], **kwargs):
    """Sends an email with a template.

    >>> send_email('mailing/end_qualifications', 'joseph@marchand.xxx', {'user': u})
    >>> send_email('mailing/qualified', 'joseph@marchand.xxx', {'user': u},
    ...            ['convocation_marchandj.pdf'])
    """
    email = TemplateMail(template_name)
    for attachement in attachements:
        email.attach_file(attachement)
    email.send(to, context, **kwargs)
