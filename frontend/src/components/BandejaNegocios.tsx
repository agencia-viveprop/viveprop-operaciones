import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from '@mantine/core'
import {
  obtenerBandejaNegocios,
  type FilaBandejaNegocio,
  type NivelNegocio,
} from '../api/negocios'
import NegocioFichaModal from './NegocioFichaModal'
import EtapaBadge from './EtapaBadge'
import { clp, duracion, fecha, MODELO_CORTO } from './negociosFormato'
import EstadoConsulta from './EstadoConsulta'

/**
 * Los niveles con su palabra, nunca el color solo.
 *
 * Los umbrales son en **días**, no en horas: los 48/24 horas de canjes miden un
 * ciclo de días, y acá los procesos duran de un mes a varios. En horas no
 * distinguirían nada.
 */
const NIVELES: Record<NivelNegocio, { texto: string; color: string }> = {
  vencido: { texto: 'Vencido', color: 'critical' },
  para_hoy: { texto: 'Para hoy', color: 'warning' },
  sin_gestion: { texto: 'Sin gestión', color: 'gray' },
  critico: { texto: 'Crítico', color: 'critical' },
  advertencia: { texto: 'Advertencia', color: 'warning' },
  al_dia: { texto: 'Al día', color: 'good' },
}

/**
 * La explicación de cada nivel, armada con los umbrales que manda la API.
 *
 * Los números venían escritos a mano en el texto --"Más de 30 días", "Entre 14 y
 * 30"-- mientras el backend los decide en `UMBRAL_CRITICO` y
 * `UMBRAL_ADVERTENCIA` y **ya los devolvía en la respuesta**. Dos copias del
 * mismo umbral: el día que se ajuste uno, la pantalla seguiría explicando el
 * viejo y nada fallaría. Un cartel que miente sobre la regla que aplica es peor
 * que no tener cartel.
 *
 * Cada nivel nombra sus **dos orígenes** (`D-094`): un compromiso incumplido
 * escala por el semáforo, así que a «Crítico» y «Advertencia» llegan negocios por
 * los días sin gestión **y** por los días de atraso. Nombrar solo uno es lo que
 * hacía que el recuadro dijera 0 mientras la tabla mostraba semanas de espera
 * (`D-093`).
 */
function ayudaDe(nivel: NivelNegocio, critico: number, advertencia: number): string {
  switch (nivel) {
    case 'vencido':
      // El día de gracia hace que el escalamiento empiece al día siguiente, así
      // que este nivel cubre desde 1 hasta el umbral de advertencia.
      return `La próxima acción venció hace ${advertencia} días o menos`
    case 'para_hoy':
      return 'La próxima acción es hoy'
    case 'sin_gestion':
      return 'Nunca se registró un movimiento'
    case 'critico':
      return `Vencida hace más de ${critico} días, o más de ${critico} días sin gestión`
    case 'advertencia':
      return `Vencida hace ${advertencia + 1} a ${critico} días, o ${advertencia} a ${critico} días sin gestión`
    case 'al_dia':
      return `Menos de ${advertencia} días`
  }
}

const ORDEN: NivelNegocio[] = [
  'vencido',
  'para_hoy',
  'sin_gestion',
  'critico',
  'advertencia',
  'al_dia',
]

/**
 * Qué negocio hay que tocar hoy.
 *
 * **Antigüedad y días sin gestión son dos cosas distintas y van las dos.** Un
 * negocio puede llevar seis meses abierto y estar avanzando perfecto; otro puede
 * llevar dos meses y estar muerto. Una sola de las dos columnas no distingue
 * esos casos.
 */
