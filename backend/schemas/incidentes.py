from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.security import sanitize_text
from backend.schemas.lotes import CODIGO_LOTE_REGEX

FOLIO_INCIDENTE_REGEX = r"^INC-\d{4}-\d{4}$"


class RecallCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    folio_incidente: str | None = Field(default=None, pattern=FOLIO_INCIDENTE_REGEX)
    codigo_lote_origen: str = Field(..., pattern=CODIGO_LOTE_REGEX, examples=["AGU-P014-260312-01"])
    motivo: str = Field(..., min_length=10, max_length=250)
    incluir_lotes_hermanos: bool = True
    ventana_dias_contaminacion: int = Field(default=1, ge=0, le=30)

    @field_validator("motivo")
    @classmethod
    def _clean_motivo(cls, v: str) -> str:
        return sanitize_text(v) or v


class RecallResponse(BaseModel):
    folio_incidente: str
    lote_origen: dict[str, Any]
    evidencia_documental: dict[str, Any] | None = None
    lotes_hermanos_bloqueados: list[dict[str, Any]] = []
    tiendas_afectadas: list[dict[str, Any]] = []
    sincronizacion: dict[str, str]


class IncidenteCerrarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    causa_raiz: str = Field(..., min_length=10, max_length=500)
    acciones_correctivas: list[str] = Field(..., min_length=1)
    responsable_qa: str = Field(..., min_length=3, max_length=100)
    aprobacion_gerencia: str = Field(..., min_length=3, max_length=100)

    @field_validator("causa_raiz", "responsable_qa", "aprobacion_gerencia")
    @classmethod
    def _clean_fields(cls, v: str) -> str:
        return sanitize_text(v) or v

    @field_validator("acciones_correctivas")
    @classmethod
    def _clean_acciones(cls, items: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in items:
            txt = sanitize_text(item) or ""
            if len(txt) < 5:
                raise ValueError("Cada acción correctiva debe tener al menos 5 caracteres.")
            cleaned.append(txt)
        return cleaned


class IncidenteCerrarResponse(BaseModel):
    folio_incidente: str
    estado_expediente: str
    fecha_cierre: Any
    causa_raiz: str
    acciones_correctivas: list[str]
    firmas_cierre: dict[str, str]
    sincronizacion: dict[str, str]
