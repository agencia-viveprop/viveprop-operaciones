import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ActionIcon,
  Badge,
  Group,
  Paper,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from '@mantine/core'
import { IconChevronLeft, IconChevronRight, IconMinus } from '@tabler/icons-react'
import {
  obtenerReporteMensual,
  rotuloVentana,
  serieDelDominio,
  VENTANAS,
  type Dominio,
  type Comparacion,
  type Variacion,
} from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'
import EvolucionMensual, { Veredicto } from '../components/EvolucionMensual'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

/** Las métricas que son plata se muestran como plata; el resto, como cuenta. */
const EN_PESOS = new Set(['Comisión real ViveProp', 'Comisión total'])

function rotulo(etiqueta: string): string {
  // Las ventanas vienen como '2026-03 a 2026-08'; un mes suelto, como '2026-08'.
  if (etiqueta.includes(' a ')) {
    return etiqueta
      .split(' a ')
      .map((e) => rotulo(e))
      .join(' — ')
  }
  const [anio, mes] = etiqueta.split('-')
  return `${MESES[Number(mes) - 1]} ${anio}`
}

function valor(v: Variacion, campo: 'actual' | 'referencia'): string {
  const n = Number(v[campo])
  return EN_PESOS.has(v.metrica) ? clp(n) : String(n)
}

/**
 * La variación, con su signo y su color.
 *
 * **`pct` nulo no es cero ni infinito: es que no hay base.** Si el período de
 * referencia tuvo cero, no existe porcentaje que calcular, y mostrar uno sería
 * inventarlo. Se dice "nuevo" y se muestra la diferencia absoluta, que sí
 * significa algo.
 */
function Delta({ v }: { v: Variacion }) {
  const abs = Number(v.absoluta)
  const sinBase = v.pct === null

  if (abs === 0 && sinBase) {
    return (
      <Group gap={4} justify="flex-end" c="dimmed">
        <IconMinus size={13} />
        <Text size="xs">sin cambio</Text>
      </Group>
    )
  }

  const color = abs > 0 ? 'good' : 'critical'
  const signo = abs > 0 ? '+' : ''
  const diferencia = EN_PESOS.has(v.metrica) ? clp(Math.abs(abs)) : String(Math.abs(abs))

  return (
    <Group gap={6} justify="flex-end" wrap="nowrap">
      {sinBase ? (
        <Tooltip label="El período de referencia estuvo en cero: no hay porcentaje que calcular">
          <Badge color={color} variant="light" size="sm">
            nuevo
          </Badge>
        </Tooltip>
      ) : (
        <Badge color={color} variant="light" size="sm">
          {signo}
          {v.pct}%
        </Badge>
      )}
      <Text size="xs" c="dimmed">
        {abs > 0 ? '+' : '−'}
        {diferencia}
      </Text>
    </Group>
  )
}

/** Un recuadro de titular. Se extrajo porque ahora hay dos juegos --uno por
 *  dominio-- y repetir el marcado siete veces invita a que se desalineen. */
function Tile({
  rotulo: etiqueta,
  valor: monto,
  pie,
}: {
  rotulo: string
  valor: string | number
  pie?: string
}) {
  return (
    <Paper withBorder radius="md" p="md">
      <Text size="xs" fw={700} c="dimmed">
        {etiqueta}
      </Text>
      <Text size="22px" fw={800} mt={4} lh={1.1}>
        {monto}
      </Text>
      {pie && (
        <Text size="xs" c="dimmed" mt={4}>
          {pie}
        </Text>
      )}
    </Paper>
  )
}


