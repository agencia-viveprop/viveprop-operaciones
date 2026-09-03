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
 * **Tres tarjetas, siempre, y las tres son plata que Dataprop gana o ganó**
 * (`D-104`). El usuario las pidió así: la total, la potencial desde la etapa de
 * oferta en adelante, y la realmente cobrada en los cerrados.
 *
 * | Tarjeta | Población | Qué responde |
 * |---|---|---|
 * | Comisión total | todos los activos | cuánto hay en la cartera abierta |
 * | Potencial desde oferta | los activos en oferta o más adelante | cuánto de eso ya tiene una oferta sobre la mesa |
 * | Realmente cobrada | los cerrados | cuánto se facturó de verdad |
 *
 * **Las dos primeras no se suman:** la segunda son los mismos canjes de la
 * primera, filtrados por etapa. La diferencia entre ambas es lo que todavía está
 * en revisión o negociando el acuerdo.
 *
 * **Y lo de los cancelados no es una cuarta tarjeta.** Estuvo al mismo nivel y con
 * 5 activos contra 224 cancelados era la cifra más grande de la fila --$39,7
 * millones--, o sea plata que no es de nadie dominando el bloque (`D-102`). Vive en
 * un renglón de referencia, rotulada por lo que es.
 *
 * Cada cifra viaja con el conteo de sobre cuántos canjes se calculó, porque una
 * comisión estimada sobre 121 de 224 cancelados no dice lo mismo que sobre los 224.
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
/** «4 canjes activos», «ningún canje cerrado», con la nota de los que no se
 *  pudieron valorizar cuando hay alguno.
 *
 *  **El sustantivo lo pone el helper y quien llama pasa solo el adjetivo.** Antes
 *  lo ponía solo en el caso de cero, y llamarlo con «canje cerrado» --que es lo que
 *  pedía la frase completa-- imprimía «ningún canje canje cerrado». */
function cuantos(b: BolsaDeCanjes, singular: string, plural: string): string {
  if (b.canjes === 0) return `ningún canje ${singular}`
  const faltan = b.canjes - b.con_monto
  const base = b.canjes === 1 ? `1 canje ${singular}` : `${b.canjes} canjes ${plural}`
  return faltan > 0 ? `${base} · ${faltan} sin poder valorizar` : base
}

/**
 * Lo que se perdió con los canjes cancelados, en un renglón y no en tarjeta.
 *
 * La cifra es cierta y hace falta, pero **no es plata que Dataprop gane ni haya
 * ganado**, que es lo que dicen las tres tarjetas. Al mismo nivel que ellas era la
 * más grande de la fila --$39,7 millones contra $1,7-- y dominaba el bloque
 * (`D-102`).
 */
function FueraDeLaComision({ noConcretada }: { noConcretada: BolsaDeCanjes }) {
  const sinValorizar = noConcretada.canjes - noConcretada.con_monto

  return (
    <Stack gap={2}>
      <Text size="xs" c="dimmed">
        Fuera de la comisión, para referencia:
      </Text>
      <Text size="xs" c="dimmed">
        <strong>No se llegó a cobrar</strong> {clp(noConcretada.comision_dataprop)} ·{' '}
        {cuantos(noConcretada, 'cancelado', 'cancelados')}.
        {sinValorizar > 0 && (
          <>
            {' '}
            {sinValorizar === 1
              ? 'El que no se pudo valorizar no tiene'
              : `Los ${sinValorizar} que no se pudieron valorizar no tienen`}{' '}
            valor de propiedad cargado, o se solicitaron antes de donde empieza la serie de UF:
            no se valorizan con la UF de otro día, se informan como no calculados.
          </>
        )}
      </Text>
    </Stack>
  )
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

      {/* Las tres van siempre, incluso en cero: la de cerrados marca $0 mientras no
          haya ninguno, y esconderla dejaría la pregunta «cuánto se cobró» sin
          respuesta en pantalla. */}
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <StatCard
          label="Comisión total"
          value={clp(data.potencial.comision_dataprop)}
          color="brand"
          caption={
            data.potencial.canjes === 0
              ? 'Ningún canje activo'
              : `${cuantos(data.potencial, 'activo', 'activos')}, en cualquier etapa`
          }
        />
        <StatCard
          label="Potencial desde oferta"
          value={clp(data.potencial_desde_oferta.comision_dataprop)}
          color="info"
          caption={
            data.potencial_desde_oferta.canjes === 0
              ? 'Ningún activo llegó a oferta'
              : `${cuantos(data.potencial_desde_oferta, 'activo', 'activos')} en oferta o más adelante`
          }
        />
        <StatCard
          label="Realmente cobrada"
          value={clp(data.cobrada.comision_dataprop)}
          color="good"
          caption={
            data.cobrada.canjes === 0
              ? 'Ningún canje cerrado'
              : cuantos(data.cobrada, 'cerrado', 'cerrados')
          }
        />
      </SimpleGrid>

      <Text size="xs" c="dimmed">
        La <strong>total</strong> y la <strong>potencial desde oferta</strong> son la misma plata
        con dos varas y <strong>no se suman</strong>: la segunda son los mismos canjes activos,
        dejando fuera los que están en revisión o negociando el acuerdo. Las dos son estimaciones:
        salen de la regla —2% por corredor en venta, medio mes cada uno en arriendo, y sobre eso
        el 6/5/4% según el tramo en UF o el 8% en arriendo— aplicada al valor de la propiedad, con
        la UF de hoy. La <strong>realmente cobrada</strong> no se estima: se registra a mano al
        cerrar el canje. Todo neto, sin IVA.
      </Text>

      <FueraDeLaComision noConcretada={data.no_concretada} />

      <Plazos p={data.plazos} />
    </Stack>
  )
}
