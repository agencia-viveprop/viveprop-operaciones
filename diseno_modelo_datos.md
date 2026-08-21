# D0 · Diseño del modelo de datos

> **Este documento existe para ser corregido antes de que se escriba una migración.**
> Cubre los sprints 4 (catálogos) y 6 (esquema de negocios). No hay código asociado.

**Última actualización:** 2026-08-21 · Relacionados: [plan_desarrollo.md](plan_desarrollo.md) · [decisiones.md](decisiones.md) · [estados.md](estados.md)

---

## Por qué existe

`D-017` cambió tres campos del modelo, la fuente de la base de comisión y el diseño de 19 tests. Apareció a tiempo porque estábamos conversando el diseño en vez de construyéndolo. Este documento busca que el resto de esas correcciones aparezcan ahora y no después de una migración.

**Las seis preguntas quedaron resueltas el 2026-08-21.** Este documento pasa de propuesta a especificación aprobada: es lo que se implementa en los sprints 4 y 6.

---

## 1 · Catálogos (sprint 4)

`CONFIG` define seis listas: alianzas (8), modelos de negocio (3), etapas E1–E7 con responsable, estados de facturación (12), tipos de propiedad y tipos de operación.

### Opción A — Una tabla genérica *(aprobada, D-021)*

```
catalogos
  id         int PK
  tipo       varchar(40)    'alianza' | 'estado_facturacion' | 'tipo_propiedad' | ...
  codigo     varchar(40)
  nombre     varchar(120)
  orden      int null
  activo     bool default true
  metadatos  jsonb null     lo propio de cada tipo
  UNIQUE (tipo, codigo)
```

**A favor:** un mantenedor sirve para todos; agregar un catálogo nuevo no requiere migración; un endpoint `/api/catalogos?tipo=alianza` cubre todo.

**En contra:** sin claves foráneas por tipo, nada a nivel de base impide que un negocio apunte a un catálogo del tipo equivocado. Y `metadatos` en `jsonb` esconde estructura: el responsable de una etapa y el modelo asociado a una alianza quedan sin tipo.

### Opción B — Una tabla por catálogo

Seis tablas chicas con claves foráneas reales. A favor: integridad referencial de verdad y columnas tipadas. En contra: seis migraciones, seis endpoints y seis mantenedores para listas de 3 a 12 filas que casi no cambian.

### Recomendación

**Opción A, con dos excepciones.**

Los cuatro catálogos que son listas planas — alianzas, estados de facturación, tipos de propiedad, tipos de operación — van a la tabla genérica.

**`etapas` va como tabla propia**, porque tiene estructura real (código, nombre, responsable, orden) y la consulta el motor de pipeline, no solo un desplegable.

**`modelo_negocio` no va a catálogo: va como enum.** Son tres, y cada uno tiene una fórmula de comisión distinta escrita en código. Si alguien agrega un cuarto modelo desde un mantenedor, el motor no sabría calcularlo. Un enum obliga a que agregar un modelo sea un cambio de código, que es lo correcto.

---

## 2 · Propiedades

Hay 5 unidades que aparecen en más de un negocio. `Mario Kreutzberger 1520 u.316-A` tomó tres intentos: VVP-4 perdido, VVP-13 perdido, VVP-16 cerrado. Hoy eso es invisible.

```
propiedades
  id                int PK
  direccion         text          not null
  unidad            varchar(40)   null
  comuna            varchar(120)  not null
  tipo_propiedad    varchar(40)   not null
  estado_propiedad  varchar(20)   not null    'Nuevo' | 'Usado'
  creado_en         timestamptz
  UNIQUE (direccion, unidad, comuna)
```

**Ojo con la clave única.** En los datos reales la misma unidad aparece escrita distinto: `Av. Fernández Albano 492` contra `Fernández Albano 492`, y `1207-B` contra `Dpto 1207 torre B`. Una restricción sobre texto libre no va a agrupar esos casos. Propuesta: la restricción se queda como red mínima, y en el alta la interfaz ofrece propiedades parecidas en vez de confiar en la base.

---

## 3 · Negocios y sus hitos

`D-002` cerró que hay padre e hijos. Cómo se implementa quedó abierto, y son dos formas con consecuencias distintas.

### Opción A — Autorreferencia en una tabla

Una sola tabla `negocios` con `padre_id` nullable apuntando a sí misma. Es lo que asumió `D-013`.

**En contra:** la mitad de las columnas quedan sin sentido según el rol. Un padre no tiene comisión; un hijo no tiene alianza propia. Nada en la base impide llenar las dos. Y toda consulta de reportería tiene que recordar filtrar por hojas para no doblar montos.

### Opción B — Dos tablas *(aprobada, D-020)*

