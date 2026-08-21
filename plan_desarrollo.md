# Plan de desarrollo · ViveProp Operaciones

> **Regla base:** no se escribe código sin autorización explícita, sprint por sprint.
> Autorizar un sprint no autoriza el siguiente.

**Versión:** v4 · **Última actualización:** 2026-08-20

Archivos relacionados: [estados.md](estados.md) (avance) · [decisiones.md](decisiones.md) (decisiones) · [diseno_modelo_datos.md](diseno_modelo_datos.md) (D0, diseño del esquema)

---

## Objetivo

Una sola app sobre Neon que permita **registrar, gestionar e informar** dos dominios que no se cruzan:

- **Negocios** — pipeline propio de ViveProp. Entrada manual, etapas E1–E7, y motor de comisiones con 3 modelos de negocio que reparte entre Broker / ViveProp / Equipo / Tercero / Concentrador.
- **Canjes** — programa Dataprop. Importación manual del `.xlsx` de Dataprop, más seguimiento operativo por canje.

Ambos comparten login, jerarquía de roles (`gerencia < operaciones < admin`) y la tabla `movimientos` como línea de tiempo.

Reemplaza a `Archivos/GESTION_OPERACIONES_VIVEPROP.xlsx` como herramienta de trabajo. Las hojas `CONFIG` y `REGLAS CALCULO` de ese archivo son la especificación de negocio a codificar.

---

## Orden de ejecución

Las letras son la etiqueta de serie (continúan la convención del repo: `A1–A4` cimientos, `B1–B4` canjes). **Lo que manda es el número.**

| Orden | # | Sprint | Qué deja funcionando |
|---|---|---|---|
| 1 | 1 | C1 · Ambiente dev y red de seguridad | ✅ **Listo** |
| 2 | 4 | C3 · Catálogos | ✅ **Listo** |
| 3 | 6 | D1 · Esquema de negocios | ✅ **Listo** |
| 4 | 7 | D2 · Motor de comisiones | Los 22 casos de prueba pasando |
| 5 | 8 | D3 · CRUD backend | Alta y edición por API, comisión calculada al guardar |
| 6 | 10 | D5 · Carga de los 19 históricos | Datos reales adentro, cuadrando al peso |
| 7 | 9 | D4 · Pantalla Negocios | **Primer hito visible**, con datos reales |
| 8 | 11 | D6 · Pipeline de negocios | Avance por etapas E1–E7 con historial |
| 9 | 12 | F1 · Base de cálculo | Ganado / pipeline / potencial perdido, en CLP |
| 10 | 13 | F2 · Dashboard de negocios | **Segundo hito visible** |
| 11 | 3 | C2 · Tabla UF y conversión | ✅ **Listo** |
| 12 | 5 | C4 · Plantilla y carga manual de UF | Carga mensual autónoma. **Ver fecha límite abajo** |
| 13 | 2 | G2 · Despliegue en Render | Dominio propio, health check, cookie `secure`, `<title>` |
| 14 | 14 | E1 · Plantilla de negocios | Formulario de carga masiva descargable |
| 15 | 15 | E2 · Importador de negocios | Carga masiva validada fila por fila |
| 16 | 16 | F3 · Reporte semanal | Qué se cerró, avanzó, se cayó, está estancado |
| 17 | 17 | F4 · Reporte mensual comparativo | Contra mes anterior y mismo mes del año anterior |
| 18 | 18 | F5 · Vista directorio | Presentación ejecutiva exportable |
| 19 | 19 | B5 · Registrar movimientos en canjes | Se activa la tabla que hoy está en cero |
| 20 | 20 | B6 · Semáforo y bandeja diaria | "Qué me toca hoy" sobre los 297 canjes |
| 21 | 21 | B7 · Migrar el seguimiento histórico | 69 filas trabajadas + 65 motivos |
| 22 | 22 | G1 · Recuperación de contraseña | Reset con cambio forzado |

**Dos cambios de orden respecto de v4**, aprobados el 2026-08-21:

