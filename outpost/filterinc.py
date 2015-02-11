# Copyright 2015 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under BSD-license. See license.txt
#
import json
import os
import gzip

from StringIO import StringIO

from pyramid.renderers import render


def template(response, request, settings, url):
    """
    Templating filter
    -----------------
    Calls a template with the file or proxy response as the value.
    The template itself is loaded as a pyramid renderer baased on the template path.
    You can use any pyramid template engine as long as it is included by calling
    `config.include()` during startup.

    The template path can be an asset spec path e.g. `myproject:templates/tmpl.pt` or
    absolute path or a relative path starting with `./` or `../`.

    The template is called with `content` and `response` attributes in the templates
    namespace. Also the original request is passed as `request`.

    Settings ::

        template: the template path

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.template",
           "applyTo": "proxy",
           "content_type": "text/html",
           "path": "\.html",
           "settings": {"template": "../templates/main.pt"},
           "name": "HTML filter example"}
          ]

    """
    tmpl = settings.get("template")
    if not tmpl:
        return response
    # extend relative path
    wd = os.getcwd()+os.sep
    if tmpl.startswith("."+os.sep):
        tmpl = wd + tmpl[2:]
    elif tmpl.startswith(".."+os.sep):
        tmpl = wd + tmpl
        tmpl = os.path.normpath(tmpl)
    elif tmpl.find(":") == -1 and not tmpl.startswith(os.sep):
        tmpl = wd + tmpl
    if not tmpl:
        return response
    values = {"content": response.unicode_body, "response": response}
    response.unicode_body = render(tmpl, values, request=request)
    return response


def replacestr(response, request, settings, url):
    """
    Simple string replacer
    ----------------------
    Search and replace strings in the responses body.

    Settings

    replacestr: one or a list of strings to be replaced ::

        {"str": "old", "new": "new"}

    or ::

        [{"str": "old", "new": "new"}, {"str": "also", "new": "new"}]

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.replacestr",
           "applyTo": "file",
           "path": "\.html",
           "settings": {"str": "http://127.0.0.1/assets/", "new": "http://cdn.someserver.com/"},
           "name": "String replacer example"}
          ]

    """
    if not settings:
        return response
    # process
    if not isinstance(settings, (list,tuple)):
        settings = (settings,)
    for repl in settings:
        response.unicode_body = response.unicode_body.replace(repl["str"], repl["new"])
    return response


def rewrite_urls(response, request, settings, url):
    """
    Rewirite proxied urls
    ----------------------
    Search and replace urls based on proxy server host and backend host.

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.rewrite_urls",
           "applyTo": "proxy",
           "path": "\.html",
           "settings": {},
           "name": "rewrite_urls"}
          ]

    """
    if not url:
        return response
    # rewrite urls
    response.unicode_body = url.rewriteUrls(response.unicode_body)
    return response


def compress(response, request, settings, url):
    """
    Compress response body
    ----------------------
    Compress the resposne with gzip on the fly.

    Example ini file section ::

        filter = [
          {"callable": "outpost.filterinc.compress",
           "applyTo": "proxy",
           "content_type": "text/",
           "settings": {},
           "name": "compress"}
          ]

    """
    response.content_encoding = "gzip"
    response.accept_ranges = "bytes"
    response.content_length = len(response.body)
    # compress
    zipped = StringIO()
    gz = gzip.GzipFile(fileobj=zipped, mode="wb")
    gz.write(response.body)
    gz.close()

    zipped.seek(0)
    response.body = zipped.read()
    zipped.close()
    return response


# quick and dirty string filter callables

def appendhead(response, request, settings, url):
    htmlfile = settings.get("appendhead")
    if not htmlfile:
        return response
    try:
        with open(htmlfile) as f:
            data = f.read()
    except IOError:
        return response
    # process
    response.body = response.body.replace("</head>", data+"</head>")
    return response


def appendbody(response, request, settings, url):
    htmlfile = settings.get("appendbody")
    if not htmlfile:
        return response
    try:
        with open(htmlfile) as f:
            data = f.read()
    except IOError:
        return response
    # process
    response.body = response.body.replace("</body>", data+"</body>")
    return response


