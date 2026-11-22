from fastapi import APIRouter, Depends, status
from neo4j import Driver
from psycopg import Connection
from pymongo.database import Database

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.security import ROLE_RECEPCION, CurrentUser, require_roles
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.recepciones import RecepcionCreateRequest, RecepcionResponse
from backend.services.lotes_service import LotesService

router = APIRouter(prefix="/api/v1/recepciones", tags=["Recepciones CEDIS"])


@router.post(
    "",
    response_model=RecepcionResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_recepcion(
    payload: RecepcionCreateRequest,
    user: CurrentUser = Depends(require_roles(ROLE_RECEPCION)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> RecepcionResponse:
    """Registra arribo en CEDIS, evalúa cadena de frío (RN-07), guarda acta en MongoDB y proyecta Neo4j."""
    service = LotesService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.registrar_recepcion(payload, user)
    return RecepcionResponse(**result)
