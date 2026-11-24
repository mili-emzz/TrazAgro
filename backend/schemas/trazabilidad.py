from typing import Any

from pydantic import BaseModel


class TrazabilidadAdelanteResponse(BaseModel):
    codigo_lote: str
    total_envios: int
    total_kg_despachados: float
    tiendas_afectadas: list[dict[str, Any]]


class TrazabilidadAtrasLateralResponse(BaseModel):
    codigo_lote: str
    ventana_dias: int
    origen: dict[str, Any] | None = None
    lotes_hermanos: list[dict[str, Any]]
