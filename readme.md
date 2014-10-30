
# Outpost 

### local-javascript-application development server 

Outpost is a file server with integrated proxy, filter options and 
debugging tools. 

It is meant to be used for local javascript application development 
in combination with remote web api services. The build in proxy
prevents browsers `Cross Origin Resource Scripting` restrictions
by routing all requests through a single (local) address.

Advanced options include request debugging and stream filter.

Implemented in pure python; with the pyramid web framework.

Please refer to Github for source codes: https://github.com/nive/outpost

## Features

- Serves static files from a directory
- Routes webservice requests through the proxy
- Insert html snippets in served files
- Interactive request hacking and tracing
- Several logging and debugging tools
- Filter support
- Easy installation, runs on any os


## Configuration - Basic setup

All configuration options are set in `server.ini` in projects' home folder.

The directory to be served. Either a python module asset path, relative path 
or absolute path 

    server.directory = /home/me/myfiles
    server.defaultfile = index.html

The domain to connect to. Ajax calls and urls can use a domain
placeholder to be inserted by outpost before proxying the request.
By default the placeholder is '__domain'. The string will
replaced with the following configuration setting.

    proxy.domain = mydomain.nive.io

The url prefix used to route request through the proxy. By default
urls starting with `http://127.0.0.1:5556/__proxy/` will be handled by the 
proxy
  
    proxy.route = __proxy


## Installation

Short installation description:

- Install Python 
- Install Python setuptools and virtualenv
- Create a virtual environment (virtualenv) directory named ‘outpost’ (or use your projects name)
  ``virtualenv outpost``
- Install outpost from pypi.python.org ``bin/pip install outpost``
- Create a new project by using the scaffold ``bin/pcreate -t default myApp``
- Start the web server ``bin/pserve myApp/server.ini`` 

If you are using a relative directory please make sure you start the webserver from the right
working directory.

## Release

This is a beta release, though stable. And it is not meant to run as production server.
