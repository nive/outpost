# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import logging
import os

from pyramid.config import Configurator

from outpost import filtermanager
from outpost.proxy import callProxy
from outpost.files import serveFile


def setup(global_config, **settings):
    """
    Parse ini file settings, setup defaults and register views

    :param global_config:
    :param settings:
    :return: returns pyramid configurator
    """
    log = logging.getLogger("outpost")

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

        log.info("Serving files with path prefix '%s' from directory '%s'" % (fileroute, directory))

    # normalize default path
    path = settings.get("server.default_path", "")
    if path and not path.startswith("/"):
        settings["server.default_path"] = "/"+path

    # set up proxy routing
    host = settings.get("proxy.host")
    # bw 0.2.6 renamed ini file setting
    if host is None:
        host = settings.get("proxy.domain")
    if not host:
        log.info("Proxy target host empty ('proxy.host'). Request proxy disabled.")
    else:
        proxyroute = settings.get("proxy.route")
        if not proxyroute.startswith("/"):
            proxyroute = "/"+proxyroute
        if not proxyroute.endswith("/"):
            proxyroute += "/"
        log.info("Proxying requests with path prefix '%s' to '%s'", proxyroute, host)

    if directory and fileroute==proxyroute:
        raise filtermanager.ConfigurationError("File and proxy routing is equal.")

    # setup pyramid configuration and routes
    config = Configurator(settings = settings)

    # route proxy requests
    def regproxy(route):
        # handle all /proxy/... urls by the proxy server
        config.add_route("proxy", route+"*subpath")
        config.add_view(callProxy, route_name="proxy")

    # route the local directory
    def regfile(route):
        config.add_route("files", route+"*subpath")
        config.add_view(serveFile, route_name="files")

    # swap order of route registration to handle fallbacks
    fallback = settings.get("server.fallback")

    if proxyroute and fallback!="proxy":
        regproxy(proxyroute)

    if directory:
        regfile(fileroute)

    if proxyroute and fallback=="proxy":
        regproxy(proxyroute)

    config.commit()

    return config




# Main server function
def main(global_config, **settings):
    # setup outpost
    config = setup(global_config, **settings)
    logger = logging.getLogger("requests.packages.urllib3.connectionpool")
    logger.level = "error"
    # creates the static server
    return config.make_wsgi_app()


