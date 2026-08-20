# Estados de avance · ViveProp Operaciones

Registro del avance en la ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Decisiones tomadas durante la ejecución: [decisiones.md](decisiones.md).

**Última actualización:** 2026-08-20 (sprint 1 listo)

---

## Resumen

| | Cantidad |
|---|---|
| Sprints del plan | 22 |
| Listos | 1 |
| En curso | 0 |
| Pendientes | 21 |
| Bloqueados | 0 |

**Sprint actual:** ninguno. El sprint 1 quedó **Listo**. El siguiente en el orden es el 2 (G2 · Despliegue en Render), pendiente de autorización.

---

## Avance en porcentaje

Cuenta sprints, no esfuerzo: el sprint 7 (motor de comisiones) pesa mucho más que
el 3 (cargar la tabla de UF). Sirve como avance de hitos, no de horas.

| Lectura | Listos | Total | % |
|---|---:|---:|---:|
| **Camino crítico** (1, 3–13) | 1 | 12 | **8,3%** |
| Plan completo | 1 | 22 | 4,5% |
| Proyecto entero (incluye los 9 sprints previos en producción) | 10 | 31 | 32% |

| Serie | Listos | Total | % | Sprints |
|---|---:|---:|---:|---|
| **C** · Cimientos | 1 | 4 | 25% | 1, 3, 4, 5 |
| **G** · Acceso y despliegue | 0 | 2 | 0% | 2, 22 |
| **D** · Negocios | 0 | 6 | 0% | 6–11 |
| **F** · Reportería | 0 | 5 | 0% | 12, 13, 16–18 |
| **E** · Carga masiva | 0 | 2 | 0% | 14, 15 |
| **B** · Gestión de canjes | 0 | 3 | 0% | 19–21 |

Distancia a los hitos visibles: **8 sprints** hasta la pantalla de Negocios (9) y
**12** hasta su dashboard (13). Entre el 2 y el 8 no hay cambios visibles en la app.

---

## Estados posibles

| Estado | Significado |
|---|---|
| `Pendiente` | No autorizado ni iniciado. |
| `Autorizado` | El usuario dio el visto bueno explícito, aún no comienza. |
| `En curso` | En desarrollo. |
| `Listo` | Cumple su criterio de "listo cuando" y está commiteado. |
| `Bloqueado` | Autorizado pero detenido por una dependencia externa. Indicar cuál. |
| `Diferido` | Sacado del orden por decisión del usuario. Registrar el motivo en `decisiones.md`. |

---

## Plan en ejecución

| # | Sprint | Estado | Fecha | Commit | Notas |
|---|---|---|---|---|---|
| 1 | C1 · Ambiente dev y red de seguridad | **Listo** | 2026-08-20 | — | 7 tests del importador pasando. `dev` operativa. Binarios fuera del repo. |
| 2 | G2 · Despliegue en Render | Pendiente | — | — | |
| 3 | C2 · Tabla UF y conversión | Pendiente | — | — | |
| 4 | C3 · Catálogos | Pendiente | — | — | |
| 5 | C4 · Plantilla y carga manual de UF | Pendiente | — | — | |
| 6 | D1 · Esquema de negocios | Pendiente | — | — | |
| 7 | D2 · Motor de comisiones | Pendiente | — | — | Decisión pendiente: `% Broker` en arriendo. |
| 8 | D3 · CRUD backend | Pendiente | — | — | |
| 9 | D4 · Pantalla Negocios | Pendiente | — | — | Primer hito visible. |
| 10 | D5 · Carga de los 19 históricos | Pendiente | — | — | Decisión pendiente: tasas de rebate y motivos de pérdida. |
| 11 | D6 · Pipeline de negocios | Pendiente | — | — | |
| 12 | F1 · Base de cálculo | Pendiente | — | — | |
| 13 | F2 · Dashboard de negocios | Pendiente | — | — | Segundo hito visible. |
| 14 | E1 · Plantilla de negocios | Pendiente | — | — | |
| 15 | E2 · Importador de negocios | Pendiente | — | — | |
| 16 | F3 · Reporte semanal | Pendiente | — | — | |
| 17 | F4 · Reporte mensual comparativo | Pendiente | — | — | |
| 18 | F5 · Vista directorio | Pendiente | — | — | Decisión pendiente: contenido para el directorio. |
| 19 | B5 · Registrar movimientos en canjes | Pendiente | — | — | |
| 20 | B6 · Semáforo y bandeja diaria | Pendiente | — | — | |
| 21 | B7 · Migrar el seguimiento histórico | Pendiente | — | — | |
| 22 | G1 · Recuperación de contraseña | Pendiente | — | — | Disparador: antes de crear la tercera cuenta de usuario. |

---

## Sprints anteriores al plan (ya en producción)

Base sobre la que se construye. Verificado en el historial de git al 2026-08-20.

