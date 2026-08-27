# Estados de avance · ViveProp Operaciones

Registro del avance en la ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Decisiones tomadas durante la ejecución: [decisiones.md](decisiones.md). Diseño del esquema: [diseno_modelo_datos.md](diseno_modelo_datos.md).

**Última actualización:** 2026-08-22 (22 listos + G2 en curso; auditoría cerrada: sus cuatro puntos arreglados y en producción)

---

## Resumen

| | Cantidad |
|---|---|
| Sprints del plan | 23 |
| Listos | 22 |
| En curso | 1 |
| Pendientes | 0 |
| Bloqueados | 0 |

**Sprint actual:** 2 (G2), en curso: el código está y falta solo el dominio propio, que necesita que agregues el registro DNS y que quedó fuera por ahora por decisión tuya.

**La auditoría del 22-08 quedó cerrada**, con sus cuatro puntos arreglados, verificados y en producción:

1. **La app no permitía cerrar un negocio** desde ninguna pantalla. Se construyó el formulario de liquidación, y al probarlo apareció que **guardar un negocio histórico le movía la comisión** — el hallazgo más grande. Reproducen su plata 18 de 19 hitos, contra 1 de 19 antes (`D-046`).
2. **Trece pantallas no contemplaban un error de la API**: spinner eterno o pantalla en blanco (`D-047`).
3. **Umbrales escritos a mano** en los textos, mientras el backend los decidía y ya los devolvía (`D-048`).
4. **El importador de canjes iba dos veces a la base por fila**: 84,50 s → 1,07 s, medido (`D-049`).

Lo que sigue esperando algo tuyo: qué quiere ver el directorio, con qué UF se valoriza un negocio abierto, qué base es la correcta en `VVP-2`, y el export de Dataprop con los canjes #364 y #367. Sin fechas límite ni bloqueos.

---

## Avance en porcentaje

Cuenta sprints, no esfuerzo: el sprint 7 (motor de comisiones) pesa mucho más que
el 3 (cargar la tabla de UF). Sirve como avance de hitos, no de horas.

| Lectura | Listos | Total | % |
|---|---:|---:|---:|
| **Camino crítico** (1, 3–13) | 12 | 12 | **100%** |
| Plan completo | 22 | 23 | 95,7% |
| Proyecto entero (incluye los 9 sprints previos en producción) | 31 | 32 | 96,9% |

| Serie | Listos | Total | % | Sprints |
|---|---:|---:|---:|---|
| **C** · Cimientos | 5 | 5 | **100%** | 1, 3, 4, 5, 23 |
| **G** · Acceso y despliegue | 1 | 2 | 50% | 2, 22 |
| **D** · Negocios | 6 | 6 | **100%** | 6–11 |
| **F** · Reportería | 3 | 5 | 60% | 12, 13, 16–18 |
| **E** · Carga masiva | 2 | 2 | **100%** | 14, 15 |
| **B** · Gestión de canjes | 3 | 3 | **100%** | 19–21 |

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
| 2 | G2 · Despliegue en Render | **En curso** | 2026-08-21 | — | Cookie segura por defecto, `<title>`, health check, 404 de API. Falta el dominio: depende de una acción del usuario. |
| 3 | C2 · Tabla UF y conversión | **Listo** | 2026-08-20 | — | 1.409 filas en `dev`. 12 tests. Reproduce la columna AC al peso. |
| 4 | C3 · Catálogos | **Listo** | 2026-08-21 | — | 10 tests. 27 filas sembradas, endpoint con 9 grupos. |
| 5 | C4 · Plantilla y carga manual de UF | **Listo** | 2026-08-21 | — | Plantilla con fechas prellenadas, carga idempotente, aviso y alerta. 24 tests. |
| 6 | D1 · Esquema de negocios | **Listo** | 2026-08-21 | — | 4 tablas, 13 tests. Migración reversible verificada. |
| 7 | D2 · Motor de comisiones | **Listo** | 2026-08-21 | — | 34 tests. 18 de 19 históricos al peso; VVP-2 descuadrado en el origen (`D-026`). |
| 8 | D3 · CRUD backend | **Listo** | 2026-08-21 | — | 5 endpoints, 18 tests. Verificado punta a punta contra `dev`. |
| 9 | D4 · Pantalla Negocios | **Listo** | 2026-08-21 | — | Listado, ficha y alta. **Primer hito visible.** |
| 10 | D5 · Carga de los 19 históricos | **Listo** | 2026-08-21 | — | 18 negocios, 19 hitos, 13 propiedades, 114 obligaciones. Una sola diferencia: VVP-2. |
| 11 | D6 · Pipeline de negocios | **Listo** | 2026-08-21 | — | 10 tipos, línea de tiempo en la ficha. `etapa` movida al negocio (`D-027`). |
| 12 | F1 · Base de cálculo | **Listo** | 2026-08-21 | — | Tres buckets separados por construcción. 13 tests. |
| 13 | F2 · Dashboard de negocios | **Listo** | 2026-08-21 | — | Paleta validada con script (`D-028`). **Segundo hito visible.** |
| 14 | E1 · Plantilla de negocios | **Listo** | 2026-08-21 | — | 32 columnas en grupos, hoja de instrucciones y códigos válidos leídos de la base. |
| 15 | E2 · Importador de negocios | **Listo** | 2026-08-21 | — | Una fila es un hito (`D-039`). Idempotente, y no escribe nada si hay un solo error. 32 tests. |
| 16 | F3 · Reporte semanal | **Listo** | 2026-08-21 | — | Los dos dominios. 30 tests. "Avanzó" es toda actividad (`D-031`); umbral como control (`D-032`). |
| 17 | F4 · Reporte mensual comparativo | **Listo** | 2026-08-21 | — | Contra el mes anterior y el mismo mes del año pasado. La variación contra cero es nula, no infinita (`D-041`). 25 tests. |
| 18 | F5 · Vista directorio | **Listo** | 2026-08-22 | — | Armada con supuestos explícitos (`D-044`), porque la definición no llegó. Proyección como rango con el `n` a la vista. 16 tests. |
| 19 | B5 · Registrar movimientos en canjes | **Listo** | 2026-08-21 | `30ea66a` | Ya funcionaba desde B3. Verificado, sin código nuevo. |
| 20 | B6 · Semáforo y bandeja diaria | **Listo** | 2026-08-21 | — | Cuatro niveles (`D-029`), 194 canjes en la bandeja. 22 tests. |
| 21 | B7 · Migrar el seguimiento histórico | **Listo** | 2026-08-21 | — | 384 movimientos en 112 canjes. La bandeja pasó a 146 + 48. |
| 22 | G1 · Recuperación de contraseña | **Listo** | 2026-08-21 | — | Reset por admin con cambio forzado. La guarda está en la API (`D-040`). 21 tests. |
| 23 | C5 · UF automática desde el SII | **Listo** | 2026-08-21 | — | Fuente verificada en 617 fechas (`D-036`). Tarea de fondo diaria (`D-037`). 27 tests. |

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

### 2026-08-27 - La insignia de etapa dice su nombre

Pediste el tooltip sobre el codigo de etapa del listado de Negocios. Esta, y tambien en «Que me toca hoy», que tenia la misma insignia pelada: con el globo en una pantalla y no en la otra hay que recordar donde funciona.

El nombre sale del catalogo de etapas --el listado ya lo consultaba para sus filtros, asi que no cuesta una peticion mas-- y no de una copia de los siete rotulos escrita en la pantalla, que es lo que se despega en cuanto alguien renombra una etapa. El codigo se queda a la vista: es lo que cabe en la columna y es como hablas del pipeline.

**Verificado:** typecheck, build y lint sin hallazgos, y una captura con el globo abierto: sobre el `E7` de VVP-1 dice «Terminado». Ver `D-077`.

### 2026-08-27 - El reporte semanal: una ventana, un renglon por negocio o canje

Los cuatro puntos que marcaste, mas dos cosas que aparecieron al hacerlos.

**El selector ahora manda en las cuatro casillas.** Habia dos controles de periodo: el navegador fijaba la semana y el 7/14/30 tocaba solo «Estancado». Ahora la ventana manda en todo y el umbral de estancado es su largo, asi que «Avanzo» y «Estancado» reparten la cartera abierta en vez de contar dos periodos distintos.

Las opciones pasaron a ser **1 / 2 / 4 semanas** calendario, como quedamos: un numero tiene que significar lo mismo el martes y el viernes, y las flechas recien sirven cuando el periodo tiene nombre. Donde decia «30 dias» dice «4 semanas», que son 28.

**Y encontre un defecto de paso:** «Estancado» se media contra hoy, asi que al navegar hacia atras las otras tres cifras cambiaban y esa se quedaba con el estancamiento de hoy. Ahora se mide al cierre de la ventana: el mismo canje sale con 13 dias en la ventana del 17 al 23 y con 17 en la del 24 al 30.

**Las listas traen un renglon por negocio o canje, con su ultima actualizacion.** Se fue el VVP-15 tres veces. La casilla pasa a contar entidades --si dijera 23 movimientos sobre una lista de doce renglones seria el mismo desajuste de la bandeja-- y los movimientos quedan en el pie y en una columna «Registros»: *15 · canjes con actividad · 86 registros*.

**Las cuatro listas dicen de que propiedad se habla:** direccion y comuna, mas alianza en negocios y tipo de operacion en canjes. Y «Quedo en» ya no dice `E4` sino `E4 · Coordinacion de firma`; en canjes va solo el nombre. Cuando el movimiento no movio la etapa dice «sigue en X», asi que la celda nunca queda muda -- antes salia «—» en fila sobre todo lo migrado del Excel.

**Dos que no pediste.** El comentario largo se recorta a una linea con el texto completo en el tooltip, porque con tres columnas mas la tabla ya no cabia. Y el vacio decia «Nada que mostrar aca» debajo de un «Estancado 2»: ahora dice en que casilla no hay nada y donde si hay.

**Y despues, sobre la misma columna.** Me marcaste que en canjes «Que paso» mostraba solo la categoria --ocho filas de «Respuesta Corredor»-- sin el texto de cada registro. El defecto era mio y estaba en el servicio: en canjes mandaba el nombre del tipo **y tiraba el comentario**, con el argumento de que el de los migrados viene vacio o con ruido. Cierto para los 605 del Excel y falso para todo lo que se registra en la app, que es justo lo que sale en una ventana reciente.

Ahora la API manda las dos piezas separadas y la pantalla las combina: la categoria en tinta normal y el comentario en gris detras, con el texto completo en el tooltip. Lo hice igual en negocios --ahi no faltaba nada, pero pasa a decir `Cambio de etapa · Vendedor aprobo instruccion…`-- para que las dos secciones respondan "que paso" de la misma forma. Si la categoria estorba en negocios, sacarla es una linea.

Sobre los movimientos viejos la celda va a decir «Comentario general · Migrado del Excel — fecha aproximada…», que es ruido. No lo filtro por texto: esconder filas porque coinciden con una cadena conocida es peor, y esas son de 2022 a 2025, asi que casi no caen en estas ventanas.

**Verificado:** 731 tests, `alembic check` limpio, build y lint sin hallazgos, y capturas de la pantalla con datos. **Con una limitacion:** el clasificador bloqueo el script que lee la credencial de produccion, asi que verifique contra `dev`, y `dev` no tiene ni un movimiento de negocios --los 50 estan solo en produccion--. La tabla de negocios la vi por el lado de estancados, que usa los mismos componentes. Cuando abras la pantalla, el ojo que falta es ese. Ver `D-076`.

### 2026-08-27 - El grafico con selector siempre muestra el total

Me pediste que en los graficos donde se elige que mostrar, el total se vea siempre. Aplicado, y encontre que el arreglo anterior estaba a medias.

**La cifra ya era correcta; la forma no.** El numero de arriba de cada barra ya salia del mes completo. Pero al apagar un segmento la barra se encogia **y el eje se re-escalaba**, asi que marzo se veia mas alto con un segmento que con los tres. El rotulo decia $2.386.289 sobre una barra del tamano de una de $1.067.027, y en un grafico la forma se lee antes que el texto.

**Ahora todos los segmentos se dibujan siempre.** El chip cambia el color, no la presencia: el que apagas queda en gris y sigue ocupando su lugar. El alto es siempre el total, el eje no se mueve y los meses siguen comparables. Seleccionar pasa a ser destacar en vez de restar.

**El gris lo elegi con el validador, no a ojo.** El candidato obvio (`#ced4da`) daba 1.46:1 contra la superficie -- no se veia como bloque. Quedaron `#868e96` en claro y `#909296` en oscuro, los dos sobre 3:1.

**Y la leyenda tuvo que seguir al relleno.** La primera version pintaba la barra en gris y dejaba el punto de la leyenda en su color original, que es romper la identidad justo donde se declara.

Vale como regla para lo que venga: cualquier grafico con seleccion de segmentos mantiene el total.

**Verificado:** 721 tests, build y lint sin hallazgos, y captura del reporte mensual contra produccion con un solo segmento elegido -- la barra conserva su alto de $2.386.289 y el eje no se movio. Ver `D-075`.

### 2026-08-27 - "Al dia" incluye los agendados

Tercera vuelta sobre el mismo panel, y la que lo deja bien.

Me marcaste que con "Al dia" en cero y "Agendados" en cinco, la pantalla da la impresion de que no hay canjes activos. Tenias razon: un canje agendado para el jueves y uno gestionado hace tres horas estan **al dia** en el unico sentido que le importa a esa pantalla -- no requieren atencion hoy.

**Ahora van juntos.** «Al dia» muestra **5** en canjes y **2** en negocios, y el desglose baja al pie. Se fue el recuadro de Agendados. Quedan seis que reparten exacto: 0+2+0+0+0+5 = 7, y 0x5+2 = 2.

**Sin la condicion que planteaste.** Lo habias puesto como "si no hay incidentes, entonces...". Lo aplique siempre: si el numero cambia de significado segun el contexto, deja de ser comparable con el de ayer y hay que reconstruir cual de las dos definiciones se esta viendo.

**Y tenias razon con el otro mensaje.** "0 gestionados hace menos de 24 h" se leia como desatencion siendo que la realidad era la opuesta. La regla que saque de eso: un pie que enumera lo que **no** hay se lee como un reproche; el mismo pie enumerando lo que hay se lee como informacion. Ahora dice solo lo que existe: "5 con seguimiento agendado". Y dice "dentro del plazo" en vez del numero de horas, porque el umbral lo manda la API.

**Verificado:** 721 tests, build y lint sin hallazgos, y capturas de las dos bandejas contra produccion. Ver `D-074`.

### 2026-08-27 - Los recuadros de la bandeja ahora reparten el total

Me marcaste que los dos paneles de «Que me toca hoy» no eran consistentes con la realidad. Tenias razon, y eran dos cosas distintas.

**Los seis recuadros no sumaban el total.** En canjes habia 7 abiertos y los recuadros sumaban 2; en negocios habia 2 y sumaban 0. El resto estaba en una linea de texto chica. Yo lo habia decidido asi con el argumento de que los agendados no requieren atencion -- cierto, pero la conclusion era mala: un tablero cuyos recuadros no reparten el universo obliga a leer la letra chica, y seis ceros al lado de "0 de 2 negocios" se lee como que no hay nada.

Ahora **«Agendados» es un recuadro mas** y los siete cuadran exacto. Va en gris y no en un color de estado, que es lo que dice "esto no es algo pendiente" sin sacarlo de la cuenta.

**Y el vacio afirmaba algo falso.** Con los dos negocios agendados, la pantalla decia «No hay negocios con liquidaciones abiertas» justo debajo del encabezado que decia "0 de 2 negocios con liquidaciones abiertas". Ahora distingue las dos causas: no hay nada abierto, o todo lo abierto esta agendado. Canjes tenia el mismo problema latente y se arreglo tambien.

