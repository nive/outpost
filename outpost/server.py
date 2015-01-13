
import logging
import os

from pyramid.config import Configurator

from proxy import Proxy, ProxyUrlHandler
from files import FileServer


# delegate views to the file server and proxy server
 
def callProxy(request):
    settings = request.registry.settings
    ph = settings.get("proxy.domainplaceholder","__domain")
    do = settings.get("proxy.domain")
    url = ProxyUrlHandler(request.matchdict["subpath"], domain=do, placeholder=ph)
    proxy = Proxy(url, request)
    return proxy.response()

def serveFile(context, request):
    server = FileServer(request.matchdict["subpath"], context, request)
    return server.response()


# Main server function

def main(global_config, **settings):
    log = logging.getLogger()

    # settings
    directory = settings.get("server.directory")
    if not directory:
        raise ConfigurationError("The directory to be served is missing. Please make sure 'server.directory = <...>'"
                                 " in the server.ini configuration file is set.")
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
        log.info("Proxy not activated. To activate please make sure 'proxy.route = <...>' in the server.ini"
                 " configuration file is set.")
    else:
        if not proxyroute.startswith("/"):
            proxyroute = "/"+proxyroute
        if not proxyroute.endswith("/"):
            proxyroute = proxyroute+"/"
        log.info("Proxying requests with prefix: " + proxyroute)
    
    config = Configurator(settings = settings)

    if proxyroute:
        # handle all /proxy/... urls by the proxy server
        config.add_route("proxy", proxyroute+"*subpath")
        config.add_view(callProxy, route_name="proxy", http_cache=0)

    # map the directory and disable caching
    config.add_route("files", "/*subpath")
    config.add_view(serveFile, route_name="files")

    config.commit()
        
    logger = logging.getLogger("requests.packages.urllib3.connectionpool")
    logger.level = "error"

    # creates the static server
    return config.make_wsgi_app()


class ConfigurationError(Exception):
    """
    """
