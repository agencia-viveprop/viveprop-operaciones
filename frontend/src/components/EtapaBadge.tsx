import { Badge, Tooltip } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { obtenerCatalogos } from '../api/catalogos'

/**
 * La etapa de un negocio como insignia: el código a la vista, el nombre al pasar
 * el mouse.
 *
 * El código es lo que cabe en una columna angosta y es el vocabulario con el que
 * se habla del pipeline --«está en E2»--, pero por sí solo no dice qué falta
 * hacer, y son siete. El nombre lo dice y **sale del catálogo**: una copia de los
 * siete rótulos escrita en la pantalla se despega de la tabla en cuanto alguien
 * renombra una etapa, que es el mismo error que ya se corrigió con los rótulos
 * de canje en el reporte semanal.
 *
 * Vive en su propio componente porque la misma insignia va en el listado de
 * Negocios y en «Qué me toca hoy»: con el tooltip en uno y no en el otro hay que
 * recordar dónde funciona.
 *
 * El caso «sin etapa» se queda en quien llama: cada pantalla ya tenía resuelto
 * cómo dibujar el vacío de su tabla y no hay razón para uniformarlo desde acá.
 */
export default function EtapaBadge({ codigo }: { codigo: string }) {
  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const nombre = catalogos?.etapas.find((e) => e.codigo === codigo)?.nombre
  const insignia = <Badge variant="default">{codigo}</Badge>

  // Sin nombre no hay tooltip: un globo vacío es peor que ninguno. Pasa mientras
  // el catálogo viaja, y con un código que ya no esté en la tabla.
  if (!nombre) return insignia

  return (
    <Tooltip label={nombre} withArrow openDelay={200}>
      {insignia}
    </Tooltip>
  )
}
