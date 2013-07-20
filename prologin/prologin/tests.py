from time import sleep
import httplib, urllib
import re

class Validator():
    def __init__(self):
        self.useragent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36'

    def SOAPValidity(self, soap):
        # Why not using a lib?
        # 1. including dependencies only for unit testing sounds weird
        # 2. at this time, there's no good and maintained projects:
        #    http://stackoverflow.com/questions/206154/whats-the-best-soap-client-library-for-python-and-where-is-the-documentation-f
        pat = re.compile(r'^.*<m:validity>true</m:validity>.*$', re.M | re.I)
        return pat.search(soap) != None

    def wait(self):
        sleep(2)

    def checkHTML(self, html):
        self.wait()
        conn = httplib.HTTPConnection('validator.w3.org')
        params = urllib.urlencode({
            'fragment': html,
            'prefill': 0,
            'doctype': 'Inline',
            'prefill_doctype': 'html401',
            'group': 0,
            'output': 'soap12',
        })
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': self.useragent,
        }
        conn.request('POST', '/check', params, headers)
        response = conn.getresponse()
        if response.status != 200:
            return False
        data = response.read()
        return self.SOAPValidity(data)

    def checkCSS(self, css):
        self.wait()
        conn = httplib.HTTPConnection('jigsaw.w3.org')
        params = urllib.urlencode({
            'text': css,
            'profile': 'css3',
            'usermedium': 'all',
            'type': 'none',
            'warning': '1',
            'vextwarning': 'true',
            'lang': 'en',
            'output': 'soap12',
        })
        headers = {
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': self.useragent,
        }
        conn.request('GET', '/css-validator/validator?' + str(params), headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            return False
        data = response.read()
        return self.SOAPValidity(data)
