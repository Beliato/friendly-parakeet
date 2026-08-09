from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.routers import auth

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Julia en Camino API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# Handler genérico para no filtrar stack traces al cliente.
# Nota: los exception_handlers de FastAPI pueden bypassear el CORSMiddleware,
# por eso añadimos manualmente el header Access-Control-Allow-Origin aquí.
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging

    logging.getLogger("julia").error(f"Unhandled error: {exc}", exc_info=True)
    origin = request.headers.get("origin", "")
    headers: dict[str, str] = {}
    if origin in settings.cors_origins_list:
        headers["access-control-allow-origin"] = origin
        headers["access-control-allow-credentials"] = "true"
        headers["vary"] = "Origin"
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
        headers=headers,
    )


app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
