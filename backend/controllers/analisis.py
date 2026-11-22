from fastapi import APIRouter, Depends, Path, Query, status
from neo4j import Driver
from psycopg import Connection
from pymongo.database import Database

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.security import (
    ROLE_LABORATORIO,
    ROLE_PRODUCTOR,
    ROLE_QA,
    CurrentUser,
    require_roles,
)
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.analisis import (
    AnalisisCreateRequest,
    AnalisisListResponse,
    AnalisisResponse,
)
from backend.schemas.lotes import CODIGO_LOTE_REGEX
from backend.services.laboratorio_service import LaboratorioService

router = APIRouter(prefix="/api/v1/analisis", tags=["Laboratorio"])


@router.post(
    "",
    response_model=AnalisisResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_analisis(
    payload: AnalisisCreateRequest,
    _user: CurrentUser = Depends(require_roles(ROLE_LABORATORIO, ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> AnalisisResponse:
    """Registra un certificado de laboratorio inmutable (V1 o enmienda V+1, RN-05)."""
    service = LaboratorioService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.registrar_analisis(payload)
    return AnalisisResponse(**result)


@router.get("/{codigo_lote}", response_model=AnalisisListResponse)
def consultar_analisis(
    codigo_lote: str = Path(..., pattern=CODIGO_LOTE_REGEX),
    solo_vigentes: bool = Query(default=False),
    solo_no_conformes: bool = Query(default=False),
    user: CurrentUser = Depends(require_roles(ROLE_QA, ROLE_LABORATORIO, ROLE_PRODUCTOR)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> AnalisisListResponse:
    """Consulta certificados de laboratorio de un lote con soporte de filtros y RN-11."""
    service = LaboratorioService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.consultar_analisis(
        codigo_lote,
        user,
        solo_vigentes=solo_vigentes,
        solo_no_conformes=solo_no_conformes,
    )
    return AnalisisListResponse(**result)
