# Viveprop Operaciones

App interna que reemplaza el seguimiento en Excel de dos procesos:

- **Canjes** (programa Dataprop) — importación manual (no automática) de un `.xlsx` exportado desde producción.
- **Negocios** (pipeline propio de Viveprop) — entrada 100% manual, con cálculo de comisiones por modelo de negocio.

Ambos módulos comparten login, roles (`gerencia < operaciones < admin`) y una tabla de `movimientos` (línea de tiempo por entidad) en vez de campos que se sobrescriben.

Plan de arquitectura completo (esquema SQL, sprints, apéndice de seguridad): ver el plan de diseño de esta app (fuera de este repo).

## Estructura

```
backend/    FastAPI + SQLAlchemy + Alembic
frontend/   React + Vite + TypeScript + Mantine
```

## Desarrollo local

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp ../.env.example ../.env    # completar DATABASE_URL con una Neon de desarrollo
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Tests:**

```bash
cd backend
pytest
```

Los tests corren contra SQLite en memoria, nunca contra Neon. `DATABASE_URL` debe
apuntar a la rama `dev` de Neon para desarrollo -- la de `production` solo vive en
las variables de entorno de Render.

Ojo con el string de conexion: Neon entrega `postgresql://...` y SQLAlchemy necesita
el driver, asi que hay que reemplazar ese prefijo por `postgresql+psycopg://`.

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

El frontend en dev apunta a `/api` vía proxy de Vite hacia `http://localhost:8000`.

**Ojo con el chequeo de tipos:** `npx tsc --noEmit` pasa en verde aunque haya
errores. El `tsconfig.json` de la raíz es un archivo de referencias y no incluye
ningún fuente, así que no revisa nada. El chequeo real es `npm run build`, que
corre `tsc -b`. Un archivo roto ya pasó ese falso verde una vez.

## Despliegue

Un solo Web Service en Render: build del frontend se copia a `backend/static/`, y FastAPI sirve tanto `/api/*` como el resto de rutas como SPA. Ver `render.yaml`.

Variables de entorno en Render:

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | La rama `production` de Neon. |
| `ALLOWED_ORIGINS` | Orígenes que acepta el CORS, separados por coma. **Al agregar un dominio propio hay que sumarlo acá** o el navegador rechaza las llamadas. |
| `ENVIRONMENT` | Decide si la cookie de sesión sale con `secure`. Solo `development`, `local` y `test` la desactivan; **cualquier otro valor, o su ausencia, deja la cookie segura** (`D-033`). No hace falta configurarla para estar seguro. |
| `TAREAS_DE_FONDO` | Opcional. Apaga las tareas periódicas del proceso si se pone en `false`. Hoy la única es la descarga de UF. |

**La UF se actualiza sola.** Una tarea dentro del web service chequea una vez al día si a la serie le quedan menos de 20 días por delante y, si es así, baja lo que publica el SII (`D-036`, `D-037`). La fuente se verificó contra 617 fechas sin una diferencia. Hay además un botón para traer la historia completa, un año por página desde 2022, para una serie que arranque tarde. La carga manual de la plantilla se queda como respaldo para cuando el SII no esté o cambie su página, y los dos caminos escriben con el mismo upsert. Solo admin puede cargar UF (`D-038`).

**Carga masiva de negocios.** Botón *Carga masiva* en la pantalla de Negocios: baja una plantilla `.xlsx` con los códigos válidos de esta base y la vuelve a subir. Una fila es un hito, las tasas van en porcentaje y **las comisiones no se escriben** — las calcula el motor (`D-039`). No es la vía para los 19 históricos: esos van con `scripts/cargar_negocios.py`, que migra fiel sin recalcular.

**Qué columnas espera cada archivo.** Los dos modales de carga --*Importar Canjes* y *Carga masiva*-- tienen un **«Ver estructura del archivo»** que abre la lista completa: las columnas agrupadas, cuáles son obligatorias, qué va en cada una, los valores que se aceptan y las trampas. Sale de la misma definición que genera la plantilla, así que la pantalla y el Excel no pueden divergir (`D-050`). Canjes también tiene plantilla para descargar, pero **no es para llenarla a mano**: el archivo sale de la query contra Dataprop, y la plantilla sirve para comparar encabezados cuando la carga falla.

