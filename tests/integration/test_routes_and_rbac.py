from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.core.database import db_manager
from backend.main import app


def test_openapi_exposes_all_14_contract_endpoints():
    schema = app.openapi()
    paths = schema["paths"]
    expected = [
        ("/api/v1/health", "get"),
        ("/api/v1/auth/login", "post"),
        ("/api/v1/lotes", "post"),
        ("/api/v1/lotes/{codigo_lote}", "get"),
        ("/api/v1/recepciones", "post"),
        ("/api/v1/analisis", "post"),
        ("/api/v1/analisis/{codigo_lote}", "get"),
        ("/api/v1/lotes/{codigo_lote}/liberar", "patch"),
        ("/api/v1/envios", "post"),
        ("/api/v1/incidentes/recall", "post"),
        ("/api/v1/incidentes/{folio}/cerrar", "patch"),
        ("/api/v1/trazabilidad/{codigo_lote}/adelante", "get"),
        ("/api/v1/trazabilidad/{codigo_lote}/atras-lateral", "get"),
        ("/api/v1/admin/reconciliacion/ejecutar", "post"),
    ]
    for route, method in expected:
        assert route in paths, f"Falta ruta {route}"
        assert method in paths[route], f"Falta método {method} en {route}"

    # RN-05: No debe existir PUT ni DELETE en /api/v1/analisis
    assert "put" not in paths["/api/v1/analisis"]
    assert "delete" not in paths["/api/v1/analisis"]


def test_health_endpoint_masks_internal_errors(client: TestClient):
    with patch.object(
        db_manager,
        "check_health",
        return_value={
            "postgresql": {"status": "ok"},
            "mongodb": {"status": "error", "detail": "mongodb://secret_pass@10.0.0.5:27017"},
            "neo4j": {"status": "ok"},
        },
    ):
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded" or body["status"] == "degradado"
    assert body["databases"]["mongodb"]["status"] == "degradado"
    assert body["databases"]["mongodb"]["detail"] is None
    assert "secret_pass" not in resp.text


def test_security_headers_present_on_api_responses(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "max-age=31536000" in resp.headers["Strict-Transport-Security"]
    assert resp.headers["Content-Security-Policy"] == "default-src 'self'"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_max_body_size_middleware_rejects_over_5mb(client: TestClient, headers_qa: dict[str, str]):
    resp = client.post(
        "/api/v1/lotes",
        headers={**headers_qa, "Content-Length": str(6 * 1024 * 1024)},
        content=b"{}",
    )
    assert resp.status_code == 413
    assert resp.json()["error"] == "PAYLOAD_TOO_LARGE"


def test_rbac_blocks_unauthorized_roles(
    client: TestClient,
    headers_productor_1: dict[str, str],
    headers_recepcion: dict[str, str],
    headers_lab: dict[str, str],
):
    # Recepción no puede liberar lotes ni ejecutar recall (RN-04)
    assert (
        client.patch(
            "/api/v1/lotes/AGU-P018-260314-01/liberar",
            headers=headers_recepcion,
            json={"motivo": "Intento indebido de liberación"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/incidentes/recall",
            headers=headers_recepcion,
            json={"codigo_lote_origen": "AGU-P014-260312-01", "motivo": "Intento indebido de recall"},
        ).status_code
        == 403
    )
    assert (
        client.post("/api/v1/admin/reconciliacion/ejecutar", headers=headers_recepcion).status_code
        == 403
    )

    # Productor no puede registrar recepciones, envíos ni análisis
    assert client.post("/api/v1/envios", headers=headers_productor_1, json={}).status_code == 403
    assert client.post("/api/v1/recepciones", headers=headers_productor_1, json={}).status_code == 403
    assert client.post("/api/v1/analisis", headers=headers_productor_1, json={}).status_code == 403

    # Laboratorio no puede crear lotes ni cerrar incidentes
    assert client.post("/api/v1/lotes", headers=headers_lab, json={}).status_code == 403
    assert (
        client.patch("/api/v1/incidentes/INC-2026-0001/cerrar", headers=headers_lab, json={}).status_code
        == 403
    )


def test_bola_idor_rn11_isolates_productor_data(
    client: TestClient,
    headers_productor_1: dict[str, str],
    headers_productor_2: dict[str, str],
):
    # Productor 1 puede consultar su propio lote (parcela 1 -> productor 1)
    r_own = client.get("/api/v1/lotes/AGU-P014-260312-01", headers=headers_productor_1)
    assert r_own.status_code == 200

    # Productor 1 NO puede consultar el lote de Productor 2 (parcela 3 -> productor 2)
    r_other = client.get("/api/v1/lotes/AGU-P018-260314-01", headers=headers_productor_1)
    assert r_other.status_code == 403

    # Productor 1 NO puede consultar análisis de lote ajeno
    r_an_other = client.get("/api/v1/analisis/AGU-P018-260314-01", headers=headers_productor_1)
    assert r_an_other.status_code == 403

    # Productor 1 NO puede crear lote en parcela de Productor 2
    r_create_other = client.post(
        "/api/v1/lotes",
        headers=headers_productor_1,
        json={
            "codigo_lote": "AGU-P018-260321-01",
            "parcela_id": 3,
            "producto": "Aguacate Hass",
            "fecha_cosecha": "2026-03-21T08:00:00Z",
            "cuadrilla_cosecha": "Cuadrilla Ajena",
            "peso_inicial_kg": 1000.0,
        },
    )
    assert r_create_other.status_code == 403

    # Listado de lotes filtra estrictamente por productor_id
    lotes_p1 = client.get("/api/v1/lotes", headers=headers_productor_1).json()
    lotes_p2 = client.get("/api/v1/lotes", headers=headers_productor_2).json()
    assert all(l["productor_id"] == 1 for l in lotes_p1)
    assert all(l["productor_id"] == 2 for l in lotes_p2)


def test_unhandled_exception_returns_safe_500_without_leaks(
    client: TestClient,
    headers_qa: dict[str, str],
    monkeypatch,
):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("psycopg.OperationalError: password=SUPER_SECRET_DB_PASS on table lotes")

    monkeypatch.setattr(
        "backend.services.trazabilidad_qa_service.TrazabilidadQAService.obtener_expediente_360",
        _boom,
    )
    resp = client.get("/api/v1/lotes/AGU-P014-260312-01", headers=headers_qa)
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"] == "INTERNAL_SERVER_ERROR"
    assert "codigo_referencia" in body and len(body["codigo_referencia"]) == 8
    assert "SUPER_SECRET_DB_PASS" not in resp.text
    assert "psycopg" not in resp.text

