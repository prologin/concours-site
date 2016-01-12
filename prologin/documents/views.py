from django.template import defaultfilters
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import contest.models
import django.http
import documents.models
import itertools
import users.models


def _regionale_contestants_from_year_center(year, center):
    center_qs = contest.models.Center.objects.all()
    if center == 'all':
        center_name = str(_("all"))
    else:
        center_qs = center_qs.filter(pk=center)
        if not center_qs:
            raise django.http.Http404(_("No such center"))
        center_name = center_qs[0].name

    contestants = contest.models.Contestant.objects.filter(
        edition__year=year,
        assignation_semifinal=contest.models.Assignation.assigned.value,
        assignation_semifinal_event__center=center_qs,
    )
    return contestants, center_name


def _regionale_contestants_from_year_user(year, user):
    contestant_qs = contest.models.Contestant.objects.filter(pk=user)
    if not contestant_qs:
        raise django.http.Http404(_("No such user"))
    contestant_name = contestant_qs[0].user.username

    contestants = contest.models.Contestant.objects.filter(
        pk=user,
    )
    return contestants, contestant_name


def _finale_contestants_from_year(year):
    return contest.models.Contestant.objects.filter(
        edition__year=year,
        assignation_final=contest.models.Assignation.assigned.value,
    )


def _document_response(request, fobj, filename, content_type='application/pdf'):
    """
    Outputs a HttpResponse containing data from :param fobj with the given :param filename and :param content_type.
    If request contains the ?dl parameter, the response is an attachment (downlaod popup).
    :param request: the request to respond for
    :param fobj: file object to output
    :param filename:
    :param content_type:
    :return: HttpReponse
    """
    response = django.http.HttpResponse(content_type=content_type)
    if request.GET.get('dl') is not None:
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    response.write(fobj.read())
    return response

@staff_member_required
def generate_regionales_convocations(request, year, center):
    contestants, center_name = _regionale_contestants_from_year_center(year, center)
    context = {
        'year': year,
        'items': contestants.order_by('edition__year', 'user__last_name', 'user__first_name'),
        'url': settings.SITE_BASE_URL,
    }
    with documents.models.generate_tex_pdf("documents/convocation-regionale.tex", context) as output:
        return _document_response(request, output, "convocations-regionales-{year}-{center}.pdf".format(
            year=year, center=slugify(center_name),
        ))


@staff_member_required
def generate_regionales_user_convocation(request, year, user):
    contestants, user_name = _regionale_contestants_from_year_user(year, user)
    context = {
        'year': year,
        'items': contestants,
        'url': settings.SITE_BASE_URL,
    }
    with documents.models.generate_tex_pdf("documents/convocation-regionale.tex", context) as output:
        return _document_response(request, output, "convocations-regionales-{year}-{user}.pdf".format(
            year=year, user=slugify(user_name),
        ))

@staff_member_required
def generate_portrayal_agreement(request, year):
    context = {
        'year': year,
    }
    with documents.models.generate_tex_pdf("documents/droit-image.tex", context) as output:
        return _document_response(request, output, "droit-image.pdf")


@staff_member_required
def generate_finale_convocations(request, year):
    contestants = _finale_contestants_from_year(year)
    context = {
        'year': year,
        'items': contestants.order_by('assignation_final_event__event__center__name', 'user__last_name', 'user__first_name'),
    }
    with documents.models.generate_tex_pdf("documents/convocation-finale.tex", context) as output:
        return _document_response(request, output, "convocations-finale-{year}.pdf".format(
            year=year,
        ))


@staff_member_required
def generate_regionales_userlist(request, year, center):
    contestants, center_name = _regionale_contestants_from_year_center(year, center)
    contestants = itertools.groupby(
        contestants.order_by('event__center__pk', 'user__last_name', 'user__first_name'),
        lambda w: w.event.center)

    items = []
    for center, grouped in contestants:
        items.append((center, list(grouped)))

    context = {
        'year': year,
        'items': items,
    }
    with documents.models.generate_tex_pdf("documents/liste-appel.tex", context) as output:
        return _document_response(request, output, "liste-appel-{year}-{center}.pdf".format(
            year=year, center=slugify(center_name),
        ))


@staff_member_required
def generate_finale_userlist(request, year):
    contestants = _finale_contestants_from_year(year)
    contestants = itertools.groupby(
        contestants.order_by('event__center__pk', 'user__last_name', 'user__first_name'),
        lambda w: w.event.center)

    items = []
    for center, grouped in contestants:
        items.append((center, list(grouped)))

    context = {
        'year': year,
        'items': items,
    }
    with documents.models.generate_tex_pdf("documents/liste-appel.tex", context) as output:
        return _document_response(request, output, "liste-appel-{year}.pdf".format(
            year=year,
        ))


@staff_member_required
def generate_regionales_interviews(request, year, center):
    contestants, center_name = _regionale_contestants_from_year_center(year, center)
    context = {
        'year': year,
        'items': contestants.order_by('event__center__name', 'user__last_name', 'user__first_name'),
    }
    with documents.models.generate_tex_pdf("documents/interviews.tex", context) as output:
        return _document_response(request, output, "liste-appel-{year}.pdf".format(
            year=year,
        ))


@staff_member_required
def generate_regionales_passwords(request, year, center):
    contestants, center_name = _regionale_contestants_from_year_center(year, center)
    contestants = itertools.groupby(
        contestants.order_by('assignation_semifinal_event__center__pk', 'user__last_name', 'user__first_name'),
        lambda c: c.assignation_semifinal_event.center)

    items = []
    for center, grouped in contestants:
        items.append((center, list(grouped)))

    context = {
        'year': year,
        'items': items,
    }
    with documents.models.generate_tex_pdf("documents/passwords.tex", context) as output:
        return _document_response(request, output, "liste-mots-de-passe-{year}-{center}.pdf".format(
            year=year, center=slugify(center_name),
        ))


@staff_member_required
def generate_finale_passwords(request, year):
    contestants = _finale_contestants_from_year(year)
    contestants = itertools.groupby(
        contestants.order_by('assignation_final_event__center__pk', 'user__last_name', 'user__first_name'),
        lambda c: c.assignation_final_event.center)

    items = []
    for center, grouped in contestants:
        items.append((center, list(grouped)))

    context = {
        'year': year,
        'items': items,
    }
    with documents.models.generate_tex_pdf("documents/passwords.tex", context) as output:
        return _document_response(request, output, "liste-mots-de-passe-{year}.pdf".format(
            year=year,
        ))
