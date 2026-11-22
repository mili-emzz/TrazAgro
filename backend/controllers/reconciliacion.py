from fastapi import APIRouter, Depends, Query
from neo4j import Driver
from psycopg import Connection
from pymongo.database import Database

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.security import ROLE_QA, CurrentUser, require_roles
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.reconciliacion import ReconciliacionEjecucionResponse
from backend.services.reconciliacion_service import ReconciliacionService

router = APIRouter(prefix="/api/v1/admin/reconciliacion", tags=["Reconciliación Outbox"])


@router.post("/ejecutar", response_model=ReconciliacionEjecucionResponse)
def ejecutar_reconciliacion(
    limit: int = Query(default=50, ge=1, le=200),
    _user: CurrentUser = Depends(require_roles(ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> ReconciliacionEjecucionResponse:
    """Reprocesa eventos pendientes en eventos_reconciliacion hacia MongoDB y Neo4j."""
    service = ReconciliacionService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.ejecutar_pendientes(limit=limit)
    return ReconciliacionEjecucionResponse(**result)
