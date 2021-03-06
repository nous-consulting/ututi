"""Pylons middleware initialization"""
import sys
from beaker.middleware import CacheMiddleware, SessionMiddleware
from paste.cascade import Cascade
from paste.registry import RegistryManager
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool
from pylons.middleware import ErrorHandler, StatusCodeRedirect
from pylons.wsgiapp import PylonsApp
from routes.middleware import RoutesMiddleware

from ututi.model import setup_tables
from ututi.model import meta, setup_orm
from ututi.config.environment import load_environment


def make_app(global_conf, full_stack=True, static_files=True, **app_conf):
    """Create a Pylons WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``full_stack``
        Whether this application provides a full WSGI stack (by default,
        meaning it handles its own exceptions and errors). Disable
        full_stack when this application is "managed" by another WSGI
        middleware.

    ``static_files``
        Whether this application serves its own static files; disable
        when another web server is responsible for serving them.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).

    """
    # Configure the Pylons environment
    config = load_environment(global_conf, app_conf)
    if not getattr(meta.metadata, 'set_up', False):
        setup_tables(meta.engine)
        setup_orm()
        meta.metadata.set_up = True

    # The Pylons WSGI app
    app = PylonsApp(config=config)

    # Routing/Session/Cache Middleware
    app = RoutesMiddleware(app, config['routes.map'])
    app = SessionMiddleware(app, config)
    app = CacheMiddleware(app, config)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

    if asbool(full_stack):

        # Display error documents for 401, 403, 404 status codes (and
        # 500 when debug is disabled)
        if asbool(config['debug']):
            # Handle Python exceptions
            app = ErrorHandler(app, global_conf, **config['pylons.errorware'])
            app = StatusCodeRedirect(app)
        else:
            from raven.contrib.pylons import Sentry
            if config.get('sentry.dsn'):
                app = Sentry(app, config)
            else:
                app = ErrorHandler(app, global_conf, **config['pylons.errorware'])
            app = StatusCodeRedirect(app, [400, 401, 403, 404, 500])

    # Establish the Registry for this application
    app = RegistryManager(app)

    if asbool(static_files):
        # Serve static files
        kwargs = {}
        if not asbool(config['debug']):
            kwargs['cache_max_age'] = 3600
        static_app = StaticURLParser(config['pylons.paths']['static_files'],
                                     **kwargs)
        app = Cascade([static_app, app])

    app.config = config
    return app
