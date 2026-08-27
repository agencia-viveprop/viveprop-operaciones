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
| `DOMINIOS_EMAIL` | Opcional. Dominios que se aceptan al crear usuarios, separados por coma. Por defecto `viveprop.com`; vacío desactiva la restricción. |

**La UF se actualiza sola.** Una tarea dentro del web service chequea una vez al día si a la serie le quedan menos de 20 días por delante y, si es así, baja lo que publica el SII (`D-036`, `D-037`). La fuente se verificó contra 617 fechas sin una diferencia. Hay además un botón para traer la historia completa, un año por página desde 2022, para una serie que arranque tarde. La carga manual de la plantilla se queda como respaldo para cuando el SII no esté o cambie su página, y los dos caminos escriben con el mismo upsert. Solo admin puede cargar UF (`D-038`).

**Carga masiva de negocios.** Botón *Carga masiva* en la pantalla de Negocios: baja una plantilla `.xlsx` con los códigos válidos de esta base y la vuelve a subir. Una fila es un hito, las tasas van en porcentaje y **las comisiones no se escriben** — las calcula el motor (`D-039`). No es la vía para los 19 históricos: esos van con `scripts/cargar_negocios.py`, que migra fiel sin recalcular.

**Qué columnas espera cada archivo.** Los dos modales de carga --*Importar Canjes* y *Carga masiva*-- tienen un **«Ver estructura del archivo»** que abre la lista completa: las columnas agrupadas, cuáles son obligatorias, qué va en cada una, los valores que se aceptan y las trampas. Sale de la misma definición que genera la plantilla, así que la pantalla y el Excel no pueden divergir (`D-050`). Canjes también tiene plantilla para descargar, pero **no es para llenarla a mano**: el archivo sale de la query contra Dataprop, y la plantilla sirve para comparar encabezados cuando la carga falla.

**Cerrar y editar una liquidación.** En la ficha de un negocio, cada liquidación tiene su botón —*Cerrar o editar* si está activa— y hay uno para *Agregar liquidación*. El formulario manda **tasas, no montos**: la comisión total, la del broker, el rebate, el equipo y la real VP las calcula el motor al guardar, con la UF de la fecha de valorización. Un hito cerrado exige fecha de cierre y uno que no lo está no la puede tener: sin esa regla la plata queda en el bucket de ganado pero en ningún mes.

**Guardar una liquidación ya cerrada pide confirmación.** Si el recálculo movería alguno de sus siete montos, la API responde 409 y la pantalla muestra el monto de hoy y el que quedaría, con un botón *Guardar de todas formas*. Existe porque los 19 negocios del Excel se cargaron con los montos tal cual (`D-026`) y la API los pasa por el motor en cada guardado: había filas cuyas entradas no reproducían su propio monto, y abrir el formulario y guardar —sin tocar nada— les cambiaba la comisión. La migración `f5a92c3d81e6` dejó esas filas consistentes y `test_valorizacion_historica.py` lo vigila, pero la guarda protege el caso que ninguna carga futura puede descartar. Ver `D-046`.

**Canjes por etapa, con filtro.** En *Inicio*, el bloque «Canjes por etapa» tiene un selector **Todos · Activos · Cancelados**. Filtra al instante, sin volver a consultar: los doce números —seis etapas por dos estados— vienen en la misma respuesta, de una sola consulta agrupada. Al lado va el total de la vista. Cuando hay canjes en estado ACTIVO con la etapa en Cerrado, la pantalla lo dice: el recuadro «Activos» de arriba los excluye, así que sin ese aviso el desglose sumaría más que el recuadro sin explicación (`D-051`).

**La secuencia del pipeline se valida.** Un negocio no puede llegar a E1 después de haber pasado por E3: la carga rechaza el negocio completo cuando las fechas contradicen el orden de las etapas, y señala cuál es la sospechosa. El historial se lee **de E1 hacia adelante**, con desempate por orden de registro para las etapas del mismo día (`D-068`).

**La comision de Dataprop.** Canjes tiene eje de plata, y es **de Dataprop, no de ViveProp**: la app lo dice en texto para que nadie la sume con la de Negocios. Tres cifras -- cobrada (registrada al cerrar), potencial y no concretada (calculadas con la regla: 2% por corredor en venta o medio mes cada uno en arriendo, y sobre eso el 6/5/4% por tramo en UF o el 8%). Todo neto. Mas los plazos, con las dos poblaciones que si se pueden medir (`D-072`).

**Un canje puede estar cerrado.** El estado admite **Activo**, **Cerrado** y **Cancelado**. La etapa dice hasta dónde llegó el proceso y el estado en qué terminó: un canje puede llegar a la etapa de cierre y caerse igual, y eso pasó 31 veces en el histórico. El gráfico de solicitudes reparte el total del mes en los tres estados (`D-071`).

**Carga del historial de etapas.** Negocios → «Historial de etapas»: una plantilla **pre-llenada** con una fila por cada etapa desde E1 hasta donde está hoy cada negocio, para cargar hacia atrás cuándo pasó por cada una y desbloquear la proyección de plazos. No agenda seguimientos, no hace retroceder la etapa actual, recargar no duplica, y se niega a corregir una fecha de inicio si eso movería la valorización (`D-067`).

