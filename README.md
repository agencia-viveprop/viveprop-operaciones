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

**Ojo con el chequeo de tipos:** `npx tsc --noEmit` pasa en verde aunque haya
errores. El `tsconfig.json` de la raíz es un archivo de referencias y no incluye
ningún fuente, así que no revisa nada. El chequeo real es `npm run build`, que
corre `tsc -b`. Un archivo roto ya pasó ese falso verde una vez.

## Despliegue

Un solo Web Service en Render: build del frontend se copia a `backend/static/`, y FastAPI sirve tanto `/api/*` como el resto de rutas como SPA. Ver `render.yaml`.

Variables de entorno en Render:

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | La rama `production` de Neon. |
| `ALLOWED_ORIGINS` | Orígenes que acepta el CORS, separados por coma. **Al agregar un dominio propio hay que sumarlo acá** o el navegador rechaza las llamadas. |
| `ENVIRONMENT` | Decide si la cookie de sesión sale con `secure`. Solo `development`, `local` y `test` la desactivan; **cualquier otro valor, o su ausencia, deja la cookie segura** (`D-033`). No hace falta configurarla para estar seguro. |
| `SESSION_SECRET` | Declarada pero **el código nunca la lee**. Pendiente de limpiar. |
| `TAREAS_DE_FONDO` | Opcional. Apaga las tareas periódicas del proceso si se pone en `false`. Hoy la única es la descarga de UF. |

**La UF se actualiza sola.** Una tarea dentro del web service chequea una vez al día si a la serie le quedan menos de 20 días por delante y, si es así, baja lo que publica el SII (`D-036`, `D-037`). La fuente se verificó contra 617 fechas sin una diferencia. Hay además un botón para traer la historia completa, un año por página desde 2022, para una serie que arranque tarde. La carga manual de la plantilla se queda como respaldo para cuando el SII no esté o cambie su página, y los dos caminos escriben con el mismo upsert. Solo admin puede cargar UF (`D-038`).

**Carga masiva de negocios.** Botón *Carga masiva* en la pantalla de Negocios: baja una plantilla `.xlsx` con los códigos válidos de esta base y la vuelve a subir. Una fila es un hito, las tasas van en porcentaje y **las comisiones no se escriben** — las calcula el motor (`D-039`). No es la vía para los 19 históricos: esos van con `scripts/cargar_negocios.py`, que migra fiel sin recalcular.

**Reset de contraseña.** En *Usuarios*, el botón **Resetear** genera una clave temporal, la muestra una sola vez y cierra las sesiones de esa persona. Al entrar, la app le pide elegir una propia y **la API le devuelve 403 en todo** hasta que lo haga — el bloqueo está en `get_current_user`, no en la pantalla (`D-040`). Nadie puede resetear su propia clave: para eso está *Cambiar contraseña*.

**Health checks.** Son dos y miden cosas distintas (`D-035`):

- `GET /api/health` — el proceso está vivo, **y qué commit está corriendo**. No toca la base a propósito: Neon suspende la rama sin tráfico y un despertar lento se leería como servicio caído. Es el que mira Render (`healthCheckPath`). El `commit` sale de `RENDER_GIT_COMMIT` y sirve para confirmar en un segundo si lo desplegado es lo que se subió — cuando un deploy no cambia el frontend, el hash del bundle no alcanza para distinguirlo.
- `GET /api/health/db` — la base responde. `SELECT 1`, con 503 si falla. Para diagnosticar cuando la app carga pero ninguna pantalla trae datos.
