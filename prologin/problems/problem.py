import os

from django.conf import settings

from problems import QUALIFICATION_TUP, REGIONAL_TUP


def path_challenge(challenge, *tail):
    return os.path.abspath(os.path.join(settings.TRAINING_PROBLEM_REPOSITORY_PATH, challenge, *tail))


def path_problem(challenge, problem, *tail):
    return path_challenge(challenge, problem, *tail)


def path_challenge_props(challenge):
    return path_challenge(challenge, 'challenge.props')


def path_problem_props(challenge, problem):
    return path_problem(challenge, problem, 'problem.props')


def get_props(filename):
    def parse(value):
        value = value.strip()
        value_lower = value.lower()
        if value.isnumeric() or (value.startswith('-') and value[1:].isnumeric()):
            return int(value)
        if value_lower in ('true', 'false'):
            return value_lower == 'true'
        return value

    with open(filename) as f:
        return {k.strip(): parse(v)
                for line in f if line.strip()
                for k, v in [line.split(':', 1)]}


def get_challenge(challenge, with_subject=False, with_problem_props=False, with_problem_data=False):
    path = path_challenge(challenge)
    problems = []
    challenge_props = get_props(path_challenge_props(challenge))

    if challenge.startswith('demi'):
        event_type = REGIONAL_TUP
    elif challenge.startswith('qcm'):
        event_type = QUALIFICATION_TUP
    else:
        event_type = None

    for problem_dir in os.listdir(path):
        full_problem_dir = os.path.join(path, problem_dir)
        if os.path.isdir(full_problem_dir) and not problem_dir.startswith('.') and os.path.exists(
                path_problem_props(challenge, problem_dir)):
            problems.append(get_problem(challenge, problem_dir,
                                        with_props=with_problem_props, with_data=with_problem_data))
    data = {
        'name': challenge,
        'props': challenge_props,
        'problems': problems,
        'event_type': event_type,
    }
    if with_subject:
        with open(path_challenge(challenge, 'challenge.txt')) as f:
            data['subject'] = f.read()
    return data

def get_problem(challenge, problem, with_props=False, with_data=False):
    path = path_problem(challenge, problem)
    problem_data = {
        'name': problem,
        'tests': {},
        'subject': '',
    }

    if with_props:
        problem_data['props'] = get_props(path_problem_props(challenge, problem))

    if with_data:
        subject_path_md = path_problem(challenge, problem, 'subject.md')
        subject_path_txt = path_problem(challenge, problem, 'subject.txt')
        if os.path.exists(subject_path_md):
            with open(subject_path_md) as f:
                problem_data['subject'] = (f.read(), 'markdown')
        elif os.path.exists(subject_path_txt):
            with open(subject_path_txt) as f:
                problem_data['subject'] = (f.read(), 'html')
        for item in os.listdir(path):
            subpath = os.path.join(path, item)
            if item.endswith('.in') or item.endswith('.out'):
                with open(subpath) as f:
                    problem_data['tests'][item] = f.read()

    return problem_data


def list_challenges():
    challenges = []

    for challenge_dir in os.listdir(settings.TRAINING_PROBLEM_REPOSITORY_PATH):
        if not challenge_dir.startswith('.'):
            prop_file = path_challenge_props(challenge_dir)
            if os.path.exists(prop_file):
                challenge = get_challenge(challenge_dir, with_problem_props=False, with_problem_data=False)
                if challenge['event_type'] and challenge['props'].get('display_website', True):
                    challenges.append(challenge)

    return challenges
