# Plan de desarrollo · ViveProp Operaciones

> **Regla base:** no se escribe código sin autorización explícita, sprint por sprint.
> Autorizar un sprint no autoriza el siguiente.

**Versión:** v4 · **Última actualización:** 2026-08-21

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
| 4 | 7 | D2 · Motor de comisiones | ✅ **Listo** |
| 5 | 8 | D3 · CRUD backend | Alta y edición por API, comisión calculada al guardar |
| 6 | 10 | D5 · Carga de los 19 históricos | ✅ **Listo** |
| 7 | 9 | D4 · Pantalla Negocios | ✅ **Listo** **primer hito visible** |
| 8 | 11 | D6 · Pipeline de negocios | ✅ **Listo** |
| 9 | 12 | F1 · Base de cálculo | ✅ **Listo** |
| 10 | 13 | F2 · Dashboard de negocios | ✅ **Listo** **segundo hito visible** |
| 11 | 3 | C2 · Tabla UF y conversión | ✅ **Listo** |
| 12 | 5 | C4 · Plantilla y carga manual de UF | ✅ **Listo** |
| 13 | 2 | G2 · Despliegue en Render | 🔸 **En curso** falta solo el dominio (acción tuya) |
| 14 | 14 | E1 · Plantilla de negocios | Formulario de carga masiva descargable |
| 15 | 15 | E2 · Importador de negocios | Carga masiva validada fila por fila |
| 16 | 16 | F3 · Reporte semanal | ✅ **Listo** los dos dominios |
| 17 | 17 | F4 · Reporte mensual comparativo | Contra mes anterior y mismo mes del año anterior |
| 18 | 18 | F5 · Vista directorio | Presentación ejecutiva exportable |
| 19 | 19 | B5 · Registrar movimientos en canjes | ✅ **Listo** ya estaba desde B3 |
| 20 | 20 | B6 · Semáforo y bandeja diaria | ✅ **Listo** |
| 21 | 21 | B7 · Migrar el seguimiento histórico | ✅ **Listo** |
| 22 | 22 | G1 · Recuperación de contraseña | Reset con cambio forzado |

**Dos cambios de orden respecto de v4**, aprobados el 2026-08-21:

1. **El sprint 10 va antes del 9**: los 19 históricos se cargan antes de construir la pantalla. Una pantalla hecha contra una tabla vacía se ve perfecta y se rompe con datos reales; acá los datos traen VVP-3 con sus dos hitos anidados, direcciones largas, los dos arriendos con su lógica 50/50 y VVP-2 con valor manual. El sprint 10 se verifica por SQL, así que no pierde nada por ir antes.
2. **Los sprints 5 y 2 se corren hacia atrás**: ninguno desbloquea la cadena de negocios, y el 2 se encogió cuando Render resultó estar sano.

**Fecha límite del sprint 5: cumplida.** La serie llega hasta el 2026-09-09 y desde el 2026-08-21 hay cómo extenderla desde la app, sin scripts ni línea de comando.

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

### 2 · G2 — Despliegue en Render 🔸 En curso

Se mantiene **un solo servicio**, sin dividir a Vercel: el build del front se copia a `backend/static/` y FastAPI sirve `/api/*` y la SPA.

**Hecho el 2026-08-21:**

- **La cookie de sesión es `secure` por defecto** (`D-033`). Antes se activaba solo si `ENVIRONMENT == "production"`, así que si esa variable faltaba o tenía un typo la cookie salía sin `secure` sobre HTTPS **y nada fallaba**. Ahora solo `development`, `local` y `test` la desactivan; cualquier otro valor cae del lado seguro.
- **El `<title>` ya no dice `frontend`** — el default de Vite que nunca se tocó. Dice `ViveProp Operaciones`, el `lang` pasó de `en` a `es`, y se agregó `noindex` porque es una app interna que no tiene por qué estar en Google.
- **`healthCheckPath` apuntado a `/api/health`** en `render.yaml`. Antes Render usaba la raíz, que devuelve el `index.html`: un 200 que no prueba que la app arrancó.
- **`/api/health` y `/api/health/db` quedaron separados** (`D-035`). El de Render no toca la base a propósito; el otro sirve para diagnosticar, y es el que habría contestado la duda del 503 del 2026-08-20 en un segundo.
- **Un `/api/...` inexistente ahora es 404 y no la SPA** (`D-034`). Estaba devolviendo 200 con el `index.html`, verificado en producción. De paso, el servido de archivos ya no arma la ruta con la URL sin revisarla.

