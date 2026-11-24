from fastapi import APIRouter

from backend.core.config import settings
from backend.core.database import db_manager
from backend.schemas.health import HealthResponse, MotorStatus

router = APIRouter(prefix="/api/v1", tags=["Salud"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Verifica el estado de la API y la conectividad con PostgreSQL, MongoDB y Neo4j."""
    raw_status = db_manager.check_health()
    safe_databases: dict[str, MotorStatus] = {}
    all_ok = True

    for motor, info in raw_status.items():
        is_ok = info.get("status") == "ok"
        if not is_ok:
            all_ok = False
        safe_databases[motor] = MotorStatus(
            status="operativo" if is_ok else "degradado",
            detail=None,
        )

    return HealthResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="operativo" if all_ok else "degradado",
        databases=safe_databases,
    )
