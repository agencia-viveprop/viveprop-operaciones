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
import {
  IconArrowsExchange,
  IconBriefcase,
  IconChevronLeft,
  IconChevronRight,
} from '@tabler/icons-react'
import {
  aISO,
  lunesDe,
  obtenerReporteSemanal,
  type ItemMovido,
  type Seccion,
  type Ubicacion,
} from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp, fecha } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'

/** Cuál de los dos dominios. Cambia una columna y el sustantivo de las ayudas. */
type Dominio = 'negocios' | 'canjes'

const plural = (n: number, uno: string, muchos: string) => (n === 1 ? uno : muchos)

/** "a", "a y b", "a, b y c". */
function enumerar(partes: string[]): string {
  if (partes.length <= 1) return partes.join('')
  return `${partes.slice(0, -1).join(', ')} y ${partes[partes.length - 1]}`
}

/** Cómo se llama cada casilla, para poder nombrarla en el vacío. */
const ROTULOS: Record<string, string> = {
  cerrados: 'Se cerró',
  avanzados: 'Avanzó',
  caidos: 'Se cayó',
  estancados: 'Estancado',
}

/** "17 al 23 de agosto de 2026", o con los dos meses si la ventana los cruza. */
function rotulo(desde: string, hasta: string): string {
  const d = new Date(`${desde}T12:00:00`)
  const h = new Date(`${hasta}T12:00:00`)
  const mes = (f: Date) => f.toLocaleDateString('es-CL', { month: 'long' })
  const cola = `de ${mes(h)} de ${h.getFullYear()}`
  return d.getMonth() === h.getMonth()
    ? `${d.getDate()} al ${h.getDate()} ${cola}`
    : `${d.getDate()} de ${mes(d)} al ${h.getDate()} ${cola}`
}

/**
 * Texto largo en una celda: una línea, con el completo en el tooltip.
 *
 * Las tablas son de una línea por fila a propósito --se leen de un barrido-- así
 * que un comentario de doscientos caracteres no puede decidir el ancho de todas
 * las columnas. Al agregar dirección, comuna y alianza el problema se volvió
 * visible: la tabla de negocios ya salía con desplazamiento horizontal y lo que
 * se lo comía era el comentario.
 *
 * Se recorta con CSS y no cortando el string, para que el texto siga completo
 * para copiar y el tooltip tenga qué mostrar.
 */
function Recortado({ texto, ancho }: { texto: string | null; ancho: number }) {
  if (!texto) return <>—</>
  return (
    <Tooltip label={texto} multiline w={420} withArrow openDelay={400}>
      <Text size="xs" truncate="end" style={{ maxWidth: ancho }}>
        {texto}
      </Text>
    </Tooltip>
  )
}

/** Las columnas que dicen de qué propiedad se habla.
 *
 * Van en las cuatro listas de la sección. La referencia sola --«VVP-15», «#344»--
 * no le dice nada a quien lee el reporte sin abrir otra pantalla, y el reporte se
 * lee justamente para decidir a quién llamar hoy. */
function CabecerasUbicacion({ dominio }: { dominio: Dominio }) {
  return (
    <>
      {dominio === 'canjes' && <Table.Th>Operación</Table.Th>}
      <Table.Th>Dirección</Table.Th>
      <Table.Th>Comuna</Table.Th>
      {dominio === 'negocios' && <Table.Th>Alianza</Table.Th>}
    </>
  )
}

function CeldasUbicacion({ item, dominio }: { item: Ubicacion; dominio: Dominio }) {
  return (
    <>
      {dominio === 'canjes' && <Table.Td>{item.operacion ?? '—'}</Table.Td>}
      <Table.Td>
        <Recortado texto={item.direccion} ancho={260} />
      </Table.Td>
      <Table.Td>{item.comuna ?? '—'}</Table.Td>
      {dominio === 'negocios' && <Table.Td>{item.alianza ?? '—'}</Table.Td>}
    </>
  )
}

