
import logging
import requests
import os

from pyramid.config import Configurator
from pyramid.response import Response

from proxy import Proxy, ProxyUrlHandler
from files import FileServer


def callProxy(request):
    """
    proxy view function 
    """
    url = ProxyUrlHandler(request.matchdict["subpath"])
    proxy = Proxy(url, request)
    return proxy.response()

def serveFile(context, request):
    """
    send back file 
    """
    server = FileServer(request.matchdict["subpath"], context, request)
    return server.response()


def main(global_config, **settings):
    # Static server main function
    log = logging.getLogger()

    # settings
    directory = settings.get("server.directory")
    if not directory:
        raise ConfigurationError, "The directory to be served is missing. Please make sure 'server.directory = <...>'" \
                                  " in the server.ini configuration file is set."
    proxyroute = settings.get("proxy.route")

    # extend relative directory
    wd = os.getcwd()+os.sep
    if directory.startswith("."+os.sep):
        directory = wd + directory[2:]
    elif directory.find(":") == -1 and not directory.startswith(os.sep):
        directory = wd + directory
    settings["server.directory"] = directory
        
    log.info("Serving files from directory: " + directory)
    if not proxyroute:
        log.info("Proxy not activated. To activate please make sure 'proxy.route = <...>' in the server.ini" \
                 " configuration file is set.")
    else:
        if not proxyroute.startswith("/"):
            proxyroute = "/"+proxyroute
        if not proxyroute.endswith("/"):
            proxyroute = proxyroute+"/"
        log.info("Proxying requests" \
                 " with prefix: " + proxyroute)
    
    # This function creates the static server.
    config = Configurator(settings = settings)

    if proxyroute:
        # handle all /proxy/... urls by the proxy server
        config.add_route("proxy", proxyroute+"*subpath")
        config.add_view(callProxy, route_name="proxy", http_cache=0)

    # map the directory and disable caching
    #config.add_static_view(name="", path=directory, cache_max_age=0)
    config.add_route("files", "/*subpath")
    config.add_view(serveFile, route_name="files")

    config.commit()
        
    logger = logging.getLogger("requests.packages.urllib3.connectionpool")
    logger.level = "error"

    return config.make_wsgi_app()
