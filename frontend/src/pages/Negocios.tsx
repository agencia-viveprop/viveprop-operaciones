import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ActionIcon,
  Badge,
  Button,
  Group,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
} from '@mantine/core'
import { IconEye, IconPlus, IconTableImport } from '@tabler/icons-react'
import { obtenerCatalogos } from '../api/catalogos'
import {
  listarNegocios,
  type EstadoNegocio,
  type FiltrosNegocios,
  type NegocioResumen,
} from '../api/negocios'
import AvisoUF from '../components/AvisoUF'
import PageHeader from '../components/PageHeader'
import NegocioFichaModal from '../components/NegocioFichaModal'
import NegocioFormModal from '../components/NegocioFormModal'
import CargaMasivaModal from '../components/CargaMasivaModal'
import { COLOR_ESTADO, clp, duracion, fecha, MODELO_CORTO } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'

/** Un negocio con hitos en estados distintos no tiene "un" estado. */
function estadosResumidos(estados: EstadoNegocio[]) {
  return [...new Set(estados)]
}

export default function Negocios({ puedeEditar }: { puedeEditar: boolean }) {
  const [filtros, setFiltros] = useState<FiltrosNegocios>({})
  const [fichaId, setFichaId] = useState<number | null>(null)
  const [formAbierto, setFormAbierto] = useState(false)
  const [cargaAbierta, setCargaAbierta] = useState(false)

  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const consulta = useQuery({
    queryKey: ['negocios', filtros],
    queryFn: () => listarNegocios(filtros),
  })
  const { data: negocios } = consulta

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
            <Group gap="xs">
              <Button
                variant="light"
                leftSection={<IconTableImport size={16} />}
                onClick={() => setCargaAbierta(true)}
              >
                Carga masiva
              </Button>
              <Button color="accent" leftSection={<IconPlus size={16} />} onClick={() => setFormAbierto(true)}>
                Nuevo negocio
              </Button>
            </Group>
          )
        }
      />

      {/* Sin UF vigente no se puede valorizar, y eso rompe el alta. */}
      <AvisoUF />

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

      {!negocios && <EstadoConsulta de={consulta} alto={160} vacio="No hay negocios que coincidan." />}

      {negocios && (
        <Table.ScrollContainer minWidth={1000}>
          <Table striped withTableBorder highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Código</Table.Th>
                <Table.Th>Propiedad</Table.Th>
                <Table.Th>Modelo</Table.Th>
                <Table.Th>Etapa</Table.Th>
                <Table.Th>Alianza</Table.Th>
                <Table.Th>Estado</Table.Th>
                <Table.Th ta="right">Abierto</Table.Th>
                <Table.Th ta="right">Última gestión</Table.Th>
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
                  <Table.Td>
                    {n.etapa ? (
                      <Badge variant="default">{n.etapa}</Badge>
                    ) : (
                      <Text size="sm" c="dimmed">—</Text>
                    )}
                  </Table.Td>
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
                  <Table.Td ta="right">
                    <Text size="xs">{duracion(n.duraciones.dias_abierto)}</Text>
                    {n.fecha_inicio && (
                      <Text size="xs" c="dimmed">
                        desde {fecha(n.fecha_inicio)}
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td ta="right">
                    {/* Nulo es "nunca se registró un movimiento", no cero. Hoy es
                        el caso de todos: el pipeline nunca se usó. */}
                    {n.duraciones.dias_sin_gestion === null ? (
                      <Text size="xs" c="dimmed">
                        sin gestión
                      </Text>
                    ) : (
                      <Text size="xs">hace {duracion(n.duraciones.dias_sin_gestion)}</Text>
                    )}
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
                  <Table.Th colSpan={8}>Total</Table.Th>
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
      <CargaMasivaModal abierto={cargaAbierta} onCerrar={() => setCargaAbierta(false)} />

      <NegocioFormModal
        abierto={formAbierto}
        onClose={() => setFormAbierto(false)}
      />
    </Stack>
  )
}
