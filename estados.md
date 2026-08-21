# Estados de avance · ViveProp Operaciones

Registro del avance en la ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Decisiones tomadas durante la ejecución: [decisiones.md](decisiones.md). Diseño del esquema: [diseno_modelo_datos.md](diseno_modelo_datos.md).

**Última actualización:** 2026-08-21 (11 sprints listos; **camino crítico cerrado**)

---

## Resumen

| | Cantidad |
|---|---|
| Sprints del plan | 22 |
| Listos | 11 |
| En curso | 0 |
| Pendientes | 11 |
| Bloqueados | 0 |

**Sprint actual:** ninguno. Once sprints listos y **el camino crítico está cerrado**: negocios queda registrable, gestionable e informable. Lo que sigue son bloques independientes: carga masiva (14–15), reportería avanzada (16–18), gestión de canjes (19–21) y contraseñas (22). También queda el sprint 5, con fecha límite el 9 de septiembre.

---

## Avance en porcentaje

Cuenta sprints, no esfuerzo: el sprint 7 (motor de comisiones) pesa mucho más que
el 3 (cargar la tabla de UF). Sirve como avance de hitos, no de horas.

| Lectura | Listos | Total | % |
|---|---:|---:|---:|
| **Camino crítico** (1, 3–13) | 12 | 12 | **100%** |
| Plan completo | 11 | 22 | 50,0% |
| Proyecto entero (incluye los 9 sprints previos en producción) | 20 | 31 | 65% |

| Serie | Listos | Total | % | Sprints |
|---|---:|---:|---:|---|
| **C** · Cimientos | 3 | 4 | 75% | 1, 3, 4, 5 |
| **G** · Acceso y despliegue | 0 | 2 | 0% | 2, 22 |
| **D** · Negocios | 6 | 6 | **100%** | 6–11 |
| **F** · Reportería | 2 | 5 | 40% | 12, 13, 16–18 |
| **E** · Carga masiva | 0 | 2 | 0% | 14, 15 |
| **B** · Gestión de canjes | 0 | 3 | 0% | 19–21 |

**Los dos hitos visibles están alcanzados** y el camino crítico cerrado, en el orden aprobado el 2026-08-21. Entre el 2 y el 8 no hay cambios visibles en la app.

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
| 6 | D1 · Esquema de negocios | **Listo** | 2026-08-21 | — | 4 tablas, 13 tests. Migración reversible verificada. |
| 7 | D2 · Motor de comisiones | **Listo** | 2026-08-21 | — | 34 tests. 18 de 19 históricos al peso; VVP-2 descuadrado en el origen (`D-026`). |
| 8 | D3 · CRUD backend | **Listo** | 2026-08-21 | — | 5 endpoints, 18 tests. Verificado punta a punta contra `dev`. |
| 9 | D4 · Pantalla Negocios | **Listo** | 2026-08-21 | — | Listado, ficha y alta. **Primer hito visible.** |
| 10 | D5 · Carga de los 19 históricos | **Listo** | 2026-08-21 | — | 18 negocios, 19 hitos, 13 propiedades, 114 obligaciones. Una sola diferencia: VVP-2. |
| 11 | D6 · Pipeline de negocios | **Listo** | 2026-08-21 | — | 10 tipos, línea de tiempo en la ficha. `etapa` movida al negocio (`D-027`). |
| 12 | F1 · Base de cálculo | **Listo** | 2026-08-21 | — | Tres buckets separados por construcción. 13 tests. |
| 13 | F2 · Dashboard de negocios | **Listo** | 2026-08-21 | — | Paleta validada con script (`D-028`). **Segundo hito visible.** |
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

### 2026-08-21 · Sprint 13 (F2) — Listo · camino crítico cerrado

**El dashboard de negocios funciona**, consumiendo el resumen del sprint 12. Con esto el camino crítico está completo: negocios queda registrable, gestionable e informable.

**Qué muestra:**

- Tres tiles para los tres buckets, cada uno con etiqueta y número, así que la identidad nunca depende solo del color. El rebate va como leyenda dentro del tile que le corresponde, porque es parte de esa comisión real.
- Gráfico mensual de **una sola serie**: comisión real VP por mes de cierre. Sin leyenda, porque el título dice qué se mide. La comisión total va al tooltip, y abajo la misma información como tabla.
- Barras horizontales por alianza, por modelo y del pipeline por etapa, con el monto como etiqueta directa en cada fila.
- Aviso si hay liquidaciones sin valorizar.
- Una nota al pie que recuerda por qué el potencial no concretado se conserva y por qué no se suma con lo ganado.

