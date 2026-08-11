import type { Usuario } from '../api/auth'
import PageHeader from '../components/PageHeader'

export default function Home({ usuario }: { usuario: Usuario }) {
  return (
    <PageHeader
      title={`Bienvenido, ${usuario.nombre}`}
      subtitle={`${usuario.email} · rol: ${usuario.rol}`}
    />
  )
}
