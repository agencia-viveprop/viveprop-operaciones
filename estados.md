# Estados de avance · ViveProp Operaciones

Registro del avance en la ejecución de [plan_desarrollo.md](plan_desarrollo.md).
Decisiones tomadas durante la ejecución: [decisiones.md](decisiones.md).

**Última actualización:** 2026-08-20

---

## Resumen

| | Cantidad |
|---|---|
| Sprints del plan | 22 |
| Listos | 0 |
| En curso | 0 |
| Pendientes | 22 |
| Bloqueados | 1 *(sprint 1, esperando la rama `dev` en Neon)* |

**Sprint actual:** ninguno. El plan está aprobado en su estructura y esperando autorización para arrancar.

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
| 1 | C1 · Ambiente dev y red de seguridad | Pendiente | — | — | Requiere la rama `dev` en Neon (acción del usuario). |
| 2 | G2 · Despliegue en Render | Pendiente | — | — | |
| 3 | C2 · Tabla UF y conversión | Pendiente | — | — | |
| 4 | C3 · Catálogos | Pendiente | — | — | |
| 5 | C4 · Plantilla y carga manual de UF | Pendiente | — | — | |
| 6 | D1 · Esquema de negocios | Pendiente | — | — | |
| 7 | D2 · Motor de comisiones | Pendiente | — | — | Decisión pendiente: `% Broker` en arriendo. |
| 8 | D3 · CRUD backend | Pendiente | — | — | |
| 9 | D4 · Pantalla Negocios | Pendiente | — | — | Primer hito visible. |
| 10 | D5 · Carga de los 19 históricos | Pendiente | — | — | Decisión pendiente: tasas de rebate y motivos de pérdida. |
| 11 | D6 · Pipeline de negocios | Pendiente | — | — | |
| 12 | F1 · Base de cálculo | Pendiente | — | — | |
| 13 | F2 · Dashboard de negocios | Pendiente | — | — | Segundo hito visible. |
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

### 2026-08-20 · Planificación — plan aprobado en estructura

Auditoría completa del Excel `GESTION_OPERACIONES_VIVEPROP.xlsx` (7 hojas) y de la base de Neon. Se levantaron las reglas de negocio no documentadas (arriendo 50/50, rebate del concentrador, comisión potencial en negocios perdidos) y se verificó que la aritmética de comisiones del Excel cuadra al peso en las 19 filas, lo que habilita usarlas como tests de regresión.

Plan cerrado en 22 sprints y 6 series, con orden de ejecución definido. Sin código escrito.
