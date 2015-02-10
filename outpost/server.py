# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import logging
import os
import json

from pyramid.config import Configurator

from outpost.proxy import Proxy, ProxyUrlHandler, VirtualPathProxyUrlHandler
from outpost.files import FileServer
from outpost import filtermanager

# delegate views to the file server and proxy server
 
def callProxy(request):
    settings = request.registry.settings
    route = settings.get("proxy.route")
    # todo pluggable url handlers
    if route=="__proxy":
        url = VirtualPathProxyUrlHandler(request, settings)
    else:
        url = ProxyUrlHandler(request, settings)
    proxy = Proxy(url, request, debug=settings.get("debug"))
    return proxy.response()

def serveFile(context, request):
    server = FileServer(request.matchdict["subpath"], context, request, debug=settings.get("debug"))
    return server.response()


# Main server function

def main(global_config, **settings):
    log = logging.getLogger()

    fileroute=proxyroute = None
    debug = settings.get("debug")

    # parse filter
    fstr = settings.get("filter")
    settings["filter"] = filtermanager.parseJsonString(fstr, exitOnTestFailure=not debug)

    # set up local file directory
    directory = settings.get("files.directory")
    # bw 0.2.6 renamed ini file setting
    if directory is None:
        directory = settings.get("server.directory")
    if not directory:
        log.info("Local directory path empty ('files.directory'). File serving disabled.")
    else:
        # extend relative directory
        wd = os.getcwd()+os.sep
        if directory.startswith("."+os.sep):
            directory = wd + directory[2:]
        elif directory.find(":") == -1 and not directory.startswith(os.sep):
            directory = wd + directory
        settings["files.directory"] = directory
        
        fileroute = settings.get("files.route", "")
        if not fileroute.startswith("/"):
            fileroute = "/"+fileroute
        if not fileroute.endswith("/"):
            fileroute += "/"
            
        log.info("Serving files from directory: " + directory)
        log.info("Serving files with path prefix: " + fileroute)
    
    # set up proxy routing
    host = settings.get("proxy.host")
    # bw 0.2.6 renamed ini file setting
    if host is None:
        host = settings.get("proxy.domain")
    if not host:
        log.info("Proxy target host empty ('proxy.host'). Request proxy disabled.")
    else:
        proxyroute = settings.get("proxy.route")
        if proxyroute:
            if not proxyroute.startswith("/"):
                proxyroute = "/"+proxyroute
            if not proxyroute.endswith("/"):
                proxyroute += "/"
        log.info("Proxying requests with path prefix '%s' to '%s'", proxyroute, host)

    if directory and fileroute==proxyroute:
        raise filtermanager.ConfigurationError("File and proxy routing is equal.")
    
    # setup pyramid configuration and routes
    config = Configurator(settings = settings)

    if proxyroute:
        # handle all /proxy/... urls by the proxy server
        config.add_route("proxy", proxyroute+"*subpath")
        config.add_view(callProxy, route_name="proxy", http_cache=0)

    # map the directory and disable caching
    if directory:
        config.add_route("files", fileroute+"*subpath")
        config.add_view(serveFile, route_name="files")

    config.commit()

    logger = logging.getLogger("requests.packages.urllib3.connectionpool")
    logger.level = "error"

    # creates the static server
    return config.make_wsgi_app()


