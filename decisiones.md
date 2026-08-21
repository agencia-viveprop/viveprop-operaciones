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

**Diferido explícitamente:** límite de intentos de login, política mínima de contraseñas, restricción de dominio de email, fuga de tiempos que revela qué emails tienen cuenta, y limpiar `SESSION_SECRET` (declarada en `config.py`, README y `render.yaml`, nunca leída por el código).

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

**Decisión.** No se fuerza el motor para reproducirlo. El caso queda como `xfail` estricto en `tests/test_comisiones.py`, con el motivo escrito: si algún día se corrige y el test empieza a pasar, pytest avisa en vez de quedar silenciosamente verde. Y hay un test dedicado, `test_vvp2_esta_descuadrado_en_el_origen`, que deja constancia del monto exacto y de que el broker se calculó sobre la base original.

**Pendiente para el sprint 10.** Al cargar hay que decidir quién absorbió los 903.803: si el corredor aliado tomó parte del ajuste y la planilla no se actualizó, o si ViveProp lo absorbió completo. De eso depende con qué números entra VVP-2 a la base.

**Nota sobre `D-017`.** El caso confirma que el valor manual existe como necesidad —Felipe lo ratificó—, pero VVP-2 tal como está registrado no lo implementa de forma consistente: se overrideó el total sin rehacer el reparto. El diseño de `valor_clp_manual` sigue siendo el correcto; lo que no sirve es tomar VVP-2 como su ejemplo limpio.