**La paleta se validó con un script** (`D-028`), sobre las rampas de `theme.ts`. Encontró tres cosas que no se habrían visto a ojo:

1. `brand-3` `#adade1` **no sirve como color de dato**: falla el piso de croma y se lee como gris. Los tonos claros de esa rampa se hicieron para fondos.
2. **El modo oscuro no puede ser un volteo del claro.** Ningún par de la rampa pasa contra la superficie oscura, así que el paso oscuro se eligió y validó aparte.
3. **La tríada verde / teal / rojo era casi ilegible**: verde y teal a **ΔE 2,8 en tritanopía**. Con el indigo de marca en lugar del teal, el peor caso sube a **18,8**.

**Eso cambió la forma del gráfico, para mejor.** Iba a tener dos series —total y real VP— pero ningún par pasaba en oscuro. Al revisarlo quedó claro que el trabajo de ese gráfico es una sola medida en el tiempo; la comisión total es contexto, no una serie de igual peso.

**Componente nuevo:** `BarrasMontos.tsx`, porque el `BarList` existente cuenta unidades y no pesos, y no valía la pena tocar el que usa el dashboard de canjes.

**Lo que no pude verificar:** no tengo credenciales para entrar a la app, así que **no revisé el resultado renderizado**. La guía de visualización pide mirarlo por colisiones de etiquetas, geometría y desbordes. Typecheck, lint y build están limpios, y los datos que consume están verificados, pero el aspecto visual lo tiene que mirar Felipe.

**Nota operativa:** el reloader de uvicorn se quedó pegado y estuvo sirviendo código de dos sprints antes durante un rato. Al matarlo quedó un socket huérfano en el puerto 8000 sostenido por un proceso hijo que `Get-Process` no mapeaba; hubo que buscarlo por línea de comando. Vale saberlo si vuelve a pasar.

### 2026-08-21 · Sprint 12 (F1) — Listo

**La base de cálculo de la reportería está lista** y da exactamente los números verificados en la auditoría inicial: **8.087.862 ganado, 1.824.272 en pipeline, 4.751.491 de comisión potencial no concretada.**

`app/services/reportes_negocios.py` más `GET /api/negocios/reportes/resumen`. Es la capa que van a consumir los sprints 13 a 18.

**La propiedad que define el sprint:** los tres buckets están separados de forma **estructural**, no como un filtro que alguien recuerde aplicar. Y **no existe un campo que los sume** — hay un test que lo verifica, `test_no_existe_un_campo_que_los_sume`. Sumar ganado, pipeline y perdido da un número que no significa nada; si alguien lo quiere, lo suma a mano y sabe lo que está haciendo.

**Decisiones del cálculo:**

- `DESISTIDO` va con lo perdido: no entró.
- **Los negocios se cuentan sin duplicar.** Un negocio con dos hitos ganados es un negocio, no dos. Los hitos sí se cuentan por separado.
- El corte por mes usa **`fecha_cierre`**, no la de inicio: lo que importa es cuándo entró la plata. Un hito cerrado sin fecha cae en "Sin fecha" en vez de desaparecer del gráfico.
- Los desgloses por alianza y modelo van **solo sobre lo ganado**. El pipeline se mira por etapa, que es donde está detenido cada negocio.
- **Los hitos sin valorizar se cuentan aparte.** Cuentan como hitos del pipeline pero no aportan plata, porque todavía no tienen base. Hoy son cero, pero el modelo lo permite y el dashboard no debería hacerlos desaparecer.
- El rebate del concentrador va por bucket: los 317.153 del pipeline no están en lo ganado.

**La normalización a CLP ya estaba resuelta** al guardar, en el sprint 8: las columnas `comision_*` son `numeric(16,2)` en pesos, calculadas con la UF congelada del hito. Acá no se convierte nada, solo se agrupa.

**Dos notas técnicas:**

1. El agrupamiento por mes se hace en Python y no con `to_char`, que es exclusivo de Postgres y dejaría este cálculo sin poder testearse contra la base en memoria. Con este volumen la diferencia es irrelevante, y tener el número verificado vale más que ahorrar una vuelta. Ojo: `reportes_canjes.py` sí usa `to_char` y por eso esa parte no tiene test.
2. Un defecto encontrado al verificar: el corte por modelo mostraba `ModeloNegocio.MERCADO_PRIMARIO`, el repr de Python del enum, en vez de su valor. Corregido con un test.

**117 tests pasando** más 1 xfail.

### 2026-08-21 · Sprint 11 (D6) — Listo · serie D completa

**El pipeline de negocios funciona**, reusando la tabla `movimientos` que ya servía a canjes. 10 tipos sembrados con prefijo `NEG_` (`D-014`), verificado: cero colisiones con los 14 de canjes.

