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
import {
  IconArrowsExchange,
  IconBriefcase,
  IconChevronLeft,
  IconChevronRight,
} from '@tabler/icons-react'
import {
  aISO,
  lunesDe,
  obtenerReporteSemanal,
  type Seccion,
} from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp, fecha } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'

const ETAPA_LABELS: Record<string, string> = {
  RECEPCION: 'Recepción',
  EN_REVISION: 'En revisión',
  PROCESO_DE_ACUERDO: 'Proceso de acuerdo',
  EN_OFERTA: 'En oferta',
  EN_NEGOCIO: 'En negocio',
  CERRADO: 'Cierre',
}

const etapaTexto = (e: string | null) => (e ? (ETAPA_LABELS[e] ?? e) : '—')

/** "17 al 23 de agosto de 2026", o con los dos meses si la semana los cruza. */
function rotulo(desde: string, hasta: string): string {
  const d = new Date(`${desde}T12:00:00`)
  const h = new Date(`${hasta}T12:00:00`)
  const mes = (f: Date) => f.toLocaleDateString('es-CL', { month: 'long' })
  const cola = `de ${mes(h)} de ${h.getFullYear()}`
  return d.getMonth() === h.getMonth()
    ? `${d.getDate()} al ${h.getDate()} ${cola}`
    : `${d.getDate()} de ${mes(d)} al ${h.getDate()} ${cola}`
}

function Tile({
  rotulo: texto,
  valor,
  ayuda,
  color,
  activo,
  onClick,
}: {
  rotulo: string
  valor: string
  ayuda: string
  color: string
  activo: boolean
  onClick: () => void
}) {
  return (
    <Paper
      withBorder
      radius="md"
      p="md"
      onClick={onClick}
      style={{ cursor: 'pointer', borderColor: activo ? `var(--mantine-color-${color}-6)` : undefined }}
    >
      <Badge color={color} variant="light" mb={6}>
        {texto}
      </Badge>
      <Text size="26px" fw={800} lh={1.1}>
        {valor}
      </Text>
      <Text size="xs" c="dimmed" mt={4}>
        {ayuda}
      </Text>
    </Paper>
  )
}

