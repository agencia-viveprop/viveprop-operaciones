# Estados de avance · ViveProp Operaciones

Registro del avance en la ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Decisiones tomadas durante la ejecución: [decisiones.md](decisiones.md). Diseño del esquema: [diseno_modelo_datos.md](diseno_modelo_datos.md).

**Última actualización:** 2026-08-21 (sprints 1, 3 y 4 listos)

---

## Resumen

| | Cantidad |
|---|---|
| Sprints del plan | 22 |
| Listos | 3 |
| En curso | 0 |
| Pendientes | 19 |
| Bloqueados | 0 |

**Sprint actual:** ninguno. Listos el 1, el 3 y el 4. Sin bloqueos ni decisiones pendientes. El siguiente en el orden aprobado es el **6 (D1 · Esquema de negocios)**, con especificación cerrada en `D-020`.

---

## Avance en porcentaje

Cuenta sprints, no esfuerzo: el sprint 7 (motor de comisiones) pesa mucho más que
el 3 (cargar la tabla de UF). Sirve como avance de hitos, no de horas.

| Lectura | Listos | Total | % |
|---|---:|---:|---:|
| **Camino crítico** (1, 3–13) | 3 | 12 | **25,0%** |
| Plan completo | 3 | 22 | 13,6% |
| Proyecto entero (incluye los 9 sprints previos en producción) | 12 | 31 | 39% |

| Serie | Listos | Total | % | Sprints |
|---|---:|---:|---:|---|
| **C** · Cimientos | 3 | 4 | 75% | 1, 3, 4, 5 |
| **G** · Acceso y despliegue | 0 | 2 | 0% | 2, 22 |
| **D** · Negocios | 0 | 6 | 0% | 6–11 |
| **F** · Reportería | 0 | 5 | 0% | 12, 13, 16–18 |
| **E** · Carga masiva | 0 | 2 | 0% | 14, 15 |
| **B** · Gestión de canjes | 0 | 3 | 0% | 19–21 |

Distancia a los hitos visibles: **4 sprints** hasta la pantalla de Negocios y
**7** hasta su dashboard, en el orden aprobado el 2026-08-21. Entre el 2 y el 8 no hay cambios visibles en la app.

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
| 2 | G2 · Despliegue en Render | Pendiente | — | — | **Desbloqueado.** El servicio está sano; el 503 era transitorio. |
| 3 | C2 · Tabla UF y conversión | **Listo** | 2026-08-20 | — | 1.409 filas en `dev`. 12 tests. Reproduce la columna AC al peso. |
| 4 | C3 · Catálogos | **Listo** | 2026-08-21 | — | 10 tests. 27 filas sembradas, endpoint con 9 grupos. |
| 5 | C4 · Plantilla y carga manual de UF | Pendiente | — | — | |
| 6 | D1 · Esquema de negocios | Pendiente | — | — | Especificación aprobada en `D-020`. Listo para autorizar. |
| 7 | D2 · Motor de comisiones | Pendiente | — | — | **Sin decisiones pendientes.** `D-018` y `D-022`. |
| 8 | D3 · CRUD backend | Pendiente | — | — | |
| 9 | D4 · Pantalla Negocios | Pendiente | — | — | Primer hito visible. |
| 10 | D5 · Carga de los 19 históricos | Pendiente | — | — | Solo queda pendiente los 10 motivos de pérdida. |
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

### 2026-08-21 · Sprint 4 (C3) — Listo

**Modelo.** `catalogos(id, tipo, codigo, nombre, orden, activo, metadatos)` con `UNIQUE (tipo, codigo)` e índice en `tipo`, más `etapas(codigo PK, nombre, responsable, orden, activo)`. Migración `c8f2b41d7e05`, aplicada a `dev` y **verificada reversible**. El `metadatos` es `JSONB` en Postgres con variante `JSON` en SQLite, para poder crear la tabla en la base de test sin renunciar al tipo nativo.

**Enums en código, no en catálogo** (`D-021`): `ModeloNegocio` (3) y `EstadoNegocio` (4). El tipo de Postgres se crea en el sprint 6, junto con la tabla que lo usa. Se agregó también `ResponsableEtapa`.

**Seed desde `CONFIG`**, dentro de la migración siguiendo la convención de `b2dbf50bc5fc`: 8 alianzas —cada una con su modelo de negocio en `metadatos`—, 11 estados de facturación, 2 tipos de propiedad, 2 de operación, 2 de estado de propiedad, y las 7 etapas con su responsable. `motivo_perdida` queda vacío por `D-023`.

**Endpoint.** `GET /api/catalogos` devuelve los nueve grupos en una llamada, para que ningún formulario tenga que orquestar cinco peticiones. Más `GET /api/catalogos/{tipo}`, que ante un tipo desconocido responde 404 diciendo cuáles son los válidos.

