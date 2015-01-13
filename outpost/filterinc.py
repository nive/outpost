
import json
import os

from pyramid.renderers import render

# quick and dirty string replacements

def appendhead(file, settings, request=None):
    htmlfile = settings.get("filter.appendhead")
    if not htmlfile:
        return file
    try:
        with open(htmlfile) as f:
            data = f.read()
    except IOError:
        return file
    # process
    file.body = file.body.replace("</head>", data+"</head>")
    return file


def appendbody(file, settings, request=None):
    htmlfile = settings.get("filter.appendbody")
    if not htmlfile:
        return file
    try:
        with open(htmlfile) as f:
            data = f.read()
    except IOError:
        return file
    # process
    file.body = file.body.replace("</body>", data+"</body>")
    return file


def replacestr(file, settings, request=None):
    conf = settings.get("filter.replacestr")
    if not conf:
        return file
    conf = json.loads(conf)
    # process
    if not isinstance(conf, (list,tuple)):
        conf = (conf,)
    for repl in conf:
        codepage = repl.get("codepage", "utf-8") or "utf-8"
        file.body = file.body.replace(repl["str"].encode(codepage), repl["new"].encode(codepage))
    return file


def template(file, settings, request=None):
    tmpl = settings.get("filter.template")
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
        return file
    values = {"content": file.unicode_body, "file": file}
    file.unicode_body = render(tmpl, values, request=request)
    return file


# available filter sections ------------------------------------------------------------------------
FILTER = (
    ("filter.template", template),
    ("filter.appendhead", appendhead),
    ("filter.appendbody", appendbody), 
    ("filter.replacestr", replacestr)
)

