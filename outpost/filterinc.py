
import json

# quick and dirty string replacements

def appendhead(file, settings):
    htmlfile = settings.get("filter.appendhead")
    if not htmlfile:
        return file
    with open(htmlfile) as f:
        data = f.read()
    # process
    file.body = file.body.replace("</head>", data+"</head>")
    return file


def appendbody(file, settings):
    htmlfile = settings.get("filter.appendbody")
    if not htmlfile:
        return file
    with open(htmlfile) as f:
        data = f.read()
    # process
    file.body = file.body.replace("</body>", data+"</body>")
    return file


def replacestr(file, settings):
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


# available filter sections ------------------------------------------------------------------------
FILTER = (
    ("filter.appendhead", appendhead), 
    ("filter.appendbody", appendbody), 
    ("filter.replacestr", replacestr)
)

