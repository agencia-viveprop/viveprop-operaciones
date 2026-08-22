import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Center,
  Group,
  Loader,
  Paper,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from '@mantine/core'
import { IconArrowsExchange, IconBriefcase } from '@tabler/icons-react'
import { obtenerBandeja, type FilaBandeja, type NivelSemaforo } from '../api/canjes'
import BandejaNegocios from '../components/BandejaNegocios'
import PageHeader from '../components/PageHeader'
import SeguimientoModal from '../components/SeguimientoModal'
import { fecha } from '../components/negociosFormato'

/**
 * El nivel se muestra siempre con su palabra, nunca con el color solo. En este
 * proyecto eso además está anotado en `theme.ts`: el coral de acento y el rojo
 * crítico se parecen entre sí, así que el color por sí mismo no distingue.
 */
const NIVELES: Record<NivelSemaforo, { texto: string; color: string; ayuda: string }> = {
  sin_gestion: {
    texto: 'Sin gestión',
    color: 'gray',
    ayuda: 'Nunca se registró un movimiento en la app',
  },
  critico: { texto: 'Crítico', color: 'critical', ayuda: 'Más de 48 horas sin gestión' },
  advertencia: { texto: 'Advertencia', color: 'warning', ayuda: 'Entre 24 y 48 horas' },
  al_dia: { texto: 'Al día', color: 'good', ayuda: 'Menos de 24 horas' },
}

const ORDEN: NivelSemaforo[] = ['sin_gestion', 'critico', 'advertencia', 'al_dia']

const ETAPA_LABELS: Record<string, string> = {
  SIN_ETAPA: 'Sin etapa',
  EN_REVISION: 'En revisión',
  PROCESO_DE_ACUERDO: 'Proceso de acuerdo',
  EN_OFERTA: 'En oferta',
  EN_NEGOCIO: 'En negocio',
  CERRADO: 'Cerrado',
}

function espera(f: FilaBandeja): string {
  if (f.horas_sin_gestion === null) return '—'
  const h = f.horas_sin_gestion
  if (h < 48) return `${Math.round(h)} h`
  return `${Math.floor(h / 24)} días`
}

/**
 * "Qué me toca hoy", para los dos dominios.
 *
 * Van con selector y no apilados, igual que los dashboards de Inicio: son dos
 * tipos de gestión con relojes distintos --canjes se mide en horas, negocios en
 * meses-- y juntarlos invitaría a compararlos.
 */