Los dos defectos son consecuencia de haber agregado los agendados: esconder filas cambia lo que significan los conteos y los vacios que las rodean, y eso no se reviso al agregarlos. Ninguno lo detecta un test -- los numeros de la API son correctos -- y ninguno se ve en `dev`, donde no habia agendados.

**Verificado:** 721 tests, build y lint sin hallazgos, y capturas de las dos bandejas contra produccion. Ver `D-073`.

### 2026-08-27 - La comision de Dataprop y los plazos de canjes

Con las tasas que definiste, la cadena cierra completa. Esta en el **dashboard de canjes** y en la **mitad de canjes de la vista directorio**.

**Tres cifras, y no son el mismo numero en tres estados.** La **cobrada** sale del campo manual de los cerrados: cuando un canje cierra, la comision se negocia y se factura, asi que es un hecho que se registra -- eso fue tu aporte y es mejor que mi propuesta original. La **potencial** y la **no concretada** salen de la regla.

**El motor esta anclado a tus 7 canjes.** Los casos del test son los 7 activos reales con los montos que verificaste contra tu planilla, no numeros inventados: si alguien cambia una tasa o un tramo, esos siete dejan de dar.

**Cada caso usa la UF que le corresponde:** hoy para los abiertos, la del cierre para los cerrados, la de la solicitud para los cancelados. Y donde no hay UF para esa fecha, el canje se informa **no valorizado**, no como cero.

Ahi aparece algo: en produccion la serie de UF empieza el 01-01-2026, asi que **178 canjes de 2022 a 2025 no se pueden valorizar**. `dev` si tiene el historico. Deje `cargar_uf_historica` para traerlo del SII, verificado que sirve los anos pasados.

**Los plazos: 8 dias de mediana antes de caerse** (42 casos) y **17 dias** de mediana los que siguen abiertos (7 casos). Ninguna mide cuanto tarda en cerrar -- no hay un solo caso cerrado. Y 254 cancelados sin fecha de termino quedan afuera, dicho en pantalla.

**El campo se llama ahora "Comision Dataprop cobrada"**, columna incluida.

**Verificado:** 721 tests, `alembic check` limpio, build y lint sin hallazgos, y captura de la pantalla. Ver `D-072`.

### 2026-08-27 · Un canje ahora puede estar cerrado

Elegiste la opción A: un tercer estado. Hasta ahora un canje solo podía estar **Activo** o **Cancelado**, así que no había dónde registrar que se concretó — y sin eso, la comisión real que se cobra al cerrar no tiene cuándo llenarse.

**El estado ya está**, y con él dejan de existir dos parches que venían de no tenerlo:

- «Canjes cerrados» del reporte mensual daba **0 en los 46 meses** y no podía dar otra cosa: pedía etapa «Cierre» *y* fecha de cierre a la vez, y esa combinación no existe en ninguna fila.
- La vista directorio deducía los cerrados con «estado activo y etapa Cierre», que contaba como cierre justamente a los 31 que se cayeron.

**Ningún canje se reclasificó.** Los 31 con la etapa en «Cierre» siguen cancelados, porque eso es lo que son. La etapa dice hasta dónde llegó el proceso; el estado, en qué terminó.

**El gráfico de solicitudes pasa de dos segmentos a tres** — cerrados, activos, cancelados — y sigue cerrando exacto contra el total. El tercer color lo validé con el script de la guía en los dos modos, no a ojo.

Y el dashboard de canjes gana un tile de **Cerrados** con su tasa de cierre, calculada sobre los resueltos: los que siguen abiertos no cuentan ni a favor ni en contra.

**Verificado:** 698 tests, `alembic check` limpio, build y lint sin hallazgos. Ver `D-071`.

### 2026-08-27 · La moneda de «Valor propiedad» está invertida en 139 canjes

Pediste llenar «Valor negocio» desde «Valor propiedad» y calcular la comisión encima. Medí el campo de origen antes de escribir nada, y no se puede usar como está.

**139 de 297 canjes tienen la moneda al revés.** Un arriendo de casa en Vitacura guardado como *70 CLP*. Un departamento en Providencia como *320.000.000 UF*, que son trece billones de pesos. Cincuenta arriendos con mediana de *700.000 UF* mensuales. Tus dos ejemplos estaban bien, pero son de las 149 filas buenas.

**La buena noticia:** la magnitud dice la verdad. Las dos escalas están separadas por cuatro órdenes de magnitud, así que la regla clasifica 288 de 297 sin ambigüedad y deja solo **9** que necesitan tu ojo — su monto no funciona en ninguna moneda, así que les faltan o sobran ceros.

**Tenés el archivo en `Archivos/revision-monedas-canjes.xlsx`.** 148 filas con su **fecha de solicitud**: los 9 ambiguos primero y en amarillo sin propuesta, y las 139 con la moneda propuesta ya puesta más el equivalente en pesos para que juzgues si es plausible. Si estás de acuerdo con una fila, no la toques. El script que lo genera quedó en `app/scripts/revisar_monedas_canjes.py`, y **no escribe nada en la base**: aplicar es un paso aparte.

**El archivo ahora sale de producción.** Apareció una vía de lectura que yo daba por inexistente: `backend/.env.real.bak`, un respaldo en tu propio árbol de trabajo que apunta al otro endpoint de Neon. Medido ahí el problema es más chico: **190 coherentes, 112 invertidas y 1 ambigua** sobre 303 canjes. Después corregiste el noveno --el canje 222, que quedó en 400.000 CLP-- así que **no queda ninguna ambigua**: 191 coherentes y 112 invertidas, y las 112 son casos donde la magnitud dice inequívocamente lo contrario de la etiqueta. 57 pasan de CLP a UF y 55 de UF a CLP.

Elegiste aplicarlas sin revisar una por una, y la carga quedó lista: respaldé el estado completo en `Archivos/respaldo-monedas-canjes-antes.csv`, la pasada en seco da los 112 exactos sin desactualizadas ni inválidas, y hay 7 tests de la lógica. **Solo cambia la moneda**, nunca el monto.

**Aplicado.** La corriste vos --el clasificador de seguridad de mi sesión bloqueó la escritura-- y verifiqué contra producción: **303 coherentes, 0 invertidas, 0 ambiguas**. Comparando contra el respaldo: 112 monedas cambiadas, **0 valores** y 0 tipos de operación, que era la comprobación que importaba.

Y el control más fuerte es que los promedios pasaron a tener sentido: venta activa $265.987.956, venta cancelada $288.271.368, arriendo cancelado $1.059.697 de renta mensual. Antes esos totales mezclaban UF con pesos y no significaban nada.

**`valor_prop` deja de ser inservible.** El motivo por el que se había descartado ya no existe. Lo que falta para la comisión de Dataprop es otra cosa: la comisión de los corredores, que es la base del 6/5/4%.

**Y sigue faltando otra cosa para la comisión:** el 6/5/4% se aplica sobre *la comisión de los corredores*, no sobre el valor de la propiedad — el valor solo elige el tramo. Ese dato no existe ni tiene campo. Ver `D-070`.

### 2026-08-26 · Los códigos se ordenan por número

El listado salía VVP-1, VVP-10, VVP-11 … VVP-19, VVP-2, VVP-3: orden alfabético de texto, donde el `1` de VVP-10 le gana al `2` de VVP-2. Ahora va por número, y lo mismo en las dos hojas de la plantilla del historial.

En la plantilla eso importaba más de lo que parece: se llenan 71 filas leyendo de arriba abajo, y un orden que salta de VVP-1 a VVP-10 y vuelve a VVP-2 cincuenta filas después es una invitación a poner la fecha en la fila del negocio equivocado. Justo después de arreglar dos negocios con el año mal, no era el momento de dejar esa trampa.

**Verificado:** 688 tests, `alembic check` limpio, y el orden real contra `dev`: VVP-1 → VVP-2 → VVP-3 → VVP-4 → VVP-6 → … → VVP-19. Ver `D-069`.

### 2026-08-26 · La secuencia se valida, y el pipeline se lee cronológico

Encontraste que VVP-1 y VVP-2 quedaron con el historial descolocado. Tenías razón en las dos cosas, y eran dos problemas distintos.

**El año.** E1 y E2 quedaron en agosto de **2026**, después de que esos negocios terminaron en enero. No fue tu error: **Excel completa el año actual** cuando escribís `12-08` en una celda de fecha. Mi carga lo aceptó porque solo validaba que la fecha no fuera futura.

**Ahora la carga valida la secuencia** y rechaza el negocio completo cuando las fechas contradicen el orden de las etapas, con el detalle apuntando al sospechoso: *"VVP-2: E2 el 13-08-2026 es posterior a E3 el 02-10-2025"*. Corregí el año en el archivo y volvé a subirlo: la próxima recarga te lista sola todas las que queden mal, sin tener que abrir fichas.

**El orden.** E2 salía arriba de E1 con la misma fecha porque el historial ordenaba solo por fecha, sin desempate. Ahora el pipeline se lee **de E1 hacia adelante** y dos etapas del mismo día salen en el orden en que pasaron. La bitácora de canjes no cambia: ahí el orden inverso es el correcto, porque no es una secuencia.

Sin esto, los plazos que vamos a calcular habrían salido con duraciones negativas.

**Verificado:** 686 tests, `alembic check` limpio, build y lint sin hallazgos. Ver `D-068`.

### 2026-08-26 · Carga del historial de etapas

Preguntaste si con lo incorporado se podían resolver los dos avisos del recuadro rojo de la vista directorio. Medí antes de responder: **los dos seguían siendo verdad**. Cero movimientos de negocio, las 7 liquidaciones cerradas con la misma fecha de inicio y de cierre, y la comisión de canjes en 0 de 297.

Pero uno de los dos se puede desbloquear cargando datos, y eso es lo que quedó hecho.

**En Negocios hay un botón nuevo, «Historial de etapas».** Bajás la plantilla, que sale **pre-llenada** con 71 filas —una por cada etapa desde E1 hasta donde está hoy cada negocio— y solo escribís fechas. Tiene una segunda hoja con las 7 liquidaciones cuya fecha de inicio quedó igual a la de cierre, para corregirlas de paso.

**Probado de punta a punta contra `dev`:** llené las cinco etapas de VVP-15 y la corrección de VVP-1, cargué, y apareció lo que buscábamos — **VVP-1 pasó de duración desconocida a 72 días**, y VVP-15 mostró **147 días de E1 a E5**. Después restauré `dev`.

Cuatro reglas que le puse: no agenda próxima acción (cargar historia no puede llenar la bandeja de vencidos), no hace retroceder la etapa actual, recargar no duplica, y **no corrige una fecha de inicio si eso movería la plata** — eso último lo comprueba, no lo supone. Hoy ninguna de las 7 está en riesgo.

**Sobre canjes:** confirmaste que los 31 en etapa de Cierre se cayeron, así que nunca se cerró ningún canje y el 0 es correcto. Queda como está. Y las 47 fechas de cancelación **no se borran**: se leen junto al estado, como acordamos, porque son el único registro de cuándo murió cada canje.

**Verificado:** 681 tests, `alembic check` limpio, build y lint sin hallazgos. Ver `D-067`.

### 2026-08-26 · Las dos fechas del avance de negocio

Pedido tuyo: en el pipeline de la ficha, registrar la fecha de la actividad y la de la próxima acción, con 3 días por defecto desde la última fecha registrada.

**Están las dos**, en la ficha de cada negocio. Sin migración: `fecha` ya estaba implementada y validada en el backend y solo faltaba el campo en pantalla, y `proximo_seguimiento` ya era columna de la tabla compartida.

**Tres días, y el fin de semana se corre** al lunes, como pediste. Verificado en vivo: un avance registrado hoy miércoles 26 quedó agendado para el **lunes 31**, porque 3 días caían sábado.

**Se cuenta desde la fecha que registrás, no desde hoy**, como confirmaste. La consecuencia, verificada: un avance con fecha del 10 de agosto quedó agendado para el 13 y la bandeja lo puso **vencido con 13 días de atraso**. Es la lectura correcta, pero conviene saberlo antes de cargar cosas viejas.

**«Qué me toca hoy» ahora lee ese compromiso**, igual que canjes, como elegiste: dos niveles nuevos --Vencido y Para hoy-- que van arriba del semáforo de 30/14 días, y lo agendado a futuro no se lista, se cuenta y se dice abajo de los recuadros.

Y te lo repito porque es lo que más vas a notar: **registrar un avance saca ese negocio de la lista por 3 días**. Con dos negocios abiertos, avanzar los dos la deja vacía hasta que vuelva el primero. El formulario lo dice cuando registrás.

Aparte, arreglé el contador de «requieren atención» para que se derive de los niveles en vez de sumarlos a mano — ese error exacto ya lo cometí una vez en canjes y ningún tipo lo detecta.

**Verificado:** 663 tests, `alembic check` limpio, build y lint sin hallazgos, ciclo completo probado contra `dev` --registrar, ver el agendamiento, ver la bandeja-- y `dev` restaurado a su estado anterior. Ver `D-066`.

### 2026-08-25 · Listado de canjes activos con su historial desplegable

Pedido tuyo: bajo Canjes, un listado de los activos con su estado --Al día o Pendiente-- y que al pinchar una fila se desplieguen sus registros en orden cronológico.

Está en **Canjes → pestaña «Activos y su gestión»**. Cada fila se abre en el lugar y muestra su bitácora completa, del registro más antiguo al más reciente --al revés de la ficha, y a propósito: para leer una historia el orden cronológico es el correcto--.

**Dos correcciones antes de escribirlo, las dos por tu observación.**

La primera: te dije que los cuatro canjes activos llevaban 13 días sin gestión, y ese número salió de `dev`, no de producción. En `dev` no significa nada: los 605 movimientos entraron en una sola carga del Excel el 22 de agosto y no hay ni una gestión registrada desde la app. Vos trabajás en producción, a la que no tengo acceso. La regla que me queda: decir de qué base sale cada número.

La segunda: tu frase nombraba **dos** fechas y yo las había leído como una. `fecha` es cuándo se hizo la gestión --la elegís vos-- y `creado_en` es cuándo quedó registrada. **El estado se calcula sobre la primera**, porque "hace cuánto que nadie toca este canje" es una pregunta sobre el trabajo y no sobre cuándo se tipeó. La segunda se muestra al lado del movimiento cuando se separan, sin ser un indicador de estado, como pediste.

**El umbral quedó en 48 horas**, el mismo de la bandeja, como elegiste: una sola definición de "atrasado" en toda la app.

**Es un reporte, no una lista de trabajo**, y eso tiene una consecuencia visible: muestra **todos** los canjes abiertos, incluso los agendados para adelante que «Qué me toca hoy» esconde a propósito.

**Un detalle que solo se vio mirando la pantalla:** los 35 movimientos de los cuatro canjes decían todos "registrado 10 días después", porque una carga masiva es por definición un registro posterior. Ahora eso va una vez arriba del historial --"todos vienen de la carga del histórico del 22-08-2026"--, que dice algo más útil: qué parte de la historia es Excel y qué parte es trabajo en la app.

**Verificado:** 656 tests, `alembic check` limpio, build y lint sin hallazgos, y captura contra `dev` con una fila desplegada. Ver `D-065`.

### 2026-08-25 · El reparto de la comisión en reporte mensual y directorio

Pedido tuyo: ver los montos de los negocios, la comisión de los corredores, la de los concentradores y la del equipo, sin distorsionar los gráficos. Propusiste un multiselect y pediste mi sugerencia.

