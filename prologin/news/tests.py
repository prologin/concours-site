# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from prologin.tests import Validator
from django.conf import settings
from xml.dom.minidom import parseString
from news.models import News

class TeamTest(TestCase):
    def setUp(self):
        self.validator = Validator()
        self.client = Client()

    def test_css(self):
        """
        Tests the CSS' compliance with the W3C standards.
        """
        path = settings.SITE_ROOT + 'prologin/static/prologin.css'
        css = open(path, 'r').read()
        valid = self.validator.checkCSS(css)
        self.assertEqual(valid, True)

    def test_html(self):
        """
        Tests the HTML's compliance with the W3C standards.
        """
        News.objects.all().delete()
        response = self.client.get(reverse('home'))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)

        n = News(title='<test>news<b>1</test2> è_é', body='Lorem ïpsum 1 <i>dolor</i> sit <b>amnet, <i>consicutor</b> melorum ignare.</i>')
        n.save()
        response = self.client.get(reverse('home'))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)

        response = self.client.get(reverse('news:show', args=(n.id,)))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)

        News(title='<test>news<b>2</test2> è_é', body='Lorem ïpsum 2 <i>dolor</i> sit <b>amnet, <i>consicutor</b> melorum ignare.</i>').save()
        News(title='<test>news<b>3</test2> è_é', body='Lorem ïpsum 3 <i>dolor</i> sit <b>amnet, <i>consicutor</b> melorum ignare.</i>').save()
        response = self.client.get(reverse('home'))
        valid = self.validator.checkHTML(response.content)
        self.assertEqual(valid, True)

    def test_rss(self):
        """
        Tests the RSS' validity.
        """
        try:
            News.objects.all().delete()
            response = self.client.get(reverse('news:rss'))
            parseString(response.content)

            News(title='<test>news<b>1</test2> è_é', body='Lorem ïpsum 1 <i>dolor</i> sit <b>amnet, <i>consicutor</b> melorum ignare.</i>').save()
            response = self.client.get(reverse('news:rss'))
            parseString(response.content)

            News(title='<test>news<b>2</test2> è_é', body='Lorem ïpsum 2 <i>dolor</i> sit <b>amnet, <i>consicutor</b> melorum ignare.</i>').save()
            News(title='<test>news<b>3</test2> è_é', body='Lorem ïpsum 3 <i>dolor</i> sit <b>amnet, <i>consicutor</b> melorum ignare.</i>').save()
            response = self.client.get(reverse('news:rss'))
            parseString(response.content)
        except:
            self.fail('Invalid XML')