**Cerrar y editar una liquidación.** En la ficha de un negocio, cada liquidación tiene su botón —*Cerrar o editar* si está activa— y hay uno para *Agregar liquidación*. El formulario manda **tasas, no montos**: la comisión total, la del broker, el rebate, el equipo y la real VP las calcula el motor al guardar, con la UF de la fecha de valorización. Un hito cerrado exige fecha de cierre y uno que no lo está no la puede tener: sin esa regla la plata queda en el bucket de ganado pero en ningún mes.

**Guardar una liquidación ya cerrada pide confirmación.** Si el recálculo movería alguno de sus siete montos, la API responde 409 y la pantalla muestra el monto de hoy y el que quedaría, con un botón *Guardar de todas formas*. Existe porque los 19 negocios del Excel se cargaron con los montos tal cual (`D-026`) y la API los pasa por el motor en cada guardado: había filas cuyas entradas no reproducían su propio monto, y abrir el formulario y guardar —sin tocar nada— les cambiaba la comisión. La migración `f5a92c3d81e6` dejó esas filas consistentes y `test_valorizacion_historica.py` lo vigila, pero la guarda protege el caso que ninguna carga futura puede descartar. Ver `D-046`.

**Canjes por etapa, con filtro.** En *Inicio*, el bloque «Canjes por etapa» tiene un selector **Todos · Activos · Cancelados**. Filtra al instante, sin volver a consultar: los diez números —cinco etapas por dos estados— vienen en la misma respuesta, de una sola consulta agrupada. Al lado va el total de la vista. Cuando hay canjes en estado ACTIVO con la etapa en Cerrado, la pantalla lo dice: el recuadro «Activos» de arriba los excluye, así que sin ese aviso el desglose sumaría más que el recuadro sin explicación (`D-051`).

**La secuencia del pipeline se valida.** Un negocio no puede llegar a E1 después de haber pasado por E3: la carga rechaza el negocio completo cuando las fechas contradicen el orden de las etapas, y señala cuál es la sospechosa. El historial se lee **de E1 hacia adelante**, con desempate por orden de registro para las etapas del mismo día (`D-068`).

**La comision de Dataprop.** Canjes tiene eje de plata, y es **de Dataprop, no de ViveProp**: la app lo dice en texto para que nadie la sume con la de Negocios. Tres cifras -- cobrada (registrada al cerrar), potencial y no concretada (calculadas con la regla: 2% por corredor en venta o medio mes cada uno en arriendo, y sobre eso el 6/5/4% por tramo en UF o el 8%). Todo neto. Mas los plazos, con las dos poblaciones que si se pueden medir (`D-072`).

**Filtrar por corredor o comuna, con sugerencias.** El listado tiene un filtro para el **corredor solicitante**, otro para el **propietario** y uno de **comuna** --son dos preguntas distintas y el mismo corredor cumple los dos roles--. Cada campo sugiere mientras se escribe, pero **no obliga a elegir**: «vicente» filtra igual. Las listas de opciones salen de un endpoint propio --las tres juntas-- y son el universo completo, no el listado ya filtrado, para que elegir un valor no haga desaparecer a los demás (`D-084`, `D-088`).

**Buscar un canje por su número.** El listado filtra por **N° de solicitud** --el `ID_CANJE` de Dataprop, el de la primera columna-- y lo hace **por prefijo**: «36» trae los 36x y «364» trae ese. Con igualdad exacta, escribir un número pasaría por estados intermedios con la lista vacía, que se leen como «no existe». Acepta pegar «#364» (`D-083`).