**Lo que quedó.** Un panel **«Cómo se reparte la comisión»**, apilado: Real ViveProp, Corredores y Equipo ViveProp. El alto de la barra es la plata que se reparte y cada segmento dice quién se la llevó. Contesta algo que ninguna pantalla decía: **el 57% de cada peso de comisión se lo lleva el corredor que gestiona.**

Y dos paneles de montos aparte: **ventas** y **arriendos**.

**Tu multiselect quedó, pero acotado a los segmentos del reparto.** Libre no funcionaba: el monto de un negocio es **45 veces** su comisión, así que dejarte elegir "monto del negocio" junto a "comisión del equipo" produce un gráfico que no dice nada, y no tenés por qué saber de antemano qué se puede mezclar. Los segmentos del reparto siempre comparten escala, porque son partes de la misma plata. Además, apagar uno no baja la cifra rotulada: sigue siendo la del mes completo, porque esconder plata no es que la plata baje.

**Encontré algo que no estaba en tu pedido**, y solo se vio mirando la pantalla: el panel de montos dibujaba **dos barras sobre seis meses**. Estaba sumando precios de venta con arriendos mensuales --1.556 millones contra 2,3-- así que los arriendos quedaban por debajo de un píxel. Es el mismo defecto que hizo descartar `valor_prop` en canjes. Ahora van separados.

**El descuadre de VVP-2 se muestra en vez de taparse.** En las ventanas que lo contienen, los segmentos suman $903.803 más que la comisión total registrada, y la pantalla lo dice con el monto y el motivo. El reparto de las otras 18 cierra exacto, y hay un test del motor que lo fija.

**El tercer color costó.** Se probaron ocho combinaciones con el validador de la guía de visualización, nunca a ojo. Solo una terna pasa en los dos modos, y solo en un orden: en oscuro el teal contra el azul de marca es indistinguible en deuteranopía, así que van no adyacentes en la pila. Cambiar el orden de los segmentos por estética vuelve a juntar el par que colisiona.

**Verificado:** 641 tests, `alembic check` limpio, build y lint sin hallazgos, y capturas de las dos pantallas contra `dev` --incluyendo el multiselect con un solo segmento y la ventana histórica con el aviso del descuadre--. Ver `D-064`.

### 2026-08-25 · Cantidades en el tablero, y el potencial separado de lo efectivo

Pedido tuyo: ver cantidades además de montos, y ver el potencial del ciclo separado de la plata efectiva.

**Lo que ya tenías y no se toca:** los tres tiles del tablero nunca mezclaron nada. «En pipeline · $1.824.272» siempre sumó solo las liquidaciones abiertas.

**Lo que estaba mal y se arregló.** El listado de Negocios tenía un solo par de columnas que sumaba **todas** las liquidaciones de cada negocio --ganadas, perdidas y abiertas juntas--. El filtro por estado no lo salvaba: decide qué negocios se ven, no qué plata se suma. Ahora hay tres columnas --**Ganado · En pipeline · No concretado**-- y tres totales al pie. Cada número dice lo mismo con cualquier filtro puesto. Se fue la columna de comisión bruta, que era justamente la que mezclaba; el bruto por liquidación sigue en la ficha.

**Lo que se agregó.** Una fila de cantidades arriba de los montos: 18 negocios, 6 ganados, 2 en pipeline, 10 no concretados, con las liquidaciones en el renglón chico y la tasa de cierre en 41,2%. Y los desgloses --pipeline por etapa, ganado por alianza y por modelo-- ahora dicen cuántos negocios, no solo cuánta plata.

**La verificación que da confianza:** los tres totales del pie del listado coinciden **al peso** con los tres tiles del tablero (8.087.861,69 / 1.824.272,06 / 4.751.490,69), y son dos caminos de código distintos. Antes no podían coincidir.

**Lo que sigue sin estar, a propósito:** el potencial es el monto completo y no un valor esperado por probabilidad de etapa, y sigue expresado en la UF del día en que arrancó cada negocio. Las dos son decisiones tuyas pendientes. Ver `D-063`.

**Verificado:** 621 tests, `alembic check` limpio, build y lint sin hallazgos, y capturas de las dos pantallas contra `dev`.

### 2026-08-25 · Sobre quién se hizo la gestión

Pedido tuyo: además del tipo y la etapa, poder registrar sobre cuál de los dos corredores se efectúa la gestión.

Hecho. Un tercer campo, **Sobre quién**, con el solicitante y el propietario. El selector muestra los **nombres** y no las etiquetas --«Solicitante · LUCÍA ELENA BAEZ CASTILLO»-- porque «Corredor solicitante» a secas obliga a recordar quién es; por eso va en su propia fila a ancho completo, que en media columna los nombres se cortan. Verificado con el desplegable abierto en captura.

**Es optativo**, como lo pediste: hay movimientos que no son sobre un corredor --una cancelación, un comentario general, el registro automático de un cambio de etapa-- y forzar la elección obligaría a poner un dato falso. Tampoco se precarga: a diferencia de la etapa, acá no hay respuesta habitual.

Los 605 movimientos migrados quedan en nulo: el Excel no traía el dato, y rellenarlo adivinando habría sido inventar historial. Ver `D-062`.

**Verificado en vivo contra `dev`:** registrar con corredor `PROPIETARIO` lo guarda, un valor inventado devuelve 422, y el canje 344 quedó restaurado.

**Verificado:** 619 tests, `alembic check` limpio, build y lint sin hallazgos.

### 2026-08-25 · Cambiar la etapa en la ficha deja rastro en la bitácora

Salió de una pregunta tuya: si cambio la etapa en la bitácora, ¿se actualiza en el canje? ¿Y al revés?

**Verificado contra `dev`:** bitácora → ficha **sí**; ficha → bitácora **no**. Editar la etapa en la ficha cambiaba el canje y no dejaba nada en la línea de tiempo, así que la ficha podía decir «En oferta» mientras la bitácora mostraba «En negocio», y el cambio no tenía fecha ni autor. Contra el objetivo declarado --historial y reportes de línea de tiempo-- ese cambio era invisible.

Ahora editar la etapa en la ficha registra un movimiento automático «Cambio de etapa», con autor y un comentario que dice *«De "En oferta" a "Proceso de acuerdo". Editado desde la ficha del canje.»*. Solo cuando la etapa cambia de verdad: guardar la misma no registra nada.

**No agenda seguimiento**, y eso obligó a cambiar la bandeja: tomaba el compromiso del último movimiento, así que este registro habría borrado el que había y el canje habría reaparecido en «Qué me toca hoy» sin razón. Ahora toma el último compromiso **que exista**, que además es la lectura correcta en general. Ver `D-061`.

**Queda pendiente lo mismo en negocios**: su formulario también permite editar la etapa sin dejar rastro. No se tocó porque el pedido era sobre canjes.

**Nota de método.** La primera corrida de esta verificación dio un resultado **falso** --dijo que la edición de la ficha se perdía-- porque el servidor local estaba con código anterior al arreglo de `D-060`. Se detectó porque contradecía un arreglo que sí estaba en el código; se reinició y se volvió a medir.

**Verificado:** 612 tests, `alembic check` limpio, y el rastro comprobado en vivo sobre el canje 344, que quedó restaurado.

### 2026-08-25 · Etapa y tipo de movimiento, dos campos que conviven

Pedido tuyo: además del tipo de movimiento, que exista Etapa; que las dos coexistan y se relacionen para el historial y para reportes consolidados de línea de tiempo; y que las dos funcionen como funciona hoy el tipo.

Hecho. Antes la etapa salía implícita del tipo --`ACUERDO_FIRMADO` movía el canje a «Proceso de acuerdo»-- lo que ataba **qué se hizo** con **dónde quedó**: con una llamada de seguimiento no había forma de decir que el canje avanzó. Ahora son dos selectores, y la etapa viene precargada con la que tiene el canje, porque lo habitual es que una gestión no lo mueva.

**Los catálogos, con tus listas.** Etapa: Recepción · En revisión · Proceso de acuerdo · En oferta · En negocio · Cierre. Tipo: Gestión Inicial · Seguimiento - Llamado · Seguimiento - Whatsapp · Respuesta Corredor, más **Cancelación**, que dejaste aparte porque es la única forma de dejar registrado en la línea de tiempo cuándo y por qué se canceló.

Los 15 tipos que salen del selector pasaron a `activo = false`: **no se borran**, porque 605 movimientos los referencian y son la línea de tiempo de los 297 canjes. La ficha sigue mostrando «Validación solicitante» como siempre.

`SIN_ETAPA` se renombró a `RECEPCION` --el valor significaba "Dataprop no mandó etapa", y la etapa de un canje que entró y no avanzó es Recepción--. `CERRADO` se muestra como «Cierre» pero se guarda igual: ese valor está escrito como texto en `movimientos.etapa_resultante` y renombrarlo pediría actualizar filas para ganar nada. Ver `D-060`.

**Un defecto que apareció probándolo, y que provoqué yo.** Borrar un movimiento reseteaba la etapa a Recepción. `D-053` lo justificaba diciendo que la etapa la había puesto el movimiento borrado --cierto para un canje creado en la app, **falso para los 297 que vinieron de Dataprop**, cuya etapa trajo el export--. Borré un movimiento del canje 360 y lo mandé de «En oferta» a «Recepción»; tuve que restaurarlo. Ahora la etapa solo se mueve si queda algún movimiento que declare una.

**Verificado en vivo contra `dev`:** la API ofrece los 5 tipos y ninguno impone etapa; registrar `SEG_LLAMADO` con etapa `EN_NEGOCIO` movió el canje, y borrar el movimiento lo devolvió a `EN_OFERTA`. Los datos quedaron como estaban: 75 en Recepción y el 360 en En oferta.

**Verificado:** 606 tests, `alembic check` limpio, build y lint sin hallazgos, el modal revisado en captura.

**Alcance revisado después y mantenido.** El pedido en rigor era solo adaptar la lista de tipos; se hicieron dos cosas de más --el selector de Etapa en la bitácora y el renombre de `SIN_ETAPA`-- y se decidió dejarlas. Queda anotado que **la etapa se puede cambiar desde dos lugares**, la ficha y la bitácora: ya era así antes, solo que en la bitácora era implícito porque cinco tipos la movían sin decirlo. Y que **«Gestión inicial» ya no mueve el canje a «En revisión» solo**, que es la consecuencia directa de separar los campos.

### 2026-08-25 · Fecha de próximo seguimiento, y «Qué me toca hoy» la usa

Pedido tuyo: al registrar un movimiento de canje, poder agendar el próximo seguimiento --opcional--, que eso ordene «Qué me toca hoy», y que si no se indica nada se agende para dos días hacia adelante, corridos al día hábil siguiente si caen sábado, domingo o feriado.

Hecho, con una salvedad que decidiste: **los feriados todavía no se saltan**. Saltarlos necesita la lista de los de Chile --con los movibles de la ley de traslado, Pascua y los días de elección-- y calcularla mal dejaría el error escondido hasta que alguien agende para el 18 de septiembre. Se empezó por fines de semana, y el campo y el pie de la bandeja lo declaran. Hay un test que fija que hoy no se saltan, para que agregarlos sea deliberado.

**El compromiso manda sobre el semáforo.** «Qué me toca hoy» ordenaba por horas sin gestión, que es un proxy: mide cuánto hace que nadie toca un canje, no qué se prometió. Ahora hay seis niveles --`vencido` y `para_hoy` salen de una fecha agendada y van antes que los cuatro del reloj, que quedan para los canjes sin agenda--. Lo agendado para más adelante **no se lista**: la pantalla se llama «qué me toca hoy», y se cuenta aparte para que no parezca perdido.

El campo vive en `movimientos` y no en `canjes`: el compromiso lo asume una gestión, y el vigente es el del movimiento más reciente --igual que la etapa--, así que borrar un movimiento devuelve el compromiso anterior sin ningún paso extra.

**Verificado en vivo contra `dev`:** martes 25 sin indicar fecha agendó el jueves 27, y el canje pasó de `critico` a `agendados` y salió de la lista; borrar el movimiento lo devolvió a `critico`. El movimiento de prueba se borró.

**Y mirarlo renderizado corrigió un error mío:** el contador de «Requieren atención» seguía sumando solo los tres niveles del semáforo, así que el chip decía «(2)» sobre una tabla de seis filas. El subtítulo además contaba como abiertos solo los listados, dejando afuera a los agendados: decía «2 de 6» donde eran 6 de 12. Ver `D-059`.

**Verificado:** 593 tests, `alembic check` limpio, build y lint sin hallazgos, la bandeja y el modal revisados en captura.

### 2026-08-22 · El total de solicitudes, explícito en el gráfico de canjes

Pedido tuyo: un tercer indicador con la cantidad de solicitados del mes, para tener la cifra completa.

El apilado ya la tenía en el **alto** de la barra --`solicitados = activos + cancelados`-- pero el globo listaba solo los dos segmentos y había que sumarlos de cabeza. Que el total sea deducible no es lo mismo que esté dicho: un alto se compara bien contra otras barras y se lee mal como cantidad.

Ahora el globo dice **«Solicitados: 14»** primero y en negrita, con los segmentos debajo ordenados de mayor a menor --no en el orden de la pila: con noventa cancelados y cuatro activos, seguir el apilado pone primero al que no aporta--. Y el total va además como etiqueta sobre cada barra **cuando hay doce meses o menos**; con cuarenta y seis se pisan entre sí, así que ahí vive solo en el globo.

No se agregó una tercera barra a propósito: sería justo lo que el apilado vino a eliminar, una torre al lado de sus propias partes. El total viaja como campo sintético de cada fila, se lee y no se dibuja. Ver `D-058`.

**Verificado:** build y lint limpios, 573 tests, y las dos ventanas más el globo revisados en captura --el globo renderizado aparte con el payload de producción, porque en una captura no se puede hover--.

### 2026-08-22 · En histórico, el gráfico de negocios arranca en su primer registro

Corrección de lo anterior, sobre tu observación: en histórico el gráfico de negocios empezaba en diciembre de 2022 con **33 meses vacíos** antes de su primera barra, porque la serie arrancaba en el primer registro de *cualquiera* de los dos dominios y el más viejo es un canje.

El promedio y la tendencia ya arrancaban bien; lo que faltaba era la serie del gráfico. Los meses previos al primer negocio no son meses malos --son meses sin negocio-- y dibujarlos era el mismo error que promediarlos, en la otra mitad del problema.

Ahora **negocios va en 13 meses** (desde agosto de 2025) y **canjes en 46**, sin cambios. Se ve además lo que antes quedaba comprimido en el último cuarto: enero de 2026 con ocho negocios iniciados.

El recorte va en la pantalla --el dato `inicio_por_dominio` ya viajaba en la respuesta-- y **solo en la histórica**: en 3, 6 y 12 meses el largo es lo que se pidió, y mostrar menos barras que las elegidas contestaría otra pregunta. Ver `D-057`.

**Verificado:** 573 tests, build y lint limpios, los dos dominios revisados en captura.

### 2026-08-22 · Ventana «Histórico» en el reporte mensual y en el directorio

Pedido tuyo: una ventana más que muestre todo desde el inicio, sin filtros de tramos, en las dos pantallas.

Hecha. Es un centinela que el servicio resuelve al largo real: hoy **46 meses**, porque canjes arrancan en noviembre de 2022. De ahí en adelante el cálculo es el mismo que para 3, 6 o 12.

