from typing import Any

from fastapi import APIRouter, Depends, Path, Query, status
from neo4j import Driver
from psycopg import Connection
from pymongo.database import Database

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.security import (
    ROLE_PRODUCTOR,
    ROLE_QA,
    CurrentUser,
    get_current_user,
    require_roles,
)
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.lotes import (
    CODIGO_LOTE_REGEX,
    Expediente360Response,
    LoteCreateRequest,
    LoteLiberarRequest,
    LoteLiberarResponse,
    LoteResponse,
)
from backend.services.lotes_service import LotesService
from backend.services.trazabilidad_qa_service import TrazabilidadQAService

router = APIRouter(prefix="/api/v1/lotes", tags=["Lotes"])


@router.get("", response_model=list[dict[str, Any]])
def listar_lotes(
    estado: str | None = Query(default=None),
    user: CurrentUser = Depends(get_current_user),
    pg_conn: Connection = Depends(get_pg_connection),
) -> list[dict[str, Any]]:
    """Lista lotes aplicando aislamiento por productor (RN-11) cuando el rol es Productor."""
    pg_repo = PostgresRepository(pg_conn)
    productor_scope = user.productor_id if user.role == ROLE_PRODUCTOR else None
    return pg_repo.list_lotes(productor_id=productor_scope, estado=estado)


@router.post(
    "",
    response_model=LoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_lote(
    payload: LoteCreateRequest,
    user: CurrentUser = Depends(require_roles(ROLE_PRODUCTOR, ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> LoteResponse:
    """Registra un lote recién cosechado en PostgreSQL y proyecta su nodo en Neo4j (RN-06)."""
    service = LotesService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.crear_lote(payload, user)
    return LoteResponse(**result)


@router.get("/{codigo_lote}", response_model=Expediente360Response)
def obtener_expediente_360(
    codigo_lote: str = Path(..., pattern=CODIGO_LOTE_REGEX),
    user: CurrentUser = Depends(get_current_user),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> Expediente360Response:
    """Devuelve el Expediente 360° fusionando PostgreSQL, MongoDB y Neo4j (RN-11)."""
    service = TrazabilidadQAService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.obtener_expediente_360(codigo_lote, user)
    return Expediente360Response(**result)


@router.patch("/{codigo_lote}/liberar", response_model=LoteLiberarResponse)
def liberar_lote(
    payload: LoteLiberarRequest,
    codigo_lote: str = Path(..., pattern=CODIGO_LOTE_REGEX),
    user: CurrentUser = Depends(require_roles(ROLE_QA)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> LoteLiberarResponse:
    """Libera sanitariamente un lote tras verificar análisis vigentes conformes (RN-02, RN-04)."""
    service = LotesService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.liberar_lote(codigo_lote, payload, user)
    return LoteLiberarResponse(**result)
