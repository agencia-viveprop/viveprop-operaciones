import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  Alert,
  Button,
  Divider,
  Modal,
  Group,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  Timeline,
} from '@mantine/core'
import { IconArrowRight, IconMessage, IconTrash } from '@tabler/icons-react'
import {
  crearMovimientoCanje,
  eliminarMovimientoCanje,
  listarMovimientosCanje,
  listarTiposMovimiento,
} from '../api/movimientos'

/**
 * «Ahora» en el formato que espera un `datetime-local`, para el tope del input.
 *
 * `toISOString()` no sirve: devuelve UTC, así que en Chile el tope quedaría
 * cuatro horas adelantado y dejaría elegir fechas futuras. Hay que restar el
 * desfase del huso antes de recortar.
 */
/** Cuántos días agenda el servidor cuando no se indica nada. Está acá para que
 *  el texto del campo lo diga y no haya que adivinarlo; el cálculo es del
 *  backend, que es donde tiene tests. */
const DIAS_SEGUIMIENTO = 2

/** Hoy, para el mínimo del campo de agenda: agendar un seguimiento en el pasado
 *  es un tipeo, y el que ya venció se ve en «Qué me toca hoy». */
function hoyLocal(): string {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

function ahoraLocal(): string {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

/** El orden de avance, que es el de lectura del selector. */
const ETAPAS = [
  'RECEPCION',
  'EN_REVISION',
  'PROCESO_DE_ACUERDO',
  'EN_OFERTA',
  'EN_NEGOCIO',
  'CERRADO',
] as const

const ETAPA_LABELS: Record<string, string> = {
  RECEPCION: 'Recepción',
  EN_REVISION: 'En revisión',
  PROCESO_DE_ACUERDO: 'Proceso de acuerdo',
  EN_OFERTA: 'En oferta',
  EN_NEGOCIO: 'En negocio',
  CERRADO: 'Cierre',
}

export default function SeguimientoModal({
  canjeId,
  opened,
  onClose,
  puedeEditar,
  gestionadoEnApp,
  etapaActual,
}: {
  canjeId: number | null
  opened: boolean
  onClose: () => void
  puedeEditar: boolean
  /** La etapa en la que está el canje, para precargar el selector. */
  etapaActual?: string
  /** Si el canje quedó marcado como gestionado en la app. Opcional porque no
   *  todos los lugares que abren este modal tienen el canje completo a mano. */
  gestionadoEnApp?: boolean
}) {
  const queryClient = useQueryClient()
  const [tipoSeleccionado, setTipoSeleccionado] = useState<string | null>(null)
  const [comentario, setComentario] = useState('')
  // Vacío = ahora. Se deja así en vez de precargarlo con la hora actual para que
  // el camino habitual --registrar lo que acaba de pasar-- sea exactamente el que
  // había antes: sin fecha en el cuerpo, el servidor pone la de la petición.
  const [fecha, setFecha] = useState('')
  // Qué movimiento está esperando confirmación. Borrar historial no puede pasar
  // con un clic distraído, y un segundo clic en el mismo lugar es menos
  // ceremonioso que un diálogo encima del que ya está abierto.
  const [confirmando, setConfirmando] = useState<number | null>(null)
  // Vacío = lo agenda el servidor: dos días corridos, corridos al lunes si caen
  // fin de semana. Se deja vacío por defecto para que el caso habitual --seguir
  // en un par de días-- no pida escribir nada.
  const [seguimiento, setSeguimiento] = useState('')
  // La etapa donde queda el canje. Arranca en la que tiene: lo habitual es que
  // una gestión no lo mueva, y pedir la decisión en cada llamada sería fricción
  // por un dato que casi siempre es el mismo.
  const [etapa, setEtapa] = useState<string | null>(etapaActual ?? null)

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

  // Las dos mutaciones tocan lo mismo: la línea de tiempo, el listado, y la
  // bandeja y el reporte semanal, que se miden desde el último movimiento.
  const refrescar = () => {
    queryClient.invalidateQueries({ queryKey: ['movimientos', canjeId] })
    for (const clave of ['canjes', 'bandeja', 'reporte-semanal']) {
      queryClient.invalidateQueries({ queryKey: [clave] })
    }
  }

  const crear = useMutation({
    mutationFn: () =>
      crearMovimientoCanje(canjeId!, {
        tipo_movimiento: tipoSeleccionado!,
        comentario: comentario || undefined,
        // El input da hora local; se manda en ISO con zona para que el servidor
        // no tenga que adivinar de qué huso viene.
        fecha: fecha ? new Date(fecha).toISOString() : undefined,
        // Va como fecha suelta y no en ISO con zona: es un día de agenda, no un
        // instante. Mandarlo con hora lo haría depender del huso para saber si
        // "el jueves" es jueves.
        proximo_seguimiento: seguimiento || undefined,
        etapa: etapa ?? undefined,
      }),
    onSuccess: () => {
      // La bandeja también: su semáforo se mide desde el último movimiento, y
      // registrar uno con fecha atrasada le cambia el nivel.
      refrescar()
      setTipoSeleccionado(null)
      setComentario('')
      setFecha('')
      setSeguimiento('')
    },
  })

  const borrar = useMutation({
    mutationFn: (movimientoId: number) => eliminarMovimientoCanje(canjeId!, movimientoId),
    onSuccess: () => {
      refrescar()
      setConfirmando(null)
    },
  })

  const cerrar = () => {
    setConfirmando(null)
    onClose()
  }

  // Se repuebla cuando cambia el canje: si no, abrir el seguimiento de otro
  // mostraría la etapa del anterior.
  useEffect(() => {
    setEtapa(etapaActual ?? null)
  }, [canjeId, etapaActual])

  return (
    <Modal opened={opened} onClose={cerrar} title={`Seguimiento — Canje #${canjeId}`} size="md">
      <Stack gap="md">
        {isLoading && <Text size="sm" c="dimmed">Cargando...</Text>}
        {borrar.isError && (
          <Alert color="critical" variant="light">
            {(borrar.error as Error).message}
          </Alert>
        )}
        {!isLoading && movimientos?.length === 0 && (
          <Stack gap={4}>
            <Text size="sm" c="dimmed">
              Todavía no hay movimientos registrados para este canje.
            </Text>
            {/* Sin esto la consecuencia queda muda: registrar un movimiento marca
                el canje como gestionado, y borrarlo **no** deshace esa marca --la
                pone también editarlo a mano, así que revertirla dejaría que la
                importación pisara datos corregidos por una persona--. El
                resultado es un canje que la importación ya no actualiza, y eso
                hay que poder verlo. */}
            {gestionadoEnApp && (
              <Text size="xs" c="dimmed">
                El canje quedó marcado como gestionado en la app, así que la importación de
                Dataprop no lo sobreescribe. Borrar movimientos no deshace esa marca.
              </Text>
            )}
          </Stack>
        )}
        {!isLoading && movimientos && movimientos.length > 0 && (
          <Timeline active={movimientos.length} bulletSize={22} lineWidth={2}>
            {movimientos.map((m) => (
              <Timeline.Item
                key={m.id}
                bullet={m.etapa_resultante ? <IconArrowRight size={12} /> : <IconMessage size={12} />}
                title={
                  <Group justify="space-between" wrap="nowrap" gap="xs">
                    <span>{m.tipo_nombre}</span>
                    {puedeEditar && confirmando !== m.id && (
                      <ActionIcon
                        variant="subtle"
                        color="critical"
                        size="sm"
                        aria-label={`Borrar ${m.tipo_nombre}`}
                        onClick={() => setConfirmando(m.id)}
                      >
                        <IconTrash size={14} />
                      </ActionIcon>
                    )}
                  </Group>
                }
              >
                <Text size="xs" c="dimmed">
                  {new Date(m.fecha).toLocaleString('es-CL')} · {m.autor_nombre ?? 'Sistema'}
                  {m.etapa_resultante && ` · nueva etapa: ${ETAPA_LABELS[m.etapa_resultante] ?? m.etapa_resultante}`}
                </Text>
                {/* Lo que se prometió en ese movimiento. Solo el del más reciente
                    manda, pero verlos todos deja seguir cómo se fue corriendo. */}
                {m.proximo_seguimiento && (
                  <Text size="xs" c="dimmed">
                    Próximo seguimiento:{' '}
                    <Text span fw={600}>
                      {new Date(`${m.proximo_seguimiento}T12:00:00`).toLocaleDateString('es-CL')}
                    </Text>
                  </Text>
                )}
                {m.comentario && <Text size="sm">{m.comentario}</Text>}

                {/* La confirmación va acá, en la fila del movimiento, y no en un
                    diálogo encima del modal: así queda claro cuál se borra. */}
                {confirmando === m.id && (
                  <Group gap="xs" mt={6}>
                    <Text size="xs">¿Borrar este movimiento?</Text>
                    <Button
                      size="compact-xs"
                      color="critical"
                      loading={borrar.isPending}
                      onClick={() => borrar.mutate(m.id)}
                    >
                      Sí, borrar
                    </Button>
                    <Button size="compact-xs" variant="default" onClick={() => setConfirmando(null)}>
                      Cancelar
                    </Button>
                  </Group>
                )}
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
              {/* Los dos van juntos y en este orden porque son dos preguntas
                  sobre la misma gestión: qué se hizo, y dónde quedó el canje.
                  Antes la segunda salía implícita de la primera, lo que hacía
                  imposible avanzar un canje con una llamada de seguimiento. */}
              <Select
                label="Tipo de movimiento"
                placeholder="Selecciona un tipo"
                description="Qué se hizo"
                data={tipos?.map((t) => ({ value: t.codigo, label: t.nombre })) ?? []}
                value={tipoSeleccionado}
                onChange={setTipoSeleccionado}
              />
              <Select
                label="Etapa"
                placeholder="Selecciona una etapa"
                description="Dónde queda el canje"
                data={ETAPAS.map((e) => ({ value: e, label: ETAPA_LABELS[e] }))}
                value={etapa}
                onChange={setEtapa}
              />
            </SimpleGrid>

            {/* Las dos fechas juntas: cuándo pasó y cuándo se sigue. Los dos
                selectores de arriba describen la gestión; estas dos la ubican en
                el tiempo. */}
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
              <TextInput
                label="Fecha y hora"
                type="datetime-local"
                description="Vacío = ahora"
                max={ahoraLocal()}
                value={fecha}
                onChange={(e) => setFecha(e.currentTarget.value)}
              />

              <TextInput
                label="Próximo seguimiento"
                type="date"
                description={`Vacío = en ${DIAS_SEGUIMIENTO} días`}
                min={hoyLocal()}
                value={seguimiento}
                onChange={(e) => setSeguimiento(e.currentTarget.value)}
              />
            </SimpleGrid>

            {/* La regla completa va acá y no en la descripción del campo: ahí no
                cabía sin partirse en tres líneas y empujar el resto del
                formulario. */}
            <Text size="xs" c="dimmed">
              Sin fecha de seguimiento se agenda en {DIAS_SEGUIMIENTO} días, corridos al lunes
              si caen fin de semana. Los feriados todavía no se saltan.
            </Text>
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