**Falta, y depende de ti:** el dominio propio `operaciones.viveprop.com`. Hay que agregarlo en Render (Settings → Custom Domains), crear el registro DNS que Render indique, y **después** actualizar `ALLOWED_ORIGINS` en `render.yaml` para que incluya el dominio nuevo. Sin ese último paso el CORS lo rechaza.

- **Listo cuando:** la app responde en el dominio propio y la cookie sigue siendo `secure` aunque falte la variable de entorno. ✅ La segunda mitad está; falta la primera.

### 3 · C2 — Tabla UF y conversión

`uf_diaria(fecha, valor)` + migración + carga de **1.409 filas desde 2022-11** (no las 17.937 de la hoja: todo lo anterior al primer canje es peso muerto). Servicio de conversión UF↔CLP con fecha de referencia. La hoja `UF` está limpia — 0 huecos en toda la serie.

- **Listo cuando:** la conversión reproduce la columna AC del Excel al peso en negocios reales. Caso de referencia: 1.080 UF al 2026-01-02 (VVP-4) = 42.914.480,40 CLP.

### 4 · C3 — Catálogos

Tablas editables desde `CONFIG`: alianzas (8), modelos de negocio (3), etapas E1–E7 con su responsable, estados de facturación (12), tipos de propiedad y operación. Endpoint `/api/catalogos`.

- **Listo cuando:** el front pinta cualquier desplegable desde la API, sin listas hardcodeadas.

### 5 · C4 — Plantilla y carga manual de UF

✅ **Listo** **el 2026-08-21.** Pantalla propia en `/uf`, con estado de la serie, descarga de plantilla y carga.

- **La plantilla trae las fechas que faltan ya escritas** y el valor en blanco, así que no hay que averiguar cuáles son. Incluye una hoja de instrucciones. Si la serie estuviera vacía arranca en el día de hoy, porque no tiene sentido pedir cuatro años de historia a mano.
- **Carga idempotente por fecha**: subir un archivo solapado no duplica, actualiza lo que cambió y deja igual lo que no. El informe distingue nuevas, actualizadas y sin cambio.
- **Si hay errores de formato no se carga nada.** Media serie subida sin saber cuál mitad es peor que no cargar. Los errores se informan por fila.
- Acepta las dos convenciones de número: `40.885,63` y `40885.63`.
- **Aviso a 3 días** y **alerta distinta si la serie venció** (`D-008`), en un componente que aparece en la página de Negocios y en su dashboard: sin UF vigente no se puede valorizar, y eso rompe el alta. Cuando la serie está sana no dibuja nada.
- 24 tests. Piloteó el patrón que reusan los sprints 14 y 15.

**Fecha límite cumplida:** la serie llega hasta el 2026-09-09 y ahora hay cómo extenderla desde la app.

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

✅ **Listo** **el 2026-08-21.** Cinco endpoints, más búsqueda de propiedades. La comisión se calcula al guardar y se persiste.

El orden al guardar un hito es siempre el mismo, en `app/services/negocios.py`: se congela la UF de la fecha de referencia (`fecha_valorizacion`, o `fecha_inicio` si falta), se resuelve la base con el manual ganándole al calculado (`D-017`), y se aplican las comisiones con la fórmula del modelo (`D-018`).

- Verificado punta a punta contra `dev` con los números reales de VVP-4: 39.735,63 de UF, 42.914.480,40 de base y 858.289,61 de comisión total.
- Un hito sin valorizar deja los montos en **nulo**, no en cero, para distinguir "sin valorizar" de "valorizado en cero".
- Si falta la UF de la fecha, el error dice qué fecha, qué rango tiene la serie y que hay que cargar el nuevo tramo — conecta con el sprint 5.
- La propiedad se reusa si ya existe con esa dirección, unidad y comuna, así el patrón de reintento queda visible. Más `GET /api/negocios/propiedades?q=` para que el alta del sprint 9 ofrezca las parecidas.
- Los catálogos se validan por tipo en el servicio, que es el costo aceptado en `D-021`.