1. **El sprint 10 va antes del 9**: los 19 históricos se cargan antes de construir la pantalla. Una pantalla hecha contra una tabla vacía se ve perfecta y se rompe con datos reales; acá los datos traen VVP-3 con sus dos hitos anidados, direcciones largas, los dos arriendos con su lógica 50/50 y VVP-2 con valor manual. El sprint 10 se verifica por SQL, así que no pierde nada por ir antes.
2. **Los sprints 5 y 2 se corren hacia atrás**: ninguno desbloquea la cadena de negocios, y el 2 se encogió cuando Render resultó estar sano.

**Fecha límite del sprint 5.** La serie de UF cargada termina el **2026-09-09**. Si se llega a principios de septiembre sin ese sprint, las conversiones a fecha del día dejan de funcionar. No es un bloqueo: `app/scripts/cargar_uf.py` ya existe y con la planilla actualizada se corre en un comando. Pero si el 5 de septiembre el sprint no está, hay que cargar la UF a mano.

**Camino crítico:** los diez primeros de la tabla. Es la cadena donde cada sprint usa el diseño del anterior, y hacerlos seguidos evita reconstruir el contexto cada vez.

### Bloques movibles

| Bloque | Se adelanta cuando |
|---|---|
| 19–21 (canjes) | La gestión diaria de canjes se vuelva urgente. Se mueve completo, sin costo. |
| 14–15 (carga masiva) | Entren negocios en volumen y el alta manual moleste. |
| 22 (G1) | Se vaya a crear la tercera cuenta de usuario. |

---

## Detalle por sprint

### 1 · C1 — Ambiente de desarrollo y red de seguridad

Rama `dev` en Neon separada de `production` — hoy el `.env` local escribe en la misma base que usa Render. `pytest` en el repo. Primer test del importador de canjes. Sacar del repo los binarios commiteados (`.tmp_screenshots/`, `para-branding-canjes-negocios.jpeg`, `vista.jpeg`).

- **Listo cuando:** `pytest` corre verde y el `.env` local apunta a `dev`.
- **Requiere del usuario:** crear la rama en la consola de Neon y entregar el connection string, o una API key. *Única dependencia externa de todo el plan.*
- **Decisión al crearla:** la rama de Neon es copy-on-write, así que heredaría los 297 canjes reales, con nombres y correos de corredores de verdad. Cómodo para desarrollar y para probar contra casos reales, pero implica datos personales en un ambiente de desarrollo. La alternativa es una rama solo con esquema y datos sintéticos.

### 2 · G2 — Despliegue en Render

Se mantiene **un solo servicio**, sin dividir a Vercel: el build del front se copia a `backend/static/` y FastAPI sirve `/api/*` y la SPA. **El servicio está sano** — verificado el 2026-08-21: 200 en la raíz y en `/api/health`, 401 en `/api/canjes` sin sesión, ~200 ms de respuesta. El 503 que se reportó el 2026-08-20 era transitorio, probablemente el servicio despertando.

Queda entonces solo lo que se quería agregar: dominio propio `operaciones.viveprop.com`, health check apuntado a `/api/health` en la configuración de Render, dar vuelta la lógica de la cookie `secure` para que sea el valor por defecto, y **cambiar el `<title>` del HTML, que dice `frontend`** — el default de Vite que nunca se tocó.

- **Listo cuando:** la app responde en el dominio propio y la cookie sigue siendo `secure` aunque falte la variable de entorno.

### 3 · C2 — Tabla UF y conversión

`uf_diaria(fecha, valor)` + migración + carga de **1.409 filas desde 2022-11** (no las 17.937 de la hoja: todo lo anterior al primer canje es peso muerto). Servicio de conversión UF↔CLP con fecha de referencia. La hoja `UF` está limpia — 0 huecos en toda la serie.

- **Listo cuando:** la conversión reproduce la columna AC del Excel al peso en negocios reales. Caso de referencia: 1.080 UF al 2026-01-02 (VVP-4) = 42.914.480,40 CLP.

### 4 · C3 — Catálogos

Tablas editables desde `CONFIG`: alianzas (8), modelos de negocio (3), etapas E1–E7 con su responsable, estados de facturación (12), tipos de propiedad y operación. Endpoint `/api/catalogos`.

