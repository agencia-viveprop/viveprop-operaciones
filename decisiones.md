# Decisiones · ViveProp Operaciones

Registro de las decisiones tomadas durante la planificación y ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Avance de la ejecución: [estados.md](estados.md).

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

**Nota de datos.** El porcentaje nunca se registró en las 19 filas históricas. No se infiere hacia atrás; queda como campo a poblar.

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
