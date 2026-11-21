from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.controllers.health import router as health_router
from backend.core.config import settings
from backend.core.database import db_manager


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
