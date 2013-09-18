
import logging
import time
import os
import pdb
import re

from pyramid.config import Configurator
from pyramid.static import static_view
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response

from filterinc import FILTER


class FileServer(object):

    def __init__(self, url, context, request):
        self.request = request
        self.context = context
        self.url = url
        
    def response(self):
        log = logging.getLogger("files")
        settings = self.request.registry.settings
        url = self.request.url
        static = static_view(root_dir=settings["server.directory"], 
                             use_subpath=True, 
                             index=settings.get("server.defaultfile"))
        try:
            file = static(self.context, self.request)
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
            name = settings.get("server.defaultfile","")
        if name.find(".")==-1 and settings.get("server.content_type"):
            file.headers["Content-Type"] = settings.get("server.content_type")
        
        # handle files based on extensions
        extensions = settings.get("filter.extensions")
        if not extensions:
            return file
        extensions = extensions.replace("  "," ").split(" ")
        if name.find(".")==-1 and "<empty>" in extensions:   
            # trace in debugger
            if settings["server.trace"] and re.search(settings["server.trace"], url):
                pdb.set_trace()
            file = self.filter(file) #=> Ready to filter and return the current file. Step once (n) to apply filters.
            return file
        for e in extensions:
            if name.endswith(e):
                # trace in debugger
                if settings["server.trace"] and re.search(settings["server.trace"], url):
                    pdb.set_trace()
                file = self.filter(file)  #=> Ready to filter and return the current file. Step once (n) to apply filters.
                return file
        return file
        

    def filter(self, file):
        """
        Processes filters defined in the configuration
        """
        settings = self.request.registry.settings
        # load filter. 
        for f in FILTER:
            conf = settings.get(f[0])
            if not conf:
                continue
            file = f[1](file, settings)
        return file
        
