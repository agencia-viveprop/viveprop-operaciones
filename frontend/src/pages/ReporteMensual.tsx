import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ActionIcon,
  Badge,
  Group,
  Paper,
  Progress,
  SegmentedControl,
  Select,
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
  type Comparar,
  type ConteoDeEtapa,
  type DuracionEtapa,
  type Dominio,
  type Comparacion,
  type Variacion,
} from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'
import PlataDeNegocios from '../components/PlataDeNegocios'
import EvolucionMensual, { Veredicto } from '../components/EvolucionMensual'
import { rotuloEtapa } from '../components/canjesEtiquetas'
import { obtenerCatalogos } from '../api/catalogos'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

/**
 * De lo que entró en la ventana, cómo está hoy.
 *
 * **Es la foto de hoy y no la del cierre del período**, y el subtítulo lo dice:
 * reconstruir en qué etapa estaba cada canje al 30 de junio pide recorrer sus
 * movimientos uno por uno, y ese dato existe solo desde que el pipeline se usa en
 * la app (`D-098`).
 */
function PanelEtapas({
  titulo,
  subtitulo,
  conteos,
  rotularEtapa,
}: {
  titulo: string
  subtitulo: string
  conteos: ConteoDeEtapa[]
  rotularEtapa: (codigo: string | null) => string
}) {
  const total = conteos.reduce((a, c) => a + c.cantidad, 0)

  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5}>{titulo}</Title>
      <Text size="xs" c="dimmed" mb="sm">
        {subtitulo}
      </Text>
      {total === 0 ? (
        <Text size="sm" c="dimmed">
          Nada entró en esta ventana.
        </Text>
      ) : (
        <Stack gap={6}>
          {conteos.map((c) => (
            <Group key={c.etapa ?? 'sin'} gap="sm" wrap="nowrap">
              <Text size="sm" w={220} style={{ flexShrink: 0 }}>
                {rotularEtapa(c.etapa)}
              </Text>
              {/* La barra da la proporción de un vistazo; el número la precisa.
                  Con cuatro o cinco etapas una tabla de números pide comparar de
                  cabeza. */}
              <Progress
                value={(c.cantidad / total) * 100}
                size="lg"
                radius="sm"
                style={{ flex: 1, minWidth: 60 }}
              />
              <Text size="sm" ff="monospace" w={70} ta="right" style={{ flexShrink: 0 }}>
                {c.cantidad}
                <Text span size="xs" c="dimmed">
                  {' '}
                  {Math.round((c.cantidad / total) * 100)}%
                </Text>
              </Text>
            </Group>
          ))}
        </Stack>
      )}
    </Paper>
  )
}

/**
 * Cuánto llevan los abiertos en la etapa en que están.
 *
 * **El `n` va en la tabla, no escondido.** Con siete canjes repartidos en cuatro
 * etapas, el promedio de una etapa puede ser un solo caso: sin el `n` un «54 días»
 * se lee como una tendencia cuando es una anécdota.
 *
 * **Es una foto y no depende de la ventana**, y hace falta decirlo: está en una
 * pantalla donde todo lo demás sí depende. Los abiertos son los de hoy.
 */
