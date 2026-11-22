from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository


def test_rn01_cannot_dispatch_blocked_lote(client: TestClient, headers_recepcion: dict[str, str]):
    resp = client.post(
        "/api/v1/envios",
        headers=headers_recepcion,
        json={
            "codigo_envio": "ENV-2026-9001",
            "tienda_id": 1,
            "placas_vehiculo": "TRK-884-A",
            "nombre_chofer": "Luis Estrada",
            "detalles": [{"codigo_lote": "AGU-P014-260312-01", "cantidad_kg": 100.0}],
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "LOTE_NO_DISPONIBLE_PARA_DESPACHO"


def test_rn03_acid_rollback_on_insufficient_balance(
    client: TestClient,
    fake_state: dict,
    headers_recepcion: dict[str, str],
):
    saldo_antes = fake_state["lotes"]["AGU-P018-260314-01"]["saldo_kg"]
    resp = client.post(
        "/api/v1/envios",
        headers=headers_recepcion,
        json={
            "codigo_envio": "ENV-2026-9002",
            "tienda_id": 1,
            "placas_vehiculo": "TRK-884-A",
            "nombre_chofer": "Luis Estrada",
            "detalles": [{"codigo_lote": "AGU-P018-260314-01", "cantidad_kg": 9999.0}],
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "SALDO_INSUFICIENTE"
    assert fake_state["lotes"]["AGU-P018-260314-01"]["saldo_kg"] == saldo_antes


def test_rn10_blocks_inactive_producer_and_inactive_store(
    client: TestClient,
    headers_qa: dict[str, str],
    headers_recepcion: dict[str, str],
):
    # Productor 3 inactivo (parcela 4)
    r_prod = client.post(
        "/api/v1/lotes",
        headers=headers_qa,
        json={
            "codigo_lote": "AGU-P022-260322-01",
            "parcela_id": 4,
            "producto": "Aguacate Hass",
            "fecha_cosecha": "2026-03-22T07:00:00Z",
            "cuadrilla_cosecha": "Cuadrilla Jalisco",
            "peso_inicial_kg": 1200.0,
        },
    )
    assert r_prod.status_code == 409
    assert r_prod.json()["error"] == "PRODUCTOR_INACTIVO"

    # Tienda 4 inactiva
    r_store = client.post(
        "/api/v1/envios",
        headers=headers_recepcion,
        json={
            "codigo_envio": "ENV-2026-9003",
            "tienda_id": 4,
            "placas_vehiculo": "TRK-884-A",
            "nombre_chofer": "Luis Estrada",
            "detalles": [{"codigo_lote": "AGU-P018-260314-01", "cantidad_kg": 100.0}],
        },
    )
    assert r_store.status_code == 409
    assert r_store.json()["error"] == "TIENDA_INACTIVA"


def test_outbox_reconciliation_recovers_neo4j_and_mongo_partial_failures(
    client: TestClient,
    fake_state: dict,
    headers_qa: dict[str, str],
):
    # 1. Simular caída de Neo4j durante alta de lote
    fake_state["fail_neo4j"] = True
    r_create = client.post(
        "/api/v1/lotes",
        headers=headers_qa,
        json={
            "codigo_lote": "AGU-P014-260325-01",
            "parcela_id": 1,
            "producto": "Aguacate Hass",
            "fecha_cosecha": "2026-03-25T07:30:00Z",
            "cuadrilla_cosecha": "Cuadrilla Outbox",
            "peso_inicial_kg": 1400.0,
        },
    )
    assert r_create.status_code == 201
    assert r_create.json()["sincronizacion"]["postgresql"] == "confirmado"
    assert r_create.json()["sincronizacion"]["neo4j"] == "pendiente_reconciliacion"
    assert "AGU-P014-260325-01" not in fake_state["neo4j_lotes"]
    assert len(fake_state["outbox"]) == 1

    # 2. Simular caída de MongoDB durante Recall (PG igual bloquea atómicamente)
    fake_state["fail_mongo"] = True
    r_recall = client.post(
        "/api/v1/incidentes/recall",
        headers=headers_qa,
        json={
            "folio_incidente": "INC-2026-7777",
            "codigo_lote_origen": "AGU-P014-260325-01",
            "motivo": "Prueba de fallo parcial Mongo+Neo4j durante recall sanitario",
        },
    )
    assert r_recall.status_code == 201
    assert r_recall.json()["lote_origen"]["estado_actual"] == "Bloqueado"
    assert r_recall.json()["sincronizacion"]["postgresql"] == "confirmado"
    assert r_recall.json()["sincronizacion"]["mongodb"] == "pendiente_reconciliacion"
    assert r_recall.json()["sincronizacion"]["neo4j"] == "pendiente_reconciliacion"
    assert len(fake_state["outbox"]) == 3

    # 3. Restaurar motores y ejecutar reconciliación Outbox
    fake_state["fail_neo4j"] = False
    fake_state["fail_mongo"] = False
    r_rec = client.post("/api/v1/admin/reconciliacion/ejecutar", headers=headers_qa)
    assert r_rec.status_code == 200
    body = r_rec.json()
    assert body["total_pendientes"] == 3
    assert body["procesados"] == 3
    assert body["fallidos"] == 0

    # 4. Verificar convergencia final en Neo4j y MongoDB
    assert fake_state["neo4j_lotes"]["AGU-P014-260325-01"]["estado"] == "Bloqueado"
    assert "INC-2026-7777" in fake_state["expedientes"]


def test_real_repos_use_parameterized_queries_only():
    # Verificar que PostgresRepository pasa parámetros separados y no interpola el valor en SQL
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    pg = PostgresRepository(mock_conn)
    malicious = "AGU-P014-260312-01' OR '1'='1"
    pg.get_lote_by_codigo(malicious)
    executed_sql, executed_params = mock_cur.execute.call_args[0]
    assert malicious not in executed_sql
    assert executed_params == (malicious,)

    # Verificar que Neo4jRepository pasa parámetros como diccionario separado del Cypher
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_session.run.return_value = []
    mock_driver.session.return_value.__enter__.return_value = mock_session

    n4j = Neo4jRepository(mock_driver)
    cypher_injection = "'}) MATCH (n) DETACH DELETE n //"
    n4j.rastreo_adelante(cypher_injection)
    executed_cypher, cypher_params = mock_session.run.call_args[0]
    assert cypher_injection not in executed_cypher
    assert cypher_params == {"codigo_lote": cypher_injection}


def test_mongo_down_on_analisis_aborts_with_503_without_touching_neo4j(
    client: TestClient,
    fake_state: dict,
    headers_lab: dict[str, str],
):
    fake_state["fail_mongo"] = True
    resp = client.post(
        "/api/v1/analisis",
        headers=headers_lab,
        json={
            "folio_analisis": "LAB-2026-AGU-5555-V1",
            "codigo_lote": "AGU-P018-260314-01",
            "tipo_estudio": "Microbiologico",
            "fecha_muestreo": "2026-03-20T10:00:00Z",
            "dictamen_general": "Conforme",
            "laboratorio": {"nombre": "Lab AgroBio", "acreditacion_iso": "EMA-17025"},
            "muestras": [
                {
                    "identificador_muestra": "M-01",
                    "determinaciones": [{"parametro": "Salmonella spp.", "conforme": True}],
                }
            ],
        },
    )
    assert resp.status_code == 503
    assert "AGU-P018-260314-01" not in fake_state["neo4j_analisis"]
    assert len(fake_state["outbox"]) == 0


def test_analisis_filter_solo_no_conformes_and_duplicate_reception_guard(
    client: TestClient,
    headers_lab: dict[str, str],
    headers_qa: dict[str, str],
    headers_recepcion: dict[str, str],
):
    # Recepción sobre lote ya 'Liberado' debe fallar con 409
    r_dup_rec = client.post(
        "/api/v1/recepciones",
        headers=headers_recepcion,
        json={
            "folio_recepcion": "REC-2026-9999",
            "codigo_lote": "AGU-P018-260314-01",
            "placas_vehiculo": "MICH-842-K",
            "nombre_chofer": "Martín Morales",
            "codigo_cuarto_frio": "CF-01",
            "peso_recibido_kg": 2000.0,
            "temperatura_llegada_c": 5.5,
            "evaluacion_sensorial": {"color_epidermis": "Verde", "olor_extrano": False},
            "monitoreo_temperatura_caja": [{"zona_contenedor": "Centro", "temperatura_c": 5.5}],
        },
    )
    assert r_dup_rec.status_code == 409

    # Insertar 1 análisis conforme y 1 no conforme para probar filtro solo_no_conformes
    client.post(
        "/api/v1/analisis",
        headers=headers_lab,
        json={
            "folio_analisis": "LAB-2026-AGU-6001-V1",
            "codigo_lote": "AGU-P018-260314-01",
            "tipo_estudio": "Microbiologico",
            "fecha_muestreo": "2026-03-20T10:00:00Z",
            "dictamen_general": "Conforme",
            "laboratorio": {"nombre": "Lab AgroBio", "acreditacion_iso": "EMA-17025"},
            "muestras": [
                {
                    "identificador_muestra": "M-01",
                    "determinaciones": [{"parametro": "E. coli", "conforme": True}],
                }
            ],
        },
    )
    client.post(
        "/api/v1/analisis",
        headers=headers_lab,
        json={
            "folio_analisis": "LAB-2026-AGU-6002-V1",
            "codigo_lote": "AGU-P018-260314-01",
            "tipo_estudio": "Residuos de Plaguicidas",
            "fecha_muestreo": "2026-03-20T11:00:00Z",
            "dictamen_general": "No Conforme",
            "laboratorio": {"nombre": "Lab AgroBio", "acreditacion_iso": "EMA-17025"},
            "muestras": [
                {
                    "identificador_muestra": "M-02",
                    "determinaciones": [{"molecula": "Clorpirifos", "conforme": False}],
                }
            ],
        },
    )

    filtered = client.get(
        "/api/v1/analisis/AGU-P018-260314-01?solo_no_conformes=true",
        headers=headers_qa,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["analisis"][0]["folio_analisis"] == "LAB-2026-AGU-6002-V1"


def test_cerrar_incidente_nonexistent_returns_404(client: TestClient, headers_qa: dict[str, str]):
    resp = client.patch(
        "/api/v1/incidentes/INC-2026-9999/cerrar",
        headers=headers_qa,
        json={
            "causa_raiz": "Causa raíz de prueba suficientemente detallada",
            "acciones_correctivas": ["Acción correctiva documentada en prueba"],
            "responsable_qa": "Ing. Valeria Mendoza",
            "aprobacion_gerencia": "Lic. Roberto Salas",
        },
    )
    assert resp.status_code == 404

