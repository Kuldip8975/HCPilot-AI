"""Rate limiting configuration (slowapi).

This file only defines the `limiter` instance. It's wired into the app in
main.py:

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

`default_limits` applies to EVERY route automatically once SlowAPIMiddleware
is installed - a route only needs its own `@limiter.limit(...)` decorator
when it needs something stricter than the default. We use that on
/auth/login and /auth/register specifically, since those are the routes an
attacker would hammer to brute-force a password or spam fake signups.

Production note: this uses slowapi's default in-memory storage, which is
per-process. That's fine for a single backend instance (e.g. one AWS
ECS/EC2 task). If this is ever scaled to multiple instances behind a load
balancer, each instance would enforce its OWN separate limit instead of one
shared limit across all of them - at that point this needs a shared
backend (Redis) instead. Not fixed here since it doesn't matter until you
actually run more than one instance.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_API],
)
