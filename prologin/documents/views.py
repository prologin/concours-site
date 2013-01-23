# coding=utf-8
from django.template import Context, loader
from team.models import Team
from users.models import User
from contest.models import Event, Contestant
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from django.core.servers.basehttp import FileWrapper
import os, json

def french_date(date):
    jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    mois = ['janvier', u'février', 'mars', 'avril', 'mai']
    return ' '.join([jours[date.weekday()], str(date.day), mois[int(date.month) - 1], str(date.year)])

def latex_entities(code):
    return code.replace('\\n', '\\\\').replace(u'n°', '\\no{}')

def gen_doc(request):
    with open('documents/contacts.csv', 'w') as f:
        f.write('\t'.join('prenom nom adresse codepostal ville\n'.split()))
        for user in User.objects.all()[:10]:
            f.write('\t'.join([user.prenom, user.nom, user.adresse, user.code_postal, user.ville]).encode('utf-8'))
            f.write('\n')
    os.system('cd documents && pdflatex finale')
    return HttpResponse(open('documents/finale.pdf').read(), mimetype = 'application/pdf')

def generate_convocations(request):
    ct = request.GET.get('ct')
    event_ids = request.GET.get('ids').split(',')
    with open('documents/contestants.tex', 'w') as f:
        for event_id in event_ids:
            e = Event.objects.get(id=event_id)
            for c in e.contestant_set.all():
                cp = c.user.get_profile()
                f.write(latex_entities(u'\convocation{{{0}}}\n'.format('}{'.join([c.user.first_name, c.user.last_name, cp.address, cp.postal_code, cp.city, french_date(e.begin), e.center.name, e.center.address, e.center.postal_code + ' ' + e.center.city]))).encode('utf-8'))
    os.system('pwd')
    os.system('cd documents && pdflatex convocations-epreuves-regionales')
    response = HttpResponse(FileWrapper(open('documents/convocations-epreuves-regionales.pdf')), mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=convocations.pdf'
    return response
