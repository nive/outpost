# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import logging
import pdb
import re
from mimetypes import guess_type

from pyramid.static import static_view

from zope.interface import alsoProvides

from outpost import filtermanager

__ct_cache__ = {}


# delegate views to the file server
def serveFile(context, request):
    settings = request.registry.settings
    url = FileUrlHandler(request, settings)
    server = FileServer(url, context, request, debug=settings.get("debug"))
    return server.response()


class FileServer(object):
    """
    The file server handles local file serving based on the directory setting.
    """

    def __init__(self, url, context, request, debug):
        self.request = request
        self.context = context
        self.url = url
        self.debug = debug
        
    def response(self):
        log = logging.getLogger("outpost.files")
        settings = self.request.registry.settings
        url = self.request.url

        # run pre proxy request hooked filters
        # if the filter returns a response and not None. The response is returned
        # immediately
        try:
            file = filtermanager.runPreHook(filtermanager.EmptyFileResponse(), self.request, self.url)
        except filtermanager.ResponseFinished, e:
            return e.response

        if file is None:
            df = settings.get("server.default_path")
            # bw 0.2.6
            if df is None:
                df = settings.get("server.defaultfile")
            if df:
                static = static_view(root_dir=settings["files.directory"],
                                     use_subpath=True,
                                     index=df)
            else:
                static = static_view(root_dir=settings["files.directory"],
                                     use_subpath=True)
            file = static(self.context, self.request)
            alsoProvides(file, filtermanager.IFileRequest)

            # adjust headers
            #file.headers["Cache-control"] = "no-cache"
            #file.headers["Pragma"] = "no-cache"
            #file.headers["Expires"] = "0"
            #if "Last-Modified" in file.headers:
            #    del file.headers["Last-Modified"]
            # set default mime type to text/html
            if len(self.request.subpath):
                name = self.request.subpath[-1]
            else:
                name = df

            # cache content type
            global __ct_cache__
            ext = ".".join(name.split(".")[1:])
            if ext in __ct_cache__:
                ct = __ct_cache__[ext]
            else:
                ct = guess_type(name, strict=False)[0] or settings.get("server.content_type")
                __ct_cache__[ext] = ct

            file.headers["Content-Type"] = ct
            file.content_type = ct
            file.charset = settings.get("files.charset") or "utf-8"

        if self.debug:
            server_trace = settings.get("files.trace")
            # bw 0.2.6 renamed setting
            if server_trace is None:
                server_trace = settings.get("server.trace")
            # trace in debugger
            if server_trace and re.search(server_trace, url):
                pdb.set_trace()

        # run post file server hooked filters
        file = filtermanager.runPostHook(file, self.request, self.url) #=> Ready to filter and return the current file. Step once (n) to apply filters.
        return file
        



class FileUrlHandler(object):
    """
    Handles local urls

    Attributes:
    - protocol: http or https
    - host: without protocol, including port
    - path: path without protocol and domain
    - destUrl: valid proxy destination url
    - destDomain: valid proxy destination domain
    - srcUrl: embedded proxy url
    - srcDomain: embedded proxy domain

    Methods:
    - rewriteUrls()

    """
    def __init__(self, request, settings):
        self.host = "local"
        self.protocol = "file"
        self.path = "/".join(request.matchdict["subpath"])
        self.qs = request.query_string
        if not self.path.startswith("/"):
            self.path = "/"+self.path

    def __str__(self):
        return self.path

    @property
    def fullPath(self):
        if self.qs:
            return "//%s/%s%s?%s" % (self.protocol, self.host, self.path, self.qs)
        return "//%s/%s%s" % (self.protocol, self.host, self.path)

    @property
    def destUrl(self):
        return "//%s/%s%s" % (self.protocol, self.host, self.path)

    @property
    def srcUrl(self):
        return self.path

    @property
    def destDomain(self):
        return "//%s/%s" % (self.protocol, self.host)

    @property
    def srcDomain(self):
        return ""

    def rewriteUrls(self, body):
        return body