| Sprint | Estado | Commit | Qué dejó |
|---|---|---|---|
| A1 · Esqueleto backend y frontend | Listo | `7be8a13` | FastAPI + Alembic, Vite + React + Mantine. |
| A2 · Usuarios y sesiones | Listo | `ec3df77` | Login con Argon2id, cookie de sesión en base. |
| A3 · Jerarquía de roles | Listo | `fdcda21` | `gerencia < operaciones < admin` + mantenedor de usuarios. |
| A4 · Tema Mantine | Listo | `714caab` | Paleta, sidebar, modo oscuro. |
| B1 · Esquema de canjes | Listo | `866e391` | Tabla `canjes`, CRUD y listado con filtros. |
| B2 · Importar Canjes | Listo | `d5cd7cd` | Upsert desde el `.xlsx` de Dataprop. |
| B3 · Movimientos | Listo | `30ea66a` | Tabla `movimientos`, catálogo `tipos_movimiento`, modal de seguimiento. |
| B4 · Dashboard de canjes | Listo | `233a8f6` | Reportes y resumen de canjes. |
| — · Branding | Listo | `1906091` | Logo, paleta y tipografías oficiales. |

Fuera de sprint: cambio de contraseña propia (`393fa3e`), fix de edición de email (`75831c0`), fix del seed de `tipos_movimiento` contra Postgres (`107f3c0`).

---

## Bitácora

Entradas en orden inverso (lo más reciente arriba). Formato:

```
### AAAA-MM-DD · Sprint N (código) — <estado nuevo>
Qué se hizo. Qué quedó verificado. Qué quedó pendiente o cambió respecto del plan.
```

### 2026-08-20 · Sprint 1 (C1) — Listo

**Ambiente.** `backend/.env` apunta a la rama `dev` y la app arranca contra ella: verificado que `engine.url.host` es `ep-summer-brook-ay3dg8nw-pooler`, backend en 8000 respondiendo `{"status":"ok"}`, `/api/canjes` devolviendo 401 sin sesión, frontend en 5173. `alembic upgrade head` contra `dev` es no-op: ya estaba en `b2dbf50bc5fc`.

**Tests.** `pytest>=8.3.3` en `requirements.txt` (instalado 9.1.1), `pytest.ini` con `pythonpath = .`, y `backend/tests/` con `conftest.py` más `test_importar_canjes.py`. **7 tests, todos pasando.** Corren contra SQLite en memoria creando solo la tabla `canjes` — se evita `sesiones`, que usa el UUID del dialecto de Postgres, y nunca se toca el engine de `app.db`, así que un test no puede escribir en Neon.

Los casos cubren: mapeo de campos en alta, actualización al reimportar, respeto de `gestionado_en_app`, falta de columna requerida, una fila inválida que no frena a las demás, y etapa vacía cayendo en `SIN_ETAPA`. El más importante es `test_la_importacion_no_toca_estado_ni_etapa`: fija la regla de que estado y etapa los gobierna la app y no el archivo, que hasta ahora solo existía como comentario en el código.

**Repo.** `.tmp_screenshots/` y los dos `.jpeg` de la raíz salieron del control de versiones con `git rm --cached` — siguen en disco. Agregados al `.gitignore` como `.tmp_screenshots/` y `/*.jpeg` con ancla de raíz, para no afectar assets legítimos del frontend. Nota: los ~420 KB ya commiteados siguen en el historial; sacarlos de ahí requeriría reescribirlo y no se hizo.

**README.** Documentado cómo correr los tests y la trampa del string de conexión de Neon (hay que reemplazar `postgresql://` por `postgresql+psycopg://`, porque el proyecto usa psycopg 3).

### 2026-08-20 · Sprint 1 (C1) — desbloqueado, sin iniciar

Rama `dev` creada en Neon (`br-proud-sky-aykcfakh`, host `ep-summer-brook-ay3dg8nw-pooler`, Postgres 18.6). Por copy-on-write heredó los datos de producción: 297 canjes, 14 tipos de movimiento, 2 usuarios, 0 movimientos. Alembic quedó en `b2dbf50bc5fc`, la misma versión que producción — no hay migraciones por aplicar.

Eso resuelve de hecho la decisión pendiente del sprint 1: `dev` quedó **con los datos reales heredados**, no solo con el esquema.

`backend/.env` ahora apunta a `dev`. Al pegar el string de Neon había quedado el esquema duplicado (`postgresql+psycopg:postgresql://`), que SQLAlchemy no podía parsear; corregido a `postgresql+psycopg://` y conexión verificada. Respaldo del archivo previo en `backend/.env.antes-de-fix` (ignorado por git). El `.env` ya no contiene el string de producción, que sigue vivo en las variables de entorno de Render.

Ningún sprint iniciado. Sin código escrito.

### 2026-08-20 · Planificación — plan aprobado en estructura

Auditoría completa del Excel `GESTION_OPERACIONES_VIVEPROP.xlsx` (7 hojas) y de la base de Neon. Se levantaron las reglas de negocio no documentadas (arriendo 50/50, rebate del concentrador, comisión potencial en negocios perdidos) y se verificó que la aritmética de comisiones del Excel cuadra al peso en las 19 filas, lo que habilita usarlas como tests de regresión.

Plan cerrado en 22 sprints y 6 series, con orden de ejecución definido. Sin código escrito.