export default function BandejaNegocios({ puedeEditar }: { puedeEditar: boolean }) {
  const [fichaId, setFichaId] = useState<number | null>(null)
  const consulta = useQuery({
    queryKey: ['bandeja-negocios'],
    queryFn: obtenerBandejaNegocios,
  })
  const { data } = consulta

  if (!data) return <EstadoConsulta de={consulta} alto={240} />

  // Todo lo que no está al día. Se deriva de `ORDEN` en vez de sumar niveles a
  // mano: la versión a mano de esto ya se rompió una vez en canjes al agregar dos
  // niveles --el chip decía «2» sobre una lista de seis filas-- y el error no lo
  // detecta ningún tipo.
  const requieren = ORDEN.filter((n) => n !== 'al_dia').reduce(
    (a, n) => a + data.resumen[n],
    0,
  )
  // Los listados más los agendados: los agendados están abiertos, solo que su día
  // no es hoy.
  const abiertos = data.filas.length + data.resumen.agendados

  // «Al día» son los dos: con la próxima acción comprometida, o gestionados dentro
  // del plazo. Ninguno requiere atención hoy. Ver `Bandeja.tsx`.
  const alDia = data.resumen.al_dia + data.resumen.agendados

  // Solo nombra las poblaciones que existen: un pie que enumera lo que no hay se
  // lee como un reproche.
  const desgloseAlDia = [
    data.resumen.agendados > 0 && `${data.resumen.agendados} con su próxima acción agendada`,
    data.resumen.al_dia > 0 && `${data.resumen.al_dia} gestionados dentro del plazo`,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        {requieren} de {abiertos} negocios con liquidaciones abiertas requieren atención. Los
        umbrales son en días, no en horas: acá los procesos duran de un mes a varios. La próxima
        acción comprometida manda mientras está vigente; una vez vencida, el atraso escala igual
        que los días sin gestión.
      </Text>

      {/* **«Al día» incluye los agendados, y los seis recuadros reparten el
          universo.** Ver la explicación larga en `Bandeja.tsx`: es la misma
          decisión y por los mismos motivos. */}
      <SimpleGrid cols={{ base: 2, sm: 3, lg: 6 }}>
        {ORDEN.map((nivel) => (
          <Paper key={nivel} withBorder radius="md" p="md" className="caja-cifra">
            <Badge color={NIVELES[nivel].color} variant="light" mb={4}>
              {NIVELES[nivel].texto}
            </Badge>
            <Text className="cifra" fw={800} lh={1.1}>
              {nivel === 'al_dia' ? alDia : data.resumen[nivel]}
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              {nivel === 'al_dia' && alDia > 0
                ? desgloseAlDia
                : ayudaDe(nivel, data.umbral_critico_dias, data.umbral_advertencia_dias)}
            </Text>
          </Paper>
        ))}
      </SimpleGrid>

      {/* **El vacio tiene dos causas distintas y decia solo una.** Con los dos
          negocios abiertos agendados, la tabla queda sin filas y el mensaje
          afirmaba "no hay negocios con liquidaciones abiertas" -- justo debajo de
          un encabezado que decia "0 de 2 negocios con liquidaciones abiertas". Dos
          frases de la misma pantalla contradiciendose. */}
      {data.filas.length === 0 ? (
        <Paper withBorder radius="md" p="xl">
          <Text ta="center" c="dimmed">
            {abiertos === 0
              ? 'No hay negocios con liquidaciones abiertas.'
              : abiertos === 1
                ? 'El único negocio abierto tiene su próxima acción agendada para más adelante, así que hoy no toca.'
                : `Los ${abiertos} negocios abiertos tienen su próxima acción agendada para más adelante, así que hoy no toca ninguno.`}
          </Text>
        </Paper>
      ) : (
        <div className="tabla-scroll-x">
          <Table striped withTableBorder highlightOnHover fz="xs" className="tabla-una-linea">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Estado</Table.Th>
                <Table.Th>Negocio</Table.Th>
                <Table.Th>Propiedad</Table.Th>
                <Table.Th>Etapa</Table.Th>
                <Table.Th ta="right">Abierto</Table.Th>
                <Table.Th ta="right">Sin gestión</Table.Th>
                <Table.Th ta="right">En la etapa</Table.Th>
                <Table.Th>Última gestión</Table.Th>
                <Table.Th ta="right">Real VP</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.filas.map((f: FilaBandejaNegocio) => (
                <Table.Tr
                  key={f.negocio_id}
                  onClick={() => setFichaId(f.negocio_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <Table.Td>
                    <Badge color={NIVELES[f.nivel].color} variant="light">
                      {NIVELES[f.nivel].texto}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" fw={600}>
                      {f.codigo}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {MODELO_CORTO[f.modelo]}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs">{f.direccion ?? '—'}</Text>
                    <Text size="xs" c="dimmed">
                      {f.comuna ?? '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    {f.etapa ? <EtapaBadge codigo={f.etapa} /> : '—'}
                  </Table.Td>
                  <Table.Td ta="right">
                    <Text size="xs">{duracion(f.duraciones.dias_abierto)}</Text>
                    {f.fecha_inicio && (
                      <Text size="xs" c="dimmed">
                        desde {fecha(f.fecha_inicio)}
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace">
                    {duracion(f.duraciones.dias_sin_gestion)}
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace">
                    {/* Distinto de "sin gestión": se puede haber trabajado diez
                        veces sin salir de la etapa. Ahí está el atasco. */}
                    {duracion(f.duraciones.dias_en_etapa)}
                  </Table.Td>
                  <Table.Td>
                    {f.ultimo_movimiento_nombre ? (
                      <>
                        <Text size="xs">{f.ultimo_movimiento_nombre}</Text>
                        <Text size="xs" c="dimmed">
                          {fecha(f.ultimo_movimiento)}
                        </Text>
                      </>
                    ) : (
                      <Text size="xs" c="dimmed">
                        Nunca
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace">
                    {clp(f.comision_real_vp)}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </div>
      )}

      <Group justify="space-between">
        <Text size="xs" c="dimmed">
          Hacer clic en una fila abre la ficha. Registrar un movimiento lo saca de "sin
          gestión" y reinicia el reloj.
        </Text>
      </Group>

      <NegocioFichaModal
        negocioId={fichaId}
        onClose={() => setFichaId(null)}
        puedeEditar={puedeEditar}
      />
    </Stack>
  )
}