function TablaCerrados({ seccion, conMonto }: { seccion: Seccion; conMonto: boolean }) {
  return (
    <Table striped withTableBorder fz="xs" className="tabla-una-linea">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Referencia</Table.Th>
          <Table.Th>Detalle</Table.Th>
          <Table.Th>Fecha de cierre</Table.Th>
          {conMonto && <Table.Th ta="right">Comisión real VP</Table.Th>}
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {seccion.cerrados.map((c, i) => (
          <Table.Tr key={`${c.referencia}-${i}`}>
            <Table.Td fw={600}>{c.referencia}</Table.Td>
            <Table.Td>{c.detalle ?? '—'}</Table.Td>
            <Table.Td>{fecha(c.fecha)}</Table.Td>
            {conMonto && (
              <Table.Td ta="right" ff="monospace">
                {clp(c.monto)}
              </Table.Td>
            )}
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

function TablaMovidos({ items, columnaEtapa }: { items: Seccion['avanzados']; columnaEtapa: boolean }) {
  return (
    <Table striped withTableBorder fz="xs" className="tabla-una-linea">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Referencia</Table.Th>
          <Table.Th>Fecha</Table.Th>
          <Table.Th>Qué pasó</Table.Th>
          {columnaEtapa && <Table.Th>Quedó en</Table.Th>}
          <Table.Th>Dónde</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {items.map((m, i) => (
          <Table.Tr key={`${m.referencia}-${i}`}>
            <Table.Td fw={600}>{m.referencia}</Table.Td>
            <Table.Td>{fecha(m.fecha)}</Table.Td>
            <Table.Td>{m.comentario ?? '—'}</Table.Td>
            {columnaEtapa && (
              <Table.Td>
                {m.etapa ? (
                  etapaTexto(m.etapa)
                ) : (
                  // Un movimiento que no mueve la etapa es gestión, no un
                  // avance de pipeline: se dice, no se deja la celda muda.
                  <Text size="xs" c="dimmed">
                    sigue igual
                  </Text>
                )}
              </Table.Td>
            )}
            <Table.Td>{m.detalle ?? '—'}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

function TablaEstancados({ seccion }: { seccion: Seccion }) {
  return (
    <Table striped withTableBorder fz="xs" className="tabla-una-linea">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Referencia</Table.Th>
          <Table.Th ta="right">Sin moverse</Table.Th>
          <Table.Th>Etapa</Table.Th>
          <Table.Th>Dónde</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {seccion.estancados.map((e, i) => (
          <Table.Tr key={`${e.referencia}-${i}`}>
            <Table.Td fw={600}>{e.referencia}</Table.Td>
            <Table.Td ta="right" ff="monospace">
              {e.dias_sin_movimiento ?? '—'} días
            </Table.Td>
            <Table.Td>{etapaTexto(e.etapa)}</Table.Td>
            <Table.Td>{e.detalle ?? '—'}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

function Dominio({
  nombre,
  icono,
  seccion,
  conMonto,
}: {
  nombre: string
  icono: React.ReactNode
  seccion: Seccion
  conMonto: boolean
}) {
  const [bucket, setBucket] = useState('avanzados')

  const listas: Record<string, { largo: number; total: number; nodo: React.ReactNode }> = {
    cerrados: {
      largo: seccion.cerrados.length,
      total: seccion.total_cerrados,
      nodo: <TablaCerrados seccion={seccion} conMonto={conMonto} />,
    },
    avanzados: {
      largo: seccion.avanzados.length,
      total: seccion.total_avanzados,
      nodo: <TablaMovidos items={seccion.avanzados} columnaEtapa />,
    },
    caidos: {
      largo: seccion.caidos.length,
      total: seccion.total_caidos,
      nodo: <TablaMovidos items={seccion.caidos} columnaEtapa={false} />,
    },
    estancados: {
      largo: seccion.estancados.length,
      total: seccion.total_estancados,
      nodo: <TablaEstancados seccion={seccion} />,
    },
  }
  const elegido = listas[bucket]

  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="md">
        <Group gap="xs">
          {icono}
          <Title order={4}>{nombre}</Title>
        </Group>

        <SimpleGrid cols={{ base: 2, sm: 4 }}>
          <Tile
            rotulo="Se cerró"
            valor={conMonto ? clp(seccion.monto_cerrado) : String(seccion.total_cerrados)}
            ayuda={
              conMonto
                ? `${seccion.total_cerrados} hito${seccion.total_cerrados === 1 ? '' : 's'} en comisión real VP`
                : 'canjes cerrados en el período'
            }
            color="good"
            activo={bucket === 'cerrados'}
            onClick={() => setBucket('cerrados')}
          />
          <Tile
            rotulo="Avanzó"
            valor={String(seccion.total_avanzados)}
            ayuda="movimientos registrados, con o sin cambio de etapa"
            color="info"
            activo={bucket === 'avanzados'}
            onClick={() => setBucket('avanzados')}
          />
          <Tile
            rotulo="Se cayó"
            valor={String(seccion.total_caidos)}
            ayuda={conMonto ? 'pérdidas y desistimientos' : 'cancelaciones'}
            color="critical"
            activo={bucket === 'caidos'}
            onClick={() => setBucket('caidos')}
          />
          <Tile
            rotulo="Estancado"
            valor={String(seccion.total_estancados)}
            ayuda="abierto y sin moverse hace más del umbral"
            color="warning"
            activo={bucket === 'estancados'}
            onClick={() => setBucket('estancados')}
          />
        </SimpleGrid>

        {elegido.largo === 0 ? (
          <Text size="sm" c="dimmed" ta="center" py="lg">
            Nada que mostrar acá.
          </Text>
        ) : (
          <Stack gap={4}>
            <div className="tabla-scroll-x">{elegido.nodo}</div>
            {elegido.total > elegido.largo && (
              // Sin esto la lista topeada se leería como el total.
              <Text size="xs" c="dimmed">
                Se muestran {elegido.largo} de {elegido.total}.
              </Text>
            )}
          </Stack>
        )}
      </Stack>
    </Paper>
  )
}

/**
 * El reporte de la semana: qué se cerró, qué avanzó, qué se cayó y qué está
 * estancado, en los dos dominios.
 *
 * Es lo contrario del dashboard. El dashboard responde "cómo vamos" y mira el
 * estado actual; esto responde "qué pasó" y mira los movimientos del período.
 * Por eso no repite las cifras de cartera: sumar lo mismo dos veces con dos
 * cortes distintos es la forma más rápida de que nadie confíe en ninguna.
 *
 * El umbral de estancado es un control y no una constante escondida: 14 días es
 * una estimación, no un dato del negocio, y quien lee el reporte sabe mejor qué
 * es "mucho" en su semana.
 */
export default function ReporteSemanal() {
  const [semanas, setSemanas] = useState(0)
  const [dias, setDias] = useState('14')

  const lunes = lunesDe(new Date(), semanas)
  const domingo = new Date(lunes)
  domingo.setDate(domingo.getDate() + 6)
  const desde = aISO(lunes)
  const hasta = aISO(domingo)

  const consulta = useQuery({
    queryKey: ['reporte-semanal', desde, hasta, dias],
    queryFn: () => obtenerReporteSemanal({ desde, hasta, dias_estancado: Number(dias) }),
  })
  const { data } = consulta

  return (
    <Stack gap="md">
      <PageHeader
        title="Reporte semanal"
        subtitle="Qué pasó en la semana, en negocios y en canjes. El dashboard dice cómo vamos; esto dice qué cambió."
        action={
          <Group gap="xs">
            <Tooltip label="Semana anterior">
              <ActionIcon variant="default" onClick={() => setSemanas((s) => s - 1)} aria-label="Semana anterior">
                <IconChevronLeft size={16} />
              </ActionIcon>
            </Tooltip>
            <Text size="sm" fw={600} w={230} ta="center">
              {rotulo(desde, hasta)}
            </Text>
            <Tooltip label={semanas >= 0 ? 'Todavía no empieza' : 'Semana siguiente'}>
              <ActionIcon
                variant="default"
                disabled={semanas >= 0}
                onClick={() => setSemanas((s) => s + 1)}
                aria-label="Semana siguiente"
              >
                <IconChevronRight size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        }
      />

      <Group gap="xs">
        <Text size="xs" c="dimmed">
          Estancado después de
        </Text>
        <SegmentedControl
          size="xs"
          value={dias}
          onChange={setDias}
          data={[
            { value: '7', label: '7 días' },
            { value: '14', label: '14 días' },
            { value: '30', label: '30 días' },
          ]}
        />
      </Group>

      {!data ? (
        <EstadoConsulta de={consulta} alto={240} />
      ) : (
        <Stack gap="lg">
          <Dominio
            nombre="Negocios"
            icono={<IconBriefcase size={20} />}
            seccion={data.negocios}
            conMonto
          />
          <Dominio
            nombre="Canjes"
            icono={<IconArrowsExchange size={20} />}
            seccion={data.canjes}
            conMonto={false}
          />
        </Stack>
      )}
    </Stack>
  )
}
