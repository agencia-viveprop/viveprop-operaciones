import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  FileButton,
  Group,
  List,
  Modal,
  NumberInput,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core'
import {
  actualizarCanje,
  crearCanje,
  importarCanjes,
  listarCanjes,
  type Canje,
  type CanjeEstado,
  type CanjeEtapa,
  type ImportarResumen,
} from '../api/canjes'

const ETAPA_LABELS: Record<CanjeEtapa, string> = {
  SIN_ETAPA: 'Sin etapa',
  EN_REVISION: 'En revisión',
  PROCESO_DE_ACUERDO: 'Proceso de acuerdo',
  EN_OFERTA: 'En oferta',
  EN_NEGOCIO: 'En negocio',
  CERRADO: 'Cerrado',
}

const ESTADOS: CanjeEstado[] = ['ACTIVO', 'CANCELADO']
const ETAPAS = Object.keys(ETAPA_LABELS) as CanjeEtapa[]
const OPERACIONES = ['VENTA', 'ARRIENDO', 'OTRO']
const MONEDAS = ['CLP', 'UF', 'OTRA']

function vacio() {
  return {
    id: '',
    fecha_solicitud: '',
    corredor_solicitante_nombre: '',
    corredor_solicitante_email: '',
    corredor_propietario_nombre: '',
    corredor_propietario_email: '',
    tipo_operacion: '',
    tipo_inmueble: '',
    comuna: '',
    direccion: '',
    valor_prop: '' as number | '',
    moneda_valor: '',
    link_propiedad: '',
    valor_negocio: '' as number | '',
    valor_negocio_moneda: '',
    comision_dbrokers: '' as number | '',
    comision_dbrokers_moneda: '',
    notas: '',
    estado: 'ACTIVO' as CanjeEstado,
    etapa: 'SIN_ETAPA' as CanjeEtapa,
  }
}

