import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  Alert,
  Autocomplete,
  Badge,
  Button,
  FileButton,
  Group,
  List,
  Modal,
  NumberInput,
  Select,
  Tabs,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Textarea,
} from '@mantine/core'
import { IconClockHour4, IconDownload, IconPencil } from '@tabler/icons-react'
import {
  actualizarCanje,
  crearCanje,
  descargarPlantillaCanjes,
  importarCanjes,
  CLAVE_OPCIONES_CANJES,
  listarCanjes,
  listarOpcionesDeFiltro,
  type Canje,
  type CanjeEstado,
  type CanjeEtapa,
  type ImportarResumen,
} from '../api/canjes'
import { obtenerEstructuraCanjes } from '../api/estructura'
import EstructuraArchivo from '../components/EstructuraArchivo'
import ReporteCanjesActivos from '../components/ReporteCanjesActivos'
import SeguimientoModal from '../components/SeguimientoModal'
import PageHeader from '../components/PageHeader'
import { ETAPA_LABELS, ETAPAS } from '../components/canjesEtiquetas'

const ESTADOS: CanjeEstado[] = ['ACTIVO', 'CERRADO', 'CANCELADO']
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
    comision_dataprop: '' as number | '',
    comision_dataprop_moneda: '',
    notas: '',
    estado: 'ACTIVO' as CanjeEstado,
    etapa: 'EN_REVISION' as CanjeEtapa,
  }
}