```
negocios                            negocio_hitos
  id             int PK               id           int PK
  codigo         varchar(40) UQ       negocio_id   int FK
  propiedad_id   int FK               nombre       varchar(60) null
  modelo         enum                 fecha_inicio date
  alianza_id     int FK               fecha_cierre date null
  contraparte_*  text                 estado       enum
  corredor       text                 etapa        varchar(4)
  notas          text                 ... valorización y comisiones
```

`nombre` del hito es `PROMESA`, `ESCRITURA`, o nulo cuando el negocio tiene uno solo.

**A favor:** cada columna vive donde tiene sentido y no hay estados imposibles. **Sumar comisiones es siempre sumar `negocio_hitos`**, sin filtros y sin riesgo de doble conteo — que era el objetivo de `D-002`. Los 17 negocios simples son un negocio con un hito, sin caso especial.

**En contra:** una tabla más, y hay que decidir a quién apunta `movimientos`.

### Recomendación

**Opción B.** El argumento decisivo: `D-002` se tomó para hacer imposible el doble conteo, y la autorreferencia no lo hace imposible, solo lo hace evitable si uno se acuerda del filtro.

Sobre `movimientos`: apunta al **negocio**, no al hito. El pipeline E1 a E7 es del negocio; el hito es una liquidación dentro de él. `D-013` sigue aplicando: `negocios.id` es entero y `codigo` va aparte con índice único.

**Modifica `D-013`**, que hablaba de `padre_id` autorreferencial. Ya actualizado: ver `D-020`.

---

## 4 · Valorización (D-017)

En `negocio_hitos`:

| Campo | Tipo | Nota |
|---|---|---|
| `valor_negocio` | `numeric(16,2)` | El monto como se acordó |
| `moneda` | enum UF / CLP | |
| `fecha_valorizacion` | `date null` | Si falta, se usa `fecha_inicio` |
| `uf_snapshot` | `numeric(12,2) null` | UF congelada. Nulo si la moneda es CLP |
| `valor_clp_calculado` | `numeric(16,2)` | `valor_negocio` × `uf_snapshot` |
| `valor_clp_manual` | `numeric(16,2) null` | **Cuando existe, manda** |
| `motivo_valor_manual` | `text null` | Opcional, no obligatorio |

**Base de comisión** = `COALESCE(valor_clp_manual, valor_clp_calculado)`. El motor trabaja siempre sobre ella.

Va en el **hito**, no en el negocio: VVP-3 PROMESA y VVP-3 ESCRITURA tienen bases distintas, 241,7M y 242,2M.

---

## 5 · Comisiones

Por `D-005` van tasas y montos por separado. Las tasas son entrada; los montos se calculan al guardar y se persisten.

**Tasas** (entrada, con los nombres propuestos más abajo): `pct_comision_vendedor`, `pct_comision_comprador`, `pct_rebate_concentrador`, `pct_broker_vendedor`, `pct_broker_comprador`, `pct_vp_vendedor`, `pct_vp_comprador`, `pct_equipo`, `pct_tercero`, `nombre_tercero`.

**Montos calculados:** `comision_total`, `comision_broker`, `rebate_concentrador`, `comision_vp_bruta`, `comision_equipo`, `comision_tercero`, `comision_real_vp`.

### Lo que quedó verificado sobre los datos

La Comisión Total depende del modelo, y **cada modelo lee columnas distintas**:

| Modelo | Comisión Total |
|---|---|
| Mercado Primario | base × `% com vendedor` (AD) |
| Secundario Concentradores | base × `% com comprador` (AE) — **AD no participa**, es la tasa del concentrador |
| Secundario Agencia | base × (`% com vendedor` + `% com comprador`), que en arriendo es 50% + 50% |

Verificado en **18 de las 19 filas**. La única excepción es VVP-2, que usa base externa (`D-017`).

- **El rebate del concentrador es `base × AD × 12%`**, no 12% de la Comisión Total. AD es lo que el concentrador le cobra al vendedor, y comparte el 12% de eso. Calza al peso en los 3 negocios cerrados; en los 10 perdidos la tasa está y el monto es 0, que es correcto.
- **El rebate no entra en la Comisión Total**; se suma al final a Real VP. Por eso Real VP puede superar el total.
- `pct_equipo` es 0,10 en las 19 filas, pero va editable (ver más abajo).

### La fórmula de Concentradores, resuelta el 2026-08-21

**Los nombres de las columnas engañan**, y eso era lo que trababa el sprint 7. Lo que la planilla realmente hace:

