from django.template import defaultfilters
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
import contest.models
import django.http
import documents.models


def _regionale_wishes_from_year_center(year, center):
    center_qs = contest.models.Center.objects.all()
    if center == 'all':
        center_name = str(_("all"))
    else:
        center_qs = center_qs.filter(pk=center)
        if not center_qs:
            raise django.http.Http404("No such center")
        center_name = center_qs[0].name

    wishes = contest.models.EventWish.objects.filter(
        event__edition__year=year, event__center=center_qs, is_approved=True,
        event__type=contest.models.Event.EventType.regionale.value,
    )
    return wishes, center_name


def _finale_wishes_from_year(year):
    return contest.models.EventWish.objects.filter(
        event__edition__year=year, is_approved=True,
        event__type=contest.models.Event.EventType.finale.value,
    )


def generate_regionales_convocations(request, year, center):
    wishes, center_name = _regionale_wishes_from_year_center(year, center)

    letters = []
    for wish in wishes:
        user = wish.contestant.user
        center = wish.event.center
        args = (
            user.first_name,
            user.last_name,
            user.address,
            user.postal_code,
            user.city,
            defaultfilters.date(wish.event.date_begin, "l d F Y"),
            center.name,
            center.address,
            "{} {}".format(center.postal_code, center.city),
        )
        letters.append(r"\convocation%s" % "".join("{%s}" % documents.models.latex_escape(arg) for arg in args))

    context = {
        'YEAR': documents.models.latex_escape(str(year)),
        'BODY': "\n".join(letters),
    }
    with documents.models.generate_tex_pdf("convocation-regionale.tex", context) as output:
        response = django.http.HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="convocations-regionales-{year}-{center}.pdf"'.format(
            year=year, center=slugify(center_name),
        )
        response.write(output.read())
        return response


def generate_finale_convocations(request, year):
    letters = []
    for wish in _finale_wishes_from_year(year):
        user = wish.contestant.user
        center = wish.event.center
        args = (
            user.first_name,
            user.last_name,
            user.address,
            user.postal_code,
            user.city,
            defaultfilters.date(wish.event.date_begin, "l d F Y"),
            center.name,
            center.address,
            "{} {}".format(center.postal_code, center.city),
        )
        letters.append(r"\convocation%s" % "".join("{%s}" % documents.models.latex_escape(arg) for arg in args))

    context = {
        'YEAR': documents.models.latex_escape(str(year)),
        'BODY': "\n".join(letters),
    }
    with documents.models.generate_tex_pdf("convocation-finale.tex", context) as output:
        response = django.http.HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="convocations-finale-{year}.pdf"'.format(
            year=year,
        )
        response.write(output.read())
        return response


def generate_regionales_userlist(request, year, center):
    wishes, center_name = _regionale_wishes_from_year_center(year, center)

    tablines = []
    for wish in wishes:
        user = wish.contestant.user
        args = (user.first_name, user.last_name, defaultfilters.date(user.birthday, "Y-m-d"),)
        tablines.append(r"\tabline%s" % "".join("{%s}" % documents.models.latex_escape(arg) for arg in args))

    context = {
        'YEAR': documents.models.latex_escape(str(year)),
        'CENTER': documents.models.latex_escape(center_name),
        'BODY': "\n".join(tablines),
    }
    with documents.models.generate_tex_pdf("liste-appel.tex", context) as output:
        response = django.http.HttpResponse(content_type='application/pdf')
        #response['Content-Disposition'] = 'attachment; filename="liste-appel-{year}-{center}.pdf"'.format(
        #    year=year, center=slugify(center_name),
        #)
        response.write(output.read())
        return response


def generate_finale_userlist(request, year):
    wishes = _finale_wishes_from_year(year)

    tablines = []
    for wish in wishes:
        user = wish.contestant.user
        args = (user.first_name, user.last_name, defaultfilters.date(user.birthday, "Y-m-d"),)
        tablines.append(r"\tabline%s" % "".join("{%s}" % documents.models.latex_escape(arg) for arg in args))

    context = {
        'YEAR': documents.models.latex_escape(str(year)),
        'CENTER': _("Finale"),
        'BODY': "\n".join(tablines),
    }
    with documents.models.generate_tex_pdf("liste-appel.tex", context) as output:
        response = django.http.HttpResponse(content_type='application/pdf')
        #response['Content-Disposition'] = 'attachment; filename="liste-appel-{year}.pdf"'.format(
        #    year=year,
        #)
        response.write(output.read())
        return response


def generate_regionales_interviews(request, year, center):
    wishes, center_name = _regionale_wishes_from_year_center(year, center)

    inteviews = []
    for wish in wishes:
        contestant = wish.contestant
        user = contestant.user
        args = (
            user.first_name, user.last_name, defaultfilters.date(user.birthday, "Y-m-d"),
            user.address, user.postal_code, user.city,
            wish.event.center.name,
            contestant.score_qualif_qcm, contestant.score_qualif_algo, contestant.score_qualif_bonus,
            contestant.correction_by.get_full_name(), contestant.correction_comments,
        )[:9]
        inteviews.append(r"\interview%s" % "".join("{%s}" % documents.models.latex_escape("" if arg is None else str(arg)) for arg in args))

    context = {
        'YEAR': documents.models.latex_escape(str(year)),
        'BODY': "\n".join(inteviews),
    }
    with documents.models.generate_tex_pdf("interviews.tex", context) as output:
        response = django.http.HttpResponse(content_type='application/pdf')
        #response['Content-Disposition'] = 'attachment; filename="liste-appel-{year}.pdf"'.format(
        #    year=year,
        #)
        response.write(output.read())
        return response