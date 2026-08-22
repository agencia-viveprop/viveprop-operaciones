import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Group,
  Modal,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core'
import { obtenerCatalogos } from '../api/catalogos'
import { actualizarNegocio, type Negocio } from '../api/negocios'

/**
 * Editar los datos del negocio: modelo, alianza, contrapartes, notas.
 *
 * **No incluye la propiedad ni las liquidaciones**, y eso es deliberado. La
 * propiedad es una entidad aparte que otros negocios pueden compartir, así que
 * cambiarla acá cambiaría la dirección de negocios ajenos; corregirla es otra
 * operación. Y las liquidaciones se editan una por una desde su propia tarjeta,
 * porque cada una recalcula comisiones.
 *
 * **Cambiar el modelo recalcula la plata.** El modelo decide qué lado se cobra,
 * así que el backend vuelve a pasar todas las liquidaciones por el motor. Se
 * avisa antes de guardar en vez de dejar que la cifra cambie sin explicación.
 */
export default function NegocioEditarModal({
  negocio,
  abierto,
  onClose,
}: {
  negocio: Negocio
  abierto: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })

  const desde = () => ({
    modelo: negocio.modelo as string,
    etapa: negocio.etapa ?? '',
    alianza_id: negocio.alianza_id === null ? '' : String(negocio.alianza_id),
    tipo_operacion_id:
      negocio.tipo_operacion_id === null ? '' : String(negocio.tipo_operacion_id),
    vendedor_arrendador: negocio.vendedor_arrendador ?? '',
    comprador_arrendatario: negocio.comprador_arrendatario ?? '',
    corredor_agente: negocio.corredor_agente ?? '',
    notas: negocio.notas ?? '',
    observaciones: negocio.observaciones ?? '',
  })

  const [form, setForm] = useState(desde)

  useEffect(() => {
    if (abierto) setForm(desde())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abierto, negocio])

  const set = (campo: keyof ReturnType<typeof desde>, valor: string) =>
    setForm((f) => ({ ...f, [campo]: valor }))

  const guardar = useMutation({
    mutationFn: () =>
      actualizarNegocio(negocio.id, {
        modelo: form.modelo,
        etapa: form.etapa || null,
        alianza_id: form.alianza_id ? Number(form.alianza_id) : null,
        tipo_operacion_id: form.tipo_operacion_id ? Number(form.tipo_operacion_id) : null,
        vendedor_arrendador: form.vendedor_arrendador || null,
        comprador_arrendatario: form.comprador_arrendatario || null,
        corredor_agente: form.corredor_agente || null,
        notas: form.notas || null,
        observaciones: form.observaciones || null,
      }),
    onSuccess: () => {
      ;['negocio', 'negocios', 'resumen-negocios', 'negocios-por-mes',
        'bandeja-negocios', 'reporte-mensual', 'reporte-semanal', 'vista-directorio',
      ].forEach((k) => queryClient.invalidateQueries({ queryKey: [k] }))
      onClose()
    },
  })

  const cambiaModelo = form.modelo !== negocio.modelo
  const opciones = (items: { id: number | null; nombre: string }[] = []) =>
    items.map((i) => ({ value: String(i.id), label: i.nombre }))

  return (
    <Modal opened={abierto} onClose={onClose} title={`Editar ${negocio.codigo}`} size="lg">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          guardar.mutate()
        }}
      >
        <Stack gap="sm">
          <SimpleGrid cols={{ base: 1, sm: 2 }}>
            <Select
              label="Modelo de negocio"
              data={(catalogos?.modelos_negocio ?? []).map((m) => ({
                value: m.codigo,
                label: m.nombre,
              }))}
              value={form.modelo}
              onChange={(v) => set('modelo', v ?? form.modelo)}
            />
            <Select
              label="Etapa"
              data={(catalogos?.etapas ?? []).map((e) => ({
                value: e.codigo,
                label: `${e.codigo} · ${e.nombre}`,
              }))}
              value={form.etapa || null}
              onChange={(v) => set('etapa', v ?? '')}
              clearable
            />
            <Select
              label="Alianza"
              data={opciones(catalogos?.alianzas)}
              value={form.alianza_id || null}
              onChange={(v) => set('alianza_id', v ?? '')}
              clearable
            />
            <Select
              label="Operación"
              data={opciones(catalogos?.tipos_operacion)}
              value={form.tipo_operacion_id || null}
              onChange={(v) => set('tipo_operacion_id', v ?? '')}
              clearable
            />
          </SimpleGrid>

          {cambiaModelo && (
            <Alert color="warning" variant="light" title="Cambiar el modelo recalcula la comisión">
              <Text size="sm">
                El modelo decide qué lado se cobra, así que al guardar se recalculan todas las
                liquidaciones de este negocio. Si las tasas cargadas no corresponden al modelo
                nuevo, los montos van a cambiar.
              </Text>
            </Alert>
          )}

          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <TextInput
              label="Vendedor / arrendador"
              value={form.vendedor_arrendador}
              onChange={(e) => set('vendedor_arrendador', e.currentTarget.value)}
            />
            <TextInput
              label="Comprador / arrendatario"
              value={form.comprador_arrendatario}
              onChange={(e) => set('comprador_arrendatario', e.currentTarget.value)}
            />
            <TextInput
              label="Corredor o agente"
              value={form.corredor_agente}
              onChange={(e) => set('corredor_agente', e.currentTarget.value)}
            />
          </SimpleGrid>

          <Textarea
            label="Notas"
            autosize
            minRows={2}
            value={form.notas}
            onChange={(e) => set('notas', e.currentTarget.value)}
          />
          <Textarea
            label="Observaciones"
            autosize
            minRows={2}
            value={form.observaciones}
            onChange={(e) => set('observaciones', e.currentTarget.value)}
          />

          <Text size="xs" c="dimmed">
            La dirección de la propiedad no se edita acá: otros negocios pueden compartirla, y
            cambiarla les cambiaría la dirección a ellos también.
          </Text>

          {guardar.isError && (
            <Alert color="critical" variant="light">
              {(guardar.error as Error).message}
            </Alert>
          )}

          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" color="accent" loading={guardar.isPending}>
              Guardar
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}