- **Listo cuando:** el front pinta cualquier desplegable desde la API, sin listas hardcodeadas.

### 5 · C4 — Plantilla y carga manual de UF

Botón que descarga la plantilla (`FECHA`, `VALOR`). Carga con **upsert por fecha** para que subir meses solapados no duplique. Informe de resumen igual al de canjes (nuevas / actualizadas / sin cambio / errores por fila). **Aviso** cuando falten 3 días o menos respecto del último registro, y **alerta** distinta y más visible si la serie quedó vencida.

- **Listo cuando:** borrando los últimos días, la carga los repone y los dos umbrales se comportan bien.
- **Nota:** pilotea el patrón plantilla + importador validador que reusan los sprints 14 y 15.

### 6 · D1 — Esquema de negocios

- `propiedades` — habilita ver reintentos sobre la misma unidad. Hay 5 casos; `Mario Kreutzberger 1520 u.316-A` tomó 3 intentos hasta cerrar.
- `negocios` con `padre_id` autorreferencial. El padre lleva propiedad, contrapartes, alianza, modelo y valor; cada hijo lleva su %, su comisión, sus fechas y sus estados. El doble conteo queda imposible por construcción.
- `negocio_obligaciones` — facturación y pago por parte, en vez de 6 columnas aplanadas.

**Restricción del esquema existente (D-013).** El PK de `negocios` debe ser un entero autoincremental, y `VVP-N` va en una columna `codigo` con índice único. `movimientos.entity_id` es `bigint`, así que un PK de texto dejaría a negocios fuera de la línea de tiempo compartida.

**Validación a replicar.** `movimientos.entity_id` no tiene ni puede tener foreign key (es polimórfico). La verificación de que la entidad exista antes de insertar vive en la capa de servicio — `crear_movimiento_canje` ya lo hace, y hay que replicarlo para negocios.

**Valorización (D-017).** El hijo lleva `valor_negocio` + `moneda`, `fecha_valorizacion`, `uf_snapshot`, `valor_clp_calculado`, `valor_clp_manual` (nullable) y `motivo_valor_manual`. La **base de comisión** es `COALESCE(valor_clp_manual, valor_clp_calculado)` — el valor en pesos se puede ingresar a mano porque en Mercado Primario y Assetplan lo determinan liquidaciones externas que no siguen la regla de la UF.

- **Listo cuando:** la migración sube y baja limpia contra `dev`.

### 7 · D2 — Motor de comisiones

Función pura, sin base de datos: entra el negocio, salen los 5 montos del orden universal (Total → Broker → VP Bruta → Equipo → Real VP). **Los tests se escriben antes del motor.**

- **Listo cuando:** pasan los **22 casos** — 3 de `REGLAS CALCULO` + 19 de regresión con las filas reales, cubriendo los 3 modelos, venta y arriendo, con y sin rebate de concentrador, con y sin tercero.
- **Corren sobre la base de comisión (D-017)**, no sobre la conversión por UF. Si corrieran sobre la UF, VVP-2 no reproduciría nunca.
- **La fórmula de Concentradores está resuelta y verificada (D-018).** Cada modelo lee columnas distintas para la Comisión Total, y el rebate es `base × % del concentrador × 12%`, no 12% del total.
- **Decisión pendiente:** en arriendo, `% Broker` sobre la comisión total o sobre el arriendo mensual. Hoy indistinguible porque las partes pagan 50/50. Se arranca con la fórmula documentada (sobre el valor) y queda el test marcado.

### 8 · D3 — CRUD backend

Endpoints de negocios con cálculo de comisiones **al guardar** — persistido, no recalculado al leer, para que un cambio futuro de reglas no altere la historia. Padre e hijos. Respeta la jerarquía de roles.

- **Listo cuando:** crear un negocio con dos hitos por API devuelve las comisiones correctas y sumar no duplica.

### 9 · D4 — Pantalla Negocios

Listado con filtros (estado, modelo, alianza, etapa) + ficha con sus hitos + formulario de alta y edición.

- **Listo cuando:** se puede registrar un negocio completo desde el navegador sin tocar la API.

