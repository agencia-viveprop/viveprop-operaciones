# Viveprop Operaciones

App interna que reemplaza el seguimiento en Excel de dos procesos:

- **Canjes** (programa Dataprop) — importación manual (no automática) de un `.xlsx` exportado desde producción.
- **Negocios** (pipeline propio de Viveprop) — entrada 100% manual, con cálculo de comisiones por modelo de negocio.

Ambos módulos comparten login, roles (`gerencia < operaciones < admin`) y una tabla de `movimientos` (línea de tiempo por entidad) en vez de campos que se sobrescriben.

Plan de arquitectura completo (esquema SQL, sprints, apéndice de seguridad): ver el plan de diseño de esta app (fuera de este repo).

## Estructura

```
backend/    FastAPI + SQLAlchemy + Alembic
frontend/   React + Vite + TypeScript + Mantine
```

## Desarrollo local

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp ../.env.example ../.env    # completar DATABASE_URL con una Neon de desarrollo
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Tests:**

```bash
cd backend
pytest
```

Los tests corren contra SQLite en memoria, nunca contra Neon. `DATABASE_URL` debe
apuntar a la rama `dev` de Neon para desarrollo -- la de `production` solo vive en
las variables de entorno de Render.

Ojo con el string de conexion: Neon entrega `postgresql://...` y SQLAlchemy necesita
el driver, asi que hay que reemplazar ese prefijo por `postgresql+psycopg://`.

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

El frontend en dev apunta a `/api` vía proxy de Vite hacia `http://localhost:8000`.

## Despliegue

Un solo Web Service en Render: build del frontend se copia a `backend/static/`, y FastAPI sirve tanto `/api/*` como el resto de rutas como SPA. Ver `render.yaml`.

Variables de entorno requeridas en Render: `DATABASE_URL` (Neon), `SESSION_SECRET`, `ALLOWED_ORIGINS`.
