export type RolUsuario = 'gerencia' | 'operaciones' | 'admin'

export type UsuarioAdmin = {
  id: number
  email: string
  nombre: string
  rol: RolUsuario
  activo: boolean
  debe_cambiar_password: boolean
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

export type ClaveReseteada = {
  usuario_id: number
  email: string
  clave_temporal: string
}

/** Genera una clave temporal, cierra las sesiones de esa persona y la obliga a
 *  elegir una nueva al entrar. La temporal se devuelve **una sola vez**: lo que
 *  queda guardado es su hash. */
export function resetearClave(id: number): Promise<ClaveReseteada> {
  return fetch(`/api/admin/usuarios/${id}/resetear-clave`, {
    method: 'POST',
    credentials: 'include',
  }).then(parseOrThrow)
}
