import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Alert, Button, Modal, PasswordInput, Stack } from '@mantine/core'
import { cambiarClave } from '../api/auth'

export default function CambiarClaveModal({ opened, onClose }: { opened: boolean; onClose: () => void }) {
  const [actual, setActual] = useState('')
  const [nueva, setNueva] = useState('')
  const [confirmar, setConfirmar] = useState('')

  function cerrar() {
    setActual('')
    setNueva('')
    setConfirmar('')
    mutation.reset()
    onClose()
  }

  const mutation = useMutation({
    mutationFn: () => cambiarClave(actual, nueva),
    onSuccess: cerrar,
  })

  const noCoinciden = confirmar.length > 0 && nueva !== confirmar

  return (
    <Modal opened={opened} onClose={cerrar} title="Cambiar mi contraseña">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (!noCoinciden) mutation.mutate()
        }}
      >
        <Stack gap="sm">
          <PasswordInput label="Contraseña actual" required value={actual} onChange={(e) => setActual(e.currentTarget.value)} />
          <PasswordInput label="Contraseña nueva" required value={nueva} onChange={(e) => setNueva(e.currentTarget.value)} />
          <PasswordInput
            label="Confirmar contraseña nueva"
            required
            value={confirmar}
            onChange={(e) => setConfirmar(e.currentTarget.value)}
            error={noCoinciden ? 'No coincide con la contraseña nueva' : undefined}
          />
          {mutation.isError && <Alert color="critical" variant="filled">{(mutation.error as Error).message}</Alert>}
          <Button type="submit" loading={mutation.isPending} disabled={noCoinciden}>
            Guardar
          </Button>
        </Stack>
      </form>
    </Modal>
  )
}
