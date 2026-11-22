from fastapi import APIRouter, Depends, Path, Request, status
from neo4j import Driver
from psycopg import Connection
from pymongo.database import Database

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.security import (
    ROLE_QA,
    CurrentUser,
    rate_limit_recall,
    require_roles,
)
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.incidentes import (
    FOLIO_INCIDENTE_REGEX,
    IncidenteCerrarRequest,
    IncidenteCerrarResponse,
    RecallCreateRequest,
    RecallResponse,
)
from backend.services.trazabilidad_qa_service import TrazabilidadQAService

router = APIRouter(prefix="/api/v1/incidentes", tags=["Incidentes y Recall"])


@router.post(
    "/recall",
    response_model=RecallResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_recall)],
)
def ejecutar_recall(
    payload: RecallCreateRequest,
    request: Request,
    user: CurrentUser = Depends(require_roles(ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> RecallResponse:
    """Protocolo integrado de bloqueo atómico, contagio lateral y alerta de retiro (RN-04, RN-08)."""
    client_ip = request.client.host if request.client else "unknown"
    service = TrazabilidadQAService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.ejecutar_recall(payload, user, client_ip=client_ip)
    return RecallResponse(**result)


@router.patch("/{folio}/cerrar", response_model=IncidenteCerrarResponse)
def cerrar_incidente(
    payload: IncidenteCerrarRequest,
    folio: str = Path(..., pattern=FOLIO_INCIDENTE_REGEX),
    user: CurrentUser = Depends(require_roles(ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> IncidenteCerrarResponse:
    """Cierra un expediente de incidente exigiendo causa raíz, acciones correctivas y firmas (RN-09)."""
    service = TrazabilidadQAService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.cerrar_incidente(folio, payload, user)
    return IncidenteCerrarResponse(**result)