### 9 · D4 — Pantalla Negocios

✅ **Listo** **el 2026-08-21.** Listado con filtros, ficha con sus hitos y formulario de alta.

- **Listado** con filtros por código, modelo, estado y alianza. Fila de totales al pie, sumando los hitos — la única forma correcta de totalizar (`D-020`). Los negocios con más de un hito lo indican con una insignia.
- **Ficha** con el desglose de comisiones de cada hito en cascada: total del negocio, corredor aliado, ViveProp bruta, y las restas de tercero y equipo hasta la comisión real. El rebate del concentrador se muestra en verde porque suma, no resta.
- **Dos avisos que la ficha hace explícitos.** Si el hito usa valor ingresado a mano, se dice sobre qué monto se calculó y por qué. Y si la comisión total no cuadra con su reparto —el caso de VVP-2— aparece una alerta con el monto del descuadre en vez de mostrar números que no suman.
- **Formulario que se adapta al modelo**: pide el lado vendedor en Primario, el comprador en Concentradores, los dos en Agencia. No muestra campos que ese modelo ignora, que es de donde salieron tres errores de lectura en el análisis.
- Los porcentajes se ingresan como número (2 = 2%) y se envían como fracción.
- Mientras se escribe la dirección se ofrecen las propiedades parecidas, porque la clave única no agrupa `Av. Fernández Albano 492` con `Fernández Albano 492`.

### 10 · D5 — Carga de los 19 históricos

✅ **Listo** **el 2026-08-21.** `app/scripts/cargar_negocios.py`. **18 negocios, 19 hitos, 13 propiedades y 114 obligaciones** en `dev`, con el padre `VVP-3` creado, que no existía como fila.

**Migra fiel, no recalcula.** Los montos que quedan en la base son los del Excel. Recalcular cambiaría en silencio los números de siete negocios cerrados con plata ya facturada. El motor sí se ejecuta, pero solo para comparar, y la carga imprime un informe con cada diferencia — así se autoverifica.

**Resultado: una sola diferencia en los 19 negocios**, el `comision_total` de VVP-2 (`D-026`). Todo lo demás reproduce el Excel al peso.

Los totales verificados contra los números conocidos: ganado 8.087.862, pipeline 1.824.272, potencial perdido 4.751.491, y 523.674 de rebate acumulado.

La UF se preserva de la columna AB en vez de buscarla en la serie: la de VVP-3 PROMESA (39.707,30) no existe en ninguna fecha, así que recalcularla habría cambiado su valorización.
- **Sin pendientes de consultar.** Los 10 motivos de pérdida quedan vacíos por decisión (`D-023`): el campo es opcional y no se completan los históricos.

**Base de comisión, verificado sobre las 19 filas (ver D-017).** 17 siguen la regla —comisión sobre `valor × UF`— y **2 no**. Al cargar hay que decidir qué se hace con esas dos:

- **VVP-2**: comisión calculada sobre 81.505.175 en vez de los 104.100.248 que da la UF (−21,7%). La observación de la planilla lo explica: *"Ver liq Negocio, hubo ajustes por costo credito pie ultima hora"*. Es el caso de `valor_clp_manual`, y su observación es el `motivo_valor_manual`.
- **VVP-16**: base exactamente la mitad del calculado, con `% declarado` 0,04 pero cobrado 0,02. No es valor externo: es medio porcentaje. Observación: "En proceso de formalización". **Hay que preguntar** si fue un cobro parcial o el porcentaje quedó mal registrado.

**Nota sobre la UF del snapshot.** La columna AB usa la UF de `Fecha Valorización` si está poblada, y la de `Fecha_Inicio` si no. VVP-3 PROMESA tiene 39.707,30, que no corresponde a ninguna fecha de la serie —lo más cercano es el 2025-12-26 con 39.708,77— y su `Fecha Valorización` dice `2026-12-26`, con el año probablemente mal escrito. Sus comisiones sí cuadran con ese valor, así que se carga tal cual y se deja anotado.

### 11 · D6 — Pipeline de negocios

✅ **Listo** **el 2026-08-21.** 10 tipos de movimiento sembrados con prefijo `NEG_` (`D-014`), cero colisiones con los 14 de canjes. Servicio, endpoints y línea de tiempo en la ficha.