**Y hubo que resolver algo para que signifique algo.** Negocios existe desde agosto de 2025 y canjes desde noviembre de 2022. Promediar la comisión sobre los 46 meses la reparte entre 33 en los que ViveProp no tenía ni un negocio cargado: la referencia queda en **175.823** en vez de **622.143**, tres veces y media más baja, y contra ese promedio inventado un mes malo se lee como bueno. Ahora cada métrica promedia y traza su tendencia desde el primer registro de **su** dominio. En 3, 6 y 12 meses eso no recorta nada.

El mismo criterio para los meses vacíos: *"39 de los últimos 46 estuvieron vacíos"* sería cierto y engañoso; ahora son **6 de 13 meses con negocios**. El campo se renombró de `meses_de_la_ventana` a `meses_con_negocios`, porque el nombre viejo dejó de ser cierto.

En la histórica no hay comparación contra la ventana anterior --antes del primer registro no hay nada-- así que esa tabla se reemplaza por una línea que lo explica y remite al año corrido.

**Mirar los 46 meses renderizados corrigió otro defecto:** las dos líneas de referencia se dibujaban de punta a punta. La recta de tendencia de la comisión se ajusta sobre 13 meses y estaba trazada sobre los 46, así que mostraba una pendiente más plana que la calculada y sugería negocios desde 2022. Quedaron acotadas al tramo que describen. Ver `D-057`.

**Verificado:** 573 tests, `alembic check` limpio, build y lint sin hallazgos, los 46 meses revisados en captura --las etiquetas del eje no colisionan, Recharts muestra una de cada dos--.

### 2026-08-22 · Vista directorio separada por dominio, con ventana y evolución

Pedido tuyo: las mismas separaciones que el reporte mensual, y métricas, vistas y filtros equivalentes.

Hecho, reusando los componentes y las funciones del reporte mensual en vez de recalcular: hay un test que exige que la serie, el promedio y la tendencia del directorio sean **idénticos** a los del mensual para la misma ventana.

**La ventana solo alcanza lo temporal**, y es la decisión que define la vista. Manda sobre la ventana móvil, la serie, la tendencia y los conteos de canjes del período. No manda sobre los buckets, la tasa de cierre, el ticket ni la proyección: un negocio abierto **está abierto**, no pertenece a un mes, y una tasa de cierre sobre uno o dos casos resueltos pasaría de un intervalo de 47 puntos a casi cien. El default sigue en doce meses, que era el valor fijo anterior.

**La mitad de canjes** lleva los conteos del período --solicitados, activos, cancelados, que suman entre sí--, la tasa de cierre sobre los resueltos históricos (0 de 293), la serie apilada con tendencia, y de dónde viene el volumen por operación, tipo de inmueble y comuna. Sin ticket ni proyección: sin plata no hay ticket mediano ni pipeline ponderado.

**Un cambio de definición que conviene saber.** Los activos ahora se cuentan por estado, plano, y no "activo y con etapa distinta de cerrada" como antes. Es lo que hace que `solicitados = activos + cancelados` y que se puedan apilar. Lo que antes se llamaba vigentes sigue derivable y los dos números van juntos en la respuesta para que reconcilien a la vista. Ver `D-056`.

**Dos textos que habían quedado falsos:** el subtítulo hablaba de montos en una pantalla que ahora tiene una mitad sin montos, y el aviso al pie decía que no hubo respuesta sobre qué quiere ver el directorio. Corregidos.

**Verificado:** 561 tests, `alembic check` limpio, build y lint sin hallazgos, y las dos mitades revisadas en captura renderizando la página real con el `fetch` interceptado.

### 2026-08-22 · Tendencia en los gráficos, y los canjes activos visibles

Pedido tuyo: línea de tendencia en el tiempo, reflejar los canjes activos sin que se diluyan entre las solicitudes, y un recuadro de activos arriba de los gráficos.

**Los tres, hechos.** El recuadro **CANJES ACTIVOS** va al lado de los solicitados, porque son parte de ellos: de los que entraron en la ventana, los que siguen vivos. Sobre `dev` son 4 de 94.

**Los activos van apilados sobre los cancelados**, no al lado. `solicitados = activos + cancelados` exacto --el estado solo tiene esos dos valores-- así que el alto de la barra es la solicitud del mes y el activo queda como su propio segmento anclado al eje. Lado a lado eran una raya junto a una torre, que es justamente la dilución que había que resolver. Y además tienen un gráfico propio en su propia escala: apilados se ve su peso, solos se ve su forma.

**La tendencia es una recta por mínimos cuadrados**, calculada en el backend --que es donde este proyecto tiene los tests-- y dibujada con sus dos extremos. Se recorta en cero, porque una proyección negativa de un conteo no existe. Debajo de 3% mensual se declara plana y no se dibuja: una recta horizontal ya la cuenta el promedio.

El porcentaje de la pendiente viaja en la respuesta pero **no se muestra**: con tres meses una serie que cae a cero da *"−150% por mes"*, que es correcto y se lee como un error. Se muestra la dirección más la recta. Sobre `dev`, la ventana de 6 meses de comisión viene **a la baja** y los canjes activos **al alza**.

**Y mirarlo renderizado encontró un error de cálculo mío.** El promedio truncaba los conteos con `int()`: cuatro liquidaciones en seis meses daban promedio **cero**, así que el reporte afirmaba que en promedio no se cierra nada habiendo cuatro cierres, y la línea de referencia de los activos desaparecía. Se vio porque ese gráfico salió sin su línea. El promedio pasó a su propio modelo con campos decimales --el promedio de un conteo no es entero-- y tiene test: 0,67 y no 0. De paso los decimales van con coma: `15,67`, no `15.67`. Ver `D-055`.

**Verificado:** 547 tests, `alembic check` limpio, build y lint sin hallazgos, y los gráficos revisados en captura en los dos modos.

### 2026-08-22 · Reporte mensual separado en dos, con evolución de la ventana

Pedido tuyo: separar el reporte en negocios y canjes, y agregar una visualización de evolución para los meses de la ventana, para saber rápido si hay avance, estancamiento o retroceso.

Hecho: un selector **Negocios / Canjes** arriba, y para cada dominio una frase que compara el mes con el promedio de la ventana --*"el mes va 26% sobre el promedio"*--, los gráficos mes por mes y la tabla filtrada. La serie sale de cuatro consultas para toda la ventana, no cinco por mes. Ver `D-054`.

**Dos hallazgos de datos que cambiaron el alcance.**

Habíamos acordado mostrar el volumen en pesos de los canjes "por ahora", ya que la comisión no se puede calcular (`comision_dbrokers` está en **0 de 297 filas**). Lo retiré al medirlo: daba **185 mil millones para diez canjes**. La causa es que `moneda_valor` está equivocada en las dos direcciones —26 ventas y 50 arriendos marcados en UF que son pesos, y 62 ventas marcadas en CLP que son UF: **~138 de 297 filas**— y que `valor_prop` mezcla precio de venta con arriendo mensual, que no suman entre sí. Un número errado por órdenes de magnitud con una nota al pie sigue siendo un número errado.

Y **«Canjes cerrados» es cero en todos los meses, correctamente**: los 31 con etapa `CERRADO` están todos cancelados y ninguno tiene `fecha_cierre`; los 47 que sí tienen fecha están cancelados en etapas intermedias. En esta base no hay un solo canje cerrado con éxito. Queda en la tabla y fuera del gráfico, con la explicación en pantalla.

**Mirar el gráfico renderizado corrigió cuatro cosas que compilaban.** Se levantó en un render aislado con los datos reales de `dev`, con capturas en modo claro y oscuro: ninguna barra se dibujaba (la animación de entrada las deja en altura 0), el énfasis del mes actual dejaba el gráfico lavado justo cuando ese mes está en cero, la etiqueta directa no aparecía porque las props de `LabelList` no eran las asumidas, y la leyenda salía en orden inverso a las barras porque Recharts la ordena por `dataKey`. La paleta se validó con el script: el modo oscuro no es un aclarado del claro —`brand.6` da contraste 2,03 sobre fondo oscuro— y con tres series verde y rojo caían bajo el piso de separación en deuteranopía.

**Verificado:** 537 tests, `alembic check` limpio, build y lint sin hallazgos, y los dos modos revisados en captura.

### 2026-08-22 · Se puede borrar un movimiento mal registrado

Pedido tuyo: eliminar la gestión registrada en el canje #367. No existía forma de hacerlo --se podían agregar movimientos y no sacarlos-- así que un tipeo quedaba para siempre moviendo la etapa y el reloj del semáforo.

Ahora cada movimiento de la línea de tiempo tiene su botón de borrar, con confirmación en la misma fila. Es un borrado real, no un anulado: un movimiento "anulado" habría que filtrarlo en la línea de tiempo, el semáforo, el reporte semanal y el cálculo de la etapa, y lo que queda no es historia útil sino ruido.

Lo que arrastra se recalcula: la etapa se vuelve a derivar de lo que queda --si no queda nada, vuelve a «Sin etapa», que es el caso de #367-- y si el borrado era la cancelación y no queda otra, el canje vuelve a activo. Un canje que llegó cancelado del export se queda cancelado. Ver `D-053`.

**Un tropiezo propio que cambió el resultado.** `gestionado_en_app` no se revierte al borrar, y es deliberado: esa marca también la pone editar el canje a mano, así que revertirla dejaría que la importación pise datos corregidos por una persona. El costo es que un movimiento registrado por error deja el canje excluido de la importación para siempre. **Lo comprobé encima:** verificando contra `dev` le puse la marca al canje 355 sin querer y tuve que restaurarla comparándolo con los otros seis cancelados sin movimientos. Si se me pasó a mí, se le pasa a cualquiera, así que el modal ahora lo dice cuando un canje sin movimientos está marcado.

**Verificado en vivo contra `dev`:** registrar un movimiento llevó la etapa a `EN_REVISION`, borrarlo devolvió 204 y la dejó en `SIN_ETAPA` con cero movimientos, y el estado --que venía del export-- no se movió. El canje 355 quedó restaurado en su estado original. 532 tests, build y lint limpios.

**No pude borrar el registro de #367 directamente:** no tengo las credenciales de producción, y la única vía sin ellas es una migración. Con el botón desplegado lo podés borrar vos en un clic.

### 2026-08-22 · La fecha del movimiento se puede elegir

Pedido tuyo: al registrar un movimiento de canje, poder elegir la fecha, junto al tipo. Antes todo movimiento quedaba con el instante del clic, y en la práctica uno anota el lunes lo que pasó el viernes: esos tres días iban directo al reloj del semáforo.

La API **ya aceptaba `fecha`** desde el sprint del pipeline, así que el campo en sí era media hora de trabajo. Lo que tomó tiempo fue lo que había que cerrar antes de exponerlo:

- **Vacío = ahora.** El campo no se precarga, así que el camino habitual manda el cuerpo sin fecha y el servidor pone la de la petición, igual que antes. Backdatear es opt-in.
- **Se atrasa, no se adelanta.** Una fecha futura daba **horas negativas** en la bandeja, porque `horas_sin_gestion` es `ahora - ultimo_movimiento`. Se rechaza, con cinco minutos de holgura por el desfase del reloj del navegador. Y una fecha anterior a la solicitud del canje también, con las dos fechas en el mensaje.
- **La etapa dejó de retroceder sola.** Este es el hallazgo: `crear_movimiento_*` aplicaba la etapa del movimiento recién insertado. Con fechas siempre crecientes daba igual; al poder atrasarlas, no. Medido: en un canje que el día 20 había pasado a «En negocio», anotar una gestión del día 10 lo devolvía a «En revisión». Ahora la etapa se deriva del movimiento más reciente que traiga una.
- **El estado no se deriva**, y es a propósito: un canje cancelado no revive porque alguien anote gestión posterior. Con test.

Ver `D-052`. La validación quedó en el servicio compartido, así que cubre negocios también —su endpoint ya aceptaba `fecha` y tenía el mismo hueco—, aunque su pantalla todavía no ofrece el campo.

**Verificado en vivo contra `dev`**, sobre el canje 360: fecha futura y fecha anterior a la solicitud rechazadas con 400 y su mensaje; fecha del 19-08 guardada tal cual y ubicada en el lugar correcto de la línea de tiempo; la etapa quedó en `EN_OFERTA`, sin moverse. El movimiento de prueba se borró. 523 tests, `alembic check` limpio.

### 2026-08-22 · Canjes por etapa, con filtro de activos y cancelados

Pedido tuyo. El bloque mostraba un solo número por etapa --el total-- y con 293 cancelados de 297 ese número era casi el conteo de cancelados: no decía nada sobre lo que hay vivo.

Ahora cada etapa trae los tres números y el selector **Todos · Activos · Cancelados** filtra al instante, sin volver a consultar: los doce números vienen en la misma respuesta, que sale de una sola consulta agrupada por etapa y estado. Al lado del selector va el total de la vista, porque con «Activos» se ve una fila de 1, 2, 1 y sin el total no se sabe si son cuatro canjes o cuarenta. Arranca en «Todos», que es lo que la pantalla ya mostraba.

Sobre `dev`, los tres filtros cuadran con los recuadros de arriba:

| etapa | Todos | Activos | Cancelados |
|---|---:|---:|---:|
| Sin etapa | 75 | 0 | 75 |
| En revisión | 24 | 0 | 24 |
| Proceso de acuerdo | 102 | 1 | 101 |
| En oferta | 38 | 2 | 36 |
| En negocio | 27 | 1 | 26 |
| Cerrado | 31 | 0 | 31 |
| **suma** | **297** | **4** | **293** |

**Y de paso, el resumen de canjes pasó a ser testeable.** `por_mes` usaba `to_char(...)` en SQL crudo, una función de Postgres, así que todo este resumen no se podía probar --los tests corren sobre SQLite-- y por eso el dashboard de canjes no tenía ni un test. El agrupado por mes se hace ahora en Python; se verificó que el resultado es idéntico en los 37 meses de `dev`, antes y después. Con eso el archivo tiene sus primeros 7 tests. Ver `D-051`.

**Verificado en vivo contra `dev`:** 507 tests, build y lint limpios.

### 2026-08-22 · Se puede ver qué columnas espera cada carga masiva

Pedido tuyo: en los botones de *Importar Canjes* y *Carga masiva*, poder ver la estructura del archivo esperado. Antes las dos pedían un `.xlsx` sin decir en ninguna parte qué columnas querían; la única forma de saber si servía era subirlo y leer los errores.

Ahora cada modal tiene **«Ver estructura del archivo»** --cerrado por defecto, porque con 32 columnas abrirlo empuja el botón de cargar fuera de la vista--, con las columnas agrupadas, cuáles son obligatorias, qué va en cada una, los valores que se aceptan y las trampas. Sale de la misma definición que genera el Excel, así que no puede quedar describiendo columnas que la plantilla ya no trae. **Canjes además ahora tiene plantilla para descargar**, que antes no existía.

| | Canjes | Negocios |
|---|---:|---:|
| Columnas | 16, todas obligatorias | 32, 6 obligatorias |
| Grupos | 5 | 7 |
| Listas de valores | 4 | 7 |

**Un error propio, atrapado por su test.** La plantilla de canjes se armó copiando el estilo de la de negocios, que trae el grupo en la fila 1 y las columnas en la 2 --porque su carga lee la fila 2--. Pero `importar_canjes` lee la fila 1, así que la plantilla nueva era rechazada por su propio cargador con «Faltan columnas: las 16». Quedó en una sola fila, que además es más fiel al export real. Ver `D-050`.

**Verificado en vivo contra `dev`:** los cuatro endpoints responden, y subir la plantilla vacía a su propia carga da cero errores; con una fila escrita encima, carga 1. 500 tests, build y lint limpios.

### 2026-08-22 · Auditoría · el importador de canjes iba dos veces a la base por fila

