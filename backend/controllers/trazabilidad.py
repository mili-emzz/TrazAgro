from fastapi import APIRouter, Depends, Path, Query
from neo4j import Driver
from psycopg import Connection
from pymongo.database import Database

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.security import ROLE_QA, CurrentUser, require_roles
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.lotes import CODIGO_LOTE_REGEX
from backend.schemas.trazabilidad import (
    TrazabilidadAdelanteResponse,
    TrazabilidadAtrasLateralResponse,
)
from backend.services.trazabilidad_qa_service import TrazabilidadQAService

router = APIRouter(prefix="/api/v1/trazabilidad", tags=["Trazabilidad (Grafos)"])


@router.get("/{codigo_lote}/adelante", response_model=TrazabilidadAdelanteResponse)
def trazabilidad_adelante(
    codigo_lote: str = Path(..., pattern=CODIGO_LOTE_REGEX),
    _user: CurrentUser = Depends(require_roles(ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> TrazabilidadAdelanteResponse:
    """Rastreo Forward: envíos y tiendas destino alcanzados por el lote."""
    service = TrazabilidadQAService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.rastreo_adelante(codigo_lote)
    return TrazabilidadAdelanteResponse(**result)


@router.get("/{codigo_lote}/atras-lateral", response_model=TrazabilidadAtrasLateralResponse)
def trazabilidad_atras_lateral(
    codigo_lote: str = Path(..., pattern=CODIGO_LOTE_REGEX),
    ventana_dias: int = Query(default=1, ge=0, le=30),
    _user: CurrentUser = Depends(require_roles(ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> TrazabilidadAtrasLateralResponse:
    """Rastreo Backward (parcela/productor) y Lateral (lotes hermanos por vehículo o cuarto frío, RN-08)."""
    service = TrazabilidadQAService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.rastreo_atras_lateral(codigo_lote, ventana_dias=ventana_dias)
    return TrazabilidadAtrasLateralResponse(**result)