**Hubo que mover `etapa` del hito al negocio** (`D-027`): un movimiento que apunta al negocio no tenía a qué hito aplicarle la etapa. Migración sin pérdida, verificada sobre los 18 negocios cargados.

- Los 7 pasos E1–E7 mueven la etapa; `NEG_PERDIDA` y `NEG_DESISTIMIENTO` cambian el estado **solo de las liquidaciones abiertas**; `NEG_COMENTARIO` no mueve nada.
- `GET /api/negocios/tipos-movimiento` para que el front no hardcodee los pasos. Va **antes** de `/{negocio_id}` en el registro de rutas, porque FastAPI resuelve por orden y si no, `tipos-movimiento` se interpreta como un id.
- Verificado contra `dev` con VVP-17: E4 → E5 registrado con autor y fecha, y revertido después.

### 12 · F1 — Base de cálculo de reportería

✅ **Listo** **el 2026-08-21.** `app/services/reportes_negocios.py` más `GET /api/negocios/reportes/resumen`.

Los tres buckets dan exactamente los números verificados: **8.087.862 / 1.824.272 / 4.751.491**.

- **No existe un campo que los sume**, y hay un test que lo verifica. Sumar ganado, pipeline y perdido da un número que no significa nada; si alguien lo quiere, lo suma a mano y sabe lo que hace.
- `DESISTIDO` va con lo perdido: no entró.
- **Los negocios se cuentan sin duplicar**: G-2 con dos hitos ganados es un negocio, no dos.
- El corte por mes usa **`fecha_cierre`**, no la de inicio: lo que importa es cuándo entró la plata. Los cerrados sin fecha caen en "Sin fecha" en vez de desaparecer.
- Los desgloses por alianza y modelo van **solo sobre lo ganado**. El pipeline se mira por etapa, que es donde está detenido.
- **Los hitos sin valorizar se cuentan aparte**: cuentan como hitos del pipeline pero no aportan plata, porque todavía no tienen base.
- La normalización a CLP ya estaba resuelta al guardar (sprint 8): las columnas `comision_*` son `numeric(16,2)` en pesos con la UF congelada del hito. Acá no se convierte nada, solo se agrupa.

**Nota técnica:** el agrupamiento por mes se hace en Python y no con `to_char`, que es exclusivo de Postgres y dejaría este cálculo sin poder testearse contra la base en memoria. Con este volumen la diferencia es irrelevante.

### 13 · F2 — Dashboard de negocios

✅ **Listo** **el 2026-08-21.** `pages/DashboardNegocios.tsx`, consumiendo el resumen del sprint 12.

- **Tres tiles** para los tres buckets, cada uno con su etiqueta y su número: la identidad nunca depende solo del color. El rebate va como leyenda dentro del tile que le corresponde, porque es parte de esa comisión real.
- **Gráfico mensual de una sola serie**: comisión real VP por mes de cierre. Sin leyenda, porque el título dice qué se mide. La comisión total va en el tooltip, y abajo la misma información como tabla.
- **Barras horizontales** por alianza, por modelo y del pipeline por etapa, con el monto como etiqueta directa en cada fila.
- Aviso si hay liquidaciones sin valorizar, para que no desaparezcan del cuadro.
- **La paleta se validó con un script** (`D-028`), no a ojo. Encontró tres problemas que no se habrían visto, incluido que la tríada verde/teal/rojo quedaba a ΔE 2,8 en tritanopía.

### 14 · E1 — Plantilla de negocios

`.xlsx` generado por la app, con desplegables alimentados desde los catálogos del sprint 4.

### 15 · E2 — Importador de negocios

Validación fila por fila con informe de errores; no escribe nada si hay errores bloqueantes.

- **Listo cuando:** un archivo con 3 filas malas reporta las 3 y no carga ninguna.

### 16 · F3 — Reporte semanal ✅ Listo

Qué se cerró, qué avanzó, qué se cayó, qué está estancado. **En los dos dominios**: un reporte de la semana que ignore los 194 canjes abiertos sería medio reporte, y quien lo lee opera los dos.

Es lo contrario del dashboard. El dashboard responde "cómo vamos" y mira el estado actual; esto responde "qué pasó" y mira los movimientos del período. Por eso no repite las cifras de cartera.

