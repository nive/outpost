
import unittest
import os
from zope.interface import directlyProvides
from pyramid.response import Response
from pyramid.request import Request
from pyramid import testing


from outpost import filtermanager

class IfaceTest(unittest.TestCase):

    def test_file(self):
        self.assertFalse(filtermanager.IFileRequest.providedBy("oh no"))

    def test_fileok(self):
        file = testing.DummyRequest()
        directlyProvides(file, filtermanager.IFileRequest)
        self.assert_(filtermanager.IFileRequest.providedBy(file))

    def test_proxy(self):
        self.assertFalse(filtermanager.IProxyRequest.providedBy("oh no"))

    def test_proxyok(self):
        proxy = testing.DummyRequest()
        directlyProvides(proxy, filtermanager.IProxyRequest)
        self.assert_(filtermanager.IProxyRequest.providedBy(proxy))

    def test_filter(self):
        self.assertFalse(filtermanager.IFilter.providedBy("oh no"))

    def test_filterok(self):
        self.assert_(filtermanager.IFilter.providedBy(filtermanager.FilterConf()))

    def test_excp(self):
        filtermanager.ConfigurationError("OK")


class FilterConfTest(unittest.TestCase):

    def test_conf(self):
        c = filtermanager.FilterConf()
        self.assert_(c.callable is None)
        self.assert_(str(c))

    def test_dict(self):
        values = dict(
            callable = "outpost.filterinc.replacestr",
            applyTo = "",
            content_type = "",
            path = "",
            settings = {},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(c.name is "Filter example")
        self.assertFalse(c.applyTo)
        self.assert_(str(c) is "Filter example")

    def test_dict_callable1(self):
        values = dict(
            callable = "outpost.filterinc.replacestr",
            applyTo = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(c.name is "Filter example")
        self.assert_(filtermanager.IFileRequest == c.applyTo)

    def test_dict_callable2(self):
        values = dict(
            callable = lambda a,b,c: a,
            applyTo = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(c.name is "Filter example")
        self.assert_(filtermanager.IFileRequest == c.applyTo)

    def test_dict_callable3(self):
        def runfilter(a,b,c,d):
            return a
        values = dict(
            callable = runfilter,
            applyTo = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(c.name is "Filter example")
        self.assert_(filtermanager.IFileRequest == c.applyTo)

    def test_dict_apply1(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(c.name is "Filter example")
        self.assert_(filtermanager.IFileRequest == c.applyTo)

    def test_dict_apply2(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = "proxy",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(c.name is "Filter example")
        self.assert_(filtermanager.IProxyRequest == c.applyTo)

    def test_dict_apply3(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = "",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(c.name is "Filter example")
        self.assertFalse(c.applyTo)

    def test_test1(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = "",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertFalse(c.test())

    def test_test2(self):
        values = dict(
            callable =  "outpost",
            applyTo = "",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(len(c.test())==1)

    def test_test3(self):
        values = dict(
            callable =  "outpost",
            applyTo = "",
            content_type = 123,
            path = 456,
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assert_(len(c.test())==3)


class JsonTest(unittest.TestCase):

    def test_empty(self):
        jsonstr = " "
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assert_(len(ff)==0)

        jsonstr = None
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assert_(len(ff)==0)

    def test_single(self):
        jsonstr = """{
           "callable": "outpost.filterinc.replacestr",
           "applyTo": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}"""
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assert_(len(ff)==1)
        self.assert_(ff[0].name=="String replacer example")

    def test_multiple(self):
        jsonstr = """[{
           "callable": "outpost.filterinc.replacestr",
           "applyTo": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"},
           {
           "callable": "outpost.filterinc.replacestr",
           "applyTo": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "2. String replacer example"}]"""
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assert_(len(ff)==2)
        self.assert_(ff[0].name=="String replacer example")
        self.assert_(ff[1].name=="2. String replacer example")

    def test_failure(self):
        jsonstr = """{
           "callable": "",
           "applyTo": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}"""
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assert_(len(ff)==0)

    def test_failure2(self):
        jsonstr = """{
           "callable": "",
           "applyTo": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}"""
        self.assertRaises(filtermanager.ConfigurationError, filtermanager.parseJsonString, jsonstr, exitOnTestFailure=True)


class RunTest(unittest.TestCase):

    filter1 = dict(
        callable =  "outpost.filterinc.replacestr",
        applyTo = None,
        path = None,
        content_type = None,
        settings = {"str": "<body>", "new": "<body>Updated!"},
        name = "Filter example"
    )


    def test_apply(self):
        fc = filtermanager.FilterConf.fromDict(self.filter1)
        response = testing.DummyRequest().response
        response.unicode_body = u"<html><body></body></html>"
        request = testing.DummyRequest()
        response = filtermanager.applyFilter(fc, response, request, None)
        self.assert_(response.unicode_body=="<html><body>Updated!</body></html>")

    def test_run(self):
        fc = filtermanager.FilterConf.fromDict(self.filter1)
        response = testing.DummyRequest().response
        response.unicode_body = u"<html><body></body></html>"
        request = testing.DummyRequest()
        request.registry.settings = {"filter": (fc,)}
        response = filtermanager.run(response, request, None)
        self.assert_(response.unicode_body=="<html><body>Updated!</body></html>")

    def test_lookup_file(self):
        filter_file = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = "file",
            path = None,
            content_type = None,
            settings = {"str": "<body>", "new": "<body>Updated!"},
            name = "Filter example"
        )
        fc = filtermanager.FilterConf.fromDict(filter_file)
        response = testing.DummyRequest().response
        directlyProvides(response, filtermanager.IFileRequest)
        request = testing.DummyRequest()
        request.registry.settings = {"filter": (fc,)}
        filter = filtermanager.lookupFilter(response, request, None)
        self.assert_(len(filter)==1)

    def test_lookup_proxy(self):
        filter_proxy = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = "proxy",
            path = None,
            content_type = None,
            settings = {"str": "<body>", "new": "<body>Updated!"},
            name = "Filter example"
        )
        fc = filtermanager.FilterConf.fromDict(filter_proxy)
        response = testing.DummyRequest().response
        directlyProvides(response, filtermanager.IProxyRequest)
        request = testing.DummyRequest()
        request.registry.settings = {"filter": (fc,)}
        filter = filtermanager.lookupFilter(response, request, None)
        self.assert_(len(filter)==1)

    def test_lookup_path(self):
        filter_path = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = None,
            path = "index\.html",
            content_type = None,
            settings = {"str": "<body>", "new": "<body>Updated!"},
            name = "Filter example"
        )
        fc = filtermanager.FilterConf.fromDict(filter_path)
        response = testing.DummyRequest().response
        request = testing.DummyRequest()
        request.url = "http://localhost/files/index.html"
        request.registry.settings = {"filter": (fc,)}
        filter = filtermanager.lookupFilter(response, request, None)
        self.assert_(len(filter)==1)

        request.url = "http://localhost/files/image.png"
        filter = filtermanager.lookupFilter(response, request, None)
        self.assert_(len(filter)==0)

    def test_lookup_ct(self):
        filter_ct = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = None,
            path = None,
            content_type = "text/html",
            settings = {"str": "<body>", "new": "<body>Updated!"},
            name = "Filter example"
        )
        fc = filtermanager.FilterConf.fromDict(filter_ct)
        response = testing.DummyRequest().response
        response.content_type = "text/html"
        request = testing.DummyRequest()
        request.registry.settings = {"filter": (fc,)}
        filter = filtermanager.lookupFilter(response, request, None)
        self.assert_(len(filter)==1)

        response.content_type = "image/png"
        filter = filtermanager.lookupFilter(response, request, None)
        self.assert_(len(filter)==0)


    def test_lookup_all(self):
        filter_all = dict(
            callable =  "outpost.filterinc.replacestr",
            applyTo = "file",
            path = "index\.html",
            content_type = "text/*",
            settings = {"str": "<body>", "new": "<body>Updated!"},
            name = "Filter example"
        )
        fc = filtermanager.FilterConf.fromDict(filter_all)
        response = testing.DummyRequest().response
        response.content_type = "text/html"
        directlyProvides(response, filtermanager.IFileRequest)
        request = testing.DummyRequest()
        request.url = "http://localhost/files/index.html"
        request.registry.settings = {"filter": (fc,)}
        filter = filtermanager.lookupFilter(response, request, None)
        self.assert_(len(filter)==1)
