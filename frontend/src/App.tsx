import { useQuery } from '@tanstack/react-query'
import { Center, Loader, Text } from '@mantine/core'
import { Navigate, Route, Routes } from 'react-router-dom'
import { fetchMe } from './api/auth'
import Login from './pages/Login'
import Home from './pages/Home'
import AdminUsuarios from './pages/AdminUsuarios'
import Canjes from './pages/Canjes'
import Bandeja from './pages/Bandeja'
import Negocios from './pages/Negocios'
import DashboardNegocios from './pages/DashboardNegocios'
import UF from './pages/UF'
import AppShellLayout from './components/AppShellLayout'

function App() {
  const { data: usuario, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: fetchMe,
    retry: false,
  })

  if (isLoading) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    )
  }

  if (!usuario) {
    return <Login />
  }

  return (
    <AppShellLayout usuario={usuario}>
      <Routes>
        <Route path="/" element={<Home usuario={usuario} />} />
        <Route path="/canjes" element={<Canjes puedeEditar={usuario.rol !== 'gerencia'} />} />
        <Route path="/bandeja" element={<Bandeja puedeEditar={usuario.rol !== 'gerencia'} />} />
        <Route path="/negocios" element={<Negocios puedeEditar={usuario.rol !== 'gerencia'} />} />
        <Route path="/negocios/dashboard" element={<DashboardNegocios />} />
        <Route path="/uf" element={<UF puedeEditar={usuario.rol !== 'gerencia'} />} />
        <Route
          path="/admin/usuarios"
          element={
            usuario.rol === 'admin' ? (
              <AdminUsuarios />
            ) : (
              <Center h="70vh">
                <Text c="red">No tienes permiso para ver esta página.</Text>
              </Center>
            )
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShellLayout>
  )
}

export default App
