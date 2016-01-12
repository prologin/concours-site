from djmail.template_mail import TemplateMail


def send_email(template_name, to, context, attachements=[], **kwargs):
    """Sends an email with a template.

    >>> send_email('mailing/end_qualifications', 'joseph@marchand.xxx', {'user': u})
    >>> send_email('mailing/qualified', 'joseph@marchand.xxx', {'user': u},
    ...            ['convocation_marchandj.pdf', pdf_content, 'application/pdf'])
    """
    template = TemplateMail(template_name)
    email = template.make_email_object(to, context, **kwargs)
    for filename, content, mime_type in attachements:
        email.attach(filename, content, mime_type)
    email.send()
