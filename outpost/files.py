# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import logging
import pdb
import re
from mimetypes import guess_type

from pyramid.static import static_view
from pyramid.httpexceptions import HTTPNotFound

from zope.interface import alsoProvides

from outpost import filtermanager


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
        log = logging.getLogger("files")
        settings = self.request.registry.settings
        url = self.request.url

        # run pre proxy request hooked filters
        # if the filter returns a response and not None. The response is returned
        # immediately
        proxy_response = filtermanager.runPreHook(None, self.request, self.url)
        if proxy_response:
            return proxy_response


        df = settings.get("files.defaultfile")
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
        try:
            file = static(self.context, self.request)
            alsoProvides(file, filtermanager.IFileRequest)
        except HTTPNotFound, e:
            if settings.get("server.log_notfound", "true").lower()=="true":
                log.info(self.request.url+" => Status: 404 Not found")
            raise
        # adjust headers
        file.headers["Cache-control"] = "no-cache"
        file.headers["Pragma"] = "no-cache"
        file.headers["Expires"] = "0"
        if "Last-Modified" in file.headers:
            del file.headers["Last-Modified"]
        # set default mime type to text/html
        if len(self.request.subpath):
            name = self.request.subpath[-1]
        else:
            name = df
        ct = guess_type(name, strict=False)[0] or settings.get("server.content_type")
        file.headers["Content-Type"] = ct
        file.content_type = ct
        
        if self.debug:
            server_trace = settings.get("files.trace")
            # bw 0.2.6 renamed setting
            if server_trace is None:
                server_trace = settings.get("server.trace")
            # trace in debugger
            if server_trace and re.search(server_trace, url):
                pdb.set_trace()

        # run post file server hooked filters
        file = filtermanager.run(file, self.request, self.url) #=> Ready to filter and return the current file. Step once (n) to apply filters.
        return file
        



