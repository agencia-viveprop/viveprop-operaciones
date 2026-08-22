import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { IconInfoCircle, IconPrinter } from '@tabler/icons-react'
import { obtenerVistaDirectorio, type Monto } from '../api/reportes'
import PageHeader from '../components/PageHeader'
import { clp, fecha, MODELO_CORTO } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'

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
  const consulta = useQuery({
    queryKey: ['vista-directorio'],
    queryFn: obtenerVistaDirectorio,
  })
  const { data } = consulta

  if (!data) return <EstadoConsulta de={consulta} alto={240} />

  const { conversion: c, proyeccion: p, ticket: t } = data
  const anioActual = Number(data.anio_corrido.comision_real_vp)
  const anioAnterior = Number(data.anio_corrido_anterior.comision_real_vp)
  const variacion =
    anioAnterior > 0 ? Math.round(((anioActual - anioAnterior) / anioAnterior) * 100) : null

  return (
    <Stack gap="lg" className="hoja-imprimible">
      <PageHeader
        title="Vista directorio"
        subtitle={`Al ${fecha(data.generado)}. Los montos son comisión real ViveProp, en pesos.`}
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
          rotulo="ÚLTIMOS 12 MESES"
          valor={clp(data.ultimos_12_meses.comision_real_vp)}
          detalle={`${data.ultimos_12_meses.hitos_cerrados} liquidaciones cerradas`}
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

      <Text size="xs" c="dimmed">
        Los tres últimos son plata, pero no la misma plata: no se suman entre sí. El histórico
        acumulado de lo ganado es {clp(data.ganado.comision_real_vp)} en{' '}
        {data.ganado.negocios} negocios.
      </Text>

      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <TablaMezcla titulo="De dónde vino, por modelo" items={data.por_modelo} corto />
        <TablaMezcla titulo="De dónde vino, por alianza" items={data.por_alianza} />
      </SimpleGrid>

      {/* Estadísticas: cada una con su n. */}
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

      {/* La proyección, que es lo que más se puede leer mal. */}
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

      <Paper withBorder radius="md" p="md">
        <Group justify="space-between">
          <div>
            <Title order={5}>Canjes</Title>
            <Text size="xs" c="dimmed">
              El programa Dataprop, sin comisión propia en la app
            </Text>
          </div>
          <Group gap="lg">
            <div>
              <Text size="xs" c="dimmed" fw={700}>
                VIGENTES
              </Text>
              <Text size="20px" fw={800}>
                {data.canjes_vigentes}
              </Text>
            </div>
            <div>
              <Text size="xs" c="dimmed" fw={700}>
                HISTÓRICOS
              </Text>
              <Text size="20px" fw={700} c="dimmed">
                {data.canjes_historicos}
              </Text>
            </div>
          </Group>
        </Group>
      </Paper>

      <Alert color="brand" variant="light" className="sin-imprimir">
        <Text size="sm">
          <strong>Esta vista se armó con supuestos.</strong> Se preguntó qué quiere ver el
          directorio y no hubo respuesta, así que es una primera versión para corregir: qué
          entró, de dónde vino, qué hay por delante, qué se perdió y una proyección con su
          margen. Decime qué sacar y qué agregar.
        </Text>
      </Alert>
    </Stack>
  )
}
