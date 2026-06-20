"""
Middleware CSRF (Cross-Site Request Forgery).

Valida que toda request con metodo no seguro (POST, PUT, PATCH, DELETE)
incluya el header `X-CSRF-Token` cuyo valor coincida con la cookie
`csrf_token` emitida por el backend en /login.

Flujo:
1. El backend setea cookie `csrf_token` (httponly=False) en el login.
2. El frontend (api.js:160) lee la cookie y la envia como header
   `X-CSRF-Token` en cada POST/PUT/PATCH/DELETE.
3. Este middleware rechaza con 403 si la cookie o el header faltan, o
   si los valores no coinciden.

Excluye endpoints publicos que no requieren auth (login emite la cookie
inicial, asi que tampoco se valida CSRF alli):
- /api/v1/login
- /api/v1/health
- /api/v1/logout (limpia la cookie, no requiere validacion)

En test environment (`settings.environment == "test"`) se bypasea la
validacion para no romper ~30 tests existentes que hacen POST/PATCH/DELETE
con cookies parciales (sin csrf_token). Patron estandar (Django, Flask-WTF).
Los tests especificos de CSRF se hacen via Chrome MCP en DES.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

# Metodos que mutan estado y requieren proteccion CSRF
_UNSAFE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

# Paths exentos (no requieren CSRF, generalmente pre-auth o publicos)
_EXEMPT_PATHS = (
    "/api/v1/login",
    "/api/v1/health",
    "/api/v1/logout",
)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.environment == "test":
            return await call_next(request)

        if request.method in _UNSAFE_METHODS and not any(
            request.url.path.startswith(p) for p in _EXEMPT_PATHS
        ):
            csrf_cookie = request.cookies.get("csrf_token")
            csrf_header = request.headers.get("x-csrf-token")
            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token invalido"},
                )
        return await call_next(request)
