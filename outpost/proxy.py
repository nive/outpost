# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import logging
import requests
import pdb
import re

from zope.interface import alsoProvides
from pyramid.response import Response

from outpost import filtermanager

__session_cache__ = None


# delegate views to the proxy server
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



class Proxy(object):
    """
    The Proxy class handles all requests forwarded to an external server.
    The url must be an instance of a UrlHandler class.

    It is currently only meant to connect to a single backend server and
    supports keep-alives and cookie sessions.

    The proxy reads the backend servers response completely into memory.
    Streaming is currently not supported.
    """
    
    def __init__(self, url, request, debug):
        self.request = request
        self.url = url
        self.debug = debug

    def response(self):
        log = logging.getLogger("outpost.proxy")
        request = self.request
        settings = request.registry.settings

        #path = settings.get("server.default_path")
        #if path and self.url.path=="/":
        #    self.url.path = path

        # run pre proxy request hooked filters
        # if the filter returns a response and not None. The response is returned
        # immediately
        try:
            response = filtermanager.runPreHook(filtermanager.EmptyProxyResponse(), request, self.url)
        except filtermanager.ResponseFinished, e:
            return e.response

        if response is None:
            url = self.url.destUrl

            # prepare headers
            headers = {}
            for h,v in request.headers.environ.items():
                h = h.lower()
                if h.startswith(("server_", "wsgi", "bfg", "webob", "outpost")):
                    continue
                if h.startswith("http_"):
                    headers[h[5:]] = v
                elif h.find("_")!=-1:
                    headers[h.replace("_", "-")] = v
                else:
                    headers[h] = v

            headers["host"] = self.url.host
            headers["info"] = self.url.path
            if "content-length" in headers:
                del headers["content-length"]

            params = dict(request.params)
            parameter = {"headers": headers, "cookies": request.cookies, "timeout": float(settings.get("proxy.timeout"))}
            if request.method.lower() == "get":
                parameter["params"] = params
            else:
                parameter["data"] = request.body

            # request session cache on module level, supports keep-alive connections
            usesession = settings.get("proxy.session", True)
            if usesession:
                global __session_cache__
                if not __session_cache__:
                    __session_cache__ = requests.Session()
                    if settings.get("proxy.retry"):
                        adapter = requests.adapters.HTTPAdapter(max_retries=int(settings.get("proxy.retry")),pool_connections=20,pool_maxsize=30)
                        __session_cache__.mount("http://", adapter)
                session = __session_cache__
            else:
                session = requests

            # trace in debugger
            method = request.method
            if self.debug and settings.get("proxy.trace") and re.search(settings["proxy.trace"], url):
                pdb.set_trace()
            try:
                response = session.request(method, url, **parameter) #=> Ready to proxy the current request. Step once (n) to get the response. (c) to continue. (Python debugger)
                body = response.content
                # status codes 200 - 299 are considered as success
                if 200 <= response.status_code < 300:
                    size = response.raw.tell()
                    log.debug("%s %s, %d bytes in %d ms %s" % (method, response.status_code, size,
                                                               response.elapsed.microseconds/1000, self.url.destUrl))
                else:
                    log.debug("%s: %s %s, in %d ms %s" % (method, response.status_code, response.reason,
                                                          response.elapsed.microseconds/1000, self.url.destUrl))
            except Exception, e:
                #todo excp types
                log.debug("%s %s" % (str(e), self.url.destUrl))
                response = Response(body=str(e), status=500)
                body = response.body

        else:
            # pre hook returned response
            body = response.body

        headers = dict(response.headers)
        if 'content-length' in headers:
            del headers['content-length']
        if 'transfer-encoding' in headers:
            del headers['transfer-encoding']
        if 'content-encoding' in headers:
            del headers['content-encoding']
        if 'connection' in headers:
            del headers['connection']
        if 'keep-alive' in headers:
            del headers['keep-alive']
        
        # cookies
        if 'set-cookie' in headers:
            cookie = headers['set-cookie']
            host = request.host.split(":")[0]
            cookie = cookie.replace(str(self.url.host), host)
            headers['set-cookie'] = cookie
            
        proxy_response = Response(body=body, status=response.status_code)
        proxy_response.headers.update(headers)
        alsoProvides(proxy_response, filtermanager.IProxyRequest)

        # run post proxy request hooked filters
        proxy_response = filtermanager.runPostHook(proxy_response, request, self.url)

        return proxy_response