function PanelDuraciones({
  duraciones,
  rotularEtapa,
  vacio,
}: {
  duraciones: DuracionEtapa[]
  rotularEtapa: (codigo: string | null) => string
  /** Qué decir cuando no hay nada. No es lo mismo «no hay abiertos» que «no hay
   *  historia de etapas», y en negocios es lo segundo. */
  vacio: string
}) {
  const sinHistoria = duraciones.reduce((a, d) => a + d.sin_historia, 0)

  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5}>Cuánto llevan en su etapa</Title>
      <Text size="xs" c="dimmed" mb="sm">
        De los que están abiertos hoy. <strong>No depende de la ventana</strong>: los abiertos
        son los de hoy, así que esta foto es la misma en cualquier período.
      </Text>
      {duraciones.length === 0 ? (
        <Text size="sm" c="dimmed">
          {vacio}
        </Text>
      ) : (
        <>
          <div className="tabla-scroll-x">
            <Table withRowBorders={false} verticalSpacing={4} miw={420}>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Etapa</Table.Th>
                  <Table.Th ta="right">Casos</Table.Th>
                  <Table.Th ta="right">Promedio</Table.Th>
                  <Table.Th ta="right">Rango</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {duraciones.map((d) => (
                  <Table.Tr key={d.etapa ?? 'sin'}>
                    <Table.Td>{rotularEtapa(d.etapa)}</Table.Td>
                    <Table.Td ta="right" ff="monospace">
                      {d.n}
                    </Table.Td>
                    <Table.Td ta="right" ff="monospace">
                      {d.dias_promedio} d
                    </Table.Td>
                    <Table.Td ta="right" ff="monospace" c="dimmed">
                      {d.dias_min === d.dias_max ? '—' : `${d.dias_min}–${d.dias_max} d`}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </div>
          {sinHistoria > 0 && (
            <Text size="xs" c="dimmed" mt="xs">
              {sinHistoria === 1 ? 'Uno' : sinHistoria} sin movimiento que registre la entrada a
              la etapa: ahí el reloj se cuenta desde el inicio, que no es lo mismo que haberlo
              medido.
            </Text>
          )}
        </>
      )}
    </Paper>
  )
}

/** Las métricas que son plata se muestran como plata; el resto, como cuenta. */
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
  return v.es_plata ? clp(n) : String(n)
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
  const diferencia = v.es_plata ? clp(Math.abs(abs)) : String(Math.abs(abs))

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
    <Paper withBorder radius="md" p="md" className="caja-cifra" style={{ ["--cifra-max" as string]: "1.375rem" }}>
      <Text size="xs" fw={700} c="dimmed">
        {etiqueta}
      </Text>
      <Text className="cifra" fw={800} mt={4} lh={1.1}>
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
  // Contra qué se compara la serie superpuesta. Arranca en el tramo anterior
  // porque siempre tiene datos; la interanual depende de que exista ese tramo del
  // año pasado, y en negocios está casi vacío (`D-098`).
  const [comparacion, setComparacion] = useState<Comparar>('anterior')

  // Los nombres de las etapas de negocio viven en el catálogo. La consulta ya
  // está en caché para toda la app, así que pedirla acá no cuesta una llamada.
  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const rotuloEtapaNegocio = (codigo: string | null) => {
    if (!codigo) return 'sin etapa'
    const etapa = catalogos?.etapas.find((e) => e.codigo === codigo)
    return etapa ? `${codigo} · ${etapa.nombre}` : codigo
  }
  // Arranca en negocios: es donde está la plata, y el reporte de cierre se lee
  // por ahí. Canjes es volumen de gestión, no resultado.
  const [dominio, setDominio] = useState<Dominio>('negocios')

  const cursor = new Date(ahora.getFullYear(), ahora.getMonth() + desplazamiento, 1)
  const anio = cursor.getFullYear()
  const mes = cursor.getMonth() + 1

  const consulta = useQuery({
    queryKey: ['reporte-mensual', anio, mes, ventana, comparacion],
    queryFn: () => obtenerReporteMensual(anio, mes, Number(ventana), comparacion),
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
            {/* La ventana pasó a ser un desplegable: son trece opciones --1 a 12
                meses y la histórica-- y en botones en fila no caben (`D-098`). */}
            <Group gap="xs">
              <Text size="xs" c="dimmed">
                Ventana móvil de
              </Text>
              <Select
                size="xs"
                w={170}
                value={ventana}
                onChange={(v) => setVentana(v ?? '6')}
                data={VENTANAS.map((v) => ({ value: String(v), label: rotuloVentana(v) }))}
                allowDeselect={false}
              />
              {/* Las semanas del mes elegido. Es la base variable que se pidió, y
                  va como dato y no como control: con la ventana en un mes el
                  desglose ya viene por semanas. */}
              <Text size="xs" c="dimmed">
                · {MESES[mes - 1]} tiene {data.semanas_del_mes} semanas
              </Text>
            </Group>

            {/* La comparación superpone otra serie en el gráfico, en gris. No
                agrega un control nuevo por métrica: es una sola decisión para
                toda la pantalla. */}
            {!data.es_historico && (
              <Group gap="xs">
                <Text size="xs" c="dimmed">
                  Comparar con
                </Text>
                <SegmentedControl
                  size="xs"
                  value={comparacion}
                  onChange={(v) => setComparacion(v as Comparar)}
                  data={[
                    { value: 'anterior', label: 'período anterior' },
                    { value: 'anio_anterior', label: 'año anterior' },
                  ]}
                />
              </Group>
            )}
          </Group>

          {/* Los tiles muestran la **ventana**, no el mes.
           *
           * Estaban al revés: mostraban el mes calendario, arriba y en grande, en
           * una pantalla que dice que el mes es un detalle. El resultado era que
           * lo primero que se veía era "$0" --cierto para agosto, porque el
           * último cierre es del 1 de junio-- y la conclusión natural era que la
           * app estaba rota. La maquetación contradecía el mensaje. */}
          {dominio === 'negocios' ? (
            <SimpleGrid cols={{ base: 2, md: 4 }}>
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
            <SimpleGrid cols={{ base: 2, md: 4 }}>
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
                serieComparacion={data.serie_comparacion}
                rotuloComparacion={rotulo(data.rotulo_comparacion)}
                series={[{ campo: 'comision_real_vp', nombre: 'Comisión real VP', tono: 'principal' }]}
                promedio={Number(data.promedio.comision_real_vp)}
                tendencia={data.tendencias.comision_real_vp}
                esPlata
              />
              <PlataDeNegocios
                serie={serie}
                promedio={data.promedio}
                tendencias={data.tendencias}
              />
              <EvolucionMensual
                titulo="Liquidaciones y negocios por mes"
                subtitulo="Cuántos cerraron y cuántos entraron. Van en un gráfico aparte del de plata: un mismo eje para montos y unidades deja elegir la escala a gusto."
                serie={serie}
                serieComparacion={data.serie_comparacion}
                rotuloComparacion={rotulo(data.rotulo_comparacion)}
                series={[
                  { campo: 'hitos_cerrados', nombre: 'Liquidaciones cerradas', tono: 'principal' },
                  { campo: 'negocios_iniciados', nombre: 'Negocios iniciados', tono: 'secundaria' },
                ]}
                tendencia={data.tendencias.hitos_cerrados}
              />

              <PanelEtapas
                titulo="Negocios por etapa"
                subtitulo="De los negocios iniciados en la ventana, en qué etapa están hoy."
                conteos={data.negocios_por_etapa}
                rotularEtapa={rotuloEtapaNegocio}
              />
              <PanelEtapas
                titulo="Liquidaciones por estado"
                subtitulo="Van por liquidación y no por negocio: el estado vive en la liquidación, y un negocio con la promesa cerrada y la escritura activa está en los dos."
                conteos={data.hitos_por_estado}
                rotularEtapa={(c) => c ?? 'sin estado'}
              />
              <PanelDuraciones
                duraciones={data.duracion_negocios_por_etapa}
                rotularEtapa={rotuloEtapaNegocio}
                vacio="Todavía no se puede medir: el pipeline de negocios no tiene ningún movimiento registrado, así que no existe historia de cuándo entró cada negocio a su etapa. Aparece en cuanto se empiece a registrar el avance."
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
                  La comisión de Dataprop se calcula con la regla del contrato: 6/5/4% del
                  corretaje en venta según el tramo en UF, 8% en arriendo. Es{' '}
                  <strong>plata de Dataprop, no de ViveProp</strong>, y no se suma nunca con la
                  de negocios. Los canjes cuya fecha queda fuera de la serie de UF no se pueden
                  valorizar y se informan aparte: un monto bajo por eso no es poca plata.
                </Text>
              </Paper>
              {/* Apilado y no lado a lado: los tres estados suman exactamente
                  los solicitados, así que el alto total de la barra es la
                  solicitud del mes y cada estado queda como su propio segmento.
                  Lado a lado, cuatro activos junto a noventa cancelados eran una
                  raya al lado de una torre.

                  Eran dos segmentos hasta que apareció el estado «Cerrado». */}
              <EvolucionMensual
                titulo="Solicitudes por mes, y qué pasó con ellas"
                subtitulo="El alto de la barra es lo que entró en el mes; los segmentos, en qué terminó. Los cancelados se cuentan por su mes de solicitud, no de cancelación: la base no guarda cuándo se canceló."
                serie={serie}
                serieComparacion={data.serie_comparacion}
                rotuloComparacion={rotulo(data.rotulo_comparacion)}
                apilado
                etiquetaTotal="Solicitados"
                series={[
                  /* El orden no es negociable por estetica: es el que valido la
                     paleta. Ver `PALETA` en `EvolucionMensual`. */
                  { campo: 'canjes_cerrados', nombre: 'Cerrados', tono: 'positiva' },
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
                serieComparacion={data.serie_comparacion}
                rotuloComparacion={rotulo(data.rotulo_comparacion)}
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

              <PanelEtapas
                titulo="Canjes por etapa"
                subtitulo="De los canjes solicitados en la ventana, en qué etapa están hoy."
                conteos={data.canjes_por_etapa}
                rotularEtapa={(c) => (c ? rotuloEtapa(c) : 'sin etapa')}
              />
              <PanelDuraciones
                duraciones={data.duracion_canjes_por_etapa}
                rotularEtapa={(c) => (c ? rotuloEtapa(c) : 'sin etapa')}
                vacio="No hay canjes abiertos."
              />
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