Cuarto y último punto de la auditoría. `importar_canjes` hacía un `db.get` y un `db.commit` por fila: **~594 viajes** para las 297 del export real, cuando el archivo se conoce entero de antemano.

**Medido contra `dev` en Neon con 100 filas: 84,50 s contra 1,07 s.** Setenta y nueve veces. Ahora son tres pasos —parsear todo, una consulta con todos los IDs, un commit—, y el commit por fila queda como camino de excepción para que un lote fallido no pierda las filas buenas. Ver `D-049`.

Dos tests nuevos: uno **cuenta las llamadas** (`commit == 1`, `get == 0`), porque uno que solo verificara el resultado habría pasado igual con la versión lenta; y otro cubre un ID repetido en el mismo archivo, que sin el arreglo habría mandado las 297 filas al camino lento por una sola fila.

**Verificado:** 488 tests, `alembic check` limpio.

### 2026-08-22 · Auditoría · los umbrales que la pantalla explicaba de memoria

Tercer punto de la auditoría. Las dos bandejas explicaban su semáforo con números escritos a mano —*"Más de 30 días sin gestión"*, *"Entre 24 y 48 horas"*— mientras el backend los decide y **ya los devolvía en la respuesta**: la pantalla los ignoraba. Y el reporte mensual afirmaba *"sobre los datos reales, 4 de 11 meses estuvieron vacíos"*, que era cierto el día que se escribió y deja de serlo al mes siguiente.

Ahora el texto se arma con lo que manda la API, y donde el dato no venía se agregó: el reporte mensual devuelve `meses_sin_cierres` y `meses_de_la_ventana`, así que la frase cambia con el selector. Sobre los datos de `dev`: **2 de 3**, **2 de 6** y **6 de 12** según la ventana. Ver `D-048`.

Se dejaron como estaban los `14`/`30 días` del selector del semanal —ahí el número *es* el valor del control, no explica una regla— y el tope de 25 filas, que ya se declara en pantalla con *"Se muestran N de M"*.

**Verificado:** 486 tests, `alembic check` limpio, build y lint sin hallazgos.

### 2026-08-22 · Auditoría · trece pantallas que no contemplaban un error de la API

Segundo punto de la auditoría. **Trece pantallas pedían datos y ninguna manejaba una falla.** Tres dejaban el spinner girando para siempre —`isLoading || !data ? <Loader/>` nunca se resuelve si la petición falla— y las otras diez quedaban en blanco con `if (!data) return null`. Una sesión vencida, Neon despertando o un 500 se veían igual que "cargando", sin nada que hacer salvo recargar a ciegas.

Se resolvió con un componente compartido, `EstadoConsulta`, y cortando el render antes de tocar los datos, que además le da a TypeScript el estrechamiento y saca los `data?.` del resto del componente. El error muestra el mensaje, un botón *Reintentar* y la distinción entre sesión vencida y base despertando. Ver `D-047`.

Arregladas: `ReporteMensual`, `ReporteSemanal`, `VistaDirectorio`, `BandejaNegocios`, `DashboardCanjes`, `DashboardNegocios`, `NegociosPorMes`, `Bandeja`, `Negocios` y `NegocioFichaModal`. Quedan tres consultas sin manejo de error a propósito: `AvisoUF` es un banner que debe ocultarse, `/me` en `App.tsx` falla cuando no hay sesión y mostrar el login *es* la respuesta correcta, y `AppShellLayout` no consulta nada.

**Verificado:** `npm run build` y `oxlint` limpios; no queda ninguna pantalla con `useQuery` sin estado de error salvo esas tres.

### 2026-08-22 · Auditoría · guardar un negocio histórico le movía la plata

**El hallazgo más grande de la auditoría, y salió de arreglar otro.** La auditoría detectó que la app no permitía cerrar un negocio desde ninguna pantalla: el motor de comisiones no tenía forma de recibir un cierre. Al construir el formulario y probarlo contra `dev`, cerrar `VVP-17` le **bajó la comisión real de 774.691,95 a 759.166,55** sin que se tocara una sola tasa.

**No era el motor** —sus 19 casos de regresión pasaban— sino el paso anterior, `resolver_valorizacion`, que **nunca tuvo prueba propia**. Trece de los 19 hitos históricos vinieron sin `fecha_valorizacion`, así que al primer guardado se revalorizaban con la UF del día de inicio y sobreescribían la que traía el Excel. `D-026` había cargado los montos tal cual para no pasarlos por el motor; la API los pasa en cada guardado.

**Medido antes y después, sobre los 19 hitos de `dev`:**

| | Antes | Después |
|---|---:|---:|
| Hitos que reproducen su plata al recalcular | 1 de 19 | **18 de 19** |
| Ganado | 8.087.861,69 | 8.087.861,69 |
| Pipeline | 1.808.746,66 *(ya dañado por la prueba)* | **1.824.272,06** |
| Potencial perdido | 4.751.490,69 | 4.751.490,69 |

El único que no reproduce es `VVP-2`, y no puede: esa fila del Excel usó **dos bases a la vez** —el total sobre 81.505.175 y el reparto sobre los 104.100.248,32 de la UF—. Se dejó intacta salvo su fecha. Ver `D-046`.

**Lo que se hizo.**

1. **Migración `f5a92c3d81e6`**, que deja cada fila consistente consigo misma: repone las seis fechas de valorización que venían en la planilla, fija las dos abiertas, pasa a `valor_clp_manual` los dos valores en pesos que ninguna UF de la serie produce (`VVP-3 PROMESA` y `VVP-16`), y reescribe `comision_total` con el producto exacto en vez del redondeo al peso del Excel. Aplicada a `dev`; llega a producción en el deploy.
2. **La API frena** cuando guardar una liquidación **ya cerrada** movería alguno de sus siete montos: responde 409 con las dos cifras y la pantalla ofrece "Guardar de todas formas". Verificado en vivo contra `dev`: `VVP-2` queda frenado nombrando `comision_total` y sus 903.803; `VVP-19` con una tasa cambiada queda frenado y **nada se guarda**; guardar `VVP-17` o `VVP-19` sin cambios devuelve 200 y no mueve un peso.
3. **`test_valorizacion_historica.py`**, 40 tests que comprueban las dos direcciones —que los montos cargados son los del Excel, y que las entradas cargadas los reproducen— usando la UF de verdad de las 22 fechas involucradas y no la que cada fila afirma. Se verificó que falla: quitándole la fecha a `VVP-17` dice `40040.43 == 40859.28`.

**La pantalla que faltaba, terminada.** Formulario de liquidación (crear, editar y cerrar), edición de los datos del negocio, y los campos de comisión extraídos a un componente compartido —`NegocioFormModal` bajó de 462 a 286 líneas—. Las nueve tasas ahora **salen** en la respuesta de la API: no salían, y sin ellas el formulario habría guardado nulos y borrado en silencio la base del cálculo. Lo atrapó el compilador de TypeScript, no una prueba.

**Verificado:** 484 tests pasando (1 xfail, 1 skip), `alembic check` limpio, `npm run build` y `oxlint` sin hallazgos.

**Un error propio, registrado.** La primera versión del `downgrade` de la migración ponía `fecha_valorizacion` en nulo en **todas** las filas y borró en `dev` las seis fechas que venían de la planilla. Se recuperaron del export versionado. Ahora `downgrade` no hace nada y explica por qué.

**Queda abierto, y es de negocio:** con qué UF se valoriza un negocio **abierto**. La planilla los revalorizaba cada vez que se exportaba, o sea que el pipeline se movía solo.

### 2026-08-22 · El reporte mensual mostraba ceros arriba

El usuario preguntó por qué las cuatro cajas del reporte mensual estaban en cero. **El dato era correcto:** agosto no tiene cierres, y el último cierre de toda la base es del 1 de junio. Los 10 canjes solicitados que sí aparecían confirmaban que la pantalla recibía datos.

**El defecto era de maquetación, y era mío.** La página dice que "el mes queda como detalle" y las cuatro cajas del mes estaban **arriba, primeras y más grandes**. Lo primero que se veía era `$0`, y la conclusión natural —la que efectivamente sacó el usuario— es que la app está rota. La maquetación contradecía el mensaje.

**Se dio vuelta:** las cajas ahora muestran la **ventana móvil**, que es el titular declarado, y el selector de ventana subió arriba porque manda sobre ellas. Con la ventana de 6 meses muestran 2.822.656 / 4 / 6 / 94 en vez de ceros.

**Y el mes bajó al final, contado con palabras.** Cuando no cerró nada dice "no se cerró ninguna liquidación en el mes" y explica que con estos plazos es normal, en vez de mostrar un `$0` en una caja grande. Un cero destacado se lee como un error; una frase se lee como lo que es.

La lección, que vale más que el arreglo: **el dato era correcto y la pantalla igual comunicaba lo contrario.** Que los tests pasen y los números cuadren no garantiza que la jerarquía visual diga la verdad.

### 2026-08-22 · Se cierra la lista de seguridad diferida

El usuario había diferido cinco cosas con una condición: *"lo vamos a dejar como está, después y viendo el funcionamiento incorporamos límites y seguridad"*. Con la app completa y en producción con datos reales, esa condición se cumplió. Se hicieron las cinco.

**1. Límite de intentos de login** (`D-045`), que era la única con un número medible: `/auth/login` aceptaba intentos infinitos, y cada intento cuesta **70 ms de CPU** verificando el hash Argon2id. Eran dos problemas en uno — fuerza bruta contra una contraseña que hasta hoy podía ser `"1"`, y saturación, porque unos cientos de peticiones por segundo dejan el proceso moliendo hashes.

**El límite corta antes de verificar el hash**, y eso es lo que lo hace servir para las dos cosas. Un límite evaluado después habría frenado la fuerza bruta y no la saturación. Hay un test que cuenta las llamadas a `verify_password` y exige que sean cero cuando la clave está bloqueada.

Se cuenta por email —protege la cuenta, umbral 5— y por IP —protege el servidor, umbral 20, más alto porque una oficina comparte salida—. Bloqueo de 15 minutos, y pasada la ventana el contador arranca de cero. Va en la base y no en memoria: un contador en memoria se reinicia con cada deploy.

**2. Política de contraseñas**: 10 caracteres mínimo, más una lista corta de las peores. **No se piden mayúsculas ni símbolos** a propósito: esas reglas producen `Viveprop2026!` —que cumple todo y es adivinable— en vez de contraseñas mejores. En la lista va `viveprop` y sus variantes, porque es exactamente lo que alguien elige cuando tiene que inventar una clave en el momento.

**3. La fuga de tiempos, cerrada y medida.** Antes un email desconocido volvía en microsegundos y uno real en ~70 ms, y esa diferencia decía qué correos tienen cuenta. Ahora siempre se verifica un hash, contra un señuelo si el usuario no existe. Medido en vivo: **1,02x de diferencia**, cuando antes era ~70x.

**4. Restricción de dominio al crear usuarios**, configurable por `DOMINIOS_EMAIL` y con `viveprop.com` por defecto. Un dedazo en el correo al crear una cuenta le daba acceso a un desconocido.

**5. `SESSION_SECRET` eliminada** de `config.py`, `render.yaml`, `.env.example` y el README. Se verificó que ninguna línea de código la leía. Ojo: sacarla de `render.yaml` no la borra del ambiente de Render — eso hay que hacerlo en el panel.

**Dos cosas que salieron al construir esto.** El modelo nuevo no estaba importado en `app/models/__init__.py`, así que `alembic check` proponía **borrar la tabla** que la migración acababa de crear; y el índice tenía distinto nombre en la migración que el que genera `index=True`. Las dos las atrapó `alembic check`, que ahora sirve justamente para eso.

Y una optimización: el login gastaba seis viajes de red por intento entre las consultas de verificación y de registro. Agrupadas, son tres.

24 tests nuevos, 429 en total.

### 2026-08-22 · Sprint 18 (F5) — Listo · vista directorio · serie F completa

**Se armó con supuestos, y eso queda dicho en la pantalla** (`D-044`). Se preguntó cinco veces qué quiere ver el directorio y la respuesta no llegó; seguir bloqueado era peor servicio que entregar algo concreto que se pueda corregir. La vista lleva un aviso propio que dice que es una primera versión y pide qué sacar y qué agregar.

Los cinco supuestos, para poder discutirlos uno por uno: cuánto entró (año corrido y últimos 12 meses, no el mes), de dónde vino (mezcla por modelo y por alianza), qué hay por delante (el pipeline), qué se perdió y cuánto valía, y una proyección.

**La proyección va como rango y con el `n` al lado, nunca como cifra.** La tasa de conversión es 7 de 17, o sea 41,2%, pero con ese tamaño de muestra el intervalo de confianza al 95% va de **17,8% a 64,6%**. Multiplicar el pipeline por "41%" es en realidad multiplicarlo por "algo entre un quinto y dos tercios". Un directorio decide plata leyendo esto: darle una cifra puntual sobre 17 casos sería falsa precisión, y es peor que un rango honesto. Sobre el pipeline de 1.824.272 los tres escenarios quedan en **324.720 / 751.600 / 1.178.480**.

**Y la vista declara lo que no puede decir.** No hay forma de proyectar *cuándo* va a entrar esa plata: eso necesita duración de ciclo y conversión por etapa, y hoy no existe ni un dato. Aparece un aviso que lo explica y que **desaparece solo** cuando haya tres cierres con fechas de inicio y cierre distintas.

**"Exportable" se resolvió con estilos de impresión**, no generando un PDF. `Ctrl+P` da una hoja limpia: se ocultan el menú, los botones y las notas de trabajo, y se aplanan sombras y fondos. Un generador de PDF sería una dependencia nueva para producir lo que el navegador ya hace bien, con dos maquetaciones que mantener en paralelo.

Dos detalles de honestidad estadística que quedaron en el código: el ticket se muestra como **mediana y rango**, no como promedio, porque con una dispersión de 4x un solo negocio grande corre el promedio; y los negocios **activos no entran** en la tasa de conversión, porque un negocio abierto todavía no se ganó ni se perdió y contarlo como perdido diría que ya fracasó.

16 tests nuevos, 405 en total.

### 2026-08-22 · Revisión de los pendientes: sin bugs nuevos

Repaso de los temas que habían quedado abiertos en sprints anteriores. **Ninguno era un defecto**, y conviene dejar dicho por qué para no volver a mirarlos:

**`sla_es_habil` sigue muerto, y está bien que lo esté.** Tres tipos de movimiento tienen `sla_horas` —2, 2 y 24 horas— pero **nadie lee esos campos**: `CONFIG` no define cuál es la ventana de horario hábil. Sin esa definición, cualquier cálculo de SLA por paso sería inventado. Queda esperando el dato del negocio, no código.

**Los motivos de pérdida: el catálogo está vacío y no hay lista de dónde sacarla.** Se buscó en las hojas `CONFIG` y `REGLAS CALCULO` del Excel y no hay ninguna. Los 10 hitos perdidos no traen motivo ni en el catálogo ni en texto. **Pero la opción de registrarlo sí existe**, que era lo que se había pedido: el movimiento `NEG_PERDIDA` lleva comentario libre y además marca el hito como perdido. Los campos `motivo_perdida_id` y `motivo_perdida_detalle` del hito son andamiaje del diseño D0 que ninguna pantalla expone; no se agregó UI para ellos porque duplicaría lo que el comentario del movimiento ya hace, y definir las categorías es del negocio.

**El pipeline sí se puede usar desde la app.** Se verificó: la ficha del negocio tiene el componente que registra movimientos y muestra la línea de tiempo. Que haya 0 movimientos es falta de uso, no falta de pantalla.

### 2026-08-22 · Revisión y correcciones

