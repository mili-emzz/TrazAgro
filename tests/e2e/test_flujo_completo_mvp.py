import time

from fastapi.testclient import TestClient


def test_flujo_completo_mvp_cosecha_a_cierre_recall(
    client: TestClient,
    headers_productor_1: dict[str, str],
    headers_productor_2: dict[str, str],
    headers_recepcion: dict[str, str],
    headers_lab: dict[str, str],
    headers_qa: dict[str, str],
):
    # 1. COSECHA: Productor 1 registra dos lotes hermanos; Productor 2 registra uno para prueba RN-07
    lote_a = "AGU-P014-260320-01"
    lote_b = "AGU-P014-260320-02"
    lote_c = "AGU-P018-260320-01"

    for code, pid, headers in [
        (lote_a, 1, headers_productor_1),
        (lote_b, 1, headers_productor_1),
        (lote_c, 3, headers_productor_2),
    ]:
        r = client.post(
            "/api/v1/lotes",
            headers=headers,
            json={
                "codigo_lote": code,
                "parcela_id": pid,
                "producto": "Aguacate Hass",
                "fecha_cosecha": "2026-03-20T07:00:00Z",
                "cuadrilla_cosecha": "Cuadrilla E2E",
                "peso_inicial_kg": 2000.0,
            },
        )
        assert r.status_code == 201, r.text
        assert r.json()["estado"] == "Cosechado"
        assert r.json()["saldo_kg"] == 2000.0

    # 2. RECEPCIÓN CEDIS (RN-07):
    # Lote A y Lote B comparten camión MICH-842-K y cuarto frío CF-02 dentro de 4-8 °C
    for folio, code, temp in [
        ("REC-2026-0301", lote_a, 5.8),
        ("REC-2026-0302", lote_b, 6.1),
    ]:
        r_rec = client.post(
            "/api/v1/recepciones",
            headers=headers_recepcion,
            json={
                "folio_recepcion": folio,
                "codigo_lote": code,
                "placas_vehiculo": "MICH-842-K",
                "nombre_chofer": "Martín Morales",
                "codigo_cuarto_frio": "CF-02",
                "peso_recibido_kg": 1995.0,
                "temperatura_llegada_c": temp,
                "evaluacion_sensorial": {"color_epidermis": "Verde oscuro", "olor_extrano": False},
                "monitoreo_temperatura_caja": [{"zona_contenedor": "Centro", "temperatura_c": temp}],
            },
        )
        assert r_rec.status_code == 201, r_rec.text
        assert r_rec.json()["dictamen_recepcion"] == "Conforme"
        assert r_rec.json()["estado_lote_resultante"] == "Recibido"
        assert r_rec.json()["alerta_cadena_frio"] is False

    # Lote C llega a 11.4 °C -> RN-07 activa alerta de cadena de frío y lo retiene en 'En revision'
    r_rec_c = client.post(
        "/api/v1/recepciones",
        headers=headers_recepcion,
        json={
            "folio_recepcion": "REC-2026-0303",
            "codigo_lote": lote_c,
            "placas_vehiculo": "JAL-405-C",
            "nombre_chofer": "Héctor Vargas",
            "codigo_cuarto_frio": "CF-03",
            "peso_recibido_kg": 1990.0,
            "temperatura_llegada_c": 11.4,
            "evaluacion_sensorial": {"color_epidermis": "Verde opaco", "olor_extrano": False},
            "monitoreo_temperatura_caja": [{"zona_contenedor": "Puerta", "temperatura_c": 11.8}],
        },
    )
    assert r_rec_c.status_code == 201
    assert r_rec_c.json()["dictamen_recepcion"] == "Retenido"
    assert r_rec_c.json()["estado_lote_resultante"] == "En revision"
    assert r_rec_c.json()["alerta_cadena_frio"] is True

    # 3. LABORATORIO (RN-05) Y LIBERACIÓN QA (RN-02):
    # V1 No Conforme -> impide liberación
    r_v1 = client.post(
        "/api/v1/analisis",
        headers=headers_lab,
        json={
            "folio_analisis": "LAB-2026-AGU-3001-V1",
            "codigo_lote": lote_a,
            "tipo_estudio": "Residuos de Plaguicidas",
            "fecha_muestreo": "2026-03-20T15:00:00Z",
            "dictamen_general": "No Conforme",
            "laboratorio": {"nombre": "Lab AgroBio S.A. de C.V.", "acreditacion_iso": "EMA-ISA-17025-2024"},
            "muestras": [
                {
                    "identificador_muestra": "M-01",
                    "determinaciones": [
                        {
                            "molecula": "Clorpirifos",
                            "resultado_mg_kg": 0.08,
                            "limite_maximo_mg_kg": 0.01,
                            "conforme": False,
                        }
                    ],
                }
            ],
        },
    )
    assert r_v1.status_code == 201
    assert r_v1.json()["version"] == 1

    # QA intenta liberar -> 409 por RN-02
    r_lib_fail = client.patch(
        f"/api/v1/lotes/{lote_a}/liberar",
        headers=headers_qa,
        json={"motivo": "Intento de liberación con análisis No Conforme"},
    )
    assert r_lib_fail.status_code == 409

    # Enmienda V2 sin motivo -> 400 (RN-05)
    r_v2_no_motivo = client.post(
        "/api/v1/analisis",
        headers=headers_lab,
        json={
            "folio_analisis": "LAB-2026-AGU-3001-V2",
            "codigo_lote": lote_a,
            "tipo_estudio": "Residuos de Plaguicidas",
            "fecha_muestreo": "2026-03-20T18:00:00Z",
            "dictamen_general": "Conforme",
            "laboratorio": {"nombre": "Lab AgroBio S.A. de C.V.", "acreditacion_iso": "EMA-ISA-17025-2024"},
            "muestras": [
                {
                    "identificador_muestra": "M-01-R",
                    "determinaciones": [{"molecula": "Clorpirifos", "resultado_mg_kg": 0.004, "limite_maximo_mg_kg": 0.01, "conforme": True}],
                }
            ],
        },
    )
    assert r_v2_no_motivo.status_code == 400

    # Enmienda V2 con motivo_enmienda -> 201, V1 queda inmutable con es_vigente=False
    r_v2 = client.post(
        "/api/v1/analisis",
        headers=headers_lab,
        json={
            "folio_analisis": "LAB-2026-AGU-3001-V2",
            "codigo_lote": lote_a,
            "tipo_estudio": "Residuos de Plaguicidas",
            "fecha_muestreo": "2026-03-20T18:00:00Z",
            "motivo_enmienda": "Recalibración cromatógrafo confirmando lectura dentro de LMR",
            "dictamen_general": "Conforme",
            "laboratorio": {"nombre": "Lab AgroBio S.A. de C.V.", "acreditacion_iso": "EMA-ISA-17025-2024"},
            "muestras": [
                {
                    "identificador_muestra": "M-01-R",
                    "determinaciones": [{"molecula": "Clorpirifos", "resultado_mg_kg": 0.004, "limite_maximo_mg_kg": 0.01, "conforme": True}],
                }
            ],
        },
    )
    assert r_v2.status_code == 201
    assert r_v2.json()["version"] == 2
    assert r_v2.json()["folio_reemplazado"] == "LAB-2026-AGU-3001-V1"

    # Historial conserva ambas versiones (RN-05)
    hist = client.get(f"/api/v1/analisis/{lote_a}", headers=headers_qa).json()
    assert hist["total"] == 2
    assert sum(1 for a in hist["analisis"] if a["es_vigente"]) == 1

    # Ahora QA libera el lote A
    r_lib = client.patch(
        f"/api/v1/lotes/{lote_a}/liberar",
        headers=headers_qa,
        json={"motivo": "Cumple RN-02 tras enmienda V2 conforme"},
    )
    assert r_lib.status_code == 200
    assert r_lib.json()["estado_actual"] == "Liberado"

    # 4. DESPACHO FRACCIONADO (RN-01, RN-03): 450 kg a Tienda 1
    r_env = client.post(
        "/api/v1/envios",
        headers=headers_recepcion,
        json={
            "codigo_envio": "ENV-2026-3001",
            "tienda_id": 1,
            "placas_vehiculo": "TRK-884-A",
            "nombre_chofer": "Luis Estrada",
            "detalles": [{"codigo_lote": lote_a, "cantidad_kg": 450.0}],
        },
    )
    assert r_env.status_code == 201
    assert r_env.json()["saldos_actualizados"][0]["saldo_kg_restante"] == 1550.0

    # 5. EXPEDIENTE 360° Y TRAZABILIDAD (con medición de latencia)
    t0 = time.perf_counter()
    r_360 = client.get(f"/api/v1/lotes/{lote_a}", headers=headers_qa)
    lat_360_ms = (time.perf_counter() - t0) * 1000
    assert r_360.status_code == 200
    assert lat_360_ms < 200.0
    exp_360 = r_360.json()
    assert exp_360["lote"]["saldo_kg"] == 1550.0
    assert exp_360["acta_recepcion"]["folio_recepcion"] == "REC-2026-0301"
    assert len(exp_360["analisis_laboratorio"]) == 2
    assert exp_360["red_trazabilidad"]["envios_tiendas"][0]["codigo_sucursal"] == "SUC-MTY-04"

    r_fwd = client.get(f"/api/v1/trazabilidad/{lote_a}/adelante", headers=headers_qa)
    assert r_fwd.status_code == 200
    assert r_fwd.json()["total_kg_despachados"] == 450.0

    r_lat = client.get(f"/api/v1/trazabilidad/{lote_a}/atras-lateral", headers=headers_qa)
    assert r_lat.status_code == 200
    hermanos_codes = [h["codigo_lote"] for h in r_lat.json()["lotes_hermanos"]]
    assert lote_b in hermanos_codes

    # 6. RECALL INTEGRADO (RN-08): bloquea Lote A + hermano Lote B, identifica tienda y abre expediente
    t1 = time.perf_counter()
    r_recall = client.post(
        "/api/v1/incidentes/recall",
        headers=headers_qa,
        json={
            "folio_incidente": "INC-2026-3001",
            "codigo_lote_origen": lote_a,
            "motivo": "Alerta sanitaria microbiológica posterior a despacho",
            "incluir_lotes_hermanos": True,
            "ventana_dias_contaminacion": 1,
        },
    )
    lat_recall_ms = (time.perf_counter() - t1) * 1000
    assert r_recall.status_code == 201
    assert lat_recall_ms < 150.0
    recall_body = r_recall.json()
    assert recall_body["lote_origen"]["estado_actual"] == "Bloqueado"
    assert recall_body["lote_origen"]["saldo_inmovilizado_kg"] == 1550.0
    assert any(h["codigo_lote"] == lote_b for h in recall_body["lotes_hermanos_bloqueados"])
    assert recall_body["tiendas_afectadas"][0]["codigo_sucursal"] == "SUC-MTY-04"

    # Nuevo despacho sobre lote bloqueado debe fallar con 409 (RN-01)
    r_blocked_env = client.post(
        "/api/v1/envios",
        headers=headers_recepcion,
        json={
            "codigo_envio": "ENV-2026-3002",
            "tienda_id": 1,
            "placas_vehiculo": "TRK-884-A",
            "nombre_chofer": "Luis Estrada",
            "detalles": [{"codigo_lote": lote_a, "cantidad_kg": 100.0}],
        },
    )
    assert r_blocked_env.status_code == 409

    # 7. CIERRE DE INCIDENTE (RN-09)
    r_close = client.patch(
        "/api/v1/incidentes/INC-2026-3001/cerrar",
        headers=headers_qa,
        json={
            "causa_raiz": "Contaminación cruzada en línea de empaque antes del embarque",
            "acciones_correctivas": [
                "Sanitización profunda de banda transportadora y cuarto frío CF-02",
                "Retiro confirmado de 450 kg en SUC-MTY-04",
            ],
            "responsable_qa": "Ing. Valeria Mendoza",
            "aprobacion_gerencia": "Lic. Roberto Salas",
        },
    )
    assert r_close.status_code == 200
    assert r_close.json()["estado_expediente"] == "Cerrado"
    assert r_close.json()["sincronizacion"]["postgresql"] == "confirmado"
    assert r_close.json()["sincronizacion"]["neo4j"] == "sincronizado"
