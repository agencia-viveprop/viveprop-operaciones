import { useQuery } from '@tanstack/react-query'
import { Alert, Group, Paper, SimpleGrid, Stack, Text, Title } from '@mantine/core'
import { IconInfoCircle } from '@tabler/icons-react'
import { obtenerPlataCanjes, type BolsaDeCanjes, type PlazosCanjes } from '../api/canjes'
import { clp, fecha as fmtFecha } from './negociosFormato'
import EstadoConsulta from './EstadoConsulta'
import StatCard from './StatCard'

/**
 * La comisión de Dataprop y los plazos del Centro de Canje.
 *
 * **Es plata de Dataprop, no de ViveProp**, y por eso el panel lo dice arriba en
 * texto y no solo en el título. ViveProp opera el programa a nombre de Dataprop y
 * no percibe nada de él: sumar estos montos con los de negocios sería contar como
 * ingreso propio la comisión de otro.
 *
 * **Las tres cifras no son el mismo número en tres estados.** La cobrada es un
 * hecho registrado; las otras dos son proyecciones que salen de la regla. Van con
 * colores distintos y con el conteo de sobre cuántos canjes se calculó cada una,
 * porque una comisión estimada sobre 118 de 296 cancelados no dice lo mismo que
 * sobre los 296.
 */

/** Un plazo con su dispersión. `null` es "no hay casos", no cero. */
function Plazo({
  titulo,
  n,
  mediana,
  minimo,
  maximo,
  ayuda,
}: {
  titulo: string
  n: number
  mediana: number | null
  minimo: number | null
  maximo: number | null
  ayuda: string
}) {
  return (
    <Paper withBorder radius="md" p="md" className="caja-cifra">
      <Text size="xs" fw={700} c="dimmed" style={{ letterSpacing: 0.5 }}>
        {titulo.toUpperCase()}
      </Text>
      {mediana === null ? (
        <>
          <Text className="cifra" fw={800} mt={4} lh={1.1} c="dimmed">
            —
          </Text>
          <Text size="xs" c="dimmed" mt={4}>
            No hay casos para medir.
          </Text>
        </>
      ) : (
        <>
          <Text className="cifra" fw={800} mt={4} lh={1.1}>
            {mediana} <Text span size="sm" fw={400} c="dimmed">días</Text>
          </Text>
          <Text size="xs" c="dimmed" mt={4}>
            mediana de {n} {n === 1 ? 'caso' : 'casos'} · de {minimo} a {maximo} días
          </Text>
        </>
      )}
      <Text size="xs" c="dimmed" mt={6}>
        {ayuda}
      </Text>
    </Paper>
  )
}

/** El pie de un tile: sobre cuántos canjes se calculó, y cuántos quedaron afuera. */
function detalle(b: BolsaDeCanjes, singular: string, plural: string): string {
  if (b.canjes === 0) return `Ningún canje ${singular}`
  const faltan = b.canjes - b.con_monto
  const base = `${b.canjes} ${b.canjes === 1 ? singular : plural}`
  return faltan > 0 ? `${base} · ${faltan} sin poder valorizar` : base
}

function Plazos({ p }: { p: PlazosCanjes }) {
  return (
    <Stack gap="xs">
      <Title order={5}>Cuánto duran los canjes</Title>
      <Text size="xs" c="dimmed">
        Ninguna de las dos mide cuánto tarda un canje en <strong>cerrar</strong>: no hay un solo
        caso cerrado del cual medirlo. Lo que se puede saber es cuánto sobreviven los que se
        caen, y cuánto llevan los que siguen vivos.
      </Text>
      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        <Plazo
          titulo="Sobreviven antes de caerse"
          n={p.sobrevivencia_n}
          mediana={p.sobrevivencia_mediana}
          minimo={p.sobrevivencia_min}
          maximo={p.sobrevivencia_max}
          ayuda={
            p.sin_fecha_de_termino > 0
              ? `${p.sin_fecha_de_termino} cancelados no tienen fecha de término, así que su duración es desconocida y no entran en esta mediana.`
              : 'Desde la solicitud hasta la cancelación.'
          }
        />
        <Plazo
          titulo="Llevan abiertos"
          n={p.edad_n}
          mediana={p.edad_mediana}
          minimo={p.edad_min}
          maximo={p.edad_max}
          ayuda="Desde la solicitud hasta hoy. Crece solo cada día que pasa."
        />
      </SimpleGrid>
      {p.sobrevivencia_mediana !== null &&
        p.edad_mediana !== null &&
        p.edad_mediana > p.sobrevivencia_mediana && (
          <Text size="xs" c="dimmed">
            Los abiertos llevan más que la mediana de los que se cayeron, así que ya pasaron el
            tramo donde se cae la mayoría.
          </Text>
        )}
    </Stack>
  )
}

export default function PlataDeCanjes() {
  const consulta = useQuery({ queryKey: ['plata-canjes'], queryFn: obtenerPlataCanjes })
  const { data } = consulta

  if (!data) return <EstadoConsulta de={consulta} alto={220} />

  return (
    <Stack gap="md">
      <Stack gap="xs">
        <Group justify="space-between" align="baseline" wrap="wrap">
          <Title order={4}>Comisión de Dataprop</Title>
          <Text size="xs" c="dimmed" ff="monospace">
            UF {data.uf_de_hoy} · {fmtFecha(data.fecha_uf)}
          </Text>
        </Group>
        {/* Va en texto y no solo en el título: el resto de la app habla de plata de
            ViveProp, y alguien podría sumar estos montos con esos. */}
        <Alert color="brand" variant="light" icon={<IconInfoCircle size={18} />}>
          Esta plata es de <strong>Dataprop</strong>, no de ViveProp. ViveProp opera el Centro de
          Canje a nombre de Dataprop y no percibe comisiones por los canjes, así que estos montos
          no se suman con los de Negocios.
        </Alert>
      </Stack>

      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <StatCard
          label="Cobrada"
          value={clp(data.cobrada.comision_dataprop)}
          color="good"
          caption={detalle(data.cobrada, 'cerrado', 'cerrados')}
        />
        <StatCard
          label="Potencial"
          value={clp(data.potencial.comision_dataprop)}
          color="brand"
          caption={detalle(data.potencial, 'abierto', 'abiertos')}
        />
        <StatCard
          label="No concretada"
          value={clp(data.no_concretada.comision_dataprop)}
          color="critical"
          caption={detalle(data.no_concretada, 'cancelado', 'cancelados')}
        />
      </SimpleGrid>

      <Text size="xs" c="dimmed">
        La <strong>cobrada</strong> se registra a mano al cerrar el canje: es lo que se facturó,
        no una estimación. Las otras dos salen de la regla —2% por corredor en venta, medio mes
        cada uno en arriendo, y sobre eso el 6/5/4% según el tramo en UF o el 8% en arriendo—
        aplicada al valor de la propiedad. Todo neto, sin IVA.
      </Text>

      {data.no_concretada.canjes > data.no_concretada.con_monto && (
        <Text size="xs" c="dimmed">
          {data.no_concretada.canjes - data.no_concretada.con_monto === 1
            ? 'El cancelado que no se pudo valorizar es uno que no tiene'
            : `Los ${data.no_concretada.canjes - data.no_concretada.con_monto} cancelados que no se pudieron valorizar son los que no tienen`}{' '}
          valor de propiedad cargado, o se solicitaron antes de donde empieza la serie de UF: no
          se valorizan con la UF de otro día, se informan como no calculados.
        </Text>
      )}

      <Plazos p={data.plazos} />
    </Stack>
  )
}
