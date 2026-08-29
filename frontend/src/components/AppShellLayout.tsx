import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  AppShell,
  Avatar,
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

  return (
    <AppShell navbar={{ width: 260, breakpoint: 'sm' }} padding="md">
      <AppShell.Navbar p="md" style={{ justifyContent: 'space-between', display: 'flex', flexDirection: 'column' }}>
        <Stack gap="lg">
          <Group gap="xs" px="xs">
            <Logo />
          </Group>

          <Stack gap={4}>
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

          <Stack gap={4}>
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
            <Stack gap={4}>
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
