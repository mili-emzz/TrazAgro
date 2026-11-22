from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.core.security import sanitize_text
from backend.schemas.lotes import CODIGO_LOTE_REGEX

FOLIO_ANALISIS_REGEX = r"^LAB-\d{4}-AGU-\d{4}-V\d+$"


class LaboratorioInfoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=3, max_length=120)
    acreditacion_iso: str = Field(..., min_length=3, max_length=60)
    contacto_correo: str | None = Field(default=None, max_length=120)


class FirmaDigitalSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    responsable_signatario: str = Field(..., min_length=3, max_length=120)
    cedula_profesional: str | None = Field(default=None, max_length=40)
    hash_integridad: str = Field(..., min_length=8, max_length=128)


class DeterminacionSchema(BaseModel):
    """Determinación analítica polimórfica (química o microbiológica)."""

    model_config = ConfigDict(extra="allow")

    molecula: str | None = Field(default=None, min_length=2, max_length=100)
    parametro: str | None = Field(default=None, min_length=2, max_length=100)
    metodo_ensayo: str | None = Field(default=None, max_length=100)
    unidad: str | None = Field(default=None, max_length=40)
    resultado_mg_kg: float | None = Field(default=None, ge=0)
    limite_maximo_mg_kg: float | None = Field(default=None, ge=0)
    resultado_cualitativo: str | None = Field(default=None, max_length=100)
    criterio_normativo: str | None = Field(default=None, max_length=120)
    conforme: bool

    @model_validator(mode="after")
    def _require_molecula_or_parametro(self) -> "DeterminacionSchema":
        if not self.molecula and not self.parametro:
            raise ValueError("Cada determinación debe especificar 'molecula' o 'parametro'.")
        return self


class MuestraAnalisisSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identificador_muestra: str = Field(..., min_length=2, max_length=60)
    parte_analizada: str | None = Field(default=None, max_length=80)
    peso_gramos: float | None = Field(default=None, ge=1, le=50000)
    determinaciones: list[DeterminacionSchema] = Field(..., min_length=1)


class AnalisisCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    folio_analisis: str = Field(..., pattern=FOLIO_ANALISIS_REGEX, examples=["LAB-2026-AGU-0999-V1"])
    codigo_lote: str = Field(..., pattern=CODIGO_LOTE_REGEX, examples=["AGU-P015-260315-01"])
    tipo_estudio: Literal["Residuos de Plaguicidas", "Microbiologico", "Materia Seca"]
    fecha_muestreo: datetime
    fecha_emision: datetime | None = None
    motivo_enmienda: str | None = Field(default=None, max_length=300)
    dictamen_general: Literal["Conforme", "No Conforme"]
    laboratorio: LaboratorioInfoSchema
    firma_digital: FirmaDigitalSchema | None = None
    muestras: list[MuestraAnalisisSchema] = Field(..., min_length=1)

    @field_validator("motivo_enmienda")
    @classmethod
    def _clean_motivo(cls, v: str | None) -> str | None:
        return sanitize_text(v)


class AnalisisResponse(BaseModel):
    folio_analisis: str
    codigo_lote: str
    tipo_estudio: str
    version: int
    es_vigente: bool
    folio_reemplazado: str | None = None
    dictamen_general: str
    sincronizacion: dict[str, str]


class AnalisisListResponse(BaseModel):
    codigo_lote: str
    total: int
    analisis: list[dict[str, Any]]
