import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Divider,
  Group,
  Modal,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Textarea,
} from '@mantine/core'
import { IconInfoCircle } from '@tabler/icons-react'
import { obtenerCatalogos } from '../api/catalogos'
import { buscarPropiedades, CLAVE_OPCIONES_NEGOCIOS, crearNegocio } from '../api/negocios'
import CamposHito from './CamposHito'
import { hitoVacio, payloadHito, validarHito } from './hitoForm'

/** Los porcentajes se ingresan como número (2 = 2%) y se envían como fracción. */
function vacio() {
  return {
    codigo: '',
    modelo: '',
    alianza_id: '',
    tipo_operacion_id: '',
    direccion: '',
    unidad: '',
    comuna: '',
    tipo_propiedad_id: '',
    estado_propiedad_id: '',
    vendedor_arrendador: '',
    comprador_arrendatario: '',
    corredor_agente: '',
    observaciones: '',
    etapa: '',
    // La liquidación única, con los mismos campos que el formulario de edición.
    ...hitoVacio(),
  }
}

export default function NegocioFormModal({
  abierto,
  onClose,
}: {
  abierto: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState(vacio())
  const [parecidas, setParecidas] = useState<string[]>([])

  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })

  const set = (campo: string, valor: unknown) => setForm((f) => ({ ...f, [campo]: valor }))

  // Ofrece propiedades parecidas mientras se escribe la dirección: la clave
  // única no agrupa "Av. Fernández Albano 492" con "Fernández Albano 492".
  useEffect(() => {
    const texto = form.direccion.trim()
    if (texto.length < 3) {
      setParecidas([])
      return
    }
    const id = setTimeout(() => {
      buscarPropiedades(texto)
        .then((props) =>
          setParecidas(
            props
              .filter((p) => p.direccion.toLowerCase() !== texto.toLowerCase())
              .map((p) => [p.direccion, p.unidad, p.comuna].filter(Boolean).join(' · ')),
          ),
        )
        .catch(() => setParecidas([]))
    }, 350)
    return () => clearTimeout(id)
  }, [form.direccion])

  const guardar = useMutation({
    mutationFn: () => {
      return crearNegocio({
        codigo: form.codigo.trim(),
        modelo: form.modelo,
        alianza_id: form.alianza_id ? Number(form.alianza_id) : null,
        tipo_operacion_id: form.tipo_operacion_id ? Number(form.tipo_operacion_id) : null,
        propiedad: {
          direccion: form.direccion.trim(),
          unidad: form.unidad.trim() || null,
          comuna: form.comuna.trim(),
          tipo_propiedad_id: form.tipo_propiedad_id ? Number(form.tipo_propiedad_id) : null,
          estado_propiedad_id: form.estado_propiedad_id ? Number(form.estado_propiedad_id) : null,
        },
        vendedor_arrendador: form.vendedor_arrendador || null,
        comprador_arrendatario: form.comprador_arrendatario || null,
        corredor_agente: form.corredor_agente || null,
        observaciones: form.observaciones || null,
        etapa: form.etapa || null,
        hitos: [payloadHito(form)],
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['negocios'] })
      // El negocio nuevo puede traer un corredor que no estaba: el filtro del
      // listado tiene que ofrecerlo desde ya y no después de recargar.
      queryClient.invalidateQueries({ queryKey: CLAVE_OPCIONES_NEGOCIOS })
      cerrar()
    },
  })

  function cerrar() {
    setForm(vacio())
    setParecidas([])
    guardar.reset()
    onClose()
  }

  const opciones = (items: { id: number | null; nombre: string }[] = []) =>
    items.map((i) => ({ value: String(i.id), label: i.nombre }))

  const problemaHito = validarHito(form)
  const completo =
    form.codigo && form.modelo && form.direccion && form.comuna && !problemaHito

  return (
    <Modal opened={abierto} onClose={cerrar} title="Nuevo negocio" size="lg">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          guardar.mutate()
        }}
      >
        <Stack gap="sm">
          <SimpleGrid cols={2}>
            <TextInput
              label="Código"
              placeholder="VVP-20"
              required
              value={form.codigo}
              onChange={(e) => set('codigo', e.currentTarget.value)}
            />
            <Select
              label="Modelo de negocio"
              required
              data={(catalogos?.modelos_negocio ?? []).map((m) => ({ value: m.codigo, label: m.nombre }))}
              value={form.modelo || null}
              onChange={(v) => set('modelo', v ?? '')}
            />
            <Select
              label="Alianza"
              data={opciones(catalogos?.alianzas)}
              value={form.alianza_id || null}
              onChange={(v) => set('alianza_id', v ?? '')}
              clearable
              searchable
            />
            <Select
              label="Operación"
              data={opciones(catalogos?.tipos_operacion)}
              value={form.tipo_operacion_id || null}
              onChange={(v) => set('tipo_operacion_id', v ?? '')}
              clearable
            />
          </SimpleGrid>

          <Divider label="Propiedad" labelPosition="left" />
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <TextInput
              label="Dirección"
              required
              value={form.direccion}
              onChange={(e) => set('direccion', e.currentTarget.value)}
            />
            <TextInput
              label="Unidad"
              placeholder="316-A"
              value={form.unidad}
              onChange={(e) => set('unidad', e.currentTarget.value)}
            />
            <TextInput
              label="Comuna"
              required
              value={form.comuna}
              onChange={(e) => set('comuna', e.currentTarget.value)}
            />
          </SimpleGrid>

          {parecidas.length > 0 && (
            <Alert variant="light" color="info" icon={<IconInfoCircle size={18} />} title="Ya existen propiedades parecidas">
              <Stack gap={2}>
                {parecidas.slice(0, 4).map((p) => (
                  <Text key={p} size="sm">{p}</Text>
                ))}
                <Text size="xs" c="dimmed">
                  Si es la misma unidad, escribe la dirección igual y se reusa en vez de duplicarse.
                </Text>
              </Stack>
            </Alert>
          )}

          <SimpleGrid cols={2}>
            <Select
              label="Tipo de propiedad"
              data={opciones(catalogos?.tipos_propiedad)}
              value={form.tipo_propiedad_id || null}
              onChange={(v) => set('tipo_propiedad_id', v ?? '')}
              clearable
            />
            <Select
              label="Estado de la propiedad"
              data={opciones(catalogos?.estados_propiedad)}
              value={form.estado_propiedad_id || null}
              onChange={(v) => set('estado_propiedad_id', v ?? '')}
              clearable
            />
          </SimpleGrid>

          <Divider label="Contrapartes" labelPosition="left" />
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <TextInput
              label="Vendedor / Arrendador"
              value={form.vendedor_arrendador}
              onChange={(e) => set('vendedor_arrendador', e.currentTarget.value)}
            />
            <TextInput
              label="Comprador / Arrendatario"
              value={form.comprador_arrendatario}
              onChange={(e) => set('comprador_arrendatario', e.currentTarget.value)}
            />
            <TextInput
              label="Corredor"
              value={form.corredor_agente}
              onChange={(e) => set('corredor_agente', e.currentTarget.value)}
            />
          </SimpleGrid>

          {/* La etapa es del negocio, no de la liquidación: la mueve el pipeline
              y acá se deja elegir la inicial. */}
          <Select
            label="Etapa inicial"
            description="El pipeline la mueve después, registrando movimientos"
            data={(catalogos?.etapas ?? []).map((e) => ({ value: e.codigo, label: `${e.codigo} · ${e.nombre}` }))}
            value={form.etapa || null}
            onChange={(v) => set('etapa', v ?? '')}
            clearable
          />

          {/* Los campos de la liquidación salen del componente compartido con el
              formulario de edición. Estaban duplicados acá, y dos copias de las
              reglas del motor de comisiones garantizaban divergir. */}
          <CamposHito
            form={form}
            set={set as never}
            modelo={form.modelo}
            estados={catalogos?.estados_negocio ?? []}
          />


          <Textarea
            label="Observaciones"
            autosize
            minRows={2}
            value={form.observaciones}
            onChange={(e) => set('observaciones', e.currentTarget.value)}
          />

          {guardar.isError && (
            <Alert color="critical" variant="filled">
              {(guardar.error as Error).message}
            </Alert>
          )}

          <Text size="xs" c="dimmed">
            Las comisiones se calculan al guardar, con la UF de la fecha de valorización.
          </Text>

          <Group justify="flex-end">
            <Button variant="default" onClick={cerrar}>
              Cancelar
            </Button>
            <Button type="submit" color="accent" loading={guardar.isPending} disabled={!completo}>
              Guardar
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}
