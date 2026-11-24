from typing import Any

from pydantic import BaseModel


class ReconciliacionEjecucionResponse(BaseModel):
    total_pendientes: int
    procesados: int
    fallidos: int
    detalle: list[dict[str, Any]]
