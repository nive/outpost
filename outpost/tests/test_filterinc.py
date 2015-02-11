
import unittest
import os
from pyramid.response import Response
from pyramid.request import Request
from pyramid import testing


from outpost import filterinc

class TemplateTest(unittest.TestCase):

    def test_empty(self):
        response = {}
        request = {}
        settings = {"template": None}
        response = filterinc.template(response, request, settings, None)
        self.assert_(response=={})

    def test_notmpl(self):
        response = testing.DummyRequest().response
        request = testing.DummyRequest()
        settings = {"template": "None"}
        self.assertRaises(ValueError, filterinc.template, response, request, settings, None)

    def test_chameleon_empty(self):
        response = testing.DummyRequest().response
        request = testing.DummyRequest()
        settings = {"template": "tmpl.pt"}
        config = testing.setUp(request=request)
        config.include('pyramid_chameleon')
        os.chdir(os.path.dirname(__file__))
        response = filterinc.template(response, request, settings, None)
        self.assert_(response.unicode_body==u"<html><body></body></html>")

    def test_chameleon_path1(self):
        response = testing.DummyRequest().response
        request = testing.DummyRequest()
        settings = {"template": "./tmpl.pt"}
        config = testing.setUp(request=request)
        config.include('pyramid_chameleon')
        os.chdir(os.path.dirname(__file__))
        response = filterinc.template(response, request, settings, None)
        self.assert_(response.unicode_body==u"<html><body></body></html>")

    def test_chameleon_path2(self):
        response = testing.DummyRequest().response
        request = testing.DummyRequest()
        settings = {"template": "../tests/tmpl.pt"}
        config = testing.setUp(request=request)
        config.include('pyramid_chameleon')
        response = filterinc.template(response, request, settings, None)
        self.assert_(response.unicode_body==u"<html><body></body></html>")

    def test_chameleon_path3(self):
        response = testing.DummyRequest().response
        request = testing.DummyRequest()
        settings = {"template": "outpost.tests:tmpl.pt"}
        config = testing.setUp(request=request)
        config.include('pyramid_chameleon')
        response = filterinc.template(response, request, settings, None)
        self.assert_(response.unicode_body==u"<html><body></body></html>")

    def test_chameleon_content(self):
        response = testing.DummyRequest().response
        response.unicode_body = u"Original response"
        request = testing.DummyRequest()
        settings = {"template": "tmpl.pt"}
        config = testing.setUp(request=request)
        config.include('pyramid_chameleon')
        os.chdir(os.path.dirname(__file__))
        response = filterinc.template(response, request, settings, None)
        self.assert_(response.unicode_body=="<html><body>Original response</body></html>")


class ReplacestrTest(unittest.TestCase):

    def test_empty(self):
        response = {}
        request = {}
        settings = {}
        response = filterinc.replacestr(response, request, settings, None)
        self.assert_(response=={})

    def test_nosettings(self):
        response = testing.DummyRequest().response
        request = testing.DummyRequest()
        settings = {"str": "", "new": ""}
        response = filterinc.replacestr(response, request, settings, None)
        self.assert_(response.unicode_body==u"")

    def test_single(self):
        response = testing.DummyRequest().response
        response.unicode_body = u"<html><body></body></html>"
        request = testing.DummyRequest()
        settings = {"str": "<body>", "new": "<body>Updated!"}
        response = filterinc.replacestr(response, request, settings, None)
        self.assert_(response.unicode_body=="<html><body>Updated!</body></html>")

    def test_multiple(self):
        response = testing.DummyRequest().response
        response.unicode_body = u"<html><body></body></html>"
        request = testing.DummyRequest()
        settings = [{"str": "<body>", "new": "<body>Updated!"},
                    {"str": "</body>", "new": "BREAK</body>"}]
        response = filterinc.replacestr(response, request, settings, None)
        self.assert_(response.unicode_body=="<html><body>Updated!BREAK</body></html>")

