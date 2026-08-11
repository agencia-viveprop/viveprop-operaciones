import { useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  AppShell,
  Avatar,
  Group,
  NavLink,
  Stack,
  Text,
  Title,
  useComputedColorScheme,
  useMantineColorScheme,
} from '@mantine/core'
import { IconHome2, IconLogout, IconMoon, IconSun, IconUsers } from '@tabler/icons-react'
import { Link, useLocation } from 'react-router-dom'
import { logout, type Usuario } from '../api/auth'

export default function AppShellLayout({ usuario, children }: { usuario: Usuario; children: React.ReactNode }) {
  const queryClient = useQueryClient()
  const location = useLocation()
  const { toggleColorScheme } = useMantineColorScheme()
  const computedColorScheme = useComputedColorScheme('light')

  return (
    <AppShell navbar={{ width: 260, breakpoint: 'sm' }} padding="md">
      <AppShell.Navbar p="md" style={{ justifyContent: 'space-between', display: 'flex', flexDirection: 'column' }}>
        <Stack gap="lg">
          <Group gap="xs" px="xs">
            <Title order={4} c="brand">
              viveprop
            </Title>
          </Group>

          <Stack gap={4}>
            <Text size="xs" fw={700} c="dimmed" px="xs">
              GESTIÓN
            </Text>
            <NavLink
              component={Link}
              to="/"
              label="Inicio"
              leftSection={<IconHome2 size={18} />}
              active={location.pathname === '/'}
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
            </Stack>
          )}
        </Stack>

        <Stack gap="sm">
          <Group justify="space-between" px="xs">
            <Group gap="xs">
              <Avatar color="brand" radius="xl" size="sm">
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
            <ActionIcon variant="subtle" onClick={toggleColorScheme} aria-label="Cambiar tema">
              {computedColorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
            </ActionIcon>
          </Group>
          <NavLink
            label="Salir"
            leftSection={<IconLogout size={18} />}
            onClick={async () => {
              await logout()
              queryClient.setQueryData(['me'], null)
            }}
          />
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
