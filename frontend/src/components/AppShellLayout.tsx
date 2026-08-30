import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  AppShell,
  Avatar,
  Burger,
  Group,
  Menu,
  NavLink,
  Stack,
  Text,
  UnstyledButton,
  useComputedColorScheme,
  useMantineColorScheme,
} from '@mantine/core'
import {
  IconArrowsExchange,
  IconBriefcase,
  IconCalendarMonth,
  IconCalendarStats,
  IconCoin,
  IconHome2,
  IconInbox,
  IconKey,
  IconLogout,
  IconPresentation,
  IconReceipt,
  IconMoon,
  IconSun,
  IconUsers,
} from '@tabler/icons-react'
import { useDisclosure, useMediaQuery } from '@mantine/hooks'
import { Link, useLocation } from 'react-router-dom'
import { logout, type Usuario } from '../api/auth'
import CambiarClaveModal from './CambiarClaveModal'
import Logo from './Logo'

export default function AppShellLayout({ usuario, children }: { usuario: Usuario; children: React.ReactNode }) {
  const queryClient = useQueryClient()
  const location = useLocation()
  const { toggleColorScheme } = useMantineColorScheme()
  const computedColorScheme = useComputedColorScheme('light')
  const [cambiarClaveAbierto, setCambiarClaveAbierto] = useState(false)
  const [menuAbierto, { toggle: alternarMenu, close: cerrarMenu }] = useDisclosure(false)

  // **El mismo corte que usa la barra**, escrito en `em` porque los puntos de
  // corte de Mantine son en `em`: `sm` son 48em. Si acá dijera 768px, un usuario
  // con la letra agrandada tendría la cabecera y la barra en desacuerdo, y ese
  // desacuerdo es justamente el defecto que se está arreglando.
  //
  // `getInitialValueInEffect: false` mide en el primer render en vez de esperar
  // un efecto: la app es una SPA sin renderizado en servidor, así que el valor
  // está disponible, y esperarlo hacía aparecer la cabecera por un instante en
  // pantalla grande.
  const compacto = useMediaQuery('(max-width: 47.99em)', false, {
    getInitialValueInEffect: false,
  })

  // Navegar cierra el menú. Sin esto, en teléfono se elige una pantalla y la
  // barra queda encima tapándola, que es exactamente lo que uno acaba de pedir
  // que se quite.
  useEffect(() => {
    cerrarMenu()
  }, [location.pathname, cerrarMenu])

  return (
    <AppShell
      // La cabecera existe **solo en pantalla chica**. En PC va colapsada, así
      // que no reserva alto y la app se ve igual que siempre: el pedido fue
      // arreglar el teléfono, no rediseñar el escritorio.
      header={{ height: 56, collapsed: !compacto }}
      // `collapsed.mobile` es lo que faltaba. Sin esta línea la barra se dibuja
      // **encima** del contenido bajo el punto de corte --Mantine deja de
      // correr el contenido pero no esconde la barra-- y no había ningún control
      // para sacarla del camino.
      navbar={{ width: 260, breakpoint: 'sm', collapsed: { mobile: !menuAbierto } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Burger
              opened={menuAbierto}
              onClick={alternarMenu}
              size="sm"
              aria-label={menuAbierto ? 'Cerrar el menú' : 'Abrir el menú'}
            />
            <Logo height={22} />
          </Group>
          {/* El tema se repite acá porque el que ya existía vive al pie de la
              barra, y en teléfono la barra arranca cerrada: dejarlo solo ahí lo
              volvía un ajuste escondido detrás de dos clics. El resto --usuario,
              contraseña, salir-- sigue en un solo lugar, dentro de la barra. */}
          <ActionIcon variant="subtle" onClick={toggleColorScheme} aria-label="Cambiar tema">
            {computedColorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
          </ActionIcon>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md" style={{ justifyContent: 'space-between', display: 'flex', flexDirection: 'column' }}>
        <Stack gap="lg">
          <Group gap="xs" px="xs">
            <Logo />
          </Group>

          <Stack gap={4} onClick={cerrarMenu}>
            <Text size="xs" fw={700} c="dimmed" px="xs">
              GESTIÓN
            </Text>
            <NavLink
              component={Link}
              to="/"
              label="Inicio"
              description="Dashboards de canjes y negocios"
              leftSection={<IconHome2 size={18} />}
              active={location.pathname === '/'}
              variant="filled"
            />
          </Stack>

          <Stack gap={4} onClick={cerrarMenu}>
            <Text size="xs" fw={700} c="dimmed" px="xs">
              OPERACIONES
            </Text>
            <NavLink
              component={Link}
              to="/bandeja"
              label="Qué me toca hoy"
              leftSection={<IconInbox size={18} />}
              active={location.pathname === '/bandeja'}
              variant="filled"
            />
            <NavLink
              component={Link}
              to="/canjes"
              label="Canjes"
              leftSection={<IconArrowsExchange size={18} />}
              active={location.pathname === '/canjes'}
              variant="filled"
            />
            <NavLink
              component={Link}
              to="/negocios"
              label="Negocios"
              leftSection={<IconBriefcase size={18} />}
              active={location.pathname === '/negocios'}
              variant="filled"
            />
            <NavLink
              component={Link}
              to="/cobranza"
              label="Cobranza"
              leftSection={<IconReceipt size={18} />}
              active={location.pathname === '/cobranza'}
              variant="filled"
            />
            <NavLink
              component={Link}
              to="/reportes/semanal"
              label="Reporte semanal"
              leftSection={<IconCalendarStats size={18} />}
              active={location.pathname === '/reportes/semanal'}
              variant="filled"
            />
            <NavLink
              component={Link}
              to="/reportes/mensual"
              label="Reporte mensual"
              leftSection={<IconCalendarMonth size={18} />}
              active={location.pathname === '/reportes/mensual'}
              variant="filled"
            />
            <NavLink
              component={Link}
              to="/reportes/directorio"
              label="Vista directorio"
              leftSection={<IconPresentation size={18} />}
              active={location.pathname === '/reportes/directorio'}
              variant="filled"
            />
          </Stack>

          {usuario.rol === 'admin' && (
            <Stack gap={4} onClick={cerrarMenu}>
              <Text size="xs" fw={700} c="dimmed" px="xs">
                ADMIN
              </Text>
              <NavLink
                component={Link}
                to="/admin/usuarios"
                label="Usuarios"
                leftSection={<IconUsers size={18} />}
                active={location.pathname === '/admin/usuarios'}
                variant="filled"
              />
              <NavLink
                component={Link}
                to="/uf"
                label="Unidad de Fomento"
                leftSection={<IconCoin size={18} />}
                active={location.pathname === '/uf'}
                variant="filled"
              />
            </Stack>
          )}
        </Stack>

        <Stack gap="sm">
          <Group justify="space-between" px="xs">
            <Menu position="top-start" width={220} shadow="md">
              <Menu.Target>
                <UnstyledButton>
                  <Group gap="xs">
                    <Avatar color="accent" radius="xl" size="sm">
                      {usuario.nombre.charAt(0).toUpperCase()}
                    </Avatar>
                    <div>
                      <Text size="sm" fw={600}>
                        {usuario.nombre}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {usuario.rol}
                      </Text>
                    </div>
                  </Group>
                </UnstyledButton>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item leftSection={<IconKey size={16} />} onClick={() => setCambiarClaveAbierto(true)}>
                  Cambiar mi contraseña
                </Menu.Item>
                {usuario.rol === 'admin' && (
                  <Menu.Item leftSection={<IconUsers size={16} />} component={Link} to="/admin/usuarios">
                    Administrar usuarios
                  </Menu.Item>
                )}
                <Menu.Divider />
                <Menu.Item
                  color="critical"
                  leftSection={<IconLogout size={16} />}
                  onClick={async () => {
                    await logout()
                    queryClient.setQueryData(['me'], null)
                  }}
                >
                  Salir
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
            <ActionIcon variant="subtle" onClick={toggleColorScheme} aria-label="Cambiar tema">
              {computedColorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
            </ActionIcon>
          </Group>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
      <CambiarClaveModal opened={cambiarClaveAbierto} onClose={() => setCambiarClaveAbierto(false)} />
    </AppShell>
  )
}
