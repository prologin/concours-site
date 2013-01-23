import json, os, re
from data import *

centers = [_.split('|') for _ in open('centers.sql').read().splitlines()]
django_center = []
non_decimal = re.compile(r'[^\d]+')
id = 23
for center in centers:
	try:
		django_data = dict(pk=id, model='centers.center', fields={
			'city': center[1],
			'name': center[2],
			'type': center[3],
			'address': center[4],
			'phone_number': center[5],
			'comments': center[6],
			'lat': center[7],
			'lng': center[8],
		})
		django_center.append(django_data)
	except:
		print(center)
		raise
	id += 1
json.dump(django_center, open('center-bonus.json', 'w'))
# os.system('python ../prologin/manage.py loaddata center.json')