**Un canje arranca «En revisión».** El ciclo tiene **cinco** etapas --En revisión → Proceso de acuerdo → En oferta → En negocio → Cierre-- y ninguna es «Recepción»: existía para nombrar los canjes que Dataprop exportaba sin etapa, nadie pasaba tiempo en ella (los tramos daban 0 días) y los 75 que la tenían estaban todos cancelados. Se fueron a «En revisión», que es la primera etapa en la que alguien hace algo (`D-081`).

**Un canje puede estar cerrado.** El estado admite **Activo**, **Cerrado** y **Cancelado**. La etapa dice hasta dónde llegó el proceso y el estado en qué terminó: un canje puede llegar a la etapa de cierre y caerse igual, y eso pasó 31 veces en el histórico. El gráfico de solicitudes reparte el total del mes en los tres estados (`D-071`).

**Carga del historial de etapas.** Negocios → «Historial de etapas»: una plantilla **pre-llenada** con una fila por cada etapa desde E1 hasta donde está hoy cada negocio, para cargar hacia atrás cuándo pasó por cada una y desbloquear la proyección de plazos. No agenda seguimientos, no hace retroceder la etapa actual, recargar no duplica, y se niega a corregir una fecha de inicio si eso movería la valorización (`D-067`).

**La bitácora del pipeline va del más reciente al más antiguo**, igual que el historial de canjes activos: lo que se abre a mirar es en qué quedó el negocio. Dentro del mismo día desempata el orden de carga, así que E2 no puede aparecer sobre E1 por azar (`D-082`).

**Las dos fechas del avance de negocio.** El pipeline de la ficha registra cuándo pasó la actividad y cuándo es la próxima acción. La segunda es optativa: vacía se agenda a **3 días** de la fecha de la actividad, corridos al lunes si caen fin de semana. «Qué me toca hoy» lee ese compromiso y le gana al semáforo de días sin gestión; lo agendado a futuro no se lista, se cuenta (`D-066`).

**Canjes activos y su gestión.** Pestaña dentro de Canjes: los canjes abiertos con su estado --Al día o Pendiente-- y el historial completo que se despliega en la fila, **del registro más reciente al más antiguo** --lo que se abre a mirar es en qué quedó, y hay canjes con catorce registros (`D-080`)--. El estado se calcula sobre **cuándo se hizo la gestión**, no sobre cuándo quedó registrada, y el compromiso agendado manda sobre el tiempo cuando existe. A diferencia de «Qué me toca hoy», muestra **todos** los abiertos (`D-065`).

**«Se cayó» de canjes suma dos fuentes parciales.** Dataprop manda la fecha de cancelación de los canjes recientes --47 de 293, todos de los últimos cuatro meses-- y cancelar en la app **no** escribe ese campo, así que el reporte mira `fecha_cierre` **y** los movimientos, prefiriendo el movimiento cuando existe. Las filas que solo tienen fecha lo dicen, y su columna de registros marca cero. Los 246 cancelados sin fecha no caen en ninguna ventana: no se sabe cuándo fue. Y «Se cerró» filtra por **estado** y no por etapa, porque los 31 canjes con la etapa en «Cierre» están todos cancelados (`D-086`).

**Un movimiento con fecha de carga no es actividad de la ventana.** La limpieza que canceló los canjes que Dataprop dejó de exportar les creó el movimiento con la fecha del día en que corrió, así que «Se cayó» mostraba 215 en cuatro semanas. Se descuentan los movimientos que **entraron en una carga masiva y llevan la fecha del día en que se cargaron** --las dos condiciones: los migrados del Excel traen fechas reales y siguen contando-- y la pantalla dice cuántos descontó, para que un cero no parezca un error (`D-085`).

