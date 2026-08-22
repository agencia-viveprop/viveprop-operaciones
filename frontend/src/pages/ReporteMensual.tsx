import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ActionIcon,
  Badge,
  Center,
  Group,
  Loader,
  Paper,
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
  type Comparacion,
  type Variacion,
} from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp } from '../components/negociosFormato'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

/** Las métricas que son plata se muestran como plata; el resto, como cuenta. */
const EN_PESOS = new Set(['Comisión real ViveProp', 'Comisión total'])

function rotulo(etiqueta: string): string {
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
 * **`pct` nulo no es cero ni infinito: es que no hay base.** Si el mes de
 * referencia tuvo cero, no existe porcentaje que calcular, y mostrar uno sería
 * inventarlo. Se dice "sin base" y se muestra la diferencia absoluta, que sí
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
        <Tooltip label="El mes de referencia estuvo en cero: no hay porcentaje que calcular">
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
        {ayuda} · contra {rotulo(c.contra.etiqueta)}
      </Text>
      <div className="tabla-scroll-x">
        <Table striped fz="xs" className="tabla-una-linea">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Métrica</Table.Th>
              <Table.Th ta="right">Este mes</Table.Th>
              <Table.Th ta="right">{rotulo(c.contra.etiqueta)}</Table.Th>
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
 * El mes contra dos referencias.
 *
 * **Las dos comparaciones responden cosas distintas**, y por eso van las dos: el
 * mes anterior dice si la tendencia corta sube o baja, y el mismo mes del año
 * pasado dice si eso es tendencia o es estacionalidad. Con una sola no se
 * distingue "vamos mal" de "agosto siempre es flojo".
 *
 * No hay serie de veinticuatro meses acá: eso ya está en los gráficos "por mes"
 * del dashboard y responde otra pregunta.
 */
export default function ReporteMensual() {
  const ahora = new Date()
  const [desplazamiento, setDesplazamiento] = useState(0)

  const cursor = new Date(ahora.getFullYear(), ahora.getMonth() + desplazamiento, 1)
  const anio = cursor.getFullYear()
  const mes = cursor.getMonth() + 1

  const { data, isLoading } = useQuery({
    queryKey: ['reporte-mensual', anio, mes],
    queryFn: () => obtenerReporteMensual(anio, mes),
  })

  return (
    <Stack gap="md">
      <PageHeader
        title="Reporte mensual"
        subtitle="El mes contra el anterior y contra el mismo mes del año pasado. El primero dice si sube o baja; el segundo, si es tendencia o estacionalidad."
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

      {isLoading || !data ? (
        <Center h={240}>
          <Loader />
        </Center>
      ) : (
        <>
          <SimpleGrid cols={{ base: 2, sm: 4 }}>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                COMISIÓN REAL VP
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {clp(data.mes.comision_real_vp)}
              </Text>
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                LIQUIDACIONES
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {data.mes.hitos_cerrados}
              </Text>
              <Text size="xs" c="dimmed" mt={4}>
                cerradas en el mes
              </Text>
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                NEGOCIOS INICIADOS
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {data.mes.negocios_iniciados}
              </Text>
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                CANJES SOLICITADOS
              </Text>
              <Text size="22px" fw={800} mt={4} lh={1.1}>
                {data.mes.canjes_solicitados}
              </Text>
            </Paper>
          </SimpleGrid>

          <TablaComparacion
            titulo="Contra el mes anterior"
            ayuda="Si la tendencia corta sube o baja"
            c={data.mes_anterior}
          />
          <TablaComparacion
            titulo="Contra el mismo mes del año pasado"
            ayuda="Si eso es tendencia o es estacionalidad"
            c={data.mismo_mes_anio_anterior}
          />
        </>
      )}
    </Stack>
  )
}