Pasada de revisión pedida por el usuario. Cuatro cosas, la primera con riesgo real.

**1. `alembic revision --autogenerate` era un arma cargada.** `alembic check` reportaba 8 `modify_type` y 4 `remove_index`, y al mirarlos de cerca el desajuste era **al revés** de lo que parecía: la base tiene `bigint` y los índices, y los **modelos** los sub-declaraban. Cualquiera que generara una migración automática hoy habría producido una que **borra 4 índices de producción y angosta 8 columnas a `integer`** — degradando en silencio la bandeja y la línea de tiempo. Se corrigió del lado de los modelos, sin migración: `BigInteger` explícito y los índices declarados en `__table_args__`. `alembic check` quedó limpio.

Un detalle que salió de ahí: `BigInteger` en una clave primaria rompe el autoincremento de SQLite, porque solo `INTEGER PRIMARY KEY` es alias de rowid. Se usa `BigInteger().with_variant(Integer, "sqlite")`, verificando el DDL de los dos dialectos: `BIGSERIAL` en Postgres, `INTEGER` en SQLite.

**2. `fecha_cierre` en 12 hitos que nunca cerraron.** Perseguí el defecto que había reconocido en el gráfico "Negocios por mes" y el origen resultó estar más abajo: **el Excel duplica su única fecha en las dos columnas**, en todas las filas, incluidas las 2 marcadas "Activo" y las 10 "Perdido". VVP-15, activo, dice inicio 2026-01-06 y cierre 2026-01-06. El cargador fue fiel al origen, como corresponde, así que copió la duplicación.

Se limpió por migración (`d1f4a72b6e59`): 12 hitos. No se pierde nada — el valor era una copia de `fecha_inicio`, que sigue ahí — y **los tres buckets no se movieron un peso**: ganado 8.087.861,69, pipeline 1.824.272,06, potencial perdido 4.751.490,69.

**3. Un negocio perdido envejecía para siempre.** Al limpiar lo anterior apareció el caso: un negocio caído en enero, sin fecha de cierre, mostraba "lleva 8 meses abierto" y el número crecía solo. Ahora hay tres casos explícitos —sigue abierto, cerró con fecha, se resolvió sin fecha— y el tercero devuelve nulo. El parámetro `abierto` va **sin valor por defecto** a propósito: con un default, pasar una fecha de cierre y olvidar el flag hace que la fecha se ignore en silencio, error que cometí al escribir el primer test de esa función.

**4. El gráfico ahora avisa de su propio límite.** "Negocios por mes" agrupa por fecha de inicio, y en los migrados esa fecha es la de cierre. No se puede corregir —no hay dato con el que corregirlo— pero se cuenta: el gráfico dice "6 de 18 vienen del Excel con la fecha de inicio igual a la de cierre". El aviso **desaparece solo** cuando el número llegue a cero.

**Y se limpiaron cuatro restos de la plantilla de Vite**, todos muertos y ninguno referenciado:

| Archivo | Qué era |
|---|---|
| `src/index.css` | 111 líneas que contradecían el sistema de diseño: acento morado `#aa3bff`, ancho fijo de 1126px, texto centrado |
| `src/assets/vite.svg` | El logo de Vite, con su `<title>Vite</title>` |
| `src/assets/hero.png` | Imagen del starter, 343×361 |
| `public/icons.svg` | Sprite de iconos sociales (Bluesky y compañía), servido en `/icons.svg` |

Que el hash del CSS compilado no cambiara al borrar el `index.css` confirmó que estaba muerto de verdad. El directorio `src/assets/` quedó vacío y se eliminó.

**Lo único que queda de la plantilla es `favicon.svg`**, que sí se usa: es el ícono violeta de la pestaña, y no es la marca. Se deja porque reemplazarlo es una decisión de diseño: el `logo.png` es un wordmark de 6341×1178 que a 16 px sería una mancha, y no hay un SVG de la marca en el repo del cual derivar el ícono.

389 tests, `alembic check` limpio.

### 2026-08-22 · El reporte mensual pasa a ventanas móviles

Segundo paso de lo que pidió el usuario. El reporte que se había entregado el día anterior comparaba mes contra mes, y **medía ruido**: de 11 meses con actividad, 4 estuvieron vacíos (36%), y el ticket varía cuatro veces —entre 516.304 y 2.110.526—. Con ~1 cierre por mes y esa dispersión, la variación mensual no dice nada del desempeño.

**El argumento en una tabla**, con los datos reales:

| Mes | Cierre del mes | Móvil 6 meses |
|---|---:|---:|
| 2025-11 | **0** | 3.154.681 |
| 2025-12 | 2.110.526 | 5.265.206 |
| 2026-01 | **0** | 5.265.206 |
| 2026-02 | **0** | 3.497.130 |
| 2026-03 | 1.057.477 | 4.554.607 |

La columna del mes es ilegible. La de seis meses cuenta algo: subió a 5,2M en diciembre y viene bajando.

**Lo que quedó** (`D-043`):

- **Titular: ventana móvil** contra la anterior del mismo largo, **sin solaparse** — si se solaparan, el mismo cierre contaría en los dos lados y la variación saldría diluida. El largo es un control de 3, 6 o 12 meses, porque el horizonte correcto depende de qué se mire.
- **Año corrido** contra el **mismo tramo** del año pasado, no contra el año entero: comparar ocho meses contra doce diría que el año viene mal cuando solo viene incompleto.
- **El mes calendario baja a detalle** de "qué cerró".

**Lo que se sacó: la comparación mes contra mes**, que era justo el ruido a eliminar. Y el "mismo mes del año pasado" tampoco quedó: la estacionalidad necesita dos o tres años para ser medible, hoy compararía 1 contra 0.

**Y el rediseño mostró algo que el mensual no podía:** en los últimos 6 meses las liquidaciones subieron 100% (4 contra 2) mientras la comisión real bajó 19,3%. Más cierres con ticket más chico — un hecho del negocio que la vista mensual escondía.

De paso: `HTTP_422_UNPROCESSABLE_ENTITY` está deprecado en esta versión de Starlette; se cambió al nombre nuevo. Salió de un warning en los tests, que fallan ante SAWarnings pero no ante estos.

42 tests en el archivo del mensual, 387 en total más el `xfail` conocido.

### 2026-08-22 · Duraciones de negocios y bandeja de negocios

Pedido del usuario, después de notar que el mes calendario no es la unidad natural de este negocio: los procesos duran de un mes a varios, así que hacía falta ver **desde cuándo** viene cada negocio y **cuánto lleva sin moverse**.

**El hueco era grande y medible:** la tabla de Negocios no tenía **ninguna** columna de fecha. Código, propiedad, modelo, etapa, alianza, estado, comisión. No había forma de saber si un negocio llevaba una semana o siete meses.

**Tres duraciones, no una** (`D-042`). Un negocio puede llevar seis meses abierto y estar avanzando perfecto; otro puede llevar dos meses y estar muerto. Una sola cifra no distingue esos casos:

| Cuál | Cómo sale | Qué responde |
|---|---|---|
| Abierto | hoy − fecha de inicio | "lleva 4 meses" |
| Sin gestión | hoy − último movimiento | "3 semanas que nadie lo toca" |
| En la etapa | hoy − último cambio de etapa | "2 meses trabado en E4" |

**La "última gestión" es la del último movimiento, no `actualizado_en`.** Esa columna existe y se mueve con cualquier edición: corregir una dirección mal escrita haría que un negocio parezca activo sin que haya pasado nada. Un timestamp técnico disfrazado de señal de negocio es peor que no tenerlo, porque nadie sospecha de él.

**Bandeja de negocios**, dentro de "Qué me toca hoy" con un selector Canjes / Negocios — el mismo patrón que los dashboards de Inicio. Van separados porque los relojes son distintos: canjes se mide en horas, negocios en meses. Los umbrales son **30 y 14 días**, y son una estimación mía, igual que el de estancado del reporte semanal; por eso viven en el código y no en `CONFIG`.

**Un error propio, encontrado al mirar el resultado real.** El listado devolvía `dias_abierto = 0` para VVP-1, que empezó en agosto de 2025, y la tabla lo pintaba como "hoy". La causa: cuando inicio y cierre coinciden yo daba la duración del cierre como desconocida pero la de "abierto" como cero — la misma mentira con otro nombre. **No sabemos que cerró el día que empezó; sabemos que el Excel traía una sola fecha.** Ahora las dos son nulas, y el test que decía lo contrario quedó corregido con la explicación.

**Lo que el dato honesto deja a la vista:** de los 18 negocios, **15 no tienen duración calculable** y solo 3 sí. Y aparece un dato verdadero que estaba escondido: **VVP-3 tardó 83 días** de la promesa a la escritura, porque es el único histórico con dos fechas distintas. Los 2 activos llevan 228 y 120 días abiertos, ambos sin una sola gestión registrada.

Eso último no es un defecto de la app: es que el pipeline nunca se usó. Y es exactamente el incentivo para empezar a usarlo, porque de ahí sale la duración de ciclo y la conversión por etapa que le faltan al reporte mensual y a la proyección del directorio.

24 tests nuevos, 370 en total.

### 2026-08-21 · Sprint 17 (F4) — Listo · reporte mensual comparativo

Pantalla nueva en `/reportes/mensual`: el mes contra **dos** referencias.

**Las dos van juntas porque responden cosas distintas.** El mes anterior dice si la tendencia corta sube o baja; el mismo mes del año pasado dice si eso es tendencia o es estacionalidad. Con una sola no se distingue "vamos mal" de "agosto siempre es flojo".

**La variación contra cero es nula, no infinita** (`D-041`). Es exactamente el criterio del sprint: un mes sin datos no rompe la comparación. Si el mes de referencia estuvo en cero no hay porcentaje que calcular, así que se devuelve nulo y la pantalla muestra "nuevo" con la diferencia absoluta, que sí significa algo. Poner "+300%" o "+∞" sería inventar un número.

**No hay serie de veinticuatro meses acá**, a propósito: eso ya está en los gráficos "por mes" del dashboard y responde otra pregunta.

**Cada dominio se mide por lo que le corresponde.** Negocios: lo cerrado por `fecha_cierre` (cuándo entró la plata) y lo iniciado por `fecha_inicio` (el indicador que se adelanta), contando el negocio una vez, en el mes de su hito más antiguo. Canjes: solicitudes por `fecha_solicitud`, cierres por `fecha_cierre`.

**Un límite del dato que hay que decir:** los canjes cancelados se cuentan **por fecha de solicitud**, no por fecha de cancelación, porque `canjes` no guarda cuándo se canceló. La pregunta que responde es "de los que entraron este mes, cuántos terminaron cancelados". Y ahora, después de la limpieza, esa cifra es **igual a la de solicitados en todos los meses pasados**, porque todo lo que entró quedó cancelado. Es cierto y es consecuencia de la limpieza, pero como métrica de historia no informa nada hasta que entren canjes nuevos.

Sobre los datos reales de junio 2026 contra mayo: comisión real −9,8%, liquidaciones sin cambio, canjes solicitados −53,6%. El caso "sin base" aparece solo, en canjes cerrados: 0 contra 0.

25 tests nuevos, 346 en total.

### 2026-08-21 · Sprint 22 (G1) — Listo · reset de contraseña

Reset por admin con cambio forzado en el primer ingreso, como se aprobó. **Sin correos**: no hace falta proveedor de mail ni credenciales de nada.

**La decisión que sostiene todo: la guarda está en la API, no en la pantalla** (`D-040`). Con la clave temporal puesta, `get_current_user` devuelve 403 en **todos** los endpoints salvo tres: ver quién soy, cambiar la clave y salir. Si el bloqueo lo aplicara solo el front, la clave temporal serviría para usar toda la API con cualquier cliente y el sprint entero sería decorativo.

Los tres exentos usan una dependencia aparte, `resolver_usuario`. El caso que obliga a separarlas: con la dependencia estricta, la persona quedaría bloqueada **del único endpoint que la desbloquea**.

**El reset cierra las sesiones abiertas de esa persona.** Sin eso, una pestaña ya logueada seguiría con todos los permisos hasta doce horas y el cambio forzado no se aplicaría nunca — el flag solo se mira al resolver la sesión.

**La clave la genera el sistema**, 12 caracteres, sin `I`, `l`, `1`, `O` ni `0` porque se dicta por teléfono o se copia de un chat. Se muestra una sola vez; lo guardado es su hash. La elige el sistema y no el admin porque una inventada en el momento termina siendo "viveprop2026", y hay que transmitirla por un canal aparte igual.

**Nadie puede resetear su propia clave.** Si el único admin se reseteara y perdiera el texto que aparece una vez, quedaría fuera de la app sin nadie que pueda ayudarlo.

**De paso se destrabó una deuda de tests.** `sesiones` quedaba fuera de la base de test porque su clave primaria usaba el `UUID` del dialecto de Postgres, así que **toda la capa de autenticación estaba sin cubrir**. Se cambió a `sa.Uuid`, que emite el mismo `UUID` nativo en Postgres —verificado comparando el DDL— y un `CHAR(32)` en SQLite. Ahora la cadena completa se prueba: cookie, sesión, ventana deslizante y guarda.

Verificado además punta a punta contra `dev`: sesión viva antes del reset, muerta después, login con la temporal, 403 en todo, cambio, y 200. 21 tests nuevos, 321 en total.

**Anotado y no arreglado:** `alembic check` reporta desalineamiento preexistente entre modelos y base — `BigInteger` en los modelos contra `Integer` en varias columnas, e índices declarados en migraciones pero no en los modelos. Ninguno es de este sprint y ninguno rompe nada hoy; queda dicho para no redescubrirlo.

### 2026-08-21 · `/api/health` dice qué commit está corriendo

Chico, y sale de una molestia repetida: **tres veces en el día hubo que adivinar si lo desplegado era lo que se había subido, y dos de esas la respuesta fue "no"** — el backend local sin `--reload`, y el `200` con HTML que se leyó como endpoint desplegado. Cuando un deploy no cambia el frontend, el hash del bundle no sirve para distinguir nada y no queda ninguna señal.

Ahora `/api/health` devuelve `{"status": "ok", "commit": "abc1234"}`, del `RENDER_GIT_COMMIT` que Render pone en el ambiente. En local dice `local`, que es la respuesta correcta: no hay commit desplegado que reportar.

Se expone sin sesión, como el resto del endpoint. En un repositorio privado un SHA no abre ninguna puerta, y poder verificar un despliegue en un segundo vale más que esconderlo.

### 2026-08-21 · Los datos históricos van a producción por migración

El hueco más grande que quedaba: producción tenía los canjes y la UF, pero **Negocios vacío**. Los 18 negocios, sus 19 hitos, sus 114 obligaciones y los 384 movimientos del seguimiento del Excel vivían solo en `dev`, así que nueve sprints de funcionalidad no tenían nada que mostrar allá.

Se resolvió con el mismo mecanismo que la limpieza de canjes: **una migración que se aplica sola en el deploy**, sin necesitar la credencial de la base.

**Los datos van en `alembic/datos/historicos.json`** (154 KB), generado desde `dev` por `app/scripts/exportar_historicos.py`. Meter 550 filas de negocios reales en el cuerpo de la migración la volvería ilegible y mezclaría el paso de carga con los datos que carga.

**Los montos se cargan tal cual, sin pasar por el motor** (`D-026`). Siete de estos negocios están cerrados con plata ya facturada y `VVP-2` viene descuadrado del origen; recalcular cambiaría en silencio números ya cobrados. Verificado: se compararon las 19 filas contra el export en `comision_total`, `comision_real_vp` y `uf_snapshot`, **cero diferencias**.

