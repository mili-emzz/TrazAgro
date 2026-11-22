from contextlib import asynccontextmanager
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.controllers.health import router as health_router
from backend.core.config import settings
from backend.core.database import db_manager
from backend.core.exceptions import TrazaAgroError
from backend.core.middleware import MaxBodySizeMiddleware, SecurityHeadersMiddleware

logger = logging.getLogger("trazaagro.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Inicializa y libera los pools/drivers de las tres bases de datos."""
    db_manager.connect()
    try:
        yield
    finally:
        db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API de trazabilidad integral políglota para la cadena de Aguacate Hass.",
    lifespan=lifespan,
)

app.add_middleware(MaxBodySizeMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.exception_handler(TrazaAgroError)
async def trazaagro_exception_handler(_request: Request, exc: TrazaAgroError) -> JSONResponse:
    body = {
        "error": exc.error_code,
        "mensaje": exc.mensaje,
        **exc.extra,
    }
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    ref_code = uuid.uuid4().hex[:8]
    logger.exception(
        "Error interno no controlado [%s] en %s %s: %s",
        ref_code,
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "mensaje": "Ocurrió un error interno al procesar la solicitud. Contacte al administrador.",
            "codigo_referencia": ref_code,
        },
    )


app.include_router(health_router)