**Se usa en teléfono y en tablet.** Bajo 768 px la barra lateral se colapsa y se abre con el botón de menú, que vive en una cabecera que **existe solo en pantalla chica**: desde 992 px la app se ve exactamente igual que antes. Las cifras se miden contra el ancho de su tarjeta --no de la ventana-- así que un monto no se corta a la mitad, y las casillas de plata esperan hasta 992 px para pasar a cuatro columnas, porque a 820 la barra lateral deja 528 px de contenido y cuatro columnas de plata no caben. Las tablas anchas y las filas de filtros se desplazan dentro de su caja, nunca empujando la página. Los **modales van a pantalla completa** bajo 768 px, con la cabecera fija, y los campos de formulario y los filtros ocupan la fila completa ahí --desde 768 px conservan su ancho de siempre--. Verificado en 11 rutas × 6 anchos y en los 8 modales × 4 anchos, midiendo desborde y texto cortado (`D-093`).

**El historial de canjes empieza en junio de 2025.** Los anteriores se borraron definitivamente --canje, movimientos y obligaciones-- y la importación **no los vuelve a crear**: el corte vive en `limpieza_canjes.CORTE_HISTORICO` y lo usan el borrado y la carga, así que subir un export de Dataprop que todavía los traiga no repone nada. La pantalla de importar dice cuántas filas dejó fuera por antiguas. La limpieza se corre con `python -m app.scripts.borrar_canjes_antiguos`, que es **simulacro salvo que se le pase `--aplicar`** y avisa si algún canje del lote está activo o tiene gestión hecha en la app. Hay un `DELETE /api/canjes/{id}` solo para admin, sin botón en la pantalla, que existe para poder correr la limpieza contra un despliegue con una cookie en vez del string de conexión (`D-096`).

**Facturación y pago, parte por parte.** Cada liquidación de negocio y cada canje tienen su bloque: un solo campo de estado que se va moviendo --**Por Facturar → Facturado → Por Pagar → Pagado**-- y cada cambio deja un registro con su monto, su fecha y quién lo hizo. **El monto lo calcula el motor de comisiones y se puede corregir**: la tabla muestra el calculado al lado del registrado y marca el que se ajustó. Un negocio tiene seis partes --comisión total, partner comercial, corredor ViveProp, captador de la alianza, equipo y comisión real VP-- y un canje tiene dos, **una factura por corredor**, mitad y mitad de la comisión de Dataprop. No se exige el orden del circuito: un salto se registra igual y queda visible en la historia (`D-092`).

**Cobranza, y sin un gran total.** Pantalla propia con todo lo facturable y lo pagable de los dos mundos, agrupado por parte y por estado. **No hay ningún total general y es deliberado:** las seis partes de un negocio son dos niveles de la misma plata --la comisión total se reparte, y lo que le queda a ViveProp se reparte otra vez-- así que sumarlas contaría lo mismo dos veces. La de canjes va aparte porque es de Dataprop. **Y dentro de cada parte la plata va en tres columnas** --Ganado, En pipeline, No concretado; Cobrada, Potencial, No concretada en canjes-- que tampoco se suman entre sí, igual que en el listado de Negocios (`D-063`). Un selector cambia entre lo **calculado** por el motor y lo **registrado**. La tabla se puede comprobar sumando: hay una fila para el **rebate del concentrador** --que entra a la comisión real VP sin salir de ninguna otra parte-- y un aviso cuando el reparto de alguna liquidación no cuadra con su comisión total, como en VVP-2 (`D-092`, `D-095`, `D-045`).

