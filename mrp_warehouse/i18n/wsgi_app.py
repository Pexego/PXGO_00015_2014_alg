# -*- coding: UTF-8 -*-

import os
import sys
import optparse

from os.path import join, dirname, exists

import cherrypy
from cherrypy._cpconfig import as_dict
from formencode import NestedVariables

sys.path.append('/usr/share/openerp-web')

from openerp import release

sys.stdout = sys.stderr

def nestedvars_tool():
    if hasattr(cherrypy.request, 'params'):
        cherrypy.request.params = NestedVariables.to_python(cherrypy.request.params or {})

cherrypy.tools.nestedvars = cherrypy.Tool("before_handler", nestedvars_tool)
cherrypy.lowercase_api = True


class CPSessionWrapper(object):

    def __setattr__(self, name, value):
        cherrypy.session[name] = value

    def __getattr__(self, name):
        return cherrypy.session.get(name)

    def __delattr__(self, name):
        if name in cherrypy.session:
            del cherrypy.session[name]

    __getitem__ = __getattr__
    __setitem__ = __setattr__

    def get(self, name, default=None):
        return cherrypy.session.get(name, default)

    def clear(self):
        cherrypy.session.clear()


class ConfigurationError(Exception):
    pass


def setup_server(configfile):

    if not exists(configfile):
        raise ConfigurationError(_("Could not find configuration file: %s") % configfile)


    cherrypy.config.update({
        'tools.sessions.on': True,
        'tools.nestedvars.on': True,
        'log.screen': False,
        'tools.sessions.storage_type': 'file',
        'tools.sessions.storage_path': '/var/lib/openerp-web/sessions',
    })

    app_config = as_dict(configfile)
    
    _global = app_config.pop('global', {})
    _environ = _global.setdefault('server.environment', 'development')
    
    if _environ != 'development':
        _global['environment'] = _environ
        
    cherrypy.config.update(_global)
    
    static_dir = '/usr/share/openerp-web/www'
    app_config.update({'/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': static_dir
    }})
    
    app_config.update({'/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': static_dir + "/images/favicon.ico"
    }})

    app_config.update({'/LICENSE.txt': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': static_dir + "/../../doc/LICENSE.txt"
    }})

    # import profiler while makes profile decorator available as __builtins__
    from openerp import profiler
    
    from openerp.controllers.root import Root
    app = cherrypy.tree.mount(Root(), '/', app_config)

    import pkg_resources
    from openerp.widgets import register_resource_directory

    register_resource_directory(app, "openerp", static_dir)

    # initialize the rpc session
    host = app.config['openerp'].get('host')
    port = app.config['openerp'].get('port')
    protocol = app.config['openerp'].get('protocol')

    from openerp import rpc
    rpc.initialize(host, port, protocol, storage=CPSessionWrapper())

    return app

application = setup_server('/etc/openerp-web/openerp-web.cfg')
