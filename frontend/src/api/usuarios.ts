export type RolUsuario = 'gerencia' | 'operaciones' | 'admin'

export type UsuarioAdmin = {
  id: number
  email: string
  nombre: string
  rol: RolUsuario
  activo: boolean
  debe_cambiar_password: boolean
  /** Su correo no era de un dominio de la organizacion y un admin lo autorizo.
   *  Es un hecho del pasado: sigue siendo cierto aunque despues se agregue ese
   *  dominio a la lista. */
  es_externo: boolean
  externo_autorizado_por: string | null
  externo_autorizado_en: string | null
}

/** Un dominio de correo de la organizacion: los que entran sin pedir permiso. */
export type DominioOrganizacion = {
  id: number
  dominio: string
  nombre: string
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

export function crearUsuario(payload: {
  email: string
  nombre: string
  password: string
  rol: RolUsuario
  /** El admin declara que sabe que el correo no es de la organizacion y que
   *  autoriza igual ese acceso. La API lo exige; la pantalla lo pregunta. */
  autoriza_externo?: boolean
}) {
  return fetch('/api/admin/usuarios', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

export function actualizarUsuario(
  id: number,
  payload: Partial<{
    email: string
    nombre: string
    rol: RolUsuario
    activo: boolean
    password: string
    autoriza_externo: boolean
  }>,
) {
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


// ------------------------------------------- dominios de la organizacion

export function listarDominios(): Promise<DominioOrganizacion[]> {
  return fetch('/api/admin/dominios', { credentials: 'include' }).then(parseOrThrow)
}

/** Acepta un dominio, un `@dominio` o un correo completo: el backend se queda
 *  con el dominio. `nombre` es para leer la lista y es opcional. */
export function agregarDominio(payload: { dominio: string; nombre?: string }) {
  return fetch('/api/admin/dominios', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

/** Lo apaga, no lo borra, y **no le saca el acceso a nadie**: la lista se aplica
 *  al crear un usuario o al cambiarle el correo. Para cortar un acceso existe el
 *  switch de activo del usuario. */
export function desactivarDominio(id: number) {
  return fetch(`/api/admin/dominios/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  }).then(parseOrThrow)
}