**Las dos fechas del avance de negocio.** El pipeline de la ficha registra cuándo pasó la actividad y cuándo es la próxima acción. La segunda es optativa: vacía se agenda a **3 días** de la fecha de la actividad, corridos al lunes si caen fin de semana. «Qué me toca hoy» lee ese compromiso y le gana al semáforo de días sin gestión; lo agendado a futuro no se lista, se cuenta (`D-066`).

**Canjes activos y su gestión.** Pestaña dentro de Canjes: los canjes abiertos con su estado --Al día o Pendiente-- y el historial completo que se despliega en la fila, del registro más antiguo al más reciente. El estado se calcula sobre **cuándo se hizo la gestión**, no sobre cuándo quedó registrada, y el compromiso agendado manda sobre el tiempo cuando existe. A diferencia de «Qué me toca hoy», muestra **todos** los abiertos (`D-065`).

**El reporte semanal tiene una sola ventana.** El selector de arriba --**1, 2 o 4 semanas** calendario-- manda en las cuatro casillas de las dos secciones, y el umbral de «Estancado» es el largo de la ventana: lo que se movió y lo que no reparten la cartera abierta del mismo período. Las flechas mueven la ventana completa, y un período pasado se mide **al cierre de la ventana** y no contra hoy, así que se puede comparar con el siguiente. Las listas traen **un renglón por negocio o canje** --su última actualización, con la cuenta de registros detrás-- y las cuatro llevan dirección, comuna, y alianza en negocios o tipo de operación en canjes. «Quedó en» dice el nombre de la etapa, no su código, y «Qué pasó» combina la **categoría del movimiento** con el **comentario de ese registro** --la primera en tinta normal, el segundo en gris-- con el texto completo en el tooltip (`D-076`).

**El reparto de la comisión.** Reporte mensual y vista directorio muestran, apilado, quién se queda con cada peso: Real ViveProp, Corredores y Equipo. El alto de la barra es la plata que se reparte, y los chips de arriba eligen qué segmentos destacar: el que se apaga **queda en gris, no desaparece**, así que el alto de la barra sigue siendo el total del mes y la escala no se mueve (`D-075`). Los montos de los negocios van en paneles aparte --y **la venta separada del arriendo**, porque un precio de venta y un mes de renta no se suman-- (`D-064`).

**El potencial no se mezcla con lo efectivo.** El listado de Negocios tiene tres columnas de plata --**Ganado**, **En pipeline**, **No concretado**-- y tres totales al pie, en vez de un total que sumaba los tres estados juntos. El tablero abre con las cantidades --negocios arriba, liquidaciones en el renglón chico-- y la tasa de cierre deja las abiertas afuera del denominador (`D-063`).

**Sobre quién se hizo la gestión.** Tercer campo de la bitácora, junto al tipo y la etapa: a cuál de los dos corredores --solicitante o propietario--. El selector muestra los nombres, no las etiquetas. **Es optativo**: hay movimientos que no son sobre un corredor, y forzarlo pondría un dato falso. Los 605 migrados quedan en nulo, porque el Excel no lo traía (`D-062`).

**Cambiar la etapa deja rastro, por los dos caminos.** La etapa se puede cambiar registrando un movimiento o editando la ficha del canje. Lo segundo antes no dejaba nada en la línea de tiempo; ahora registra un movimiento automático «Cambio de etapa» con autor y de qué etapa a cuál, solo cuando cambia de verdad. No agenda seguimiento --corregir un dato no es una gestión-- y por eso la bandeja toma el último compromiso **que exista** y no el del último movimiento (`D-061`).

**Etapa y tipo de movimiento son dos campos.** Al registrar una gestión de canje se elige **qué se hizo** (Gestión inicial, Seguimiento - Llamado, Seguimiento - Whatsapp, Respuesta Corredor, Cancelación) y **dónde queda el canje** (Recepción, En revisión, Proceso de acuerdo, En oferta, En negocio, Cierre). Antes la etapa salía implícita del tipo, así que una llamada de seguimiento no podía avanzar el canje. La etapa viene precargada con la que tiene. Los tipos que ya no se ofrecen quedan `activo = false` y **no se borran**: 605 movimientos los referencian y son la línea de tiempo (`D-060`).

**El próximo seguimiento se agenda.** Al registrar un movimiento de canje se puede indicar cuándo volver a mirarlo. Es opcional: sin fecha se agenda **dos días corridos** hacia adelante, corridos al lunes si caen fin de semana. **Los feriados todavía no se saltan** --hace falta la lista de los de Chile, con sus movibles-- y la pantalla lo dice. Ese compromiso es lo que ordena *Qué me toca hoy*: `vencido` y `para hoy` van antes que el reloj de horas sin gestión, que queda para los canjes sin agenda, y lo agendado para más adelante no se lista pero se cuenta (`D-059`).

