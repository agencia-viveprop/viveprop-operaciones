import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Card,
  Center,
  Divider,
  Group,
  Loader,
  Modal,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'
import { obtenerCatalogos } from '../api/catalogos'
import { obtenerNegocio, type Hito } from '../api/negocios'
import { clp, COLOR_ESTADO, fecha, MODELO_CORTO, pct, uf } from './negociosFormato'

function Dato({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {label}
      </Text>
      <Text size="sm">{children}</Text>
    </div>
  )
}

/** Cuando la comisión no cuadra con su reparto, hay que decirlo, no esconderlo. */
function descuadre(h: Hito): number | null {
  if (h.comision_total === null || h.comision_broker === null || h.comision_vp_bruta === null) {
    return null
  }
  const dif = Number(h.comision_broker) + Number(h.comision_vp_bruta) - Number(h.comision_total)
  return Math.abs(dif) > 1 ? dif : null
}

function FichaHito({ hito }: { hito: Hito }) {
  const dif = descuadre(hito)
  const usaManual = hito.valor_clp_manual !== null

  return (
    <Card withBorder radius="md" p="md">
      <Group justify="space-between" mb="sm">
        <Group gap="xs">
          <Title order={5}>{hito.nombre ?? 'Liquidación única'}</Title>
          <Badge color={COLOR_ESTADO[hito.estado]} variant="light">
            {hito.estado}
          </Badge>
          {hito.etapa && <Badge variant="default">{hito.etapa}</Badge>}
        </Group>
        <Text size="sm" c="dimmed">
          {fecha(hito.fecha_inicio)}
          {hito.fecha_cierre && ` → ${fecha(hito.fecha_cierre)}`}
        </Text>
      </Group>

      <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm" mb="sm">
        <Dato label="Valor">
          {hito.moneda === 'UF' ? uf(hito.valor_negocio) : clp(hito.valor_negocio)}
        </Dato>
        <Dato label="UF congelada">{hito.uf_snapshot ? uf(hito.uf_snapshot) : '—'}</Dato>
        <Dato label="Valor calculado">{clp(hito.valor_clp_calculado)}</Dato>
        <Dato label="Base de comisión">
          <Text span fw={600}>{clp(hito.base_comision)}</Text>
        </Dato>
      </SimpleGrid>

      {usaManual && (
        <Alert color="warning" variant="light" mb="sm" title="Valor ingresado a mano">
          <Text size="sm">
            La comisión se calculó sobre {clp(hito.valor_clp_manual)} en vez de{' '}
            {clp(hito.valor_clp_calculado)}.
            {hito.motivo_valor_manual && ` Motivo: ${hito.motivo_valor_manual}`}
          </Text>
        </Alert>
      )}

      <Divider my="sm" label="Comisiones" labelPosition="left" />

      <Table withRowBorders={false} verticalSpacing={4}>
        <Table.Tbody>
          <Table.Tr>
            <Table.Td>Comisión total del negocio</Table.Td>
            <Table.Td ta="right" ff="monospace">{clp(hito.comision_total)}</Table.Td>
            <Table.Td w={90} ta="right" c="dimmed" ff="monospace">
              {pct(hito.comision_total !== null && hito.base_comision
                ? Number(hito.comision_total) / Number(hito.base_comision)
                : null)}
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td pl="lg" c="dimmed">Corredor aliado</Table.Td>
            <Table.Td ta="right" ff="monospace" c="dimmed">{clp(hito.comision_broker)}</Table.Td>
            <Table.Td />
          </Table.Tr>
          <Table.Tr>
            <Table.Td pl="lg">ViveProp bruta</Table.Td>
            <Table.Td ta="right" ff="monospace">{clp(hito.comision_vp_bruta)}</Table.Td>
            <Table.Td />
          </Table.Tr>
          {Number(hito.comision_tercero) > 0 && (
            <Table.Tr>
              <Table.Td pl="xl" c="dimmed">
                Tercero{hito.nombre_tercero ? ` · ${hito.nombre_tercero}` : ''}
              </Table.Td>
              <Table.Td ta="right" ff="monospace" c="dimmed">−{clp(hito.comision_tercero)}</Table.Td>
              <Table.Td />
            </Table.Tr>
          )}
          <Table.Tr>
            <Table.Td pl="xl" c="dimmed">Equipo ViveProp</Table.Td>
            <Table.Td ta="right" ff="monospace" c="dimmed">−{clp(hito.comision_equipo)}</Table.Td>
            <Table.Td />
          </Table.Tr>
          {Number(hito.rebate_concentrador) > 0 && (
            <Table.Tr>
              <Table.Td pl="xl" c="good">Rebate del concentrador</Table.Td>
              <Table.Td ta="right" ff="monospace" c="good">+{clp(hito.rebate_concentrador)}</Table.Td>
              <Table.Td />
            </Table.Tr>
          )}
          <Table.Tr>
            <Table.Td fw={700}>Comisión real ViveProp</Table.Td>
            <Table.Td ta="right" ff="monospace" fw={700}>{clp(hito.comision_real_vp)}</Table.Td>
            <Table.Td />
          </Table.Tr>
        </Table.Tbody>
      </Table>

      {dif !== null && (
        <Alert
          color="critical"
          variant="light"
          mt="sm"
          icon={<IconAlertTriangle size={18} />}
          title="La comisión total no cuadra con su reparto"
        >
          <Text size="sm">
            El corredor aliado y ViveProp suman {clp(Number(hito.comision_broker) + Number(hito.comision_vp_bruta))},
            que es {clp(Math.abs(dif))} {dif > 0 ? 'más' : 'menos'} que la comisión total registrada.
            Viene así del Excel y hay que resolverlo.
          </Text>
        </Alert>
      )}
    </Card>
  )
}