**Hubo que resolver una tensión de diseño primero (`D-027`).** `D-020` decía que el pipeline es del negocio y por eso `movimientos` apunta ahí, pero `etapa` había quedado en el hito porque así estaba en el Excel. Un movimiento que apunta al negocio no tenía a qué hito aplicarle la etapa resultante.

Se movió `etapa` a `negocios`, y se verificó primero que fuera sin pérdida: **ninguno de los 18 negocios tiene hitos con etapas distintas** — VVP-3 tiene sus dos en E7, el mismo valor repetido, que es la firma de un campo que pertenece al padre. `estado` **no** se movió: que la promesa cierre y la escritura se caiga es un escenario real.

**Comportamiento de los tipos:**

- Los 7 pasos E1–E7 mueven la etapa del negocio.
- `NEG_PERDIDA` y `NEG_DESISTIMIENTO` cambian el estado **solo de las liquidaciones abiertas**. Una promesa ya cerrada no se vuelve perdida porque la escritura se cayó.
- `NEG_COMENTARIO` no mueve nada, solo queda en el historial.

**En la interfaz:** la ficha del negocio muestra el recorrido E1–E7 con la etapa actual marcada, la línea de tiempo de movimientos con su autor y fecha, y el control para registrar un avance con comentario. El listado suma una columna de etapa.

**Verificado contra `dev`** con VVP-17: E4 → E5 registrado con autor y fecha, y revertido después.

**Dos defectos encontrados y corregidos:**

1. **Orden de rutas.** `GET /api/negocios/tipos-movimiento` quedaba después de `/{negocio_id}` en el registro, y FastAPI resuelve por orden: `tipos-movimiento` se interpretaba como un id y devolvía un error de validación. Se movió arriba, con un comentario que explica por qué tiene que quedar ahí.
2. **404 en vez de 400.** Un movimiento sobre un negocio inexistente devolvía 400 porque el servicio lanzaba su propio error. Un recurso que no está es un 404.

**Infraestructura de test:** se agregó `usuarios` a la base de test —`movimientos.autor_id` la referencia— y el usuario de prueba ahora se persiste en vez de existir solo en memoria.

**104 tests pasando** más 1 xfail. Migración `e5b73c19af42` verificada reversible.

### 2026-08-21 · Sprint 9 (D4) — Listo · primer hito visible

**La pantalla de Negocios funciona con los 18 negocios reales.** El total del listado da 14.663.624 de comisión real VP, el mismo número que se calculó del Excel en la auditoría inicial.

Tres archivos nuevos en el front, más el cliente de API: `pages/Negocios.tsx` (listado), `components/NegocioFichaModal.tsx` (ficha), `components/NegocioFormModal.tsx` (alta) y `components/negociosFormato.ts` (formato de moneda, UF, porcentajes y fechas en un solo lugar).

**El listado** filtra por código, modelo, estado y alianza, con fila de totales al pie sumando los hitos. Los negocios con más de un hito lo dicen con una insignia — hoy solo VVP-3.

**La ficha muestra el desglose en cascada**: comisión total del negocio, corredor aliado, ViveProp bruta, y las restas de tercero y equipo hasta la comisión real. El rebate del concentrador va en verde porque suma en vez de restar, que es lo que hace que la comisión real pueda superar el total.

**Dos cosas que la ficha hace explícitas en vez de esconder:**

1. Si el hito usa valor ingresado a mano, dice sobre qué monto se calculó, cuál era el calculado y por qué se cambió.
2. Si la comisión total no cuadra con su reparto, aparece una alerta con el descuadre. **VVP-2 la va a mostrar**, con sus 903.803. Mostrar números que no suman sin decir nada habría sido peor que no mostrarlos.

**El formulario se adapta al modelo**: pide el lado vendedor en Primario, el comprador en Concentradores, los dos en Agencia. No muestra campos que ese modelo ignora — que es exactamente de donde salieron tres lecturas equivocadas durante el análisis. Los porcentajes se ingresan como número (2 = 2%) y se convierten a fracción al enviar.

Mientras se escribe la dirección, ofrece las propiedades parecidas, porque la clave única no agrupa `Av. Fernández Albano 492` con `Fernández Albano 492`.

**Un hueco del backend encontrado al construir el consumidor:** `/api/catalogos` no devolvía el `id` de cada ítem, pero los negocios referencian catálogos por id, así que el formulario no podía traducir la alianza elegida a `alianza_id`. Se agregó, con dos tests. Los grupos que salen de un enum siguen sin id, porque no son filas de tabla.

