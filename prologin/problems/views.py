#!/usr/bin/python2
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from langs import langs
import os
import os.path
import yaml
import glob
import vm_interface
import datetime
from problems_api import *

# Create your views here.

def index(request):
    return render_to_response('index.html')

def show_list_challenges(request):
    challenges = list_challenges()
    return render_to_response('problems/index.html', {'challenges': challenges})

def show_list_problems(request, challenge):
    challenge, problems = get_challenge(challenge)
    problems = sorted(problems, key=lambda p: p['props']['difficulty'])
    return render_to_response('problems/challenge.html', {'challenge': challenge, 'problems': problems})

def show_problem(request, challenge, problem):
    problem_data = get_problem(challenge, problem)
    statement, statement_type = problem_data['subject']
    markdown = (statement_type == 'markdown')
    examples = []
    print(problem_data['props'])
    for test in problem_data['props']['samples'].split():
        example = {}
        for ext in ['in', 'comment', 'out']:
            test_name = '{0}.{1}'.format(test, ext)
            if test_name in problem_data['tests']:
                example[ext] = problem_data['tests'][test_name]
        examples.append(example)
    return render_to_response('problems/problem.html', {'problem': problem_data, 'statement': statement, 'examples': examples, 'statement_markdown': markdown})

def get_path_archive(challenge, problem, pseudo, timestamp):
    [match] = glob.glob(os.path.join(settings.ARCHIVES_PATH, '{0}-{1}-{2}-{3}.*'.format(timestamp, challenge, problem, pseudo)))
    return match

def get_list_archives(challenge, problem, pseudo):
    return glob.glob(os.path.join(settings.ARCHIVES_PATH, '*-{0}-{1}-{2}.*'.format(challenge, problem, pseudo)))

def traces(request, challenge, problem):
    archives = get_list_archives(challenge, problem, request.user.username)
    archives = list(map(os.path.basename, archives))
    traces = {} # language id : [(timestamp, date_str), ..]
    for i, lang in langs.iteritems():
        for a, archive in enumerate(archives):
            filename, extension = os.path.splitext(archive)
            timestamp = int(filename.split('-')[0])
            dt = datetime.fromtimestamp(timestamp)
            if extension == lang.ext:
                traces.setdefault(i, []).append((timestamp, dt.strftime('%d/%m/%Y à %H:%M:%S')))
                archives.pop(a)
    return render_to_response('problems/traces.html', {'langs': langs, 'traces': traces, 'problem_props': get_props(path_problem_props(challenge, problem))})

def trace(request, challenge, problem, timestamp):
    path = get_path_archive(challenge, problem, request.user.username, timestamp)
    code = open(path).read()
    filename = os.path.basename(path)
    problem_props = get_props(path_problem_props(challenge, problem))
    xml = vm_interface.remote_check(challenge, problem, code, filename)
    compilation, results, tests_details = vm_interface.parse_xml(xml, problem_props)
    tpl_env = {
        'compilation': compilation,
        'results': results,
        'tests_details': tests_details,
        'challenge': challenge,
        'problem': problem,
    }
    return render_to_response('problems/trace.html', {})