/** El texto de la etapa, no su código.
 *
 * En negocios el código se conserva como prefijo --`E4 · Coordinación`-- porque
 * es el vocabulario con el que se habla del pipeline. En canjes no: `EN_NEGOCIO`
 * es un valor de base de datos y no le sirve a nadie.
 *
 * Lo usan las dos tablas que muestran etapa: escribirla distinto en cada una
 * obligaría a traducir entre dos casillas de la misma sección. */
function textoEtapa(
  item: { etapa: string | null; etapa_nombre: string | null },
  dominio: Dominio,
): string | null {
  if (!item.etapa_nombre) return null
  return dominio === 'negocios' ? `${item.etapa} · ${item.etapa_nombre}` : item.etapa_nombre
}

/** «Quedó en».
 *
 * Cuando el último movimiento no movió la etapa se dice «sigue en», que es una
 * respuesta a "en qué quedó" y no una celda muda. */
function Etapa({ item, dominio }: { item: ItemMovido; dominio: Dominio }) {
  const texto = textoEtapa(item, dominio)
  if (!texto) return <>—</>
  return item.movio_etapa ? (
    <Text size="xs">{texto}</Text>
  ) : (
    <Text size="xs" c="dimmed">
      sigue en {texto}
    </Text>
  )
}

function TablaCerrados({
  seccion,
  conMonto,
  dominio,
}: {
  seccion: Seccion
  conMonto: boolean
  dominio: Dominio
}) {
  return (
    <Table striped withTableBorder fz="xs" className="tabla-una-linea">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Referencia</Table.Th>
          <CabecerasUbicacion dominio={dominio} />
          <Table.Th>{dominio === 'negocios' ? 'Hito' : 'Corredor'}</Table.Th>
          <Table.Th>Fecha de cierre</Table.Th>
          {conMonto && <Table.Th ta="right">Comisión real VP</Table.Th>}
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {seccion.cerrados.map((c, i) => (
          <Table.Tr key={`${c.referencia}-${i}`}>
            <Table.Td fw={600}>{c.referencia}</Table.Td>
            <CeldasUbicacion item={c} dominio={dominio} />
            <Table.Td>{c.detalle ?? '—'}</Table.Td>
            <Table.Td>{fecha(c.fecha)}</Table.Td>
            {conMonto && (
              <Table.Td ta="right" ff="monospace">
                {clp(c.monto)}
              </Table.Td>
            )}
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

/**
 * La última actualización de cada negocio o canje, un renglón por cada uno.
 *
 * Antes era un renglón por movimiento, y con eso VVP-15 aparecía tres veces y
 * había que leer las tres para saber en qué quedó. La columna «Registros» es la
 * que evita que el resumen mienta: dice cuántos movimientos hay detrás del
 * renglón que se está mostrando.
 */
function TablaMovidos({
  items,
  columnaEtapa,
  dominio,
}: {
  items: Seccion['avanzados']
  columnaEtapa: boolean
  dominio: Dominio
}) {
  return (
    <Table striped withTableBorder fz="xs" className="tabla-una-linea">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Referencia</Table.Th>
          <CabecerasUbicacion dominio={dominio} />
          <Table.Th>Última actualización</Table.Th>
          <Table.Th ta="right">Registros</Table.Th>
          <Table.Th>Qué pasó</Table.Th>
          {columnaEtapa && <Table.Th>Quedó en</Table.Th>}
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {items.map((m, i) => (
          <Table.Tr key={`${m.referencia}-${i}`}>
            <Table.Td fw={600}>{m.referencia}</Table.Td>
            <CeldasUbicacion item={m} dominio={dominio} />
            <Table.Td>{fecha(m.fecha)}</Table.Td>
            <Table.Td ta="right" ff="monospace">
              {m.registros}
            </Table.Td>
            <Table.Td>
              <Recortado texto={m.comentario} ancho={340} />
            </Table.Td>
            {columnaEtapa && (
              <Table.Td>
                <Etapa item={m} dominio={dominio} />
              </Table.Td>
            )}
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

function TablaEstancados({ seccion, dominio }: { seccion: Seccion; dominio: Dominio }) {
  return (
    <Table striped withTableBorder fz="xs" className="tabla-una-linea">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Referencia</Table.Th>
          <CabecerasUbicacion dominio={dominio} />
          <Table.Th ta="right">Sin moverse</Table.Th>
          <Table.Th>Etapa</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {seccion.estancados.map((e, i) => (
          <Table.Tr key={`${e.referencia}-${i}`}>
            <Table.Td fw={600}>{e.referencia}</Table.Td>
            <CeldasUbicacion item={e} dominio={dominio} />
            <Table.Td ta="right">
              <Text size="xs" ff="monospace" component="span">
                {e.dias_sin_movimiento ?? '—'} días
              </Text>
              {/* Que nunca se le haya registrado nada no es lo mismo que llevar
                  ese tiempo sin gestión: en el primer caso la cuenta corre desde
                  la fecha de origen y el dato es más débil. */}
              {e.sin_gestion && (
                <Text size="xs" c="dimmed">
                  sin gestión registrada
                </Text>
              )}
            </Table.Td>
            <Table.Td>{textoEtapa(e, dominio) ?? "—"}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

function Tile({
  rotulo: texto,
  valor,
  ayuda,
  color,
  activo,
  onClick,
}: {
  rotulo: string
  valor: string
  ayuda: string
  color: string
  activo: boolean
  onClick: () => void
}) {
  return (
    <Paper
      withBorder
      radius="md"
      p="md"
      onClick={onClick}
      style={{ cursor: 'pointer', borderColor: activo ? `var(--mantine-color-${color}-6)` : undefined }}
    >
      <Badge color={color} variant="light" mb={6}>
        {texto}
      </Badge>
      <Text size="26px" fw={800} lh={1.1}>
        {valor}
      </Text>
      <Text size="xs" c="dimmed" mt={4}>
        {ayuda}
      </Text>
    </Paper>
  )
}

function SeccionDominio({
  nombre,
  icono,
  seccion,
  conMonto,
  dominio,
  diasEstancado,
}: {
  nombre: string
  icono: React.ReactNode
  seccion: Seccion
  conMonto: boolean
  dominio: Dominio
  diasEstancado: number
}) {
  const [bucket, setBucket] = useState('avanzados')
  const uno = dominio === 'negocios' ? 'negocio' : 'canje'
  const varios = dominio === 'negocios' ? 'negocios' : 'canjes'

  const listas: Record<string, { largo: number; total: number; nodo: React.ReactNode }> = {
    cerrados: {
      largo: seccion.cerrados.length,
      total: seccion.total_cerrados,
      nodo: <TablaCerrados seccion={seccion} conMonto={conMonto} dominio={dominio} />,
    },
    avanzados: {
      largo: seccion.avanzados.length,
      total: seccion.total_avanzados,
      nodo: <TablaMovidos items={seccion.avanzados} columnaEtapa dominio={dominio} />,
    },
    caidos: {
      largo: seccion.caidos.length,
      total: seccion.total_caidos,
      nodo: <TablaMovidos items={seccion.caidos} columnaEtapa={false} dominio={dominio} />,
    },
    estancados: {
      largo: seccion.estancados.length,
      total: seccion.total_estancados,
      nodo: <TablaEstancados seccion={seccion} dominio={dominio} />,
    },
  }
  const elegido = listas[bucket]
  // Las otras casillas que sí tienen algo, para que el vacío no se lea como que
  // no hay nada en la sección.
  const conFilas = Object.entries(listas)
    .filter(([clave, lista]) => clave !== bucket && lista.total > 0)
    .map(([clave, lista]) => `${ROTULOS[clave]} (${lista.total})`)

  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="md">
        <Group gap="xs">
          {icono}
          <Title order={4}>{nombre}</Title>
        </Group>

        <SimpleGrid cols={{ base: 2, sm: 4 }}>
          <Tile
            rotulo="Se cerró"
            valor={conMonto ? clp(seccion.monto_cerrado) : String(seccion.total_cerrados)}
            ayuda={
              conMonto
                ? `${seccion.total_cerrados} ${plural(seccion.total_cerrados, 'hito', 'hitos')} en comisión real VP`
                : `${varios} cerrados en la ventana`
            }
            color="good"
            activo={bucket === 'cerrados'}
            onClick={() => setBucket('cerrados')}
          />
          {/* La cifra cuenta entidades y la ayuda dice los movimientos que hay
              detrás. Contaba movimientos, y como la lista ahora trae un renglón
              por entidad, la cifra y la lista no cuadraban. */}
          <Tile
            rotulo="Avanzó"
            valor={String(seccion.total_avanzados)}
            ayuda={
              seccion.total_avanzados === 0
                ? 'sin registros en la ventana'
                : `${varios} con actividad · ${seccion.movimientos_avanzados} ${plural(
                    seccion.movimientos_avanzados,
                    'registro',
                    'registros',
                  )}`
            }
            color="info"
            activo={bucket === 'avanzados'}
            onClick={() => setBucket('avanzados')}
          />
          <Tile
            rotulo="Se cayó"
            valor={String(seccion.total_caidos)}
            ayuda={conMonto ? 'pérdidas y desistimientos' : 'cancelaciones'}
            color="critical"
            activo={bucket === 'caidos'}
            onClick={() => setBucket('caidos')}
          />
          {/* El umbral lo manda la API y sale del largo de la ventana: escribirlo
              a mano en la pantalla es como se despega del que aplica de verdad. */}
          <Tile
            rotulo="Estancado"
            valor={String(seccion.total_estancados)}
            ayuda={`abierto y sin moverse en los ${diasEstancado} días de la ventana`}
            color="warning"
            activo={bucket === 'estancados'}
            onClick={() => setBucket('estancados')}
          />
        </SimpleGrid>

        {elegido.largo === 0 ? (
          // **El vacío nombra la casilla y dice dónde sí hay algo.** Decía "nada
          // que mostrar acá" debajo de una fila de recuadros donde uno podía
          // marcar 2: la frase era cierta --de la casilla elegida-- y la pantalla
          // se leía como que la sección estaba vacía. Es el mismo malentendido
          // que se arregló en la bandeja (`D-073`, `D-074`).
          <Text size="sm" c="dimmed" ta="center" py="lg">
            Nada en «{ROTULOS[bucket]}» en esta ventana.
            {conFilas.length > 0 && ` Sí hay en ${enumerar(conFilas)}.`}
          </Text>
        ) : (
          <Stack gap={4}>
            <div className="tabla-scroll-x">{elegido.nodo}</div>
            {elegido.total > elegido.largo && (
              // Sin esto la lista topeada se leería como el total.
              <Text size="xs" c="dimmed">
                Se muestran {elegido.largo} de {elegido.total} {plural(elegido.total, uno, varios)}.
              </Text>
            )}
          </Stack>
        )}
      </Stack>
    </Paper>
  )
}

/** Las ventanas que se pueden elegir, en semanas calendario.
 *
 * Semanas y no "7/14/30 días" porque un número tiene que significar lo mismo el
 * martes y el viernes: con ventana móvil, "se cayeron 3" cambia todos los días
 * para el mismo hecho y las flechas dejan de comparar períodos con nombre.
 * También deja un vocabulario común con el reporte mensual, que ya trabaja con
 * ventana móvil de meses calendario. */
const LARGOS = [
  { value: '1', label: '1 semana' },
  { value: '2', label: '2 semanas' },
  { value: '4', label: '4 semanas' },
]

/**
 * El reporte del período: qué se cerró, qué avanzó, qué se cayó y qué está
 * estancado, en los dos dominios.
 *
 * Es lo contrario del dashboard. El dashboard responde "cómo vamos" y mira el
 * estado actual; esto responde "qué pasó" y mira los movimientos del período.
 * Por eso no repite las cifras de cartera: sumar lo mismo dos veces con dos
 * cortes distintos es la forma más rápida de que nadie confíe en ninguna.
 *
 * **Un solo control de ventana para las cuatro cifras.** Antes había dos --el
 * navegador fijaba la semana y el 7/14/30 tocaba solo «Estancado»--, así que un
 * control visible movía una de cuatro casillas y se leía como si moviera las
 * cuatro. Ahora la ventana manda en todo y el umbral de estancado es su largo,
 * con lo que «Avanzó» y «Estancado» reparten la cartera abierta en vez de contar
 * dos cosas incomparables.
 */
export default function ReporteSemanal() {
  const [ventanas, setVentanas] = useState(0)
  const [largo, setLargo] = useState('1')
  const semanas = Number(largo)

  // El domingo de la ventana es el de esta semana corrido `ventanas` ventanas
  // completas, así que dos ventanas consecutivas no se pisan ni dejan hueco.
  const domingo = lunesDe(new Date(), ventanas * semanas)
  domingo.setDate(domingo.getDate() + 6)
  const lunes = new Date(domingo)
  lunes.setDate(lunes.getDate() - (semanas * 7 - 1))
  const desde = aISO(lunes)
  const hasta = aISO(domingo)

  const consulta = useQuery({
    queryKey: ['reporte-semanal', desde, hasta],
    // Sin `dias_estancado`: lo deriva el backend del largo de la ventana, y así
    // no hay dos lugares que puedan discrepar sobre cuál es el umbral.
    queryFn: () => obtenerReporteSemanal({ desde, hasta }),
  })
  const { data } = consulta

  return (
    <Stack gap="md">
      <PageHeader
        title="Reporte semanal"
        subtitle="Qué pasó en la ventana, en negocios y en canjes. El dashboard dice cómo vamos; esto dice qué cambió."
        action={
          <Group gap="xs">
            <Tooltip label="Ventana anterior">
              <ActionIcon variant="default" onClick={() => setVentanas((v) => v - 1)} aria-label="Ventana anterior">
                <IconChevronLeft size={16} />
              </ActionIcon>
            </Tooltip>
            <Text size="sm" fw={600} w={260} ta="center">
              {rotulo(desde, hasta)}
            </Text>
            <Tooltip label={ventanas >= 0 ? 'Todavía no empieza' : 'Ventana siguiente'}>
              <ActionIcon
                variant="default"
                disabled={ventanas >= 0}
                onClick={() => setVentanas((v) => v + 1)}
                aria-label="Ventana siguiente"
              >
                <IconChevronRight size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        }
      />

      <Group gap="xs">
        <Text size="xs" c="dimmed">
          Ventana móvil de
        </Text>
        <SegmentedControl size="xs" value={largo} onChange={setLargo} data={LARGOS} />
        <Text size="xs" c="dimmed">
          Las cuatro cifras y las listas hablan de esta ventana, y estancado es lo que no se movió en
          ella.
        </Text>
      </Group>

      {!data ? (
        <EstadoConsulta de={consulta} alto={240} />
      ) : (
        <Stack gap="lg">
          <SeccionDominio
            nombre="Negocios"
            icono={<IconBriefcase size={20} />}
            seccion={data.negocios}
            conMonto
            dominio="negocios"
            diasEstancado={data.dias_estancado}
          />
          <SeccionDominio
            nombre="Canjes"
            icono={<IconArrowsExchange size={20} />}
            seccion={data.canjes}
            conMonto={false}
            dominio="canjes"
            diasEstancado={data.dias_estancado}
          />
        </Stack>
      )}
    </Stack>
  )
}
