import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Divider, Modal, Select, Stack, Text, Textarea, Timeline } from '@mantine/core'
import { IconArrowRight, IconMessage } from '@tabler/icons-react'
import { crearMovimientoCanje, listarMovimientosCanje, listarTiposMovimiento } from '../api/movimientos'

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
    mutationFn: () => crearMovimientoCanje(canjeId!, { tipo_movimiento: tipoSeleccionado!, comentario: comentario || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['movimientos', canjeId] })
      queryClient.invalidateQueries({ queryKey: ['canjes'] })
      setTipoSeleccionado(null)
      setComentario('')
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
            <Select
              label="Tipo de movimiento"
              placeholder="Selecciona un tipo"
              data={tipos?.map((t) => ({ value: t.codigo, label: t.nombre })) ?? []}
              value={tipoSeleccionado}
              onChange={setTipoSeleccionado}
            />
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