export default function Canjes({ puedeEditar }: { puedeEditar: boolean }) {
  const queryClient = useQueryClient()
  const [filtros, setFiltros] = useState<{ estado: string; etapa: string; comuna: string }>({
    estado: '',
    etapa: '',
    comuna: '',
  })
  const { data: canjes, isLoading } = useQuery({
    queryKey: ['canjes', filtros],
    queryFn: () => listarCanjes(filtros),
  })

  const [modalAbierto, setModalAbierto] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(vacio())

  const [importAbierto, setImportAbierto] = useState(false)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resumenImport, setResumenImport] = useState<ImportarResumen | null>(null)
  const resetArchivoRef = useRef<() => void>(null)

  const importar = useMutation({
    mutationFn: () => importarCanjes(archivo!),
    onSuccess: (resumen) => {
      setResumenImport(resumen)
      queryClient.invalidateQueries({ queryKey: ['canjes'] })
    },
  })

  function cerrarImportModal() {
    setImportAbierto(false)
    setArchivo(null)
    setResumenImport(null)
    resetArchivoRef.current?.()
  }

  const guardar = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = { ...form }
      if (typeof payload.fecha_solicitud === 'string' && payload.fecha_solicitud.length === 10) {
        payload.fecha_solicitud = `${payload.fecha_solicitud}T00:00:00`
      }
      if (payload.valor_prop === '') payload.valor_prop = null
      if (payload.valor_negocio === '') payload.valor_negocio = null
      if (payload.comision_dbrokers === '') payload.comision_dbrokers = null
      ;['tipo_operacion', 'moneda_valor', 'valor_negocio_moneda', 'comision_dbrokers_moneda'].forEach((k) => {
        if (payload[k] === '') payload[k] = null
      })
      if (editandoId !== null) {
        delete payload.id
        return actualizarCanje(editandoId, payload)
      }
      return crearCanje({ ...payload, id: Number(form.id) })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['canjes'] })
      setModalAbierto(false)
    },
  })

  function abrirNuevo() {
    setEditandoId(null)
    setForm(vacio())
    setModalAbierto(true)
  }

  function abrirEditar(c: Canje) {
    setEditandoId(c.id)
    setForm({
      id: String(c.id),
      fecha_solicitud: c.fecha_solicitud?.slice(0, 10) ?? '',
      corredor_solicitante_nombre: c.corredor_solicitante_nombre ?? '',
      corredor_solicitante_email: c.corredor_solicitante_email ?? '',
      corredor_propietario_nombre: c.corredor_propietario_nombre ?? '',
      corredor_propietario_email: c.corredor_propietario_email ?? '',
      tipo_operacion: c.tipo_operacion ?? '',
      tipo_inmueble: c.tipo_inmueble ?? '',
      comuna: c.comuna ?? '',
      direccion: c.direccion ?? '',
      valor_prop: c.valor_prop ?? '',
      moneda_valor: c.moneda_valor ?? '',
      link_propiedad: c.link_propiedad ?? '',
      valor_negocio: c.valor_negocio ?? '',
      valor_negocio_moneda: c.valor_negocio_moneda ?? '',
      comision_dbrokers: c.comision_dbrokers ?? '',
      comision_dbrokers_moneda: c.comision_dbrokers_moneda ?? '',
      notas: c.notas ?? '',
      estado: c.estado,
      etapa: c.etapa,
    })
    setModalAbierto(true)
  }

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Canjes</Title>
        {puedeEditar && (
          <Group>
            <Button variant="light" onClick={() => setImportAbierto(true)}>
              Importar Canjes
            </Button>
            <Button onClick={abrirNuevo}>Nuevo canje</Button>
          </Group>
        )}
      </Group>

      <Group>
        <Select
          placeholder="Estado"
          data={ESTADOS}
          value={filtros.estado || null}
          onChange={(v) => setFiltros({ ...filtros, estado: v ?? '' })}
          clearable
          w={160}
        />
        <Select
          placeholder="Etapa"
          data={ETAPAS.map((e) => ({ value: e, label: ETAPA_LABELS[e] }))}
          value={filtros.etapa || null}
          onChange={(v) => setFiltros({ ...filtros, etapa: v ?? '' })}
          clearable
          w={200}
        />
        <TextInput
          placeholder="Comuna"
          value={filtros.comuna}
          onChange={(e) => setFiltros({ ...filtros, comuna: e.currentTarget.value })}
          w={160}
        />
      </Group>

      <Table striped withTableBorder highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Fecha</Table.Th>
            <Table.Th>Corredor solicitante</Table.Th>
            <Table.Th>Comuna</Table.Th>
            <Table.Th>Operación</Table.Th>
            <Table.Th>Estado</Table.Th>
            <Table.Th>Etapa</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {!isLoading &&
            canjes?.map((c) => (
              <Table.Tr key={c.id} onClick={() => puedeEditar && abrirEditar(c)} style={{ cursor: puedeEditar ? 'pointer' : 'default' }}>
                <Table.Td>{c.fecha_solicitud?.slice(0, 10)}</Table.Td>
                <Table.Td>{c.corredor_solicitante_nombre}</Table.Td>
                <Table.Td>{c.comuna}</Table.Td>
                <Table.Td>{c.tipo_operacion}</Table.Td>
                <Table.Td>
                  <Badge color={c.estado === 'ACTIVO' ? 'good' : 'critical'} variant="filled">
                    {c.estado}
                  </Badge>
                </Table.Td>
                <Table.Td>{ETAPA_LABELS[c.etapa]}</Table.Td>
              </Table.Tr>
            ))}
        </Table.Tbody>
      </Table>
      {!isLoading && canjes?.length === 0 && <Text c="dimmed">No hay canjes que calcen con el filtro.</Text>}

      <Modal opened={modalAbierto} onClose={() => setModalAbierto(false)} title={editandoId ? `Canje #${editandoId}` : 'Nuevo canje'} size="lg">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            guardar.mutate()
          }}
        >
          <Stack gap="sm">
            <SimpleGrid cols={2}>
              {editandoId === null && (
                <NumberInput
                  label="ID (mismo ID_CANJE de Dataprop)"
                  required
                  value={form.id === '' ? undefined : Number(form.id)}
                  onChange={(v) => setForm({ ...form, id: String(v ?? '') })}
                  hideControls
                />
              )}
              <TextInput
                label="Fecha de solicitud"
                type="date"
                required
                disabled={editandoId !== null}
                description={editandoId !== null ? 'No editable (viene de Dataprop)' : undefined}
                value={form.fecha_solicitud}
                onChange={(e) => setForm({ ...form, fecha_solicitud: e.currentTarget.value })}
              />
              <Select label="Estado" data={ESTADOS} value={form.estado} onChange={(v) => v && setForm({ ...form, estado: v as CanjeEstado })} />
              <Select
                label="Etapa"
                data={ETAPAS.map((e) => ({ value: e, label: ETAPA_LABELS[e] }))}
                value={form.etapa}
                onChange={(v) => v && setForm({ ...form, etapa: v as CanjeEtapa })}
              />
              <TextInput
                label="Corredor solicitante"
                value={form.corredor_solicitante_nombre}
                onChange={(e) => setForm({ ...form, corredor_solicitante_nombre: e.currentTarget.value })}
              />
              <TextInput
                label="Email solicitante"
                value={form.corredor_solicitante_email}
                onChange={(e) => setForm({ ...form, corredor_solicitante_email: e.currentTarget.value })}
              />
              <TextInput
                label="Corredor propietario"
                value={form.corredor_propietario_nombre}
                onChange={(e) => setForm({ ...form, corredor_propietario_nombre: e.currentTarget.value })}
              />
              <TextInput
                label="Email propietario"
                value={form.corredor_propietario_email}
                onChange={(e) => setForm({ ...form, corredor_propietario_email: e.currentTarget.value })}
              />
              <Select
                label="Tipo operación"
                data={OPERACIONES}
                value={form.tipo_operacion || null}
                onChange={(v) => setForm({ ...form, tipo_operacion: v ?? '' })}
                clearable
              />
              <TextInput label="Tipo inmueble" value={form.tipo_inmueble} onChange={(e) => setForm({ ...form, tipo_inmueble: e.currentTarget.value })} />
              <TextInput label="Comuna" value={form.comuna} onChange={(e) => setForm({ ...form, comuna: e.currentTarget.value })} />
              <TextInput label="Dirección" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.currentTarget.value })} />
              <Group gap="xs" align="flex-end">
                <NumberInput
                  label="Valor propiedad"
                  value={form.valor_prop}
                  onChange={(v) => setForm({ ...form, valor_prop: v as number | '' })}
                  flex={1}
                />
                <Select data={MONEDAS} value={form.moneda_valor || null} onChange={(v) => setForm({ ...form, moneda_valor: v ?? '' })} w={80} />
              </Group>
              <TextInput label="Link propiedad" value={form.link_propiedad} onChange={(e) => setForm({ ...form, link_propiedad: e.currentTarget.value })} />
              <Group gap="xs" align="flex-end">
                <NumberInput
                  label="Valor negocio (acordado)"
                  value={form.valor_negocio}
                  onChange={(v) => setForm({ ...form, valor_negocio: v as number | '' })}
                  flex={1}
                />
                <Select
                  data={MONEDAS}
                  value={form.valor_negocio_moneda || null}
                  onChange={(v) => setForm({ ...form, valor_negocio_moneda: v ?? '' })}
                  w={80}
                />
              </Group>
              <Group gap="xs" align="flex-end">
                <NumberInput
                  label="Comisión DBrokers"
                  value={form.comision_dbrokers}
                  onChange={(v) => setForm({ ...form, comision_dbrokers: v as number | '' })}
                  flex={1}
                />
                <Select
                  data={MONEDAS}
                  value={form.comision_dbrokers_moneda || null}
                  onChange={(v) => setForm({ ...form, comision_dbrokers_moneda: v ?? '' })}
                  w={80}
                />
              </Group>
            </SimpleGrid>
            <Textarea label="Notas" value={form.notas} onChange={(e) => setForm({ ...form, notas: e.currentTarget.value })} />
            {guardar.isError && <Alert color="red">{(guardar.error as Error).message}</Alert>}
            <Button type="submit" loading={guardar.isPending}>
              Guardar
            </Button>
          </Stack>
        </form>
      </Modal>

      <Modal opened={importAbierto} onClose={cerrarImportModal} title="Importar Canjes">
        <Stack gap="sm">
          <Text size="sm" c="dimmed">
            Sube el .xlsx exportado de la query contra la base de Dataprop. Se agregan las solicitudes nuevas y se
            actualizan las que aún no se están gestionando en la app; las que ya tienen movimientos no se tocan.
          </Text>
          <FileButton resetRef={resetArchivoRef} onChange={setArchivo} accept=".xlsx,.xlsm">
            {(props) => <Button {...props} variant="light">{archivo ? archivo.name : 'Seleccionar archivo'}</Button>}
          </FileButton>
          {importar.isError && <Alert color="red">{(importar.error as Error).message}</Alert>}
          {resumenImport && (
            <Alert color={resumenImport.errores.length ? 'warning' : 'good'} variant="filled" title="Resultado">
              <Text size="sm">
                {resumenImport.nuevas} nuevas · {resumenImport.actualizadas} actualizadas · {resumenImport.ignoradas} ignoradas
                (ya gestionadas) · {resumenImport.errores.length} con error
              </Text>
              {resumenImport.errores.length > 0 && (
                <List size="xs" mt="xs">
                  {resumenImport.errores.slice(0, 20).map((e, i) => (
                    <List.Item key={i}>{e}</List.Item>
                  ))}
                </List>
              )}
            </Alert>
          )}
          <Button disabled={!archivo} loading={importar.isPending} onClick={() => importar.mutate()}>
            Subir e importar
          </Button>
        </Stack>
      </Modal>
    </Stack>
  )
}
