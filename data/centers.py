import json, os, re
from data import *

centers = csv('centre_examens.csv')
django_center = [dict(pk=7, model='centers.center', fields={'city': 'Ville fantôme', 'name': 'Ville fantôme', 'type': 'centre', 'address': '168 rue du Phacochère', 'phone_number': '', 'comments': ''})]
non_decimal = re.compile(r'[^\d]+')
for center in centers:
	try:
		id = int(center['id'])
		django_data = dict(pk=id, model='centers.center', fields={
			'city': center['ville'],
			'name': center['nom'],
			'type': 'centre',
			'address': '{} {} {}'.format(center['adresse'], center['code_postal'], center['ville']),
			'phone_number': non_decimal.sub('', center['resp_tel_fixe']),
			'comments': center['commentaires'],
		})
		django_center.append(django_data)
	except:
		print(center)
		raise
json.dump(django_center, open('center.json', 'w'))
os.system('python ../prologin/manage.py loaddata center.json')