function TablaComparacion({
  titulo,
  ayuda,
  c,
  dominio,
}: {
  titulo: string
  ayuda: string
  c: Comparacion
  /** Qué mitad del reporte se está mirando. El filtro va por este campo y no
   *  por el nombre visible de la métrica: renombrar una métrica no puede
   *  cambiar en silencio de qué reporte forma parte. */
  dominio: Dominio
}) {
  const filas = c.variaciones.filter((v) => v.dominio === dominio)

  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5}>{titulo}</Title>
      <Text size="xs" c="dimmed" mb="sm">
        {ayuda} · <strong>{rotulo(c.actual.etiqueta)}</strong> contra{' '}
        {rotulo(c.contra.etiqueta)}
      </Text>
      <div className="tabla-scroll-x">
        <Table striped fz="xs" className="tabla-una-linea">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Métrica</Table.Th>
              <Table.Th ta="right">Período</Table.Th>
              <Table.Th ta="right">Referencia</Table.Th>
              <Table.Th ta="right">Variación</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {filas.map((v) => (
              <Table.Tr key={v.metrica}>
                <Table.Td>{v.metrica}</Table.Td>
                <Table.Td ta="right" ff="monospace">
                  {valor(v, 'actual')}
                </Table.Td>
                <Table.Td ta="right" ff="monospace" c="dimmed">
                  {valor(v, 'referencia')}
                </Table.Td>
                <Table.Td>
                  <Delta v={v} />
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </div>
    </Paper>
  )
}

/**
 * El reporte de cierre, con ventanas móviles.
 *
 * **El mes calendario no es la unidad natural de este negocio.** Los procesos
 * duran de un mes a varios, así que un mes en cero no es un mes malo: es que
 * ningún proceso terminó de madurar. Cuántos meses de la ventana estuvieron
 * vacíos lo cuenta la API --antes era un número escrito acá que envejecía-- y el
 * ticket varía cuatro veces. Con ~1 cierre por mes y esa dispersión, la
 * comparación mes contra mes mide ruido, no desempeño.
 *
 * Por eso el titular es una **ventana móvil** contra la anterior del mismo largo,
 * el **año corrido** va contra el mismo tramo del año pasado, y el mes queda
 * arriba como detalle de qué cerró.
 *
 * El largo de la ventana es un control y no una constante: el horizonte correcto
 * depende de qué se esté mirando, y quien lee el reporte lo sabe mejor.
 *
 * No hay serie de veinticuatro meses acá: eso ya está en los gráficos "por mes"
 * del dashboard y responde otra pregunta.
 */
export default function ReporteMensual() {
  const ahora = new Date()
  const [desplazamiento, setDesplazamiento] = useState(0)
  const [ventana, setVentana] = useState('6')
  // Arranca en negocios: es donde está la plata, y el reporte de cierre se lee
  // por ahí. Canjes es volumen de gestión, no resultado.
  const [dominio, setDominio] = useState<Dominio>('negocios')

  const cursor = new Date(ahora.getFullYear(), ahora.getMonth() + desplazamiento, 1)
  const anio = cursor.getFullYear()
  const mes = cursor.getMonth() + 1

  const consulta = useQuery({
    queryKey: ['reporte-mensual', anio, mes, ventana],
    queryFn: () => obtenerReporteMensual(anio, mes, Number(ventana)),
  })
  const { data } = consulta

  // La serie que se dibuja: en la ventana histórica arranca donde arranca el
  // dominio que se está mirando, no en el primer registro de cualquiera de los
  // dos. Ver `serieDelDominio`.
  const serie = data
    ? serieDelDominio(data.serie, data.es_historico, data.inicio_por_dominio[dominio])
    : []

  return (
    <Stack gap="md">
      <PageHeader
        title="Reporte mensual"
        subtitle="En un negocio donde los procesos duran de un mes a varios, un mes en cero no es un mes malo. Por eso el titular es una ventana móvil, y el mes queda como detalle."
        action={
          <Group gap="xs">
            <Tooltip label="Mes anterior">
              <ActionIcon variant="default" onClick={() => setDesplazamiento((d) => d - 1)} aria-label="Mes anterior">
                <IconChevronLeft size={16} />
              </ActionIcon>
            </Tooltip>
            <Text size="sm" fw={600} w={150} ta="center" tt="capitalize">
              {rotulo(`${anio}-${String(mes).padStart(2, '0')}`)}
            </Text>
            <Tooltip label={desplazamiento >= 0 ? 'Todavía no empieza' : 'Mes siguiente'}>
              <ActionIcon
                variant="default"
                disabled={desplazamiento >= 0}
                onClick={() => setDesplazamiento((d) => d + 1)}
                aria-label="Mes siguiente"
              >
                <IconChevronRight size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        }
      />

      {!data ? (
        <EstadoConsulta de={consulta} alto={240} />
      ) : (
        <>
          {/* Los dos selectores van primero porque mandan sobre todo lo de
              abajo: uno elige qué reporte y el otro con qué horizonte. */}
          <Group gap="lg" wrap="wrap">
            <SegmentedControl
              color="accent"
              value={dominio}
              onChange={(v) => setDominio(v as Dominio)}
              data={[
                { value: 'negocios', label: 'Negocios' },
                { value: 'canjes', label: 'Canjes' },
              ]}
            />
            <Group gap="xs">
              <Text size="xs" c="dimmed">
                Ventana móvil de
              </Text>
              <SegmentedControl
                size="xs"
                color="accent"
                value={ventana}
                onChange={setVentana}
                data={VENTANAS.map((v) => ({ value: String(v), label: rotuloVentana(v) }))}
              />
            </Group>
          </Group>

          {/* Los tiles muestran la **ventana**, no el mes.
           *
           * Estaban al revés: mostraban el mes calendario, arriba y en grande, en
           * una pantalla que dice que el mes es un detalle. El resultado era que
           * lo primero que se veía era "$0" --cierto para agosto, porque el
           * último cierre es del 1 de junio-- y la conclusión natural era que la
           * app estaba rota. La maquetación contradecía el mensaje. */}
          {dominio === 'negocios' ? (
            <SimpleGrid cols={{ base: 2, sm: 4 }}>
              <Tile
                rotulo="COMISIÓN REAL VP"
                valor={clp(data.movil.actual.comision_real_vp)}
                pie={data.es_historico ? 'en todo el histórico' : `en ${data.ventana_meses} meses`}
              />
              <Tile rotulo="COMISIÓN TOTAL" valor={clp(data.movil.actual.comision_total)} />
              <Tile
                rotulo="LIQUIDACIONES"
                valor={data.movil.actual.hitos_cerrados}
                pie="cerradas en la ventana"
              />
              <Tile rotulo="NEGOCIOS INICIADOS" valor={data.movil.actual.negocios_iniciados} />
            </SimpleGrid>
          ) : (
            <SimpleGrid cols={{ base: 2, sm: 4 }}>
              <Tile
                rotulo="CANJES SOLICITADOS"
                valor={data.movil.actual.canjes_solicitados}
                pie={data.es_historico ? 'en todo el histórico' : `en ${data.ventana_meses} meses`}
              />
              {/* Los activos van al lado de los solicitados porque son parte de
                  ellos: de los que entraron en la ventana, los que siguen vivos. */}
              <Tile
                rotulo="CANJES ACTIVOS"
                valor={data.movil.actual.canjes_activos}
                pie="de los solicitados en la ventana"
              />
              <Tile rotulo="CANJES CERRADOS" valor={data.movil.actual.canjes_cerrados} />
              <Tile rotulo="CANJES CANCELADOS" valor={data.movil.actual.canjes_cancelados} />
            </SimpleGrid>
          )}

          {/* La evolución va **antes** de las tablas: es la respuesta a "cómo
              vamos", y las tablas son el detalle de cuánto. */}
          {dominio === 'negocios' ? (
            <>
              <Paper withBorder radius="md" p="md">
                <Veredicto
                  actual={Number(serie[serie.length - 1]?.comision_real_vp ?? 0)}
                  promedio={Number(data.promedio.comision_real_vp)}
                  unidad="comisión"
                  tendencia={data.tendencias.comision_real_vp}
                  esPlata
                />
              </Paper>
              <EvolucionMensual
                titulo="Comisión real ViveProp por mes"
                subtitulo="La línea punteada es el promedio de la ventana. El mes que se está mirando es la última barra, y su valor va arriba a la derecha."
                serie={serie}
                series={[{ campo: 'comision_real_vp', nombre: 'Comisión real VP', tono: 'principal' }]}
                promedio={Number(data.promedio.comision_real_vp)}
                tendencia={data.tendencias.comision_real_vp}
                esPlata
              />
              <EvolucionMensual
                titulo="Liquidaciones y negocios por mes"
                subtitulo="Cuántos cerraron y cuántos entraron. Van en un gráfico aparte del de plata: un mismo eje para montos y unidades deja elegir la escala a gusto."
                serie={serie}
                series={[
                  { campo: 'hitos_cerrados', nombre: 'Liquidaciones cerradas', tono: 'principal' },
                  { campo: 'negocios_iniciados', nombre: 'Negocios iniciados', tono: 'secundaria' },
                ]}
                tendencia={data.tendencias.hitos_cerrados}
              />
            </>
          ) : (
            <>
              <Paper withBorder radius="md" p="md">
                <Veredicto
                  actual={serie[serie.length - 1]?.canjes_solicitados ?? 0}
                  promedio={Number(data.promedio.canjes_solicitados)}
                  unidad="solicitudes"
                  tendencia={data.tendencias.canjes_solicitados}
                />
                <Text size="xs" c="dimmed" mt={6}>
                  Canjes no tiene eje de plata todavía. Sí genera comisión --la de
                  administración de Dataprop, 6/5/4% en venta según el tramo en UF u 8% en
                  arriendo-- pero se calcula sobre la comisión de los corredores, y ese dato
                  está sin cargar en todas las filas.
                </Text>
              </Paper>
              {/* Apilado y no lado a lado: los activos y los cancelados suman
                  exactamente los solicitados, así que el alto total de la barra es
                  la solicitud del mes y el activo queda como su propio segmento.
                  Lado a lado, cuatro activos junto a noventa cancelados eran una
                  raya al lado de una torre. */}
              <EvolucionMensual
                titulo="Solicitudes por mes, y qué pasó con ellas"
                subtitulo="El alto de la barra es lo que entró en el mes; los segmentos, en qué terminó. Los cancelados se cuentan por su mes de solicitud, no de cancelación: la base no guarda cuándo se canceló."
                serie={serie}
                apilado
                series={[
                  { campo: 'canjes_activos', nombre: 'Siguen activos', tono: 'principal' },
                  { campo: 'canjes_cancelados', nombre: 'Cancelados', tono: 'negativa' },
                ]}
                promedio={Number(data.promedio.canjes_solicitados)}
                tendencia={data.tendencias.canjes_solicitados}
              />
              <EvolucionMensual
                titulo="Canjes activos por mes"
                subtitulo="Los mismos activos, en su propia escala. En el gráfico de arriba son un segmento chico sobre el total; acá se ve su forma."
                serie={serie}
                series={[{ campo: 'canjes_activos', nombre: 'Activos', tono: 'principal' }]}
                promedio={Number(data.promedio.canjes_activos)}
                tendencia={data.tendencias.canjes_activos}
              />
              <Text size="xs" c="dimmed">
                «Canjes cerrados» va en la tabla y no en los gráficos porque es cero en todos
                los meses: ningún canje se ha cerrado con éxito. Los que quedaron con la etapa
                en «Cerrado» están todos cancelados, así que un canje que no está cancelado
                está activo, y por eso los dos segmentos suman el total.
              </Text>
            </>
          )}

          {/* En la histórica no hay ventana anterior: antes del primer registro
              no existe nada, así que la tabla saldría entera en "sin base". Se
              reemplaza por la explicación. */}
          {data.es_historico ? (
            <Paper withBorder radius="md" p="md">
              <Title order={5}>Histórico completo</Title>
              <Text size="sm" c="dimmed" mt={4}>
                {data.ventana_meses} meses, desde el primer registro. No hay comparación
                contra un período anterior porque antes de eso no hay nada: lo que se compara
                es el año corrido, más abajo.
              </Text>
            </Paper>
          ) : (
            <TablaComparacion
              titulo={`Últimos ${data.ventana_meses} meses`}
              ayuda="Contra los mismos meses inmediatamente anteriores, sin solaparse"
              c={data.movil}
              dominio={dominio}
            />
          )}
          <TablaComparacion
            titulo="Año corrido"
            ayuda="Contra el mismo tramo del año pasado, no contra el año entero"
            c={data.anio_corrido}
            dominio={dominio}
          />

          {/* El mes, como detalle y al final.
           *
           * Cuando no cerró nada se dice con palabras y no con "$0": un cero en
           * un tile grande se lee como un error, y una frase se lee como lo que
           * es -- ningún proceso terminó de madurar ese mes. */}
          <Paper withBorder radius="md" p="md">
            <Title order={5} tt="capitalize">
              {rotulo(data.mes.etiqueta)}, el mes suelto
            </Title>
            <Text size="sm" mt={6}>
              {dominio === 'canjes' ? (
                data.mes.canjes_solicitados === 0 ? (
                  <>No entró ninguna solicitud de canje en el mes.</>
                ) : (
                  <>
                    Entraron {data.mes.canjes_solicitados}{' '}
                    {data.mes.canjes_solicitados === 1 ? 'solicitud' : 'solicitudes'}:{' '}
                    {data.mes.canjes_activos}{' '}
                    {data.mes.canjes_activos === 1 ? 'sigue activa' : 'siguen activas'} y{' '}
                    {data.mes.canjes_cancelados} ya{' '}
                    {data.mes.canjes_cancelados === 1 ? 'está cancelada' : 'están canceladas'}.
                  </>
                )
              ) : data.mes.hitos_cerrados === 0 ? (
                <>
                  No se cerró ninguna liquidación en el mes. Con procesos que duran de un
                  mes a varios eso es normal: {data.meses_sin_cierres} de los{' '}
                  {data.meses_con_negocios} meses con negocios estuvieron vacíos.
                </>
              ) : (
                <>
                  {data.mes.hitos_cerrados}{' '}
                  {data.mes.hitos_cerrados === 1 ? 'liquidación cerrada' : 'liquidaciones cerradas'}{' '}
                  por {clp(data.mes.comision_real_vp)} de comisión real.
                </>
              )}{' '}
              {dominio === 'negocios' && data.mes.negocios_iniciados > 0 && (
                <>
                  Entraron {data.mes.negocios_iniciados}{' '}
                  {data.mes.negocios_iniciados === 1 ? 'negocio' : 'negocios'}.
                </>
              )}
            </Text>
            <Text size="xs" c="dimmed" mt={6}>
              El mes no se compara contra el anterior a propósito: con esta duración de
              procesos, esa variación mide ruido.
            </Text>
          </Paper>
        </>
      )}
    </Stack>
  )
}
