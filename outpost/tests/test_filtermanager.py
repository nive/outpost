
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
        self.assertTrue(filtermanager.IFileRequest.providedBy(file))

    def test_proxy(self):
        self.assertFalse(filtermanager.IProxyRequest.providedBy("oh no"))

    def test_proxyok(self):
        proxy = testing.DummyRequest()
        directlyProvides(proxy, filtermanager.IProxyRequest)
        self.assertTrue(filtermanager.IProxyRequest.providedBy(proxy))

    def test_filter(self):
        self.assertFalse(filtermanager.IFilter.providedBy("oh no"))

    def test_filterok(self):
        self.assertTrue(filtermanager.IFilter.providedBy(filtermanager.FilterConf()))

    def test_excp(self):
        filtermanager.ConfigurationError("OK")


class FilterConfTest(unittest.TestCase):

    def test_conf(self):
        c = filtermanager.FilterConf()
        self.assertTrue(c.callable is None)
        self.assertTrue(str(c))

    def test_dict(self):
        values = dict(
            callable = "outpost.filterinc.replacestr",
            apply_to = "",
            content_type = "",
            path = "",
            settings = {},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(c.name is "Filter example")
        self.assertFalse(c.apply_to)
        self.assertTrue(str(c) is "Filter example")

    def test_dict_callable1(self):
        values = dict(
            callable = "outpost.filterinc.replacestr",
            apply_to = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(c.name is "Filter example")
        self.assertTrue(filtermanager.IFileRequest == c.apply_to)

    def test_dict_callable2(self):
        values = dict(
            callable = lambda a,b,c: a,
            apply_to = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(c.name is "Filter example")
        self.assertTrue(filtermanager.IFileRequest == c.apply_to)

    def test_dict_callable3(self):
        def runfilter(a,b,c,d):
            return a
        values = dict(
            callable = runfilter,
            apply_to = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(c.name is "Filter example")
        self.assertTrue(filtermanager.IFileRequest == c.apply_to)

    def test_dict_apply1(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = "file",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(c.name is "Filter example")
        self.assertTrue(filtermanager.IFileRequest == c.apply_to)

    def test_dict_apply2(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = "proxy",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(c.name is "Filter example")
        self.assertTrue(filtermanager.IProxyRequest == c.apply_to)

    def test_dict_apply3(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = "",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(c.name is "Filter example")
        self.assertFalse(c.apply_to)

    def test_test1(self):
        values = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = "",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertFalse(c.test())

    def test_test2(self):
        values = dict(
            callable =  "outpost",
            apply_to = "",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        c = filtermanager.FilterConf.fromDict(values)
        self.assertTrue(len(c.test())==1)

    def test_test3(self):
        values = dict(
            callable =  "outpost",
            apply_to = "",
            content_type = 123,
            path = 456,
            settings = {"insert text": "Filtered!"},
            name = "Filter example"
        )
        self.assertRaises(TypeError, filtermanager.FilterConf.fromDict, values)


class JsonTest(unittest.TestCase):

    def test_empty(self):
        jsonstr = " "
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assertEqual(len(ff), 0)

        jsonstr = None
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assertEqual(len(ff), 0)

    def test_single(self):
        jsonstr = """{
           "callable": "outpost.filterinc.replacestr",
           "apply_to": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}"""
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assertEqual(len(ff), 1)
        self.assertEqual(ff[0].name, "String replacer example")

    def test_multiple(self):
        jsonstr = """[{
           "callable": "outpost.filterinc.replacestr",
           "apply_to": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"},
           {
           "callable": "outpost.filterinc.replacestr",
           "apply_to": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "2. String replacer example"}]"""
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assertEqual(len(ff), 2)
        self.assertEqual(ff[0].name, "String replacer example")
        self.assertEqual(ff[1].name, "2. String replacer example")

    def test_failure(self):
        jsonstr = """{
           "callable": "",
           "apply_to": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}"""
        ff = filtermanager.parseJsonString(jsonstr, exitOnTestFailure=False)
        self.assertEqual(len(ff), 0)

    def test_failure2(self):
        jsonstr = """{
           "callable": "",
           "apply_to": "file",
           "path": ".html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}"""
        self.assertRaises(filtermanager.ConfigurationError, filtermanager.parseJsonString, jsonstr, exitOnTestFailure=True)


class RunTest(unittest.TestCase):

    filter1 = dict(
        callable =  "outpost.filterinc.replacestr",
        apply_to = None,
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
        response = filtermanager.applyFilter(fc, response, request, request.url)
        self.assertTrue(response.unicode_body=="<html><body>Updated!</body></html>")

    def test_runpost(self):
        fc = filtermanager.FilterConf.fromDict(self.filter1)
        response = testing.DummyRequest().response
        response.unicode_body = u"<html><body></body></html>"
        request = testing.DummyRequest()
        request.registry.settings = {"filter": (fc,)}
        response = filtermanager.runPostHook(response, request, request.url)
        self.assertTrue(response.unicode_body=="<html><body>Updated!</body></html>")

    def test_lookup_file(self):
        filter_file = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = "file",
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
        filter = [f for f in filtermanager.lookupFilter("post", response, request, request.url)]
        self.assertTrue(len(filter)==1)

    def test_lookup_proxy(self):
        filter_proxy = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = "proxy",
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
        filter = [f for f in filtermanager.lookupFilter("post", response, request, request.url)]
        self.assertTrue(len(filter)==1)

    def test_lookup_path(self):
        filter_path = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = None,
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
        filter = [f for f in filtermanager.lookupFilter("post", response, request, request.url)]
        self.assertTrue(len(filter)==1)

        request.url = "http://localhost/files/image.png"
        filter = [f for f in filtermanager.lookupFilter("post", response, request, request.url)]
        self.assertTrue(len(filter)==0)

    def test_lookup_ct(self):
        filter_ct = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = None,
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
        filter = [f for f in filtermanager.lookupFilter("post", response, request, request.url)]
        self.assertTrue(len(filter)==1)

        response.content_type = "image/png"
        filter = [f for f in filtermanager.lookupFilter("post", response, request, request.url)]
        self.assertTrue(len(filter)==0)


    def test_lookup_all(self):
        filter_all = dict(
            callable =  "outpost.filterinc.replacestr",
            apply_to = "file",
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
        filter = [f for f in filtermanager.lookupFilter("post", response, request, request.url)]
        self.assertTrue(len(filter)==1)
