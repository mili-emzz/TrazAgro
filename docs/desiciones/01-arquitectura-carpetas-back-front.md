# Backend: Python con FastAPI

backend/
├── controllers/            # Routers FastAPI: HTTP, JWT/RBAC, entrada/salida
├── schemas/                # Modelos Pydantic (contratos de la API)
├── services/               # Reglas de negocio (RN-01…RN-11) y orquestación
├── repositories/
│   ├── relational/         # PostgreSQL (psycopg)
│   ├── document/           # MongoDB (PyMongo)
│   └── graph/              # Neo4j (driver Bolt)
├── core/                   # Config, variables de entorno, pools de conexión
└── main.py                 # Arranque de la app

# Frontend: React + Vite (SPA) 
✅	Ligero, arranca rápido y encaja con tu backend separado. Las vistas son paneles internos por rol, sin necesidad de SEO.

Librerías recomendadas, una por necesidad:

React Router para la navegación por rol.
TanStack Query para consumir la API (caché, cargando, errores).
React Hook Form + Zod para los formularios de recepción, laboratorio y despacho.
React Flow o react-force-graph para el visor de la red de recall.
Tailwind para la interfaz.

frontend/
├── pages/                  # Vistas por rol, Expediente 360°, Consola Recall  (≈ controllers)
├── components/             # Formularios, tablas, visor de grafo
├── hooks/                  # Lógica reutilizable con TanStack Query (≈ services)
├── api/                    # Cliente HTTP hacia FastAPI (≈ repositories)
├── auth/                   # Manejo del JWT, rutas protegidas por rol
├── types/                  # Tipos TypeScript de los contratos de la API
└── main.tsx                # Arranque y rutas

El flujo de datos es el mismo en ambos lados, de arriba hacia abajo:

Backend: controller → service → repository → BD
Frontend: page → hook → api → backend