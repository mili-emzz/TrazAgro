from typing import Generator
from neo4j import Driver, GraphDatabase
from psycopg_pool import ConnectionPool
from pymongo import MongoClient
from pymongo.database import Database

from backend.core.config import settings


class DatabaseManager:
    """Administra el ciclo de vida y pools de PostgreSQL, MongoDB y Neo4j."""

    def __init__(self) -> None:
        self.pg_pool: ConnectionPool | None = None
        self.mongo_client: MongoClient | None = None
        self.neo4j_driver: Driver | None = None

    def connect(self) -> None:
        """Inicializa los clientes y pools de los tres motores."""
        self.pg_pool = ConnectionPool(
            conninfo=settings.POSTGRES_URI,
            min_size=1,
            max_size=10,
            open=True,
            timeout=5.0,
        )
        self.mongo_client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=3000,
        )
        self.neo4j_driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=3.0,
        )

    def close(self) -> None:
        """Cierra de forma ordenada todas las conexiones activas."""
        if self.pg_pool is not None:
            self.pg_pool.close()
            self.pg_pool = None
        if self.mongo_client is not None:
            self.mongo_client.close()
            self.mongo_client = None
        if self.neo4j_driver is not None:
            self.neo4j_driver.close()
            self.neo4j_driver = None

    def get_mongo_db(self) -> Database:
        """Devuelve la instancia de la base de datos en MongoDB."""
        if self.mongo_client is None:
            raise RuntimeError("El cliente de MongoDB no está inicializado.")
        return self.mongo_client[settings.MONGO_DB]

    def check_health(self) -> dict[str, dict[str, str]]:
        """Verifica la conectividad real con los tres motores de persistencia."""
        status: dict[str, dict[str, str]] = {}

        # PostgreSQL
        try:
            if self.pg_pool is None:
                raise RuntimeError("Pool no inicializado")
            with self.pg_pool.connection(timeout=3.0) as conn:
                conn.execute("SELECT 1")
            status["postgresql"] = {"status": "ok"}
        except Exception as exc:
            status["postgresql"] = {"status": "error", "detail": str(exc)}

        # MongoDB
        try:
            if self.mongo_client is None:
                raise RuntimeError("Cliente no inicializado")
            self.mongo_client.admin.command("ping")
            status["mongodb"] = {"status": "ok"}
        except Exception as exc:
            status["mongodb"] = {"status": "error", "detail": str(exc)}

        # Neo4j
        try:
            if self.neo4j_driver is None:
                raise RuntimeError("Driver no inicializado")
            self.neo4j_driver.verify_connectivity()
            status["neo4j"] = {"status": "ok"}
        except Exception as exc:
            status["neo4j"] = {"status": "error", "detail": str(exc)}

        return status


db_manager = DatabaseManager()


def get_pg_connection() -> Generator:
    """Dependencia FastAPI para obtener una conexión del pool de PostgreSQL."""
    if db_manager.pg_pool is None:
        raise RuntimeError("El pool de PostgreSQL no está inicializado.")
    with db_manager.pg_pool.connection() as conn:
        yield conn


def get_mongo_db() -> Database:
    """Dependencia FastAPI para obtener la base de datos de MongoDB."""
    return db_manager.get_mongo_db()


def get_neo4j_driver() -> Driver:
    """Dependencia FastAPI para obtener el driver de Neo4j."""
    if db_manager.neo4j_driver is None:
        raise RuntimeError("El driver de Neo4j no está inicializado.")
    return db_manager.neo4j_driver
