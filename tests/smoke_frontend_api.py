import httpx

base = "http://127.0.0.1:8000/api/v1"

# 1. Health
r = httpx.get(f"{base}/health")
print("1. HEALTH:", r.status_code, r.json()["status"], r.json()["databases"])

# 2. Login all 5 roles
roles = [
    ("qa_admin", "TrazaQA2026!"),
    ("recepcion_cedis", "TrazaRec2026!"),
    ("lab_agrobio", "TrazaLab2026!"),
    ("productor_michoacan", "TrazaProd1!"),
    ("productor_tancitaro", "TrazaProd2!"),
]
tokens = {}
for u, p in roles:
    res = httpx.post(f"{base}/auth/login", json={"username": u, "password": p})
    assert res.status_code == 200, f"Failed login {u}: {res.text}"
    user_info = res.json()["user"]
    tokens[u] = res.json()["access_token"]
    print(f"2. LOGIN {u}: 200 OK | Rol: {user_info['role']} | ProductorID: {user_info['productor_id']}")

# 3. Productor flow: listar lotes
h_prod = {"Authorization": f"Bearer {tokens['productor_michoacan']}"}
lotes_prod = httpx.get(f"{base}/lotes", headers=h_prod).json()
print("3. PRODUCTOR LOTES COUNT:", len(lotes_prod))
assert len(lotes_prod) > 0

# 4. CEDIS flow: listar lotes
h_rec = {"Authorization": f"Bearer {tokens['recepcion_cedis']}"}
lotes_rec = httpx.get(f"{base}/lotes", headers=h_rec).json()
print("4. CEDIS LOTES COUNT:", len(lotes_rec))
assert len(lotes_rec) >= len(lotes_prod)

# 5. QA flow - Trazabilidad & Multimotor (usando las rutas exactas del frontend)
h_qa = {"Authorization": f"Bearer {tokens['qa_admin']}"}
exp = httpx.get(f"{base}/lotes/AGU-P014-260312-01", headers=h_qa)
print("5. QA EXPEDIENTE 360 (/api/v1/lotes/{codigo}):", exp.status_code, "LOTE:", exp.json().get("lote", {}).get("codigo_lote"))
assert exp.status_code == 200

adelante = httpx.get(f"{base}/trazabilidad/AGU-P014-260312-01/adelante", headers=h_qa)
print("   QA RED ADELANTE (/api/v1/trazabilidad/{codigo}/adelante):", adelante.status_code, "TIENDAS:", len(adelante.json().get("tiendas_afectadas", [])))
assert adelante.status_code == 200

atras = httpx.get(f"{base}/trazabilidad/AGU-P014-260312-01/atras-lateral?ventana_dias=1", headers=h_qa)
print("   QA RED ATRAS/LATERAL (/api/v1/trazabilidad/{codigo}/atras-lateral):", atras.status_code, "CONTAMINACION CRUZADA:", len(atras.json().get("lotes_contaminacion_cruzada", [])))
assert atras.status_code == 200

# 6. Lab flow: consultar análisis
h_lab = {"Authorization": f"Bearer {tokens['lab_agrobio']}"}
analisis = httpx.get(f"{base}/analisis/AGU-P014-260312-01", headers=h_lab)
print("6. LAB ANALISIS LOTE (/api/v1/analisis/{codigo}):", analisis.status_code, "DOCUMENTOS:", len(analisis.json().get("analisis", [])))
assert analisis.status_code == 200

print("\n--- TODOS LOS ENDPOINTS CLAVE DEL FRONTEND RESPONDEN 200 OK EXITOSAMENTE ---")
