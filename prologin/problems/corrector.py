from django.conf import settings
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ElementTree

# TODO:
# - retrieve compile time from vm
# - retrieve run time from vm
# - retrieve memory consumption from vm

# When updating this file, please increment USER_AGENT_VERSION accordingly.
USER_AGENT_VERSION = "0.1"


def remote_check(url, challenge, problem, source, filename):
    args = {
        'challenge': challenge,
        'problem': problem,
        'source': source,
        'filename': filename,
    }
    data = urllib.parse.urlencode(args).encode('utf-8')
    request = urllib.request.Request(url)
    request.add_header('Content-Type',
                       'application/x-www-form-urlencoded;charset:utf-8')
    request.add_header('User-Agent', 'prologin-vm-interface/{}'.format(USER_AGENT_VERSION))

    with urllib.request.urlopen(request, data, timeout=settings.TRAINING_CORRECTOR_REQUEST_TIMEOUT) as response:
        payload = response.read()
        try:
            return payload.decode('utf-8').strip()
        except UnicodeDecodeError:
            # log the raw response for debug purposes
            import hashlib
            chksum = hashlib.md5(source.encode('utf-8', 'ignore')).hexdigest()
            fname = '/tmp/celeryworker.{}.{}.{}.reponse.log'.format(challenge, problem, chksum)
            with open(fname, 'wb') as log_file:
                log_file.write(payload)
            raise


def parse_xml(s):
    xml = ElementTree.fromstring(s)
    error = xml.find('error')
    if error:
        raise Exception(error)

    compilation = {
        'success': xml.find('test') is not None,
        'value': xml.find('compilation').text.strip(),
    }
    tests = []
    for test in xml.findall('test'):
        t = {
            'id': test.attrib['id'],
            'performance': test.attrib['performance'] == '1',
            'hidden': test.attrib['hidden'] == '1',
            'passed': test.find('summary').attrib['error'] == '0'}

        details = test.find('details')
        if details is not None:
            for child in test.find('details'):
                if child.tag in ('program', 'ref', 'diff'):
                    t[child.tag] = child.text

        debug = test.find('debug')
        if debug is not None:
            t['debug'] = debug.text

        tests.append(t)

    return compilation, tests