### 10 · D5 — Carga de los 19 históricos

Script one-shot desde la hoja `NEGOCIOS`, **creando el padre `VVP-3`**, que no existe como fila en el Excel.

- **Listo cuando:** los 19 quedan cargados y las comisiones en base coinciden al peso con el Excel.
- **Sin pendientes de consultar.** Los 10 motivos de pérdida quedan vacíos por decisión (`D-023`): el campo es opcional y no se completan los históricos.

**Base de comisión, verificado sobre las 19 filas (ver D-017).** 17 siguen la regla —comisión sobre `valor × UF`— y **2 no**. Al cargar hay que decidir qué se hace con esas dos:

- **VVP-2**: comisión calculada sobre 81.505.175 en vez de los 104.100.248 que da la UF (−21,7%). La observación de la planilla lo explica: *"Ver liq Negocio, hubo ajustes por costo credito pie ultima hora"*. Es el caso de `valor_clp_manual`, y su observación es el `motivo_valor_manual`.
- **VVP-16**: base exactamente la mitad del calculado, con `% declarado` 0,04 pero cobrado 0,02. No es valor externo: es medio porcentaje. Observación: "En proceso de formalización". **Hay que preguntar** si fue un cobro parcial o el porcentaje quedó mal registrado.

**Nota sobre la UF del snapshot.** La columna AB usa la UF de `Fecha Valorización` si está poblada, y la de `Fecha_Inicio` si no. VVP-3 PROMESA tiene 39.707,30, que no corresponde a ninguna fecha de la serie —lo más cercano es el 2025-12-26 con 39.708,77— y su `Fecha Valorización` dice `2026-12-26`, con el año probablemente mal escrito. Sus comisiones sí cuadran con ese valor, así que se carga tal cual y se deja anotado.

### 11 · D6 — Pipeline de negocios

Sembrar `tipos_movimiento` para `entity_type=negocio` (E1–E7 con su responsable) y activar el avance por etapa. Reusa la infraestructura de movimientos que ya existe: sin código nuevo de seguimiento.

**Restricción del esquema existente (D-014).** Los códigos van con prefijo (`NEG_CIERRE`, `NEG_CANCELACION`). `tipos_movimiento.codigo` es PK global, no compuesta con `entity_type`, y ya existen `CIERRE`, `CANCELACION` y `COMENTARIO_GENERAL` para canjes.

- **Listo cuando:** avanzar un negocio de etapa queda registrado en su línea de tiempo con autor y fecha.

### 12 · F1 — Base de cálculo de reportería

Separación **estructural** en tres buckets —ganado / pipeline / comisión potencial no concretada— y normalización a CLP vía la tabla UF. Es la capa que consumen los sprints 13 a 18, y la que impide que un informe sume cosas que no se suman.

- **Listo cuando:** los tres buckets dan los números verificados: **8,09M / 1,82M / 4,75M**.

### 13 · F2 — Dashboard de negocios

Comisión real VP por mes, por alianza, por modelo, por etapa. Rebate de concentrador como línea propia — 523.674 acumulados, 6,5% sobre lo cerrado, margen que no se reparte con el corredor aliado.

### 14 · E1 — Plantilla de negocios

`.xlsx` generado por la app, con desplegables alimentados desde los catálogos del sprint 4.

### 15 · E2 — Importador de negocios

Validación fila por fila con informe de errores; no escribe nada si hay errores bloqueantes.

- **Listo cuando:** un archivo con 3 filas malas reporta las 3 y no carga ninguna.

### 16 · F3 — Reporte semanal

Qué se cerró, qué avanzó, qué se cayó, qué está estancado.

### 17 · F4 — Reporte mensual comparativo

Mes actual contra mes anterior y contra el mismo mes del año anterior, con variación.

- **Listo cuando:** un mes sin datos no rompe la comparación, muestra vacío.

### 18 · F5 — Vista directorio

Presentación ejecutiva, exportable.

- **Pendiente de consultar:** qué quiere ver el directorio, antes de diseñarla.

### 19 · B5 — Registrar movimientos en canjes

