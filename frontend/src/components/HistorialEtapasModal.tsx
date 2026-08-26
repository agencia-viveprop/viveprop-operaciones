import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  FileButton,
  Group,
  List,
  Modal,
  Stack,
  Text,
} from '@mantine/core'
import { IconDownload, IconUpload } from '@tabler/icons-react'
import { obtenerEstructuraHistorial } from '../api/estructura'
import {
  descargarPlantillaHistorial,
  importarHistorial,
  type ResumenHistorial,
} from '../api/negocios'
import EstructuraArchivo from './EstructuraArchivo'

/**
 * Carga del historial de etapas de negocios.
 *
 * **Por qué es una carga aparte de la de negocios.** Esa crea negocios y
 * liquidaciones desde cero; esta escribe la historia de los que ya existen. Los
 * resúmenes tampoco se parecen: uno cuenta negocios y hitos, este cuenta
 * movimientos y trae tres listas que no son todas errores.
 *
 * **Para qué sirve.** La vista directorio declara imposible proyectar plazos, y
 * tiene razón: no hay un solo movimiento de negocio registrado y las liquidaciones
 * cerradas del histórico traen la misma fecha de inicio y de cierre. Esperar a que
 * se acumule esa historia son meses; cargarla hacia atrás es una tarde.
 */

/** Cuántas líneas se listan antes de resumir. Con 71 filas mal llenadas salen
 *  decenas, y una lista de decenas no se lee. */
const TOPE = 12

function Lista({
  titulo,
  items,
  color,
  ayuda,
}: {
  titulo: string
  items: string[]
  color: string
  ayuda: string
}) {
  if (items.length === 0) return null
  return (
    <Alert color={color} variant="light" title={`${items.length} ${titulo}`}>
      <Text size="xs" c="dimmed" mb={6}>
        {ayuda}
      </Text>
      <List size="xs" spacing={2}>
        {items.slice(0, TOPE).map((x) => (
          <List.Item key={x}>{x}</List.Item>
        ))}
      </List>
      {items.length > TOPE && (
        <Text size="xs" c="dimmed" mt={4}>
          y {items.length - TOPE} más.
        </Text>
      )}
    </Alert>
  )
}

export default function HistorialEtapasModal({
  abierto,
  onCerrar,
}: {
  abierto: boolean
  onCerrar: () => void
}) {
  const queryClient = useQueryClient()
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resumen, setResumen] = useState<ResumenHistorial | null>(null)
  const resetRef = useRef<() => void>(null)

  const estructura = useQuery({
    queryKey: ['estructura-archivo', 'historial'],
    queryFn: obtenerEstructuraHistorial,
    enabled: abierto,
  })

  const bajar = useMutation({ mutationFn: descargarPlantillaHistorial })

  const subir = useMutation({
    mutationFn: () => importarHistorial(archivo!),
    onSuccess: (r) => {
      setResumen(r)
      setArchivo(null)
      resetRef.current?.()
      // La carga mueve duraciones y fechas de inicio, así que se recargan la
      // bandeja, el listado y toda la reportería que los usa.
      for (const key of [
        'bandeja-negocios',
        'negocios',
        'resumen-negocios',
        'reporte-mensual',
        'vista-directorio',
      ]) {
        queryClient.invalidateQueries({ queryKey: [key] })
      }
    },
  })

  function cerrar() {
    setArchivo(null)
    setResumen(null)
    resetRef.current?.()
    onCerrar()
  }

  return (
    <Modal opened={abierto} onClose={cerrar} title="Historial de etapas" size="lg">
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          La plantilla viene <strong>pre-llenada</strong>: una fila por cada etapa desde E1 hasta
          donde está hoy cada negocio. Solo hay que escribir las fechas. Sirve para poder
          proyectar plazos, que hoy no se puede porque no hay ningún movimiento registrado.
        </Text>

        <EstructuraArchivo consulta={estructura} />

        <Group>
          <Button
            variant="light"
            leftSection={<IconDownload size={16} />}
            loading={bajar.isPending}
            onClick={() => bajar.mutate()}
          >
            Descargar plantilla pre-llenada
          </Button>

          <FileButton resetRef={resetRef} onChange={setArchivo} accept=".xlsx,.xlsm">
            {(props) => (
              <Button {...props} variant="default">
                {archivo ? archivo.name : 'Elegir archivo'}
              </Button>
            )}
          </FileButton>

          <Button
            color="accent"
            leftSection={<IconUpload size={16} />}
            disabled={!archivo}
            loading={subir.isPending}
            onClick={() => subir.mutate()}
          >
            Cargar
          </Button>
        </Group>

        {bajar.isError && (
          <Alert color="critical" variant="light">
            {(bajar.error as Error).message}
          </Alert>
        )}
        {subir.isError && (
          <Alert color="critical" variant="light" title="El archivo no se pudo leer">
            {(subir.error as Error).message}
          </Alert>
        )}

        {resumen && (
          <Stack gap="sm">
            <Alert color="good" variant="light" title="Cargado">
              <Text size="sm">
                {resumen.movimientos_creados} movimientos nuevos ·{' '}
                {resumen.movimientos_actualizados} actualizados
                {resumen.fechas_corregidas > 0 &&
                  ` · ${resumen.fechas_corregidas} ${
                    resumen.fechas_corregidas === 1
                      ? 'fecha de inicio corregida'
                      : 'fechas de inicio corregidas'
                  }`}
              </Text>
              {resumen.filas_sin_fecha > 0 && (
                <Text size="xs" c="dimmed" mt={4}>
                  {resumen.filas_sin_fecha} filas quedaron sin fecha y se ignoraron. Es lo
                  normal: se cargan las que se saben y el resto queda para después.
                </Text>
              )}
            </Alert>

            <Lista
              titulo="negocios quedaron sin cargar por fechas incoherentes"
              items={resumen.secuencia_incoherente}
              color="critical"
              ayuda="Una etapa anterior no puede tener una fecha más nueva que una posterior. La causa habitual es el año: si escribís «12-08» en una celda de fecha, Excel le pone el año actual. Corregí el año y volvé a subir el archivo."
            />

            <Lista
              titulo="filas no se pudieron aplicar"
              items={resumen.omitidas}
              color="warning"
              ayuda="El resto sí se cargó. Corregí estas y volvé a subir el archivo: recargar no duplica nada."
            />

            <Lista
              titulo="fechas quedaron antes del inicio registrado"
              items={resumen.anteriores_al_inicio}
              color="brand"
              ayuda="No es un error: es la lista de liquidaciones cuya fecha de inicio conviene corregir en la hoja LIQUIDACIONES, porque el Excel de origen les puso la fecha de cierre."
            />

            <Lista
              titulo="fechas de inicio no se corrigieron"
              items={resumen.no_corregidas_por_plata}
              color="critical"
              ayuda="La carga se negó a tocarlas: su valorización sale de la fecha de inicio, así que cambiarla movería el monto y la comisión. Hay que corregirlas a mano en la ficha, revisando la plata."
            />
          </Stack>
        )}
      </Stack>
    </Modal>
  )
}
