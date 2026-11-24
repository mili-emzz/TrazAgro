from datetime import datetime, timezone

from pydantic import ValidationError
import pytest

from backend.schemas.analisis import AnalisisCreateRequest, DeterminacionSchema
from backend.schemas.envios import EnvioCreateRequest
from backend.schemas.incidentes import IncidenteCerrarRequest
from backend.schemas.lotes import LoteCreateRequest
from backend.schemas.recepciones import EvidenciaFotograficaSchema, RecepcionCreateRequest


def test_lote_schema_valid_and_rejects_extra_fields():
    ok = LoteCreateRequest(
        codigo_lote="AGU-P014-260320-01",
        parcela_id=1,
        producto="Aguacate Hass",
        fecha_cosecha=datetime.now(timezone.utc),
        cuadrilla_cosecha="Cuadrilla Alfa-01",
        peso_inicial_kg=1500.0,
    )
    assert ok.codigo_lote == "AGU-P014-260320-01"

    with pytest.raises(ValidationError):
        LoteCreateRequest(
            codigo_lote="AGU-P014-260320-01",
            parcela_id=1,
            fecha_cosecha=datetime.now(timezone.utc),
            cuadrilla_cosecha="Cuadrilla Alfa-01",
            peso_inicial_kg=1500.0,
            estado="Liberado",  # extra=forbid debe rechazarlo
        )


def test_lote_schema_rejects_invalid_code_and_weight():
    with pytest.raises(ValidationError):
        LoteCreateRequest(
            codigo_lote="LOTE-MALO-123",
            parcela_id=1,
            fecha_cosecha=datetime.now(timezone.utc),
            cuadrilla_cosecha="Cuadrilla Alfa-01",
            peso_inicial_kg=1500.0,
        )
    with pytest.raises(ValidationError):
        LoteCreateRequest(
            codigo_lote="AGU-P014-260320-01",
            parcela_id=1,
            fecha_cosecha=datetime.now(timezone.utc),
            cuadrilla_cosecha="Cuadrilla Alfa-01",
            peso_inicial_kg=-50.0,
        )


def test_determinacion_rejects_nosql_dollar_operator_keys():
    with pytest.raises(ValidationError):
        DeterminacionSchema(
            molecula="Clorpirifos",
            conforme=False,
            **{"$where": "sleep(5000)"},
        )
    with pytest.raises(ValidationError):
        DeterminacionSchema(
            molecula="Clorpirifos",
            conforme=False,
            **{"nested.key": "injection"},
        )


def test_evidencia_fotografica_rejects_javascript_uri():
    with pytest.raises(ValidationError):
        EvidenciaFotograficaSchema(
            tipo_evidencia="Termometro",
            url_archivo="javascript:alert(1)",
        )
    ok = EvidenciaFotograficaSchema(
        tipo_evidencia="Termometro",
        url_archivo="https://cdn.trazaagro.mx/evidencias/foto1.jpg",
    )
    assert ok.url_archivo.startswith("https://")


def test_envio_rejects_duplicate_lotes_in_same_request():
    with pytest.raises(ValidationError):
        EnvioCreateRequest(
            codigo_envio="ENV-2026-2001",
            tienda_id=1,
            placas_vehiculo="TRK-884-A",
            nombre_chofer="Luis Estrada",
            detalles=[
                {"codigo_lote": "AGU-P018-260314-01", "cantidad_kg": 100.0},
                {"codigo_lote": "AGU-P018-260314-01", "cantidad_kg": 50.0},
            ],
        )


def test_incidente_cerrar_enforces_rn09_minimums():
    with pytest.raises(ValidationError):
        IncidenteCerrarRequest(
            causa_raiz="Corta",
            acciones_correctivas=[],
            responsable_qa="QA",
            aprobacion_gerencia="Dir",
        )


def test_recepcion_rejects_absurd_temperature():
    with pytest.raises(ValidationError):
        RecepcionCreateRequest(
            folio_recepcion="REC-2026-0201",
            codigo_lote="AGU-P014-260320-01",
            placas_vehiculo="MICH-842-K",
            nombre_chofer="Martín Morales",
            codigo_cuarto_frio="CF-01",
            peso_recibido_kg=1500.0,
            temperatura_llegada_c=99.5,
            evaluacion_sensorial={"color_epidermis": "Verde oscuro", "olor_extrano": False},
            monitoreo_temperatura_caja=[{"zona_contenedor": "Frente", "temperatura_c": 5.5}],
        )


def test_analisis_requires_valid_folio_regex():
    with pytest.raises(ValidationError):
        AnalisisCreateRequest(
            folio_analisis="BAD-FOLIO",
            codigo_lote="AGU-P014-260320-01",
            tipo_estudio="Microbiologico",
            fecha_muestreo=datetime.now(timezone.utc),
            dictamen_general="Conforme",
            laboratorio={"nombre": "Lab AgroBio", "acreditacion_iso": "EMA-17025"},
            muestras=[
                {
                    "identificador_muestra": "M-01",
                    "determinaciones": [{"parametro": "Salmonella spp.", "conforme": True}],
                }
            ],
        )
