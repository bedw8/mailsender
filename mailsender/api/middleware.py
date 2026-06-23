from fastapi import status,HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from fastapi.responses import JSONResponse
import json
from mailsender.lib.errors import InvalidCredentials

class HTTPSSchemeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.headers.get("x-forwarded-proto", "").lower() == "https":
            request.scope["scheme"] = "https"
        return await call_next(request)


class AuthMissingTokenInvalidCredsError(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        resp = await call_next(request)

        if resp.status_code != 422:
            return resp

        body = b''
        async for c in resp.body_iterator:
            body += c

        rdict = json.loads(body)
        for err in rdict['detail']:
            if (err['type'] == 'missing') and (err['loc'] == ['query','token']):
                exc = InvalidCredentials()
                return JSONResponse(content=dict(detail=str(exc)),
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        )

        return JSONResponse(content=rdict,status_code=resp.status_code)
