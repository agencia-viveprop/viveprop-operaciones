import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Divider,
  Modal,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  Timeline,
} from '@mantine/core'
import { IconArrowRight, IconMessage } from '@tabler/icons-react'
import { crearMovimientoCanje, listarMovimientosCanje, listarTiposMovimiento } from '../api/movimientos'

/**
 * «Ahora» en el formato que espera un `datetime-local`, para el tope del input.
 *
 * `toISOString()` no sirve: devuelve UTC, así que en Chile el tope quedaría
 * cuatro horas adelantado y dejaría elegir fechas futuras. Hay que restar el
 * desfase del huso antes de recortar.
 */
function ahoraLocal(): string {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

const ETAPA_LABELS: Record<string, string> = {
  SIN_ETAPA: 'Sin etapa',
  EN_REVISION: 'En revisión',
  PROCESO_DE_ACUERDO: 'Proceso de acuerdo',
  EN_OFERTA: 'En oferta',
  EN_NEGOCIO: 'En negocio',
  CERRADO: 'Cerrado',
}

export default function SeguimientoModal({
  canjeId,
  opened,
  onClose,
  puedeEditar,
}: {
  canjeId: number | null
  opened: boolean
  onClose: () => void
  puedeEditar: boolean
}) {
  const queryClient = useQueryClient()
  const [tipoSeleccionado, setTipoSeleccionado] = useState<string | null>(null)
  const [comentario, setComentario] = useState('')
  // Vacío = ahora. Se deja así en vez de precargarlo con la hora actual para que
  // el camino habitual --registrar lo que acaba de pasar-- sea exactamente el que
  // había antes: sin fecha en el cuerpo, el servidor pone la de la petición.
  const [fecha, setFecha] = useState('')

  const { data: movimientos, isLoading } = useQuery({
    queryKey: ['movimientos', canjeId],
    queryFn: () => listarMovimientosCanje(canjeId!),
    enabled: opened && canjeId !== null,
  })

  const { data: tipos } = useQuery({
    queryKey: ['tipos-movimiento', 'canje'],
    queryFn: () => listarTiposMovimiento('canje'),
    enabled: opened,
  })

  const crear = useMutation({
    mutationFn: () =>
      crearMovimientoCanje(canjeId!, {
        tipo_movimiento: tipoSeleccionado!,
        comentario: comentario || undefined,
        // El input da hora local; se manda en ISO con zona para que el servidor
        // no tenga que adivinar de qué huso viene.
        fecha: fecha ? new Date(fecha).toISOString() : undefined,
      }),
    onSuccess: () => {
      // La bandeja también: su semáforo se mide desde el último movimiento, y
      // registrar uno con fecha atrasada le cambia el nivel.
      ;['movimientos', 'canjes', 'bandeja', 'reporte-semanal'].forEach((k) =>
        queryClient.invalidateQueries({ queryKey: k === 'movimientos' ? [k, canjeId] : [k] }),
      )
      setTipoSeleccionado(null)
      setComentario('')
      setFecha('')
    },
  })

  return (
    <Modal opened={opened} onClose={onClose} title={`Seguimiento — Canje #${canjeId}`} size="md">
      <Stack gap="md">
        {isLoading && <Text size="sm" c="dimmed">Cargando...</Text>}
        {!isLoading && movimientos?.length === 0 && (
          <Text size="sm" c="dimmed">
            Todavía no hay movimientos registrados para este canje.
          </Text>
        )}
        {!isLoading && movimientos && movimientos.length > 0 && (
          <Timeline active={movimientos.length} bulletSize={22} lineWidth={2}>
            {movimientos.map((m) => (
              <Timeline.Item
                key={m.id}
                bullet={m.etapa_resultante ? <IconArrowRight size={12} /> : <IconMessage size={12} />}
                title={m.tipo_nombre}
              >
                <Text size="xs" c="dimmed">
                  {new Date(m.fecha).toLocaleString('es-CL')} · {m.autor_nombre ?? 'Sistema'}
                  {m.etapa_resultante && ` · nueva etapa: ${ETAPA_LABELS[m.etapa_resultante] ?? m.etapa_resultante}`}
                </Text>
                {m.comentario && <Text size="sm">{m.comentario}</Text>}
              </Timeline.Item>
            ))}
          </Timeline>
        )}

        {puedeEditar && (
          <>
            <Divider label="Agregar movimiento" />
            {/* La fecha va al lado del tipo porque son la misma decisión: qué
                pasó y cuándo. Separarlas dejaba la fecha como un detalle
                opcional al final, y es justamente lo que hay que corregir
                cuando se anota gestión de días pasados. */}
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
              <Select
                label="Tipo de movimiento"
                placeholder="Selecciona un tipo"
                data={tipos?.map((t) => ({ value: t.codigo, label: t.nombre })) ?? []}
                value={tipoSeleccionado}
                onChange={setTipoSeleccionado}
              />
              <TextInput
                label="Fecha y hora"
                type="datetime-local"
                description="Vacío = ahora"
                max={ahoraLocal()}
                value={fecha}
                onChange={(e) => setFecha(e.currentTarget.value)}
              />
            </SimpleGrid>
            <Textarea
              label="Comentario"
              placeholder="Opcional"
              value={comentario}
              onChange={(e) => setComentario(e.currentTarget.value)}
            />
            {crear.isError && <Alert color="critical" variant="filled">{(crear.error as Error).message}</Alert>}
            <Button color="accent" disabled={!tipoSeleccionado} loading={crear.isPending} onClick={() => crear.mutate()}>
              Registrar movimiento
            </Button>
          </>
        )}
      </Stack>
    </Modal>
  )
}
