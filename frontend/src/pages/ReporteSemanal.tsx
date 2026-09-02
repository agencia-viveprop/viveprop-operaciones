import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ActionIcon,
  Alert,
  Group,
  Paper,
  Progress,
  SegmentedControl,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { IconChevronLeft, IconChevronRight, IconInfoCircle } from '@tabler/icons-react'
import {
  MESES_A_COMPARAR,
  obtenerReporteSemanal,
  type EtapaAbierta,
  type EtapaDelEmbudo,
  type ReporteDeDominio,
  type TotalDelMes,
} from '../api/reportes'
import { obtenerCatalogos } from '../api/catalogos'
import PageHeader from '../components/PageHeader'
import EstadoConsulta from '../components/EstadoConsulta'
import FlujoSemanal, { type Señal } from '../components/FlujoSemanal'
import { clp } from '../components/negociosFormato'
import { rotuloEtapa } from '../components/canjesEtiquetas'

/**
 * Reporte semanal: cómo se movió el mes, semana a semana, contra los anteriores.
 *
 * **Cuatro bloques y cada título es la pregunta que responde.** Es la restricción
 * que puso el usuario --«que quien lo vea pueda entender lo que está viendo»-- y
 * la que decidió qué **no** va: ni área apilada de composición por etapa (el dato
 * no existe hacia atrás) ni la plata en el gráfico semanal (`D-098`).
 *
 * **El gráfico semanal sí lleva tendencia, una sola** (`D-100`): la de las semanas
 * completas, ajustada con toda la ventana comparada. La del bloque mensual es otra
 * --va sobre meses-- y las dos conviven porque responden preguntas distintas.
 *
 * | Bloque | La pregunta |
 * |---|---|
 * | Flujo | cómo se movió el mes, semana a semana |
 * | Embudo | por dónde avanzaron |
 * | Abiertos | dónde está lo abierto hoy y cuánta plata hay ahí |
 * | Mes a mes | los totales del período, con tendencia; y la plata solo en negocios |
 */

type Dominio = 'canjes' | 'negocios'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

/** Las tres señales del flujo, en orden de lectura: qué entró, qué se movió, qué
 *  se perdió. El sustantivo cambia por dominio. */
const SEÑALES: { campo: Señal; titulo: (d: Dominio) => string; ayuda: string }[] = [
  {
    campo: 'entraron',
    titulo: (d) => (d === 'canjes' ? 'Entraron' : 'Liquidaciones iniciadas'),
    ayuda: 'Por fecha de solicitud en canjes, y de inicio de la liquidación en negocios.',
  },
  {
    campo: 'avanzaron',
    titulo: () => 'Avanzaron de etapa',
    ayuda: 'Cuenta entidades y no movimientos: dos avances del mismo canje en la semana son uno que avanzó.',
  },
  {
    campo: 'se_cayeron',
    titulo: (d) => (d === 'canjes' ? 'Se cayeron' : 'Se perdieron'),
    ayuda: 'En canjes suma las dos fuentes: la cancelación registrada y la fecha que manda Dataprop.',
  },
]

/** Por qué una señal no tiene datos. El backend dice **cuál** falta; el texto de
 *  por qué vive acá, porque es lo que se le explica a quien mira. */
const POR_QUE_FALTA: Record<string, string> = {
  avanzaron:
    'Todavía no se puede medir: el pipeline de negocios no tiene ningún movimiento registrado, así que no hay historia de cuándo avanzó cada negocio de etapa. Aparece en cuanto se empiece a registrar el avance en la ficha.',
  se_cayeron:
    'Todavía no se puede medir: las liquidaciones perdidas no tienen fecha de cierre, así que no se sabe en qué semana se cayeron. Aparece en cuanto se registre esa fecha al cerrarlas.',
}

function rotuloMesCorto(clave: string): string {
  const nombres = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  const [anio, mes] = clave.split('-')
  return `${nombres[Number(mes) - 1] ?? mes} ${anio.slice(2)}`
}

function variacion(actual: number, referencia: number): string {
  if (referencia === 0) return actual === 0 ? '—' : 'nuevo'
  const pct = Math.round(((actual - referencia) / referencia) * 100)
  return `${pct > 0 ? '+' : ''}${pct}%`
}

