# Estados de avance · ViveProp Operaciones

Registro del avance en la ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Decisiones tomadas durante la ejecución: [decisiones.md](decisiones.md). Diseño del esquema: [diseno_modelo_datos.md](diseno_modelo_datos.md).

**Última actualización:** 2026-08-20 (sprints 1 y 3 listos)

---

## Resumen

| | Cantidad |
|---|---|
| Sprints del plan | 22 |
| Listos | 2 |
| En curso | 0 |
| Pendientes | 20 |
| Bloqueados | 0 |

**Sprint actual:** ninguno. Listos el 1 y el 3. El 2 (Render) está **esperando el diagnóstico del 503** desde la consola de Render. El siguiente autorizable sin bloqueos es el 4 (C3 · Catálogos).

---

## Avance en porcentaje

Cuenta sprints, no esfuerzo: el sprint 7 (motor de comisiones) pesa mucho más que
el 3 (cargar la tabla de UF). Sirve como avance de hitos, no de horas.

| Lectura | Listos | Total | % |
|---|---:|---:|---:|
| **Camino crítico** (1, 3–13) | 2 | 12 | **16,7%** |
| Plan completo | 2 | 22 | 9,1% |
| Proyecto entero (incluye los 9 sprints previos en producción) | 11 | 31 | 35% |

| Serie | Listos | Total | % | Sprints |
|---|---:|---:|---:|---|
| **C** · Cimientos | 2 | 4 | 50% | 1, 3, 4, 5 |
| **G** · Acceso y despliegue | 0 | 2 | 0% | 2, 22 |
| **D** · Negocios | 0 | 6 | 0% | 6–11 |
| **F** · Reportería | 0 | 5 | 0% | 12, 13, 16–18 |
| **E** · Carga masiva | 0 | 2 | 0% | 14, 15 |
| **B** · Gestión de canjes | 0 | 3 | 0% | 19–21 |

Distancia a los hitos visibles: **7 sprints** hasta la pantalla de Negocios (9) y
**11** hasta su dashboard (13). Entre el 2 y el 8 no hay cambios visibles en la app.

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
| 2 | G2 · Despliegue en Render | Pendiente | — | — | Render devuelve 503. Requiere diagnóstico del usuario antes de arrancar. |
| 3 | C2 · Tabla UF y conversión | **Listo** | 2026-08-20 | — | 1.409 filas en `dev`. 12 tests. Reproduce la columna AC al peso. |
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

### 2026-08-20 · D0 — documento de diseño del modelo entregado para revisión

Escrito [diseno_modelo_datos.md](diseno_modelo_datos.md), que cubre los sprints 4 y 6. No hay código asociado. Propone: catálogos en tabla genérica con `etapas` aparte y `modelo_negocio` como enum; tabla `propiedades` para detectar reintentos; y **dos tablas (`negocios` + `negocio_hitos`) en vez de la autorreferencia que asumía `D-013`**, porque sumar hitos hace imposible el doble conteo en vez de solo evitable.

Deja **6 preguntas abiertas**. La número 1 bloquea el sprint 7: en el modelo Concentradores no se puede determinar leyendo el Excel qué columna de porcentaje alimenta qué monto — la Comisión Broker de VVP-4 sale de 0,008 y no del 0,012 de la columna llamada "% Broker".

**Se corrige otro dato de esta sesión:** se había reportado que la tasa de rebate del concentrador nunca se registró. Es falso — la columna AG vale 0,12 en las 13 filas, y la regla es 12% de la Comisión Total. Eso saca una pregunta de la lista del sprint 10.

Los servidores locales quedaron corriendo contra `dev`. Migración `a1c4e7d92b30` verificada reversible, y las 1.409 filas de UF en `dev` son idénticas al Excel fila por fila.

### 2026-08-20 · Diseño — D-017, el valor en pesos puede ser manual

Felipe corrigió un supuesto del modelo: la valorización por regla (monto en UF × UF de la fecha) es un default, no la verdad. En Mercado Primario y Assetplan el valor en pesos lo determinan liquidaciones externas que muchas veces no coinciden.

Verificado sobre las 19 filas: **17 siguen la regla, 2 no.** VVP-2 tiene su comisión calculada sobre 81.505.175 en vez de 104.100.248 (−21,7%), con la observación *"hubo ajustes por costo credito pie ultima hora"* — el caso de valor externo. VVP-16 tiene base exactamente la mitad, con % declarado 0,04 y cobrado 0,02, que no es valor externo sino medio porcentaje y hay que preguntarlo.

**Se corrige un diagnóstico previo de esta misma sesión:** se había reportado que VVP-15 y VVP-17 tenían la UF mal capturada. Es falso — ambos siguen la regla y la diferencia de 5,38 pesos era redondeo.

Impacto: campos nuevos en el sprint 6 (`valor_clp_manual`, `motivo_valor_manual`), y los 19 tests de regresión del sprint 7 corren sobre la base de comisión y no sobre la conversión por UF.

### 2026-08-20 · Sprint 3 (C2) — Listo

**Modelo.** Tabla `uf_diaria(fecha PK, valor NUMERIC(12,2), actualizado_en)` y migración `a1c4e7d92b30`, aplicada a `dev`. **No está en producción todavía** — entra cuando se despliegue. `fecha` como clave primaria es lo que hace que la carga mensual sea un upsert y que subir meses solapados no duplique.

**Datos.** 1.409 filas cargadas desde 2022-11-01 hasta 2026-09-09, vía `app/scripts/cargar_uf.py`, que lee la hoja `UF` del Excel y hace upsert con `ON CONFLICT`.

**Servicio.** `app/services/uf.py` con `valor_uf`, `uf_a_clp`, `clp_a_uf`, `rango` y `dias_de_colchon`. Ver `D-016`: ninguna conversión sin fecha, y `Decimal` en todo el camino.

**Criterio de listo cumplido, y corregido.** El criterio que estaba escrito en el plan (6.088,44 UF al 2025-12-16) era **incorrecto**: VVP-3 PROMESA usa una UF que no existe en la serie. Se reemplazó por VVP-4, que sí es verificable. La conversión reproduce la columna AC del Excel al peso en cuatro negocios reales: VVP-4 (42.914.480,40), VVP-1 (132.739.562,16), VVP-2 (104.100.248,323) y VVP-19 en arriendo (1.096.945,74). Ida y vuelta sin pérdida.

**Tests.** 12 nuevos, total **19 pasando**. Los montos esperados no son inventados: son la columna AC de negocios reales.

**Hallazgo para el sprint 10.** Levantando el criterio apareció la regla de la columna AB: usa la UF de `Fecha Valorización` si está poblada, si no la de `Fecha_Inicio`. Exacta en 16 de 19 filas. Las 3 excepciones quedaron documentadas en el plan — VVP-15 y VVP-17 tienen la UF del día en que se editó la planilla, y VVP-3 PROMESA una que no existe en la serie.

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
