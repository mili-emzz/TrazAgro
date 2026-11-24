from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.security import sanitize_text

CODIGO_LOTE_REGEX = r"^AGU-[A-Z0-9]+-\d{6}-\d{2}$"


class LoteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo_lote: str = Field(..., pattern=CODIGO_LOTE_REGEX, examples=["AGU-P014-260320-01"])
    parcela_id: int = Field(..., ge=1)
    producto: str = Field(default="Aguacate Hass", min_length=3, max_length=60)
    fecha_cosecha: datetime
    cuadrilla_cosecha: str = Field(..., min_length=3, max_length=50)
    peso_inicial_kg: float = Field(..., gt=0, le=100000)

    @field_validator("producto", "cuadrilla_cosecha")
    @classmethod
    def _clean_text(cls, v: str) -> str:
        return sanitize_text(v) or v


class LoteResponse(BaseModel):
    lote_id: int
    codigo_lote: str
    parcela_id: int
    producto: str
    fecha_cosecha: datetime
    cuadrilla_cosecha: str
    peso_inicial_kg: float
    saldo_kg: float
    estado: str
    fecha_actualizacion: datetime
    sincronizacion: dict[str, str] | None = None


class LoteLiberarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motivo: str = Field(
        default="Liberación sanitaria aprobada tras verificación de análisis conformes vigentes (RN-02).",
        min_length=5,
        max_length=250,
    )

    @field_validator("motivo")
    @classmethod
    def _clean_motivo(cls, v: str) -> str:
        return sanitize_text(v) or v


class LoteLiberarResponse(BaseModel):
    codigo_lote: str
    estado_previo: str
    estado_actual: str
    saldo_kg: float
    folio_evento: str
    sincronizacion: dict[str, str]


class Expediente360Response(BaseModel):
    lote: dict[str, Any]
    recepcion_sql: dict[str, Any] | None = None
    acta_recepcion: dict[str, Any] | None = None
    analisis_laboratorio: list[dict[str, Any]] = []
    incidentes_bitacora: list[dict[str, Any]] = []
    expedientes_incidentes: list[dict[str, Any]] = []
    red_trazabilidad: dict[str, Any] | None = None
    advertencias: list[str] = []
