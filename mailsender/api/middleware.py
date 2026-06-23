from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest


class HTTPSSchemeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.headers.get("x-forwarded-proto", "").lower() == "https":
            request.scope["scheme"] = "https"
        return await call_next(request)


class AuthMissingTokenInvalidCredsError(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        resp = await call_next(request)
        if 'auth' in request.scope.get('path'):
            print( dir(resp))
            print( resp.info)

        return resp
