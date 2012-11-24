#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from django.conf import settings
import os
import os.path


def get_props(filename):
    props = {}
    for line in open(filename):
        key, value = line.split(':', 1)
        props[key.strip()] = value.strip()
    return props


path_challenge = lambda c: os.path.join(settings.PROBLEMS_PATH, c)
path_problem = lambda c, p: os.path.join(settings.PROBLEMS_PATH, c, p)
path_challenge_props = lambda challenge: os.path.join(
        settings.PROBLEMS_PATH, challenge, 'challenge.props')
path_problem_props = lambda challenge, problem: os.path.join(
        settings.PROBLEMS_PATH, challenge, problem, 'problem.props')


def get_challenge(challenge):
    path = path_challenge(challenge)
    problems = []
    challenge_props = get_props(path_challenge_props(challenge))
    for item in os.listdir(path):
        subpath = os.path.join(path, item)
        if os.path.isdir(subpath) and not item.startswith('.'):
            problems.append(get_problem(challenge, item))
    return challenge_props, problems


def get_problem(challenge, problem):
    path = path_problem(challenge, problem)
    problem_data = {
        'name': problem,
        'props': get_props(path_problem_props(challenge, problem)),
        'tests': {},
    }

    if os.path.exists(os.path.join(path, 'subject.md')):
        problem_data['subject'] = (open(os.path.join(path,
            'subject.md')).read(), 'markdown')
    elif os.path.exists(os.path.join(path, 'subject.txt')):
        problem_data['subject'] = (open(os.path.join(path,
            'subject.txt')).read(), 'html')
    else:
        problem_data['subject'] = ''

    for item in os.listdir(path):
        subpath = os.path.join(path, item)
        if item.endswith('.in') or item.endswith('.out'):
            problem_data['tests'][item] = open(subpath).read()
    return problem_data


def list_challenges():
    challenges = []

    def available(challenge):
        return challenge.startswith('demi') or challenge.startswith('qcm')
    for item in os.listdir(settings.PROBLEMS_PATH):
        if not item.startswith('.') and available(item):
            props = path_challenge_props(item)
            if os.path.exists(props):
                challenges.append({'name': item, 'title':
                    get_props(props)['title']})
    return challenges
