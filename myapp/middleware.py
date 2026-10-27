"""Request logging middleware for DevHelp AI.

Logs:
- HTTP method, path, status code, response time in ms
- Server-side unhandled exceptions
Strictly omits passwords, API keys, authorization tokens, or sensitive personal data.
"""

import logging
import time

logger = logging.getLogger('devhelp.requests')


class RequestLoggingMiddleware:
    """Middleware to measure and log HTTP request metrics and server errors safely."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Do not log static asset noise in detail
        if not request.path.startswith('/static/'):
            status = getattr(response, 'status_code', 500)
            logger.info(
                f"[HTTP] {request.method} {request.path} -> {status} ({duration_ms}ms)"
            )

        return response

    def process_exception(self, request, exception):
        """Log server-side unhandled exceptions with safe context."""
        logger.error(
            f"[EXCEPTION] {request.method} {request.path} raised {type(exception).__name__}: {exception}",
            exc_info=False
        )
        return None
