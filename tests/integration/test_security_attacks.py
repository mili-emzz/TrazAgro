from fastapi.testclient import TestClient


def test_unauthenticated_requests_rejected_with_401(client: TestClient):
    assert client.get("/api/v1/lotes").status_code == 401
    assert client.get("/api/v1/lotes/AGU-P014-260312-01").status_code == 401
    assert client.post("/api/v1/incidentes/recall", json={}).status_code == 401


def test_tampered_jwt_rejected_with_401(client: TestClient, headers_qa: dict[str, str]):
    tampered = headers_qa["Authorization"] + "tampered"
    resp = client.get("/api/v1/lotes", headers={"Authorization": tampered})
    assert resp.status_code == 401


def test_sql_and_cypher_injection_in_path_rejected_by_regex(
    client: TestClient,
    headers_qa: dict[str, str],
):
    r_sql = client.get("/api/v1/lotes/AGU-P014-260312-01' OR 1=1--", headers=headers_qa)
    assert r_sql.status_code == 422

    r_cypher = client.get(
        "/api/v1/trazabilidad/AGU-P014-260312-01'}) MATCH (n) DETACH DELETE n/adelante",
        headers=headers_qa,
    )
    assert r_cypher.status_code in (404, 422)


def test_nosql_injection_in_analisis_payload_rejected(
    client: TestClient,
    headers_lab: dict[str, str],
):
    resp = client.post(
        "/api/v1/analisis",
        headers=headers_lab,
        json={
            "folio_analisis": "LAB-2026-AGU-8888-V1",
            "codigo_lote": "AGU-P018-260314-01",
            "tipo_estudio": "Residuos de Plaguicidas",
            "fecha_muestreo": "2026-03-20T10:00:00Z",
            "dictamen_general": "Conforme",
            "laboratorio": {"nombre": "Lab AgroBio", "acreditacion_iso": "EMA-17025"},
            "muestras": [
                {
                    "identificador_muestra": "M-01",
                    "determinaciones": [
                        {
                            "molecula": "Clorpirifos",
                            "conforme": True,
                            "$where": "function() { return true; }",
                        }
                    ],
                }
            ],
        },
    )
    assert resp.status_code == 422


def test_xss_payload_is_sanitized_before_storage(
    client: TestClient,
    fake_state: dict,
    headers_qa: dict[str, str],
):
    resp = client.post(
        "/api/v1/lotes",
        headers=headers_qa,
        json={
            "codigo_lote": "AGU-P014-260328-01",
            "parcela_id": 1,
            "producto": "Aguacate Hass",
            "fecha_cosecha": "2026-03-28T07:00:00Z",
            "cuadrilla_cosecha": "<script>alert(1)</script>Cuadrilla Limpia",
            "peso_inicial_kg": 1000.0,
        },
    )
    assert resp.status_code == 201
    stored = fake_state["lotes"]["AGU-P014-260328-01"]["cuadrilla_cosecha"]
    assert "<script>" not in stored
    assert "Cuadrilla Limpia" in stored


def test_login_rate_limiting_blocks_brute_force(client: TestClient):
    for _ in range(10):
        r = client.post(
            "/api/v1/auth/login",
            json={"username": "qa_admin", "password": "wrong_password"},
        )
        assert r.status_code == 401
        assert r.json()["mensaje"] == "Credenciales incorrectas."

    # El intento #11 debe disparar 429 Too Many Requests
    r_blocked = client.post(
        "/api/v1/auth/login",
        json={"username": "qa_admin", "password": "wrong_password"},
    )
    assert r_blocked.status_code == 429
    assert r_blocked.json()["error"] == "TOO_MANY_REQUESTS"


def test_recall_rate_limiting_protects_multimotor_endpoint(
    client: TestClient,
    headers_qa: dict[str, str],
):
    for i in range(5):
        r = client.post(
            "/api/v1/incidentes/recall",
            headers=headers_qa,
            json={
                "folio_incidente": f"INC-2026-800{i}",
                "codigo_lote_origen": "AGU-P014-260312-01",
                "motivo": "Prueba de límite de tasa en recall sanitario",
            },
        )
        assert r.status_code == 201

    r_limited = client.post(
        "/api/v1/incidentes/recall",
        headers=headers_qa,
        json={
            "folio_incidente": "INC-2026-8009",
            "codigo_lote_origen": "AGU-P014-260312-01",
            "motivo": "Intento excediendo límite de tasa",
        },
    )
    assert r_limited.status_code == 429
