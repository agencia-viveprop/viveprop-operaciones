import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ActionIcon,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
} from '@mantine/core'
import { IconEye, IconPlus } from '@tabler/icons-react'
import { obtenerCatalogos } from '../api/catalogos'
import {
  listarNegocios,
  type EstadoNegocio,
  type FiltrosNegocios,
  type NegocioResumen,
} from '../api/negocios'
import PageHeader from '../components/PageHeader'
import NegocioFichaModal from '../components/NegocioFichaModal'
import NegocioFormModal from '../components/NegocioFormModal'
import { COLOR_ESTADO, clp, MODELO_CORTO } from '../components/negociosFormato'

/** Un negocio con hitos en estados distintos no tiene "un" estado. */
function estadosResumidos(estados: EstadoNegocio[]) {
  return [...new Set(estados)]
}

export default function Negocios({ puedeEditar }: { puedeEditar: boolean }) {
  const [filtros, setFiltros] = useState<FiltrosNegocios>({})
  const [fichaId, setFichaId] = useState<number | null>(null)
  const [formAbierto, setFormAbierto] = useState(false)

  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const { data: negocios, isLoading } = useQuery({
    queryKey: ['negocios', filtros],
    queryFn: () => listarNegocios(filtros),
  })

  const alianzas = catalogos?.alianzas ?? []
  const nombreAlianza = (id: number | null) =>
    alianzas.find((a) => a.id === id)?.nombre ?? '—'

  const totales = (negocios ?? []).reduce(
    (acc, n) => ({
      total: acc.total + Number(n.comision_total),
      realVp: acc.realVp + Number(n.comision_real_vp),
    }),
    { total: 0, realVp: 0 },
  )

  return (
    <Stack gap="md">
      <PageHeader
        title="Negocios"
        subtitle={
          negocios
            ? `${negocios.length} negocios · comisión real VP ${clp(totales.realVp)}`
            : undefined
        }
        action={
          puedeEditar && (
            <Button color="accent" leftSection={<IconPlus size={16} />} onClick={() => setFormAbierto(true)}>
              Nuevo negocio
            </Button>
          )
        }
      />

      <Group>
        <TextInput
          placeholder="Código"
          value={filtros.codigo ?? ''}
          onChange={(e) => setFiltros({ ...filtros, codigo: e.currentTarget.value })}
          w={140}
        />
        <Select
          placeholder="Modelo"
          data={(catalogos?.modelos_negocio ?? []).map((m) => ({ value: m.codigo, label: m.nombre }))}
          value={filtros.modelo ?? null}
          onChange={(v) => setFiltros({ ...filtros, modelo: v ?? undefined })}
          clearable
          w={230}
        />
        <Select
          placeholder="Estado"
          data={(catalogos?.estados_negocio ?? []).map((e) => ({ value: e.codigo, label: e.nombre }))}
          value={filtros.estado ?? null}
          onChange={(v) => setFiltros({ ...filtros, estado: v ?? undefined })}
          clearable
          w={160}
        />
        <Select
          placeholder="Alianza"
          data={alianzas.map((a) => ({ value: String(a.id), label: a.nombre }))}
          value={filtros.alianza_id ?? null}
          onChange={(v) => setFiltros({ ...filtros, alianza_id: v ?? undefined })}
          clearable
          w={180}
        />
      </Group>

      {isLoading && (
        <Center h={160}>
          <Loader />
        </Center>
      )}

      {negocios && (
        <Table.ScrollContainer minWidth={900}>
          <Table striped withTableBorder highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Código</Table.Th>
                <Table.Th>Propiedad</Table.Th>
                <Table.Th>Modelo</Table.Th>
                <Table.Th>Alianza</Table.Th>
                <Table.Th>Estado</Table.Th>
                <Table.Th ta="right">Comisión total</Table.Th>
                <Table.Th ta="right">Real VP</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {negocios.map((n: NegocioResumen) => (
                <Table.Tr key={n.id} onClick={() => setFichaId(n.id)} style={{ cursor: 'pointer' }}>
                  <Table.Td fw={600}>
                    {n.codigo}
                    {n.cantidad_hitos > 1 && (
                      <Badge ml={6} size="xs" variant="light" color="brand">
                        {n.cantidad_hitos} hitos
                      </Badge>
                    )}
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{n.direccion}</Text>
                    <Text size="xs" c="dimmed">
                      {[n.unidad, n.comuna].filter(Boolean).join(' · ')}
                    </Text>
                  </Table.Td>
                  <Table.Td>{MODELO_CORTO[n.modelo]}</Table.Td>
                  <Table.Td>{nombreAlianza(n.alianza_id)}</Table.Td>
                  <Table.Td>
                    <Group gap={4}>
                      {estadosResumidos(n.estados).map((e) => (
                        <Badge key={e} color={COLOR_ESTADO[e]} variant="light">
                          {e}
                        </Badge>
                      ))}
                    </Group>
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace">{clp(n.comision_total)}</Table.Td>
                  <Table.Td ta="right" ff="monospace" fw={600}>{clp(n.comision_real_vp)}</Table.Td>
                  <Table.Td>
                    <ActionIcon variant="subtle" aria-label="Ver ficha">
                      <IconEye size={18} />
                    </ActionIcon>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
            {negocios.length > 0 && (
              <Table.Tfoot>
                <Table.Tr>
                  <Table.Th colSpan={5}>Total</Table.Th>
                  <Table.Th ta="right" ff="monospace">{clp(totales.total)}</Table.Th>
                  <Table.Th ta="right" ff="monospace">{clp(totales.realVp)}</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Tfoot>
            )}
          </Table>
        </Table.ScrollContainer>
      )}

      {negocios?.length === 0 && <Text c="dimmed">No hay negocios que calcen con el filtro.</Text>}

      <NegocioFichaModal
        negocioId={fichaId}
        onClose={() => setFichaId(null)}
        puedeEditar={puedeEditar}
      />
      <NegocioFormModal
        abierto={formAbierto}
        onClose={() => setFormAbierto(false)}
      />
    </Stack>
  )
}