**El reporte semanal muestra el flujo del mes, con los meses anteriores encima.** Dos pestañas --`Canjes │ Negocios`--, un cursor de **mes** con flechas, y «Comparar con los últimos **1 a 12 meses**». El eje son **las semanas del mes**, contadas **desde el día 1** (`S1 1-7`, `S2 8-14`, y así) y no de lunes a domingo: con lunes, la primera semana se reparte con el mes anterior y «S1» dejaría de significar el arranque del mes. La última semana es parcial --tres días en un mes de 31-- así que **siempre se ve más baja**, y eso se dice arriba y en el globo del gráfico; febrero tiene cuatro semanas y las líneas de los meses de cinco **se cortan** ahí en vez de dibujar un cero. Van cuatro bloques y cada título es la pregunta que responde: el **flujo** --entraron / avanzaron de etapa / se cayeron-- en tres gráficos con hasta tres meses como línea propia y el promedio de los anteriores de la cuarta en adelante; **«Los mismos números»**, la misma cosa en tabla con un mes por fila y su variación contra el elegido; **«Por dónde avanzaron»**, cuántos entraron a cada etapa contra el promedio de los meses comparados; **«Dónde está lo abierto hoy»** --que es la foto de hoy y lo dice, con la comisión parada en cada etapa y cuánto lleva--; y **«Mes a mes»**, con la plata y la curva de tendencia. La plata va por etapa y por mes y **no** por semana, porque la comisión se gana al cerrar. En negocios, «Avanzaron» y «Se perdieron» **explican por qué están vacíos** --el pipeline no tiene movimientos registrados y las liquidaciones perdidas no tienen fecha de cierre-- y aparecen solos en cuanto haya datos: una línea en cero diría «no pasó nada» y lo que pasa es «no se sabe» (`D-098`).

**El reparto de la comisión.** Reporte mensual y vista directorio muestran, apilado, quién se queda con cada peso: Real ViveProp, Corredores y Equipo. El alto de la barra es la plata que se reparte, y los chips de arriba eligen qué segmentos destacar: el que se apaga **queda en gris, no desaparece**, así que el alto de la barra sigue siendo el total del mes y la escala no se mueve (`D-075`). Los montos de los negocios van en paneles aparte --y **la venta separada del arriendo**, porque un precio de venta y un mes de renta no se suman-- (`D-064`).

**Quién puede tener cuenta.** En *Usuarios* hay una lista de **dominios de la organización** --`viveprop.com`, `dataprop.cl`-- que administra un admin desde la app. Los correos de esos dominios se crean sin preguntar; **cualquier otro correo también sirve**, pero hay que autorizarlo como externo al crear el usuario, y queda la insignia «Externo» con quién lo autorizó y cuándo. Así un director o un advisor con correo propio entra sin que haya que habilitar su dominio entero. **La lista vacía no abre la app: la cierra** --todo correo pide autorización--, y quitar un dominio no le saca el acceso a nadie: eso lo hace el switch de activo, que corta en el siguiente request (`D-078`).

**La etapa dice su nombre al pasar el mouse.** La insignia del listado de Negocios y de «Qué me toca hoy» muestra el código --`E5`, que es lo que cabe en la columna y como se habla del pipeline-- y el nombre completo en el tooltip, tomado del catálogo de etapas. Donde el rótulo tiene lugar --«Pipeline por etapa», en el dashboard-- el nombre va escrito: `E5 · Escritura / Contrato / firma final` (`D-077`).

**Filtrar negocios por corredor.** El listado tiene, además de código, modelo, estado y alianza, un filtro de **corredor** que sugiere mientras se escribe y acepta texto libre. La lista de opciones sale de un endpoint propio y es el universo completo, no el listado ya filtrado. Entran los corredores que **tienen o tuvieron** al menos un negocio, en cualquier etapa y estado, y la lista se refresca al guardar --no al recargar-- así que un corredor nuevo aparece de inmediato y el que se queda sin negocios sale (`D-090`, `D-091`).

**El potencial no se mezcla con lo efectivo.** El listado de Negocios tiene tres columnas de plata --**Ganado**, **En pipeline**, **No concretado**-- y tres totales al pie, en vez de un total que sumaba los tres estados juntos. El tablero abre con las cantidades --negocios arriba, liquidaciones en el renglón chico-- y la tasa de cierre deja las abiertas afuera del denominador (`D-063`).

**Sobre quién se hizo la gestión.** Tercer campo de la bitácora, junto al tipo y la etapa: a cuál de los dos corredores --solicitante o propietario--. El selector muestra los nombres, no las etiquetas. **Es optativo**: hay movimientos que no son sobre un corredor, y forzarlo pondría un dato falso. Los 605 migrados quedan en nulo, porque el Excel no lo traía (`D-062`).

