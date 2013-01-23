import json, os, re
from data import *

django_contest = []
for year in range(1992, 2014):
	django_contest.append(dict(pk=year, model='contest.contest', fields={'year': year}))

events = csv('concours.csv')
types = {
	'Q': 'questionnaire',
	'D': 'épreuve régionale',
	'F': 'finale'
}
django_event = []
for event in events:
	try:
		id = int(event['id'])
		django_data = dict(pk=id, model='contest.event', fields={
			'contest': event['annee'],
			'center': 1 if int(event['centre_examen_id']) <= 0 else int(event['centre_examen_id']),
			'type': types[event['type'][0]],
		})
		if event['debut'] != 'NULL':
			django_data['fields']['begin'] = event['debut']
		if event['fin'] != 'NULL':
			django_data['fields']['end'] = event['fin']
		django_event.append(django_data)
	except:
		print(event)
		raise

json.dump(django_contest, open('contest.json', 'w'))
json.dump(django_event, open('event.json', 'w'))
os.system('python ../prologin/manage.py loaddata contest.json event.json')