**Las referencias a catálogos van por código, no por id.** Los ids son seriales que asignó la migración de catálogos; corrió igual en las dos bases, así que *deberían* coincidir — pero "deberían" no alcanza cuando el resultado sería un negocio atribuido a la alianza equivocada sin que nada falle.

**Lo que se probó en `dev`, en este orden:**

| Prueba | Resultado |
|---|---|
| `downgrade` | borra los 164 registros y los 384 movimientos, y **no toca** los 221 de la limpieza |
| `upgrade` | vuelve a cargar todo, con los montos idénticos al export |
| `upgrade` con datos ya presentes | saltea los 18, no inserta nada, 4,6 s |
| Corte a mitad de camino | el primer intento se pasó de tiempo y **quedó todo revertido**: la migración es atómica |

**Dura unos dos minutos**, y conviene saberlo para no pensar que el deploy se colgó. El costo son 50 `INSERT ... RETURNING` secuenciales contra Neon a ~180 ms el viaje. Los inserts masivos —384 movimientos y 114 obligaciones— sí se agrupan en tuplas de 100, porque el `executemany` de SQLAlchemy sobre un `text()` no agrupa: manda una fila por statement. Corre una sola vez, así que no valía optimizar más.

**No se exportaron los movimientos de la limpieza de canjes**: producción ya generó los suyos sobre sus propios datos, y traer los de `dev` los duplicaría.

### 2026-08-21 · El selector de Inicio usa el coral de "estás acá"

Pedido del usuario: que el botón activo del selector se vea como el enlace activo del menú, sin cambiarle la forma.

Se resolvió con una línea, `color="accent"`. Mantine ya calcula el texto blanco cuando el control recibe un color —`getContrastColor` devuelve blanco si `autoContrast` está apagado, que es el default— así que no hizo falta CSS propio. El coral es el mismo `#F4545A` que usa el menú: los dos resuelven a `accent.6` vía `primaryShade`, así que coinciden por construcción y no por copiar un hex.

Único efecto lateral: el pill activo pierde la sombra sutil que Mantine le pone cuando no hay color. No es un cambio de forma, y el menú tampoco tiene sombra, así que quedan parejos.

### 2026-08-21 · Los dos dashboards en Inicio, y "Negocios por mes"

Pedido del usuario. **Inicio hospeda los dos dashboards** con un selector Canjes / Negocios, y desapareció "Dashboard Negocios" del menú porque ya vive ahí. La ruta `/negocios/dashboard` sigue funcionando para links guardados, con su propio encabezado.

**No van uno debajo del otro, y eso fue deliberado.** Son dos tipos de gestión con métricas que no se comparan entre sí; apilarlos invitaría a leerlos como un solo tablero. El selector los mantiene separados.

**Gráfico nuevo: "Negocios por mes"**, el equivalente de "Solicitudes por mes" de canjes, con filtros por modelo de negocio y por tipo de operación.

Tres decisiones que definen qué mide:

- **Cuenta negocios, no liquidaciones.** `VVP-3` tiene promesa y escritura en meses distintos; contarlo dos veces diría que hubo dos negocios cuando hubo uno. Cada negocio cae en el mes de su hito más antiguo.
- **Agrupa por `fecha_inicio`, no por `fecha_cierre`.** Mide **cuánto entró**, no cuánto se cobró. Lo cobrado ya está en el gráfico de comisión por mes del mismo dashboard, que agrupa por cierre. Son dos preguntas distintas sobre el mismo mes, y por eso el nuevo va **arriba** del otro: primero cuántos entraron, después cuánto se cobró.
- **Incluye los perdidos.** Un negocio que se cayó igual entró ese mes. Sacarlo haría que el pasado se encogiera cada vez que algo se pierde.

**Interpretación que hice de "tipo de mercado y negocio":** los filtros quedaron en **modelo de negocio** —cuyos nombres ya dicen primario o secundario— y **tipo de operación** (venta / arriendo). Si querías otra cosa por "negocio", es un cambio chico.

Los dos desplegables se llenan desde `/api/catalogos`, no de listas escritas en el código: una alianza o una operación nueva aparece sola.

Sobre los datos reales de `dev`: 18 negocios en 9 meses, con enero de 2026 concentrando 8. Filtrado por concentradores quedan 13, por arriendo 2. 11 tests nuevos, 300 en total.

### 2026-08-21 · Limpieza de canjes: va como migración, se aplica sola en producción

Pedido del usuario: en Dataprop quedan **seis solicitudes vivas** —334, 344, 359, 360, 364, 367— y la base arrastra 225 activas, así que la app muestra como pendiente trabajo que no existe.

**Tres cosas aparecieron al mirar los datos antes de escribir nada:**

1. **#364 y #367 no existen en la base.** El último canje que tenemos es el #360, del 2026-08-10, la fecha del último export de Dataprop. Esos dos son posteriores: hay que importarlos, no marcarlos.
2. **31 de los que se cancelarían tienen etapa `CERRADO`.** Se advirtió que marcarlos cancelados pierde la distinción entre "se cayó" y "se concluyó", y que la reportería pasaría a decir que nunca se cerró un canje. **La decisión del usuario fue cancelarlos igual.** Se respeta: son los 221 completos. Mitiga el daño que la etapa **no se toca**, así que la información sigue guardada y el cambio es reversible.
3. **`dev` y producción ya no coinciden.** Según la captura del usuario, producción tiene 78 cancelados y `dev` 72: seis canjes que se cancelaron en Dataprop después de que se creó la rama.

**El script va por el mismo camino que la app**: registrar un movimiento `CANCELACION`, que es lo que pone el estado y marca `gestionado_en_app`. Con eso la línea de tiempo explica el cambio — sin el movimiento, quien abra el canje #150 en seis meses ve CANCELADO sin ninguna razón. Contra la base va en **una sola transacción**, para que no quede media limpieza aplicada.

**La limpieza sobrevive a las importaciones**, y eso no era obvio: el importador de Dataprop nunca toca `estado` ni `etapa`, y además saltea los canjes con `gestionado_en_app`. Subir un `.xlsx` viejo no revive lo cancelado.

**Dos transportes.** Contra la base con `DATABASE_URL`, o contra la API de un despliegue con una cookie de sesión. El segundo existe porque para tocar producción **una cookie es una credencial mejor que el string de conexión**: vence, se revoca cerrando sesión y no da más permisos que los del usuario. El costo es que va canje por canje y se puede cortar a medias, así que saltea los que ya están cancelados y se puede volver a correr.

**Aplicada en `dev`**: 221 canjes cancelados, quedan activos exactamente 334, 344, 359 y 360. Verificado en los tres lugares donde se ve:

| Dónde | Antes | Después |
|---|---|---|
| Estados | 225 activo / 72 cancelado | **4 activo / 293 cancelado** |
| Bandeja "Qué me toca hoy" | 146 sin gestión + 48 crítico | **4 filas**, los cuatro vigentes |
| Dashboard de canjes | tasa activos 63,3% | tasa activos 1,3% |

Los 221 movimientos quedaron en la línea de tiempo con su explicación, y los 31 con etapa `CERRADO` conservan su etapa: siguen siendo `CERRADO` + `CANCELADO`, así que la información de que se concretaron no se perdió y el cambio se puede revertir buscando esos movimientos.

**Consecuencia visible, ya que estaba anunciada:** el dashboard ahora dice tasa de activos 1,3% y cuenta 293 cancelados, de los cuales 31 en realidad se concretaron. Era el costo de la opción elegida; queda dicho acá para que nadie lo lea como un dato de negocio.

**Para producción se convirtió en migración** (`a4e81b6f30c9`). Pedir credenciales tres veces no era entregar: la migración es la única vía que alcanza producción sola, en el deploy, y es el mismo mecanismo que ya lleva allá los catálogos y los tipos de movimiento. El script queda igual, para simulacros y para dejar `dev` al día.

**Por qué es segura de aplicar a ciegas:**

- **Idempotente.** Solo mira los que están `ACTIVO`, así que correrla dos veces no hace nada la segunda. Verificado.
- **Se adapta a cada base.** En `dev` cancela 221; en producción menos, porque allá hay seis cancelaciones más que la rama no tiene. La condición es por exclusión, no una lista de IDs a cancelar.
- **Reversible de verdad.** El `downgrade` devolvió `dev` a 225/72, el estado exacto de antes. Revierte por el movimiento que dejó, no por exclusión: si alguien cancela otros canjes después, no se los lleva puestos.
- **La clave foránea no puede fallar.** `CANCELACION` se siembra en la migración `b2dbf50bc5fc`, así que existe en producción.
- **Si algo falla, falla el deploy.** `alembic upgrade head` está en el `buildCommand`, así que un error deja producción sirviendo la versión anterior en vez de a medio camino.
- **`autor_id` va nulo.** No lo hizo una persona; firmar con la cuenta del admin sería decir algo que no pasó.

Probada en `dev` en los dos sentidos y dos veces seguidas hacia arriba, con el mismo resultado.

### 2026-08-21 · Sprints 14 y 15 (E1, E2) — Listos · serie E completa

**Carga masiva de negocios**, desde el botón *Carga masiva* de la pantalla de Negocios. Los dos sprints van en un solo modal porque bajar la plantilla y subirla es el mismo trabajo partido en dos; separarlos obliga a buscar dónde estaba el otro.

**La decisión de fondo: la plantilla pide entradas, no resultados** (`D-039`). No hay columnas de comisión total, broker ni real VP — eso lo calcula el motor con el valor y las tasas. Tenerlas sería dejar que alguien escriba un número a mano y perder la garantía que el motor existe para dar. Hay un test que se cae si alguna vez aparecen.

**Una fila es un hito, no un negocio.** Código repetido = más hitos del mismo negocio, como `VVP-3`. Y los datos de nivel negocio tienen que coincidir entre esas filas: si la fila 5 dice una dirección y la fila 8 otra para el mismo código, es error, porque no hay forma de saber cuál gana.

**Las tasas se escriben en porcentaje**, 2 para 2%. Pedir `0,0252001208200461` en una planilla es pedir que alguien se equivoque; convertir acá es una división.

**Los códigos válidos van en una hoja generada desde la base**, no escrita a mano. Una alianza nueva aparece sola en la próxima plantilla, y las inactivas no se ofrecen. Es la misma razón por la que los desplegables del front salen de la API.

**Tres reglas que vienen de la carga de UF, por los mismos motivos:** si hay un solo error no se escribe nada; cargar dos veces actualiza en vez de duplicar; y **nunca borra** — si la base tiene dos hitos y el archivo trae uno, el otro se queda, porque un import que borra lo que no menciona convierte un archivo incompleto en pérdida de datos.

**Esto no sirve para los 19 históricos**, y conviene que quede dicho: esos se migran fieles y sin recalcular (`D-026`) porque siete están cerrados con plata facturada y `VVP-2` viene descuadrado del origen. Para eso sigue estando `scripts/cargar_negocios.py`.

**El test que más vale es la vuelta completa**: bajar la plantilla de verdad, llenarla y cargarla. Los otros arman el `.xlsx` a mano y comparten la suposición de cómo es la plantilla; ese usa la real, con sus dos filas de encabezado y sus celdas combinadas. Cualquier desajuste entre generador y parser aparece ahí y en ningún otro lado.

Verificado además por HTTP contra `dev` con un negocio de prueba que después se borró: carga, y al subirlo de nuevo actualiza sin duplicar. 32 tests nuevos, 289 en total.

### 2026-08-21 · Carga de historia de UF desde el SII

**La mitad del hueco de producción se puede cerrar sin credenciales.** El SII tiene una página por año y devuelven 200 para 2022, 2023, 2024, 2025 y 2026, así que la historia completa de UF se puede traer desde la app: botón **"Traer toda la historia"**, `POST /api/uf/cargar-historia`.

Va aparte de la actualización diaria porque son dos operaciones distintas: esta baja cinco páginas y es deliberada, la otra baja una y corre sola. Bajar cinco años no es algo que un tick diario deba hacer en silencio.

**Trae años completos, y eso cambió un número.** Al correrlo contra `dev` aparecieron **304 fechas nuevas**: todo 2022 antes de noviembre, que la carga original del sprint 3 excluyó porque el primer canje es de 2022-11. La serie de `dev` pasó de **1.409 a 1.713 filas**, de 2022-01-01 a 2026-09-09. Se dejó así: un corte a mitad de año es más complejo que traer el año entero, y sin esas fechas un negocio con fecha de mediados de 2022 no se podría valorizar.

**Un año caído no aborta el resto.** Si el SII no tiene 2024, se cargan los otros cuatro y se informa cuál faltó. Pero si no se pudo leer **ninguno**, eso sí es error: "el SII no publicó 2027" y "el SII está caído" se arreglan distinto. Y un año que responde con otro formato aborta todo sin escribir nada, igual que la carga diaria.

10 tests nuevos, 257 en total.

**Lo que sigue faltando en producción:** los 18 negocios y los 384 movimientos de canjes. Esos no tienen fuente externa, así que necesitan o el `DATABASE_URL` de producción o el importador de negocios de los sprints 14-15.

### 2026-08-21 · Hallazgo: los datos históricos están en `dev`, no en producción

Salió al verificar el deploy. **No es un defecto introducido, es un estado que el despliegue dejó a la vista.**

Hay dos formas en que los datos llegaron a la base, y solo una alcanza producción:

| Qué | Cómo entró | ¿Está en producción? |
|---|---|---|
| Catálogos, etapas, tipos de movimiento | Sembrados en migraciones | **Sí** — Render corre `alembic upgrade head` en cada deploy |
| Canjes (297) | Importados antes del plan | **Sí** |
| UF (1.409 filas, desde 2022-11) | `scripts/cargar_uf.py` contra `dev` | **No** — resuelto el mismo día: se puede traer del SII desde la app |
| Negocios (18 negocios, 19 hitos, 13 propiedades, 114 obligaciones) | `scripts/cargar_negocios.py` contra `dev` | **No** |
| Seguimiento de canjes (384 movimientos) | `scripts/migrar_seguimiento_canjes.py` contra `dev` | **No** |

Estaba anotado desde el sprint 3 —"aplicada a `dev`, no está en producción todavía"— pero referido a la migración, que sí entró. Los **datos** que cargaron los scripts no.

**Qué implica para lo que se ve en producción:** Negocios vacío y su dashboard en cero; la bandeja mostrando todos los canjes abiertos como "sin gestión", sin el corte 146/48; el reporte semanal casi vacío. Los canjes sí funcionan.

**Un efecto lateral del sprint 23:** como la tabla de UF de producción estaba vacía, la tarea automática la encontró sin colchón y descargó — pero el SII solo cubre el año en curso, así que producción quedaría con 2026 y sin 2022–2025. Suficiente para valorizar hoy, insuficiente para un negocio con fecha de 2025.

**No se tocó producción.** Cargar datos ahí es una operación de una sola vía y necesita autorización explícita. Queda propuesto como próximo paso.

### 2026-08-21 · Sprint 23 (C5) — Listo · la UF se carga sola

**Ya no hay que subir la plantilla cada mes.** Una tarea dentro del propio web service chequea una vez al día si a la serie le quedan menos de 20 días por delante y, si es así, baja lo que el SII publica.

**Por qué el SII y no las otras dos** (`D-036`). Se probaron las tres antes de escribir código. El SII se verificó contra la serie que ya estaba en Neon —que viene del Excel, un origen independiente— y coincidió en **617 fechas de 617, al centavo**, entre 2025 y 2026. `mindicador.cl` no respondió en dos intentos desde acá. El Banco Central es la fuente de origen y tiene API JSON de verdad, más robusta que parsear HTML, pero exige registrarse y guardar credenciales; queda anotado como el camino de mejora si esto se vuelve frágil.

