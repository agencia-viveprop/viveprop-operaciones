/** Espejo de `LARGO_MINIMO` del backend. La validación de verdad está allá; esto
 *  es para no dejar que alguien escriba ocho caracteres y recién al enviar se
 *  entere. */
export const LARGO_MINIMO_CLAVE = 10

export type Usuario = {
  id: number
  email: string
  nombre: string
  rol: 'gerencia' | 'operaciones' | 'admin'
  /** Clave temporal puesta por un admin. Mientras sea true, la API devuelve 403
   *  en todo salvo ver quién soy, cambiar la clave y salir. */
  debe_cambiar_password: boolean
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function fetchMe(): Promise<Usuario> {
  return fetch('/api/auth/me', { credentials: 'include' }).then(parseOrThrow)
}

export function login(email: string, password: string): Promise<Usuario> {
  return fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  }).then(parseOrThrow)
}

export function logout(): Promise<void> {
  return fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).then(() => undefined)
}

export function cambiarClave(claveActual: string, claveNueva: string): Promise<void> {
  return fetch('/api/auth/cambiar-clave', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ clave_actual: claveActual, clave_nueva: claveNueva }),
  }).then(parseOrThrow)
}
