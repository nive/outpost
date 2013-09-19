
import logging
import requests
import time
import pdb
import re

from pyramid.response import Response




class Proxy(object):

    def __init__(self, url, request):
        self.request = request
        self.url = url

    def response(self):
        log = logging.getLogger("proxy")
        settings = self.request.registry.settings
        params = dict(self.request.params)
        url = self.url.destUrl
        
        # prepare headers
        headers = {}
        for h,v in self.request.headers.environ.items():
            if h.startswith("SERVER_") or h.startswith("wsgi") or h.startswith("bfg") or h.startswith("webob"):
                continue
            if h.startswith("HTTP_"):
                headers[h[5:]] = v
            else:
                headers[h] = v
        headers["HOST"] = self.url.domainname
        headers["INFO"] = self.url.path

        kwargs = {"headers": headers, "cookies": self.request.cookies}
        if self.request.method.lower() == "get":
            kwargs["params"] = params
        else:
            kwargs["data"] = request.body

        # trace in debugger
        method = self.request.method.lower()
        url = self.url.destUrl
        headers = kwargs
        if settings.get("proxy.trace") and re.search(settings["proxy.trace"], self.url.destUrl):
            pdb.set_trace()
        response = requests.request(method, url, **headers) #=> Ready to proxy the current request. Step once (n) to get the response.
        # status codes 200 - 299 are considered as success
        if response.status_code >= 200 and response.status_code < 300:
            body = self.url.rewriteUrls(response.content)
            size = len(body)+len(str(response.raw.headers))
            log.info(self.url.destUrl+" => Status: %s, %d bytes in %d ms" % (response.status_code, 
                                                                             size, 
                                                                             response.elapsed.microseconds/1000)) 
        else:
            body = response.content
            log.info(self.url.destUrl+" => Status: %s %s, in %d ms" % (response.status_code, 
                                                                       response.reason, 
                                                                       response.elapsed.microseconds/1000)) 

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
            host = self.request.host.split(":")[0]
            cookie = cookie.replace(str(self.url.domainname), host)
            headers['set-cookie'] = cookie
            
        proxy_response = Response(body=body, status=response.status_code)
        proxy_response.headers.update(headers)
        return proxy_response



class ProxyUrlHandler(object):
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
    
    def __init__(self, urlparts):
        self.parts = urlparts     # urlparts is the source url in list form 
        self.prefix = self.defaultPrefix
        if not urlparts[0] in ("http","https"):
            self.protocol = self.defaultProtocol
            self.domainname = urlparts[0]
            self.path = "/".join(urlparts[1:])
        else:
            self.protocol = urlparts[0]
            self.domainname = urlparts[1]
            self.path = "/".join(urlparts[2:])
    
    def __str__(self):
        return self.destUrl
    
    @property
    def destUrl(self):
        return "%s://%s/%s" % (self.protocol, self.domainname, self.path)

    @property
    def srcUrl(self):
        return "/%s/%s/%s" % (self.protocol, self.domainname, self.path)

    @property
    def destDomain(self):
        return "%s://%s" % (self.protocol, self.domainname)

    @property
    def srcDomain(self):
        return "/%s/%s" % (self.protocol, self.domainname)
    
    def rewriteUrls(self, body):
        return body.replace(self.destDomain, self.prefix+self.srcDomain)
        

