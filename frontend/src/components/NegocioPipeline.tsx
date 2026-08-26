import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
  Timeline,
  Title,
} from '@mantine/core'
import { IconArrowRight, IconMessage } from '@tabler/icons-react'
import { obtenerCatalogos } from '../api/catalogos'
import { crearMovimiento, listarMovimientos, listarTiposMovimiento } from '../api/negocios'
import { fecha } from './negociosFormato'

/** Cuántos días hacia adelante se agenda el próximo paso cuando no se indica uno.
 *  Son tres y no dos como en canjes: un negocio dura de un mes a varios. */
const DIAS_PROXIMA_ACCION = 3

/** Hoy, para el mínimo del campo de agenda: agendar en el pasado es un tipeo. */
function hoyLocal(): string {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

/** Ahora, para el tope del campo de fecha. `toISOString()` sin corregir devuelve
 *  UTC, así que en Chile el tope quedaría cuatro horas adelantado. */
function ahoraLocal(): string {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

/** El pipeline es del negocio (D-027): una fila de etapas con la actual marcada. */
function Recorrido({ etapaActual }: { etapaActual: string | null }) {
  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const etapas = catalogos?.etapas ?? []
  const indiceActual = etapas.findIndex((e) => e.codigo === etapaActual)

  return (
    <Group gap={4} wrap="wrap">
      {etapas.map((e, i) => {
        const alcanzada = indiceActual >= 0 && i <= indiceActual
        const esActual = e.codigo === etapaActual
        return (
          <Badge
            key={e.codigo}
            variant={esActual ? 'filled' : alcanzada ? 'light' : 'outline'}
            color={esActual ? 'accent' : alcanzada ? 'brand' : 'gray'}
            title={`${e.nombre} · ${e.responsable}`}
          >
            {e.codigo}
          </Badge>
        )
      })}
    </Group>
  )
}

export default function NegocioPipeline({
  negocioId,
  etapaActual,
  puedeEditar,
}: {
  negocioId: number
  etapaActual: string | null
  puedeEditar: boolean
}) {
  const queryClient = useQueryClient()
  const [tipo, setTipo] = useState<string | null>(null)
  const [comentario, setComentario] = useState('')
  // Las dos fechas del avance: cuándo pasó, y cuándo se vuelve. Las dos vacías
  // por defecto, que el backend resuelve como "ahora" y "en tres días".
  const [cuando, setCuando] = useState('')
  const [proxima, setProxima] = useState('')

  const { data: tipos } = useQuery({
    queryKey: ['tipos-movimiento-negocio'],
    queryFn: listarTiposMovimiento,
  })
  const { data: movimientos } = useQuery({
    queryKey: ['movimientos-negocio', negocioId],
    queryFn: () => listarMovimientos(negocioId),
  })

  const registrar = useMutation({
    mutationFn: () =>
      crearMovimiento(negocioId, {
        tipo_movimiento: tipo!,
        comentario: comentario || null,
        // El backend distingue nulo de vacío: nulo es "resolvelo vos".
        fecha: cuando ? new Date(cuando).toISOString() : null,
        proximo_seguimiento: proxima || null,
      }),
    onSuccess: () => {
      setTipo(null)
      setComentario('')
      setCuando('')
      setProxima('')
      queryClient.invalidateQueries({ queryKey: ['movimientos-negocio', negocioId] })
      // El movimiento puede haber movido la etapa y cerrado hitos, así que la
      // ficha y el listado se recargan.
      queryClient.invalidateQueries({ queryKey: ['negocio', negocioId] })
      queryClient.invalidateQueries({ queryKey: ['negocios'] })
    },
  })

  const nombreEtapa = (codigo: string | null) => {
    if (!codigo) return null
    const t = tipos?.find((x) => x.etapa_resultante === codigo)
    return t?.nombre ?? codigo
  }

  return (
    <Card withBorder radius="md" p="md">
      <Group justify="space-between" mb="sm">
        <Title order={5}>Pipeline</Title>
        <Recorrido etapaActual={etapaActual} />
      </Group>

      {puedeEditar && (
        <Stack gap="xs" mb="md">
          <Group align="flex-end" gap="xs">
            <Select
              label="Registrar avance"
              placeholder="Elegir paso"
              data={(tipos ?? []).map((t) => ({
                value: t.codigo,
                label: t.etapa_resultante ? `${t.etapa_resultante} · ${t.nombre}` : t.nombre,
              }))}
              value={tipo}
              onChange={setTipo}
              flex={1}
            />
            <Button
              color="accent"
              leftSection={<IconArrowRight size={16} />}
              disabled={!tipo}
              loading={registrar.isPending}
              onClick={() => registrar.mutate()}
            >
              Registrar
            </Button>
          </Group>
          {/* Las dos fechas juntas: cuándo pasó y cuándo se vuelve. El selector
              de arriba describe qué se hizo; estas dos lo ubican en el tiempo. */}
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
            <TextInput
              label="Fecha de la actividad"
              type="datetime-local"
              description="Vacío = ahora"
              max={ahoraLocal()}
              value={cuando}
              onChange={(e) => setCuando(e.currentTarget.value)}
            />
            <TextInput
              label="Próxima acción"
              type="date"
              description={`Vacío = en ${DIAS_PROXIMA_ACCION} días`}
              min={hoyLocal()}
              value={proxima}
              onChange={(e) => setProxima(e.currentTarget.value)}
            />
          </SimpleGrid>

          {/* La regla completa va acá y no en la descripción del campo: ahí no
              cabe sin partirse en tres líneas. Y conviene decir la consecuencia:
              lo agendado sale de «Qué me toca hoy» hasta su fecha. */}
          <Text size="xs" c="dimmed">
            Sin fecha de próxima acción se agenda a {DIAS_PROXIMA_ACCION} días de la fecha de la
            actividad, corridos al lunes si caen fin de semana. Los feriados todavía no se saltan.
            Mientras esté agendado, el negocio no aparece en «Qué me toca hoy»: vuelve el día que
            le toca.
          </Text>

          <Textarea
            placeholder="Comentario (opcional)"
            autosize
            minRows={1}
            value={comentario}
            onChange={(e) => setComentario(e.currentTarget.value)}
          />
          {registrar.isError && (
            <Alert color="critical" variant="filled">
              {(registrar.error as Error).message}
            </Alert>
          )}
        </Stack>
      )}

      {/* La lista llega de más viejo a más nuevo, así que el paso actual es el
          último: `active` marca hasta dónde llegó el proceso. */}
      {movimientos && movimientos.length > 0 ? (
        <Timeline active={movimientos.length - 1} bulletSize={20} lineWidth={2}>
          {movimientos.map((m) => (
            <Timeline.Item
              key={m.id}
              bullet={m.etapa_resultante ? undefined : <IconMessage size={12} />}
              title={
                <Group gap="xs">
                  <Text size="sm" fw={600}>{m.tipo_nombre}</Text>
                  {m.etapa_resultante && (
                    <Badge size="xs" variant="light" color="brand">
                      → {m.etapa_resultante}
                    </Badge>
                  )}
                </Group>
              }
            >
              {m.comentario && (
                <Text size="sm" c="dimmed">
                  {m.comentario}
                </Text>
              )}
              <Text size="xs" c="dimmed" mt={2}>
                {fecha(m.fecha)}
                {m.autor_nombre && ` · ${m.autor_nombre}`}
                {m.proximo_seguimiento && ` · vuelve el ${fecha(m.proximo_seguimiento)}`}
              </Text>
            </Timeline.Item>
          ))}
        </Timeline>
      ) : (
        <Text size="sm" c="dimmed">
          Sin movimientos registrados. La etapa actual viene de la carga histórica.
        </Text>
      )}

      {nombreEtapa(etapaActual) === null && (
        <Text size="sm" c="dimmed" mt="xs">
          Este negocio no tiene etapa asignada.
        </Text>
      )}
    </Card>
  )
}