**Tests: 10 nuevos, total 29 pasando.** Se agregó infraestructura reutilizable: `httpx` en requirements y un fixture `cliente` que da un `TestClient` con la base en memoria y la autenticación sobreescrita. Eso deja los endpoints testeables de aquí en adelante. Un test verifica que sin ese override el endpoint responde 401.

**Detalle técnico que costó encontrar:** la base SQLite en memoria necesita `StaticPool` y `check_same_thread=False`, porque `TestClient` corre la app en otro hilo y con el pool por defecto abriría una conexión nueva sin las tablas.

**Corrección:** los estados de facturación son **11**, no 12 como se había dicho varias veces.

### 2026-08-21 · D-023 — cero pendientes del usuario

Felipe resolvió que `motivo_perdida` es opcional y que no se completan los 10 históricos. Se implementa como catálogo más texto libre, para que los motivos sean comparables cuando se usen.

Con eso **no queda nada pendiente de Felipe en todo el plan**: ni decisiones de diseño, ni datos que consultar, ni bloqueos de infraestructura. Los 22 sprints esperan solo autorización.

Consecuencia aceptada: el análisis de por qué mueren los negocios en E2 no tendrá base retroactiva. Los 4,75M de comisión potencial perdida se van a poder contar pero no explicar.

### 2026-08-21 · Render está sano — el 503 era transitorio

Reverificado el servicio de producción: **HTTP 200** en la raíz y en `/api/health`, **401** en `/api/canjes` sin sesión, y ~200 ms de respuesta sin arranque en frío. El dashboard de Render confirma "All services are up and running".

**Se corrige el reporte del 2026-08-20**, que decía que el servicio estaba caído o el deploy había fallado. Era un 503 transitorio, probablemente el servicio despertando de estar dormido, y se resolvió solo. No hubo nada que arreglar.

El sprint 2 se desbloquea y se encoge: queda solo lo que se quería agregar — dominio propio, health check en la configuración, cookie `secure` por defecto, y cambiar el `<title>` del HTML, que dice `frontend` porque es el default de Vite que nunca se tocó.

**Con esto no queda ningún bloqueo en el plan.**

### 2026-08-21 · D-022 — el motor de comisiones queda sin decisiones pendientes

Felipe confirmó que el `% Broker` en arriendo funciona igual que en ventas: se aplica sobre la base, no sobre la comisión. Eso cierra la última ambigüedad del motor y elimina una rama condicional — la fórmula es `base × pct_broker` en los tres modelos.

Ya no hace falta dejar el test marcado que se había planeado para el sprint 7.

Queda una sola cosa pendiente de Felipe en todo el plan de negocios: los 10 motivos de pérdida, para el sprint 10. Más el 503 de Render, que afecta al sprint 2.

### 2026-08-21 · D0 aprobado — sprints 4 y 6 desbloqueados

Felipe confirmó las tres preguntas que quedaban. `D0` pasa de propuesta a especificación aprobada.

- **Fórmula de Concentradores confirmada** (`D-018`): el rebate del 12% se calcula sobre la comisión que el concentrador le cobra al vendedor. Era lectura del dato y quedó ratificada como el acuerdo real.
- **Catálogos aprobados** (`D-021`): tabla genérica para las cuatro listas planas, `etapas` como tabla propia, `modelo_negocio` como enum.
- **Dos tablas aprobadas** (`D-020`): `negocios` + `negocio_hitos` en vez de `padre_id` autorreferencial. **Modifica `D-013`**, que queda vigente solo en la parte del PK entero y el `codigo` aparte.

Cero preguntas abiertas en el modelo de datos. El único bloqueo que queda en todo el plan es el 503 de Render, que afecta al sprint 2.

### 2026-08-21 · Diseño — resuelta la fórmula de Concentradores (D-018, D-019)

Se levantó la fórmula de comisiones del modelo Concentradores, que bloqueaba el sprint 7. La causa del bloqueo era que **los nombres de las columnas del Excel engañan**: `% Comisión Vendedor` no es ingreso ViveProp sino la tasa que el concentrador le cobra al vendedor, y la comisión real del negocio está en `% Comisión Comprador`.

Verificado al peso en las 13 filas. El rebate es `base × % del concentrador × 12%`, no 12% de la Comisión Total. Se renombran los campos en el modelo para que no vuelva a pasar.

**Se corrigen tres afirmaciones falsas hechas durante la sesión**, todas por leer la columna equivocada: que la Comisión Broker de VVP-4 salía de 0,008 (sale de 0,012); que VVP-15 y VVP-17 tenían la UF mal capturada (no, siguen la regla); y que VVP-16 era un cobro parcial o un error (no: su tasa de concentrador es 4% en vez de 2%, por eso el rebate es el doble). **Tally final: 18 de 19 filas siguen la regla, solo VVP-2 usa base externa.**

Respuestas de Felipe: `pct_equipo` es 10% y va editable por hito; `motivo_valor_manual` es opcional.

De las 6 preguntas de `D0` quedan 2, y las dos son aprobaciones de diseño: catálogos (sprint 4) y dos tablas contra autorreferencia (sprint 6).

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