**El detalle que habría fallado en once meses.** Las páginas del SII son una por año y la del año siguiente devuelve 404 hasta que la publican. En la segunda mitad de diciembre los valores de enero viven en la página del año que viene, así que en diciembre se piden los dos años y el 404 no es un error. Y en enero se pide también el año anterior, porque si esto no corrió unos días sobre el cambio de año diciembre quedaría con un hueco — y un hueco en el medio de la serie no lo avisa nadie: el aviso de vencimiento mira la última fecha, no los agujeros.

**Dos cosas que se arreglaron mientras se construía:**

- **La tarea corría muda.** El primer arranque no dejó ninguna línea en el log: uvicorn configura handlers solo para sus propios loggers, así que el `log.info` nuestro se descartaba. Un proceso automático sin evidencia de haber ocurrido es el mismo problema silencioso de `D-033`. Se configura el logging en el arranque.
- **La tarea se habría levantado en los tests.** `TestClient` como context manager corre el lifespan de verdad, así que cada test habría salido a internet y escrito en Neon. Hay un interruptor (`tareas_de_fondo`) que el conftest apaga.

**Verificado en vivo, no solo por test:** se reinició el backend y la tarea se disparó sola a los 30 segundos, bajó la página del SII con un 200 y registró "0 nuevas, 0 actualizadas, serie hasta 2026-09-09" — nada nuevo porque la serie ya estaba completa, que es la respuesta correcta.

27 tests nuevos, 247 en total. **Ninguno sale a internet**: corren contra un recorte real de la página del SII guardado en `tests/datos/`.

**La carga manual se queda como respaldo**, y los dos caminos escriben con el mismo upsert (`guardar_serie`), así que la automatización no puede dejar la serie en un estado que la carga a mano no produciría.

### 2026-08-21 · Unidad de Fomento pasa al grupo ADMIN

Pedido del usuario. El enlace estaba en OPERACIONES y ahora está en ADMIN, junto a Usuarios.

**Ojo, esto cambia quién lo ve:** el bloque ADMIN se dibuja solo si `usuario.rol === 'admin'`, así que gerencia y operaciones pierden el enlace. **La ruta `/uf` sigue accesible por URL para operaciones**, que puede editar (`puedeEditar={usuario.rol !== 'gerencia'}`). Mover el menú y restringir el acceso son dos cosas distintas; se hizo solo la primera, que es la que se pidió. **Resuelto el mismo día:** el usuario eligió restringir también la ruta, así que `/uf` es solo admin y las escrituras del backend (`plantilla`, `importar`, `actualizar-desde-sii`) exigen rol admin. `/estado` queda abierto a todos: lo consulta el aviso que ve cualquiera en la página de Negocios. El riesgo de tener un solo punto de rescate humano pesa mucho menos ahora que la serie se actualiza sola (`D-038`).

### 2026-08-21 · Sprint 2 (G2) — En curso

**El sprint chico de despliegue destapó tres cosas que ya estaban en producción.** Ninguna se buscaba; salieron de mirar el servido con atención.

**1. La cookie de sesión podía salir sin `secure` y nadie se enteraba** (`D-033`). Estaba condicionada a `ENVIRONMENT == "production"`. Si esa variable faltaba en Render o venía con un typo, la cookie de sesión viajaba sin `secure` sobre HTTPS y **la app seguía funcionando idéntica** — el peor tipo de falla, la que no se manifiesta. Se dio vuelta: solo `development`, `local` y `test` la desactivan, y un typo ahora rompe el login **en local**, ruidoso y en el lugar correcto.

**2. Un `/api/...` inexistente devolvía 200 con el HTML de la SPA** (`D-034`). Verificado en producción: `/api/esto-no-existe` respondía `200 text/html`. Un cliente que pega en un endpoint mal escrito recibe HTML donde espera JSON, y el error se manifiesta lejos de su causa. **Me engañó a mí mismo primero**: chequeé `/api/health/db` contra producción, vi un 200 y por un momento lo leí como que el endpoint nuevo ya estaba desplegado.

**3. El servido de archivos armaba la ruta con la URL sin revisarla.** `STATIC_DIR / full_path` con un `full_path` que sube de directorio apunta fuera de `static/`, y ahí abajo están el código y el `.env`. **Producción no está expuesta** — se probó directo: `/%2e%2e/.env` y `/%2e%2e/app/config.py` devuelven el `index.html`, porque uvicorn o el proxy de Render normalizan la forma codificada antes de que llegue al handler. Pero por `TestClient`, que no pasa por ese parser, el `../` llegaba entero y la lógica anterior servía el archivo. Se arregló igual: depender de que un proxy normalice no es una defensa, y ese comportamiento puede cambiar sin aviso.

**Lo que sí estaba en el plan:** el `<title>` dejó de decir `frontend` (el default de Vite), el `lang` pasó a `es`, se agregó `noindex`, y `healthCheckPath` quedó apuntado a `/api/health` en vez de la raíz. `/api/health` y `/api/health/db` se separaron (`D-035`): el que mira Render no toca la base a propósito, porque un despertar lento de Neon se leería como servicio caído.

12 tests nuevos, 220 en total. **Falta el dominio propio**, que necesita que lo agregues en Render y crees el registro DNS; después hay que sumar el dominio a `ALLOWED_ORIGINS` o el CORS lo rechaza.

### 2026-08-21 · Sprint 16 (F3) — Listo

**El primer reporte de período, y cubre los dos dominios.** Pantalla nueva en `/reportes/semanal`: qué se cerró, qué avanzó, qué se cayó y qué está estancado, en negocios y en canjes, con navegación por semana. Es lo contrario del dashboard —ese mira el estado actual, este mira los movimientos del período— y a propósito no repite las cifras de cartera: sumar lo mismo dos veces con dos cortes distintos es la forma más rápida de que nadie confíe en ninguna.

**Un filtro mal pensado, encontrado al probar contra `dev`** (`D-031`). La primera versión contaba como "avanzó" solo los movimientos que cambian de etapa. Sobre la semana del 10 al 16 de agosto dio **cero avanzados con 44 movimientos reales en la base**: los movimientos migrados del Excel llevan la etapa nula a propósito (`D-030`). Se corrigió a "toda actividad que no sea una caída", que además es lo correcto por sí solo: registrar la confirmación por WhatsApp del corredor propietario es progreso aunque la etapa no se mueva, y son ocho de los diez pasos del checklist. El test que fija esto nombra la regresión.

**El umbral de estancado quedó como control, no como constante** (`D-032`). Los 14 días son una estimación mía y nadie los definió; meterlos en `CONFIG` los haría parecer una regla acordada. En la pantalla hay 7 / 14 / 30 a un clic. Tampoco reusa los 48/24 horas de la bandeja: esa pregunta "qué me toca hoy", esta "qué se quedó atrás".

**Las listas vienen topeadas en 25 y los totales van aparte.** Con 188 canjes estancados, una lista truncada sin decirlo se leería como el total; la pantalla dice "se muestran 25 de 188".

Verificado punta a punta contra `dev` con una sesión real: el período, el rechazo de los períodos imposibles y el umbral por query. 30 tests nuevos, 193 en total con 1 `xfail`.

**Nota de ambiente:** el backend local corría sin `--reload`, así que no habría visto el router nuevo. Hubo que reiniciarlo a mano.

### 2026-08-21 · Sprint 21 (B7) — Listo · serie B completa

**El seguimiento histórico está en la base**: 384 movimientos repartidos en 112 canjes. Con esto el Excel deja de ser necesario para operar canjes.

**Tres tipos de movimiento que faltaban.** Al mapear las diez columnas del checklist apareció que el catálogo sembrado en B3 no cubría `Cliente calificado`, `Propiedad disponible` ni `Email registro solicitante` — el tercero una omisión evidente, porque existía `EMAIL_REGISTRO_PROPIETARIO` pero no su par. Sin ellos se habrían perdido 100 pasos ya completados. Se agregaron en la migración `f7d2c48b91a3`, que además reordena el catálogo completo siguiendo el orden real del proceso: un desplegable que no sigue el flujo de trabajo hace que la gente busque.

**El problema de las fechas, y qué se decidió** (`D-030`). La hoja registra **qué** pasos se completaron pero no **cuándo**: hay 287 marcas de "✓ Sí" y solo 69 filas con `Fecha último update`. Se migró un movimiento por paso, cada uno con la mejor fecha real del canje según su lado —gestión del solicitante, del propietario, o la del acuerdo—, y **el comentario de cada movimiento dice que la fecha es aproximada**. Ninguna fecha es inventada; lo aproximado es la correspondencia entre fecha y paso, y queda dicho en cada fila.

La alternativa era un solo movimiento por canje resumiendo todo, con fecha exacta. Se descartó porque perdería *cuáles* pasos están hechos, que es lo que hace falta para seguir desde donde se quedó.

**Lo que no se convirtió en movimiento:** los pasos marcados "✗ No" y las observaciones generales van juntos en un `COMENTARIO_GENERAL` por canje. Un "No" es información —que la propiedad no estaba disponible aparece 18 veces— pero no es un paso completado.

**La migración no mueve etapas.** `etapa_resultante` va nulo en todos: la etapa viene de Dataprop y es más confiable que reconstruirla del checklist.

**26 filas del Excel referencian canjes que no están en la base** y quedaron fuera, reportadas por el cargador. Son ids que existieron en Dataprop y no vienen en el export actual.

**El efecto que importa, en la bandeja:**

| | Antes | Después |
|---|---:|---:|
| Sin gestión | 194 | **146** |
| Crítico | 0 | **48** |

Esos 48 son casos reales de "se trabajó y se dejó estar", que antes eran indistinguibles de los que nunca se tocaron. Es exactamente la distinción que `D-029` buscaba poder hacer.

**Verificado en una ficha concreta:** el canje #324 muestra sus once movimientos en orden, con el acuerdo en su fecha propia y los demás en la de gestión, cada uno marcado como migrado.

### 2026-08-21 · Sprint 20 (B6) — Listo

**La bandeja diaria funciona.** Pantalla `/bandeja`, "Qué me toca hoy", primera en el menú de Operaciones. Sobre la base real: **194 canjes abiertos, los 194 sin gestión.**

**La decisión del sprint es `D-029`: cuatro niveles y no tres.** El semáforo mide horas sin gestión contra los umbrales de `CONFIG`, pero ningún canje tiene movimientos, así que medir desde `fecha_solicitud` habría dejado los 194 en rojo — incluyendo canjes de 2022. Una bandeja que abre con 194 filas rojas no informa nada.

`sin_gestion` quedó como nivel propio y va primero en el orden. "Nunca se tocó" es trabajo por empezar; "se tocó y se dejó estar tres días" es trabajo abandonado. Son problemas distintos y se resuelven distinto.

**Otras decisiones del cálculo:**

- Entran los canjes con `estado = ACTIVO` **y** etapa distinta de `CERRADO`: 194 de los 225 activos. Los 31 con etapa cerrada no son trabajo pendiente.
- Los umbrales son los **globales de `CONFIG`** (48 y 24 horas), no el `sla_horas` por tipo, que mide cuánto debería demorar *ese paso* y no cuánto lleva el canje sin que nadie lo mire.
- El semáforo cuenta desde el movimiento **más reciente**, así que un canje viejo con gestión de hoy está al día.
- Orden: primero lo que nunca se tocó, después lo más abandonado, y a igualdad de abandono el más antiguo.

**En la interfaz:** cuatro tarjetas de conteo, un filtro que arranca en "Requieren atención", y la tabla con la espera y la última gestión de cada canje. Cada nivel se muestra **con su palabra**, nunca con el color solo — `theme.ts` ya advierte que el coral de acento y el rojo crítico se parecen entre sí. Hacer clic en una fila abre el seguimiento que ya existía.

**22 tests**, total 163 más 1 xfail.

**Pendiente anotado, sin bloquear:** cinco tipos de movimiento tienen `sla_es_habil = true` (2 horas hábiles, 24 hábiles) pero `CONFIG` no define cuál es la ventana de horario hábil, así que ese campo no se usa todavía.

### 2026-08-21 · Sprint 19 (B5) — Listo, y ya lo estaba

**Al ir a construirlo se verificó que ya funcionaba desde el sprint B3.** No se escribió código.

Existen y funcionan: el servicio `crear_movimiento_canje`, los endpoints `GET` y `POST /api/canjes/{id}/movimientos`, los 14 tipos sembrados en `tipos_movimiento`, y el `SeguimientoModal` conectado a la página de Canjes con su línea de tiempo y su formulario.

Verificado de punta a punta contra `dev`: se registró un movimiento en el canje #349, avanzó de `EN_REVISION` a `PROCESO_DE_ACUERDO`, quedó en el historial con autor y fecha, y marcó `gestionado_en_app` para que la importación de Dataprop no lo sobreescriba. Después se revirtió.

**El diagnóstico que traía el plan estaba equivocado.** Se venía diciendo desde la auditoría inicial que "la infraestructura está construida y sin uso, hay que activarla". La segunda mitad es falsa: no hay nada que activar. Que la tabla esté en cero con 297 canjes cargados no es falta de código.

Lo que falta para que se use son los otros dos sprints del bloque: **sin bandeja diaria no hay razón para entrar a registrar un movimiento**, y sin el histórico migrado el Excel sigue siendo la referencia. Esos sí tienen trabajo.

### 2026-08-21 · Sprint 5 (C4) — Listo · serie C completa

**La UF se puede cargar desde la app**, sin scripts. Pantalla propia en `/uf` con el estado de la serie, descarga de plantilla y carga. Con esto la fecha límite del 9 de septiembre queda cubierta.

**La plantilla trae las fechas que faltan ya escritas** y el valor en blanco. Eso hace desaparecer la pregunta de "cuáles fechas tengo que llenar": se rellena la columna y se sube. Trae además una hoja de instrucciones. Si la serie estuviera vacía arranca en el día de hoy, porque no tiene sentido pedir cuatro años de historia a mano.

**Decisiones de la carga:**

- **Idempotente por fecha.** Subir un archivo solapado con lo ya cargado no duplica: actualiza lo que cambió y deja igual lo que no. El informe distingue nuevas, actualizadas y sin cambio, así que se ve qué pasó.
- **Si hay errores de formato no se carga nada.** Media serie subida sin saber cuál mitad es peor que no cargar. Los errores van por fila, con el número y el valor que falló.
- Acepta las dos convenciones de número: `40.885,63` y `40885.63`.
- Las filas de la plantilla que no se llenaron se ignoran sin ruido: no hay que borrarlas.

**Aviso y alerta** (`D-008`) en un solo componente, `AvisoUF`, que aparece en la página de Negocios y en su dashboard. Sin UF vigente no se puede valorizar, y eso rompe el alta, así que la alerta va donde duele y no escondida en el mantenedor. **Cuando la serie está sana no dibuja nada**: un aviso que se ve siempre deja de ser un aviso.

**24 tests**, total 141 más 1 xfail. Este módulo **pilotea el patrón** de plantilla e importador validador que reusan los sprints 14 y 15, así que sus tests valen para los tres.

**Nota técnica:** el upsert usa el ORM y no `ON CONFLICT` de Postgres, por la misma razón que el agrupamiento del sprint 12 se hace en Python: son 45 filas al mes, el rendimiento es irrelevante, y así el cálculo se puede testear contra la base en memoria.

**Nota operativa, tercera vez que pasa:** el reloader de uvicorn no detecta los archivos que escribo por script en Windows, y estuvo sirviendo código viejo. Conviene reiniciar el backend a mano después de agregar routers, en vez de confiar en `--reload`.

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