**95 tests pasando** más 1 xfail. Typecheck, lint y build del frontend limpios.

**Nota operativa:** el backend local quedó corriendo con `--reload`. El proceso anterior tenía el código de hace varios sprints y no habría servido los endpoints nuevos.

### 2026-08-21 · Sprint 10 (D5) — Listo

**Los datos reales están en `dev`**: 18 negocios, 19 hitos, 13 propiedades y 114 obligaciones. El padre `VVP-3` se creó en la carga, porque no existe como fila en el Excel; sus dos hitos quedaron como PROMESA y ESCRITURA.

**El cargador migra fiel, no recalcula.** Los montos que quedan en la base son los del Excel. Recalcular habría cambiado en silencio los números de siete negocios cerrados con plata ya facturada. El motor se ejecuta igual, pero solo para comparar, y la carga imprime un informe con cada diferencia: así se autoverifica en vez de pedir fe.

**Resultado: una sola diferencia en los 19 negocios.** El `comision_total` de VVP-2, exactamente los 903.802,93 conocidos. Los otros 132 montos reproducen el Excel al peso.

Eso **precisa `D-026`**: el ajuste de VVP-2 no fue un cambio de base. Broker, VP bruta, equipo y real VP son todos consistentes con la base calculada de 104.100.248,32. Se bajó únicamente el total.

**Verificado contra los números conocidos del análisis inicial:**

| | Hitos | Comisión real VP |
|---|---:|---:|
| Ganado | 7 | 8.087.862 |
| Pipeline | 2 | 1.824.272 |
| Potencial perdido | 10 | 4.751.491 |
| Rebate de concentrador | | 523.674 |

**La UF se preserva de la columna AB** en vez de buscarla en la serie. La de VVP-3 PROMESA (39.707,30) no corresponde a ninguna fecha, así que recalcularla habría cambiado su valorización.

**El patrón de reintentos quedó visible**, que era el punto de tener tabla `propiedades`:

- `Mario Kreutzberger 1520 u.316-A` — **3 intentos**: VVP-4 perdido, VVP-13 perdido, VVP-16 **cerrado**
- `San Diego 1473 u.513` — 2: VVP-9 perdido, VVP-15 activo
- `Diag. Sta. Elena 2605 u.110` — 2, ambos perdidos
- `Av. Sta. Rosa 5741 u.1309-A` — 2, ambos perdidos

En el Excel eso no se podía ver.

### 2026-08-21 · Sprint 8 (D3) — Listo

**Cinco endpoints** de negocios más la búsqueda de propiedades: listar con filtros, obtener con sus hitos, crear, editar, y agregar o editar un hito. `gerencia` solo lee; escribir exige `operaciones`.

**La capa de servicio es lo que importa.** `app/services/negocios.py` deja el orden de guardado en un solo lugar: congelar la UF de la fecha de referencia, resolver la base con el manual ganándole al calculado, aplicar la fórmula del modelo, persistir los siete montos. Ahí se juntan los sprints 3, 6 y 7.

**Verificado punta a punta contra `dev`** con los números reales de VVP-4, no solo en tests: 39.735,63 de UF congelada, 42.914.480,40 de base y 858.289,61 de comisión total, todos exactos. El negocio de prueba se borró después.

**Decisiones de implementación:**

- Un hito sin valorizar deja los montos en **nulo**, no en cero. "Sin valorizar" y "valorizado en cero" son cosas distintas y el dashboard del sprint 13 necesita poder distinguirlas.
- Si falta la UF de la fecha, el error dice qué fecha, qué rango cubre la serie y que hay que cargar el nuevo tramo. Es el mismo hueco que cierra el sprint 5.
- La propiedad se reusa si ya existe con esa dirección, unidad y comuna. Sin eso, cada reintento sobre la misma unidad crearía una propiedad nueva y el patrón que la tabla existe para mostrar quedaría invisible igual que en el Excel.
- `GET /api/negocios/propiedades?q=` para que el alta del sprint 9 ofrezca las parecidas antes de crear un duplicado — la clave única no alcanza cuando la misma dirección está escrita de dos formas.
- Cambiar el modelo de un negocio recalcula las comisiones de todos sus hitos, porque la fórmula depende del modelo.

**18 tests nuevos, 93 en la suite** más 1 xfail.

**Dos arreglos de calidad:**

1. Un `SAWarning` señalaba un orden frágil: se hacían consultas —la UF, la etapa, los catálogos— mientras el negocio todavía no estaba en la sesión, así que la cascada desde `Propiedad.negocios` no lo alcanzaba. Se agrega el negocio a la sesión antes de aplicar los hitos.
2. **Los avisos de SQLAlchemy ahora rompen los tests** (`filterwarnings` en `pytest.ini`). Casi siempre marcan un problema real de orden o de sesión, y en el resumen pasan desapercibidos.

