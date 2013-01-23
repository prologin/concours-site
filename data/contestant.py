import json, os, re
from data import *

contestants = {}
get_contestant_from_rdf = {}
get_contestant_from_rf = {}

questionnaires = csv('resultat_qcms.csv')
for questionnaire in questionnaires:
	contestant = {}
	id = int(questionnaire['id'])
	event_choices = []
	for i in range(1, 4):
		if int(questionnaire['choix_demi_{}'.format(i)]) > 0:
			event_choices.append(int(questionnaire['choix_demi_{}'.format(i)]))
	contestants[id] = {
		'user': questionnaire['user_id'],
		'events': [questionnaire['qcm_id']],
		'event_choices': event_choices
	}
	if int(questionnaire['resultat_demi_finale_id']) > 0:
		get_contestant_from_rdf[questionnaire['resultat_demi_finale_id']] = id

epreuves_regionales = csv('resultat_demi_finales.csv')
for epreuve in epreuves_regionales:
	if epreuve['id'] not in get_contestant_from_rdf:
		print('Foutue ligne orpheline', epreuve)
		continue
	id = get_contestant_from_rdf[epreuve['id']]
	contestants[id]['events'].append(epreuve['demi_finale_id'])
	get_contestant_from_rf[epreuve['resultat_finale_id']] = id

finales = csv('resultat_finales.csv')
for finale in finales:
	if finale['id'] not in get_contestant_from_rf:
		print('Foutue ligne orpheline', finale)
		continue
	id = get_contestant_from_rf[finale['id']]
	contestants[id]['events'].append(finale['finale_id'])

print()

django_contestant = []
for id in contestants:
	django_contestant.append(dict(pk=id, model='contest.contestant', fields=contestants[id]))

json.dump(django_contestant, open('contestant.json', 'w'))
os.system('python ../prologin/manage.py loaddata contestant.json')