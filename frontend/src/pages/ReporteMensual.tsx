import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ActionIcon,
  Badge,
  Group,
  Paper,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from '@mantine/core'
import { IconChevronLeft, IconChevronRight, IconMinus } from '@tabler/icons-react'
import {
  obtenerReporteMensual,
  VENTANAS,
  type Comparacion,
  type Variacion,
} from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

/** Las métricas que son plata se muestran como plata; el resto, como cuenta. */
const EN_PESOS = new Set(['Comisión real ViveProp', 'Comisión total'])

function rotulo(etiqueta: string): string {
  // Las ventanas vienen como '2026-03 a 2026-08'; un mes suelto, como '2026-08'.
  if (etiqueta.includes(' a ')) {
    return etiqueta
      .split(' a ')
      .map((e) => rotulo(e))
      .join(' — ')
  }
  const [anio, mes] = etiqueta.split('-')
  return `${MESES[Number(mes) - 1]} ${anio}`
}

function valor(v: Variacion, campo: 'actual' | 'referencia'): string {
  const n = Number(v[campo])
  return EN_PESOS.has(v.metrica) ? clp(n) : String(n)
}

/**
 * La variación, con su signo y su color.
 *
 * **`pct` nulo no es cero ni infinito: es que no hay base.** Si el período de
 * referencia tuvo cero, no existe porcentaje que calcular, y mostrar uno sería
 * inventarlo. Se dice "nuevo" y se muestra la diferencia absoluta, que sí
 * significa algo.
 */
function Delta({ v }: { v: Variacion }) {
  const abs = Number(v.absoluta)
  const sinBase = v.pct === null

  if (abs === 0 && sinBase) {
    return (
      <Group gap={4} justify="flex-end" c="dimmed">
        <IconMinus size={13} />
        <Text size="xs">sin cambio</Text>
      </Group>
    )
  }

  const color = abs > 0 ? 'good' : 'critical'
  const signo = abs > 0 ? '+' : ''
  const diferencia = EN_PESOS.has(v.metrica) ? clp(Math.abs(abs)) : String(Math.abs(abs))

  return (
    <Group gap={6} justify="flex-end" wrap="nowrap">
      {sinBase ? (
        <Tooltip label="El período de referencia estuvo en cero: no hay porcentaje que calcular">
          <Badge color={color} variant="light" size="sm">
            nuevo
          </Badge>
        </Tooltip>
      ) : (
        <Badge color={color} variant="light" size="sm">
          {signo}
          {v.pct}%
        </Badge>
      )}
      <Text size="xs" c="dimmed">
        {abs > 0 ? '+' : '−'}
        {diferencia}
      </Text>
    </Group>
  )
}