### 2026-08-21 · Sprint 7 (D2) — Listo

**Motor puro** en `app/services/comisiones.py`: no toca la base de datos, recibe modelo, estado, base y tasas, y devuelve los siete montos sin redondear. El redondeo queda como decisión de quien persiste o muestra.

**Los tests se escribieron antes del motor**, y eso pagó tres veces.

**El fixture se generó desde el Excel, no a mano.** `tests/datos_historicos.py` tiene los 19 casos con sus entradas y sus montos esperados. Se generó por script porque transcribir a mano es exactamente lo que había fallado antes, y porque el `.xlsx` está en `.gitignore`: estos son los únicos datos históricos versionados.

**34 tests: los 19 de regresión, los 3 de `REGLAS CALCULO`, y 12 de reglas aisladas.** Total de la suite: 75 pasando y 1 xfail.

**Tres hallazgos, todos antes de que existiera el motor:**

1. **El porcentaje del equipo se aplica después de sacar al tercero** (`D-025`), no sobre la VP Bruta completa como dice `REGLAS CALCULO`. Son 7.252 pesos en VVP-3 PROMESA.
2. **Cada modelo lee un lado; no se pueden sumar** (`D-025`). La planilla puebla `% VP Vendedor` con 0,008 en las 13 filas de Concentradores sin usarlo, así que sumar duplicaba la VP Bruta en 11 de los 19 casos.
3. **VVP-2 está descuadrado en el origen** (`D-026`): la Comisión Total se bajó a mano por el ajuste de crédito y el reparto siguió sobre la base original, dejando Broker + VP Bruta 903.803 por encima del total. Queda como xfail estricto con su motivo, más un test dedicado que deja constancia del monto. Hay que resolverlo en el sprint 10.

**Renombre de las tasas** (`D-024`): `pct_comision_concentrador` y `pct_comision_negocio` pasaron a `pct_lado_vendedor` y `pct_lado_comprador`, porque los primeros mienten en Mercado Primario. La migración `d3a91f6c25b8` se editó en su lugar, sin agregar una migración de renombre encima, porque no estaba pusheada.

### 2026-08-21 · Sprint 6 (D1) — Listo

**Cuatro tablas nuevas**, migración `d3a91f6c25b8` aplicada a `dev` y verificada reversible: `propiedades` (7 columnas), `negocios` (13), `negocio_hitos` (35) y `negocio_obligaciones` (6). Tres enums de Postgres creados —`modelo_negocio`, `estado_negocio`, `tipo_obligacion`— y `moneda_tipo` reutilizado desde canjes con `create_type=False` para no intentar recrearlo.

**Índices** según `D0`: `codigo` único en negocios, `(modelo, alianza_id)` para el dashboard, `negocio_id`, `(estado, fecha_cierre)` para los tres buckets del sprint 12, y `fecha_cierre` para las series mensuales.

**Decisión de precisión:** las tasas van en `numeric(16,14)`. El histórico trae valores despejados a mano como `0.0252001208200461`, y truncarlos haría que las comisiones no cuadren al peso contra el Excel, que es el criterio del sprint 7.

**Refinamiento respecto de `D0`:** las referencias a catálogos se implementaron como claves foráneas (`estado_id`, `tipo_propiedad_id`, `estado_propiedad_id`, `motivo_perdida_id`) en vez del `varchar` que proponía el documento. Mismo diseño, con integridad referencial real, y consistente con `alianza_id`.

**Tests: 13 nuevos, total 42 pasando.** El que da sentido al sprint es `test_sumar_hitos_no_duplica_el_negocio`: verifica sobre la estructura real, con los números de VVP-3, que sumar comisiones es sumar hitos y que no hay una tercera fila que haya que recordar excluir. Eso era el propósito de `D-002` y `D-020`.

También quedan cubiertos: el orden cronológico de los hitos, que un negocio simple es un negocio con un hito de nombre nulo, la unicidad de `codigo` y de la propiedad, el patrón de reintento con tres negocios sobre la misma unidad, una obligación por tipo y por hito, el borrado en cascada, y la base de comisión de `D-017` con el manual ganándole al calculado usando los números reales de VVP-2.

**Infraestructura de test:** se activaron las claves foráneas en SQLite con `PRAGMA foreign_keys=ON`. Sin eso SQLite las ignora, y los tests de integridad referencial habrían pasado sin probar nada.

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
