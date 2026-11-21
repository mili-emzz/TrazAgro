from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ubicamos el .env en la raíz del proyecto (un nivel arriba de backend/)
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configuración global cargada desde variables de entorno y archivo .env."""

    APP_NAME: str = "TrazaAgro API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # PostgreSQL
    POSTGRES_URI: str = "postgresql://trazaagro:trazaagro_dev_pass@localhost:5433/trazaagro"

    # MongoDB
    MONGO_URI: str = "mongodb://trazaagro:trazaagro_dev_pass@localhost:27017/trazaagro?authSource=admin"
    MONGO_DB: str = "trazaagro"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "trazaagro_dev_pass"

    # Seguridad JWT
    JWT_SECRET_KEY: str = "cambia_esta_clave_en_produccion"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
