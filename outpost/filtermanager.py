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
    content_type: applies the filter only if the mime type of the response matches
    path: applies the filter only if the pyth of the request matches
    environ: match a request.environ field
    sub_filter: name of filter. trigger the named filter filter only if this filter has been executed
    is_sub_filter: True/False. if True run only if a preious filter has set this filters' name as sub_filter
    settings: individual filter settings
    name: name, used to reference sub filter and in logging

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
            environ = {"name": page, "value": True},
            sub_filter = "maintmpl"
            is_sub = False
            content_type = "text/html",
            settings = {"insert text": "Filtered!"},
            name = "HTML filter example"
        )
    """
    implements(IFilter)

    callable=None
    hook="post"
    content_type=None
    environ=None
    sub_filter=None
    is_sub_filter=False
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
        if not self.hook in ("post","pre","all",""):
            result.append("hook must be set to 'all', 'post', 'pre'! %s"% (str(self.hook)))
        if self.environ:
            if not "name" in self.environ and not "value" in self.environ:
                result.append("environ must have 'name' and 'value' keys! %s"% (str(self.environ)))
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
    for ff in lookupFilter("pre", response, request, url):
        log.debug("pre %s: %s" % (ff.name or str(ff.callable), str(url)))
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
    for ff in lookupFilter("post", response, request, url):
        log.debug("post %s: %s" % (ff.name or str(ff.callable), str(url)))
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
    #matched = []
    for ff in all:
        # match sub filter
        if ff.is_sub_filter:
            if ff.name in request.environ.get("outpost.sub_filter", ()):
                #matched.append(ff)
                yield ff
            continue
        # match pre/post hook
        if ff.hook != hook:
            continue
        # match response type
        if ff.apply_to:
            if not ff.apply_to.providedBy(response):
                continue
        # match environ
        if ff.environ is not None and ff.environ.value != request.environ.get(ff.environ.name):
            continue
        # match path
        if ff.path:
            if not ff.path.search(str(url)):
                continue
        # match content type
        if ff.content_type:
            if not ff.content_type.search(response.content_type):
                continue
        yield ff
    #return matched


def applyFilter(filterconf, response, request, url):
    """
    Applies a single filter returned by `lookupFilter`

    :param filterconf:
    :param request:
    :param response:
    :param url:
    :return: response
    """
    # load filter.
    response = filterconf.callable(response, request, filterconf.settings, url)
    _trackFilter(filterconf, request)
    # activate subfilter
    _activateSubFilter(filterconf, request)
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
                                                              tf.apply_to or "all requests"))
    if exitOnTestFailure and err:
        raise ConfigurationError("Invalid filter configurations found. See error log for details.")
    return ok


def _trackFilter(ff, request):
    if not "outpost.filter" in request.environ:
        request.environ["outpost.filter"] = [ff.name or str(ff.callable)]
    elif not ff.sub_filter in request.environ["outpost.filter"]:
        request.environ["outpost.filter"].append(ff.name or str(ff.callable))

def _activateSubFilter(ff, request):
    if ff.sub_filter:
        if not "outpost.sub_filter" in request.environ:
            request.environ["outpost.sub_filter"] = [ff.sub_filter]
        elif not ff.sub_filter in request.environ["outpost.sub_filter"]:
            request.environ["outpost.sub_filter"].append(ff.sub_filter)



class ResponseFinished(Exception):
    """
    """
    def __init__(self, response):
        self.response = response


class ConfigurationError(Exception):
    """
    """
