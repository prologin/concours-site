from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
import os
import yaml
import glob
import vm_interface

# Create your views here.

def index(request):
	return render_to_response('index.html')

def get_props(file):
	return yaml.load(open(file), Loader=yaml.loader.BaseLoader) # BaseLoader => 01 (sample) is not converted to int

def get_challenge(path):
	challenge = {}
	problems = []
	for item in os.listdir(path):
		if '.svn' in item:
			continue
		subpath = '/'.join([path, item])
		if item.endswith('.props'):
			challenge['props'] = get_props(subpath)
		elif os.path.isdir(subpath):
			problems.append(get_problem(subpath))
	return challenge, problems

def get_problem(path):
	problem = {'name': os.path.basename(path)}
	for item in os.listdir(path):
		if '.svn' in item:
			continue
		subpath = '/'.join([path, item])
		if item.endswith('.props'):
			problem['props'] = get_props(subpath)
		else:
			problem.setdefault('list', []).append(item)
	return problem

def list_challenges(request):
	challenges = []
	for item in os.listdir('../../problems/'):
		if '.svn' in item:
			continue
		props = u'../../problems/{0}/challenge.props'.format(item)
		if os.path.exists(props):
			challenges.append({'name': item, 'title': get_props(props)['title']})
	return render_to_response('problems/index.html', {'challenges': challenges})

def list_problems(request, challenge):
	challenge, problems = get_challenge('../../problems/{0}'.format(challenge))
	problems = sorted(problems, key=lambda p: p['props']['difficulty'])
	return render_to_response('problems/challenge.html', {'challenge': challenge, 'problems': problems})

def show_problem(request, challenge, problem):
	problem_path = '../../problems/{0}/{1}'.format(challenge, problem)
	problem = get_problem(problem_path)
	statement = open('{0}/subject.md'.format(problem_path)).read()
	examples = []
	print(problem['props'])
	for test in problem['props']['samples'].split():
		example = {}
		for ext in ['in', 'comment', 'out']:
			test_path = '{0}/{1}.{2}'.format(problem_path, test, ext)
			print(test_path)
			if os.path.exists(test_path):
				example[ext] = open(test_path).read()
		examples.append(example)
	return render_to_response('problems/problem.html', {'problem': problem, 'statement': statement, 'examples': examples})

def get_path_archive(challenge, problem, pseudo, timestamp):
    [match] = glob.glob(os.path.join(settings.ARCHIVES_PATH, '{0}-{1}-{2}-{3}.*'.format(timestamp, challenge, problem, pseudo)))
    return match

def trace(request, challenge, problem, timestamp):
    path = get_path_archive(challenge, problem, request.user.username, timestamp)
    code = open(path).read()
    filename = os.path.basename(path)
    xml = vm_interface.remote_check(challenge, problem, code, filename)
