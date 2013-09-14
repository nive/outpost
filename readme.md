
# Outpost - anti cors local html application/webservice development server 

Includes a static file web server with integrated proxy based on
url prefixes and debugging tools. 

Use for local html application development with online webservice 
connection. To prevent browsers Cross Origin Resource Scripting
all requests are routed through a single address.

Implemented in pure python; with the web framework pyramid.

## Features

- Serves static files from a directory
- Routes webservice requests through the proxy
- Insert html snippets in served files
- Several logging and debugging tools
- Easy installation, runs on any os

## Configuration 

See server.ini

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

This is a alpha release several options are still missing. 