export default function NegocioFichaModal({
  negocioId,
  onClose,
}: {
  negocioId: number | null
  onClose: () => void
  puedeEditar: boolean
}) {
  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const { data: negocio, isLoading } = useQuery({
    queryKey: ['negocio', negocioId],
    queryFn: () => obtenerNegocio(negocioId!),
    enabled: negocioId !== null,
  })

  const nombreCatalogo = (id: number | null) => {
    if (id === null || !catalogos) return '—'
    const todos = [
      ...catalogos.alianzas,
      ...catalogos.tipos_operacion,
      ...catalogos.tipos_propiedad,
      ...catalogos.estados_propiedad,
    ]
    return todos.find((c) => c.id === id)?.nombre ?? '—'
  }

  const totalReal = (negocio?.hitos ?? []).reduce((a, h) => a + Number(h.comision_real_vp ?? 0), 0)

  return (
    <Modal
      opened={negocioId !== null}
      onClose={onClose}
      title={negocio ? `${negocio.codigo} · ${negocio.propiedad.direccion}` : 'Negocio'}
      size="xl"
    >
      {isLoading && (
        <Center h={200}>
          <Loader />
        </Center>
      )}

      {negocio && (
        <Stack gap="md">
          <SimpleGrid cols={{ base: 2, sm: 3 }} spacing="sm">
            <Dato label="Modelo">{MODELO_CORTO[negocio.modelo]}</Dato>
            <Dato label="Alianza">{nombreCatalogo(negocio.alianza_id)}</Dato>
            <Dato label="Operación">{nombreCatalogo(negocio.tipo_operacion_id)}</Dato>
            <Dato label="Propiedad">
              {negocio.propiedad.direccion}
              {negocio.propiedad.unidad && ` · ${negocio.propiedad.unidad}`}
            </Dato>
            <Dato label="Comuna">{negocio.propiedad.comuna}</Dato>
            <Dato label="Corredor">{negocio.corredor_agente ?? '—'}</Dato>
            <Dato label="Vendedor / Arrendador">{negocio.vendedor_arrendador ?? '—'}</Dato>
            <Dato label="Comprador / Arrendatario">{negocio.comprador_arrendatario ?? '—'}</Dato>
          </SimpleGrid>

          {negocio.observaciones && (
            <Alert variant="light" color="brand" title="Observaciones">
              <Text size="sm">{negocio.observaciones}</Text>
            </Alert>
          )}

          <Group justify="space-between" align="baseline">
            <Title order={4}>
              {negocio.hitos.length === 1 ? 'Liquidación' : `${negocio.hitos.length} liquidaciones`}
            </Title>
            {negocio.hitos.length > 1 && (
              <Text size="sm">
                Comisión real VP del negocio:{' '}
                <Text span fw={700} ff="monospace">{clp(totalReal)}</Text>
              </Text>
            )}
          </Group>

          {negocio.hitos.map((h) => (
            <FichaHito key={h.id} hito={h} />
          ))}
        </Stack>
      )}
    </Modal>
  )
}