| Columna | Nombre en el Excel | Lo que es |
|---|---|---|
| AD | *% Comisión Vendedor* | La tasa que **el concentrador** le cobra al vendedor. No es ingreso ViveProp. |
| AE | *% Comisión Comprador* | La comisión real del negocio: lo que paga el comprador. |
| AI | *% Broker Comprador* | La parte de AE que va al corredor aliado. |
| AK | *% VP Comprador* | La parte de AE que va a ViveProp. |
| AG | *% Comisión Agencia Concentrador* | 12%: la tajada de su propia comisión que el concentrador comparte. |

Se cumple la identidad **AI + AK = AE** en las 13 filas.

```
Comision Total = base x AE
  Broker       = base x AI
  VP Bruta     = base x AK
    Equipo     = VP Bruta x pct_equipo
    Real VP    = VP Bruta - Equipo - Tercero + Rebate
Rebate         = base x AD x AG      solo si el negocio cierra
```

Verificado al peso en las 13 filas para total, broker, VP bruta y la identidad. El rebate cuadra en los 3 negocios que cerraron; en los 10 perdidos la tasa está registrada y el monto es 0, que es el comportamiento correcto.

**Nombres propuestos para el modelo**, porque los del Excel inducen al error:

| Excel | Modelo |
|---|---|
| `% Comisión Vendedor` (AD) | `pct_comision_concentrador` |
| `% Comisión Comprador` (AE) | `pct_comision_negocio` |
| `% Broker Comprador` (AI) | `pct_broker` |
| `% VP Comprador` (AK) | `pct_vp` |

**Confirmado por Felipe:** el rebate del 12% se calcula sobre `base × AD`, la comisión que el concentrador le cobra al vendedor.

**Corrección:** este documento reportaba antes que la Comisión Broker de VVP-4 salía de 0,008. Sale de 0,012, que es exactamente `% broker comprador`. La lectura anterior era un error.

### pct_equipo

Es 10% en las 19 filas, contra los 30–40% de los ejemplos de `REGLAS CALCULO`. **Manda la práctica: 10%.** Pero va como campo editable por hito, no como constante, porque debe poder cambiar a futuro.

---

## 6 · Obligaciones de facturación y pago

Seis columnas del Excel con los mismos 12 estados posibles. Como tabla hija:

```
negocio_obligaciones
  id       int PK
  hito_id  int FK
  tipo     enum      PAGO_PARTNER_COMERCIAL | FACT_CORREDOR_VP |
                     FACT_CAPTADOR_ALIANZA | PAGO_EQUIPO_VP |
                     FACT_COMISION_TOTAL | PAGO_COMISION_REAL_VP
  estado   varchar(40)
  monto    numeric(16,2) null
  fecha    date null
  UNIQUE (hito_id, tipo)
```

Van en el hito, no en el negocio: cada liquidación se factura y se paga por separado.

En los datos, `No Aplica - Negocio Caído` aparece en los 10 perdidos y en las 6 columnas. Eso sugiere que el estado se podría derivar del estado del negocio en vez de guardarse — pero lo dejo explícito, porque un negocio puede caerse **después** de que algo ya se facturó, y ahí la derivación mentiría.

---

## 7 · Índices propuestos

| Tabla | Índice | Para |
|---|---|---|
| `negocios` | `codigo` UNIQUE | Búsqueda por `VVP-N` |
| `negocios` | `(modelo, alianza_id)` | Dashboard por modelo y alianza |
| `negocio_hitos` | `negocio_id` | Traer los hitos de un negocio |
| `negocio_hitos` | `(estado, fecha_cierre)` | Los tres buckets del sprint 12 |
| `negocio_hitos` | `fecha_cierre` | Series mensuales de los sprints 13 y 17 |
| `propiedades` | `(direccion, unidad, comuna)` UNIQUE | Detección de reintentos |
| `negocio_obligaciones` | `(hito_id, tipo)` UNIQUE | Una obligación por tipo |

---

## Preguntas abiertas

| # | Pregunta | Estado |
|---|---|---|
| 1 | ¿Cómo se reparte la comisión en Assetplan? | **Cerrada.** Fórmula en `D-018`, confirmada por Felipe |
| 2 | ¿Catálogos en tabla genérica, `etapas` aparte, `modelo_negocio` como enum? | **Aprobada** — `D-021` |
| 3 | ¿Dos tablas en vez de autorreferencia? | **Aprobada** — `D-020`, modifica `D-013` |
| 4 | ¿`motivo_valor_manual` obligatorio? | **Cerrada: no** — `D-019` |
| 5 | ¿`pct_equipo` manda la práctica? | **Cerrada: 10%**, editable por hito — `D-019` |
| 6 | VVP-16: ¿cobro parcial o error? | **Cerrada: ninguno.** Su tasa de concentrador es 4% en vez de 2% |

**Tally:** 18 de las 19 filas siguen la regla. El único con base externa es VVP-2.

**No queda ninguna pregunta abierta.** Los sprints 4 y 6 se pueden implementar contra esta especificación.
