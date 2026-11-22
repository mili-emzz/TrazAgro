from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.security import sanitize_text
from backend.schemas.lotes import CODIGO_LOTE_REGEX

FOLIO_RECEPCION_REGEX = r"^REC-\d{4}-\d{4}$"


class EvaluacionSensorialSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    color_epidermis: str = Field(..., min_length=2, max_length=80)
    firmeza_pulpa_lb: float | None = Field(default=None, ge=0, le=100)
    materia_seca_estimada_pct: float | None = Field(default=None, ge=0, le=100)
    calibre_predominante: str | None = Field(default=None, max_length=40)
    pedunculo_presente_pct: float | None = Field(default=None, ge=0, le=100)
    olor_extrano: bool = False


class DefectoDetectadoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo_defecto: str = Field(..., min_length=2, max_length=80)
    severidad: Literal["Leve", "Moderada", "Grave"] = "Leve"
    porcentaje_afectado: float = Field(..., ge=0, le=100)


class LecturaTemperaturaCajaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zona_contenedor: str = Field(..., min_length=2, max_length=60)
    tarima: str | None = Field(default=None, max_length=40)
    temperatura_c: float = Field(..., ge=-5.0, le=40.0)


class EvidenciaFotograficaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo_evidencia: str = Field(..., min_length=2, max_length=60)
    url_archivo: str = Field(..., min_length=5, max_length=300)
    descripcion: str | None = Field(default=None, max_length=200)


class RecepcionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    folio_recepcion: str = Field(..., pattern=FOLIO_RECEPCION_REGEX, examples=["REC-2026-0201"])
    codigo_lote: str = Field(..., pattern=CODIGO_LOTE_REGEX, examples=["AGU-P014-260318-01"])
    placas_vehiculo: str = Field(..., min_length=5, max_length=15)
    nombre_chofer: str = Field(..., min_length=3, max_length=80)
    codigo_cuarto_frio: str = Field(..., min_length=3, max_length=15)
    peso_recibido_kg: float = Field(..., gt=0, le=100000)
    temperatura_llegada_c: float = Field(..., ge=-5.0, le=40.0)
    turno: str = Field(default="Matutino", min_length=3, max_length=30)
    evaluacion_sensorial: EvaluacionSensorialSchema
    defectos_detectados: list[DefectoDetectadoSchema] = Field(default_factory=list)
    monitoreo_temperatura_caja: list[LecturaTemperaturaCajaSchema] = Field(..., min_length=1)
    evidencias_fotograficas: list[EvidenciaFotograficaSchema] = Field(default_factory=list)
    observaciones_inspector: str | None = Field(default=None, max_length=500)

    @field_validator("nombre_chofer", "observaciones_inspector")
    @classmethod
    def _clean_text(cls, v: str | None) -> str | None:
        return sanitize_text(v)


class RecepcionResponse(BaseModel):
    recepcion_id: int
    folio_recepcion: str
    codigo_lote: str
    fecha_llegada: datetime
    placas_vehiculo: str
    codigo_cuarto_frio: str
    peso_recibido_kg: float
    temperatura_llegada_c: float
    dictamen_recepcion: str
    estado_lote_resultante: str
    alerta_cadena_frio: bool
    sincronizacion: dict[str, str]
