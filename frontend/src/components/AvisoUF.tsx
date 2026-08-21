import { useQuery } from '@tanstack/react-query'
import { Alert, Anchor, Text } from '@mantine/core'
import { IconAlertTriangle, IconClock } from '@tabler/icons-react'
import { Link } from 'react-router-dom'
import { obtenerEstadoUF } from '../api/uf'

/**
 * Aviso y alerta de la serie de UF, en un solo componente porque son el mismo
 * dato con dos pesos distintos (D-008):
 *
 * - `aviso` a 3 días o menos: recordatorio, discreto.
 * - `vencida` o `vacia`: alerta, porque ya no se puede valorizar con fecha de
 *   hoy y eso rompe el alta de negocios.
 *
 * Cuando la serie está sana no dibuja nada. Un aviso que se ve siempre deja de
 * ser un aviso.
 */
export default function AvisoUF() {
  const { data } = useQuery({ queryKey: ['estado-uf'], queryFn: obtenerEstadoUF })

  if (!data || data.nivel === 'ok') return null

  const grave = data.nivel === 'vencida' || data.nivel === 'vacia'

  return (
    <Alert
      color={grave ? 'critical' : 'warning'}
      variant="light"
      icon={grave ? <IconAlertTriangle size={18} /> : <IconClock size={18} />}
      title={grave ? 'La serie de UF no cubre el día de hoy' : 'Hay que cargar la UF pronto'}
    >
      <Text size="sm">
        {data.mensaje}{' '}
        <Anchor component={Link} to="/uf" size="sm">
          Cargar el nuevo tramo
        </Anchor>
      </Text>
    </Alert>
  )
}
