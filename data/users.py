import json, os
from datetime import datetime
from data import *

profile_values = csv('profile_values.csv')
fids = {}
for entry in profile_values:
	fids.setdefault(int(entry['uid']), {})[int(entry['fid'])] = entry['value']

users = csv('users.csv')
django_user = []
django_userprofile = []
pk = 1
for user in users:
	try:
		uid = int(user['uid'])
		if uid == 0 or user['name'] == 'NULL':
			continue
		django_data = dict(pk=uid, model='auth.user', fields = {
			'username': user['name'],
			'password': '',
			'first_name': fids[uid][3] if uid in fids else '',
			'last_name': fids[uid][2] if uid in fids else '',
			'email': user['mail'],
			'last_login': datetime.fromtimestamp(int(user['login'])).isoformat() if 'login' in user else '',
			'date_joined': datetime.fromtimestamp(int(user['created'])).isoformat()
		})
		if uid == 1:
			django_data['fields']['password'] = 'pbkdf2_sha256$10000$8VI9m2cXyxbN$VVCTmSiKsu0b+DbATwUkhf1FJym51wi0giQeYvQzo8w='
			django_data['fields']['is_active'] = True
			django_data['fields']['is_staff'] = True
			django_data['fields']['is_superuser'] = True
		django_user.append(django_data)
		django_data = dict(pk=pk, model='users.userprofile', fields = {
			'user': uid,
			'title': fids[uid][1],
			'address': fids[uid][8],
			'postal_code': fids[uid][9],
			'city': fids[uid][10],
			'country': fids[uid][6],
			'phone_number': fids[uid][12] if 12 in fids[uid] else '',			
			'newsletter': fids[uid][11] == '0'
		})
		if birthday_from_drupal(fids[uid][5]) != '':
			django_data['fields']['birthday'] = birthday_from_drupal(fids[uid][5])
		django_userprofile.append(django_data)
		pk += 1
	except:
		print(pk, user)
		raise
# json.dump(django_user, open('user.json', 'w'))
json.dump(django_userprofile, open('userprofile.json', 'w'))
os.system('python ../prologin/manage.py loaddata userprofile.json user.json')

# uids = [1, 3627, 8109, 10360]
# sql('users')