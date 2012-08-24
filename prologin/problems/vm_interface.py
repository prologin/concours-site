#!/usr/bin/python2
# coding: utf-8

import urllib
import urllib2
from collections import namedtuple
from xml.etree import ElementTree as etree
from django.conf import settings
import xml.etree.ElementTree as ElementTree

def remote_check(challenge, problem, source, filename):
    args = {
            'challenge' : challenge,
            'problem' : problem,
            'source' : source,
            'filename' : filename,
            }
    data = urllib.urlencode(args)
    request = urllib2.Request(settings.REMOTE_VM_URL)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded;charset:utf-8')
    request.add_header('User-Agent', "Site d'entraînement TTY-powered")
    
    result = urllib2.urlopen(request, data)
    result = result.read().decode('utf-8').strip()
    return result

class TestResult():
    def __init__(self):
        status = ''
        details = None
        debug = None
        hidden = False
        test_type = 'standard'

def parse_xml(s, problem_props):
    xml = ElementTree.fromstring(s)
    error = xml.find('error')
    if error:
        raise VMError(error)
    compilation = {
        'sucess': bool(xml.find('test'))
        'value': xml.find('compilation').text.strip()
    }
    tests_results = {
        'standard': [0, 0] # [nb, nb_ok]
        'performance': [0, 0]
    }
    
    details = []
    for test in xml.findall('test'):
        t = TestResult()
        
        if test.attrib['id'] in problem_props['performance']
            t.test_type = 'performance'
        else:
            t.test_type = 'standard'

        tests_results[t.test_type][1] += 1
        if test.find('summary').attrib['error'] == 0:
            t.status, t.details = 'ok', None
            tests_results[t.test_type][0] += 1
        else:
            details = test.find('details')
            if details.find('diff'):
                t.status, t.details = 'diff', details.find('diff')
            elif details.find('program'):
                t.status = 'program-ref'
                t.details = (details.find('program').text, details.find('ref').text)
        
        if test.find('debug'):
            t.debug = test.find('debug').text
        else:
            t.debug = None
        
        if test.attrib['id'] in problem_props['hidden'].split():
            t.hidden = True
            
        details.append(t)

        return compilation, tests_results, details
