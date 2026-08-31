import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Group,
  Paper,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from '@mantine/core'
import { IconArrowsExchange, IconBriefcase } from '@tabler/icons-react'
import { obtenerBandeja, type FilaBandeja, type NivelSemaforo } from '../api/canjes'
import BandejaNegocios from '../components/BandejaNegocios'
import PageHeader from '../components/PageHeader'
import SeguimientoModal from '../components/SeguimientoModal'
import { fecha } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'
import { rotuloEtapa } from '../components/canjesEtiquetas'

/**
 * El nivel se muestra siempre con su palabra, nunca con el color solo. En este
 * proyecto eso además está anotado en `theme.ts`: el coral de acento y el rojo
 * crítico se parecen entre sí, así que el color por sí mismo no distingue.
 */
const NIVELES: Record<NivelSemaforo, { texto: string; color: string }> = {
  vencido: { texto: 'Vencido', color: 'critical' },
  para_hoy: { texto: 'Para hoy', color: 'accent' },
  sin_gestion: { texto: 'Sin gestión', color: 'gray' },
  critico: { texto: 'Crítico', color: 'critical' },
  advertencia: { texto: 'Advertencia', color: 'warning' },
  al_dia: { texto: 'Al día', color: 'good' },
}

/**
 * La explicación de cada nivel, armada con los umbrales que manda la API.
 *
 * Los números venían escritos a mano mientras el backend los decide en
 * `UMBRAL_CRITICO` y `UMBRAL_ADVERTENCIA` --que salen de la hoja `CONFIG`-- y ya
 * los devolvía en la respuesta. Dos copias del mismo umbral: el día que se
 * ajuste uno, la pantalla seguiría explicando el viejo y nada fallaría.
 *
 * **Crítico y Advertencia dicen «y sin seguimiento agendado», y esa mitad no se
 * puede sacar.** El reloj clasifica solo a los canjes que no tienen un
 * compromiso registrado: el compromiso es un hecho y el reloj una inferencia, y
 * cuando los dos opinan gana el hecho (`bandeja_canjes.py`). Sin esa mitad de la
 * frase el recuadro se contradice con la tabla que tiene debajo --el usuario lo
 * leyó así: «Crítico 0» arriba y «Espera 4 días» en cinco filas, cuando el
 * umbral son 48 horas-- porque esos canjes están contados en «Vencido»
 * (`D-093`).
 */
function ayudaDe(nivel: NivelSemaforo, critico: number, advertencia: number): string {
  switch (nivel) {
    case 'vencido':
      return 'El seguimiento agendado ya pasó'
    case 'para_hoy':
      return 'El seguimiento agendado es hoy'
    case 'sin_gestion':
      return 'Nunca se registró un movimiento en la app'
    case 'critico':
      return `Más de ${critico} horas sin gestión y sin seguimiento agendado`
    case 'advertencia':
      return `Entre ${advertencia} y ${critico} horas, sin seguimiento agendado`
    case 'al_dia':
      return `Menos de ${advertencia} horas`
  }
}

// El orden de lectura: primero lo que alguien se comprometió a hacer, después lo
// que el semáforo infiere por tiempo sin gestión. Un compromiso registrado vale
// más que una inferencia.
const ORDEN: NivelSemaforo[] = [
  'vencido',
  'para_hoy',
  'sin_gestion',
  'critico',
  'advertencia',
  'al_dia',
]

/** Una fecha suelta --sin hora-- en formato chileno.
 *
 *  El mediodía en el `Date` es deliberado: `new Date('2026-08-27')` se parsea como
 *  medianoche **UTC**, que en Chile es el 26 a las 20:00, así que la fecha se
 *  mostraría un día antes. Al mediodía ningún huso la corre de día. */
function fechaSola(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString('es-CL')
}

/** El atraso en palabras. */
function atraso(dias: number | null): string {
  if (dias === null) return ''
  if (dias === 0) return 'es hoy'
  if (dias === 1) return 'venció ayer'
  return `venció hace ${dias} días`
}

function espera(f: FilaBandeja): string {
  if (f.horas_sin_gestion === null) return '—'
  const h = f.horas_sin_gestion
  if (h < 48) return `${Math.round(h)} h`
  return `${Math.floor(h / 24)} días`
}

/**
 * "Qué me toca hoy", para los dos dominios.
 *
 * Van con selector y no apilados, igual que los dashboards de Inicio: son dos
 * tipos de gestión con relojes distintos --canjes se mide en horas, negocios en
 * meses-- y juntarlos invitaría a compararlos.
 */
