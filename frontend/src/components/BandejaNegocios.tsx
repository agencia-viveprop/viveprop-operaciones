import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Center,
  Group,
  Loader,
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
import { clp, duracion, fecha, MODELO_CORTO } from './negociosFormato'

/**
 * Los niveles con su palabra, nunca el color solo.
 *
 * Los umbrales son en **días**, no en horas: los 48/24 horas de canjes miden un
 * ciclo de días, y acá los procesos duran de un mes a varios. En horas no
 * distinguirían nada.
 */
const NIVELES: Record<NivelNegocio, { texto: string; color: string; ayuda: string }> = {
  sin_gestion: {
    texto: 'Sin gestión',
    color: 'gray',
    ayuda: 'Nunca se registró un movimiento',
  },
  critico: { texto: 'Crítico', color: 'critical', ayuda: 'Más de 30 días sin gestión' },
  advertencia: { texto: 'Advertencia', color: 'warning', ayuda: 'Entre 14 y 30 días' },
  al_dia: { texto: 'Al día', color: 'good', ayuda: 'Menos de 14 días' },
}

const ORDEN: NivelNegocio[] = ['sin_gestion', 'critico', 'advertencia', 'al_dia']

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
  const { data, isLoading } = useQuery({
    queryKey: ['bandeja-negocios'],
    queryFn: obtenerBandejaNegocios,
  })

  if (isLoading) {
    return (
      <Center h={240}>
        <Loader />
      </Center>
    )
  }
  if (!data) return null

  const requieren = data.resumen.sin_gestion + data.resumen.critico + data.resumen.advertencia

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        {requieren} de {data.filas.length} negocios con liquidaciones abiertas requieren
        atención. Los umbrales son en días, no en horas: acá los procesos duran de un mes a
        varios.
      </Text>

      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        {ORDEN.map((nivel) => (
          <Paper key={nivel} withBorder radius="md" p="md">
            <Badge color={NIVELES[nivel].color} variant="light" mb={4}>
              {NIVELES[nivel].texto}
            </Badge>
            <Text size="28px" fw={800} lh={1.1}>
              {data.resumen[nivel]}
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              {NIVELES[nivel].ayuda}
            </Text>
          </Paper>
        ))}
      </SimpleGrid>

      {data.filas.length === 0 ? (
        <Paper withBorder radius="md" p="xl">
          <Text ta="center" c="dimmed">
            No hay negocios con liquidaciones abiertas.
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
                    {f.etapa ? <Badge variant="default">{f.etapa}</Badge> : '—'}
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
