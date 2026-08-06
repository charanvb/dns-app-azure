"""Redirects any unauthenticated request to /login, except public paths."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

PUBLIC_PATHS = {"/login", "/api/health", "/api/docs", "/api/redoc", "/api/openapi.json"}
PUBLIC_PREFIXES = ("/static",)


class LoginRequiredMiddleware(BaseHTTPMiddleware):
    """Gatekeeper for the whole app while local auth is in place (pre-SSO)."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)
        if request.session.get("user_id") is None:
            return RedirectResponse(url="/login", status_code=303)
        return await call_next(request)
