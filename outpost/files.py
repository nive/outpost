
import logging
import time
import os

from pyramid.config import Configurator
from pyramid.static import static_view
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response




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
        # set default mime type to text/html
        name = self.request.subpath[-1]
        if name.find(".")==-1 and settings.get("server.content_type"):
            file.headers["Content-Type"] = settings.get("server.content_type")
        
        # handle files based on extensions
        extensions = settings.get("filter.extensions")
        if not extensions:
            return file
        extensions = extensions.replace("  "," ").split(" ")
        name = self.request.subpath[-1]
        if name.find(".")==-1 and "<empty>" in extensions:
            return self.filter(file)
        for e in extensions:
            if name.endswith(e):
                # run filter
                return self.filter(file)
        return file
        

    def filter(self, file):
        """
        the only one right now
        """
        settings = self.request.registry.settings
        # load filter. 
        insertfile = settings.get("filter.inserthead")
        if not insertfile:
            return file
        with open(insertfile) as f:
            data = f.read()
        # process
        contents = file.body
        contents = contents.replace("</head>", data+"</head>")
        file.body = contents
        return file
        