export default function Bandeja({ puedeEditar }: { puedeEditar: boolean }) {
  const [vista, setVista] = useState('canjes')
  const [filtro, setFiltro] = useState<string>('atencion')
  const [seguimientoId, setSeguimientoId] = useState<number | null>(null)

  const consulta = useQuery({
    queryKey: ['bandeja'],
    queryFn: obtenerBandeja,
    enabled: vista === 'canjes',
  })
  const { data } = consulta

  const selector = (
    <SegmentedControl
      color="accent"
      value={vista}
      onChange={setVista}
      data={[
        {
          value: 'canjes',
          label: (
            <Group gap={6} wrap="nowrap">
              <IconArrowsExchange size={15} />
              Canjes
            </Group>
          ),
        },
        {
          value: 'negocios',
          label: (
            <Group gap={6} wrap="nowrap">
              <IconBriefcase size={15} />
              Negocios
            </Group>
          ),
        },
      ]}
    />
  )

  if (vista === 'negocios') {
    return (
      <Stack gap="md">
        <PageHeader
          title="Qué me toca hoy"
          subtitle="Negocios con liquidaciones abiertas, ordenados por cuánto llevan sin moverse."
          action={selector}
        />
        <BandejaNegocios puedeEditar={puedeEditar} />
      </Stack>
    )
  }

  if (!data) return <EstadoConsulta de={consulta} alto={240} />

  const { resumen, filas } = data
  // Todo lo que no está al día ni agendado para después. Incluye los dos niveles
  // de compromiso: la primera versión de este cálculo se quedó con los tres del
  // semáforo, así que el chip decía "Requieren atención (2)" y la tabla mostraba
  // seis filas. Un contador que no cuadra con su propia lista no se vuelve a creer.
  const requierenAtencion =
    resumen.vencido +
    resumen.para_hoy +
    resumen.sin_gestion +
    resumen.critico +
    resumen.advertencia

  // Los abiertos son los listados más los agendados: los agendados están abiertos,
  // solo que su día no es hoy.
  const abiertos = filas.length + resumen.agendados

  // «Al día» son los dos: los que tienen fecha comprometida y los que se tocaron
  // dentro del plazo. Ninguno de los dos requiere atención hoy.
  const alDia = resumen.al_dia + resumen.agendados

  /**
   * El pie de «Al día», que **solo nombra las poblaciones que existen**.
   *
   * Antes decía "0 gestionados hace menos de 24 h" cuando los cinco eran
   * agendados, y eso se leía como desatención siendo que la realidad era la
   * opuesta. Un pie que enumera lo que no hay se lee como un reproche; el mismo
   * pie enumerando lo que hay se lee como información.
   *
   * Dice "dentro del plazo" y no "hace menos de 24 h" porque el umbral lo manda
   * la API: escribirlo a mano en dos lugares es como se despegan.
   */
  const desgloseAlDia = [
    resumen.agendados > 0 && `${resumen.agendados} con seguimiento agendado`,
    resumen.al_dia > 0 && `${resumen.al_dia} gestionados dentro del plazo`,
  ]
    .filter(Boolean)
    .join(' · ')

  const visibles =
    filtro === 'todos'
      ? filas
      : filtro === 'atencion'
        ? filas.filter((f) => f.nivel !== 'al_dia')
        : filas.filter((f) => f.nivel === filtro)

  const filaSeguida = filas.find((f) => f.canje_id === seguimientoId)

  return (
    <Stack gap="md">
      <PageHeader
        title="Qué me toca hoy"
        subtitle={
          `${requierenAtencion} de ${abiertos} canjes abiertos requieren atención. ` +
          'Manda el seguimiento agendado; donde no hay ninguno, el reloj de horas sin ' +
          `gestión: ${data.umbral_critico_horas} horas es crítico, ${data.umbral_advertencia_horas} es advertencia.`
        }
        action={selector}
      />

      {/* **«Al día» incluye los agendados, y los seis recuadros reparten el
          universo.**

          Primero los agendados no tenían recuadro --el argumento era que no
          requieren atención-- y quedaban en una línea de texto: con siete canjes
          abiertos y cinco agendados, los recuadros sumaban dos y no había forma de
          ver dónde estaban los otros cinco. Después tuvieron el suyo, y ahí «Al
          día» mostraba cero al lado de un «Agendados» en cinco, que se leía como
          que no había nada vivo.

          Los dos están **al día** en el único sentido que importa acá: no
          requieren atención hoy. Uno porque se comprometió una fecha y el otro
          porque se tocó recién. Van juntos en el número y separados en el pie.

          La regla vale siempre, no solo cuando no hay incidentes: si el número
          cambiara de significado según el contexto, dejaría de ser comparable con
          el de ayer. */}
      <SimpleGrid cols={{ base: 2, sm: 3, lg: 6 }}>
        {ORDEN.map((nivel) => (
          <Paper key={nivel} withBorder radius="md" p="md" className="caja-cifra">
            <Group gap="xs" mb={4}>
              <Badge color={NIVELES[nivel].color} variant="light">
                {NIVELES[nivel].texto}
              </Badge>
            </Group>
            <Text className="cifra" fw={800} lh={1.1}>
              {nivel === 'al_dia' ? alDia : resumen[nivel]}
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              {nivel === 'al_dia' && alDia > 0
                ? desgloseAlDia
                : ayudaDe(nivel, data.umbral_critico_horas, data.umbral_advertencia_horas)}
            </Text>
          </Paper>
        ))}
      </SimpleGrid>

      {/* En un telefono las cuatro etiquetas piden mas de 400 px y la ultima
          quedaba fuera de la pantalla, sin forma de tocarla. */}
      <div className="fila-scroll-x">
      <SegmentedControl
        value={filtro}
        onChange={setFiltro}
        data={[
          { value: 'atencion', label: `Requieren atención (${requierenAtencion})` },
          { value: 'vencido', label: `Vencidos (${resumen.vencido})` },
          { value: 'para_hoy', label: `Para hoy (${resumen.para_hoy})` },
          { value: 'sin_gestion', label: `Sin gestión (${resumen.sin_gestion})` },
          // "Todos" son los que se listan, que no son todos los abiertos: los
          // agendados para más adelante quedan fuera a propósito.
          { value: 'todos', label: `Todos los de hoy (${filas.length})` },
        ]}
      />
      </div>

      {/* El vacio tiene dos causas distintas y decia solo una: con todos los
          canjes abiertos agendados, la tabla queda sin filas y "nada pendiente"
          se lee como "no hay canjes abiertos". */}
      {visibles.length === 0 ? (
        <Paper withBorder radius="md" p="xl">
          <Text ta="center" c="dimmed">
            {filas.length === 0 && resumen.agendados > 0
              ? resumen.agendados === 1
                ? 'El único canje abierto tiene su seguimiento agendado para más adelante, así que hoy no toca.'
                : `Los ${resumen.agendados} canjes abiertos tienen su seguimiento agendado para más adelante, así que hoy no toca ninguno.`
              : abiertos === 0
                ? 'No hay canjes abiertos.'
                : `Nada pendiente acá.${filtro === 'atencion' ? ' Todos los canjes listados están al día.' : ''}`}
          </Text>
        </Paper>
      ) : (
        <Table.ScrollContainer minWidth={860}>
          <Table striped withTableBorder highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Estado</Table.Th>
                <Table.Th>Canje</Table.Th>
                <Table.Th>Corredores</Table.Th>
                <Table.Th>Propiedad</Table.Th>
                <Table.Th>Etapa</Table.Th>
                <Table.Th ta="right">Espera</Table.Th>
                <Table.Th>Última gestión</Table.Th>
                <Table.Th>Seguimiento</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {visibles.map((f) => (
                <Table.Tr
                  key={f.canje_id}
                  onClick={() => setSeguimientoId(f.canje_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <Table.Td>
                    <Badge color={NIVELES[f.nivel].color} variant="light">
                      {NIVELES[f.nivel].texto}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" fw={600}>
                      #{f.canje_id}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {fecha(f.fecha_solicitud)}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{f.corredor_solicitante_nombre ?? '—'}</Text>
                    <Text size="xs" c="dimmed">
                      {f.corredor_propietario_nombre ?? '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{f.direccion ?? '—'}</Text>
                    <Text size="xs" c="dimmed">
                      {f.comuna ?? '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{rotuloEtapa(f.etapa)}</Text>
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace">
                    {espera(f)}
                  </Table.Td>
                  <Table.Td>
                    {f.ultimo_movimiento_nombre ? (
                      <>
                        <Text size="sm">{f.ultimo_movimiento_nombre}</Text>
                        <Text size="xs" c="dimmed">
                          {fecha(f.ultimo_movimiento)}
                        </Text>
                      </>
                    ) : (
                      <Text size="sm" c="dimmed">
                        Nunca
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td>
                    {f.proximo_seguimiento === null ? (
                      <Text size="sm" c="dimmed">
                        Sin agendar
                      </Text>
                    ) : (
                      <>
                        <Text size="sm">{fechaSola(f.proximo_seguimiento)}</Text>
                        {/* El atraso en palabras, no solo la fecha: "era el 21-08"
                            obliga a restar de cabeza para saber si es de ayer o de
                            la semana pasada. */}
                        <Text
                          size="xs"
                          c={(f.dias_de_atraso ?? 0) > 0 ? 'critical.7' : 'dimmed'}
                        >
                          {atraso(f.dias_de_atraso)}
                        </Text>
                      </>
                    )}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}

      <Text size="xs" c="dimmed">
        Hacer clic en una fila abre el seguimiento del canje. Registrar un movimiento agenda
        el próximo --dos días hacia adelante si no se indica otro, corridos al lunes si caen
        fin de semana-- y saca el canje de esta lista hasta ese día. Los feriados todavía no
        se saltan.
      </Text>

      <SeguimientoModal
        canjeId={seguimientoId}
        opened={seguimientoId !== null}
        onClose={() => setSeguimientoId(null)}
        puedeEditar={puedeEditar}
        etapaActual={filaSeguida?.etapa}
        solicitante={filaSeguida?.corredor_solicitante_nombre}
        propietario={filaSeguida?.corredor_propietario_nombre}
      />
    </Stack>
  )
}
