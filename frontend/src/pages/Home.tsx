import { useState } from 'react'
import { Group, SegmentedControl, Stack } from '@mantine/core'
import { IconArrowsExchange, IconBriefcase } from '@tabler/icons-react'
import type { Usuario } from '../api/auth'
import PageHeader from '../components/PageHeader'
import DashboardCanjes from '../components/DashboardCanjes'
import DashboardNegocios from './DashboardNegocios'

/**
 * Inicio hospeda los dos dashboards, con un selector para alternar.
 *
 * Van en la misma pantalla porque quien entra a la app quiere ver cómo va todo,
 * y tener que acordarse de que negocios estaba en otro lugar del menú hacía que
 * ese dashboard se mirara menos. Pero **no van uno debajo del otro**: son dos
 * tipos de gestión distintos, con métricas que no se comparan entre sí, y
 * apilarlos invitaría a leerlos como un solo tablero.
 *
 * El selector no recuerda la elección entre visitas. Se puede agregar, pero
 * guardar estado de interfaz merece su propia decisión y no se colaba acá.
 */
export default function Home({ usuario }: { usuario: Usuario }) {
  const [vista, setVista] = useState('canjes')

  return (
    <Stack gap="lg">
      <PageHeader
        title="Centro de Control"
        subtitle={`Bienvenido, ${usuario.nombre} · ${usuario.email}`}
        action={
          <SegmentedControl
            // El mismo coral del enlace activo del menú, con texto blanco: es el
            // color de "esto es lo que estás mirando" en toda la app. Mantine
            // calcula el blanco solo al recibir `color`, y no cambia la forma
            // del control -- solo le saca la sombra del pill activo, que el
            // menú tampoco tiene.
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
        }
      />

      {vista === 'canjes' ? <DashboardCanjes /> : <DashboardNegocios embebido />}
    </Stack>
  )
}
