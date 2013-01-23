import json
tables = ['role', 'team']
data = []

pk = 1
for table in tables:
	j = json.load(open('team_{}.json'.format(table)))
	for entree in j:
		if table == 'role':
			fields = {'role': entree['role'], 'rank': entree['rank']}
		else:
			fields = {'role': entree['role_id'] + 1, 'uid': int(entree['uid']), 'year': int(entree['year'])}
		data.append({'pk': pk, 'model': 'team.' + table, 'fields': fields})
		pk += 1
	pk = 1
print(json.dumps(data, indent = 4))
