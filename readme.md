
# Outpost 

### anti-cors-local-html-application development server 

Provides a static file web server with integrated webservice proxy,
filter options and debugging tools. 

Use for local html application development with online webservice 
connection. To prevent browsers Cross Origin Resource Scripting
all requests are routed through a single address.

Static files can be run through filters before being send to the browser.

Implemented in pure python; with the pyramid web framework.

## Features

- Serves static files from a directory
- Routes webservice requests through the proxy
- Insert html snippets in served files
- Interactive request hacking and tracing
- Several logging and debugging tools
- Filter support
- Easy installation, runs on any os

## Configuration 

(See server.ini)

the directory to be served. Either a python module asset path, relative path 
or absolute path 

    server.directory = {{root}}
    server.defaultfile = index.html
    server.log_notfound = True
    server.content_type = text/html; charset=UTF-8

Activate interactive commandline request tracing in python debugger. 
Allows you to modify and pause requests before being returned to the browser.
Takes a regular expression as parameter, the server breaks only if the re matches.
e.g. \.html for html files.

    server.trace = 

filter configuration. filters are loaded based on file extensions. `empty` means 
files without extension are filtered, too.

    filter.extensions = .html <empty>

Points to a file and inserts the contents at the end of the html-head
section of the served file. e.g. `files/header.html` 

    filter.appendhead = 

Points to a file and inserts the contents at the end of the html-body
section of the served file. e.g. `files/body.html` 

    filter.appendbody = 

string replacement directive in json (can also be a list of directives):  
e.g. {"str": "old string", "new": "new string", "codepage": "utf-8"}

    filter.replacestr = 

The url prefix used to route request through the proxy. By default
urls starting with `http://127.0.0.1:5556/__proxy/` will be handled by the 
proxy
  
    proxy.route = __proxy

Activate interactive commandline request tracing in python debugger. 
Allows you to modify and pause calls to the webservice. Takes a regular
expression as parameter, the server breaks only if the re matches.
e.g. datastore/api/setItem.

    proxy.trace = 

## Installation

Short installation description:

- Install Python 
- Install Python setuptools and virtualenv
- Create a virtual environment (virtualenv) directory named ‘outpost’ (or use your projects name)
  ``virtualenv outpost``
- Install outpost from pypi.python.org ``bin/pip install outpost``
- Create a new project by using the scaffold ``bin/pcreate -t default myHtmlApp``
- Start the web server ``bin/pserve myHtmlApp/server.ini`` 

If you are using a relative directory please make sure you start the webserver from the right
working directory.

## Release

This is a alpha release, though stable. And it is not meant to run as production server.
