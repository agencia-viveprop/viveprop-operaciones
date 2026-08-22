from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://user:pass@localhost:5432/viveprop_operaciones"
    environment: str = "development"
    allowed_origins: str = "http://localhost:5173"
    # Las tareas periodicas del proceso (hoy: la descarga de UF desde el SII).
    # Se puede apagar por variable de entorno sin tocar codigo, y los tests la
    # apagan para no salir a la red.
    tareas_de_fondo: bool = True
    # Dominios de email que se aceptan al crear usuarios, separados por coma.
    # Vacio desactiva la restriccion; el default es el de la empresa porque una
    # app interna con las comisiones adentro no deberia poder invitar a un correo
    # cualquiera por un dedazo.
    dominios_email: str = "viveprop.com"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def dominios_email_lista(self) -> list[str]:
        return [d.strip().lower() for d in self.dominios_email.split(",") if d.strip()]

    @property
    def es_local(self) -> bool:
        """Si el ambiente es una máquina de desarrollo servida por HTTP.

        Solo estos tres valores exactos cuentan como local. Es al revés de como
        estaba antes: `secure` de la cookie se activaba solo si
        `environment == "production"`, así que si la variable de entorno faltaba
        o venía con un typo la cookie de sesión salía **sin** `secure` sobre
        HTTPS, en silencio y sin que nada fallara.

        Ahora un valor desconocido cae del lado seguro. Y un typo en la
        configuración local falla ruidoso -- el navegador no guarda una cookie
        `secure` sobre `http://localhost` y el login deja de funcionar de
        inmediato -- que es la dirección correcta para que un error se note.
        """
        return self.environment.strip().lower() in {"development", "local", "test"}


settings = Settings()