class ProxyUrlHandler(object):
    """
    Handles proxied urls and converts them between source and destination.
    
    e.g. the incoming Request/URL ::

        http://localhost:5556/datastore/api/keys
  
    will be translated to the destination url ::
  
        http://test.nive.io/datastore/api/keys

    'http://test.nive.io' is looked up in the settings dict as `proxy.host`.
    
    Also urls in response bodies can be converted back to the source url.
    
    Attributes:
    - protocol: http or https
    - host: without protocol, including port
    - path: path without protocol and domain
    - destUrl: valid proxy destination url
    - destDomain: valid proxy destination domain
    - srcUrl: embedded proxy url
    - srcDomain: embedded proxy domain
    
    Methods:
    - rewriteUrls()
    
    """
    def __init__(self, request, settings):
        self.host = settings.get("proxy.host")
        self.protocol = settings.get("proxy.protocol") or "http"
        self.path = request.path_info     # path without host and query string
        self.qs = request.query_string
        if not self.path.startswith("/"):
            self.path = "/"+self.path

    def __str__(self):
        return self.destUrl
    
    @property
    def fullPath(self):
        if self.qs:
            return "%s://%s%s?%s" % (self.protocol, self.host, self.path, self.qs)
        return "%s://%s%s" % (self.protocol, self.host, self.path)

    @property
    def destUrl(self):
        return "%s://%s%s" % (self.protocol, self.host, self.path)

    @property
    def srcUrl(self):
        return self.path

    @property
    def destDomain(self):
        return "%s://%s" % (self.protocol, self.host)

    @property
    def srcDomain(self):
        return ""
    
    def rewriteUrls(self, body):
        return body.replace(self.destDomain, self.srcDomain)


class VirtualPathProxyUrlHandler(object):
    """
    Handles proxied urls and converts them between source and destination.

    e.g. the incoming Request/URL ::

      http://localhost:5556/___proxy/http/test.nive.co/datastore/api/keys

    will be translated to the destination url ::

      http://test.nive.co/datastore/api/keys

    Also urls in response bodies can be converted back to the source url.

    Attributes:
    - protocol: http or https
    - domainname: without protocol, including port
    - path: path without protocol and domain
    - destUrl: valid proxy destination url
    - destDomain: valid proxy destination domain
    - srcUrl: embedded proxy url
    - srcDomain: embedded proxy domain

    Methods:
    - rewriteUrls()

    """
    defaultProtocol = "http"
    defaultPrefix = "/__proxy/"

    def __init__(self, request, settings):
        urlparts = request.matchdict["subpath"]     # urlparts is the source url in list form
        host = settings.get("proxy.host")
        placeholder = settings.get("proxy.domainplaceholder","__domain")
        self.qs = request.query_string
        # bw 0.2.6
        if host is None:
            host = settings.get("proxy.domain")

        self.prefix = self.defaultPrefix
        if not urlparts[0] in ("http","https"):
            self.protocol = self.defaultProtocol
            self.host = urlparts[0]
            self.path = "/".join(urlparts[1:])
        else:
            self.protocol = urlparts[0]
            self.host = urlparts[1]
            self.path = "/".join(urlparts[2:])
        if placeholder and host:
            if self.host == placeholder:
                self.host = host

    def __str__(self):
        return self.destUrl

    @property
    def fullPath(self):
        if self.qs:
            return "%s://%s%s?%s" % (self.protocol, self.host, self.path, self.qs)
        return "%s://%s%s" % (self.protocol, self.host, self.path)

    @property
    def destUrl(self):
        return "%s://%s/%s" % (self.protocol, self.host, self.path)

    @property
    def srcUrl(self):
        return "/%s/%s/%s" % (self.protocol, self.host, self.path)

    @property
    def destDomain(self):
        return "%s://%s" % (self.protocol, self.host)

    @property
    def srcDomain(self):
        return "/%s/%s" % (self.protocol, self.host)

    def rewriteUrls(self, body):
        return body.replace(self.destDomain.encode("utf-8"), ("/__proxy"+self.srcDomain).encode("utf-8"))