**Cambiar la etapa deja rastro, por los dos caminos.** La etapa se puede cambiar registrando un movimiento o editando la ficha del canje. Lo segundo antes no dejaba nada en la línea de tiempo; ahora registra un movimiento automático «Cambio de etapa» con autor y de qué etapa a cuál, solo cuando cambia de verdad. No agenda seguimiento --corregir un dato no es una gestión-- y por eso la bandeja toma el último compromiso **que exista** y no el del último movimiento (`D-061`).

**Etapa y tipo de movimiento son dos campos.** Al registrar una gestión de canje se elige **qué se hizo** (Gestión inicial, Seguimiento - Llamado, Seguimiento - Whatsapp, Respuesta Corredor, Cancelación) y **dónde queda el canje** (Recepción, En revisión, Proceso de acuerdo, En oferta, En negocio, Cierre). Antes la etapa salía implícita del tipo, así que una llamada de seguimiento no podía avanzar el canje. La etapa viene precargada con la que tiene. Los tipos que ya no se ofrecen quedan `activo = false` y **no se borran**: 605 movimientos los referencian y son la línea de tiempo (`D-060`).

**El próximo seguimiento se agenda.** Al registrar un movimiento de canje se puede indicar cuándo volver a mirarlo. Es opcional: sin fecha se agenda **dos días corridos** hacia adelante, corridos al lunes si caen fin de semana. **Los feriados todavía no se saltan** --hace falta la lista de los de Chile, con sus movibles-- y la pantalla lo dice. Ese compromiso es lo que ordena *Qué me toca hoy*: `vencido` y `para hoy` van antes que el reloj de horas sin gestión, que queda para los canjes sin agenda, y lo agendado para más adelante no se lista pero se cuenta (`D-059`). **Pero un compromiso incumplido deja de proteger**: desde que vence, el atraso entra al semáforo con los mismos umbrales y un día de gracia --vencido ayer es «Vencido», hace 2 días «Advertencia», hace 3 o más «Crítico»--, así que poner una fecha de seguimiento ya no saca al canje del semáforo. En negocios es igual con sus umbrales de 14 y 30 días. Cada recuadro **nombra sus dos orígenes** --«Vencido hace 3 días o más, o más de 48 horas sin gestión»-- y la pestaña «Vencidos» filtra por el hecho de estar vencido, no por el nivel, para que no muestre cero cuando hay compromisos incumplidos escalados (`D-093`, `D-094`).

**La fecha del movimiento se elige.** En el seguimiento de un canje, al lado del tipo de movimiento va **Fecha y hora**. Vacío significa ahora --el comportamiento de siempre--; llenarlo permite anotar gestión de días pasados, que es el caso real. Se puede atrasar pero no adelantar: una fecha futura daría horas negativas en la bandeja, y una anterior a la solicitud del canje es un tipeo. **La etapa vigente se deriva del movimiento más reciente**, no del último que se guardó, para que atrasar uno no haga retroceder la etapa contra un movimiento posterior (`D-052`).

**Borrar un movimiento mal registrado.** Cada movimiento de la línea de tiempo tiene su botón de borrar, con confirmación en la misma fila. Es un borrado real y lo que dependía de él se recalcula: la etapa se vuelve a derivar de los movimientos que quedan --sin ninguno, vuelve a «Sin etapa»-- y si el borrado era la cancelación y no queda otra, el canje vuelve a activo. **`gestionado_en_app` no se revierte**, porque esa marca también la pone editar el canje a mano; el modal lo dice cuando un canje sin movimientos quedó marcado, para que no sea una exclusión silenciosa de la importación (`D-053`).

**Reporte mensual, separado por dominio.** Un selector **Negocios / Canjes** arriba: cada uno con sus recuadros, sus gráficos y su tabla. Según la ventana elegida (3, 6 o 12 meses) se dibuja la serie mes por mes con el promedio de la ventana como línea de referencia, y una frase dice si el mes va sobre, bajo o en línea con ese promedio. El promedio incluye los meses en cero a propósito: son parte de la normalidad de este negocio y excluirlos inflaría la referencia (`D-054`).