export default function Canjes({ puedeEditar }: { puedeEditar: boolean }) {
  const queryClient = useQueryClient()
  const [filtros, setFiltros] = useState<{
    estado: string
    etapa: string
    comuna: string
    numero: string
    solicitante: string
    propietario: string
  }>({
    estado: '',
    etapa: '',
    comuna: '',
    numero: '',
    solicitante: '',
    propietario: '',
  })
  // Las sugerencias de los filtros. Se consultan una vez y se cachean: no
  // dependen de los filtros aplicados, justamente para que elegir uno no vacie
  // las opciones de los demas.
  const { data: opciones } = useQuery({
    queryKey: CLAVE_OPCIONES_CANJES,
    queryFn: listarOpcionesDeFiltro,
  })
  const { data: canjes, isLoading } = useQuery({
    queryKey: ['canjes', filtros],
    queryFn: () => listarCanjes(filtros),
  })

  const [modalAbierto, setModalAbierto] = useState(false)
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [form, setForm] = useState(vacio())

  const [seguimientoId, setSeguimientoId] = useState<number | null>(null)
  // Qué pestaña se está mirando. El listado completo arranca puesto: es la
  // pantalla que la gente ya conoce, y el reporte es lo que se va a buscar.
  const [vista, setVista] = useState('listado')

  const [importAbierto, setImportAbierto] = useState(false)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resumenImport, setResumenImport] = useState<ImportarResumen | null>(null)
  const resetArchivoRef = useRef<() => void>(null)

  // Solo se pide con el modal abierto: es la forma de un archivo, no cambia.
  const estructura = useQuery({
    queryKey: ['estructura-archivo', 'canjes'],
    queryFn: obtenerEstructuraCanjes,
    enabled: importAbierto,
  })
  const bajarPlantilla = useMutation({ mutationFn: descargarPlantillaCanjes })

  const importar = useMutation({
    mutationFn: () => importarCanjes(archivo!),
    onSuccess: (resumen) => {
      setResumenImport(resumen)
      queryClient.invalidateQueries({ queryKey: ['canjes'] })
      // Una importación trae corredores y comunas nuevos: sin esto, el filtro
      // sigue ofreciendo la lista de antes hasta que alguien recargue.
      queryClient.invalidateQueries({ queryKey: CLAVE_OPCIONES_CANJES })
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
      if (payload.comision_dataprop === '') payload.comision_dataprop = null
      ;['tipo_operacion', 'moneda_valor', 'valor_negocio_moneda', 'comision_dataprop_moneda'].forEach((k) => {
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
      // El alta y la edición escriben corredor y comuna, así que las sugerencias
      // quedan viejas.
      queryClient.invalidateQueries({ queryKey: CLAVE_OPCIONES_CANJES })
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
      comision_dataprop: c.comision_dataprop ?? '',
      comision_dataprop_moneda: c.comision_dataprop_moneda ?? '',
      notas: c.notas ?? '',
      estado: c.estado,
      etapa: c.etapa,
    })
    setModalAbierto(true)
  }

  // Se busca una vez y no tres veces en el JSX.
  const canjeSeguido = canjes?.find((c) => c.id === seguimientoId)

  return (
    <Stack gap="md">
      <PageHeader
        title="Canjes"
        action={
          puedeEditar && (
            <Group>
              <Button variant="light" onClick={() => setImportAbierto(true)}>
                Importar Canjes
              </Button>
              <Button color="accent" onClick={abrirNuevo}>Nuevo canje</Button>
            </Group>
          )
        }
      />

      <Tabs value={vista} onChange={(v) => setVista(v ?? "listado")}>
        <Tabs.List mb="md">
          <Tabs.Tab value="listado">Todos los canjes</Tabs.Tab>
          <Tabs.Tab value="activos">Activos y su gestión</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="listado">
          <Stack gap="md">
          <Group>
            <Select
              placeholder="Estado"
              data={ESTADOS}
              value={filtros.estado || null}
              onChange={(v) => setFiltros({ ...filtros, estado: v ?? '' })}
              clearable
              w={{ base: '100%', sm: 160 }}
            />
            <Select
              placeholder="Etapa"
              data={ETAPAS.map((e) => ({ value: e, label: ETAPA_LABELS[e] }))}
              value={filtros.etapa || null}
              onChange={(v) => setFiltros({ ...filtros, etapa: v ?? '' })}
              clearable
              w={{ base: '100%', sm: 200 }}
            />
            {/* Comuna tambien sugiere, igual que los dos de corredor. Ya filtraba
                con lo que se escribiera --el backend hace coincidencia parcial--
                pero sin la lista habia que recordar como esta escrita cada una, y
                en los datos hay 43. Sigue aceptando texto libre: escribir «flor»
                filtra sin necesidad de elegir «La Florida» de la lista. */}
            <Autocomplete
              placeholder="Comuna"
              data={opciones?.comunas ?? []}
              value={filtros.comuna}
              onChange={(v) => setFiltros({ ...filtros, comuna: v })}
              limit={10}
              clearable
              w={{ base: '100%', sm: 200 }}
            />
            {/* El N° de solicitud es el ID_CANJE de Dataprop, el mismo que se ve
                en la primera columna. Busca **por prefijo**: mientras se escribe
                «364», el «3» y el «36» ya muestran algo, en vez de parpadear en
                vacío y leerse como que el canje no existe.
                Es `TextInput` y no `NumberInput` a propósito: no es una cantidad
                --no se suma ni se incrementa-- y los separadores de miles que
                pondría un campo numérico romperían la búsqueda por prefijo. Se
                filtran los dígitos acá para que pegar «#364» funcione, que es
                como la app escribe las referencias en los reportes. */}
            <TextInput
              placeholder="N° de solicitud"
              inputMode="numeric"
              value={filtros.numero}
              onChange={(e) =>
                setFiltros({
                  ...filtros,
                  numero: e.currentTarget.value.replace(/[^0-9]/g, ''),
                })
              }
              w={{ base: '100%', sm: 160 }}
            />
            {/* Autocomplete y no Select: es un filtro, no un formulario. El
                Select obligaria a elegir una opcion exacta, y acá escribir
                «vicente» y ver los canjes de Vicente Farías tiene que funcionar
                aunque no se termine de elegir de la lista. Las sugerencias son
                una ayuda, no un corsé.
                La lista viene del universo completo --no del listado filtrado--
                para que elegir un corredor no haga desaparecer a los demas. */}
            <Autocomplete
              placeholder="Corredor solicitante"
              data={opciones?.solicitantes ?? []}
              value={filtros.solicitante}
              onChange={(v) => setFiltros({ ...filtros, solicitante: v })}
              limit={10}
              clearable
              w={{ base: '100%', sm: 260 }}
            />
            <Autocomplete
              placeholder="Corredor propietario"
              data={opciones?.propietarios ?? []}
              value={filtros.propietario}
              onChange={(v) => setFiltros({ ...filtros, propietario: v })}
              limit={10}
              clearable
              w={{ base: '100%', sm: 260 }}
            />
          </Group>

          {/* Los dos corredores van en una sola columna, uno sobre otro, que es lo
              que hace que la tabla quepa sin desplazamiento horizontal. Los nombres
              van completos: acortarlos era resolver el problema equivocado.
              Cada fila ocupa dos lineas, y ese es el precio elegido. */}
          <div className="tabla-scroll-x">
          <Table striped withTableBorder highlightOnHover fz="xs" className="tabla-una-linea">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>N°</Table.Th>
                <Table.Th>Fecha</Table.Th>
                <Table.Th>Corredores</Table.Th>
                <Table.Th>Comuna</Table.Th>
                <Table.Th>Operación</Table.Th>
                <Table.Th>Estado</Table.Th>
                <Table.Th>Etapa</Table.Th>
                <Table.Th>Acciones</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {!isLoading &&
                canjes?.map((c) => (
                  <Table.Tr key={c.id}>
                    <Table.Td fw={600} ff="monospace">{c.id}</Table.Td>
                    <Table.Td>{c.fecha_solicitud?.slice(0, 10)}</Table.Td>
                    <Table.Td>
                      {/* La etiqueta va en cada linea: la posicion sola no alcanza
                          para saber cual es cual al escanear la tabla. */}
                      <Group gap={6} wrap="nowrap">
                        <Text size="xs" c="dimmed" w={30} ta="right">
                          Sol.
                        </Text>
                        <Text size="xs">{c.corredor_solicitante_nombre ?? '—'}</Text>
                      </Group>
                      <Group gap={6} wrap="nowrap">
                        <Text size="xs" c="dimmed" w={30} ta="right">
                          Prop.
                        </Text>
                        <Text size="xs">{c.corredor_propietario_nombre ?? '—'}</Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>{c.comuna}</Table.Td>
                    <Table.Td>{c.tipo_operacion}</Table.Td>
                    <Table.Td>
                      <Badge color={c.estado === 'ACTIVO' ? 'good' : 'critical'} variant="light">
                        {c.estado}
                      </Badge>
                    </Table.Td>
                    <Table.Td>{ETAPA_LABELS[c.etapa]}</Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon variant="subtle" onClick={() => setSeguimientoId(c.id)} aria-label="Seguimiento">
                          <IconClockHour4 size={18} />
                        </ActionIcon>
                        {puedeEditar && (
                          <ActionIcon variant="subtle" onClick={() => abrirEditar(c)} aria-label="Editar">
                            <IconPencil size={18} />
                          </ActionIcon>
                        )}
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
            </Table.Tbody>
          </Table>
          </div>
          </Stack>
        </Tabs.Panel>

        {/* Un reporte, no una lista de trabajo: muestra todos los abiertos
            --incluso los agendados a futuro que la bandeja esconde-- y cada
            fila despliega su historial en orden cronológico. */}
        <Tabs.Panel value="activos">
          <ReporteCanjesActivos />
        </Tabs.Panel>
      </Tabs>
      {!isLoading && canjes?.length === 0 && <Text c="dimmed">No hay canjes que calcen con el filtro.</Text>}

      <Modal opened={modalAbierto} onClose={() => setModalAbierto(false)} title={editandoId ? `Canje #${editandoId}` : 'Nuevo canje'} size="lg">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            guardar.mutate()
          }}
        >
          <Stack gap="sm">
            <SimpleGrid cols={{ base: 1, xs: 2 }}>
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
                  label="Comisión Dataprop cobrada"
                  description="Solo al cerrar: lo que efectivamente se cobró"
                  value={form.comision_dataprop}
                  onChange={(v) => setForm({ ...form, comision_dataprop: v as number | '' })}
                  flex={1}
                />
                <Select
                  data={MONEDAS}
                  value={form.comision_dataprop_moneda || null}
                  onChange={(v) => setForm({ ...form, comision_dataprop_moneda: v ?? '' })}
                  w={80}
                />
              </Group>
            </SimpleGrid>
            <Textarea label="Notas" value={form.notas} onChange={(e) => setForm({ ...form, notas: e.currentTarget.value })} />
            {guardar.isError && <Alert color="critical" variant="filled">{(guardar.error as Error).message}</Alert>}
            <Button type="submit" color="accent" loading={guardar.isPending}>
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
            Las solicitudes <strong>anteriores a junio de 2025</strong> no se cargan: ese historial se borró
            de la app a propósito y el export de Dataprop lo sigue trayendo.
          </Text>

          <EstructuraArchivo consulta={estructura} />

          <Group>
            <Button
              variant="light"
              leftSection={<IconDownload size={16} />}
              loading={bajarPlantilla.isPending}
              onClick={() => bajarPlantilla.mutate()}
            >
              Descargar plantilla
            </Button>
            <FileButton resetRef={resetArchivoRef} onChange={setArchivo} accept=".xlsx,.xlsm">
              {(props) => <Button {...props} variant="default">{archivo ? archivo.name : 'Seleccionar archivo'}</Button>}
            </FileButton>
          </Group>

          {bajarPlantilla.isError && (
            <Alert color="critical" variant="light">{(bajarPlantilla.error as Error).message}</Alert>
          )}
          {importar.isError && <Alert color="critical" variant="filled">{(importar.error as Error).message}</Alert>}
          {resumenImport && (
            <Alert color={resumenImport.errores.length ? 'warning' : 'good'} variant="filled" title="Resultado">
              <Text size="sm">
                {resumenImport.nuevas} nuevas · {resumenImport.actualizadas} actualizadas · {resumenImport.ignoradas} ignoradas
                (ya gestionadas) · {resumenImport.errores.length} con error
                {/* Se dice solo cuando pasó: en un archivo sin filas viejas, un
                    «0 antiguas» es ruido. Y cuando pasa hay que decirlo, porque
                    si no un archivo de 300 filas que carga 20 se lee como un
                    error de la importación. */}
                {resumenImport.antiguas > 0 && (
                  <> · {resumenImport.antiguas} anteriores a junio 2025 (no se cargan)</>
                )}
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
          <Button color="accent" disabled={!archivo} loading={importar.isPending} onClick={() => importar.mutate()}>
            Subir e importar
          </Button>
        </Stack>
      </Modal>

      <SeguimientoModal
        canjeId={seguimientoId}
        opened={seguimientoId !== null}
        onClose={() => setSeguimientoId(null)}
        puedeEditar={puedeEditar}
        gestionadoEnApp={canjeSeguido?.gestionado_en_app}
        etapaActual={canjeSeguido?.etapa}
        solicitante={canjeSeguido?.corredor_solicitante_nombre}
        propietario={canjeSeguido?.corredor_propietario_nombre}
      />
    </Stack>
  )
}
