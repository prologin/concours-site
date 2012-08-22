#!/usr/bin/python2
# coding: utf-8

import urllib
import urllib2
from collections import namedtuple
from xml.etree import ElementTree as etree
from django.conf import settings

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