**Tendencia y canjes activos.** Cada gráfico lleva una **curva** de tendencia por mínimos cuadrados sobre la ventana, con su dirección nombrada en la leyenda. El grado crece con los puntos --recta abajo de 5 meses, y 2, 3 o 4 según la ventana-- así que la línea muestra las inflexiones que el período tenga en vez de una sola dirección promedio. La dirección se mide **al final de la curva**: sobre una serie que baja y vuelve a subir, la recta decía «plana». No se extrapola hacia adelante, y una tendencia sin forma ni pendiente no se dibuja porque el promedio ya la cuenta (`D-089`). En canjes, los activos van **apilados** sobre los cancelados: `solicitados = activos + cancelados` exacto, así que el alto de la barra es lo que entró en el mes y el activo es su propio segmento --lado a lado, cuatro activos junto a noventa cancelados no se veían--. Tienen además un gráfico propio en su propia escala, y un recuadro entre los titulares (`D-055`).

**Canjes no tiene eje de plata todavía, y está explicado en la pantalla.** Sí genera comisión --la de administración de Dataprop, 6/5/4% en venta según el tramo en UF u 8% en arriendo-- pero se calcula sobre la comisión de los corredores participantes, que está sin cargar en las 297 filas. Y `valor_prop` no sirve como reemplazo: la moneda está equivocada en ~138 filas y el campo mezcla precio de venta con arriendo mensual.

**Ventana «Histórico».** Además de 3, 6 y 12 meses, las dos pantallas de reporte tienen una ventana que muestra todo desde el primer registro --hoy 46 meses--. **El promedio y la tendencia de cada métrica arrancan donde arranca su dominio**: promediar la comisión sobre meses en que no había ni un negocio cargado dejaría la referencia tres veces y media más baja y haría ver bueno un mes malo (`D-057`). En la histórica no hay comparación contra la ventana anterior, porque antes del primer registro no hay nada.

**Vista directorio, separada por dominio.** Mismo selector Negocios / Canjes y misma ventana móvil que el reporte mensual, reusando sus componentes y sus cálculos. **La ventana solo alcanza lo temporal** --la ventana móvil, la serie, la tendencia y los conteos de canjes del período--: los buckets, la tasa de cierre, el ticket y la proyección siguen siendo históricos, porque un negocio abierto no pertenece a un mes y una tasa sobre uno o dos casos resueltos tendría un margen de casi cien puntos (`D-056`). La mitad de canjes va de volumen, origen y supervivencia, sin ticket ni proyección.

**Vista directorio.** En *Vista directorio*, la presentación ejecutiva: cuánto entró, de dónde vino, qué hay por delante y una proyección. La proyección va como **rango** con el `n` a la vista, nunca como cifra (`D-044`). Se exporta imprimiendo: `Ctrl+P` da una hoja limpia.

**Reset de contraseña.** En *Usuarios*, el botón **Resetear** genera una clave temporal, la muestra una sola vez y cierra las sesiones de esa persona. Al entrar, la app le pide elegir una propia y **la API le devuelve 403 en todo** hasta que lo haga — el bloqueo está en `get_current_user`, no en la pantalla (`D-040`). Nadie puede resetear su propia clave: para eso está *Cambiar contraseña*.

**Health checks.** Son dos y miden cosas distintas (`D-035`):

- `GET /api/health` — el proceso está vivo, **y qué commit está corriendo**. No toca la base a propósito: Neon suspende la rama sin tráfico y un despertar lento se leería como servicio caído. Es el que mira Render (`healthCheckPath`). El `commit` sale de `RENDER_GIT_COMMIT` y sirve para confirmar en un segundo si lo desplegado es lo que se subió — cuando un deploy no cambia el frontend, el hash del bundle no alcanza para distinguirlo.
- `GET /api/health/db` — la base responde. `SELECT 1`, con 503 si falla. Para diagnosticar cuando la app carga pero ninguna pantalla trae datos.