- **Listo cuando:** una semana con gestión registrada pero sin cambios de etapa aparece con actividad, no vacía (`D-031`), y el umbral de estancado es un control visible, no una constante escondida (`D-032`). ✅ 30 tests; verificado contra `dev`.

### 17 · F4 — Reporte mensual comparativo

Mes actual contra mes anterior y contra el mismo mes del año anterior, con variación.

- **Listo cuando:** un mes sin datos no rompe la comparación, muestra vacío.

### 18 · F5 — Vista directorio

Presentación ejecutiva, exportable.

- **Pendiente de consultar:** qué quiere ver el directorio, antes de diseñarla.

### 19 · B5 — Registrar movimientos en canjes

✅ **Listo** **el 2026-08-21, sin escribir código.** Al ir a construirlo se verificó que ya funcionaba desde el sprint B3: existen el servicio `crear_movimiento_canje`, los endpoints `GET`/`POST /api/canjes/{id}/movimientos`, los 14 tipos sembrados y el modal de seguimiento conectado a la página de Canjes.

Verificado de punta a punta contra `dev`: registrar un movimiento en un canje real lo avanzó de `EN_REVISION` a `PROCESO_DE_ACUERDO`, quedó en el historial con autor y fecha, y marcó `gestionado_en_app` para que la importación de Dataprop no lo sobreescriba.

**El diagnóstico del plan estaba mal.** Que la tabla esté en cero no era falta de código: es que nadie lo ha usado todavía. Lo que falta para que se use son los sprints 20 y 21 — sin bandeja diaria no hay razón para entrar a registrar, y sin el histórico migrado el Excel sigue siendo la referencia.

### 20 · B6 — Semáforo y bandeja diaria

✅ **Listo** **el 2026-08-21.** Pantalla `/bandeja`, "Qué me toca hoy", primera en el menú de Operaciones.

- **Cuatro niveles**, no tres: `sin gestión`, `crítico`, `advertencia`, `al día`. Ver `D-029`: los 194 canjes abiertos nunca se tocaron, y meterlos en rojo dejaría la bandeja con 194 filas rojas y el color sin significado.
- **Los umbrales son los globales de `CONFIG`** —48 y 24 horas— y no el `sla_horas` por tipo, que mide otra cosa.
- Entran a la bandeja los canjes con `estado = ACTIVO` **y** etapa distinta de `CERRADO`: son 194 de los 225 activos.
- **Orden de atención**: primero lo que nunca se tocó, después lo más abandonado, y a igualdad de abandono el más antiguo.
- Cada nivel se muestra con su palabra, nunca con el color solo — `theme.ts` ya advierte que el coral de acento y el rojo crítico se parecen.
- Hacer clic en una fila abre el seguimiento del canje, que ya existía. Registrar un movimiento saca el canje de "sin gestión" y reinicia el reloj.
- 22 tests.

### 21 · B7 — Migrar el seguimiento histórico

✅ **Listo** **el 2026-08-21.** **384 movimientos en 112 canjes**, vía `app/scripts/migrar_seguimiento_canjes.py`.

- **Tres tipos de movimiento que faltaban.** El catálogo sembrado en B3 no cubría `Cliente calificado`, `Propiedad disponible` ni `Email registro solicitante` — este último una omisión evidente, porque existía el del propietario. Sin ellos se perdían 100 pasos completados. Se agregaron y se reordenó el catálogo siguiendo el orden real del proceso.
- **Las fechas son aproximadas y lo dicen** (`D-030`). La hoja registra qué pasos se completaron pero no cuándo; cada movimiento lleva la mejor fecha real del canje según su lado, y el comentario dice `Migrado del Excel — fecha aproximada`.
- Los pasos marcados "No" y las observaciones van juntos en un comentario, no como movimientos: un "No" no es un paso completado.
- **La migración no mueve etapas**: la etapa viene de Dataprop y es más confiable que reconstruirla del checklist.
- **26 filas del Excel referencian canjes que no están en la base** y quedaron fuera, reportadas por el cargador.

**El efecto en la bandeja:** de 194 canjes indiferenciados a **146 sin gestión y 48 críticos**. Los 48 son casos reales de "se trabajó y se dejó estar", que antes eran indistinguibles.

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
