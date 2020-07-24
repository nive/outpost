
Outpost 
=======

**Application level proxy server**

Outpost combines proxy, static file serving and application
framework functionality in a single server application.

Advanced options include request debugging and stream filter.

Implemented in pure python; with the pyramid web framework.

Please refer to Github for source codes: https://github.com/nive/outpost

Features
--------

- Serves static files from a directory
- Routes webservice requests through the proxy
- Session and cookie support for proxied requests
- Custom filter support
- Single and multiple concurrent connections
- Interactive request hacking and tracing
- Easy installation, runs on any os


Configuration - Basic setup
---------------------------

All configuration options are set in `server.ini` in projects' home folder.

The directory to be served. Either a python module asset path, relative path 
or absolute path ::

    server.directory = /home/me/myfiles
    server.defaultfile = index.html

The domain to connect to. Ajax calls and urls can use a domain
placeholder to be inserted by outpost before proxying the request.
By default the placeholder is '__domain'. The string will
replaced with the following configuration setting. ::

    proxy.domain = mydomain.nive.io

The url prefix used to route request through the proxy. By default
urls starting with `http://127.0.0.1:5556/__proxy/` will be handled by the 
proxy ::
  
    proxy.route = __proxy


Installation
------------

Short installation description:

- Install Python 
- Install Python setuptools and virtualenv
- Create a virtual environment (virtualenv) directory named ‘outpost’ (or use your projects name)
  ``virtualenv outpost``
- Install outpost from pypi.python.org ``bin/pip install outpost``
- Create a new project by using the scaffold ``bin/pcreate -t outpost myApp``
- change into myApp directory ``cd myApp``
- Start the web server ``../bin/pserve server.ini`` (the served directory path is relative)

If you are using a relative directory please make sure you start the webserver from the right
working directory.


Debug Toolbar
-------------

You can also use the pyramid debug toolbar to get a request log in the browser. 
To enable the toolbar open the ini file and set ``debugtoolbar.enabled = true``


Setting a breakpoint
--------------------

Change the line in your ini file to match proxied urls you would like to halt and inspect. ::

    proxy.trace = signin

Each proxied url containing `signin` will be interrupted and can be inspected in the python debugger
on the commandline. 

Basic commands (Take a look at python debugger for all commands):

- n : next step
- c : continue execution

Once you are in the debugger you can print the current requests values and change them (e.g. headers):

- method : http method
- url : the url to send the request to
- **parameter : a dictionary including headers and form values

after receiving the response

- response
- response.headers