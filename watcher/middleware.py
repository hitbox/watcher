import logging

logger = logging.getLogger("access")  # separate access logger

class PrefixMiddleware:
    """
    WSGI middleware to mount a Flask (or other WSGI) app under a URL prefix
    and log all HTTP requests (access logging).

    Rewrites PATH_INFO and SCRIPT_NAME so the app behaves as if it is served
    under the specified prefix. Requests that do not start with the prefix
    return a 404.

    Access logs include client IP, request method, full path (including query string),
    and user agent.

    Example usage:

        app = Flask(__name__)
        app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/myapp')

    Attributes:
        app: The WSGI application to wrap.
        prefix: The URL prefix under which the app will be mounted.
    """

    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix.rstrip('/')

    def __call__(self, environ, start_response):
        # Capture basic request info for logging
        remote_addr = environ.get('REMOTE_ADDR') or environ.get('REMOTE_HOST', '-')
        method = environ.get('REQUEST_METHOD', '-')
        path = environ.get('PATH_INFO', '-')
        query = environ.get('QUERY_STRING')
        if query:
            path = f"{path}?{query}"
        user_agent = environ.get('HTTP_USER_AGENT', '-')

        # Log every request
        logger.info('%s - %s "%s" "%s"', remote_addr, method, path, user_agent)

        # Check prefix
        normalized_path = environ['PATH_INFO'].rstrip('/')
        if normalized_path.lower().startswith(self.prefix.lower()):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):] or '/'
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            # Log prefix mismatch
            logger.warning(
                "Prefix mismatch: expected %r, got %r", self.prefix, environ['PATH_INFO']
            )
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found']
