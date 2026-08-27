import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Alert,
  Button,
  Group,
  Paper,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { IconInfoCircle, IconPrinter } from '@tabler/icons-react'
import {
  obtenerVistaDirectorio,
  rotuloVentana,
  serieDelDominio,
  VENTANAS,
  type Conteo,
  type Dominio,
  type Monto,
} from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp, fecha, MODELO_CORTO } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'
import PlataDeNegocios from '../components/PlataDeNegocios'
import EvolucionMensual, { Veredicto } from '../components/EvolucionMensual'

function Tile({
  rotulo,
  valor,
  detalle,
  color,
}: {
  rotulo: string
  valor: string
  detalle?: string
  color?: string
}) {
  return (
    <Paper withBorder radius="md" p="md">
      <Text size="xs" fw={700} c="dimmed">
        {rotulo}
      </Text>
      <Text size="24px" fw={800} mt={4} lh={1.1} c={color}>
        {valor}
      </Text>
      {detalle && (
        <Text size="xs" c="dimmed" mt={4}>
          {detalle}
        </Text>
      )}
    </Paper>
  )
}

function TablaMezcla({
  titulo,
  items,
  corto,
}: {
  titulo: string
  items: Monto[]
  corto?: boolean
}) {
  const total = items.reduce((acc, m) => acc + Number(m.valor), 0)
  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5} mb="sm">
        {titulo}
      </Title>
      {items.length === 0 ? (
        <Text size="sm" c="dimmed">
          Todavía no hay negocios cerrados.
        </Text>
      ) : (
        <Table fz="xs">
          <Table.Tbody>
            {items.map((m) => (
              <Table.Tr key={m.etiqueta}>
                <Table.Td>
                  {corto
                    ? (MODELO_CORTO[m.etiqueta as keyof typeof MODELO_CORTO] ?? m.etiqueta)
                    : m.etiqueta}
                </Table.Td>
                <Table.Td ta="right" ff="monospace">
                  {clp(m.valor)}
                </Table.Td>
                <Table.Td ta="right" c="dimmed" w={60}>
                  {total > 0 ? `${Math.round((Number(m.valor) / total) * 100)}%` : '—'}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Paper>
  )
}

/**
 * El mismo desglose que `TablaMezcla` pero en unidades.
 *
 * Va aparte y no como un parámetro de la otra porque el porcentaje se calcula
 * distinto --sobre un total de conteos, no de montos-- y porque los desgloses de
 * canjes se recortan a los primeros: nueve comunas llenan media pantalla y la
 * cola larga no dice dónde está el volumen.
 */
function TablaConteo({ titulo, items }: { titulo: string; items: Conteo[] }) {
  const total = items.reduce((acc, x) => acc + x.cantidad, 0)
  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5} mb="sm">
        {titulo}
      </Title>
      {items.length === 0 ? (
        <Text size="sm" c="dimmed">
          Sin datos.
        </Text>
      ) : (
        <Table fz="xs">
          <Table.Tbody>
            {items.map((x) => (
              <Table.Tr key={x.etiqueta}>
                <Table.Td>{x.etiqueta}</Table.Td>
                <Table.Td ta="right" ff="monospace">
                  {x.cantidad}
                </Table.Td>
                <Table.Td ta="right" c="dimmed" w={60}>
                  {total > 0 ? `${Math.round((x.cantidad / total) * 100)}%` : '—'}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Paper>
  )
}


/**
 * La vista que se lleva a la reunión de directorio.
 *
 * **Está armada con supuestos, no con un requerimiento.** Se preguntó varias
 * veces qué quiere ver el directorio y no llegó la respuesta, así que esto es una
 * primera versión concreta para corregir. Los supuestos están en el docstring del
 * servicio, uno por uno, para poder discutirlos.
 *
 * **La proyección va como rango y con el `n` al lado.** Con 17 negocios resueltos
 * la tasa de conversión tiene un intervalo de casi 50 puntos; una cifra puntual
 * sería falsa precisión sobre una decisión de plata.
 *
 * **"Exportable" se resolvió con estilos de impresión** en vez de generando un
 * PDF. `Ctrl+P` da una hoja limpia: sin menú, sin botones, sin sombras. Un
 * generador de PDF sería una dependencia nueva para producir lo que el navegador
 * ya hace bien, y encima habría que mantener dos maquetaciones.
 */
export default function VistaDirectorio() {
  // Arranca en negocios: es donde está la plata, y una reunión de directorio se
  // abre por ahí. Canjes es volumen de gestión, no resultado.
  const [dominio, setDominio] = useState<Dominio>('negocios')
  const [ventana, setVentana] = useState('12')

  const consulta = useQuery({
    queryKey: ['vista-directorio', ventana],
    queryFn: () => obtenerVistaDirectorio(Number(ventana)),
  })
  const { data } = consulta

  if (!data) return <EstadoConsulta de={consulta} alto={240} />

  // Igual que en el reporte mensual: en la histórica la serie del gráfico arranca
  // donde arranca el dominio que se está mirando.
  const serie = serieDelDominio(data.serie, data.es_historico, data.inicio_por_dominio[dominio])

  const { conversion: c, proyeccion: p, ticket: t } = data
  const anioActual = Number(data.anio_corrido.comision_real_vp)
  const anioAnterior = Number(data.anio_corrido_anterior.comision_real_vp)
  const variacion =
    anioAnterior > 0 ? Math.round(((anioActual - anioAnterior) / anioAnterior) * 100) : null

  return (
    <Stack gap="lg" className="hoja-imprimible">
      <PageHeader
        title="Vista directorio"
        subtitle={
          dominio === 'negocios'
            ? `Al ${fecha(data.generado)}. Los montos son comisión real ViveProp, en pesos.`
            : `Al ${fecha(data.generado)}. Canjes se mide en volumen: el programa no tiene comisión propia cargada.`
        }
        action={
          <Button
            variant="light"
            leftSection={<IconPrinter size={16} />}
            onClick={() => window.print()}
            className="sin-imprimir"
          >
            Imprimir
          </Button>
        }
      />

      {/* Los dos selectores primero: uno elige qué reporte y el otro con qué
          horizonte. El de ventana solo alcanza lo temporal --la ventana móvil, la
          serie y la tendencia--; los buckets, la tasa de cierre, el ticket y la
          proyección siguen siendo históricos. */}
      <Group gap="lg" wrap="wrap" className="sin-imprimir">
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

      {dominio === 'negocios' ? (
        <>
      {/* Lo primero: cuánto entró. */}
      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        <Tile
          rotulo="AÑO CORRIDO"
          valor={clp(anioActual)}
          detalle={
            variacion === null
              ? 'sin base del año anterior para comparar'
              : `${variacion > 0 ? '+' : ''}${variacion}% contra el mismo tramo del año pasado`
          }
          color="good"
        />
        <Tile
          rotulo={data.es_historico ? 'HISTÓRICO COMPLETO' : `ÚLTIMOS ${data.ventana_meses} MESES`}
          valor={clp(data.ventana_movil.comision_real_vp)}
          detalle={`${data.ventana_movil.hitos_cerrados} liquidaciones cerradas`}
        />
        <Tile
          rotulo="EN PROCESO"
          valor={clp(data.pipeline.comision_real_vp)}
          detalle={`${data.pipeline.negocios} negocios abiertos`}
          color="brand"
        />
        <Tile
          rotulo="NO CONCRETADO"
          valor={clp(data.potencial_perdido.comision_real_vp)}
          detalle={`${data.potencial_perdido.negocios} negocios`}
          color="critical"
        />
      </SimpleGrid>

      {/* La evolución va después de los titulares y antes del detalle: responde
          "cómo vamos", que es lo que se pregunta en una reunión. */}
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
        subtitulo="La línea punteada es el promedio de la ventana; la recta, su tendencia."
        serie={serie}
        series={[{ campo: 'comision_real_vp', nombre: 'Comisión real VP', tono: 'principal' }]}
        promedio={Number(data.promedio.comision_real_vp)}
        tendencia={data.tendencias.comision_real_vp}
        esPlata
      />
      <PlataDeNegocios serie={serie} promedio={data.promedio} tendencias={data.tendencias} />
      <EvolucionMensual
        titulo="Liquidaciones y negocios por mes"
        subtitulo="Cuántos cerraron y cuántos entraron."
        serie={serie}
        series={[
          { campo: 'hitos_cerrados', nombre: 'Liquidaciones cerradas', tono: 'principal' },
          { campo: 'negocios_iniciados', nombre: 'Negocios iniciados', tono: 'secundaria' },
        ]}
        tendencia={data.tendencias.hitos_cerrados}
      />

      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <TablaMezcla titulo="De dónde vino, por modelo" items={data.por_modelo} corto />
        <TablaMezcla titulo="De dónde vino, por alianza" items={data.por_alianza} />
      </SimpleGrid>
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <Paper withBorder radius="md" p="md">
          <Title order={5}>Tasa de cierre</Title>
          <Group align="baseline" gap="xs" mt={4}>
            <Text size="24px" fw={800} lh={1.1}>
              {c.tasa_pct}%
            </Text>
            <Text size="sm" c="dimmed">
              de {c.n} negocios resueltos
            </Text>
          </Group>
          <Text size="xs" c="dimmed" mt={6}>
            {c.cerrados} cerrados, {c.perdidos} no concretados. Con esta cantidad de casos el
            margen real va de <strong>{c.intervalo_bajo_pct}%</strong> a{' '}
            <strong>{c.intervalo_alto_pct}%</strong>.
          </Text>
        </Paper>

        <Paper withBorder radius="md" p="md">
          <Title order={5}>Comisión por negocio cerrado</Title>
          {t === null ? (
            <Text size="sm" c="dimmed" mt={4}>
              Todavía no hay cierres.
            </Text>
          ) : (
            <>
              <Group align="baseline" gap="xs" mt={4}>
                <Text size="24px" fw={800} lh={1.1}>
                  {clp(t.mediano)}
                </Text>
                <Text size="sm" c="dimmed">
                  mediana de {t.n}
                </Text>
              </Group>
              <Text size="xs" c="dimmed" mt={6}>
                Va de {clp(t.minimo)} a {clp(t.maximo)}. Se usa la mediana y no el promedio
                porque con esa dispersión un solo negocio grande corre el promedio.
              </Text>
            </>
          )}
        </Paper>
      </SimpleGrid>
      <Paper withBorder radius="md" p="md">
        <Title order={5} mb={4}>
          Qué podría entrar del pipeline
        </Title>
        <SimpleGrid cols={{ base: 3 }} mt="sm">
          <div>
            <Text size="xs" c="dimmed" fw={700}>
              PESIMISTA
            </Text>
            <Text size="20px" fw={700}>
              {clp(p.pesimista)}
            </Text>
          </div>
          <div>
            <Text size="xs" c="dimmed" fw={700}>
              ESPERADO
            </Text>
            <Text size="20px" fw={800} c="brand">
              {clp(p.esperado)}
            </Text>
          </div>
          <div>
            <Text size="xs" c="dimmed" fw={700}>
              OPTIMISTA
            </Text>
            <Text size="20px" fw={700}>
              {clp(p.optimista)}
            </Text>
          </div>
        </SimpleGrid>

        <Text size="xs" c="dimmed" mt="md">
          Sobre un pipeline de {clp(p.pipeline)}. {p.nota.replace(/\*\*/g, '')}
        </Text>

        {p.sin_dato_de_plazo && (
          <Alert
            color="warning"
            variant="light"
            mt="sm"
            icon={<IconInfoCircle size={16} />}
            title="No hay con qué proyectar plazos"
          >
            <Text size="sm">
              Para decir <em>cuándo</em> va a entrar esta plata hacen falta dos datos que hoy
              no se están capturando: la duración real de los negocios y su paso por las
              etapas. Se resuelve registrando movimientos en el pipeline; en unos meses la
              proyección pasa de estimarse a calcularse.
            </Text>
          </Alert>
        )}
      </Paper>
        </>
      ) : (
        <>

      {/* Lo primero de canjes: cuánto volumen entró y cuánto sobrevive. */}
      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        <Tile
          rotulo="SOLICITADOS"
          valor={String(data.canjes.solicitados)}
          detalle={
            data.es_historico
              ? `en los ${data.ventana_meses} meses del histórico`
              : `en ${data.ventana_meses} meses · ${data.canjes.solicitados_historicos} en toda la historia`
          }
          color="brand"
        />
        <Tile
          rotulo="SIGUEN ACTIVOS"
          valor={String(data.canjes.activos)}
          detalle={`de los solicitados en la ventana · ${data.canjes.activos_historicos} activos en total`}
          color="good"
        />
        <Tile
          rotulo="CANCELADOS"
          valor={String(data.canjes.cancelados)}
          detalle="de los solicitados en la ventana"
          color="critical"
        />
        <Tile
          rotulo="TASA DE CIERRE"
          valor={`${data.canjes.tasa_cierre_pct}%`}
          detalle={`${data.canjes.cerrados_historicos} de ${data.canjes.resueltos_historicos} resueltos, en toda la historia`}
          color="accent"
        />
      </SimpleGrid>

      <Text size="xs" c="dimmed">
        La tasa de cierre va sobre los <strong>resueltos</strong> y sobre toda la historia,
        igual que en negocios: los que siguen abiertos no cuentan ni a favor ni en contra
        porque todavía no terminaron. Hoy da cero y es cierto — ningún canje se ha cerrado
        con éxito, y los que quedaron con la etapa en «Cerrado» están todos cancelados.
      </Text>

      <Paper withBorder radius="md" p="md">
        <Veredicto
          actual={serie[serie.length - 1]?.canjes_solicitados ?? 0}
          promedio={Number(data.promedio.canjes_solicitados)}
          unidad="solicitudes"
          tendencia={data.tendencias.canjes_solicitados}
        />
        <Text size="xs" c="dimmed" mt={6}>
          Canjes no tiene eje de plata. Sí genera comisión —la de administración de
          Dataprop, 6/5/4% en venta según el tramo en UF u 8% en arriendo— pero se calcula
          sobre la comisión de los corredores participantes, y ese dato está sin cargar en
          las {data.canjes.solicitados_historicos} filas.
        </Text>
      </Paper>

      <EvolucionMensual
        titulo="Solicitudes por mes, y qué pasó con ellas"
        subtitulo="El alto de la barra es lo que entró en el mes; los segmentos, en qué terminó."
        serie={serie}
        apilado
        etiquetaTotal="Solicitados"
        series={[
          /* El orden no es negociable por estetica: es el que valido la paleta.
             Ver `PALETA` en `EvolucionMensual`. */
          { campo: 'canjes_cerrados', nombre: 'Cerrados', tono: 'positiva' },
          { campo: 'canjes_activos', nombre: 'Siguen activos', tono: 'principal' },
          { campo: 'canjes_cancelados', nombre: 'Cancelados', tono: 'negativa' },
        ]}
        promedio={Number(data.promedio.canjes_solicitados)}
        tendencia={data.tendencias.canjes_solicitados}
      />
      <EvolucionMensual
        titulo="Canjes activos por mes"
        subtitulo="Los mismos activos, en su propia escala. Apilados son un segmento chico; acá se ve su forma."
        serie={serie}
        series={[{ campo: 'canjes_activos', nombre: 'Activos', tono: 'principal' }]}
        promedio={Number(data.promedio.canjes_activos)}
        tendencia={data.tendencias.canjes_activos}
      />

      {/* De dónde viene el volumen. Son los desgloses que canjes sí tiene con
          datos confiables: los tres son conteos, no montos. */}
      <SimpleGrid cols={{ base: 1, md: 3 }}>
        <TablaConteo titulo="Por operación" items={data.canjes.por_operacion} />
        <TablaConteo titulo="Por tipo de inmueble" items={data.canjes.por_tipo_inmueble} />
        <TablaConteo titulo="Por comuna" items={data.canjes.por_comuna} />
      </SimpleGrid>
      <Text size="xs" c="dimmed">
        Los desgloses van sobre toda la historia y muestran las categorías con más volumen,
        no el listado completo.
      </Text>
        </>
      )}

      <Alert color="brand" variant="light" className="sin-imprimir">
        <Text size="sm">
          <strong>Qué falta para cerrar esta vista.</strong> La estructura está definida
          --separada por dominio, con ventana móvil, evolución y tendencia--, pero dos cosas
          siguen sin poder calcularse: los <strong>plazos</strong> de negocios, que necesitan
          movimientos registrados en el pipeline, y la <strong>comisión de canjes</strong>,
          que necesita la comisión de los corredores participantes. Hasta entonces la
          proyección de plazos se declara imposible en vez de estimarse, y canjes va sin eje
          de plata.
        </Text>
      </Alert>
    </Stack>
  )
}
