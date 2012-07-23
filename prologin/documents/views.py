# coding=utf-8
from django.template import Context, loader
from team.models import Team
from users.models import User
from django.http import HttpResponse
import os

def gen_doc(request):
	with open('documents/contacts.csv', 'w') as f:
		f.write('\t'.join('prenom nom adresse codepostal ville\n'.split()))
		for user in User.objects.all()[:10]:
			f.write('\t'.join([user.prenom, user.nom, user.adresse, user.code_postal, user.ville]).encode('utf-8'))
			f.write('\n')
	os.system('cd documents && pdflatex finale')
	return HttpResponse(open('documents/finale.pdf').read(), mimetype = 'application/pdf')
