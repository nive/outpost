
import logging
import requests
import os

from pyramid.config import Configurator
from pyramid.response import Response

from proxy import Proxy, UrlHandler



def callProxy(request):
    """
    proxy view function 
    """
    url = UrlHandler(request.matchdict["subpath"])
    proxy = Proxy(url, request)
    return proxy.response()


def main(global_config, **settings):
    # Static server main function
    log = logging.getLogger()

    # settings
    directory = settings.get("static.directory")
    if not directory:
        raise ConfigurationError, "The directory to be served is missing. Please make sure 'static.directory = <...>'" \
                                  " in the server.ini configuration file is set."
    proxyroute = settings.get("proxy.route")

    # extend relative directory
    wd = os.getcwd()+os.sep
    if directory.startswith("."+os.sep):
        directory = wd + directory[2:]
    elif directory.find(":") == -1 and not directory.startswith(os.sep):
        directory = wd + directory
        
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
        config.add_view(callProxy, route_name="proxy")

    # map the directory and disable caching
    config.add_static_view(name="", path=directory, cache_max_age=0)

    config.commit()
        
    return config.make_wsgi_app()