export default function Bandeja({ puedeEditar }: { puedeEditar: boolean }) {
  const [vista, setVista] = useState('canjes')
  const [filtro, setFiltro] = useState<string>('atencion')
  const [seguimientoId, setSeguimientoId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['bandeja'],
    queryFn: obtenerBandeja,
    enabled: vista === 'canjes',
  })

  const selector = (
    <SegmentedControl
      color="accent"
      value={vista}
      onChange={setVista}
      data={[
        {
          value: 'canjes',
          label: (
            <Group gap={6} wrap="nowrap">
              <IconArrowsExchange size={15} />
              Canjes
            </Group>
          ),
        },
        {
          value: 'negocios',
          label: (
            <Group gap={6} wrap="nowrap">
              <IconBriefcase size={15} />
              Negocios
            </Group>
          ),
        },
      ]}
    />
  )

  if (vista === 'negocios') {
    return (
      <Stack gap="md">
        <PageHeader
          title="Qué me toca hoy"
          subtitle="Negocios con liquidaciones abiertas, ordenados por cuánto llevan sin moverse."
          action={selector}
        />
        <BandejaNegocios puedeEditar={puedeEditar} />
      </Stack>
    )
  }

  if (isLoading) {
    return (
      <Center h={240}>
        <Loader />
      </Center>
    )
  }
  if (!data) return null

  const { resumen, filas } = data
  const requierenAtencion =
    resumen.sin_gestion + resumen.critico + resumen.advertencia

  const visibles =
    filtro === 'todos'
      ? filas
      : filtro === 'atencion'
        ? filas.filter((f) => f.nivel !== 'al_dia')
        : filas.filter((f) => f.nivel === filtro)

  return (
    <Stack gap="md">
      <PageHeader
        title="Qué me toca hoy"
        subtitle={`${requierenAtencion} de ${filas.length} canjes abiertos requieren atención. Los umbrales son los de CONFIG: ${data.umbral_critico_horas} horas es crítico, ${data.umbral_advertencia_horas} es advertencia.`}
        action={selector}
      />

      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        {ORDEN.map((nivel) => (
          <Paper key={nivel} withBorder radius="md" p="md">
            <Group gap="xs" mb={4}>
              <Badge color={NIVELES[nivel].color} variant="light">
                {NIVELES[nivel].texto}
              </Badge>
            </Group>
            <Text size="28px" fw={800} lh={1.1}>
              {resumen[nivel]}
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              {NIVELES[nivel].ayuda}
            </Text>
          </Paper>
        ))}
      </SimpleGrid>

      <SegmentedControl
        value={filtro}
        onChange={setFiltro}
        data={[
          { value: 'atencion', label: `Requieren atención (${requierenAtencion})` },
          { value: 'sin_gestion', label: `Sin gestión (${resumen.sin_gestion})` },
          { value: 'critico', label: `Críticos (${resumen.critico})` },
          { value: 'todos', label: `Todos (${filas.length})` },
        ]}
      />

      {visibles.length === 0 ? (
        <Paper withBorder radius="md" p="xl">
          <Text ta="center" c="dimmed">
            Nada pendiente acá. {filtro === 'atencion' && 'Todos los canjes abiertos están al día.'}
          </Text>
        </Paper>
      ) : (
        <Table.ScrollContainer minWidth={860}>
          <Table striped withTableBorder highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Estado</Table.Th>
                <Table.Th>Canje</Table.Th>
                <Table.Th>Corredores</Table.Th>
                <Table.Th>Propiedad</Table.Th>
                <Table.Th>Etapa</Table.Th>
                <Table.Th ta="right">Espera</Table.Th>
                <Table.Th>Última gestión</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {visibles.map((f) => (
                <Table.Tr
                  key={f.canje_id}
                  onClick={() => setSeguimientoId(f.canje_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <Table.Td>
                    <Badge color={NIVELES[f.nivel].color} variant="light">
                      {NIVELES[f.nivel].texto}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" fw={600}>
                      #{f.canje_id}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {fecha(f.fecha_solicitud)}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{f.corredor_solicitante_nombre ?? '—'}</Text>
                    <Text size="xs" c="dimmed">
                      {f.corredor_propietario_nombre ?? '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{f.direccion ?? '—'}</Text>
                    <Text size="xs" c="dimmed">
                      {f.comuna ?? '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{ETAPA_LABELS[f.etapa] ?? f.etapa}</Text>
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace">
                    {espera(f)}
                  </Table.Td>
                  <Table.Td>
                    {f.ultimo_movimiento_nombre ? (
                      <>
                        <Text size="sm">{f.ultimo_movimiento_nombre}</Text>
                        <Text size="xs" c="dimmed">
                          {fecha(f.ultimo_movimiento)}
                        </Text>
                      </>
                    ) : (
                      <Text size="sm" c="dimmed">
                        Nunca
                      </Text>
                    )}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}

      <Text size="xs" c="dimmed">
        Hacer clic en una fila abre el seguimiento del canje. Registrar un movimiento lo saca
        de "sin gestión" y reinicia el reloj.
      </Text>

      <SeguimientoModal
        canjeId={seguimientoId}
        opened={seguimientoId !== null}
        onClose={() => setSeguimientoId(null)}
        puedeEditar={puedeEditar}
      />
    </Stack>
  )
}
