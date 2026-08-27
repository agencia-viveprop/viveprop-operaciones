# Decisiones · ViveProp Operaciones

Registro de las decisiones tomadas durante la planificación y ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Avance de la ejecución: [estados.md](estados.md). Diseño del esquema: [diseno_modelo_datos.md](diseno_modelo_datos.md).

**Última actualización:** 2026-08-20

Formato de cada entrada: **contexto** (qué obligó a decidir), **decisión** (qué se resolvió), **motivo** (por qué). Las decisiones descartadas se dejan registradas para no volver a discutirlas.

---

## Índice

| # | Fecha | Decisión | Sprint |
|---|---|---|---|
| [D-001](#d-001) | 2026-08-20 | Sin código sin autorización explícita | Todos |
| [D-002](#d-002) | 2026-08-20 | Negocios con hitos: padre + hijos | 6 |
| [D-003](#d-003) | 2026-08-20 | El Excel pasa a ser plantilla de carga, no planilla de trabajo | 14, 15 |
| [D-004](#d-004) | 2026-08-20 | Reportería en cuatro niveles | 13, 16, 17, 18 |
| [D-005](#d-005) | 2026-08-20 | Se conservan porcentaje y monto, no uno derivado del otro | 6, 7 |
| [D-006](#d-006) | 2026-08-20 | Los negocios perdidos conservan su comisión calculada | 12 |
| [D-007](#d-007) | 2026-08-20 | La UF no se autoactualiza: carga manual mensual | 5 |
| [D-008](#d-008) | 2026-08-20 | Umbral del aviso de UF: 3 días, más alerta por serie vencida | 5 |
| [D-009](#d-009) | 2026-08-20 | Un solo servicio en Render, sin dividir a Vercel | 2 |
| [D-010](#d-010) | 2026-08-20 | Seguridad del acceso diferida | — |
| [D-011](#d-011) | 2026-08-20 | Sin rol super admin ni guardas de autodesactivación | — |
| [D-012](#d-012) | 2026-08-20 | Orden de ejecución: negocios antes que gestión de canjes | Todos |
| [D-013](#d-013) | 2026-08-20 | `negocios.id` entero autoincremental, `VVP-N` como columna aparte | 6 |
| [D-014](#d-014) | 2026-08-20 | Códigos de `tipos_movimiento` de negocio con prefijo | 11 |
| [D-015](#d-015) | 2026-08-20 | La documentación se actualiza en el mismo commit que el cambio | Todos |
| [D-016](#d-016) | 2026-08-20 | Ninguna conversión UF↔CLP sin fecha, y Decimal en todo el camino | 3 |
| [D-017](#d-017) | 2026-08-20 | El valor en pesos se puede ingresar a mano y es la base de comisión | 6, 7, 10 |
| [D-018](#d-018) | 2026-08-21 | La fórmula de comisiones de Concentradores, y los nombres del modelo | 7 |
| [D-020](#d-020) | 2026-08-21 | Dos tablas, `negocios` + `negocio_hitos`, en vez de autorreferencia | 6 |
| [D-021](#d-021) | 2026-08-21 | Catálogos: tabla genérica, `etapas` aparte, `modelo_negocio` como enum | 4 |
| [D-022](#d-022) | 2026-08-21 | El `% Broker` se aplica sobre la base en los tres modelos, arriendo incluido | 7 |
| [D-023](#d-023) | 2026-08-21 | `motivo_perdida` es opcional, con catálogo más texto libre | 6, 10 |
| [D-024](#d-024) | 2026-08-21 | Las tasas se nombran por lado de la operación, no por destino | 6, 7 |
| [D-025](#d-025) | 2026-08-21 | Dos correcciones a `REGLAS CALCULO`, verificadas en los datos | 7 |
| [D-026](#d-026) | 2026-08-21 | VVP-2 está descuadrado en el origen | 10 |
| [D-027](#d-027) | 2026-08-21 | `etapa` es del negocio; `estado` se queda en el hito | 11 |
| [D-028](#d-028) | 2026-08-21 | La paleta de los gráficos se valida con un script, no a ojo | 13 |
| [D-029](#d-029) | 2026-08-21 | `sin gestión` es un nivel del semáforo, no `crítico` | 20 |
| [D-030](#d-030) | 2026-08-21 | El seguimiento migrado conserva la estructura y admite la fecha aproximada | 21 |
| [D-031](#d-031) | 2026-08-21 | En el reporte semanal, "avanzó" es toda actividad registrada | 16 |
| [D-032](#d-032) | 2026-08-21 | El umbral de estancado es un parámetro, no una constante de negocio | 16 |
| [D-033](#d-033) | 2026-08-21 | La cookie de sesión es `secure` por defecto, no por configuración | 2 |
| [D-034](#d-034) | 2026-08-21 | Un `/api/...` sin router es 404, no la SPA | 2 |
| [D-035](#d-035) | 2026-08-21 | El health check de Render no toca la base | 2 |
| [D-036](#d-036) | 2026-08-21 | La UF se baja del SII, verificado contra 617 fechas | 23 |
| [D-037](#d-037) | 2026-08-21 | La descarga corre en el propio servicio, no en un Cron Job | 23 |
| [D-038](#d-038) | 2026-08-21 | Cargar UF es solo de admin; consultar su estado, de todos | 23 |
| [D-039](#d-039) | 2026-08-21 | La plantilla de negocios pide entradas, no resultados | 14, 15 |
| [D-040](#d-040) | 2026-08-21 | El cambio forzado de clave lo aplica la API, no la pantalla | 22 |
| [D-041](#d-041) | 2026-08-21 | La variación contra cero es nula, no infinita | 17 |
| [D-042](#d-042) | 2026-08-22 | Un negocio tiene tres duraciones distintas, y ninguna es `actualizado_en` | — |
| [D-043](#d-043) | 2026-08-22 | El cierre mensual se compara con ventanas móviles, no mes contra mes | 17 |
| [D-044](#d-044) | 2026-08-22 | La vista directorio se entrega con supuestos declarados, y la proyección va como rango | 18 |
| [D-045](#d-045) | 2026-08-22 | El límite de intentos corta antes de verificar el hash | — |

---

## D-001 · Sin código sin autorización explícita

**Contexto.** El trabajo previo se hizo a base de propuestas revisadas antes de ejecutar.

**Decisión.** Condición excluyente: no se escribe ni modifica código, migraciones ni esquema salvo indicación explícita del usuario, sprint por sprint. Autorizar un sprint no autoriza el siguiente. Analizar, diagnosticar, inspeccionar datos y proponer planes no requiere permiso.

**Motivo.** Mantener el control sobre qué se construye y en qué orden.

---

## D-002 · Negocios con hitos: padre + hijos

**Contexto.** En la hoja `NEGOCIOS`, `VVP-3 PROMESA` y `VVP-3 ESCRITURA` comparten el `ID_Base` `VVP-3`. No existe una fila padre `VVP-3`. Ambos hitos comparten propiedad y valor (6.088,44 UF) pero tienen porcentaje y comisión distintos: 2% en promesa (4.835.110) y 1% en escritura (2.422.629). El 3% del negocio se cobra partido.

**Decisión.** `negocios` con `padre_id` autorreferencial. El padre lleva identidad, propiedad, contrapartes, alianza, modelo y valor. Cada hijo lleva su porcentaje, su comisión, sus fechas y sus estados de facturación. La migración histórica debe **crear** el padre `VVP-3`.

**Motivo.** Es lo que reflejan los datos reales, y separar así hace imposible el doble conteo al sumar comisiones.

**Descartado:** un solo negocio con los hitos como movimientos de su línea de tiempo (no permitiría comisión por hito), y registros independientes sin relación real (replicaría el problema del Excel).

---

## D-003 · El Excel pasa a ser plantilla de carga, no planilla de trabajo

**Contexto.** El Excel tiene el estado y la etapa duplicados entre `📋 Info General` y `✅ Seguimiento Operativo`, con **19 canjes cuya etapa difiere entre las dos hojas** y ninguna forma de saber cuál es la correcta.

**Decisión.** La app es la única fuente de escritura. El Excel se rediseña como **plantilla de carga masiva**: `.xlsx` descargable desde la app con desplegables alimentados por los catálogos, más un importador que valida fila por fila y reporta los errores.

**Motivo.** Con dos escritores ya hay 19 conflictos sin árbitro; agregar un tercero garantiza más. Las hojas `CONFIG` y `REGLAS CALCULO` quedan como especificación de negocio, no como datos.

**Descartado:** corte limpio sin plantilla (el usuario necesita carga masiva) y mantener el Excel como planilla operativa (perpetúa los conflictos).

---

## D-004 · Reportería en cuatro niveles

**Contexto.** Se preguntó por el alcance de "informar".

**Decisión.** Cuatro niveles: dashboard en pantalla, reporte semanal, reporte mensual comparando contra períodos anteriores, y vista para el directorio de la empresa.

**Consecuencia de diseño.** La comparación entre períodos obliga a normalizar moneda, lo que convierte la tabla UF en requisito y no en opcional, y exige que la separación ganado / pipeline / perdido sea estructural y no un filtro que alguien recuerde aplicar.

---

## D-005 · Se conservan porcentaje y monto, no uno derivado del otro

**Contexto.** El rebate del concentrador aparece en dos columnas del Excel: `AG` como porcentaje (en cero en las 19 filas) y `AP` como monto (poblada en 3). Se propuso quedarse solo con el monto.

**Decisión.** Se conservan ambos, como campos independientes. Regla general: **si una columna del Excel guarda tanto el porcentaje como el monto, ambos van al modelo.** Ya aplica a las comisiones (`AD–AN` tasas, `AO–AT` montos).

**Motivo.** El porcentaje es el acuerdo y el monto es el resultado; compararlos es precisamente el análisis. Permite verificar que la tasa pactada se cumpla, comparar condiciones entre concentradores, y ver su evolución. Bonus: con `monto / pct` queda implícita la comisión propia del concentrador.

**Nota de datos, corregida el 2026-08-20.** Se había reportado que el porcentaje nunca se registró. **Es falso**: la columna AG vale 0,12 en las 13 filas de Concentradores. La regla, corregida el 2026-08-21, es `rebate = base × % comisión del concentrador × 12%` — no 12% de la Comisión Total. Calza al peso en los 3 negocios cerrados. En los 10 perdidos la tasa está y el monto es 0, que es correcto.

---

## D-006 · Los negocios perdidos conservan su comisión calculada

**Contexto.** Los 10 negocios `Perdido` están todos en etapa E2 pero con la comisión calculada completa (4,75M en total). Se advirtió que sumarlos junto a lo ganado produce informes falsos.

**Decisión.** Se conserva la comisión calculada de los negocios perdidos como **comisión potencial no concretada**, y pasa a ser un indicador de primera clase de la reportería. Vive en su propio bucket, separado de lo ganado (8,09M) y del pipeline (1,82M).

**Motivo.** Saber cuánto se habría ganado es útil para análisis, evaluaciones y mejoras. La separación en buckets es lo que hace posible ese análisis, no lo que lo impide.

---

## D-007 · La UF no se autoactualiza: carga manual mensual

**Contexto.** Se evaluó integrar mindicador.cl o el Banco Central para mantener la serie al día. Al verificarlo, **mindicador.cl resultó inalcanzable** (falla por timeout, mientras `api.github.com` y `si3.bcentral.cl` responden 200 en la misma prueba). El servicio del Banco Central sí responde y acepta la serie `F073.UFF.PRE.Z.D`, pero exige registro.

**Decisión.** Sin integración externa. Botón que entrega la plantilla de carga, y el usuario sube el archivo a mano una vez al mes. Sin credenciales de terceros, sin scheduler.

**Motivo.** Es una tarea estacional de una vez al mes; automatizarla no justifica la complejidad ni la dependencia. Render en plan `starter` tampoco incluye cron jobs.

**Consecuencia favorable.** Este sprint pasa a ser el primer caso del patrón plantilla + importador validador, en su versión más simple (dos columnas), lo que acorta los sprints 14 y 15 a "aplicar el mecanismo" en vez de "construirlo".

---

## D-008 · Umbral del aviso de UF: 3 días, más alerta por serie vencida

**Contexto.** Se propuso avisar cuando a la serie le quedaran menos de 15 días.

**Decisión.** El aviso se enciende cuando falten **3 días o menos** respecto del último registro. Aparte va una **alerta** distinta y más visible para el caso de serie vencida (último registro anterior a hoy), porque ahí las conversiones del día no están disponibles.

**Motivo.** La UF va del día 10 al 9 del mes siguiente, así que el colchón oscila entre ~30 días y 1. Con 15 días el aviso se encendería alrededor del 25 de cada mes y quedaría prendido dos semanas — un aviso permanente deja de ser un aviso. Con 3 días se enciende entre el 6 y el 9, cuando la publicación del nuevo tramo ya salió.

---

## D-009 · Un solo servicio en Render, sin dividir a Vercel

**Contexto.** El usuario usa Render y Vercel en otros proyectos y preguntó cómo disponibilizar la app.

**Decisión.** Se mantiene el despliegue actual: un solo Web Service en Render, con el build del front copiado a `backend/static/` y FastAPI sirviendo `/api/*` y la SPA. **No se separa el frontend a Vercel.**

**Motivo.** El argumento decisivo es la cookie de sesión: hoy front y back comparten origen, así la cookie `httponly` funciona sin fricción y `SameSite=Lax` protege de CSRF bloqueando POST desde otros sitios. Separarlos obligaría a `SameSite=None` más CORS con credenciales, perdiendo esa protección — complejidad a cambio de peor seguridad. Además FastAPI con SQLAlchemy contra Neon quiere un proceso persistente, no funciones serverless con arranque en frío. Y lo que Vercel aporta (CDN al borde, preview deploys) no aplica a una herramienta interna de cinco personas.

**Se revisaría si:** el frontend pasara a ser público y con tráfico, o si se quisieran preview deploys por PR.

**Agregados al despliegue actual:** dominio propio `operaciones.viveprop.com`, health check a `/api/health`, y cookie `secure` por defecto en lugar de condicionada a `ENVIRONMENT=production`.

---

## D-010 · Seguridad del acceso diferida

**Contexto.** Se auditó el login. Está bien construido: Argon2id, sesiones en base con revocación real, revalidación de `usuario.activo` en cada request, roles validados en el servidor, y **sin registro público** — la única forma de tener cuenta es que un admin la cree.

**Decisión.** No se toca por ahora. Se retoma después, viendo el funcionamiento. Lo único que entra al plan es la recuperación de contraseña (sprint 22), porque el cambio voluntario ya existía.

**Diferido en su momento y hecho el 2026-08-22** (`D-045`): límite de intentos de login, política mínima de contraseñas, restricción de dominio de email, fuga de tiempos que revelaba qué emails tienen cuenta, y `SESSION_SECRET`, que se eliminó. La condición que el usuario había puesto —"después y viendo el funcionamiento"— se cumplió cuando la app quedó completa y en producción con datos reales.

**Disparador para retomarlo:** antes de que la app quede en manos de seis personas y un directorio.

**Descartado:** SSO con Google Workspace, que habría eliminado la gestión de contraseñas y atado el acceso al empleo. Queda disponible si se retoma el tema.

---

## D-011 · Sin rol super admin ni guardas de autodesactivación

**Contexto.** Hay un solo admin y solo un admin puede resetear contraseñas: si olvida la suya, no hay camino de vuelta dentro de la app. Además `PATCH /admin/usuarios/{id}` no tiene guardas, así que un admin puede cambiar su propio rol o desactivar su propia cuenta y dejar la administración de usuarios inaccesible.

**Decisión.** No se crea rol super admin. Tampoco se agregan las guardas propuestas. El usuario asume el riesgo y respalda sus credenciales por fuera.

**Motivo.** Un cuarto rol solo movería la pregunta un nivel más arriba. Y respecto de las guardas, el usuario prefiere no modificar nada en este punto.

**Riesgo conocido y asumido.** Respaldar las credenciales cubre el olvido de contraseña, que es el escenario probable. No cubre el cambio accidental de rol propio o la autodesactivación, donde la contraseña respaldada no sirve. Para ese caso el rescate es `backend/app/scripts/seed_admin.py`, que promueve a admin, resetea la clave y reactiva la cuenta — requiere una máquina con el `DATABASE_URL`.

**No volver a proponer las guardas** salvo que el usuario lo pida.

---

## D-012 · Orden de ejecución: negocios antes que gestión de canjes

**Contexto.** El usuario indicó que negocios y gestión de canjes tenían prioridad similar y pidió una recomendación.

**Decisión.** El camino crítico es cimientos → negocios → reportería. La gestión de canjes (sprints 19–21) va al final.

**Motivo.** No es por importancia sino por dependencias: canjes ya tiene registro y dashboard funcionando hoy, mientras negocios no tiene nada, y además negocios bloquea la reportería al directorio, que sin él no dice nada sobre dinero. Los sprints 19–21 son el único bloque sin dependencias y se pueden adelantar completos, sin costo para el resto.

**Excepción dentro del orden:** los sprints 12 y 13 (base de cálculo y dashboard) van antes de la carga masiva (14 y 15), porque con 19 negocios cargados y el alta manual funcionando desde el sprint 9, ver el tablero rinde más que automatizar una carga sin volumen.

**Aclaración.** El registro de canjes ya está en producción desde los sprints B1–B4; no hay nada que construir ahí. Lo que queda pendiente de canjes es solo la **gestión** (seguimiento operativo, semáforo, bandeja diaria), y eso es lo que va al final. No se "termina canjes y después se empieza negocios": negocios se construye completo primero.

---

## D-013 · `negocios.id` entero autoincremental, `VVP-N` como columna aparte

**Contexto.** `movimientos.entity_id` es `bigint` y no puede tener foreign key porque apunta a dos tablas distintas (diseño polimórfico). El identificador de negocio en el Excel es texto: `VVP-3`, `VVP-3 PROMESA`.

**Decisión.** La clave primaria de `negocios` es un entero autoincremental. El identificador `VVP-N` va en una columna `codigo` con índice único, separada del PK.

**Motivo.** Es una restricción dura del esquema existente: si el PK fuera texto, negocios no podría usar la tabla `movimientos`, que es justamente el activo que se está reaprovechando. Verificado contra la base: `entity_id` es `bigint`.

> **Modificada el 2026-08-21 por [D-020](#d-020).** La parte del PK entero y del `codigo` aparte **sigue vigente**. Lo que cambia es la estructura padre/hijo: en vez de `padre_id` autorreferencial van dos tablas, `negocios` y `negocio_hitos`.

---

## D-014 · Códigos de `tipos_movimiento` de negocio con prefijo

**Contexto.** `tipos_movimiento.codigo` es la clave primaria global, no compuesta con `entity_type`. Ya existen los códigos `CIERRE`, `CANCELACION` y `COMENTARIO_GENERAL` para `entity_type=canje`, y los tres son plausibles también como movimientos de negocio. Al sembrar los tipos de negocio habría colisión de clave.

**Decisión.** Los códigos de negocio llevan prefijo: `NEG_CIERRE`, `NEG_CANCELACION`, etc.

**Motivo.** La alternativa era cambiar el PK a compuesto `(entity_type, codigo)`, conceptualmente más limpio, pero obliga a migrar la foreign key de `movimientos` y a reescribir las 14 filas existentes. Riesgo de migración innecesario a cambio de elegancia.

**Descartado:** PK compuesto `(entity_type, codigo)`.

---

## D-015 · La documentación se actualiza en el mismo commit que el cambio

**Contexto.** Los tres archivos de este directorio son el mecanismo de control del proyecto: Felipe revisa y decide leyéndolos. Si quedan desfasados respecto al código, pierden su función y el estado real hay que reconstruirlo a mano.

**Decisión.** Regla general: **cada vez que se hace o modifica algo, se actualizan los `.md` que correspondan**, sin que haya que pedirlo. Van en el mismo commit que el cambio que documentan, no en uno aparte.

Qué se revisa en cada cierre de trabajo:

| Archivo | Cuándo se toca |
|---|---|
| `estados.md` | Siempre que un sprint avanza o cambia de estado: la fila, los contadores del resumen, y una entrada nueva de bitácora con lo verificado. |
| `decisiones.md` | Siempre que se toma una decisión de diseño, incluidas las que surgen a mitad de la ejecución. Con contexto, decisión, motivo y lo descartado. |
| `plan_desarrollo.md` | Cuando cambia el alcance, el orden, una restricción de diseño o una decisión pendiente de un sprint. |
| `README.md` | Cuando cambia cómo se instala, configura o ejecuta el proyecto. |

**Motivo.** Documentar después es documentar peor: al momento del cambio están frescos los detalles que importan —qué se verificó, qué se descartó, qué quedó fuera— y son justamente los que se pierden si se posterga.

---

## D-016 · Ninguna conversión UF↔CLP sin fecha, y Decimal en todo el camino

**Contexto.** Implementando el sprint 3 había que decidir la firma del servicio de conversión y el tipo numérico.

**Decisión.** Dos reglas en `app/services/uf.py`:

1. **Toda conversión exige una fecha de referencia.** No existe una función que convierta UF a pesos "al valor de hoy" por defecto.
2. **Se usa `Decimal` de punta a punta**, nunca `float`.

**Motivo.** Lo primero, porque un monto en UF sin la fecha a la que se valorizó no se puede llevar a pesos de forma reproducible, y la reportería comparativa de `D-004` necesita exactamente reproducir el valor de un período pasado. Un default silencioso a "hoy" produciría números que cambian solos entre una consulta y la siguiente.

Lo segundo es aritmética: con `float`, 1080 × 39.735,63 no da exacto, y las comisiones dejarían de cuadrar al peso contra el Excel. Verificado en 4 negocios reales: VVP-4, VVP-1, VVP-2 y VVP-19, los cuatro reproduciendo la columna AC exactamente.

**Consecuencia.** `dias_de_colchon` devuelve negativo cuando la serie está vencida, lo que le da al sprint 5 la señal para distinguir el aviso (3 días o menos, `D-008`) de la alerta (serie vencida).

---

## D-017 · El valor en pesos se puede ingresar a mano y es la base de comisión

**Contexto.** La valorización por regla —monto en UF por la UF de la fecha— es un buen default, pero **no es la verdad**. En Mercado Primario y en Assetplan el valor en pesos del negocio lo determinan liquidaciones externas que muchas veces no coinciden con la regla.

Verificado en el histórico: 17 de 19 filas siguen la regla, y **VVP-2 no**. Su comisión se calculó sobre 81.505.175 en vez de los 104.100.248 que da la UF, un 21,7% menos, y la observación de la planilla lo explica: *"Ver liq Negocio, hubo ajustes por costo credito pie ultima hora"*.

**Decisión.** El modelo guarda los dos valores y el manual manda:

| Campo | Rol |
|---|---|
| `valor_negocio` + `moneda` | El monto como se acordó |
| `fecha_valorizacion` | Nullable; si falta se usa `fecha_inicio` |
| `uf_snapshot` | La UF congelada, para trazabilidad |
| `valor_clp_calculado` | Derivado: `valor_negocio × uf_snapshot` |
| `valor_clp_manual` | Nullable. **Cuando existe, manda.** |
| `motivo_valor_manual` | Por qué se ingresó a mano |

La **base de comisión** es `COALESCE(valor_clp_manual, valor_clp_calculado)`, y el motor trabaja siempre sobre ella, nunca sobre la conversión por UF directamente.

**Motivo.** Los dos valores se conservan, no uno reemplazando al otro, por la misma razón de `D-005`: comparar el calculado contra el real es información. Si las liquidaciones de un concentrador o una inmobiliaria se desvían sistemáticamente de la regla, eso se ve en los datos en vez de perderse.

`motivo_valor_manual` existe porque el único caso real del histórico vino con su explicación escrita. Un número puesto a mano sin motivo no es auditable.

**Consecuencia para el sprint 7.** Los 19 tests de regresión corren sobre la base de comisión, no sobre la conversión por UF. Si corrieran sobre la UF, VVP-2 no reproduciría nunca.

**Corrección de un diagnóstico previo.** Se había reportado que VVP-15 y VVP-17 tenían la UF mal capturada. **Es falso**: ambos siguen la regla y sus números cuadran; la diferencia de 5,38 pesos era redondeo. El caso real de valor externo es VVP-2.

---

## D-018 · La fórmula de comisiones de Concentradores, y los nombres del modelo

**Contexto.** El sprint 7 estaba bloqueado: no se podía determinar qué columna de porcentaje alimentaba qué monto en el modelo Concentradores. La causa era que **los nombres de las columnas del Excel engañan**.

**Lo que las columnas realmente son:**

| Excel | Es | Nombre en el modelo |
|---|---|---|
| `% Comisión Vendedor` (AD) | La tasa que el **concentrador** cobra al vendedor. No es ingreso ViveProp | `pct_comision_concentrador` |
| `% Comisión Comprador` (AE) | La comisión real del negocio, la que paga el comprador | `pct_comision_negocio` |
| `% Broker Comprador` (AI) | La parte de AE que va al corredor aliado | `pct_broker` |
| `% VP Comprador` (AK) | La parte de AE que va a ViveProp | `pct_vp` |
| `% Comisión Agencia Concentrador` (AG) | 12%, la tajada de su comisión que el concentrador comparte | `pct_rebate_concentrador` |

**Decisión.** La fórmula de Concentradores queda:

```
Comision Total = base x pct_comision_negocio
  Broker       = base x pct_broker
  VP Bruta     = base x pct_vp
    Equipo     = VP Bruta x pct_equipo
    Real VP    = VP Bruta - Equipo - Tercero + Rebate
Rebate         = base x pct_comision_concentrador x pct_rebate_concentrador
                 (solo si el negocio cierra)
```

Con la identidad `pct_broker + pct_vp = pct_comision_negocio`, que se cumple en las 13 filas.

Y **se renombran los campos en el modelo**, porque los nombres del Excel ya causaron tres lecturas equivocadas en una sola sesión.

**Motivo.** Verificado al peso en las 13 filas de Concentradores para total, broker, VP bruta y la identidad. El rebate calza en los 3 negocios cerrados; en los 10 perdidos la tasa está registrada y el monto es 0, que es el comportamiento correcto — sin negocio no hay rebate.

**Confirmado por Felipe el 2026-08-21:** el 12% se calcula sobre la comisión que el concentrador cobra al vendedor. Era lectura del dato y quedó ratificada como el acuerdo real.

**Correcciones que arrastra.** Durante la sesión se reportaron tres cosas falsas sobre estos datos, todas por leer la columna equivocada:

1. Que la Comisión Broker de VVP-4 salía de 0,008. Sale de 0,012 (`pct_broker`).
2. Que VVP-15 y VVP-17 tenían la UF mal capturada. No: siguen la regla.
3. Que VVP-16 tenía la base a la mitad y era un cobro parcial o un error. No: su `pct_comision_concentrador` es 4% en vez de 2%, por eso su rebate es el doble. Todo cuadra.

**Tally final: 18 de 19 filas siguen la regla.** El único con base externa es VVP-2.

---

## D-019 · pct_equipo es 10% y editable, y el motivo del valor manual es opcional

**Decisión.** Dos respuestas de Felipe del 2026-08-21:

- **`pct_equipo` = 10%**, como en la práctica, no el 30–40% de los ejemplos de `REGLAS CALCULO`, que quedaron viejos. Pero va como **campo editable por hito**, no como constante, porque debe poder cambiar a futuro.
- **`motivo_valor_manual` es opcional**, no obligatorio. Se había propuesto exigirlo; Felipe prefiere no agregar esa fricción al ingreso.

---

## D-020 · Dos tablas, `negocios` + `negocio_hitos`, en vez de autorreferencia

**Contexto.** `D-002` cerró que un negocio con hitos es padre e hijos, y `D-013` asumió que eso se implementaba con `padre_id` autorreferencial. Al detallar el esquema en `D0` apareció que hay dos formas con consecuencias distintas.

**Decisión.** Dos tablas. `negocios` lleva lo que es del negocio — código, propiedad, alianza, modelo, contrapartes. `negocio_hitos` lleva lo que es de cada liquidación — nombre del hito, fechas, estado, etapa, valorización y comisiones. Aprobado por Felipe el 2026-08-21.

**Motivo.** `D-002` se tomó para hacer el doble conteo **imposible**, y la autorreferencia solo lo hace **evitable**: obliga a que toda consulta de reportería recuerde filtrar las hojas, y si alguien lo olvida el total sale doble sin que nada avise. Con dos tablas, sumar comisiones es siempre `SUM(negocio_hitos)`.

Además desaparecen los estados imposibles: en una sola tabla, la mitad de las columnas quedan sin sentido según el rol de la fila y nada impide llenarlas. Y los 17 negocios simples son un negocio con un hito, sin caso especial ni rama en el código.

**Consecuencias.**

- `movimientos` apunta al **negocio**, no al hito: el pipeline E1–E7 es del negocio, el hito es una liquidación dentro de él.
- `negocio_obligaciones` cuelga del **hito**: cada liquidación se factura y se paga por separado.
- La valorización de `D-017` vive en el hito, porque VVP-3 PROMESA y VVP-3 ESCRITURA tienen bases distintas.
- **Modifica `D-013`** en la parte de `padre_id`. Sigue vigente que `negocios.id` es entero y que `codigo` (`VVP-N`) va aparte con índice único, porque `movimientos.entity_id` es `bigint`.

---

## D-021 · Catálogos: tabla genérica, `etapas` aparte, `modelo_negocio` como enum

**Contexto.** `CONFIG` define seis listas. La pregunta era si van seis tablas chicas con claves foráneas reales o una sola tabla genérica.

**Decisión.** Aprobado por Felipe el 2026-08-21, en tres partes:

1. **Tabla genérica `catalogos(tipo, codigo, nombre, orden, activo, metadatos)`** con `UNIQUE (tipo, codigo)` para las cuatro listas planas: alianzas, estados de facturación, tipos de propiedad y tipos de operación. Un mantenedor, un endpoint, y agregar un catálogo nuevo no requiere migración.
2. **`etapas` como tabla propia**, porque tiene estructura real —código, nombre, responsable, orden— y la consulta el motor de pipeline, no solo un desplegable.
3. **`modelo_negocio` como enum, no como catálogo.** Son tres, y cada uno tiene una fórmula de comisión distinta escrita en código: la de Concentradores (`D-018`) no se parece a la de Primario. Si alguien agregara un cuarto modelo desde un mantenedor, el motor no sabría calcularlo y fallaría en silencio. El enum obliga a que agregar un modelo sea un cambio de código con su test.

**Costo aceptado.** La tabla genérica no tiene claves foráneas por tipo, así que nada a nivel de base impide que un negocio apunte a un catálogo del tipo equivocado. Se acepta a cambio de no mantener seis tablas para listas de 3 a 12 filas que casi no cambian; la validación queda en la capa de servicio.

---

## D-022 · El `% Broker` se aplica sobre la base en los tres modelos, arriendo incluido

**Contexto.** En arriendo era indistinguible si el `% Broker` se calculaba sobre la comisión total o sobre el monto del arriendo, porque cuando las partes pagan 50% y 50% la Comisión Total resulta igual a la base y las dos lecturas dan el mismo número. Divergirían el día que un arriendo no se pague 50/50.

**Decisión.** Felipe confirmó el 2026-08-21 que **funciona igual que en ventas**: el `% Broker` se aplica sobre la base, no sobre la comisión.

```
Comision Broker = base x pct_broker      en los tres modelos
```

**Motivo.** Es la fórmula documentada en `REGLAS CALCULO` y la que ya se verificó en venta. Que sea uniforme en los tres modelos elimina la última rama condicional del motor de comisiones.

**Consecuencia.** El sprint 7 **no tiene decisiones pendientes**. No hace falta dejar un test marcado como se había planeado: la fórmula es una sola.

---

## D-023 · `motivo_perdida` es opcional, con catálogo más texto libre

**Contexto.** Los 10 negocios perdidos están todos en etapa E2 y todos con Assetplan, sumando 4,75M de comisión potencial, y la columna `Motivo_Perdida` del Excel está **100% vacía**. Se propuso pedirle los motivos a Felipe para poder analizar el patrón.

**Decisión.** Felipe resolvió el 2026-08-21 que **el motivo no es obligatorio**, pero que debe existir la opción de registrarlo. No se van a completar los 10 históricos.

Se implementa como **catálogo más texto libre**: un `motivo_perdida_id` opcional apuntando al catálogo de motivos, y un `motivo_perdida_detalle` de texto libre. El catálogo arranca vacío y se puebla con lo que efectivamente se escriba.

**Motivo del diseño.** Que sea catálogo y no solo texto hace que los motivos sean comparables entre negocios cuando alguien los llene. Con texto libre puro, diez frases distintas no se pueden agrupar y el campo no sirve para informar, solo para leer una ficha.

**Consecuencia aceptada.** Los 10 negocios perdidos del histórico quedan sin motivo, así que **el análisis de por qué mueren los negocios en E2 no tiene base retroactiva**. Los 4,75M de comisión potencial perdida se van a poder contar pero no explicar. De aquí en adelante sí, en la medida en que el campo se use.

Cuatro de esas unidades se volvieron a trabajar después — `Mario Kreutzberger 1520 u.316-A` se intentó tres veces y cerró a la tercera — y sin el motivo de la primera caída no se puede saber si el reintento tenía fundamento o fue suerte.

---

## D-024 · Las tasas se nombran por lado de la operación, no por destino

**Contexto.** `D-018` propuso renombrar la columna AD del Excel como `pct_comision_concentrador` y AE como `pct_comision_negocio`. Al implementar el esquema quedó claro que **esos nombres mienten en Mercado Primario**: ahí AD es lo que paga la inmobiliaria —no un concentrador— y AE vale cero, así que "comisión del negocio" sería cero.

**Decisión.** Se nombran por lado de la operación, que es verdadero en los tres modelos:

| Excel | Modelo |
|---|---|
| `% Comisión Vendedor` (AD) | `pct_lado_vendedor` |
| `% Comisión Comprador` (AE) | `pct_lado_comprador` |

El destino de cada uno depende del modelo, y eso vive documentado en `app/services/comisiones.py`, donde se puede explicar en prosa en vez de comprimirlo en un nombre de columna.

**Motivo.** Un nombre que es correcto en dos modelos de tres y falso en el tercero es peor que un nombre neutro. Los nombres del Excel ya causaron cuatro lecturas equivocadas en esta sesión; la solución no era ponerles otro nombre igual de específico, sino uno que no dependa del modelo.

La migración `d3a91f6c25b8` se editó en su lugar en vez de agregar una migración de renombre encima: no estaba pusheada y nada dependía de ella, así que un par "crear y renombrar" en el historial habría sido ruido.

---

## D-025 · Dos correcciones a `REGLAS CALCULO`, verificadas en los datos

Ambas aparecieron al hacer pasar los 19 casos de regresión, **antes de escribir el motor**. Las dos se resolvieron a favor de los datos.

### 1. El porcentaje del equipo se aplica después de sacar al tercero

`REGLAS CALCULO` dice `③ Comisión Equipo = Comisión_VP_Bruta × Factor_Equipo_%`. Los datos dicen:

```
Comision Equipo = (VP Bruta - Comision Tercero) x pct_equipo
Real VP         = VP Bruta - Tercero - Equipo + Rebate
```

Verificado en las 19 filas. Solo se nota en los dos hitos de VVP-3, que son los únicos con tercero, pero ahí son **7.252 pesos** de diferencia en la promesa.

### 2. Cada modelo lee un lado, no se pueden sumar los dos

La tentación era sumar `vendedor + comprador` asumiendo que el lado no usado viene en cero. **Es falso**: en las 13 filas de Concentradores, `% VP Vendedor` vale 0,008 y `% Comisión Comprador` vale 0,02 **sin participar del cálculo**. Sumar duplicaba la VP Bruta en 11 de los 19 casos.

El reparto se resuelve con una rama explícita por modelo:

| Modelo | Comisión Total | Broker | VP Bruta |
|---|---|---|---|
| Mercado Primario | lado vendedor | broker vendedor | VP vendedor |
| Secundario Concentradores | lado comprador | broker comprador | VP comprador |
| Secundario Agencia | suma de ambos | suma de ambos | suma de ambos |

**Lección para lo que viene:** la planilla tiene celdas pobladas que su modelo no usa. No se puede inferir la fórmula de que un valor esté presente.

---

## D-026 · VVP-2 está descuadrado en el origen

**Contexto.** VVP-2 es el único de los 19 negocios que ninguna fórmula consistente reproduce, y la razón no es el modelo sino la planilla.

| | |
|---|---:|
| Comisión Total (AF) | 3.260.207 |
| Comisión Broker (AO) | 2.623.339 |
| Comisión VP Bruta (AQ) | 1.540.671 |
| **Broker + VP Bruta** | **4.164.010** |
| **Descuadre** | **903.803** |

La Comisión Total se bajó a mano por el ajuste de costo de crédito que menciona la observación de la fila, pero **el reparto siguió calculado sobre la base original**. Broker y ViveProp juntos reclaman 903.803 más de lo que entró.

**Precisado al cargar los históricos (sprint 10).** La comparación del motor contra el Excel en los 19 negocios devolvió **una sola diferencia**: `comision_total` de VVP-2. Todo lo demás de esa fila —broker, VP bruta, equipo, real VP— es consistente con la base calculada de 104.100.248,32. Así que el ajuste no fue un cambio de base: **se bajó únicamente el total**, y ningún otro monto se tocó.

**Decisión.** No se fuerza el motor para reproducirlo. El caso queda como `xfail` estricto en `tests/test_comisiones.py`, con el motivo escrito: si algún día se corrige y el test empieza a pasar, pytest avisa en vez de quedar silenciosamente verde. Y hay un test dedicado, `test_vvp2_esta_descuadrado_en_el_origen`, que deja constancia del monto exacto y de que el broker se calculó sobre la base original.

**Resuelto el modo de carga, no el fondo.** VVP-2 entró a la base con los números del Excel tal como están, marcado en el informe de carga. Corregir contabilidad histórica es decisión de Felipe con los datos en pantalla, y el endpoint de edición del sprint 8 ya permite hacerlo.

**Sigue pendiente:** quién absorbió los 903.803, si el corredor aliado tomó parte del ajuste o si ViveProp lo absorbió completo.

**Nota sobre `D-017`.** El caso confirma que el valor manual existe como necesidad —Felipe lo ratificó—, pero VVP-2 tal como está registrado no lo implementa de forma consistente: se overrideó el total sin rehacer el reparto. El diseño de `valor_clp_manual` sigue siendo el correcto; lo que no sirve es tomar VVP-2 como su ejemplo limpio.

---

## D-027 · `etapa` es del negocio; `estado` se queda en el hito

**Contexto.** `D-020` dejó dicho que el pipeline E1–E7 es del negocio y que el hito es una liquidación dentro de él, y por eso `movimientos` apunta al negocio. Pero al implementar el esquema la columna `etapa` quedó en el hito, porque así estaba en el Excel. Eso hacía imposible el sprint 11: un movimiento que apunta al negocio no tiene a qué hito aplicarle la etapa resultante.

**Decisión.** `etapa` pasa a `negocios`. `estado` se queda en `negocio_hitos`.

**Motivo.** Son dos cosas distintas que el Excel había aplanado en la misma fila:

- La **etapa** es la posición del negocio en su avance. Un negocio está en un punto del pipeline, no en varios. Verificado sobre los 18 negocios cargados: **ninguno tiene hitos con etapas distintas** — VVP-3 tiene sus dos hitos en E7, o sea el mismo valor repetido, que es la firma de un campo que pertenece al padre. La migración es sin pérdida.
- El **estado** es el desenlace de cada liquidación. Que la promesa cierre y la escritura se caiga es un escenario real, aunque los 18 negocios históricos no lo muestren todavía. Moverlo al negocio habría cerrado esa puerta.

**Consecuencia en el servicio.** `crear_movimiento_negocio` mueve la etapa del negocio vía `etapa_resultante` del tipo, y los desenlaces (`NEG_PERDIDA`, `NEG_DESISTIMIENTO`) cambian el estado **solo de las liquidaciones que siguen abiertas**. Una promesa ya cerrada no se vuelve perdida porque la escritura se cayó.

**Códigos con prefijo `NEG_`** según `D-014`, verificado: cero colisiones con los 14 tipos de canje.

---

## D-028 · La paleta de los gráficos se valida con un script, no a ojo

**Contexto.** El dashboard de negocios necesitaba color para gráficos, y `theme.ts` ya define las rampas oficiales del proyecto. La pregunta era qué pasos de esas rampas usar.

**Decisión.** Los colores se eligen corriendo un validador que comprueba banda de luminosidad, piso de croma, separación bajo daltonismo, piso de visión normal y contraste contra la superficie. Nada se elige por criterio visual.

**Resultado, con las rampas del proyecto:**

| Uso | Claro | Oscuro |
|---|---|---|
| Serie única de los gráficos | `brand-6` `#3D3EA8` | `brand-4` `#7c7dcf` |
| Tiles de los tres buckets | `good` `#059669`, `brand-6` `#3D3EA8`, `critical` `#DC2626` | los mismos |

**Tres cosas que el validador encontró y que no se habrían visto a ojo:**

1. **`brand-3` `#adade1` no sirve como color de dato**: falla el piso de croma, o sea que se lee como gris. Los tonos claros de la rampa de marca se construyeron como fondos, no como series.
2. **El modo oscuro no puede ser un volteo del claro.** Ningún par de la rampa de marca pasa contra la superficie oscura, así que el paso oscuro se eligió aparte y se validó contra su propia superficie.
3. **La tríada verde / teal / rojo era casi ilegible.** Verde `#059669` y teal `#0891B2` quedan a **ΔE 2,8 en tritanopía** — prácticamente el mismo color. Reemplazar el teal por el indigo de marca sube el peor caso a **18,8**.

**Consecuencia de forma.** El gráfico mensual iba a tener dos series —comisión total y real VP— pero ningún par de la rampa pasaba en modo oscuro. Eso obligó a revisar la forma, y la conclusión fue mejor: **el trabajo de ese gráfico es una sola medida en el tiempo**, cuánto se quedó ViveProp. La comisión total es contexto, no una serie de igual peso, así que va al tooltip y a la tabla. Una serie sola no necesita leyenda ni paleta categórica.

**Regla que queda.** Antes de agregar color a un gráfico nuevo, se corre el validador sobre los pasos candidatos de `theme.ts`. Si un par no pasa, primero se revisa si la forma es la correcta.

---

## D-029 · `sin gestión` es un nivel del semáforo, no `crítico`

**Contexto.** El semáforo de la bandeja mide horas sin gestión contra los umbrales de `CONFIG`: 48 horas es crítico, 24 es advertencia. Pero los 194 canjes abiertos **no tienen ningún movimiento registrado**, porque el seguimiento se hacía en el Excel. Si se midiera desde `fecha_solicitud`, todos serían críticos: hay canjes de 2022.

**Decisión.** `sin_gestion` es un nivel propio, distinto de `critico`, y va primero en el orden de atención.

**Motivo.** Una bandeja que abre con 194 filas rojas no informa nada: el color deja de distinguir. Y son dos problemas distintos que se resuelven distinto — "nunca se tocó" es trabajo por empezar, "se tocó y se dejó estar tres días" es trabajo abandonado. Meterlos en el mismo cubo perdería justamente la información que la bandeja existe para dar.

**Qué entra en la bandeja.** `estado = ACTIVO` **y** etapa distinta de `CERRADO`. Los 31 canjes que están activos pero con etapa cerrada no son trabajo pendiente; es el mismo desalineamiento del dato de Dataprop que motivó el filtro del dashboard de canjes.

**Los umbrales son globales, no por tipo.** `tipos_movimiento` tiene un `sla_horas` propio de cada paso, pero eso mide otra cosa: cuánto debería demorar *ese* paso, no cuánto lleva el canje sin que nadie lo mire. El semáforo usa los dos umbrales de `CONFIG` y nada más.

**Pendiente, sin bloquear.** Cinco tipos de movimiento tienen `sla_es_habil = true` (2 horas hábiles, 24 hábiles). `CONFIG` no define cuál es la ventana de horario hábil, así que ese campo no se usa todavía. Cuando haga falta medir SLA por paso habrá que preguntar el horario.

---

## D-030 · El seguimiento migrado conserva la estructura y admite la fecha aproximada

**Contexto.** La hoja `✅ Seguimiento Operativo` registra **qué** pasos se completaron —287 marcas de "✓ Sí" en diez columnas— pero **no cuándo** se completó cada uno. Las fechas que hay son de otra cosa: `Fecha último update` en 69 filas de 158, `Última gestión solicitante` en 91 y `Última gestión propietario` en 64.

**Decisión.** Se migra un movimiento por paso completado, y cada uno recibe la **mejor fecha real disponible para ese canje** según el lado al que pertenece: los pasos del solicitante usan su fecha de gestión, los del propietario la suya, el acuerdo su propia fecha, y el respaldo es `Fecha último update` o, si falta, la fecha de solicitud del canje.

**Ninguna fecha es inventada.** Lo aproximado es la correspondencia entre la fecha y el paso, y **cada movimiento lo dice en su comentario**: `Migrado del Excel — fecha aproximada · operador Felipe`. Quien lea la línea de tiempo sabe qué está mirando.

**La alternativa descartada** era un solo movimiento por canje resumiendo todo, con la fecha real y sin ambigüedad. Se descartó porque perdería **cuáles** pasos están hechos, que es justamente lo que hace falta para seguir desde donde se quedó. La estructura vale más que la precisión de un dato que el origen nunca tuvo.

**Lo que no se convirtió en movimiento.** Los pasos marcados con "✗ No" y las observaciones generales van juntos en un `COMENTARIO_GENERAL` por canje. Un "No" es información —que la propiedad no estaba disponible aparece 18 veces— pero no es un paso completado, y no valía inventar tipos de movimiento para representar el fracaso de cada paso.

**La migración no mueve etapas.** `etapa_resultante` va nulo en todos los movimientos migrados: la etapa de cada canje viene de Dataprop y es más confiable que reconstruirla desde el checklist.

**Consecuencia en la bandeja.** Pasó de 194 canjes indiferenciados a **146 sin gestión y 48 críticos**. Esos 48 son casos reales de "se trabajó y se dejó estar", que antes eran indistinguibles de los que nunca se tocaron. Eso es exactamente lo que `D-029` buscaba poder distinguir.

---

## D-031 · En el reporte semanal, "avanzó" es toda actividad registrada

**Contexto.** La primera versión del reporte contaba como "avanzó" solo los movimientos que cambian de etapa (`etapa_resultante is not None`). Probada contra `dev` sobre la semana del 10 al 16 de agosto, devolvió **cero avanzados sobre 44 movimientos reales**. Los movimientos migrados del Excel llevan la etapa nula a propósito (`D-030`), así que el filtro dejaba el reporte vacío sobre toda la historia previa.

**Decisión.** "Avanzó" es todo movimiento del período que no sea una caída. Cuando el movimiento sí mueve la etapa, la columna la muestra; cuando no, dice "sigue igual".

**Motivo.** No es solo salvar la historia migrada. En un reporte semanal lo que importa es dónde hubo progreso, y registrar la confirmación por WhatsApp del corredor propietario **es** progreso aunque la etapa no se mueva: son ocho de los diez pasos del checklist de canjes. Un reporte que no ve la gestión registrada no sirve para la reunión de los lunes, que es para lo que existe.

**Las caídas se cuentan aparte y no en las dos columnas.** Una cancelación es un movimiento, pero contarla también como avance infla las dos cifras con el mismo hecho.

**Descartado:** una tercera columna que separe "avance de pipeline" de "gestión sin cambio de etapa". Es más preciso y es lo que el reporte muestra igual dentro de la lista, pero cuatro cifras de cabecera ya son las que alguien lee de un vistazo; una quinta se lee como ruido.

---

## D-032 · El umbral de estancado es un parámetro, no una constante de negocio

**Contexto.** "Estancado" no es un estado guardado: es una ausencia — algo abierto sin movimiento en más de N días. Había que elegir N.

**Decisión.** El default es **14 días** y es un control visible en la pantalla, con 7 / 14 / 30 a un clic. No entra en `CONFIG`.

**Motivo.** Los 14 días son una estimación mía, no un dato del negocio: nadie los definió. Esconderlos en `CONFIG` los haría parecer una regla acordada. Como control, quien lee el reporte —que sabe mejor qué es "mucho" en su semana— lo mueve y ve el efecto.

**Por qué no reusa los umbrales de la bandeja.** Los 48/24 horas de `CONFIG` miden otra cosa: la bandeja diaria pregunta "qué me toca hoy" sobre canjes abiertos. El reporte semanal pregunta "qué se quedó atrás esta semana" sobre los dos dominios. Compartir el número porque ambos midan tiempo sin gestión sería confundir dos preguntas distintas.

**El umbral es estricto.** A los 14 días exactos todavía no está estancado; a los 15 sí. Sin eso, el límite dependería de a qué hora se abre el reporte.

---

## D-033 · La cookie de sesión es `secure` por defecto, no por configuración

**Contexto.** `set_session_cookie` marcaba `secure=settings.environment == "production"`. La cookie de sesión es la credencial completa: quien la tenga es el usuario. Sin `secure`, el navegador la manda también sobre HTTP.

**El modo de falla es silencioso.** Si `ENVIRONMENT` faltaba en Render, venía vacía, o decía `prod` en vez de `production`, la cookie salía **sin** `secure` y la app seguía funcionando exactamente igual. Nada en la aplicación falla, ningún log lo dice, ninguna pantalla se ve distinta. Solo la sesión viaja expuesta.

**Decisión.** Se invierte: `secure` está activo salvo que el ambiente se declare local, y solo tres valores exactos cuentan como local — `development`, `local`, `test`.

**Motivo.** La pregunta correcta no es "¿estamos en producción?" sino "¿tenemos permiso para bajar la defensa?". Con la lógica anterior, un valor desconocido caía del lado insegura; ahora cae del lado seguro. Y cuando la configuración local se equivoca, el navegador no guarda una cookie `secure` sobre `http://localhost` y el login deja de funcionar **de inmediato y en la máquina del que se equivocó** — la dirección correcta para que un error se note.

**Descartado:** una variable propia `COOKIE_SECURE`. Sería otra cosa que hay que acordarse de configurar, y el problema que se está arreglando es justamente que algo dependía de acordarse.

---

## D-034 · Un `/api/...` sin router es 404, no la SPA

**Contexto.** FastAPI sirve la SPA con un catch-all: cualquier ruta que no matcheó ningún router devuelve el `index.html`, porque el ruteo de la SPA es del lado del navegador. Pero el catch-all no distinguía `/negocios` —una pantalla— de `/api/negocios-mal-escrito` —un endpoint que no existe.

**Verificado en producción el 2026-08-21:** `/api/esto-no-existe` respondía `200 text/html`.

**Decisión.** Todo lo que empiece con el prefijo `api/` y no haya matcheado un router es un 404. El resto sigue cayendo en el `index.html`.

**Motivo.** Un 200 con HTML donde el cliente espera JSON hace que el error se manifieste lejos de su causa: el `fetch` no falla, falla el `.json()`, o peor, algo más adelante recibe `undefined`. **Costó una verificación mal leída en esta misma sesión**: se consultó `/api/health/db` contra producción, volvió 200, y por un momento se interpretó como que el endpoint nuevo ya estaba desplegado. Era el `index.html`.

**Ojo con el prefijo.** La comparación es contra `api` exacto o `api/`, no `startswith("api")`: una futura ruta `/apiario` es de la SPA. Hay un test que lo fija.

**Aparte, y en la misma función:** el servido de archivos armaba la ruta como `STATIC_DIR / full_path` sin revisar el resultado. Un `full_path` que sube de directorio apunta fuera de `static/`, y abajo están el código y el `.env`. Ahora se resuelve y se comprueba que quede dentro. **Producción no estaba expuesta** —`/%2e%2e/.env` devuelve el `index.html`, porque uvicorn o el proxy de Render normalizan la forma codificada antes del handler— pero por `TestClient` el `../` llegaba entero y la lógica anterior servía el archivo. Se arregló igual: que un proxy normalice no es una defensa de la aplicación, y puede cambiar sin aviso.

---

## D-035 · El health check de Render no toca la base

**Contexto.** `healthCheckPath` estaba sin definir, así que Render usaba la raíz: devuelve el `index.html`, un 200 que no prueba que la aplicación arrancó. Había que apuntarlo a `/api/health`, y ahí surgió la pregunta de si ese endpoint debería confirmar que la base responde.

**Decisión.** Dos endpoints separados. `/api/health` dice que el proceso está vivo y no consulta nada externo — es el que mira Render. `/api/health/db` hace un `SELECT 1` y devuelve 503 si falla — es para diagnosticar, no para el monitoreo automático.

**Motivo.** Neon suspende la rama cuando no hay tráfico, y despertarla toma unos segundos. Si el chequeo de Render dependiera de eso, un despertar lento se leería como servicio caído y Render reiniciaría un proceso que no tiene nada roto — un reinicio que además vuelve a pagar el arranque. Son dos preguntas distintas: "¿está corriendo?" es de monitoreo, "¿puede trabajar?" es de diagnóstico.

**El de diagnóstico existe por un caso concreto:** el 503 del 2026-08-20, donde no había forma rápida de distinguir "se cayó el servicio" de "se cayó la base". Con `/api/health/db` la respuesta es una consulta.

**No devuelve el mensaje de la excepción**, solo su tipo. El detalle de una falla de conexión trae el host y a veces el usuario de la base, y este endpoint no pide sesión.

---

## D-036 · La UF se baja del SII, verificado contra 617 fechas

**Contexto.** La serie se cargaba a mano con una plantilla, una vez al mes. El usuario pidió automatizarla y nombró tres fuentes posibles: `mindicador.cl`, el Banco Central y el SII.

**Se probaron las tres antes de escribir una línea de código.**

| Fuente | Resultado |
|---|---|
| **SII** | Responde. Una página HTML por año, con la serie completa. |
| `mindicador.cl` | No respondió: timeout en el puerto 443, dos intentos. |
| **Banco Central** | Responde, pero redirige a una página de error sin credenciales. |

**Decisión.** El SII.

**El motivo es que se pudo verificar.** Se parsearon las páginas de 2025 y 2026 y se compararon contra la serie que ya estaba en Neon —que viene del Excel, o sea un origen independiente— con este resultado: **617 fechas en común, 0 diferencias.** No una muestra: todas. Dos orígenes que no se hablan entre sí coinciden al centavo.

**Lo que se descartó y por qué.** `mindicador.cl` entrega JSON, que es bastante más robusto que parsear HTML, pero no se pudo verificar desde acá y además es un servicio gratuito de un tercero sin compromiso de disponibilidad. El Banco Central **es** la fuente de origen y tiene API de verdad; el costo es crear una cuenta y guardar usuario y clave. Queda anotado como el camino de mejora si el parseo del SII se vuelve frágil.

**El riesgo asumido es explícito:** parsear HTML se rompe si cambian la página. Se mitiga de dos formas. El parser **falla ruidoso** —si no encuentra la tabla, o si entiende menos de 20 fechas, levanta excepción en vez de cargar poco— y **si falla no se escribe nada**, la misma regla de la carga manual. Y la carga manual se queda: es la salida cuando esto se caiga.

---

## D-037 · La descarga corre en el propio servicio, no en un Cron Job

**Contexto.** Había que ejecutar la descarga periódicamente. En Render, un Cron Job es un servicio aparte que se cobra aparte.

**Decisión.** Una tarea `asyncio` dentro del web service que ya está corriendo, que despierta una vez al día. Arranca y se corta con el ciclo de vida de la app.

**Motivo.** No agrega infraestructura ni costo para algo que el SII publica una vez al mes. Y es seguro repetirla: la escritura es un upsert por fecha, así que correrla dos veces —o desde dos instancias— da el mismo resultado.

**No pide la página todos los días para nada.** Solo descarga cuando quedan menos de 20 días de serie por delante. El SII publica hasta el 9 del mes siguiente, así que con ese umbral el chequeo encuentra el mes nuevo poco después de que aparece.

**Nunca tumba la aplicación.** Si el SII no responde o cambió el formato, la tarea lo registra y sigue durmiendo. La UF ya cargada alcanza para valorizar y la plantilla sigue estando.

**Dos cosas que salieron mal al construirla, las dos silenciosas:**

1. **Corría muda.** El primer arranque no dejó ninguna línea en el log, porque uvicorn configura handlers solo para sus propios loggers y el `log.info` nuestro se descartaba. Un proceso automático sin evidencia de haber ocurrido es el mismo problema de `D-033`. Se configura el logging en el arranque.
2. **Se habría levantado en cada test.** `TestClient` como context manager corre el lifespan de verdad, así que la suite habría salido a internet y escrito en Neon. Hay un interruptor `tareas_de_fondo` que el conftest apaga, y que además permite apagarla en producción por variable de entorno sin tocar código.

**El caso que la habría hecho fallar a los once meses.** Las páginas del SII son una por año, y la del siguiente devuelve 404 hasta que la publican. En la segunda mitad de diciembre la UF de enero vive en la página del año que viene, así que en diciembre se consultan los dos años y ese 404 no es un error. En enero se consulta también el año anterior: si esto no corrió unos días sobre el cambio de año, diciembre quedaría con un hueco, y **un hueco en el medio de la serie no lo avisa nadie** — el aviso de vencimiento mira la última fecha, no los agujeros.

---

## D-038 · Cargar UF es solo de admin; consultar su estado, de todos

**Contexto.** El usuario pidió mover Unidad de Fomento al grupo ADMIN del menú. Ese grupo se dibuja solo si el rol es admin, así que el enlace desaparecía para gerencia y operaciones — pero la ruta seguía alcanzable escribiendo la URL, y operaciones podía cargar.

**Decisión.** Se restringen las dos cosas: la ruta `/uf` en el frontend y las escrituras en el backend (`plantilla`, `importar`, `actualizar-desde-sii`) exigen rol admin.

**`GET /uf/estado` queda abierto a cualquier usuario con sesión.** Lo consulta el aviso que aparece en la página de Negocios y en su dashboard: sin UF vigente no se puede valorizar, y quien opera necesita saberlo aunque no pueda arreglarlo. Restringirlo dejaría a operaciones sin entender por qué no puede dar de alta un negocio.

**El riesgo que se aceptó.** Deja al admin como único punto de rescate humano: si la serie vence y no está, no se puede valorizar nada. Se le preguntó al usuario justamente eso y eligió restringir. Pesa mucho menos ahora que la serie se actualiza sola (`D-037`), que era la condición que hacía razonable la decisión.

---

## D-039 · La plantilla de negocios pide entradas, no resultados

**Contexto.** `negocio_hitos` tiene unas 35 columnas. Había que decidir cuáles entran en la plantilla de carga masiva. La tentación era espejar el Excel, que trae las comisiones calculadas en sus propias columnas.

**Decisión.** La plantilla tiene 32 columnas y **ninguna es un monto de comisión**. Pide el valor del negocio, la moneda, la fecha de valorización y las tasas; comisión total, broker, rebate, VP bruta, equipo, tercero y real VP las calcula el motor al cargar.

**Motivo.** Si la plantilla tuviera esas columnas, alguien escribiría un número a mano y la garantía que el motor existe para dar se perdería en silencio, fila por fila. Hay un test que falla si alguna de esas columnas aparece: la propiedad se protege, no se confía en que nadie la agregue.

**Corolario incómodo, y hay que decirlo:** por eso mismo **esta no es la herramienta para los 19 históricos**. Esos se migran fieles y sin recalcular (`D-026`), porque siete están cerrados con plata ya facturada y `VVP-2` viene descuadrado del origen. Para eso sigue estando `scripts/cargar_negocios.py`, que migra tal cual y reporta las diferencias contra el motor. Se evaluó agregar un grupo de columnas de override para cubrir los dos casos con una sola herramienta y **se descartó**: sería exactamente el agujero que el párrafo anterior cierra.

**Una fila es un hito, no un negocio.** Si el código se repite son varios hitos del mismo negocio, como `VVP-3` con su PROMESA y su ESCRITURA. Y los datos de nivel negocio —propiedad, modelo, alianza, etapa— tienen que coincidir entre esas filas: si la fila 5 dice una dirección y la fila 8 otra para el mismo código, es error. No hay forma de saber cuál gana, y elegir una en silencio sería peor que rechazar.

**Las tasas se escriben en porcentaje**, 2 para 2%. La base guarda la fracción. Se pide en porcentaje porque es como están escritas en los contratos y en la hoja de reglas; pedirle a alguien que escriba `0,0252001208200461` es pedirle que se equivoque.

**Los códigos válidos van en una hoja generada desde la base**, no escrita en el código. Una alianza nueva aparece sola en la próxima plantilla que alguien baje, y las inactivas no se ofrecen porque no tiene sentido cargar contra ellas. Misma razón por la que los desplegables del front salen de la API.

**Los errores de contenido vuelven con 200, no con 4xx.** Son decenas de mensajes por fila y el front los lista; un 400 obligaría a inventar una forma aparte de transportarlos. Lo que sí es 400 es un archivo que no se puede leer o al que le faltan columnas: ahí no hay nada que listar.

**Y las tres reglas heredadas de la carga de UF**, por los mismos motivos: si hay un solo error no se escribe nada, cargar dos veces actualiza en vez de duplicar, y **nunca borra** — si la base tiene dos hitos y el archivo trae uno, el otro se queda. Un import que borra lo que no menciona convierte un archivo incompleto en pérdida de datos.

---

## D-040 · El cambio forzado de clave lo aplica la API, no la pantalla

**Contexto.** Un admin resetea la clave de alguien, esa persona recibe una temporal y tiene que elegir una propia antes de usar la app. La pregunta es dónde se impide "usar la app".

**Decisión.** En `get_current_user`. Con el flag `debe_cambiar_password` puesto, **todos** los endpoints devuelven 403 salvo tres: `/auth/me`, `/auth/cambiar-clave` y `/auth/logout`.

**Motivo.** Si el bloqueo lo aplicara solo el front, la clave temporal serviría para usar toda la API con `curl` y el cambio forzado sería decorativo. La pantalla que tapa la app existe igual, pero para que la persona entienda qué pasa en vez de chocar contra un 403 en cada vista.

**Los tres exentos usan una dependencia aparte**, `resolver_usuario`, que resuelve la sesión sin exigir la clave al día. Separarlas no es elegancia: con la dependencia estricta en `cambiar-clave`, la persona quedaría bloqueada **del único endpoint que la desbloquea**. Hay un test que fija exactamente eso.

**El reset cierra las sesiones abiertas de esa persona.** El flag se mira al resolver la sesión, así que una pestaña ya logueada seguiría operando con todos los permisos hasta doce horas y el cambio forzado no se aplicaría nunca. Se borran sus sesiones, no las de quien resetea.

**La clave temporal la genera el sistema.** Doce caracteres, sin `I`, `l`, `1`, `O` ni `0`: se dicta por teléfono o se copia de un chat y esos cinco se confunden entre sí. Se devuelve **una sola vez** y lo que queda en la base es su hash. Se descartó que la eligiera el admin: una inventada en el momento termina siendo "viveprop2026", y hay que transmitirla por un canal aparte igual.

**Nadie puede resetear su propia clave.** Para eso está "cambiar contraseña". Si el único admin se reseteara a sí mismo y perdiera el texto que aparece una sola vez, quedaría fuera de la app sin nadie que pueda ayudarlo.

**La clave nueva no puede ser igual a la actual.** Sin eso, "cambiar" la temporal por sí misma limpiaría el flag sin cambiar nada.

**Lo que sigue sin hacerse, a propósito:** no hay política mínima de contraseñas — `cambiar-clave` acepta `"1"`. Está en la lista de diferidos por decisión del usuario y no se tocó. Vale decir que debilita esto: el cambio forzado obliga a elegir una clave, no a elegir una buena.

**De paso, una deuda de tests que esto destrabó.** `sesiones` no se creaba en la base de test porque su clave primaria usaba el `UUID` del dialecto de Postgres, y eso dejaba **toda la capa de autenticación sin cubrir**. Se cambió a `sa.Uuid`, que en Postgres emite el mismo tipo nativo —verificado comparando el DDL compilado— y en SQLite un `CHAR(32)` con la conversión incluida. No cambia nada en producción y ahora la cadena completa se prueba.

---

## D-041 · La variación contra cero es nula, no infinita

**Contexto.** El reporte mensual compara el mes con el anterior y con el mismo mes del año pasado. Con siete cierres repartidos en siete meses distintos, los meses de referencia en cero no son un caso raro: son lo habitual.

**Decisión.** Cuando la referencia es cero, el porcentaje se devuelve **nulo**. La pantalla muestra "nuevo" y la diferencia absoluta.

**Motivo.** Si el mes pasado hubo 0 y este hay 3, eso no es "+300%" ni "+∞": no hay base contra la que comparar, y cualquier número que se ponga ahí está inventado. Un porcentaje falso en un reporte que alguien va a mirar para decidir es peor que un guión honesto. La diferencia absoluta sí significa algo y es lo que se muestra.

**Es el criterio del sprint, no un detalle.** "Listo cuando: un mes sin datos no rompe la comparación" se cumple así, y hay tests que lo fijan en las dos direcciones: sin base da nulo, con base da el porcentaje.

**Dos comparaciones y no una.** El mes anterior dice si la tendencia corta sube o baja; el mismo mes del año pasado dice si eso es tendencia o estacionalidad. Con una sola no se distingue "vamos mal" de "agosto siempre es flojo". Se descartó una serie de veinticuatro meses: eso ya está en los gráficos "por mes" del dashboard y responde otra pregunta.

**Un límite del dato, dicho donde se ve.** Los canjes cancelados se cuentan por **fecha de solicitud**, porque `canjes` no guarda cuándo se canceló. Lo que se responde es "de los que entraron este mes, cuántos terminaron cancelados". Y después de la limpieza del 2026-08-21 esa cifra coincide con la de solicitados en todos los meses pasados, porque todo lo que entró quedó cancelado: es cierto, pero como métrica de historia no informa nada hasta que entren canjes nuevos.

---

## D-042 · Un negocio tiene tres duraciones distintas, y ninguna es `actualizado_en`

**Contexto.** Los procesos de negocio duran de un mes a varios, y algunos siguen abiertos. La tabla de Negocios no tenía **ninguna** columna de fecha, así que no se podía saber si un negocio llevaba una semana o siete meses. El usuario pidió ver fecha de inicio por un lado y última actualización por el otro.

**Decisión.** Tres duraciones, no una:

| Cuál | Cómo sale | Qué responde |
|---|---|---|
| `dias_abierto` | hoy − fecha de inicio | "lleva 4 meses abierto" |
| `dias_sin_gestion` | hoy − último movimiento | "3 semanas que nadie lo toca" |
| `dias_en_etapa` | hoy − último cambio de etapa | "2 meses trabado en E4" |

**Motivo.** Un negocio puede llevar seis meses abierto y estar avanzando perfecto; otro puede llevar dos meses y estar muerto. Una sola cifra no distingue esos casos. Y la tercera es la más valiosa: dice **dónde** se atascan los procesos, que es lo que va a permitir proyectar cierres cuando haya historia.

**"Cuándo se hizo algo" y "cuándo cambió de etapa" son dos consultas separadas** a propósito: un negocio puede tener diez movimientos de gestión sin salir de E4, y ahí está justamente el atasco que interesa ver.

**La última gestión es la del último movimiento, no `actualizado_en`.** Esa columna existe y era la opción obvia, pero se mueve con cualquier edición: corregir una dirección mal escrita haría que un negocio parezca activo sin que haya pasado nada. Un timestamp técnico disfrazado de señal de negocio es peor que no tenerlo, porque nadie sospecha de él. Es la misma distinción del reporte semanal: el estado dice dónde estás, el movimiento dice qué cambió.

**El nulo significa "no se sabe", no cero.** Y esto costó una corrección: la primera versión devolvía `dias_abierto = 0` para los negocios donde inicio y cierre coinciden, y la tabla los mostraba como "hoy" — incluido uno de agosto de 2025. El razonamiento equivocado era "cerró el día que empezó, eso sí se sabe". No se sabe: lo que se sabe es que el Excel traía una sola fecha y la migración la puso en las dos columnas. Un cierre el mismo día existe en teoría, pero en un negocio de ciclo largo es tan raro que conviene equivocarse del lado de "no se sabe" antes que mostrar un cero que se lee como un hecho.

**Consecuencia, y es información:** de los 18 negocios, 15 no tienen duración calculable. El único histórico que sí la tiene es `VVP-3`, con 83 días entre la promesa y la escritura, porque es el único con dos fechas distintas. Que 15 muestren un guión no es un defecto de la pantalla: es el estado real del dato, y hacerlo visible es lo que justifica empezar a usar el pipeline.

**Los umbrales del semáforo son en días, no en horas.** Los 48/24 horas de `CONFIG` son de canjes, donde el ciclo es de días. Acá 30 y 14 días, y son una estimación, igual que el umbral de estancado del reporte semanal: viven en el código y no en `CONFIG` porque no son una regla que alguien haya acordado.

---

## D-043 · El cierre mensual se compara con ventanas móviles, no mes contra mes

**Contexto.** El sprint 17 se entregó comparando el mes con el mes anterior y con el mismo mes del año pasado. El usuario señaló que este negocio no va mes a mes: cada proceso dura entre un mes y muchos, y algunos siguen abiertos.

**Los datos le dan la razón.** De 11 meses con actividad, **4 estuvieron vacíos** (36%). El ticket varía cuatro veces, entre 516.304 y 2.110.526. Con ~1 cierre por mes y esa dispersión, la variación mes contra mes no mide desempeño: mide ruido. Un mes en cero no es un mes malo, es que ningún proceso terminó de madurar.

**Decisión.** El titular pasa a ser una **ventana móvil** contra la ventana equivalente inmediatamente anterior, más el **año corrido** contra el mismo tramo del año pasado. El mes calendario se queda, pero como detalle de "qué cerró".

**El contraste, con los datos reales:** la serie mensual de comisión real es 0 / 2,1M / 0 / 0 / 1,05M —no se puede leer una tendencia ahí—. La de seis meses dice que subió hasta 5,2M en diciembre y viene bajando a 2,8M.

**Las ventanas no se solapan.** La referencia de marzo-agosto es septiembre-febrero, no octubre-marzo. Si se solaparan, el mismo cierre contaría en los dos lados y la variación saldría diluida hacia cero.

**El año corrido compara el mismo tramo**, enero-agosto contra enero-agosto. Comparar ocho meses contra doce diría que el año viene mal cuando solo viene incompleto.

**El largo de la ventana es un control** —3, 6 o 12 meses— y no una constante: el horizonte correcto depende de qué se esté mirando, y quien lee el reporte lo sabe mejor. Es el mismo criterio del umbral de estancado del reporte semanal.

**Se descartó** la comparación mes contra mes, que era justo el ruido a eliminar, y el "mismo mes del año anterior": la estacionalidad necesita dos o tres años de datos para ser medible, y hoy compararía 1 contra 0. Se descartó también una serie de veinticuatro meses, que responde otra pregunta y ya está en los gráficos "por mes" del dashboard.

**Lo que el rediseño dejó ver, y la vista mensual escondía:** en los últimos 6 meses las liquidaciones cerradas subieron 100% (4 contra 2) mientras la comisión real bajó 19,3%. Más cierres con ticket más chico. Eso es un hecho del negocio, y ninguna comparación mes contra mes lo iba a mostrar.

---

## D-044 · La vista directorio se entrega con supuestos declarados, y la proyección va como rango

**Contexto.** El sprint 18 pedía una presentación ejecutiva exportable, y su nota decía "pendiente de consultar: qué quiere ver el directorio, antes de diseñarla". Se preguntó **cinco veces** a lo largo de la ejecución y la respuesta no llegó.

**Decisión.** Se entrega con supuestos explícitos, y la propia pantalla lo dice. Seguir bloqueado era peor servicio que dar algo concreto que se pueda corregir: es más fácil reaccionar a una versión que responder una pregunta abierta.

Los cinco supuestos, para poder discutirlos uno por uno: cuánto entró (año corrido y últimos 12 meses), de dónde vino (mezcla por modelo y por alianza), qué hay por delante (el pipeline), qué se perdió y cuánto valía, y una proyección.

**La proyección va como rango, nunca como cifra, y con el `n` al lado.** La tasa de conversión es 7 de 17 —41,2%— pero con ese tamaño de muestra el intervalo de confianza al 95% va de **17,8% a 64,6%**. Multiplicar el pipeline por "41%" es en realidad multiplicarlo por "algo entre un quinto y dos tercios". Un directorio decide plata leyendo esto, y darle una cifra puntual sobre 17 casos sería falsa precisión. Los tres escenarios —pesimista, esperado, optimista— **no son criterios inventados**: son el mismo dato con su margen de error.

**El `n` viaja siempre junto a la tasa.** Un 41% sobre 17 casos y un 41% sobre 1.700 se leen igual en una pantalla y no valen lo mismo. La estructura de datos lo hace difícil de omitir.

**La vista declara lo que no puede decir.** No hay forma de proyectar *cuándo* va a entrar la plata del pipeline: eso necesita duración de ciclo y conversión por etapa, y hoy no existe ni un dato —los históricos traen la misma fecha de inicio y de cierre porque el Excel tenía una sola, y no hay ni un movimiento de negocio registrado—. Aparece un aviso que lo explica, y **desaparece solo** cuando haya al menos tres cierres con fechas distintas. Informar la carencia es mejor que rellenarla con una estimación que nadie podría auditar.

**Dos decisiones de honestidad estadística más.** El ticket se muestra como **mediana y rango**, no como promedio: con una dispersión de 4x —de 516.304 a 2.110.526— un solo negocio grande corre el promedio y da una cifra que no representa a ninguno. Y los negocios **activos no entran** en la tasa de conversión: un negocio abierto todavía no se ganó ni se perdió, y contarlo del lado perdido diría que ya fracasó.

**"Exportable" se resolvió con estilos de impresión**, no generando un PDF. `Ctrl+P` produce una hoja limpia: se ocultan el menú, los botones y las notas de trabajo, y se aplanan sombras y fondos, que en papel solo gastan tinta. Se descartó un generador de PDF: sería una dependencia nueva para producir lo que el navegador ya hace bien, y obligaría a mantener dos maquetaciones en paralelo que se desincronizan a la primera de cambio.

---

## D-045 · El límite de intentos corta antes de verificar el hash

**Contexto.** `/auth/login` aceptaba intentos infinitos. Se había diferido con una condición: *"después y viendo el funcionamiento incorporamos límites y seguridad"*. Con la app completa y en producción con datos reales, la condición se cumplió.

**Y había un número.** Cada intento cuesta **70 ms de CPU** verificando el hash Argon2id, medido. Eso convierte la falta de límite en dos problemas distintos: fuerza bruta contra una contraseña que hasta ese día podía ser `"1"`, y **saturación**, porque unos cientos de peticiones por segundo dejan el proceso moliendo hashes y la app deja de responder.

**Decisión.** El límite se evalúa **antes** de verificar la contraseña.

**Motivo, y es el punto entero.** Un límite aplicado después habría frenado la fuerza bruta y no la saturación: el atacante seguiría gastando 70 ms de CPU por intento aunque el resultado se descartara. Cortando antes, un intento bloqueado no toca el hash. Hay un test que cuenta las llamadas a `verify_password` y exige que sean **cero** cuando la clave está bloqueada.

**Se cuenta por email y por IP, y las dos hacen falta.** Por email protege la cuenta —alguien que conoce un correo y prueba claves—, umbral 5. Por IP protege el servidor —alguien que prueba correos al azar, que después de cerrar la fuga de tiempos también consume CPU—, umbral 20, más alto porque una oficina comparte salida y varias personas pueden equivocarse el mismo día. Una sola de las dos deja el otro flanco abierto.

**En la base, no en memoria.** Un contador en memoria se reinicia con cada deploy y no sirve si alguna vez hay más de una instancia. La tabla se limpia sola: entrar bien borra la fila, y la tarea diaria saca las que quedaron sin actividad.

**El bloqueo es una ventana, no un contador que se descarta.** Pasados los 15 minutos se vuelve a contar de cero. Es más fácil de explicar a quien se quedó afuera que una curva exponencial, y para dos usuarios internos alcanza.

**La política de contraseñas es largo mínimo —10— más una lista corta de las peores.** No se exigen mayúsculas ni símbolos: esas reglas producen `Viveprop2026!`, que cumple todo y es adivinable, en vez de contraseñas mejores. El largo es lo único que correlaciona de verdad con resistencia. En la lista de prohibidas va `viveprop` y sus variantes, porque es exactamente lo que alguien elige cuando tiene que inventar una clave en el momento — y ya se había predicho ese nombre al diseñar el reset.

**La fuga de tiempos se cerró y se midió.** Antes, un email desconocido volvía sin tocar ningún hash y uno real gastaba 70 ms: la diferencia decía qué correos tienen cuenta. Ahora siempre se verifica un hash, contra un señuelo calculado una vez al importar cuando el usuario no existe. Medido en vivo: **1,02x de diferencia**, contra ~70x antes.

**Dos errores propios que atrapó `alembic check`,** y que justifican haberlo dejado limpio el día anterior: el modelo nuevo no estaba importado en `app/models/__init__.py`, así que `autogenerate` proponía **borrar la tabla** que la migración acababa de crear; y el índice llevaba en la migración un nombre distinto del que genera `index=True` en el modelo.

---

## D-046 · Los hitos históricos se dejan reproducibles por el motor, y guardar una liquidación cerrada pide confirmación

**Contexto: la pantalla para cerrar un negocio destapó un defecto en los datos.** La auditoría encontró que la app no permitía cerrar un negocio desde ninguna pantalla —el motor de comisiones, la pieza más grande del proyecto, no tenía forma de recibir un cierre—. Al construir el formulario y probarlo contra `dev`, cerrar `VVP-17` le **bajó la comisión real de 774.691,95 a 759.166,55** sin que se tocara una sola tasa.

**No era el motor.** Sus 19 casos de regresión pasaban y siguen pasando. El defecto estaba en el paso anterior, `resolver_valorizacion`, que **nunca tuvo prueba propia**: `test_comisiones.py` recibe la base en pesos ya calculada y verifica el reparto, así que la conversión de UF a pesos no estaba cubierta por nada.

**La causa.** `resolver_valorizacion` toma la UF de `fecha_valorizacion`, y si está vacía la de `fecha_inicio`. Trece de los 19 hitos vinieron con esa fecha en nulo, así que al primer guardado se revalorizaban con la UF del día de inicio y **sobreescribían la `uf_snapshot` que traía el Excel**. `D-026` había cargado los montos tal cual justamente para no pasarlos por el motor; la migración fue cuidadosa, pero la API los pasa en cada guardado y nadie lo había notado porque hasta ahora ninguna pantalla guardaba un hito.

**Decisión 1: dejar cada fila consistente consigo misma**, de modo que recalcularla dé lo que ya está guardado (migración `f5a92c3d81e6`).

- Se reponen las **seis fechas de valorización que sí venían en la planilla** —`VVP-1`, `VVP-2`, `VVP-3 ESCRITURA`, `VVP-16`, `VVP-18`, `VVP-19`—, que se habían perdido en el camino.
- `VVP-15` y `VVP-17`, los dos abiertos, no traían fecha: la planilla los valorizaba con **la UF del día en que se exportaba**. Quedan fijos al 20-08-2026, que preserva el monto pero lo congela.
- `VVP-3 PROMESA` y `VVP-16` traen un valor en pesos que **ninguna UF de la serie produce** —la primera difiere en 1,23 de la más cercana; la segunda equivale a 40.976,47 cuando la propia planilla anotaba 40.779,55—. Van con `valor_clp_manual`, que es el campo para un valor que se afirma en vez de derivarse, y la ficha lo muestra con su aviso.
- `comision_total` se reescribe con el producto exacto: el Excel la guardaba al peso y las demás columnas con todos sus decimales, así que las 19 filas diferían en menos de un peso. Sin esto, cualquier guardado futuro movería centavos y una auditoría no sabría distinguirlo de un problema real.

**`VVP-2` queda intacto salvo su fecha, y a propósito.** Esa fila usó **dos bases a la vez**: el total sobre 81.505.175 y el broker y la VP bruta sobre los 104.100.248,32 de la UF. Ninguna base única la reproduce —`test_comisiones.py` ya la tiene como `xfail` estricto—. Ponerle `valor_clp_manual` le bajaría la comisión real a 1.085.640; dejarla derivar de la UF le subiría el total a 4.164.010. Las dos son inventar plata. Se le fija la fecha, que estabiliza su UF sin mover un peso, y el resto espera la decisión de negocio.

**Decisión 2: la migración arregla los datos que hay, no la clase de problema.** Cualquier carga futura puede traer otra fila así. Así que la API **frena** cuando guardar una liquidación **ya cerrada** movería alguno de sus siete montos, y responde 409 con las dos cifras en vez de guardar. La pantalla las muestra y ofrece "Guardar de todas formas": no es un bloqueo, es un aviso que hay que ver y aceptar.

- **Solo las que ya estaban cerradas.** Cerrar un negocio calcula la comisión por primera vez: ahí el cambio es el objetivo. Y mover la plata de un negocio abierto es trabajo normal de pipeline. Lo que no puede pasar en silencio es que cambie un monto ya facturado.
- **Se vigilan los siete montos, no solo `comision_real_vp`.** La primera versión miraba solo ése y en la prueba en vivo **dejó pasar a `VVP-2`**, cuyo desvío está en `comision_total` y deja la comisión real intacta. Una guarda de una sola columna se perdía justamente el descuadre más grande.

**Decisión 3: el resguardo va en un test, no en la migración.** `test_valorizacion_historica.py` comprueba las dos direcciones: que los montos del JSON son los del Excel —contra `HISTORICOS`, el fixture de la planilla— y que pasando las *entradas* del JSON por `refrescar_hito` salen esos mismos montos. Usa **la UF de verdad** de las 22 fechas involucradas y no la que cada fila afirma, porque derivarla del propio `uf_snapshot` habría vuelto el test circular. Se verificó que falla: quitándole la fecha a `VVP-17` dice `40040.43 == 40859.28` y nombra el negocio.

**Un error propio que vale registrar.** La primera versión de `downgrade` ponía `fecha_valorizacion` en nulo en todas las filas, y **borró en `dev` las seis fechas que venían de la planilla** por confundirlas con las que la migración escribe. Se recuperaron del export versionado. La lección queda escrita en el archivo: una migración de datos que "revierte" a un valor supuesto destruye el dato real que había. Ahora `downgrade` no hace nada y explica por qué.

**Queda abierto, y es de negocio:** con qué UF se valoriza un negocio **abierto**. La planilla los revalorizaba a la fecha de exportación, o sea que el pipeline se movía solo cada vez que alguien abría el archivo. Congelarlos a una fecha preserva el número pero lo deja envejecer. No se decide por cuenta propia.

---

## D-047 · El estado de una consulta se dibuja en un solo lugar, y el render se corta antes de tocar los datos

**Contexto.** La auditoría encontró **trece pantallas que pedían datos a la API y ninguna contemplaba que la petición falle**. Salían de dos formas, las dos malas:

- `{isLoading || !data ? <Loader/> : ...}` — **el spinner queda girando para siempre**. Al fallar, `isLoading` pasa a falso y `data` sigue sin existir, así que la condición nunca se resuelve.
- `if (!data) return null` — **la pantalla queda en blanco**, sin explicación ni acción posible.

En los dos casos una sesión vencida, Neon despertando o un 500 se veían exactamente igual que "todavía cargando". Lo único que quedaba era recargar a ciegas.

**Decisión.** Un componente compartido, `EstadoConsulta`, dibuja los tres estados —cargando, error y vacío— y las pantallas cortan el render antes de tocar los datos:

```tsx
const consulta = useQuery({ ... })
const { data } = consulta
if (!data) return <EstadoConsulta de={consulta} alto={300} />
// desde acá `data` existe
```

**Por qué cortar el render y no envolver el contenido.** El corte le da a TypeScript el estrechamiento: después de esa línea `data` deja de ser opcional y desaparecen los `data?.` y los `?? []` que ensuciaban el resto del componente. Un envoltorio no puede hacer eso, y habría dejado a cada pantalla igual de expuesta a olvidar el caso.

**El componente pide una forma mínima, no el tipo de TanStack Query.** `{ isLoading, isError, error, refetch }` y nada más. Así sirve igual con una consulta o con una lista de cinco —muestra el primer error y reintenta todas— sin pelear con los genéricos en cada pantalla.

**El error trae qué hacer, no solo qué pasó.** Se muestra el mensaje de la API, un botón *Reintentar* que vuelve a lanzar la consulta, y una línea que distingue los dos casos frecuentes: si dice que la sesión venció hay que entrar de nuevo, y si no, suele ser la base despertando y reintentar alcanza.

**Tres pantallas quedan como estaban, a propósito.** `AvisoUF` es un banner: si su consulta falla lo correcto es que no aparezca, no que grite. `App.tsx` consulta `/me` y un fallo ahí *significa* que no hay sesión, así que muestra el login —que es la respuesta correcta, no un error—. Y `AppShellLayout` no consulta nada.

---

## D-048 · Los números que la interfaz explica los manda la API, no los escribe la pantalla

**Contexto.** La auditoría encontró umbrales y cifras escritos a mano en los textos de la interfaz, mientras el backend los decidía —y en dos casos **ya los devolvía en la respuesta y la pantalla los ignoraba**:

- Las dos bandejas explicaban su semáforo con números fijos: *"Más de 30 días sin gestión"*, *"Entre 24 y 48 horas"*. El backend los tiene en `UMBRAL_CRITICO` y `UMBRAL_ADVERTENCIA` —de la hoja `CONFIG`— y los mandaba como `umbral_critico_dias` / `umbral_critico_horas`.
- El reporte mensual, al explicar un mes sin cierres, afirmaba *"sobre los datos reales, 4 de 11 meses estuvieron vacíos"*.

**Decisión.** El texto se arma con lo que manda la API. Donde el dato no venía —los meses vacíos— se agregó al reporte (`meses_sin_cierres`, `meses_de_la_ventana`) en vez de dejarlo escrito.

**Motivo.** Dos copias del mismo umbral no fallan: divergen. El día que se ajuste el semáforo a 45 días, la pantalla va a seguir explicando 30 y nada va a avisar. **Un cartel que miente sobre la regla que aplica es peor que no tener cartel**, porque se le cree.

El caso del reporte mensual es aún más claro: *"4 de 11 meses"* era cierto el día que se escribió y deja de serlo al mes siguiente, sin que nada falle. Ahora dice cuántos meses de **la ventana que el usuario está mirando** estuvieron vacíos, así que cambia con el selector: 2 de 3, 2 de 6, 6 de 12 sobre los datos de hoy. Un dato que envejece mal es peor que ninguno, porque nadie se entera de que dejó de valer.

**Se recorre la ventana mes por mes para contarlo.** Son tres, seis o doce consultas cortas. La alternativa —un `GROUP BY` por mes— habría duplicado la lógica de `_metricas`, que es justamente el tipo de duplicación que esta decisión evita.

**Lo que se dejó como está, y por qué no es lo mismo.** Los `14 días` / `30 días` del selector del reporte semanal **son** los valores del control: el número no explica una regla, la elige. Y el tope de 25 filas de las listas del semanal ya se declara en pantalla —*"Se muestran 25 de 41"*— así que no hay recorte silencioso.

---

## D-049 · El importador de canjes hace una consulta y un commit, no dos por fila

**Contexto.** `importar_canjes` iba a la base dos veces por cada fila del archivo: un `db.get` para ver si el canje existía y un `db.commit` para guardarlo. Con las 297 filas del export real de Dataprop son **~594 idas y vueltas**, y para nada: el archivo se conoce entero de antemano.

**Medido contra `dev` en Neon, con 100 filas: 84,50 s contra 1,07 s.** Setenta y nueve veces. La latencia desde la máquina de desarrollo es de ~190 ms por viaje, así que el export completo tardaba minutos; dentro de Render, a ~10 ms, eran unos seis segundos contra menos de uno. En los dos casos el costo era latencia, no trabajo.

**Decisión.** Tres pasos: parsear todo, **una** consulta con todos los IDs, **un** commit.

**Parsear primero no es solo orden.** Los errores de formato —un `ESTADO` que no está en el mapa, una fecha ilegible— salen sin gastar una sola consulta. Son además los que de verdad ocurren: el test de la fila inválida que ya existía falla en el parseo y nunca llegaba a la base.

**El commit por fila protegía algo, y se conserva como camino de excepción.** Si el lote falla, se rehace fila por fila para que el error quede atribuido a su fila y las buenas se guarden igual. Deja de ser el camino normal, que es lo que costaba los 594 viajes, y pasa a ser el que se toma cuando algo salió mal de verdad.

**Un ID repetido dentro del mismo archivo actualiza, no duplica.** El mapa de existentes se va poblando con lo que se crea. Sin eso, la segunda aparición intentaría insertar de nuevo, el commit del lote fallaría, y **las 297 filas se irían al camino lento por una sola fila repetida**. Hay un test para ese caso.

**El test cuenta las llamadas, no solo el resultado.** Un test que verificara únicamente que las 30 filas quedaron cargadas habría pasado igual con la versión lenta. Se exige `commit == 1` y `get == 0`: si alguien vuelve a meter un commit en el bucle, falla.

---

## D-050 · La estructura del archivo se muestra en pantalla, y sale de la misma definición que pinta la plantilla

**Contexto.** Las dos cargas masivas pedían un `.xlsx` sin decir en ninguna parte qué columnas esperaban. La de negocios tenía plantilla para bajar, así que la respuesta estaba dentro de un archivo que había que descargar y abrir en Excel; la de canjes no tenía ni eso. En los dos casos la única forma de saber si el archivo servía era subirlo y leer los errores.

**Decisión.** Cada modal muestra la estructura: las columnas agrupadas, cuáles son obligatorias, qué va en cada una, los valores que se aceptan y las trampas. Se sirve por API desde la misma definición que genera el Excel.

**Sale de la definición que pinta la plantilla, no de un texto aparte.** `plantilla_negocios.COLUMNAS` ya tenía grupo, obligatoriedad y ayuda para las 32 columnas —solo se usaba para pintar el encabezado del Excel—, así que se expone tal cual. Es la misma razón que `D-048`: dos copias de lo mismo no fallan, divergen, y una pantalla que describe una columna que la carga ya no pide es peor que no describir nada, porque se le cree. En canjes la lista de nombres vive en `importar_canjes.COLUMNAS_REQUERIDAS` —que es lo que la carga verifica de verdad— y las descripciones se le agregan al lado, con un test que exige que las dos digan lo mismo **y en el mismo orden**.

**Va cerrado por defecto.** Con 32 columnas, mostrarlas al abrir el modal empuja el botón de cargar fuera de la vista, y quien ya sabe llenar el archivo —que va a ser el caso habitual— tendría que bajar cada vez.

**Canjes ahora también tiene plantilla, y su encabezado va en una sola fila.** Acá hubo un error propio que vale registrar: se copió el estilo de la plantilla de negocios, que trae el grupo en la fila 1 y las columnas en la 2 porque `importar_negocios` lee la fila 2. Pero `importar_canjes` lee **la fila 1**, así que la plantilla recién creada era rechazada por su propio cargador con "Faltan columnas: las 16". Lo atrapó un test que sube la plantilla a la carga y exige que la acepte —una plantilla que su propio cargador rechaza es peor que no tenerla—. Quedó en una sola fila, que además es más fiel: el archivo real es el resultado de una query, y una query no devuelve encabezados agrupados. Los grupos existen solo para la pantalla.

**Y esa plantilla no es para llenarla a mano.** El archivo de canjes sale de la query contra Dataprop. Se baja para **comparar encabezados** cuando la carga falla y no se entiende por qué. Está dicho así en la pantalla, para que nadie se ponga a tipear canjes en ella.

**El orden de las rutas importa.** `/canjes/plantilla` va registrada antes de `/canjes/{canje_id}`, o FastAPI intenta parsear "plantilla" como un entero. Es el mismo error que ya se había cometido con `/canjes/bandeja`, y hay un test que lo fija.

---

## D-051 · El desglose por etapa viene con la respuesta, y el filtro es de pantalla

**Contexto.** El bloque «Canjes por etapa» mostraba un solo número por etapa: el total, sin distinguir activos de cancelados. Con **293 cancelados de 297**, ese número era básicamente el conteo de cancelados y no decía nada sobre lo que hay vivo — que es lo que uno viene a mirar.

**Decisión.** Cada etapa trae los tres números en la misma respuesta —total, activos, cancelados— y el selector filtra en la pantalla, sin volver a consultar.

**Por qué no un parámetro en la URL.** Son seis etapas por dos estados: doce números que caben en la misma respuesta que ya se pide. Un `?estado=` habría significado una ida al servidor por cada clic en el selector, con su carga y su parpadeo, para traer datos que ya estaban ahí. Se resuelve con **una sola consulta agrupada por las dos columnas**, no con dos consultas más.

**Arranca en «Todos».** Es lo que la pantalla mostraba antes de que existiera el selector: agregar un filtro no debería cambiar lo que uno ya veía. Queda dicho en el código que «Activos» es la vista más informativa de las tres, pero elegirla como defecto es una decisión de quien usa la app, no del código.

**El total de la vista va al lado del selector.** Con «Activos» se ve una fila de números chicos —1, 2, 1— y sin el total no queda claro si son cuatro canjes o cuarenta.

**Los activos con la etapa en Cerrado se declaran en vez de esconderse.** El recuadro «Activos» de arriba exige `estado = ACTIVO` **y** `etapa != Cerrado`: un canje cerrado no está activo, aunque nadie le haya cambiado el estado. El desglose por etapa, en cambio, cuenta por estado sin más. Un canje en ese cruce aparecería como activo en la fila «Cerrado» y no en el recuadro, y la suma daría uno más sin explicación. Así que la respuesta trae `activos_con_etapa_cerrada` y la pantalla lo dice —**solo cuando no es cero**, para no poner un cartel sobre un caso que hoy no existe—. Hay un test que construye ese cruce y exige que la diferencia sea exactamente ese número.

**Y de paso: el resumen de canjes pasó a ser testeable.** `por_mes` se calculaba con `to_char(fecha_solicitud, 'YYYY-MM')` en SQL crudo, que es una función de Postgres, así que **todo este resumen no se podía probar** —los tests corren sobre SQLite— y por eso el dashboard de canjes no tenía ni un test. Ahora el agrupado por mes se hace en Python. El costo es traer una fecha por canje en vez de un agregado: son 297 filas, y a diez mil sigue siendo una consulta y un bucle. Se verificó que el resultado es idéntico en los 37 meses de `dev` antes y después.

---

## D-052 · La fecha de un movimiento se puede atrasar, y la etapa vigente se deriva de la línea de tiempo

**Contexto.** La pantalla de seguimiento no ofrecía fecha, así que todo movimiento quedaba con el instante en que se apretaba el botón. En la práctica uno anota el lunes lo que pasó el viernes, y esos tres días de diferencia van directo al reloj del semáforo y al reporte semanal.

La API **ya aceptaba `fecha`** en canjes y en negocios desde el sprint del pipeline; el hueco era solo de pantalla. Lo que faltaba no era el campo: era todo lo que había que cerrar antes de exponerlo.

**Decisión 1: el campo va vacío, y vacío significa «ahora».** No se precarga con la hora actual. Así el camino habitual —registrar lo que acaba de pasar— manda un cuerpo sin `fecha` y el servidor pone la de la petición, exactamente como antes. Backdatear es opt-in, y no hay forma de que un formulario abierto diez minutos guarde una hora vieja por descuido.

**Decisión 2: se puede atrasar, no adelantar.** Una fecha futura envenena el reloj de la bandeja: `horas_sin_gestion` es `ahora - ultimo_movimiento`, así que daría **horas negativas** en pantalla, y con ellas el semáforo y el reporte semanal. Se rechaza con 400. Y una fecha anterior a que la cosa existiera —la solicitud del canje, o el hito más antiguo del negocio— no es un dato sino un tipeo; el mensaje trae las dos fechas para que se vea cuál era el mínimo.

**Hay cinco minutos de holgura**, porque la fecha la arma el navegador y su reloj puede ir unos minutos adelante. Sin eso, registrar «ahora» desde una máquina adelantada se rechazaría por venir del futuro, que es un error incomprensible para quien lo ve.

**Decisión 3, y es la que el campo obligó a tomar: la etapa vigente se deriva de la línea de tiempo.** Antes, `crear_movimiento_*` hacía `entidad.etapa = tipo.etapa_resultante` con el movimiento recién insertado. Con fechas siempre crecientes eso era correcto; **desde que se pueden atrasar, no.** Está medido: en un canje que el día 20 había pasado a «En negocio», anotar una gestión con fecha del día 10 lo devolvía a «En revisión» —la etapa retrocedía sola, contra un movimiento posterior que seguía ahí—.

Ahora se lee: la etapa es la del movimiento **más reciente** que traiga una. Es un cambio de acumular a derivar, y es lo correcto de todas formas: la etapa vigente es una consecuencia de la línea de tiempo, no un contador.

**El estado no se deriva, y eso sí es a propósito.** Un canje que se canceló quedó cancelado; que después alguien anote otra gestión no lo revive. Deshacer una cancelación es una edición manual, no un movimiento. Hay un test que lo fija para que nadie «complete» la simetría por prolijidad.

**La validación se puso en el servicio compartido**, así que cubre canjes y negocios. La pantalla de negocios todavía no ofrece el campo —no se pidió—, pero su endpoint ya aceptaba `fecha`: cerrar el agujero en un dominio y dejarlo abierto en el otro habría sido arreglar la mitad.

---

## D-053 · Un movimiento se borra de verdad, y lo que dependía de él se recalcula

**Contexto.** Se podían agregar movimientos y no sacarlos. Un tipeo —un tipo equivocado, una gestión anotada en el canje de al lado— quedaba para siempre moviendo la etapa y el reloj del semáforo, y corregirlo exigía tocar la base a mano. El pedido fue concreto: borrar la única gestión registrada en el canje #367.

**Decisión: borrado real, no anulado.** Un movimiento marcado como "anulado" hay que filtrarlo en la línea de tiempo, en el semáforo, en el reporte semanal y en el cálculo de la etapa: cuatro lugares donde olvidarlo produce un número mal. Y lo que queda no es historia útil sino ruido —"acá hubo algo que no pasó"—. Para dos personas corrigiendo sus propios registros, borrar es lo proporcionado.

**Lo puede hacer quien los registra** (rol `operaciones`, decidido con el usuario). Corregir un tipeo propio no debería necesitar a otra persona.

**Lo que arrastra se recalcula, no se adivina.**

- **La etapa** se vuelve a derivar de los movimientos que quedan, con el mecanismo de `D-052`. Si no queda ninguno vuelve a `SIN_ETAPA`: la puso el movimiento que se borró y no hay nada más que la sostenga. Es el caso de #367.
- **Si el borrado era la cancelación** y no queda otra, el canje vuelve a `ACTIVO`. Registrarla fue el error, así que el canje no estaba cancelado. Un canje que llegó cancelado del export —sin movimiento de cancelación— se queda cancelado: borrar gestión cualquiera no lo revive.

**`gestionado_en_app` no se toca, y hay que decirlo en pantalla.** Es tentador devolverlo a `False` cuando no quedan movimientos, pero no lo pone solo el seguimiento: también lo pone crear o editar el canje a mano. Revertirlo dejaría que la próxima importación de Dataprop sobreescriba en silencio datos corregidos por una persona.

El costo de esa decisión es que un movimiento registrado por error deja el canje excluido de la importación **para siempre**. Lo comprobé encima: verificando esto contra `dev` le puse la marca al canje 355 sin querer, y tuve que restaurarla comparándolo con los otros seis cancelados sin movimientos, que estaban en `False`. Si a mí se me pasó teniendo el modelo entero en la cabeza, a cualquiera se le pasa. Así que **el modal lo dice** cuando un canje sin movimientos está marcado: la consecuencia es la misma, pero deja de ser invisible.

**La confirmación va en la fila del movimiento, no en un diálogo.** Un diálogo encima de un modal ya abierto tapa justamente lo que hay que mirar para decidir. Un segundo clic en el mismo lugar —"¿Borrar este movimiento?" con Sí y Cancelar— deja a la vista de cuál se trata.

---

## D-054 · El reporte mensual se separa por dominio y muestra la evolución de la ventana

**Contexto.** El reporte mezclaba negocios y canjes en la misma tabla, y decía cuánto cambió la ventana contra la anterior —un número— pero no en qué dirección venía. Con eso no se puede responder lo que se le pide: si hay avance, estancamiento o retroceso.

**Decisión 1: un selector Negocios / Canjes**, el mismo patrón que Inicio. Cada dominio ocupa la pantalla con sus recuadros, sus gráficos y su tabla. El backend etiqueta cada variación con su `dominio` en vez de dejar que la pantalla filtre por el nombre visible: renombrar una métrica no puede cambiar en silencio de qué reporte forma parte.

**Decisión 2: la serie mes por mes de la ventana**, con el promedio como referencia. Es lo que convierte el gráfico en respuesta: una barra más baja que la anterior no dice si el mes es malo; una barra bajo el promedio de su propia ventana, sí. Va acompañada de una frase —*"el mes va 26% sobre el promedio de la ventana"*— porque eso es lo que se lee en un segundo. El umbral de "en línea" es 10%: con estos volúmenes, menos que eso no es tendencia.

**El promedio incluye los meses en cero.** De 11 meses con actividad, 4 estuvieron vacíos: son parte de la normalidad de este negocio, y excluirlos inflaría la referencia justo en el sentido que hace ver retroceso donde no hay.

**Cuatro consultas para toda la serie, no cinco por mes.** Llamar a `_metricas` doce veces habría costado sesenta viajes. Se traen las filas del rango completo y se agrupan en Python, la misma decisión de `D-051` por el mismo motivo: contra Neon lo que cuesta es la latencia. De paso reemplazó el bucle que contaba los meses vacíos, que recorría la ventana una segunda vez.

**Decisión 3: la plata y las cantidades en gráficos separados.** Nunca dos ejes en el mismo: un eje doble deja que la escala de cada serie se elija sola, y con eso cualquier par de curvas se puede hacer coincidir o divergir a gusto.

### Lo que se descubrió al construirlo, y que cambió el alcance

**Canjes no tiene eje de plata, y no por olvido.** Sí genera comisión —la de administración de Dataprop: 6/5/4% en venta según el tramo en UF, u 8% en arriendo, siempre **sobre la comisión de los corredores participantes**—. Pero:

- `comision_dbrokers` y `valor_negocio` están en **0 de 297 filas**. El campo existe en el formulario y nadie lo llenó nunca; ningún reporte lo usa. Sin la comisión de los corredores no hay base sobre la que aplicar la escala.
- `valor_prop`, que era la alternativa, **no se puede sumar**. La moneda está equivocada en las dos direcciones: 26 ventas y 50 arriendos marcados en UF con valores de más de 100.000 —que serían miles de millones de pesos, o sea que son pesos— y 62 ventas marcadas en CLP con valores de 1.000 a 100.000 —que como precio de venta en pesos es absurdo, o sea que son UF—. Son **~138 de 297 filas**. Y encima el campo mezcla precio de venta con arriendo mensual, que no suman entre sí.

Se había acordado mostrar el volumen en pesos "por ahora"; se retiró al medirlo, porque daba 185 mil millones para diez canjes. **Un número errado por órdenes de magnitud con una nota al pie sigue siendo un número errado en pantalla** (`D-048`).

**«Canjes cerrados» es cero en todos los meses, y es correcto.** Los 31 canjes con etapa `CERRADO` están **todos cancelados** y ninguno tiene `fecha_cierre`; los 47 que sí tienen fecha están cancelados en etapas intermedias. En esta base no hay un solo canje cerrado con éxito. La métrica queda en la tabla y fuera del gráfico —una serie plana en cero no informa y gastaba un color—, con la explicación escrita en la pantalla.

Queda anotado que su definición es frágil: exige `etapa = CERRADO` **y** `fecha_cierre` en el rango, y el patrón de los 31 sugiere que el primer cierre real también podría llegar sin fecha. No se cambió sobre una suposición.

### Lo que corrigió mirar el gráfico renderizado

Compila, pasa el lint y aun así estaba mal de cuatro formas. Se levantó la página en un render aislado con los datos reales de `dev` y se sacaron capturas en los dos modos:

1. **Ninguna barra se dibujaba.** La animación de entrada las deja en altura 0 y en un render sin ventana visible nunca avanza. Quedó desactivada, que además evita que cada cambio de ventana o de dominio sea un rebote.
2. **El énfasis del mes actual no servía.** Se dibujaba el mes actual opaco y los anteriores translúcidos; como el mes que se mira es justamente el que suele estar en cero —por eso se lo mira—, el resultado era un gráfico lavado con el foco en una barra ausente. Ahora todas van al mismo tono y lo que ubica el mes actual es su posición, su valor en el encabezado y la línea del promedio.
3. **La etiqueta directa sobre la última barra no aparecía**: las props que entrega `LabelList` no eran las que se asumieron. El valor se movió al encabezado, al lado de su referencia; se lee mejor y no depende de los internals de Recharts.
4. **La leyenda salía en orden inverso a las barras** —"Cancelados · Solicitados"— porque Recharts la ordena por `dataKey`, y en la versión 3 ya no acepta un `payload` propio. Se dibuja a mano.

**La paleta se validó con el script, no a ojo.** El modo oscuro no es un aclarado automático del claro: `brand.6` (#3D3EA8) contra fondo oscuro da contraste 2,03, bajo el mínimo de 3:1, así que oscuro usa `brand.4`. Y con tres series el verde y el rojo caían a ΔE 7,9 en deuteranopía; se resolvió dejando dos series por gráfico —que además saca del medio la serie que hoy es cero—. La rejilla y los ejes también van por modo: la escala de grises de Mantine no se invierte, así que un gris recesivo sobre blanco queda prominente sobre negro.

---

## D-055 · Tendencia de la ventana, y los canjes activos como segmento en vez de barra aparte

**Contexto.** El reporte ya mostraba la serie de la ventana con su promedio, pero faltaban dos cosas: hacia **dónde va** la ventana, y los canjes **activos**, que en un gráfico de solicitudes contra cancelaciones quedaban invisibles —cuatro activos junto a noventa cancelados—.

**Decisión 1: una recta de tendencia por mínimos cuadrados, calculada en el backend.**

El promedio y la tendencia responden preguntas distintas y las dos hacen falta: el promedio dice si el mes está por encima o por debajo de lo normal, la tendencia dice hacia dónde va la ventana. **Una ventana puede estar toda sobre su promedio y venir cayendo.**

Se calcula en el backend y no en la pantalla porque es donde este proyecto tiene los tests. Viaja con sus dos extremos ya ajustados, así que la pantalla dibuja la recta con dos puntos y no repite el ajuste.

**La recta se recorta en cero.** Una proyección negativa de un conteo o de una comisión no existe, y dibujarla bajo el eje sugeriría que sí.

**Debajo de 3% mensual se declara plana**, y una tendencia plana no se dibuja: una recta horizontal ya la cuenta el promedio, y dos líneas paralelas solo agregan tinta.

**El porcentaje de la pendiente viaja en la respuesta pero no se muestra.** Con tres meses, una serie que cae a cero da *"−150% por mes"*: correcto, y se lee como un error. Lo que se muestra es la dirección más la recta dibujada, que es la misma información sin el número absurdo.

**Decisión 2: los canjes activos van apilados sobre los cancelados**, no al lado.

`canjes_solicitados = canjes_activos + canjes_cancelados` **exacto**, porque el estado solo tiene esos dos valores. Esa identidad —que tiene su propio test, para que agregar un tercer estado falle en vez de hacer mentir al gráfico sobre su total— es la que habilita el apilado: el alto de la barra **es** la solicitud del mes y el activo es su propio segmento, anclado al eje para que se pueda comparar entre meses.

Lado a lado no servía: cuatro activos junto a noventa cancelados son una raya junto a una torre, que es exactamente el problema de dilución que había que resolver.

**Y además un gráfico propio de activos, en su propia escala.** Apilados se ve su peso relativo; solos se ve su forma. Los dos juntos responden "cuántos son" y "cómo vienen", que no es lo mismo.

**Activos en índigo y cancelados en rojo, no verde y rojo.** En un apilado los segmentos se tocan, y el validador da verde↔rojo en ΔE 7,9 en deuteranopía en modo oscuro: bajo el piso. Índigo↔rojo pasa en los dos modos. Es una diferencia con los recuadros de Inicio, donde activo es verde, y se acepta porque acá los segmentos están pegados y la leyenda los nombra.

### El error que encontró mirarlo renderizado

**El promedio truncaba los conteos.** `_promedio` casteaba con `int()`, así que cuatro liquidaciones en seis meses daban un promedio de **cero**: el reporte afirmaba que en promedio no se cierra nada habiendo cuatro cierres, y la línea de referencia de los canjes activos desaparecía por quedar bajo cero. Se vio porque el gráfico de activos salió sin su línea.

El promedio pasó a su propio modelo, `PromedioMes`, con todos los campos decimales. No reusa `MetricasMes` porque ahí los conteos son enteros y **el promedio de un conteo no lo es**. Hay un test que lo fija: 0,67 y no 0.

De paso, los conteos fraccionarios van con coma decimal: `15,67` y no `15.67`, que se lee como otro número.

---

## D-056 · La vista directorio se separa por dominio, y la ventana solo alcanza lo temporal

**Contexto.** El directorio era una foto sin ventana elegible —doce meses fijos— y de canjes mostraba dos conteos sueltos en un recuadro al pie. El pedido fue darle el mismo tratamiento que al reporte mensual: separación por dominio, y métricas, vistas y filtros equivalentes.

**Decisión 1: el mismo selector Negocios / Canjes y la misma ventana móvil**, reusando los componentes del reporte mensual —`EvolucionMensual`, `Veredicto`— y sus funciones de backend —`_serie_mensual`, `_promedio`, `_tendencia`—. No se recalcula nada acá: dos versiones del mismo cálculo divergen, y hay un test que exige que la serie, el promedio y la tendencia del directorio sean **idénticos** a los del reporte mensual para la misma ventana.

**Decisión 2, y es la que define la vista: la ventana solo manda sobre lo temporal.**

Alcanza la ventana móvil, la serie, la tendencia y los conteos de canjes del período. **No** alcanza los buckets —ganado, en proceso, no concretado—, la tasa de cierre, el ticket ni la proyección.

El motivo no es comodidad. Un negocio abierto **está abierto**: no pertenece a un mes, y filtrarlo por ventana obligaría a inventar un criterio —¿los abiertos que se iniciaron en la ventana?— que responde otra pregunta. Y la tasa de cierre con tres meses se calcularía sobre uno o dos casos resueltos: su intervalo de confianza pasaría de los 47 puntos actuales a casi cien, y la proyección heredaría ese rango. Un número con ese margen no informa una decisión de plata; es peor que no darlo.

El default es doce meses, que era el valor fijo anterior: da la lectura anualizada sin depender de en qué mes del año estemos.

**Decisión 3: la mitad de canjes es de volumen, origen y supervivencia.** Sin ticket ni proyección, porque sin plata no hay ticket mediano ni pipeline ponderado (`D-054`). Lleva los conteos del período —solicitados, activos, cancelados, que suman entre sí—, la tasa de cierre sobre los resueltos históricos, la serie apilada con su tendencia, y de dónde viene el volumen por operación, tipo de inmueble y comuna.

**Los desgloses se recortan a ocho categorías y se declara que están recortados.** Nueve comunas ya ocupan media pantalla y la cola larga no dice dónde está el volumen. Se ordenan de mayor a menor y **se saltan los nulos** en vez de agruparlos en "Sin dato": en un desglose de origen, una categoría "Sin dato" grande empuja hacia abajo a las reales y no explica de dónde vino nada.

**Los activos se cuentan por estado, plano, y eso cambió respecto de la versión anterior.** Antes `canjes_vigentes` era "activo **y** con etapa distinta de cerrada", el mismo criterio de la bandeja. Ahora la partición es por estado sin condiciones extra, porque los conteos del período tienen que cumplir `solicitados = activos + cancelados` para poder dibujarse apilados (`D-055`). Lo que antes se llamaba vigentes sigue siendo derivable —`activos_historicos − cerrados_historicos`— y **los dos números van en la respuesta justamente para que reconcilien a la vista**, en vez de dejar al lector eligiendo cuál creer.

**Dos textos que quedaron falsos y se corrigieron.** El subtítulo decía "los montos son comisión real ViveProp" en una pantalla que ahora también muestra una mitad sin montos; pasó a depender del dominio. Y el aviso al pie decía que se preguntó qué quiere ver el directorio y no hubo respuesta: ya la hubo, dos veces. Ahora dice qué falta para cerrar la vista —los plazos de negocios y la comisión de canjes—, que es lo que de verdad queda pendiente.

---

## D-057 · La ventana histórica, y el promedio que no se diluye con meses sin dominio

**Contexto.** Las ventanas eran 3, 6 y 12 meses. Faltaba una que mostrara todo desde el principio, sin tramos.

**Decisión 1: histórico es un centinela que el servicio resuelve al largo real.** `ventana = 0` significa "todo"; el servicio busca el primer registro de cualquiera de los dos dominios y calcula cuántos meses hay hasta el mes que se está mirando —hoy son **46**, canjes arrancan en noviembre de 2022— y de ahí en adelante el cálculo es idéntico al de cualquier otra ventana. La respuesta trae el largo resuelto en `ventana_meses` y un `es_historico` para que la pantalla lo rotule "Histórico" en vez de "46 meses".

Va como centinela y no como una ventana de N meses porque **el largo lo decide el dato, no quien pregunta**: el mes que viene serán 47.

**Decisión 2, y es la que hace que la ventana histórica signifique algo: el promedio y la tendencia arrancan donde arranca su dominio.**

Negocios existe desde agosto de 2025 y canjes desde noviembre de 2022. Promediar la comisión sobre los 46 meses históricos la reparte entre 33 meses en los que ViveProp no tenía ni un negocio cargado: la referencia queda en **175.823** en vez de **622.143**, tres veces y media más baja. Contra ese promedio inventado, un mes malo se lee como bueno.

Los meses previos al primer negocio no son meses malos: son meses sin negocio. Así que cada métrica promedia y ajusta su recta desde el primer registro de **su** dominio. En las ventanas de 3, 6 y 12 eso no recorta nada —el dominio ya existía en todo el tramo— así que la única que cambia es la histórica, que es donde hacía falta.

El mismo criterio se aplicó a los meses vacíos: *"39 de los últimos 46 meses estuvieron vacíos"* sería cierto y engañoso. Ahora son **6 de 13 meses con negocios**. Y el campo se renombró de `meses_de_la_ventana` a `meses_con_negocios`, porque el nombre viejo dejó de ser cierto y dejarlo así habría sido dejarlo mintiendo.

**Decisión 3: en la histórica no hay comparación contra la ventana anterior.** Antes del primer registro no existe nada, así que la tabla saldría entera en "sin base". Se reemplaza por una línea que lo dice y remite al año corrido, que sí tiene con qué comparar.

### Lo que corrigió mirar los 46 meses renderizados

**Las dos líneas de referencia se dibujaban de punta a punta.** La recta de tendencia de la comisión se ajusta sobre trece meses, y estaba trazada a lo largo de los cuarenta y seis: le cambiaba la pendiente a la vista —más plana que la calculada— y sugería que había negocios desde 2022. La línea del promedio hacía lo mismo con su nivel.

Las dos quedaron acotadas al tramo que describen, usando el `puntos` que la tendencia ya traía. Se ve en el gráfico: las de negocios arrancan en agosto de 2025 y las de canjes cruzan todo.

De paso, el veredicto decía *"la ventana de 13 meses viene a la baja"* en una pantalla rotulada "46 meses". Ahora dice *"la tendencia sobre 13 meses"*, que es lo que es.

**Las etiquetas del eje no colisionan**: Recharts las adelgaza solo, y con 46 barras muestra una de cada dos. Se verificó en captura antes de darlo por bueno.

### Corrección: el gráfico también arranca donde arranca el dominio

La primera versión recortaba el promedio y la tendencia al primer registro de cada dominio, pero **dejaba la serie completa en el gráfico**. El resultado, visto en pantalla: el gráfico de negocios empezaba en diciembre de 2022 con **33 meses vacíos** antes de su primera barra, la forma real apretada en el último cuarto, y las líneas de referencia colgando en el aire desde agosto de 2025.

Los meses previos al primer negocio no son meses malos, son meses sin negocio, y **dibujarlos era el mismo error que promediarlos**, solo que en la otra mitad del problema. Ahora la serie del gráfico arranca donde arranca el dominio que se está mirando: negocios en 13 meses, canjes en 46. Se ve además lo que antes quedaba comprimido —enero de 2026 con ocho negocios iniciados—.

**El recorte va en la pantalla y no en la API, y solo en la histórica.** En la pantalla porque el dato ya viajaba —`inicio_por_dominio`— y devolver dos series por dominio habría duplicado la respuesta para que cada mitad use la mitad. Y solo en la histórica porque en 3, 6 y 12 meses el largo es lo que se pidió: mostrar menos barras que las elegidas contestaría otra pregunta, y ahí lo que se acota son las líneas, que ya saben su tramo.

---

## D-058 · En el apilado, el total va explícito: leer un alto no es leer un número

**Contexto.** El gráfico apilado de canjes pone el total del mes como **alto de la barra** —`solicitados = activos + cancelados`, exacto— y el globo listaba un renglón por segmento: *"Cancelados: 10", "Siguen activos: 4"*. La cifra completa del mes estaba ahí, en la geometría, pero para decirla había que sumar de cabeza.

Es una distinción que se me pasó al diseñar el apilado: que el total sea **deducible** no es lo mismo que esté **dicho**. El alto de una barra se compara bien contra otras barras y se lee mal como cantidad.

**Decisión: el total va primero y en negrita en el globo, y como etiqueta sobre la barra cuando caben.**

En el globo el orden es el de la pregunta —cuántos entraron, y en qué terminaron—, así que el total es el titular y los segmentos van debajo. **Los segmentos se ordenan de mayor a menor y no en el orden de la pila**: con noventa cancelados y cuatro activos, seguir el orden del apilado pone primero al que no aporta.

**La etiqueta sobre la barra solo aparece con doce meses o menos.** Con cuarenta y seis las etiquetas se pisan entre sí y tapan justamente lo que vienen a explicar; ahí el número vive en el globo. Es la regla de `dataviz` sobre etiquetas directas selectivas, aplicada al caso concreto: doce es lo que entra sin colisión en el ancho de la tarjeta.

**El total viaja como un campo sintético en cada fila**, no como una serie: se lee para el globo y la etiqueta, y no se dibuja como barra. Una tercera barra habría sido justamente lo que el apilado vino a eliminar —una torre al lado de sus propias partes—.

**Aplica solo al apilado.** En los gráficos de una o dos series independientes no hay total que sumar: ahí la suma de las barras no significa nada, y ponerla sería inventar una métrica.


---

## D-059 · El próximo seguimiento se agenda, y manda sobre el semáforo

**Contexto.** «Qué me toca hoy» ordenaba por horas sin gestión. Eso es un **proxy**: mide cuánto hace que nadie toca un canje, no qué se prometió hacer. Un canje que se llamó ayer y quedó en retomarse el jueves se veía igual que uno abandonado.

**Decisión: cada movimiento puede agendar cuándo volver a mirar el canje, y el compromiso vigente manda sobre el semáforo.** Cuando los dos opinan, gana el que no es una inferencia.

Los niveles pasan a ser seis: `vencido` y `para_hoy` salen de un compromiso registrado y van antes que los cuatro del semáforo, que quedan para los canjes sin fecha agendada.

**Va en `movimientos` y no en `canjes`.** El compromiso lo asume una gestión —"llamé y quedamos en que sigo el jueves"— así que pertenece a ese registro. En `canjes` sería un campo que se sobreescribe sin dejar rastro de quién lo movió; en la línea de tiempo queda al lado del movimiento que lo generó, y **el vigente es el del más reciente**, igual que la etapa (`D-052`). Como se deriva y no se acumula, borrar un movimiento devuelve el compromiso anterior sin ningún paso extra.

**El default nunca deja el campo en nulo.** Sin fecha, el canje volvería a depender del reloj de horas, que es justamente el proxy que esto reemplaza. Se agendan **dos días corridos** —no dos hábiles— y el resultado se corre al lunes si cae fin de semana: un viernes más dos da domingo, y el hábil siguiente es el lunes. Contar hábiles daría martes, y "te llamo en un par de días" son días de calendario.

**Se ancla al más nuevo entre la fecha del movimiento y hoy.** Anclarlo solo al movimiento haría que anotar hoy una gestión de hace tres meses agendara un seguimiento vencido hace tres meses, y la bandeja se llenaría de vencidos que nadie prometió. Anclarlo solo a hoy perdería el caso normal. El mayor de los dos resuelve ambos.

**Una fecha escrita a mano no se corrige.** El default evita el fin de semana; si alguien escribe sábado es porque va a trabajar el sábado, y moverle la fecha que acaba de escribir sería el sistema opinando sobre su agenda.

**Los feriados no se saltan, y está declarado en pantalla.** Saltarlos necesita la lista de los de Chile —con los movibles de la ley de traslado, Pascua y los días de elección— y calcularla mal dejaría el error escondido hasta que alguien agende un seguimiento para el 18 de septiembre. Se decidió empezar por fines de semana; hasta que haya una lista verificada, el campo y el pie de la bandeja lo dicen en vez de dar a entender que los conoce. **Hay un test que fija que hoy no se saltan**, para que agregarlos sea un cambio deliberado y no algo que pase de casualidad.

**Lo agendado para más adelante no se lista.** La pantalla se llama «qué me toca hoy»: listar lo que no toca es lo que hace que se deje de mirar. Se cuentan aparte y se dice cuántos son, para que no parezca que se perdieron.

### El error que corrigió mirarlo renderizado

**El contador de «Requieren atención» no incluía los niveles nuevos.** Seguía sumando los tres del semáforo, así que el chip decía «Requieren atención (2)» sobre una tabla de seis filas. Un contador que no cuadra con su propia lista no se vuelve a creer. Y el subtítulo contaba como abiertos solo los listados, dejando afuera a los agendados —que están abiertos, solo que su día no es hoy—: decía «2 de 6» donde eran 6 de 12.

---

## D-060 · Etapa y tipo de movimiento son dos datos, no uno

**Contexto.** Registrar una gestión de canje pedía un solo dato —el tipo— y la etapa salía implícita de él: `ACUERDO_FIRMADO` movía el canje a «Proceso de acuerdo», `CLIENTE_CALIFICADO` no lo movía a ninguna parte. Eso ataba dos cosas que no son la misma: **qué se hizo** y **dónde quedó el canje**. Con una llamada de seguimiento no había forma de decir que el canje avanzó, ni de avanzarlo sin inventar un tipo de movimiento que lo hiciera.

**Decisión: dos selectores que conviven en el mismo registro**, y la etapa elegida gana sobre la del tipo.

**La etapa viene precargada con la del canje.** Lo habitual es que una gestión no lo mueva, y pedir la decisión en cada llamada sería fricción por un dato que casi siempre es el mismo. Registrar la misma etapa dos veces no es ruido: la línea de tiempo queda diciendo "el 10 de julio seguía en revisión", que es un dato.

**El cambio es aditivo.** Sin etapa indicada se cae al `etapa_resultante` del tipo, que es lo que hacía antes. Eso mantiene funcionando a la migración de cancelación masiva y a cualquier llamador que no pase el parámetro, y deja el pipeline de negocios —que sí usa `etapa_resultante`— intacto.

**Los 13 tipos que salen del selector no se borran: pasan a `activo = false`.** 605 movimientos los referencian y son la línea de tiempo de los 297 canjes. Inactivo quiere decir "no se ofrece más", no "no existió", y la ficha de un canje sigue mostrando «Validación solicitante» como siempre. `CANCELACION` se queda activa aunque no esté en la lista nueva: es la única forma de dejar registrado **cuándo y por qué** se canceló un canje —editar el estado a mano lo cambia sin dejar rastro—.

**`SIN_ETAPA` pasa a llamarse `RECEPCION`.** No es cosmético: el valor significaba "Dataprop no mandó etapa", y la etapa de un canje que entró y no avanzó es «Recepción». Se hizo con `ALTER TYPE ... RENAME VALUE`, que es atómico y no toca ninguna fila; la migración verifica antes que ningún `etapa_resultante` guarde ese texto, para no dejar strings colgando.

**`CERRADO` no se renombró a `CIERRE`**, y también es deliberado: ahí el cambio sería puramente de rótulo —es la misma etapa— y ese valor sí está guardado como texto en `movimientos.etapa_resultante`. Renombrarlo obligaría a actualizar esas filas para ganar nada. Se muestra «Cierre» y se guarda `CERRADO`.

### El defecto que apareció probándolo, y que yo mismo provoqué

**Borrar un movimiento reseteaba la etapa a `RECEPCION`.** `D-053` lo justificaba así: "la etapa la puso el movimiento que se acaba de borrar y no hay nada más que la sostenga". Eso es cierto para un canje creado en la app y **falso para los 297 que vinieron de Dataprop**: su etapa la trajo el export, y ninguno de sus movimientos migrados declara una.

Lo medí encima: verificando esto borré un movimiento del canje 360 y lo mandé de «En oferta» a «Recepción», perdiendo un dato que el borrado no había puesto. Tuve que restaurarlo comparando contra la salida de una verificación anterior de esta misma sesión.

Ahora la etapa **solo se mueve si queda algún movimiento que declare una**. Si ninguno lo hace, no se toca: quedarse con una etapa vieja es preferible a borrar una que era correcta.

### El alcance se revisó después y se mantuvo

El pedido, en rigor, era más chico: **adaptar la lista de tipos de movimiento**, sin tocar etapas. Se hicieron dos cosas de más —el selector de Etapa en la bitácora y el renombre de `SIN_ETAPA`— y al revisarlo se decidió dejarlas.

Queda anotado el detalle que motivó la revisión, porque cambia cómo se lee la pantalla: **la etapa se puede cambiar desde dos lugares**, la ficha del canje y la bitácora. Eso ya era así antes, solo que en la bitácora pasaba implícito: cinco de los diecisiete tipos movían la etapa al registrarse sin decirlo. Hacerlo explícito no agrega una vía, hace visible la que había —y de paso deja en la línea de tiempo **cuándo** cambió y **con qué gestión**, que la ficha no registra—.

**Y un efecto que hay que tener presente: «Gestión inicial» ya no mueve el canje a «En revisión» por su cuenta.** Antes lo hacía, porque su `etapa_resultante` lo decía; ahora la etapa la elige quien registra. Es la consecuencia directa de separar los dos campos, no un olvido.

Se verificó al revisar que **ningún registro histórico se alteró**: los 605 movimientos de canje están intactos, y ninguno tenía etapa guardada —la migración solo tocó `tipos_movimiento` y el tipo enumerado—.

---

## D-061 · Cambiar la etapa desde la ficha deja rastro en la bitácora

**Contexto.** La etapa de un canje se puede cambiar por dos caminos: registrando un movimiento, o editando la ficha. El primero quedaba en la línea de tiempo y el segundo no.

Medido en `dev`, respondiendo una pregunta del usuario: se editó la ficha a «En oferta» y la bitácora siguió mostrando que el último movimiento la había dejado en «En negocio». Las dos pantallas decían cosas distintas, y el cambio no tenía fecha ni autor.

Eso es especialmente malo para lo que la bitácora existe —el pedido original hablaba de *"registrar historial, poder ver el historial, y de futuro generar reportes consolidados en línea de tiempo con gestiones y actividades"*—: un cambio de etapa sin rastro no aparece en ninguno de los tres.

**Decisión: editar la etapa en la ficha registra un movimiento automático**, de tipo `CAMBIO_ETAPA`, con fecha, autor y un comentario que dice de qué etapa a cuál. Las dos vías quedan con la misma memoria.

**Solo cuando la etapa cambia de verdad.** Guardar la ficha sin tocarla, o guardar la misma etapa, no registra nada: apretar Guardar no puede ensuciar la bitácora. Y corregir un email tampoco deja rastro — eso no es historial.

**El tipo va como `activo = false`, y no es una contradicción.** El campo significa "se ofrece en el selector", y este no se elige: lo escribe el sistema. Existe en el catálogo porque `movimientos.tipo_movimiento` tiene clave foránea contra él.

**No agenda seguimiento**, y eso obligó a cambiar la bandeja. Corregir un dato no es una gestión: agendar uno metería el canje en «Qué me toca hoy» por una razón que nadie eligió. Pero la bandeja tomaba el compromiso **del último movimiento**, así que un registro sin seguimiento habría borrado el que había y el canje habría reaparecido en la lista.

Ahora la bandeja toma el último compromiso **que exista**, no el del último movimiento. Es además la lectura correcta en general: un compromiso sigue en pie hasta que alguien pone otro.

**El comentario usa los rótulos y no los códigos** —«En oferta», no `EN_OFERTA`—: lo lee una persona en la línea de tiempo. Para eso, `ETAPA_LABELS` se mudó de `reportes_canjes` a `app/models/canje.py`, al lado del enum, que es donde corresponde el nombre canónico de un valor.

**Queda pendiente lo mismo en negocios.** Su formulario también permite editar la etapa sin dejar rastro. No se tocó porque el pedido era sobre canjes, y hacerlo de paso habría metido un cambio de comportamiento en un dominio que nadie estaba mirando.

### Nota de método

La primera corrida de esta verificación dio un resultado **falso**: dijo que la edición de la ficha se perdía al borrar un movimiento. El servidor local estaba corriendo código anterior al arreglo de `D-060`. Se detectó porque el resultado contradecía un arreglo que sí estaba en el código, se reinició y se volvió a medir. Vale anotarlo: un servidor de desarrollo que no se reinició es una fuente de conclusiones equivocadas que parecen mediciones.

---

## D-062 · Sobre quién se hizo la gestión

**Contexto.** La bitácora decía **qué se hizo** (el tipo), **dónde quedó el canje** (la etapa) y **cuándo** (la fecha), pero no sobre quién. Un canje tiene dos corredores —el solicitante y el propietario— y una llamada o un WhatsApp se le hace a uno de los dos. Sin ese dato, *"Seguimiento - Llamado · 3 veces"* no dice si se insistió tres veces al mismo o una vez a cada uno, y un reporte de gestión no puede separar quién no contesta.

**Decisión: un tercer campo, `corredor`, con dos valores: solicitante o propietario.**

**Es optativo, y eso sale del pedido.** Fue *"la opción de registrar"*, y hay movimientos que no son sobre un corredor: una cancelación, un comentario general, el registro automático de un cambio de etapa. Forzar la elección obligaría a poner un dato falso en esos casos, que es peor que dejarlo vacío.

**No se precarga.** A diferencia de la etapa —donde lo habitual es que no cambie, así que precargarla ahorra una decisión— acá no hay respuesta habitual: depende de a quién se llamó. Adivinar dejaría el dato mal en la mitad de los casos.

**El selector muestra los nombres, no las etiquetas.** «Corredor solicitante» a secas obliga a recordar quién es de los dos; «Solicitante · LUCÍA ELENA BAEZ CASTILLO» se elige de un golpe. Por eso el campo va en su propia fila a ancho completo: en media columna los nombres se cortan justo donde importa. Se verificó con el desplegable abierto en captura.

**Va como `String(20)` y no como tipo enumerado de Postgres**, igual que `etapa_resultante` en la misma tabla y por el mismo motivo: `movimientos` es polimórfica —sirve a canjes y a negocios— y un valor que solo tiene sentido en un dominio no debería imponerle un tipo a la columna que comparten. La validación la hace Pydantic en la API, que es donde el dominio se conoce; se verificó que un valor inventado devuelve 422.

**Los 605 migrados quedan en nulo.** El Excel no traía el dato. Nulo dice la verdad —"no se sabe"— y rellenar la columna adivinando un corredor habría sido inventar historial.

---

## D-063 · Cantidades junto a los montos, y el potencial separado de lo efectivo

**Contexto.** El tablero de negocios abría con tres montos y las cantidades vivían en la letra chica del pie de cada uno: *"7 liquidaciones en 6 negocios"*. La pregunta "cuántos negocios tengo en el ciclo" se contestaba leyendo un renglón de 11 píxeles, mientras la de canjes abre con Total, Activos, Cancelados y Tasa en número grande.

**Y había algo peor que una omisión.** El listado de Negocios tenía un solo par de columnas de plata que sumaba **todas** las liquidaciones de cada negocio: ganadas, no concretadas y abiertas en la misma cifra. El filtro por estado no lo arreglaba, porque decide **qué negocios aparecen**, no **qué plata se suma** — filtrar «Activo» y leer el total daba un número que mezclaba plata efectiva con plata potencial. Con los datos de hoy no se notaba, porque los 2 negocios abiertos no tienen ninguna liquidación cerrada encima; se rompía el día que un negocio tuviera la promesa ganada y la escritura abierta, que es el caso normal.

### Decisión 1: en el listado, tres columnas de plata en vez de una

**Ganado · En pipeline · No concretado**, las tres en comisión real ViveProp. Cada fila dice cuánto de ese negocio ya entró, cuánto podría entrar y cuánto no entró, y el pie da los tres totales por separado.

Así el número es correcto **con cualquier filtro puesto**, en vez de depender de que el filtro y la columna coincidan por casualidad. Un test lo fija: el mismo negocio, con y sin filtro, devuelve las mismas tres cifras.

**Se fue la columna de comisión total bruta.** Era la que mezclaba estados, y conservarla "de referencia" habría dejado la trampa intacta al lado del arreglo. El bruto por liquidación sigue en la ficha, que es donde se lo mira para trabajar.

**El cero se muestra como guion.** Casi todos los negocios tienen plata en una sola de las tres columnas: dos `$0` escritos en cada fila tapan el único número que esa fila tiene para decir.

**El helper reusa `BUCKETS` de la reportería** en vez de repetir la lista de estados. Si algún día `DESISTIDO` deja de contar como no concretado, el listado y el tablero se mueven juntos o van a decir cosas distintas de la misma plata.

### Decisión 2: en el tablero, una fila de cantidades antes de los montos

Negocios · Ganados · En pipeline · No concretados. **El número grande es de negocios y el chico de liquidaciones**, y las dos unidades van juntas porque ninguna reemplaza a la otra: 7 liquidaciones pueden ser 6 negocios, y ahí "6" y "7" contestan preguntas distintas.

Los tiles de plata dejaron de repetir esos conteos: dichos dos veces, el ojo los lee como dos datos distintos.

**La tasa de cierre deja las abiertas afuera del denominador** — es ganadas sobre resueltas, 41,2% hoy. Si las abiertas entraran, abrir un negocio nuevo haría **bajar** la tasa de cierre sin que se haya perdido nada, que es lo contrario de lo que el número debe decir.

**Los conteos de negocios pueden sumar más que el total, y se mide en vez de suponerse.** Un negocio con liquidaciones en dos estados está en dos recuadros. La pantalla calcula la diferencia y solo cuando existe escribe cuántos son, para que la resta no quede como un descuadre sin explicación. Hoy da 0. En liquidaciones nunca puede pasar: cada una tiene un estado y uno solo, y un test fija que los tres buckets suman exacto el total.

**`total_negocios` y `total_hitos` no violan `D-006`.** Ese principio prohíbe totalizar los tres **montos**, porque sumar plata que entró con plata que no entró da un número sin significado. Estos dos son conteos del universo y salen de contar filas, sin pasar por los buckets. El test que cuidaba la regla se volvió más preciso en vez de aflojarse: ahora nombra los dos campos permitidos y verifica lo que de verdad importa.

### Lo que sigue sin estar, a propósito

El potencial es el **monto completo, no un valor esperado**: no hay probabilidad por etapa, así que un negocio en E2 y uno en E6 aportan lo mismo al pipeline. Y sigue expresado en la **UF del día en que arrancó** cada negocio, no la de hoy, así que lo abierto vale más de lo que dice. Las dos son decisiones pendientes del usuario, no cosas que se resuelvan de paso.

### Nota de método

Al levantar el servidor local para verificar había **un uvicorn viejo escuchando en el 8000**, de una sesión anterior. Es la misma trampa de la nota de `D-061`: se mató antes de medir. La verificación cruzada que da confianza es otra: los tres totales del pie del listado coinciden **al peso** con los tres tiles del tablero --8.087.861,69 / 1.824.272,06 / 4.751.490,69-- y son dos caminos de código distintos sobre la misma base. Antes no podían coincidir, porque uno de los dos sumaba estados mezclados.

---

## D-064 · El reparto de la comisión, y por qué no es un multiselect libre

**Pedido.** Ver en reporte mensual y vista directorio los montos de los negocios, la comisión de los corredores que gestionan, la que aportan los concentradores y la del equipo ViveProp. La idea propuesta fue un filtro de selección múltiple sobre las métricas.

**Antes de diseñar se midieron los datos**, y de ahí salió todo lo demás.

### Hallazgo 1: el valor de los negocios no puede compartir eje con ninguna comisión

1.556 millones contra 34,8 en toda la historia: **45 veces**. En el mismo eje, las cuatro comisiones quedan aplastadas contra el cero. Y no se arregla con doble eje, que es la peor práctica número uno en visualización: ahí la relación entre las series la termina decidiendo la escala elegida, no el dato.

Por eso el monto va en su propio panel. **Y esto es lo que hace que el multiselect libre sea una mala idea:** dejar elegir "monto del negocio" junto a "comisión del equipo" produce un gráfico que no dice nada, y el usuario no tiene por qué saber de antemano cuáles se pueden mezclar. El selector quedó acotado a elegir **segmentos del reparto**, que siempre comparten escala porque son partes de la misma plata.

### Hallazgo 2: la venta y el arriendo tampoco son la misma unidad

Esto no estaba en el pedido y apareció al mirar la pantalla renderizada: el panel de montos dibujaba **dos barras sobre seis meses**. La causa: en una venta la base es el precio de la propiedad --cientos de millones-- y en un arriendo es **un mes de renta**, del orden del millón. 1.556 millones contra 2,3. Los arriendos quedaban por debajo de un píxel.

Es el mismo defecto que hizo descartar `valor_prop` en canjes (`D-054`): un campo que mezcla precio de venta con renta mensual. Se partió en `valor_venta` y `valor_arriendo`, cada uno con su panel, y hay dos tests que lo fijan --uno de la separación y otro de que un negocio sin tipo de operación caiga en venta en vez de desaparecer--.

Detalle que confirma la lectura: en los dos arriendos del histórico la base **coincide exactamente** con la comisión total, porque en arriendo la comisión es 50% + 50% de un mes. O sea, un mes.

### Hallazgo 3: los tres montos de comisión no son series paralelas, son un reparto

Verificado contra el motor, liquidación por liquidación:

```
comisión total + rebate = corredores + terceros + equipo + real ViveProp
```

El rebate va del lado izquierdo y no del derecho porque **no es una tajada**: es plata que entra desde afuera, la que el concentrador comparte de lo que le cobró al vendedor (`D-018`).

Por eso el panel es **apilado y no líneas superpuestas**: el alto de la barra es la plata que se reparte y cada segmento dice quién se quedó con qué. Superpuestas se pisan y, peor, invitan a leerlas como si compitieran entre sí. Y contesta algo que ninguna pantalla decía: **el 57% de cada peso de comisión se lo lleva el corredor que gestiona**.

Un test nuevo fija la identidad sobre los 18 casos que cierran. Es la premisa del gráfico: si deja de cerrar, los segmentos ya no suman el alto de la barra y el apilado empieza a mentir.

### El descuadre se muestra, no se tapa

La identidad **no** cierra en `VVP-2`: 903.802,94 de diferencia, el descuadre de origen ya documentado --la planilla bajó la comisión total sin recalcular el reparto--. En las ventanas que lo contienen, los segmentos suman más que la comisión total registrada.

La pantalla **mide la diferencia y la dice**, con el monto y el motivo, en vez de que el que mira la barra se quede sin explicación de por qué el alto no coincide. El umbral es de un peso y no de cero porque los siete montos se guardan cuantizados por separado, y sobre decenas de filas eso deja centavos de arrastre que no son un descuadre de nada.

### Esconder un segmento no puede leerse como que la plata bajó

Si el total se calculara sumando lo visible, apagar un segmento bajaría la cifra rotulada. Eso se lee como una caída, y no hubo caída: se escondió. `EvolucionMensual` recibió una prop para que el total salga del mes completo y no de los segmentos mostrados.

### El tercer color costó, y el orden de la pila no es negociable

El archivo ya advertía que con tres series el validador no daba margen. Se probaron ocho combinaciones con el script de la guía de visualización --nunca a ojo--. Resultado:

- La única terna que pasa las seis comprobaciones en los dos modos es marca, acento y el teal de `info`.
- Pero **solo en un orden**: en oscuro, el teal contra `brand.4` cae a ΔE 4.3 en deuteranopía, o sea indistinguibles. Se resolvió dejándolos **no adyacentes** en la pila, que es lo que el validador mide. Con marca abajo, acento al medio y teal arriba: ALL CHECKS PASS en claro y en oscuro, peor par adyacente ΔE 13.1.
- El teal de relleno es `info.6` en los dos modos: el paso claro que se usa para la línea de tendencia queda fuera de la banda de luminosidad como área.

Cambiar el orden de los segmentos por estética vuelve a juntar el par que colisiona. Está anotado en el código.

**No hay cuarto segmento.** Terceros y rebate son 2 y 3 liquidaciones en toda la historia: dentro de la barra serían un pelo invisible, y además no habría color que pase. Van como cifras al costado, con la aclaración de que el rebate ya está dentro de «Real ViveProp» y no se suma otra vez.

### De paso: la pantalla dejaba de saber qué era plata

`Variacion` ganó `es_plata`. La tabla de comparaciones decidía si formatear en pesos con **un conjunto de nombres visibles** --`new Set(['Comisión real ViveProp', 'Comisión total'])`--, exactamente el acoplamiento contra el que advierte el comentario de `dominio` dos campos más arriba. Con siete métricas de plata nuevas eso era insostenible, y renombrar una métrica dejaba el monto sin signo de peso sin que nada fallara. Ahora sale del catálogo, que es el único lugar donde el dato se conoce.

### Nota de método

Otra vez el servidor local viejo: la primera captura mostró `$NaN` en el panel de montos porque el uvicorn seguía sirviendo `valor_base` después de partirlo en dos. Es la tercera aparición de la misma trampa (`D-061`, `D-063`). Y el hallazgo 2 --el que no estaba en el pedido-- salió **solo de mirar la pantalla renderizada**: dos barras sobre seis meses no se detectan leyendo código ni corriendo tests.

---

## D-065 · Listado de canjes activos con su historial desplegable

**Pedido.** Bajo Canjes, un listado de los canjes activos con su estado --Al día o Pendiente-- y que al pinchar una fila se desplieguen sus registros en orden cronológico.

### Primero, una corrección de método

La primera respuesta afirmó *"hoy las cuatro filas van a decir Pendiente, porque la gestión más reciente tiene 13 días"*. El usuario respondió que todos los canjes activos habían sido actualizados hoy, y tenía razón en dudar: **ese número salió de `dev`**, y en `dev` no significa nada. Ahí los 605 movimientos de canje se insertaron en una sola transacción el 22 de agosto a las 02:24, desde el Excel; no hay ni una gestión registrada desde la app. El usuario trabaja en producción, a la que este entorno no tiene acceso.

La regla que queda: **decir de qué base sale cada número.** Un dato de `dev` presentado como la realidad del usuario es peor que no darlo.

### Y una corrección de lectura, que cambió el diseño

El pedido decía *"según la fecha de último registro respecto de la última fecha de gestión"*. La primera lectura tomó eso como una sola cosa dicha dos veces. No lo es: son **dos columnas que existen de verdad** en `movimientos`.

- `fecha` — cuándo se hizo la gestión. La elige la persona en el modal.
- `creado_en` — cuándo quedó registrada. La pone el servidor y no se edita.

En los 605 migrados se separan por **años**. Y de acá en adelante se separan cada vez que alguien registra el lunes lo que hizo el viernes.

**El estado se calcula sobre `fecha`.** "Hace cuánto que nadie toca este canje" es una pregunta sobre el trabajo, no sobre cuándo se tipeó. Un test lo fija con dos canjes de igual registro y distinta gestión.

**Y la otra fecha se muestra, sin ser una señal de estado.** Si se registró tarde no cambia que la gestión ocurrió cuando ocurrió; pero sin decirlo, un registro atrasado deja un canje con cara de al día y nadie puede saber por qué. El usuario pidió explícitamente **no** convertirlo en un segundo indicador de estado, y así quedó: un dato al lado del movimiento.

### El umbral es el de la bandeja, por decisión del usuario

48 horas, las de la hoja `CONFIG`. Se le ofreció 7 o 14 días con el argumento de que en un ciclo de días casi todo va a estar Pendiente casi siempre, y un estado que casi nunca cambia deja de informar. Eligió la consistencia: **una sola definición de "atrasado" en toda la app**, y las dos pantallas nunca se contradicen. La constante se importa de `bandeja_canjes` en vez de copiarse.

### Es un reporte, no una lista de trabajo

Se pisa a propósito con «Qué me toca hoy» en las filas, pero contesta otra pregunta, y de ahí salen las diferencias:

- **Muestra todos los activos**, incluso los agendados para adelante que la bandeja esconde. La bandeja los saca de la vista con razón --si te comprometiste a llamar el jueves, el martes no es tu problema-- pero un reporte que esconde filas no sirve para saber cuántos canjes abiertos hay.
- **Dos estados y no seis.** Para "cómo viene" el detalle del semáforo es ruido.
- **El historial va del más viejo al más nuevo**, al revés que la ficha. Para leer una historia el orden cronológico es el correcto; para ver qué pasó último, el inverso.

El compromiso sigue mandando sobre el tiempo cuando existe, igual que en la bandeja: un canje agendado a futuro está al día aunque lleve un mes sin tocarse, porque eso es exactamente lo que significa haberlo agendado.

### Los registros de una carga masiva no llevan el aviso de atraso

Esto **no se detectó leyendo código ni corriendo tests**: se vio en la captura. Los 35 movimientos de los cuatro canjes abiertos decían todos *"registrado 10 días después"*, porque una carga masiva es, por definición, un registro posterior a la gestión. Repetido en cada línea deja de ser una señal y se vuelve empapelado.

**La primera hipótesis para distinguirlos era falsa, y se verificó antes de usarla:** "los migrados no tienen autor" --384 de ellos sí tienen, porque la carga corrió como el usuario admin.

Lo que sí los distingue no necesita ningún dato nuevo ni ninguna constante: **una carga comparte el `creado_en` al microsegundo**, porque es una sola transacción. Dos movimientos con el mismo instante de creación entraron juntos. El aviso se reemplaza por uno solo arriba del historial --"todos vienen de la carga del histórico del 22-08-2026"-- que además dice algo más útil que el original: qué parte de la historia es Excel y qué parte es trabajo hecho en la app.

### De paso: los rótulos de etapa estaban en tres copias

`ETAPA_LABELS` estaba escrito en el modal de seguimiento, en la bandeja y en la pantalla de canjes. Este listado iba a ser la cuarta. Las tres decían lo mismo --se comparó, no había un error todavía-- pero eran tres lugares donde renombrar una etapa deja las pantallas diciendo cosas distintas de la misma cosa, sin que nada falle. Quedaron en `canjesEtiquetas.ts`, con dos helpers para el caso en que la etapa llega como texto suelto: `movimientos.etapa_resultante` es `String(20)` y no un tipo enumerado, porque la tabla es polimórfica.

---

## D-066 · Las dos fechas del avance de negocio, y el compromiso en la bandeja

**Pedido.** En el pipeline de la ficha de negocio, poder registrar la fecha de la actividad y la de la próxima acción. La segunda es optativa y, si no se indica, **3 días hacia adelante de la última fecha registrada**.

**Sin migración.** `fecha` ya estaba implementada y validada en el backend --rechaza fechas futuras y anteriores al inicio de la primera liquidación-- y solo faltaba el campo en la pantalla. Y `proximo_seguimiento` ya es columna de `movimientos`, que es la tabla compartida entre canjes y negocios.

### Tres diferencias con canjes, las tres deliberadas

**Son 3 días y no 2.** Dos ritmos distintos: un canje se responde en días, un negocio dura de un mes a varios. Quedaron como dos constantes, `DIAS_SEGUIMIENTO` y `DIAS_SEGUIMIENTO_NEGOCIO`.

**Se cuenta desde la fecha que se registra, no desde hoy.** Es lo que dice el pedido, y se confirmó explícitamente. Tiene una consecuencia que conviene tener a la vista: cargar hoy un avance con fecha de hace dos semanas agenda una próxima acción vencida hace casi dos semanas, así que el negocio aparece de inmediato como atrasado. Se verificó en vivo: un avance con fecha del 10 de agosto quedó agendado para el 13 y la bandeja lo puso como **vencido con 13 días de atraso**. Es la lectura correcta --se registró algo viejo, su seguimiento ya está atrasado-- y en canjes se resolvió al revés, contando desde el más nuevo entre la gestión y hoy. Los dos criterios conviven a propósito y hay un test que lo declara.

**El fin de semana sí se corre**, igual que en canjes, a pedido explícito del usuario después de que la primera propuesta planteara no hacerlo. Se reusa `proximo_habil`, así que la regla vive en un solo lugar. Los feriados siguen sin saltarse, por el motivo que ese helper ya documenta.

### El compromiso manda en «Qué me toca hoy», como en canjes

El usuario eligió *"igual que canjes"* entre tres opciones, después de preguntar cómo funcionaba allá. Así que la bandeja de negocios gana lo mismo:

- Dos niveles arriba del semáforo: **vencido** y **para hoy**. Salen de un compromiso registrado, y por eso van antes que el semáforo de 30/14 días, que es una inferencia sobre el tiempo que pasó. Cuando los dos opinan, gana el que no infiere.
- **Lo agendado a futuro no se lista.** Se cuenta y se dice en una línea abajo de los recuadros. La pantalla se llama "qué me toca hoy" y listar lo que no toca es lo que hace que se deje de mirar.
- El compromiso vigente es el último que **exista**, no el del último movimiento (`D-061`): un movimiento sin seguimiento no borra lo que se prometió antes.

**La consecuencia se le dijo antes de decidir**, y se repite en la pantalla del formulario: como registrar un avance agenda 3 días por defecto, ese negocio sale de la lista por 3 días. Con dos negocios abiertos, avanzar los dos deja la lista vacía hasta que vuelva el primero. En canjes se diluye entre cien filas; acá son dos.

### El contador de «requieren atención» se deriva, no se suma a mano

Era `sin_gestion + critico + advertencia`, escrito a mano. Con dos niveles nuevos habría seguido compilando y mostrando un número menor al real: **ese error exacto ya se cometió una vez en canjes** --el chip decía «2» sobre una lista de seis filas-- y ningún tipo lo detecta. Ahora sale de filtrar `ORDEN`, así que agregar un nivel lo incluye solo.

Y el "de N negocios" del subtítulo pasó a contar los listados **más** los agendados: los agendados están abiertos, solo que su día no es hoy.

### Nota de método

La verificación en vivo registró dos avances en `dev` y eso **movió la etapa de los dos negocios a E1**, porque el tipo elegido traía `etapa_resultante`. Se restauraron las etapas originales --E5 y E4-- y se borraron los dos movimientos, dejando la bandeja igual que antes. No hay endpoint para borrar movimientos de negocio, así que la limpieza fue por SQL. Vale anotarlo: verificar contra una base con datos reales deja rastro, y el rastro hay que planificarlo antes de escribir el POST.

---

## D-067 · Carga del historial de etapas, y la fecha de término de canjes

Dos temas que salieron de la misma pregunta: *"con lo que se fue incorporando, hay cómo resolver los avisos del recuadro rojo de la vista directorio"*. Se midió antes de responder, y la respuesta fue **no** para los dos avisos. Pero uno de los dos se puede desbloquear cargando datos, y el otro dejó al descubierto algo peor.

### Los dos avisos seguían siendo verdad

**Plazos de negocios:** cero movimientos de negocio registrados, y **las 7 liquidaciones cerradas tienen la misma fecha de inicio y de cierre**. Las 7. No había ni una duración real en toda la base.

**Comisión de canjes:** `comision_dbrokers` en 0 de 297, `valor_negocio` en 0 de 297. `valor_prop` está en 296 pero es el campo descartado en `D-054`.

### Lo que sí cambió: la fecha del avance es editable

Desde `D-066` se puede registrar un movimiento con fecha pasada, así que la historia se puede cargar **hacia atrás** en vez de esperar a que se acumule. Eso convierte *"en unos meses la proyección pasa de estimarse a calcularse"* en *"cuando alguien cargue lo que ya sabe"*. De ahí sale la carga masiva de este sprint.

### La plantilla sale pre-llenada, y no es un lujo

**71 filas** para los 18 negocios: una por cada etapa desde `E1` hasta donde está hoy cada uno, con el código y la etapa puestos. Solo hay que escribir fechas. Un archivo en blanco pediría escribir 213 celdas sin equivocarse en ninguna; así son 71 fechas y nada más.

Dos hojas, porque son **dos granos distintos**: el historial es una fila por etapa, y la corrección de fechas de inicio es una fila por liquidación --`VVP-3` tiene dos--. Mezclarlas obligaría a repetir el mismo dato en varias filas y a decidir cuál gana si no coinciden.

**El supuesto de secuencia se declara.** Que un negocio en `E5` pasó por `E1` a `E4` es lo normal, no una certeza: las filas que no correspondan se borran, y las que queden sin fecha se ignoran.

### Cuatro reglas de la carga, cada una evitando un daño concreto

**No agenda próxima acción.** Si lo hiciera, cargar la historia de 18 negocios metería 18 compromisos vencidos de meses en «Qué me toca hoy» y la pantalla quedaría en rojo por una tarea administrativa. Una carga histórica no es una gestión: nadie prometió volver el jueves.

**No hace retroceder la etapa vigente.** Registrar un movimiento mueve la etapa del negocio al del movimiento cronológicamente más nuevo (`D-060`). Cargar `E1` y `E2` de un negocio en `E7` lo bajaría a `E2`: reemplazaría el dato bueno por uno viejo. La carga escribe historia y no toca el presente; se verificó en vivo que `VVP-15` siguió en `E5` después de cargarle desde `E1`.

**Recargar no duplica.** La clave es negocio + etapa. Es lo que permite iterar --cargar lo que se sabe, mirar el resultado, corregir-- sin ensuciar la bitácora.

**No corrige una fecha de inicio si eso mueve plata, y lo comprueba en vez de suponerlo.** Cuando una liquidación no tiene `fecha_valorizacion`, su UF sale de `fecha_inicio`: cambiarla movería el monto y la comisión. La carga se niega y lo informa. Se midió antes de escribirla: de las 7 liquidaciones a corregir, cinco tienen `fecha_valorizacion` y dos tienen valor manual, que manda sobre la conversión (`D-017`), así que hoy **ninguna** está en riesgo. La guarda es mecánica igual, para que siga siendo verdad si los datos cambian.

Y una relajación deliberada: **la validación de fecha mínima se levanta para esta carga.** El sistema rechaza un movimiento anterior al inicio de la primera liquidación, que es correcto para el uso normal; pero en 7 liquidaciones ese inicio **está mal**, así que la validación bloquearía justamente las fechas reales. Se permiten y se listan aparte, que es la lista de las que conviene corregir.

### Verificación de punta a punta

Se bajó la plantilla, se llenó como la llenaría una persona --las cinco etapas de `VVP-15` y la corrección de `VVP-1`-- y se cargó contra `dev`. Resultado: 5 movimientos creados, 66 filas sin fecha ignoradas, 1 fecha corregida, cero omitidas. Y lo que apareció es el punto de todo esto: **`VVP-1` pasó de duración desconocida a 72 días**, y `VVP-15` mostró **147 días de `E1` a `E5`**. Después se restauró `dev` a su estado anterior.

### Canjes: la fecha de cierre es fecha de término

Buscando si al menos los canjes tenían duración de ciclo apareció esto:

- **47 canjes tienen fecha de cierre**, y están todos **cancelados** en etapas de mitad de proceso. Ninguno llegó a Cierre.
- **31 tienen la etapa en Cierre**, y ninguno tiene fecha.
- **Los dos conjuntos no se cruzan: intersección cero.**

O sea que `canjes.fecha_cierre` es la **fecha de cancelación**. Si esa mediana se hubiera publicado como "cuánto tarda un canje en cerrar", se habría publicado el tiempo que tardan en morir.

El usuario propuso como norma que un canje cancelado no tenga fecha de cierre y quede en su etapa real. **Se acordó no vaciar esas 47 fechas**: son el único registro de cuándo murió cada canje, y con ellas se puede saber cuánto sobrevive uno antes de caerse --mediana 8 días, y bajando: mayo 8, junio 15, julio 2, agosto 1--. La columna se lee **junto al estado**: cancelado, es cuándo se canceló; cerrado, cuándo cerró. Cero migración y cero dato destruido.

**Y sobre los 31: el usuario confirmó que se cayeron**, estando en la etapa de Cierre. Así que **nunca se cerró ningún canje**, el 0 de «Canjes cerrados» es correcto y se deja como está. Queda anotado un hueco del modelo para cuando eso cambie: `CanjeEstado` solo tiene `ACTIVO` y `CANCELADO`, así que hoy no hay forma de registrar un cierre exitoso.

### Nota de método

Las dos hipótesis que se probaron antes de usarlas resultaron **falsas**, y las dos se descartaron a tiempo: que los movimientos migrados se distinguieran por no tener autor (`D-065`), y que los canjes con fecha de cierre fueran los cerrados. La segunda habría publicado una métrica equivocada. Verificar antes de construir sigue siendo más rápido que construir y desarmar.

---

## D-068 · La secuencia se valida, y el pipeline se lee cronológicamente

Dos defectos que salieron de mirar las fichas después de la primera carga real, no de leer código ni de correr tests.

### El defecto: la carga aceptó una historia imposible

`VVP-1` y `VVP-2` quedaron con `E1` y `E2` fechados en **agosto de 2026** — después de que esos mismos negocios terminaron, en enero. La causa no es del usuario: **Excel completa el año actual** cuando alguien escribe `12-08` en una celda con formato de fecha, y la columna de referencia decía `12-08-2025`.

La carga lo aceptó porque validaba que la fecha no fuera futura y nada más. Y nadie lo habría notado hasta que la proyección de plazos empezara a devolver **duraciones negativas** — de `E1` a `E2`, menos un año.

**Ahora se valida la secuencia.** El pipeline es ordenado, así que las fechas tienen que subir junto con la etapa. Cuando no lo hacen, el mensaje señala al sospechoso correcto: *"VVP-2: E2 el 13-08-2026 es posterior a E3 el 02-10-2025, y una etapa anterior no puede tener una fecha más nueva"*, y agrega la causa habitual para que no haya que adivinarla.

**Se rechaza el negocio completo, no la fila.** Cuando `E1` es posterior a `E3` no hay forma de saber cuál de las dos fechas está mal: cargar la mitad de una historia contradictoria es peor que no cargar nada. Y la validación mira **también lo que ya está guardado**, así que partir el archivo en dos no es una forma de esquivarla sin darse cuenta.

**Dos etapas el mismo día son válidas.** La regla es que las fechas no bajen, no que suban: exigir que suban rechazaría una calificación y una visita el mismo día, que es exactamente lo que trajeron los datos reales.

Primera versión del mensaje decía la relación **al revés** --"E3 es posterior a E2" cuando era lo contrario-- y lo agarró el test. Vale anotarlo: en un mensaje de error, invertir la relación manda a corregir el dato bueno.

### El otro defecto: el orden de la línea de tiempo

El usuario reportó que el historial se veía "en desorden". La mitad era el año mal, pero había una segunda causa real: **`E2` aparecía arriba de `E1` aunque los dos tenían la misma fecha.** El historial se ordenaba solo por `fecha`, sin desempate, así que dos etapas del mismo día salían en orden arbitrario.

Dos cambios:

**Ascendente, de más viejo a más nuevo.** Antes iba descendente, como una bitácora que se mira para ver qué pasó último. Pero el pipeline es una secuencia y su historia se lee de `E1` hacia adelante — es el mismo criterio que ya se había elegido a propósito para el historial del reporte de canjes activos (`D-065`). La línea de tiempo marca como activo el **último** paso, que ahora es el actual.

**Desempate por `id`.** La carga inserta en el orden del archivo, que es el de las etapas, así que dos etapas del mismo día salen en el orden en que ocurrieron. Deja de depender de lo que devuelva el motor de base de datos.

La bitácora de canjes **no** cambia: ahí el orden descendente es correcto, porque no es una secuencia sino una lista de gestiones y lo que importa es la última.

### Nota de método

Los dos defectos se encontraron **abriendo una ficha**, después de que la carga reportara éxito sin una sola omisión. Es la tercera vez en esta serie de cambios que el problema real aparece mirando la pantalla renderizada y no en los tests: antes fueron las dos barras sobre seis meses de `D-064` y los 35 avisos repetidos de `D-065`. Un resumen que dice "cargado, cero errores" no es evidencia de que el dato quedó bien; es evidencia de que ninguna regla lo contradijo. Y la regla que faltaba era justamente la que importaba.

---

## D-069 · Los códigos se ordenan por número, no como texto

El listado de Negocios salía `VVP-1, VVP-10, VVP-11, VVP-12 … VVP-19, VVP-2, VVP-3`. Ordenar `codigo` como texto compara caracter por caracter, así que el `1` de `VVP-10` le gana al `2` de `VVP-2`. Con 18 negocios el efecto es que la mitad de la lista está en el lugar equivocado.

**Se resuelve en Python y no en SQL.** Extraer el número necesitaría `substring(... from '[0-9]+$')::int`, que es exclusivo de Postgres, y dejaría el orden sin poder probarse contra la base en memoria. Es el mismo criterio que ya se aplicó al agrupamiento por mes del reporte mensual, y por el mismo motivo: tener el orden verificado vale más que ahorrar una vuelta sobre 18 filas.

La clave vive al lado del modelo, en `clave_de_orden`, porque es una propiedad del formato del código y no de una pantalla. Se aplica en los tres lugares que lo mostraban: el listado, y las dos hojas de la plantilla del historial.

**En la plantilla importa más de lo que parece.** La persona llena 71 filas leyendo de arriba abajo, y un orden que salta de `VVP-1` a `VVP-10` y vuelve a `VVP-2` cincuenta filas después es una invitación a escribir la fecha en la fila del negocio equivocado. Justo después de haber arreglado dos negocios con el año mal, no era el momento de dejar una trampa de transcripción.

Un código sin número al final va antes que los numerados de su prefijo. No es un caso que exista hoy, pero `-1` es determinista y no colisiona con ningún número real, así que el orden no depende de lo que devuelva el motor.

---

## D-070 · La moneda de `valor_prop` está invertida en 139 de 297 canjes

**El pedido** fue llenar «Valor negocio» automáticamente desde «Valor propiedad» y calcular la comisión de Dataprop encima. Antes de escribir nada se midió el campo de origen, y no se puede usar como está.

### La evidencia

| Etiqueta | Coherentes | Invertidos |
|---|---|---|
| CLP | 93 | **69** con valores bajo 100.000 → son UF |
| UF | 59 | **76** con valores sobre 100.000 → son CLP |

Casos concretos: un arriendo de casa en Vitacura guardado como **70 CLP**, una venta de terreno en Osorno como **3 CLP**, un departamento en Providencia como **320.000.000 UF** --trece billones de pesos-- y 50 arriendos con mediana de **700.000 UF** mensuales, o sea 28 mil millones de renta al mes.

El usuario había señalado, con razón, que el campo trae su moneda y que eso alcanza para convertir. Alcanzaría si la etiqueta fuera correcta; sus dos ejemplos lo eran, pero son de las 149 filas buenas.

### La magnitud dice la verdad y la etiqueta no

Las dos escalas están separadas por **cuatro órdenes de magnitud**: una venta en UF anda en miles y la misma en pesos en cientos de millones. No existe la propiedad que valga 5.000 pesos ni la que valga 300 millones de UF. Así que clasificar por monto no es adivinar.

Medida la distribución, es limpiamente bimodal y **no hay una sola fila en el medio**: las 114 ventas del tramo UF van de 1.274 a 80.000, las 48 del tramo CLP de 21 a 720 millones. Los arriendos igual: 114 en pesos, de 140.000 a 5.000.000 mensuales.

```
Venta    → bajo 1.000.000 es UF · sobre 20.000.000 es CLP
Arriendo → bajo 1.000 es UF · entre 100.000 y 20.000.000 es CLP
```

Entre esos rangos la regla **no afirma nada**, y eso es deliberado: son 9 casos cuyo monto no funciona en ninguna de las dos monedas --cuatro parcelas en Lo Barnechea con 2.100.000 y etiquetas que se contradicen entre sí-- así que probablemente les falten o les sobren ceros. Eso no lo puede resolver una regla.

### Se corrige, pero nadie corrige 139 filas a ciegas

Entre tres caminos --corregir las etiquetas, interpretar por magnitud sin tocar el registro, o calcular solo sobre las coherentes-- el usuario eligió **corregir**, previa revisión. Es la decisión correcta: una etiqueta equivocada no es un registro que haya que preservar, es un error, y mientras esté ahí cada cálculo futuro tiene que arrastrar el parche.

Pero la corrección sale de una **inferencia**, así que no se aplica sola. `app/scripts/revisar_monedas_canjes.py` genera `Archivos/revision-monedas-canjes.xlsx` con las 148 filas que necesitan atención --los 9 ambiguos primero y en amarillo, sin propuesta-- y el equivalente en pesos de cada una para poder juzgar si el monto es plausible. Las 149 correctas no van: no hay nada que decidir sobre ellas.

Cada fila lleva la **fecha de solicitud**, que es la que ubica el caso. No `creado_en`: esa es la del momento en que corrió la carga masiva, o sea la misma para los 297, y por lo tanto inútil para encontrar un canje.

El script **no escribe en la base**. Aplicar los cambios es un paso aparte y deliberado.

### Lo que sigue bloqueado, y es otra cosa

Arreglar la moneda **no alcanza para calcular la comisión.** La regla que rige el Centro de Canje aplica 6/5/4% --u 8% en arriendo-- sobre *la comisión de los corredores participantes*, no sobre el valor de la propiedad: el valor solo elige el tramo. Y la comisión de los corredores no existe como dato ni como campo.

También quedó aclarado un malentendido de fondo que venía de antes: **ViveProp no participa en los canjes ni percibe nada de ellos.** Opera a nombre de Dataprop. Así que la plata de canjes es de Dataprop, y cuando se muestre tiene que ir rotulada como tal y nunca sumada con la de negocios. Por eso el campo pasa a llamarse «Comisión Dataprop» en vez de «Comisión DBrokers».

### Nota de método: aparece una vía de lectura a producción

Durante varios sprints se dio por sentado que este entorno no tenía forma de ver producción, y todas las mediciones de canjes salieron de `dev`. Al pedir el usuario explícitamente que la revisión se hiciera contra producción, se buscó de nuevo y apareció **`backend/.env.real.bak`**, un respaldo en el propio árbol de trabajo que apunta a otro endpoint de Neon. Es producción: 7 canjes activos --el número que el usuario había corregido--, 303 canjes y los 50 movimientos de negocio de su carga.

Vale anotar el error: la afirmación "no tengo acceso a producción" se arrastró como un hecho durante toda la conversación **sin haberse verificado más de una vez**. Las cifras que se citaron mientras tanto eran de `dev` y estaban dichas como tales, pero varias conclusiones se demoraron por un límite que no existía.

Medido contra producción, el problema es más chico de lo que decía `dev`: **190 coherentes, 112 invertidas y 1 ambigua**, sobre 303 canjes. El usuario ya había corregido 8 de los 9 ambiguos por su cuenta, y después el noveno --el canje 222, que quedó en 400.000 CLP--, así que **no quedó ninguna ambigua**: 191 coherentes y 112 invertidas, 57 de CLP a UF y 55 de UF a CLP.

### La aplicación: `aplicar_monedas_canjes`

El usuario eligió aplicar las 112 sin revisar una por una. Es razonable: los casos que necesitaban criterio eran los 9 ambiguos y ya estaban resueltos; las 112 restantes son mecánicas --una casa en Maipú no vale 4.500 pesos-- y revisar 112 obviedades no rinde.

El script **solo toca `moneda_valor`**. No el monto, que es correcto: lo que estaba mal era decir en qué unidad estaba expresado.

**No escribe salvo que se lo pidan.** Sin `--aplicar` hace una pasada en seco. Es el default porque corre contra producción, y una escritura de 112 filas no puede ser el resultado de tipear mal un comando.

**Compara contra el estado actual antes de escribir.** Si un canje cambió en la base después de generarse el archivo, esa revisión está vieja y aplicarla pisaría una edición más nueva; esas filas se omiten y se informan en vez de ganar por ser las últimas en llegar. Es la guarda que hace que el archivo se pueda revisar sin apuro. Hay un test por cada rama de esa decisión.

Antes de aplicar se respaldó el estado completo --303 filas con su valor y su moneda-- en `Archivos/respaldo-monedas-canjes-antes.csv`, así que la corrección es reversible sin depender de un backup de la base.

### Aplicado, y cómo se verificó

El clasificador de seguridad de la sesión bloqueó la escritura, así que la corrió el usuario con el comando documentado. Tres comprobaciones después, contra producción:

1. **La regla ya no encuentra nada:** 303 coherentes, 0 invertidas, 0 ambiguas.
2. **Solo cambió la moneda.** Comparando fila por fila contra el respaldo: 112 monedas cambiadas, **0 valores** y **0 tipos de operación**. Es la comprobación que importa, porque el modo de falla temido era mover un monto sin querer.
3. **Los promedios pasaron a tener sentido**, que es la señal más fuerte de que la clasificación era correcta:

| | Canjes | Promedio |
|---|---|---|
| Venta · activos | 7 | $265.987.956 |
| Venta · cancelados | 167 | $288.271.368 |
| Arriendo · cancelados | 129 | $1.059.697 de renta mensual |

Antes de la corrección esos totales mezclaban UF con pesos y no significaban nada. Un promedio de venta de 288 millones y una renta promedio de un millón son cifras que se sostienen solas.

**Con esto `valor_prop` deja de ser inservible.** El motivo por el que se descartó en `D-054` --moneda equivocada en la mitad de las filas-- ya no existe. Lo que sigue faltando para calcular la comisión de Dataprop es otra cosa: la comisión de los corredores participantes, que es la base sobre la que se aplica el 6/5/4%.

---

## D-071 · Un canje ahora puede estar cerrado

**El problema.** El estado de un canje solo admitía `ACTIVO` o `CANCELADO`, así que **no había forma de registrar que se concretó**. Los 296 cancelados incluyen 31 con la etapa en «Cierre», y el usuario confirmó que ésos se cayeron: llegaron hasta la firma y no cerraron. En cuatro años no se cerró ninguno.

Eso ya se veía en dos pantallas, y las dos estaban haciendo lo mejor que se podía sin el estado:

- La métrica «Canjes cerrados» del reporte mensual daba **0 en los 46 meses** y no podía dar otra cosa: contaba etapa «Cierre» **y** fecha de cierre, y esa combinación no existe en ninguna fila porque esa fecha es en realidad la de cancelación (`D-070`).
- La vista directorio deducía los cerrados con la heurística «estado activo y etapa Cierre», que contaba como cierre exactamente a los 31 que se habían caído.

**Y ahora hace falta de verdad**, porque la comisión de Dataprop se cobra *por cada operación cerrada*: sin un estado que diga «cerró», el campo donde se registra lo cobrado no tiene cuándo llenarse.

Entre tres opciones --un tercer estado, redefinir la etapa «Cierre», o un campo aparte de resultado-- el usuario eligió **el tercer estado**.

### La etapa y el estado son cosas distintas, y ahora se ve

La etapa dice **hasta dónde llegó** el proceso; el estado, **en qué terminó**. Un canje puede llegar a la etapa de cierre y caerse igual, y eso pasó 31 veces. La migración **no reclasifica ninguna fila**: reetiquetar esos 31 sería inventar cierres que no ocurrieron.

### La identidad del apilado se mantuvo, y por eso el gráfico sigue cerrando

`canjes_solicitados = canjes_activos + canjes_cancelados` era exacta porque el estado tenía dos valores, y es lo que permite dibujar las solicitudes apiladas con el total en el alto de la barra. Con tres valores la identidad sigue siendo exacta --la partición sigue completa-- y el apilado pasa de dos segmentos a tres.

**Pero `canjes_cerrados` no podía ser uno de esos segmentos como estaba.** Se contaba por **mes de cierre** y los otros dos por **mes de solicitud**: dos granos distintos. Ahora los tres van por fecha de solicitud, y lo que responden es "de los que entraron en agosto, cuántos terminaron cerrados". Cuando haya cierres de verdad va a hacer falta además contarlos por mes de cierre, que es cuando se gana la comisión; eso llega con el eje de plata de canjes, y hoy sería una serie de ceros.

### El tercer color, otra vez validado y no elegido a ojo

El apilado necesitaba un tercer tono. Acá los tres segmentos **son estados** --cerrado, en curso, cancelado-- no categorías, así que corresponde la paleta de estado: verde, marca, rojo. Validado en ese orden semántico con el script de la guía: ALL CHECKS PASS en los dos modos, peor par adyacente ΔE 15.1 en deuteranopía oscuro.

El tritan de ese par baja a 7.4, que la guía permite **solo con codificación secundaria**. El apilado la tiene de sobra: leyenda con nombres, separación de 2px entre segmentos y el total rotulado arriba. Queda dicho en el código para que nadie lo lea como un descuido.

### Lo que se propagó

Tres servicios asumían dos estados: el resumen de canjes --que gana `cerrados` y una `tasa_cierre_pct` sobre los **resueltos**, no sobre el total--, la vista directorio, y el reporte mensual. En el frontend, el selector de estado del formulario, el filtro por etapa del dashboard, los dos gráficos apilados y los tiles.

La **tasa de cierre va sobre cerrados más cancelados** y no sobre el total, por el mismo motivo que en negocios (`D-063`): si los abiertos entraran al denominador, una solicitud nueva bajaría la tasa sin que se haya perdido nada.

**El importador de Dataprop no cambia.** Su export trae "Activo" y "Cancelado" nomás, así que `CERRADO` se marca en la app. Es coherente: Dataprop no sabe si el canje cerró, lo sabe quien lo gestiona.

---

## D-072 · El motor de comisiones de canjes, y los plazos que sí se pueden medir

Cierra el pedido de ver, en canjes, las comisiones reales de lo cerrado, las potenciales de lo abierto y una estimación de plazos.

### La plata de canjes es de Dataprop, y eso cambia cómo se muestra

Quedó aclarado un malentendido que venía de lejos: **ViveProp no participa en los canjes ni percibe nada de ellos.** Opera el Centro de Canje a nombre de Dataprop. Toda la demás plata de la app --los tres buckets, el reparto de la comisión, el ticket-- es ingreso de ViveProp, así que un monto de canjes puesto en las mismas pantallas invita a sumarlo.

Por eso el panel dice **en texto, no solo en el título**, que esa plata es de Dataprop. Un rótulo se lee; un párrafo que explica de quién es la plata, se entiende.

### Las reglas, y las dos que no estaban en el contrato

El contrato fija lo que percibe Dataprop: 6/5/4% según el tramo en UF en venta, u 8% en arriendo. Pero eso se aplica **sobre la comisión de los corredores**, no sobre el valor de la propiedad, y esa comisión no existía como dato. El usuario definió las dos tasas que faltaban: **2% por cada corredor en venta** y **50% por cada corredor en arriendo**, sobre el precio de la propiedad. Participan dos corredores, así que la comisión total es 4% del precio en venta y un mes completo en arriendo.

**El tramo lo define el valor de la operación en UF**, no la comisión. Y todo va **neto, sin IVA**: el IVA no es ingreso ni egreso, se recauda y se entrega.

Un detalle de la redacción quedó fijado en un test porque invita a "arreglarlo" mal: el contrato dice "% de la comisión de **cada** corredor participante", y como los dos cobran lo mismo, aplicarlo a cada uno y sumar da idéntico a aplicarlo al total. La ambigüedad existe y es inocua.

### El motor está anclado a los 7 canjes reales

Los casos del test no son números inventados para que pase: son los **7 canjes activos de producción**, con los montos y los valores en UF que el usuario verificó uno por uno contra su propia planilla. Coincidieron al peso, incluidos los dos guardados en pesos y los cinco en UF. Si alguien cambia una tasa o un tramo, esos siete dejan de dar y hay que decidirlo a propósito.

### Tres cifras que significan cosas distintas

| Cuál | De dónde sale | Qué es |
|---|---|---|
| Cobrada | el campo manual de los cerrados | un hecho |
| Potencial | la regla, sobre los abiertos | una estimación |
| No concretada | la regla, sobre los cancelados | lo que no se llegó a cobrar |

**La cobrada no se calcula: se registra.** Cuando un canje cierra, la comisión se negocia y se factura. Ese fue el aporte del usuario sobre la propuesta original --que planteaba el campo manual como "override para excepciones"-- y es mejor: separa *estimado* de *real*, que es la distinción que el reporte necesita.

Por eso el campo pasó a llamarse **«Comisión Dataprop cobrada»**, y un canje cerrado sin ese dato cuenta en el conteo pero no en el monto: cerró y todavía nadie registró cuánto se cobró, que es distinto de cobrar cero.

### Cada caso con la UF que le corresponde

- **Abiertos** → la de hoy. Es un potencial: vale lo que valdría si cerrara ahora.
- **Cerrados** → la del cierre. Ahí la comisión se gana.
- **Cancelados** → la de la fecha de solicitud. Ese valor de propiedad se registró en ese momento; ponerle la UF de hoy a un canje que se cayó en 2023 sería valorizarlo con una unidad que nunca tuvo.

Todo con `valor_uf`, que **falla si no hay UF para esa fecha** en vez de agarrar el último valor de la serie. No es paranoia: una consulta armada al momento tomó la UF del **09-09-2026** --futura, porque la serie se publica adelantada-- y el error solo salió porque el usuario preguntó qué fecha se había usado.

Y donde no hay UF, el canje se informa como **no valorizado**, no como cero. En producción eso son 178 canjes de 2022 a 2025, porque allá la serie empieza el 01-01-2026; `dev` sí tiene el histórico. Queda `cargar_uf_historica`, que lo trae del SII --se verificó que sirve los años pasados: 365 fechas de 2025-- y que solo inserta lo que falta.

### Los plazos miden dos cosas, y ninguna es cuánto tarda en cerrar

No hay un solo canje cerrado, así que ese número no existe. Lo que sí se puede medir:

- **Cuánto sobreviven antes de caerse:** 42 casos, mediana 8 días, de 1 a 44.
- **Cuánto llevan los abiertos:** 7 casos, mediana 17 días, de 1 a 49.

Van separados y nombrados por lo que son. Llamar "duración" a la mediana de las cancelaciones sería publicar el tiempo que tardan en morir como si fuera el que tardan en cerrar --el error que casi se cometió al ver esa mediana de 8 días por primera vez--.

**Y se dice cuántos quedan afuera.** 254 cancelados no tienen fecha de término, así que su duración es desconocida y no entra en ninguna mediana. Una duración de cero días también se cuenta como desconocida: no se distingue de "el origen traía una sola fecha".

### Nota de método

Al mirar la pantalla contra `dev`, la comisión no concretada dio **1,6 billones de pesos**. No es un error del motor: `dev` no tiene la corrección de monedas que se aplicó en producción (`D-070`), así que 139 canjes tienen la moneda invertida y el motor los convierte fielmente. Entra basura, sale basura, y se ve. Es la mejor demostración de por qué esa corrección era condición previa.

---

## D-073 · Los recuadros de la bandeja reparten el universo

El usuario señaló que los dos paneles de «Qué me toca hoy» no eran consistentes con la realidad. Tenía razón, y eran dos defectos distintos.

### Los seis recuadros no sumaban el total

En canjes: siete abiertos, y los seis recuadros mostraban 0, 2, 0, 0, 0, 0. En negocios: dos abiertos, y los seis en cero. El resto vivía en una línea de texto chica abajo: *"5 canjes tienen seguimiento agendado para más adelante y no se listan acá"*.

Eso lo decidí a propósito, y el argumento era razonable: **los agendados no requieren atención, así que no merecen un recuadro.** Pero el resultado fue malo. Un tablero cuyos recuadros no reparten el universo obliga a leer la letra chica para saber dónde está el resto, y en negocios el efecto era peor: seis ceros al lado de un encabezado que dice "0 de 2 negocios" se lee como *no hay nada*.

**Ahora «Agendados» es un recuadro más**, y los siete reparten exacto: 0+2+0+0+0+0+5 = 7 en canjes, y 0×6+2 = 2 en negocios. Va en **gris y no en un color de estado**, que es lo que dice "esto no es algo pendiente" sin sacarlo de la cuenta.

El argumento original --que no requieren atención-- sigue siendo cierto; lo que estaba mal era la conclusión. No merecen un color de alarma, pero sí un lugar en la partición.

### El vacío afirmaba algo falso

Con los dos negocios abiertos agendados, la tabla queda sin filas y la pantalla decía **«No hay negocios con liquidaciones abiertas»** — justo debajo de un encabezado que decía *"0 de 2 negocios con liquidaciones abiertas"*. Dos frases de la misma pantalla contradiciéndose, y la que estaba en el lugar más visible era la falsa.

El vacío tiene **dos causas distintas** y decía solo una:

- No hay nada abierto → *"No hay negocios con liquidaciones abiertas."*
- Todo lo abierto está agendado → *"Los 2 negocios abiertos tienen su próxima acción agendada para más adelante, así que hoy no toca ninguno."*

Canjes tenía el mismo problema latente: su vacío decía *"Nada pendiente acá"*, que con todos los canjes agendados se habría leído igual de mal. Se arregló también, antes de que apareciera.

### Nota de método

Los dos defectos son consecuencia directa de haber agregado los agendados (`D-059`, `D-066`): esconder filas de una lista cambia lo que significan los conteos y los vacíos que la rodean, y eso no se revisó cuando se agregaron. Ninguno de los dos lo detecta un test --los números que sirve la API son correctos-- y ninguno se ve en `dev`, donde no había agendados. Aparecieron cuando el usuario usó la app con sus datos.

---

## D-074 · «Al día» incluye los agendados

Tercera vuelta sobre el mismo panel, y la que lo deja bien. Vale seguir las tres porque cada una arregló algo y creó lo siguiente.

**Primero** los agendados no tenían recuadro: iban en una línea de texto, con el argumento de que no requieren atención. Resultado: con siete canjes abiertos y cinco agendados, los seis recuadros sumaban dos y no había forma de ver dónde estaban los otros cinco (`D-073`).

**Después** tuvieron el suyo. Los siete repartían el universo, pero apareció otra cosa: «Al día» mostraba **0** al lado de un «Agendados» en **5**, y el usuario señaló que eso *"da la impresión de que no hay canjes o negocios activos"*. Tenía razón.

**Ahora los dos van juntos.** Un canje agendado para el jueves y uno gestionado hace tres horas están **al día** en el único sentido que le importa a esta pantalla: no requieren atención hoy. Uno porque se comprometió una fecha, el otro porque el reloj no llegó al umbral. Van juntos en el número y separados en el pie.

Quedan seis recuadros que reparten exacto: 0+2+0+0+0+**5** = 7 en canjes, y 0×5+**2** = 2 en negocios.

### La regla vale siempre, no solo cuando no hay incidentes

El usuario la había planteado condicionada --*"si no hay incidentes… entonces Al día muestra los agendados"*--. Se aplicó **sin la condición**: si el número cambiara de significado según si hay incidentes o no, dejaría de ser comparable con el de ayer, y quien lo mire tendría que reconstruir cuál de las dos definiciones está viendo. «Al día» significa siempre lo mismo: todo lo que no requiere atención hoy.

### No enumerar ausencias

El pie decía **«0 gestionados hace menos de 24 h»** cuando los cinco eran agendados, y el usuario observó que *"da la sensación de desatención de los procesos, cuando la realidad es otra"*. Exacto, y la regla general que sale de eso vale más que el arreglo puntual:

> Un pie que enumera lo que **no** hay se lee como un reproche. El mismo pie enumerando lo que hay se lee como información.

Así que el desglose solo nombra las poblaciones que existen: `5 con seguimiento agendado`, o `2 gestionados dentro del plazo`, o las dos separadas por un punto. Cuando «Al día» es cero, queda el texto del umbral de siempre.

Y dice **«dentro del plazo»** y no «hace menos de 24 h» porque el umbral lo manda la API: escribirlo a mano en la pantalla es como se despega del que aplica de verdad --el mismo error que ya se había corregido en la explicación de los niveles--.

### Lo que no cambió

Los contadores de «requieren atención» --el del encabezado y el del filtro-- excluyen «al día» por construcción, así que la fusión no los toca. Siguen diciendo 2 de 7 y 0 de 2, que es correcto.
