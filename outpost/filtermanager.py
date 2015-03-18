# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import logging
import json
import re
from zope.interface import Interface, implements
from pyramid.path import DottedNameResolver
from pyramid.path import caller_package


class IFilter(Interface):
    """
    IFilter marks filter configuration classes
    """

class IFileRequest(Interface):
    """
    IFileRequest is used to mark file responses and can be used in filters to
    differentiate between file and proxy requests.

       IFileRequest.providedBy(response)

    """
class IProxyRequest(Interface):
    """
    IProxyRequest is used to mark proxy responses and can be used in filters to
    differentiate between file and proxy requests.

       IProxyRequest.providedBy(response)

    """


class FilterConf(object):
    """
    Filter configuration class

    callable: points to the callable of the filter. A function, dotted path spec or class.
    hook: hook the filter before (pre) or after (post) triggering the proxy or file server.
    apply_to: defines the reponse type to apply the filter to: `file`, `proxy`. `None` for both.
    mime: applies the filter only if the mime type of the response matches
    path: applies the filter only if the pyth of the request matches
    settings: individual filter settings
    name: readable name, just used in logging

    Example ::

        def runfilter(response, request, settings):
            text = settings["insert text"]
            # process headers
            response.headers.update({"X-MyHeader": text})
            # alter body
            response.body = response.body.replace("</body>", "<div>%s</div></body>"%text)
            return response

        htmlfilter = FilterConf(
            callable = runfilter,
            apply_to = "proxy",
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "HTML filter example"
        )
    """
    implements(IFilter)

    callable=None
    hook="post"
    content_type=None
    path=None
    apply_to=None
    settings=None
    name=""

    @staticmethod
    def fromDict(conf):
        """
        Creates a filter configuration class from a dictionary
        """
        fc = FilterConf()
        fc.__dict__.update(conf)
        # replace strings with interfaces
        if fc.apply_to:
            if fc.apply_to=="file":
                fc.apply_to = IFileRequest
            elif fc.apply_to=="proxy":
                fc.apply_to = IProxyRequest
            else:
                # invalid value -> remove
                fc.apply_to = None
        # resolve callable if it is a string
        if fc.callable and isinstance(fc.callable, basestring):
            base = caller_package()
            cc = DottedNameResolver(base).resolve(fc.callable)
            fc.callable = cc
        # compile path and content_type regex if set
        if fc.path:
            fc.path = re.compile(fc.path)
        if fc.content_type:
            fc.content_type = re.compile(fc.content_type)
        return fc

    def __str__(self):
        return self.name or repr(self.callable)

    def test(self):
        """
        Tests configuration settings.
        Returns a empty list on success. Otherwise a list of failures.
        """
        result = []
        if not callable(self.callable):
            result.append("Filter callable is *not* a callable! %s"% (repr(self.callable)))
        if not self.hook in ("post","pre"):
            result.append("hook must be set to 'post' or 'pre'! %s"% (str(self.hook)))
        return result


def runPreHook(response, request, url):
    """
    Lookup and apply filters for response/request

    :param response:
    :param request:
    :param url:
    :return: response
    """
    log = logging.getLogger("outpost.filter")
    matched = lookupFilter("pre", response, request, url)
    for ff in matched:
        log.debug("run pre %s: %s" % (ff.name or str(ff.callable), str(url)))
        response = applyFilter(ff, response, request, url)
    return response


def runPostHook(response, request, url):
    """
    Lookup and apply filters for response/request

    :param response:
    :param request:
    :param url:
    :return: response
    """
    log = logging.getLogger("outpost.filter")
    matched = lookupFilter("post", response, request, url)
    for ff in matched:
        log.debug("run post %s: %s" % (ff.name or str(ff.callable), str(url)))
        response = applyFilter(ff, response, request, url)
    return response


def lookupFilter(hook, response, request, url):
    """
    Lookup a list of filters matching the current request and response

    :param hook:
    :param request:
    :param response:
    :param url:
    :return: list of filters
    """
    all = request.registry.settings["filter"]
    matched = []
    for ff in all:
        # match response type
        if ff.hook != hook:
            continue
        # match response type
        if ff.apply_to:
            if not ff.apply_to.providedBy(response):
                continue
        # match path
        if ff.path:
            if not ff.path.search(str(url)):
                continue
        # match content type
        if ff.content_type:
            if not ff.content_type.search(response.content_type):
                continue
        matched.append(ff)
    return matched


def applyFilter(filter, response, request, url):
    """
    Applies a single filter returned by `lookupFilter`

    :param filter:
    :param request:
    :param response:
    :param url:
    :return: response
    """
    # load filter.
    response = filter.callable(response, request, filter.settings, url)
    return response


def parseJsonString(jsonstr, exitOnTestFailure=True):
    """
    Parse and test filter configuration from json string.

    Raises a ConfigurationError if exitOnTestFailure is true

    :param jsonstr:
    :param exitOnTestFailure:
    :return: list of parsed filter
    """
    log = logging.getLogger("outpost")
    if jsonstr is None:
        return ()
    jsonstr = jsonstr.strip()
    if not jsonstr:
        return ()
    ff = json.loads(jsonstr)
    if isinstance(ff, dict):
        ff = (FilterConf.fromDict(ff),)
    elif isinstance(ff, list):
        confs = []
        for a in ff:
            if isinstance(a, dict):
                confs.append(FilterConf.fromDict(a))
            else:
                confs.append(a)
        ff = tuple(confs)
    err = False
    ok = []
    for tf in ff:
        # log errors
        failures = tf.test()
        if failures:
            err = True
            log.error("filter test: "+str(tf))
            for f in failures:
                log.error(f)
        else:
            ok.append(tf)
            log.info("Loaded %s filter %s (%s) for %s"%(tf.hook, str(tf), repr(tf.callable),
                                                              tf.apply_to or ""))
    if exitOnTestFailure and err:
        raise ConfigurationError("Invalid filter configurations found. See error log for details.")
    return ok


class ConfigurationError(Exception):
    """
    """
