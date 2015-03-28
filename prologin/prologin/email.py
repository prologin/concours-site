from djmail.template_mail import TemplateMail


def send_email(template_name, to, context, **kwargs):
    return TemplateMail(template_name).send(to, context, **kwargs)