**La fecha del movimiento se elige.** En el seguimiento de un canje, al lado del tipo de movimiento va **Fecha y hora**. Vacío significa ahora --el comportamiento de siempre--; llenarlo permite anotar gestión de días pasados, que es el caso real. Se puede atrasar pero no adelantar: una fecha futura daría horas negativas en la bandeja, y una anterior a la solicitud del canje es un tipeo. **La etapa vigente se deriva del movimiento más reciente**, no del último que se guardó, para que atrasar uno no haga retroceder la etapa contra un movimiento posterior (`D-052`).

**Borrar un movimiento mal registrado.** Cada movimiento de la línea de tiempo tiene su botón de borrar, con confirmación en la misma fila. Es un borrado real y lo que dependía de él se recalcula: la etapa se vuelve a derivar de los movimientos que quedan --sin ninguno, vuelve a «Sin etapa»-- y si el borrado era la cancelación y no queda otra, el canje vuelve a activo. **`gestionado_en_app` no se revierte**, porque esa marca también la pone editar el canje a mano; el modal lo dice cuando un canje sin movimientos quedó marcado, para que no sea una exclusión silenciosa de la importación (`D-053`).

**Reporte mensual, separado por dominio.** Un selector **Negocios / Canjes** arriba: cada uno con sus recuadros, sus gráficos y su tabla. Según la ventana elegida (3, 6 o 12 meses) se dibuja la serie mes por mes con el promedio de la ventana como línea de referencia, y una frase dice si el mes va sobre, bajo o en línea con ese promedio. El promedio incluye los meses en cero a propósito: son parte de la normalidad de este negocio y excluirlos inflaría la referencia (`D-054`).

**Tendencia y canjes activos.** Cada gráfico lleva una recta de tendencia por mínimos cuadrados sobre la ventana, con su dirección nombrada en la leyenda; una tendencia plana no se dibuja, porque el promedio ya la cuenta. En canjes, los activos van **apilados** sobre los cancelados: `solicitados = activos + cancelados` exacto, así que el alto de la barra es lo que entró en el mes y el activo es su propio segmento --lado a lado, cuatro activos junto a noventa cancelados no se veían--. Tienen además un gráfico propio en su propia escala, y un recuadro entre los titulares (`D-055`).

**Canjes no tiene eje de plata todavía, y está explicado en la pantalla.** Sí genera comisión --la de administración de Dataprop, 6/5/4% en venta según el tramo en UF u 8% en arriendo-- pero se calcula sobre la comisión de los corredores participantes, que está sin cargar en las 297 filas. Y `valor_prop` no sirve como reemplazo: la moneda está equivocada en ~138 filas y el campo mezcla precio de venta con arriendo mensual.

**Ventana «Histórico».** Además de 3, 6 y 12 meses, las dos pantallas de reporte tienen una ventana que muestra todo desde el primer registro --hoy 46 meses--. **El promedio y la tendencia de cada métrica arrancan donde arranca su dominio**: promediar la comisión sobre meses en que no había ni un negocio cargado dejaría la referencia tres veces y media más baja y haría ver bueno un mes malo (`D-057`). En la histórica no hay comparación contra la ventana anterior, porque antes del primer registro no hay nada.

**Vista directorio, separada por dominio.** Mismo selector Negocios / Canjes y misma ventana móvil que el reporte mensual, reusando sus componentes y sus cálculos. **La ventana solo alcanza lo temporal** --la ventana móvil, la serie, la tendencia y los conteos de canjes del período--: los buckets, la tasa de cierre, el ticket y la proyección siguen siendo históricos, porque un negocio abierto no pertenece a un mes y una tasa sobre uno o dos casos resueltos tendría un margen de casi cien puntos (`D-056`). La mitad de canjes va de volumen, origen y supervivencia, sin ticket ni proyección.

**Vista directorio.** En *Vista directorio*, la presentación ejecutiva: cuánto entró, de dónde vino, qué hay por delante y una proyección. La proyección va como **rango** con el `n` a la vista, nunca como cifra (`D-044`). Se exporta imprimiendo: `Ctrl+P` da una hoja limpia.

**Reset de contraseña.** En *Usuarios*, el botón **Resetear** genera una clave temporal, la muestra una sola vez y cierra las sesiones de esa persona. Al entrar, la app le pide elegir una propia y **la API le devuelve 403 en todo** hasta que lo haga — el bloqueo está en `get_current_user`, no en la pantalla (`D-040`). Nadie puede resetear su propia clave: para eso está *Cambiar contraseña*.

**Health checks.** Son dos y miden cosas distintas (`D-035`):

- `GET /api/health` — el proceso está vivo, **y qué commit está corriendo**. No toca la base a propósito: Neon suspende la rama sin tráfico y un despertar lento se leería como servicio caído. Es el que mira Render (`healthCheckPath`). El `commit` sale de `RENDER_GIT_COMMIT` y sirve para confirmar en un segundo si lo desplegado es lo que se subió — cuando un deploy no cambia el frontend, el hash del bundle no alcanza para distinguirlo.
- `GET /api/health/db` — la base responde. `SELECT 1`, con 503 si falla. Para diagnosticar cuando la app carga pero ninguna pantalla trae datos.
