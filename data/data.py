import os, re
from collections import Counter

def csv(file):
	with open(file + '.tmp', 'wb') as f:
		f.write(open(file, 'rb').read().replace(b'\r', b''))
	os.system('mv {}.tmp {}'.format(file, file))
	with open(file) as f:
		fields = f.readline().strip().split('\t')
		data = [dict(zip(fields, line.split('\t'))) for line in f.read().splitlines()]
	return data

def birthday_from_drupal(beurk):
	day = int(re.search('s:3:"day";s:\d+:"(\d+)"', beurk).group(1))
	month = int(re.search('s:5:"month";s:\d+:"(\d+)"', beurk).group(1))
	year = int(re.search('s:4:"year";s:\d+:"(\d+)"', beurk).group(1))
	return '{:4d}-{:02d}-{:02d}'.format(year, month, day)

def sql(table, uids=[]):
	command = 'select * from {}'.format(table)
	if uids:
		 command += ' where ' + ' or '.join(['uid = {}'.format(uid) for uid in uids])
	os.system('echo "{}" | mysql -u root -proot prologin > {}-tmp.csv'.format(command, table))
	os.system('iconv -f latin1 -t utf8 {}-tmp.csv > {}.csv && rm {}-tmp.csv'.format(table, table, table))
