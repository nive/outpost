import binascii
import os

from pyramid.compat import native_

from pyramid.scaffolds import PyramidTemplate # API
from pyramid.scaffolds.template import Template

class DefaultTemplate(PyramidTemplate):
    _template_dir = 'default'
    summary = 'The default server setup'

    def pre(self, command, output_dir, vars):
        """ Overrides :meth:`pyramid.scaffold.template.Template.pre`, adding
        several variables to the default variables list (including
        ``random_string``, and ``package_logger``).  It also prevents common
        misnamings (such as naming a package "site" or naming a package
        logger "root".
        """
        # configuration
        
        vars['root'] = raw_input("Root directory for files (default './files'): ")
        if not vars['root']:
            vars['root'] = "files"

        vars['domain'] = raw_input("Rewrite proxy requests to the following domain e.g. 'mydomain.nive.io' (default empty): ")

        #vars['proxy'] = raw_input("Proxy url prefix (default '__proxy'): ")
        #if not vars['proxy']:
        #    vars['proxy'] = "__proxy"

        #vars['host'] = raw_input("Server host (default '127.0.0.1'): ")
        #if not vars['host']:
        #    vars['host'] = "127.0.0.1"

        #vars['port'] = raw_input("Server port (default 5556): ")
        #if not vars['port']:
        #    vars['port'] = "5556"

        return PyramidTemplate.pre(self, command, output_dir, vars)
    
