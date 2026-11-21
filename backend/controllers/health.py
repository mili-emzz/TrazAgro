from fastapi import APIRouter

from backend.core.config import settings
from backend.core.database import db_manager
from backend.schemas.health import HealthResponse

router = APIRouter(tags=["Salud"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Verifica el estado de la API y la conectividad con PostgreSQL, MongoDB y Neo4j."""
    db_status = db_manager.check_health()
    all_ok = all(item["status"] == "ok" for item in db_status.values())
    return HealthResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="ok" if all_ok else "degraded",
        databases=db_status,
    )
