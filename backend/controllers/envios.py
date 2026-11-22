from fastapi import APIRouter, Depends, status
from neo4j import Driver
from psycopg import Connection
from pymongo.database import Database

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.security import ROLE_RECEPCION, CurrentUser, require_roles
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.envios import EnvioCreateRequest, EnvioCreateResponse
from backend.services.despachos_service import DespachosService

router = APIRouter(prefix="/api/v1/envios", tags=["Envíos y Despachos"])


@router.post(
    "",
    response_model=EnvioCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_envio(
    payload: EnvioCreateRequest,
    _user: CurrentUser = Depends(require_roles(ROLE_RECEPCION)),
    pg_conn: Connection = Depends(get_pg_connection),
    mongo_db: Database = Depends(get_mongo_db),
    neo4j_driver: Driver = Depends(get_neo4j_driver),
) -> EnvioCreateResponse:
    """Registra despacho fraccionado ACID (RN-01, RN-03) en PostgreSQL y proyecta aristas en Neo4j."""
    service = DespachosService(
        PostgresRepository(pg_conn),
        MongoRepository(mongo_db),
        Neo4jRepository(neo4j_driver),
    )
    result = service.registrar_envio(payload)
    return EnvioCreateResponse(**result)