Activar en la ficha del canje el registro de movimientos. La tabla y los 14 tipos ya existen en Neon y están **en cero**.

- **Listo cuando:** registrar un movimiento avanza la etapa del canje y queda en su historial.

### 20 · B6 — Semáforo y bandeja diaria

Semáforo por SLA usando `tipos_movimiento.sla_horas` con los umbrales 48h/24h de `CONFIG`, y bandeja "qué me toca hoy".

- **Listo cuando:** un canje sin gestión por más de 48h aparece en rojo en la bandeja.

### 21 · B7 — Migrar el seguimiento histórico

Las 69 filas trabajadas de `✅ Seguimiento Operativo` a `movimientos`, más los 65 motivos de cancelación.

### 22 · G1 — Recuperación de contraseña

Reset desde `/admin/usuarios` que genera una temporal, más marca `debe_cambiar_clave` que bloquea la navegación hasta que el usuario la cambie. La regla es **según la puerta, no según el rol**: contraseña puesta por un tercero siempre queda marcada como temporal, sea gerencia, operaciones o admin; contraseña puesta por el propio usuario en "Cambiar mi contraseña" no se marca. El cambio voluntario ya existe y no se toca.

- **Listo cuando:** un usuario con clave reseteada no llega a ninguna pantalla sin cambiarla primero.

---

## Decisiones pendientes

Ninguna bloquea el arranque.

| Sprint | Pregunta |
|---|---|
| 1 (C1) | La rama `dev` se crea con los datos reales heredados o solo con el esquema. |
| 7 (D2) | En arriendo, `% Broker` se calcula sobre la comisión total o sobre el arriendo mensual. |
| 10 (D5) | Tasas de rebate de VVP-15/16/17 y los 10 motivos de pérdida vacíos. |
| 18 (F5) | Qué quiere ver el directorio. |

## Diferido por decisión del usuario

Fuera del plan, registrado para cuando se retome tras ver el funcionamiento:

- Límite de intentos de login (hoy `/auth/login` acepta intentos infinitos).
- Política mínima de contraseñas (`cambiar-clave` acepta `"1"`).
- Restricción de dominio de email al crear usuarios.
- Fuga de tiempos en el login que revela qué emails tienen cuenta.
- Limpiar `SESSION_SECRET`: declarada en `config.py`, README y `render.yaml`, nunca leída por el código.
- Rol super admin y guardas contra autodesactivación del admin: **descartados**. Rescate ante bloqueo total: `backend/app/scripts/seed_admin.py` con el `DATABASE_URL`.

---

## Estado del sistema al momento del plan

Verificado el 2026-08-20 contra la base de Neon (proyecto `viveprop-operaciones`, rama única `production`).

| Tabla | Filas | Observación |
|---|---|---|
| `canjes` | 297 | Datos reales de Dataprop, 2022-11-29 → 2026-08-10. 225 ACTIVO / 72 CANCELADO. 31 son ACTIVO + etapa CERRADO. |
| `tipos_movimiento` | 14 | Todos `entity_type=canje`. Ninguno de negocio. |
| `movimientos` | 0 | Infraestructura construida, sin uso. |
| `usuarios` | 2 | felipe (admin), gianfranco (operaciones). |
| `sesiones` | 2 | |

**Ya construido:** auth con Argon2id y sesiones en base, jerarquía de roles validada en servidor, CRUD y listado de canjes, importador de `.xlsx` de Dataprop con la regla `gestionado_en_app`, dashboard de reportes de canjes, cambio de contraseña propia, mantenedor de usuarios, tema Mantine con branding, despliegue de un servicio en Render.

**No existe:** dominio Negocios completo, motor de comisiones, tabla UF, catálogos, tests.

**El Excel de canjes está obsoleto respecto a la base:** 158 filas contra 297, y la distribución invertida (Excel 153 cancelado / 5 activo; Neon 72 / 225). Las hojas `📋 Info General` y `📊 Resumen Canjes` no son fuente de verdad. Lo irremplazable del Excel es el seguimiento operativo (69 filas trabajadas), los motivos de cancelación, y los catálogos y reglas de negocio.