/** La tabla del flujo: los mismos números del gráfico, mes por mes.
 *
 * Va **debajo del gráfico y no en lugar de él**: el usuario pidió las dos cosas,
 * «visualmente y en números». La columna de variación compara cada mes anterior
 * contra el elegido, que es la pregunta «cómo vamos respecto de esos períodos». */
function TablaDelFlujo({
  dominio,
  reporte,
  señal,
}: {
  dominio: ReporteDeDominio
  reporte: ReporteDeDominio
  señal: Señal
}) {
  void dominio
  const [actual] = reporte.flujo
  const totalDe = (valores: number[]) => valores.reduce((a, b) => a + b, 0)
  const totalActual = totalDe(actual[señal])

  return (
    <div className="tabla-scroll-x">
      <Table withRowBorders={false} verticalSpacing={4} fz="xs" miw={520}>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Mes</Table.Th>
            {reporte.semanas.map((s) => (
              <Table.Th key={s.etiqueta} ta="right">
                {s.etiqueta.split(' ')[0]}
              </Table.Th>
            ))}
            <Table.Th ta="right">Total</Table.Th>
            <Table.Th ta="right">vs {rotuloMesCorto(actual.mes)}</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {reporte.flujo.map((f, indice) => (
            <Table.Tr key={f.mes}>
              <Table.Td fw={indice === 0 ? 700 : 400}>{rotuloMesCorto(f.mes)}</Table.Td>
              {reporte.semanas.map((s, i) => (
                <Table.Td key={s.etiqueta} ta="right" ff="monospace">
                  {f[señal][i] ?? '—'}
                </Table.Td>
              ))}
              <Table.Td ta="right" ff="monospace" fw={700}>
                {totalDe(f[señal])}
              </Table.Td>
              <Table.Td ta="right" ff="monospace" c="dimmed">
                {indice === 0 ? '—' : variacion(totalActual, totalDe(f[señal]))}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </div>
  )
}

/** El embudo: por dónde avanzaron en el mes.
 *
 * **Todas las etapas van, incluso en cero**: el embudo se lee por su forma --dónde
 * se angosta-- y una etapa que desaparece parece no existir. El promedio de los
 * meses anteriores va como número al lado y no como una segunda barra, que es lo
 * que recargaría la pantalla. */
function Embudo({
  embudo,
  rotular,
  vacio,
}: {
  embudo: EtapaDelEmbudo[]
  rotular: (codigo: string) => string
  vacio?: string
}) {
  const tope = Math.max(...embudo.map((e) => e.entraron), 1)
  const total = embudo.reduce((a, e) => a + e.entraron, 0)

  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5}>Por dónde avanzaron</Title>
      <Text size="xs" c="dimmed" mb="sm">
        Cuántos entraron a cada etapa en el mes, y el promedio de los meses que estás
        comparando.
      </Text>
      {vacio ? (
        <Text size="sm" c="dimmed">
          {vacio}
        </Text>
      ) : total === 0 ? (
        <Text size="sm" c="dimmed">
          Nadie cambió de etapa en este mes.
        </Text>
      ) : (
        <Stack gap={6}>
          {embudo.map((e) => (
            <Group key={e.etapa} gap="sm" wrap="nowrap">
              <Text size="sm" w={210} style={{ flexShrink: 0 }}>
                {rotular(e.etapa)}
              </Text>
              <Progress
                value={(e.entraron / tope) * 100}
                size="lg"
                radius="sm"
                style={{ flex: 1, minWidth: 60 }}
              />
              <Text size="sm" ff="monospace" w={100} ta="right" style={{ flexShrink: 0 }}>
                {e.entraron}
                <Text span size="xs" c="dimmed">
                  {' '}
                  prom {Number(e.promedio_anteriores).toLocaleString('es-CL')}
                </Text>
              </Text>
            </Group>
          ))}
        </Stack>
      )}
    </Paper>
  )
}

/** Dónde está lo abierto hoy, con la plata en juego y cuánto lleva ahí. */
function Abiertos({
  abiertos,
  rotular,
  rotuloPlata,
}: {
  abiertos: EtapaAbierta[]
  rotular: (codigo: string) => string
  rotuloPlata: string
}) {
  const sinHistoria = abiertos.reduce((a, e) => a + e.sin_historia, 0)

  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5}>Dónde está lo abierto hoy</Title>
      <Text size="xs" c="dimmed" mb="sm">
        <strong>No depende del mes que estés mirando</strong>: lo abierto es lo de hoy, así que
        esta foto es la misma en cualquier período.
      </Text>
      {abiertos.length === 0 ? (
        <Text size="sm" c="dimmed">
          No hay nada abierto.
        </Text>
      ) : (
        <>
          <div className="tabla-scroll-x">
            <Table withRowBorders={false} verticalSpacing={4} miw={480}>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Etapa</Table.Th>
                  <Table.Th ta="right">Casos</Table.Th>
                  <Table.Th ta="right">{rotuloPlata}</Table.Th>
                  <Table.Th ta="right">Promedio</Table.Th>
                  <Table.Th ta="right">Rango</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {abiertos.map((e) => (
                  <Table.Tr key={e.etapa}>
                    <Table.Td>{rotular(e.etapa)}</Table.Td>
                    <Table.Td ta="right" ff="monospace">
                      {e.casos}
                    </Table.Td>
                    <Table.Td ta="right" ff="monospace">
                      {clp(e.comision)}
                    </Table.Td>
                    <Table.Td ta="right" ff="monospace">
                      {e.dias_promedio} d
                    </Table.Td>
                    <Table.Td ta="right" ff="monospace" c="dimmed">
                      {e.dias_min === e.dias_max ? '—' : `${e.dias_min}–${e.dias_max} d`}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </div>
          {sinHistoria > 0 && (
            <Text size="xs" c="dimmed" mt="xs">
              {sinHistoria === 1 ? 'Uno' : sinHistoria} sin movimiento que registre la entrada a
              la etapa: ahí el reloj se cuenta desde el inicio, que no es lo mismo que haberlo
              medido.
            </Text>
          )}
        </>
      )}
    </Paper>
  )
}

/** Mes a mes: los totales del período, con la tendencia sobre los meses.
 *
 * **La plata va solo en negocios** (`D-103`). En canjes las tres columnas de plata
 * se retiraron: el usuario las señaló --«solo enreda la interpretación»--. Ahí la
 * comisión es de Dataprop y solo la de los canjes **activos** es plata en juego
 * (`D-102`), así que un monto por mes de entrada se lee como ganado cuando no lo
 * es. Lo que sí es plata en juego se muestra en «Dónde está lo abierto hoy».
 *
 * **Esta tendencia va sobre meses y es otra que la del gráfico semanal** (`D-100`).
 * Esa dice cómo se mueve el mes por dentro --semana a semana-- y esta hacia dónde
 * va el período. Con cinco semanas y la última de tres días, una sola curva no
 * podía responder las dos. */
function MesAMes({
  totales,
  tendencias,
  rotuloPlata,
  conPlata,
}: {
  totales: TotalDelMes[]
  tendencias: ReporteDeDominio['tendencias']
  rotuloPlata: string
  /** Si van las tres columnas de plata. **En canjes no van** (`D-103`). */
  conPlata: boolean
}) {
  const te = tendencias.entraron

  return (
    <Paper withBorder radius="md" p="md">
      <Group justify="space-between" align="baseline">
        <Title order={5}>Mes a mes</Title>
        {te?.mostrar && (
          <Text size="xs" c="dimmed">
            la tendencia de {te.puntos} meses viene{' '}
            <Text span fw={700}>
              {te.direccion === 'sube' ? 'al alza' : te.direccion === 'baja' ? 'a la baja' : 'plana'}
            </Text>
          </Text>
        )}
      </Group>
      <Text size="xs" c="dimmed" mb="sm">
        {conPlata
          ? 'Los totales del período y la plata. La plata va acá y no en el gráfico semanal: se gana al cerrar, así que semana a semana serían ceros con un pico.'
          : 'Cuántos entraron, cuántos avanzaron y cuántos se cayeron en cada mes del período.'}
      </Text>
      <div className="tabla-scroll-x">
        <Table withRowBorders={false} verticalSpacing={4} miw={conPlata ? 620 : 380}>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Mes</Table.Th>
              <Table.Th ta="right">Entraron</Table.Th>
              <Table.Th ta="right">Avanzaron</Table.Th>
              <Table.Th ta="right">Se cayeron</Table.Th>
              {conPlata && (
                <>
                  <Table.Th ta="right">{rotuloPlata}</Table.Th>
                  <Table.Th ta="right">Ventas</Table.Th>
                  <Table.Th ta="right">Arriendos</Table.Th>
                </>
              )}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {totales.map((t, i) => (
              <Table.Tr key={t.etiqueta}>
                <Table.Td fw={i === totales.length - 1 ? 700 : 400}>
                  {rotuloMesCorto(t.etiqueta)}
                </Table.Td>
                <Table.Td ta="right" ff="monospace">
                  {t.entraron}
                </Table.Td>
                <Table.Td ta="right" ff="monospace">
                  {t.avanzaron}
                </Table.Td>
                <Table.Td ta="right" ff="monospace">
                  {t.se_cayeron}
                </Table.Td>
                {conPlata && (
                  <>
                    <Table.Td ta="right" ff="monospace">
                      {clp(t.comision)}
                    </Table.Td>
                    <Table.Td ta="right" ff="monospace" c="dimmed">
                      {clp(t.valor_venta)}
                    </Table.Td>
                    <Table.Td ta="right" ff="monospace" c="dimmed">
                      {clp(t.valor_arriendo)}
                    </Table.Td>
                  </>
                )}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </div>
      {conPlata && (
        <Text size="xs" c="dimmed" mt="xs">
          Ventas y arriendos van en columnas separadas y <strong>no se suman</strong>: un precio
          de venta y un mes de renta no son la misma unidad.
        </Text>
      )}
    </Paper>
  )
}

export default function ReporteSemanal() {
  // El mes que se está mirando. Arranca en el actual y las flechas lo mueven.
  const [cursor, setCursor] = useState(() => {
    const hoy = new Date()
    return new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  })
  const [meses, setMeses] = useState('3')
  const [dominio, setDominio] = useState<Dominio>('canjes')

  const anio = cursor.getFullYear()
  const mes = cursor.getMonth() + 1

  const consulta = useQuery({
    queryKey: ['reporte-semanal', anio, mes, meses],
    queryFn: () => obtenerReporteSemanal(anio, mes, Number(meses)),
  })
  const { data } = consulta

  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const rotularNegocio = (codigo: string) => {
    const etapa = catalogos?.etapas.find((e) => e.codigo === codigo)
    return etapa ? `${codigo} · ${etapa.nombre}` : codigo
  }
  const rotularCanje = (codigo: string) => rotuloEtapa(codigo)

  const correr = (delta: number) =>
    setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + delta, 1))

  const reporte = data ? data[dominio] : null
  const rotular = dominio === 'canjes' ? rotularCanje : rotularNegocio
  const rotuloPlata = dominio === 'canjes' ? 'Comisión Dataprop' : 'Comisión real VP'

  return (
    <>
      <PageHeader
        title="Reporte semanal"
        subtitle="Cómo se movió el mes, semana a semana, contra los meses anteriores."
        action={
          <Group gap="xs" wrap="nowrap">
            <ActionIcon variant="default" radius="xl" onClick={() => correr(-1)} aria-label="Mes anterior">
              <IconChevronLeft size={16} />
            </ActionIcon>
            <Text fw={700} ta="center" style={{ minWidth: 150 }}>
              {MESES[mes - 1]} {anio}
            </Text>
            <ActionIcon variant="default" radius="xl" onClick={() => correr(1)} aria-label="Mes siguiente">
              <IconChevronRight size={16} />
            </ActionIcon>
          </Group>
        }
      />

      {!reporte || !data ? (
        <EstadoConsulta de={consulta} alto={240} />
      ) : (
        <Stack gap="md">
          <Group gap="lg" wrap="wrap">
            <SegmentedControl
              color="accent"
              value={dominio}
              onChange={(v) => setDominio(v as Dominio)}
              data={[
                { value: 'canjes', label: 'Canjes' },
                { value: 'negocios', label: 'Negocios' },
              ]}
            />
            <Group gap="xs">
              <Text size="xs" c="dimmed">
                Comparar con los últimos
              </Text>
              <Select
                size="xs"
                w={110}
                value={meses}
                onChange={(v) => setMeses(v ?? '3')}
                data={MESES_A_COMPARAR.map((m) => ({
                  value: String(m),
                  label: m === 1 ? '1 mes' : `${m} meses`,
                }))}
                allowDeselect={false}
              />
              <Text size="xs" c="dimmed">
                · {MESES[mes - 1]} tiene {reporte.semanas.length} semanas
              </Text>
            </Group>
          </Group>

          <Alert variant="light" color="brand" icon={<IconInfoCircle size={18} />}>
            <Text size="sm">
              Las semanas se cuentan <strong>desde el día 1</strong> del mes: del 1 al 7, del 8
              al 14, y así.{' '}
              {reporte.semanas[reporte.semanas.length - 1].dias < 7 && (
                <>
                  La última tiene{' '}
                  <strong>{reporte.semanas[reporte.semanas.length - 1].dias} días</strong>, así
                  que siempre va a verse más baja: es el calendario, no una caída de actividad.
                </>
              )}
            </Text>
          </Alert>

          {/* ── 1. El flujo, semana a semana ─────────────────────────── */}
          {/* Con muchos meses el grupo de cada semana tiene una barra por mes
              (`D-101`), así que los tres gráficos en fila dejarían barras de
              cuatro píxeles: de siete meses en adelante bajan a dos columnas y de
              diez a una, para que cada barra siga siendo una barra. */}
          <SimpleGrid
            cols={{ base: 1, lg: Number(meses) > 9 ? 1 : Number(meses) > 6 ? 2 : 3 }}
            spacing="md"
          >
            {SEÑALES.map((s) => (
              <FlujoSemanal
                key={s.campo}
                titulo={s.titulo(dominio)}
                subtitulo={s.ayuda}
                semanas={reporte.semanas}
                flujo={reporte.flujo}
                señal={s.campo}
                tendencia={reporte.tendencia_semanal[s.campo]}
                sinDatos={
                  reporte.sin_datos.includes(s.campo) ? POR_QUE_FALTA[s.campo] : undefined
                }
              />
            ))}
          </SimpleGrid>

          <Paper withBorder radius="md" p="md">
            <Title order={5}>Los mismos números</Title>
            <Text size="xs" c="dimmed" mb="sm">
              Cada mes en su fila, con sus semanas y su total. La última columna compara ese mes
              contra {MESES[mes - 1]}.
            </Text>
            <Stack gap="lg">
              {SEÑALES.filter((s) => !reporte.sin_datos.includes(s.campo)).map((s) => (
                <div key={s.campo}>
                  <Text size="sm" fw={600} mb={4}>
                    {s.titulo(dominio)}
                  </Text>
                  <TablaDelFlujo dominio={reporte} reporte={reporte} señal={s.campo} />
                </div>
              ))}
            </Stack>
          </Paper>

          {/* ── 2. Por dónde avanzaron ───────────────────────────────── */}
          <Embudo
            embudo={reporte.embudo}
            rotular={rotular}
            vacio={
              reporte.sin_datos.includes('avanzaron') ? POR_QUE_FALTA.avanzaron : undefined
            }
          />

          {/* ── 3. Dónde está lo abierto ─────────────────────────────── */}
          <Abiertos abiertos={reporte.abiertos} rotular={rotular} rotuloPlata={rotuloPlata} />

          {/* ── 4. Mes a mes, con la tendencia ───────────────────────── */}
          <MesAMes
            totales={reporte.totales}
            tendencias={reporte.tendencias}
            rotuloPlata={rotuloPlata}
            conPlata={dominio === 'negocios'}
          />
        </Stack>
      )}
    </>
  )
}