function TablaComparacion({ titulo, ayuda, c }: { titulo: string; ayuda: string; c: Comparacion }) {
  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5}>{titulo}</Title>
      <Text size="xs" c="dimmed" mb="sm">
        {ayuda} · <strong>{rotulo(c.actual.etiqueta)}</strong> contra{' '}
        {rotulo(c.contra.etiqueta)}
      </Text>
      <div className="tabla-scroll-x">
        <Table striped fz="xs" className="tabla-una-linea">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Métrica</Table.Th>
              <Table.Th ta="right">Período</Table.Th>
              <Table.Th ta="right">Referencia</Table.Th>
              <Table.Th ta="right">Variación</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {c.variaciones.map((v) => (
              <Table.Tr key={v.metrica}>
                <Table.Td>{v.metrica}</Table.Td>
                <Table.Td ta="right" ff="monospace">
                  {valor(v, 'actual')}
                </Table.Td>
                <Table.Td ta="right" ff="monospace" c="dimmed">
                  {valor(v, 'referencia')}
                </Table.Td>
                <Table.Td>
                  <Delta v={v} />
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </div>
    </Paper>
  )
}

/**
 * El reporte de cierre, con ventanas móviles.
 *
 * **El mes calendario no es la unidad natural de este negocio.** Los procesos
 * duran de un mes a varios, así que un mes en cero no es un mes malo: es que
 * ningún proceso terminó de madurar. Sobre los datos reales, 4 de 11 meses
 * estuvieron vacíos y el ticket varía cuatro veces. Con ~1 cierre por mes y esa
 * dispersión, la comparación mes contra mes mide ruido, no desempeño.
 *
 * Por eso el titular es una **ventana móvil** contra la anterior del mismo largo,
 * el **año corrido** va contra el mismo tramo del año pasado, y el mes queda
 * arriba como detalle de qué cerró.
 *
 * El largo de la ventana es un control y no una constante: el horizonte correcto
 * depende de qué se esté mirando, y quien lee el reporte lo sabe mejor.
 *
 * No hay serie de veinticuatro meses acá: eso ya está en los gráficos "por mes"
 * del dashboard y responde otra pregunta.
 */
export default function ReporteMensual() {
  const ahora = new Date()
  const [desplazamiento, setDesplazamiento] = useState(0)
  const [ventana, setVentana] = useState('6')

  const cursor = new Date(ahora.getFullYear(), ahora.getMonth() + desplazamiento, 1)
  const anio = cursor.getFullYear()
  const mes = cursor.getMonth() + 1

  const consulta = useQuery({
    queryKey: ['reporte-mensual', anio, mes, ventana],
    queryFn: () => obtenerReporteMensual(anio, mes, Number(ventana)),
  })
  const { data } = consulta

  return (
    <Stack gap="md">
      <PageHeader
        title="Reporte mensual"
        subtitle="En un negocio donde los procesos duran de un mes a varios, un mes en cero no es un mes malo. Por eso el titular es una ventana móvil, y el mes queda como detalle."
        action={
          <Group gap="xs">
            <Tooltip label="Mes anterior">
              <ActionIcon variant="default" onClick={() => setDesplazamiento((d) => d - 1)} aria-label="Mes anterior">
                <IconChevronLeft size={16} />
              </ActionIcon>
            </Tooltip>
            <Text size="sm" fw={600} w={150} ta="center" tt="capitalize">
              {rotulo(`${anio}-${String(mes).padStart(2, '0')}`)}
            </Text>
            <Tooltip label={desplazamiento >= 0 ? 'Todavía no empieza' : 'Mes siguiente'}>
              <ActionIcon
                variant="default"
                disabled={desplazamiento >= 0}
                onClick={() => setDesplazamiento((d) => d + 1)}
                aria-label="Mes siguiente"
              >
                <IconChevronRight size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        }
      />

      {!data ? (
        <EstadoConsulta de={consulta} alto={240} />
      ) : (
        <>
          {/* El selector va primero porque manda sobre los tiles de abajo. */}
          <Group gap="xs">
            <Text size="xs" c="dimmed">
              Ventana móvil de
            </Text>
            <SegmentedControl
              size="xs"
              color="accent"
              value={ventana}
              onChange={setVentana}
              data={VENTANAS.map((v) => ({ value: String(v), label: `${v} meses` }))}
            />
          </Group>

          {/* Los tiles muestran la **ventana**, no el mes.
           *
           * Estaban al revés: mostraban el mes calendario, arriba y en grande, en
           * una pantalla que dice que el mes es un detalle. El resultado era que
           * lo primero que se veía era "$0" --cierto para agosto, porque el
           * último cierre es del 1 de junio-- y la conclusión natural era que la
           * app estaba rota. La maquetación contradecía el mensaje. */}
          <SimpleGrid cols={{ base: 2, sm: 4 }}>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                COMISIÓN REAL VP
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {clp(data.movil.actual.comision_real_vp)}
              </Text>
              <Text size="xs" c="dimmed" mt={4}>
                en {data.ventana_meses} meses
              </Text>
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                LIQUIDACIONES
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {data.movil.actual.hitos_cerrados}
              </Text>
              <Text size="xs" c="dimmed" mt={4}>
                cerradas en la ventana
              </Text>
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                NEGOCIOS INICIADOS
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {data.movil.actual.negocios_iniciados}
              </Text>
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                CANJES SOLICITADOS
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {data.movil.actual.canjes_solicitados}
              </Text>
            </Paper>
          </SimpleGrid>

          <TablaComparacion
            titulo={`Últimos ${data.ventana_meses} meses`}
            ayuda="Contra los mismos meses inmediatamente anteriores, sin solaparse"
            c={data.movil}
          />
          <TablaComparacion
            titulo="Año corrido"
            ayuda="Contra el mismo tramo del año pasado, no contra el año entero"
            c={data.anio_corrido}
          />

          {/* El mes, como detalle y al final.
           *
           * Cuando no cerró nada se dice con palabras y no con "$0": un cero en
           * un tile grande se lee como un error, y una frase se lee como lo que
           * es -- ningún proceso terminó de madurar ese mes. */}
          <Paper withBorder radius="md" p="md">
            <Title order={5} tt="capitalize">
              {rotulo(data.mes.etiqueta)}, el mes suelto
            </Title>
            <Text size="sm" mt={6}>
              {data.mes.hitos_cerrados === 0 ? (
                <>
                  No se cerró ninguna liquidación en el mes. Con procesos que duran de un mes
                  a varios eso es normal: sobre los datos reales, 4 de 11 meses estuvieron
                  vacíos.
                </>
              ) : (
                <>
                  {data.mes.hitos_cerrados}{' '}
                  {data.mes.hitos_cerrados === 1 ? 'liquidación cerrada' : 'liquidaciones cerradas'}{' '}
                  por {clp(data.mes.comision_real_vp)} de comisión real.
                </>
              )}{' '}
              {data.mes.negocios_iniciados > 0 && (
                <>
                  Entraron {data.mes.negocios_iniciados}{' '}
                  {data.mes.negocios_iniciados === 1 ? 'negocio' : 'negocios'}.{' '}
                </>
              )}
              {data.mes.canjes_solicitados > 0 && (
                <>Se solicitaron {data.mes.canjes_solicitados} canjes.</>
              )}
            </Text>
            <Text size="xs" c="dimmed" mt={6}>
              El mes no se compara contra el anterior a propósito: con esta duración de
              procesos, esa variación mide ruido.
            </Text>
          </Paper>
        </>
      )}
    </Stack>
  )
}
