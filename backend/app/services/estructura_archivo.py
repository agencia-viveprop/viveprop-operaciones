"""La forma que tiene que tener un archivo de carga, para poder mostrarla.

**Por qué existe.** Las dos cargas masivas --canjes y negocios-- pedían un `.xlsx`
sin decir en ninguna parte qué columnas esperaban. La de negocios tenía una
plantilla para bajar, así que la respuesta estaba dentro de un archivo que había
que descargar y abrir en Excel; la de canjes no tenía ni eso. En los dos casos la
única forma de saber si el archivo servía era subirlo y leer los errores.

La definición de las columnas ya existía en el código --`plantilla_negocios.COLUMNAS`
tiene grupo, obligatoriedad y ayuda para cada una-- pero solo se usaba para pintar
el Excel. Acá se expone tal cual, así que la pantalla y la plantilla describen lo
mismo por construcción y no pueden divergir.

**Los modelos son comunes a los dos dominios** aunque las columnas no se parezcan:
eso deja que una sola pantalla los muestre. Lo que cambia es quién los llena.
"""
from pydantic import BaseModel


class ColumnaArchivo(BaseModel):
    nombre: str
    obligatoria: bool
    ayuda: str


class GrupoColumnas(BaseModel):
    """Las columnas van agrupadas porque una lista de 32 no se lee.

    El grupo es el mismo que la plantilla pinta como encabezado superior.
    """

    nombre: str
    columnas: list[ColumnaArchivo]


class ValoresDeColumna(BaseModel):
    """Lo que una columna acepta, cuando no es texto libre.

    Sale de la base o de los enums, nunca escrito a mano: una alianza nueva
    aparece sola, igual que en la plantilla (`D-048`).
    """

    columna: str
    valores: list[str]
    nota: str | None = None


class EstructuraArchivo(BaseModel):
    titulo: str
    # De dónde sale el archivo: una plantilla que se baja, o un export externo.
    origen: str
    # Qué representa una fila. Es lo primero que hay que entender y lo que más se
    # malinterpreta: en negocios una fila es un hito, no un negocio.
    fila: str
    grupos: list[GrupoColumnas]
    valores: list[ValoresDeColumna]
    notas: list[str] = []

    @property
    def total_columnas(self) -> int:
        return sum(len(g.columnas) for g in self.grupos)
