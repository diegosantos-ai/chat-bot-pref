"""Shared application extensions and singletons.

Place shared objects here to avoid circular imports when routers need
access to the same Limiter instance used by the app.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


# Default limiter used across the app
# Keep headers disabled to avoid requiring every endpoint to accept a
# `response: Response` parameter (slowapi injects headers via the
# response object when present). Enabling headers without ensuring every
# endpoint exposes a Response leads to runtime exceptions.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"],
    headers_enabled=False,
    storage_uri="memory://",
)

# A separate limiter for webhook endpoints (higher limits). Individual
# endpoints may override default_limits via the decorator.
webhook_limiter = Limiter(
    key_func=get_remote_address,
    # Disable headers here as well to avoid runtime exceptions coming from
    # slowapi when endpoints don't expose a `response: Response` parameter.
    # We can re-enable headers after a coordinated change that ensures all
    # decorated endpoints accept the Response object.
    headers_enabled=False,
    storage_uri="memory://",
)
