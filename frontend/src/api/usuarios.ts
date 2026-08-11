export type RolUsuario = 'gerencia' | 'operaciones' | 'admin'

export type UsuarioAdmin = {
  id: number
  email: string
  nombre: string
  rol: RolUsuario
  activo: boolean
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function listarUsuarios(): Promise<UsuarioAdmin[]> {
  return fetch('/api/admin/usuarios', { credentials: 'include' }).then(parseOrThrow)
}

export function crearUsuario(payload: { email: string; nombre: string; password: string; rol: RolUsuario }) {
  return fetch('/api/admin/usuarios', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

export function actualizarUsuario(id: number, payload: Partial<{ email: string; nombre: string; rol: RolUsuario; activo: boolean; password: string }>) {
  return fetch(`/api/admin/usuarios/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}
