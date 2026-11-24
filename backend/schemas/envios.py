from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.security import sanitize_text
from backend.schemas.lotes import CODIGO_LOTE_REGEX

CODIGO_ENVIO_REGEX = r"^ENV-\d{4}-\d{4}$"


class EnvioDetalleItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo_lote: str = Field(..., pattern=CODIGO_LOTE_REGEX, examples=["AGU-P018-260314-01"])
    cantidad_kg: float = Field(..., gt=0, le=100000)


class EnvioCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo_envio: str = Field(..., pattern=CODIGO_ENVIO_REGEX, examples=["ENV-2026-2001"])
    tienda_id: int = Field(..., ge=1)
    placas_vehiculo: str = Field(..., min_length=5, max_length=15)
    nombre_chofer: str = Field(..., min_length=3, max_length=80)
    detalles: list[EnvioDetalleItemSchema] = Field(..., min_length=1)

    @field_validator("nombre_chofer")
    @classmethod
    def _clean_chofer(cls, v: str) -> str:
        return sanitize_text(v) or v

    @field_validator("detalles")
    @classmethod
    def _no_duplicate_lotes(cls, items: list[EnvioDetalleItemSchema]) -> list[EnvioDetalleItemSchema]:
        seen: set[str] = set()
        for item in items:
            if item.codigo_lote in seen:
                raise ValueError(f"El lote '{item.codigo_lote}' está duplicado en el detalle del envío.")
            seen.add(item.codigo_lote)
        return items


class SaldoActualizadoSchema(BaseModel):
    codigo_lote: str
    saldo_kg_restante: float


class EnvioCreateResponse(BaseModel):
    codigo_envio: str
    estado_envio: str
    tienda_id: int
    total_kg: float
    saldos_actualizados: list[SaldoActualizadoSchema]
    sincronizacion: dict[str, str]
