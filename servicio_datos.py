"""
servicio_datos.py

La ÚNICA capa que habla con los datos. El agente no la ve.

Hoy es un diccionario en memoria. Mañana puede ser una consulta a una base de
datos real o una llamada a otra parte de tu aplicación. El agente no se entera
del cambio: la herramienta que lo usa mantiene el mismo contrato de entrada y
salida.

Este archivo es el punto de la decisión de diseño del proyecto: el agente nunca
importa esto directamente ni arma consultas. Solo la herramienta `consultar_cuenta`
(en agente.py) lo llama.
"""


# Datos de ejemplo. En un sistema real esto vive en una base de datos detrás de
# este servicio, no en el proceso del agente.
_USUARIOS = {
    "u-1042": {
        "plan": "Premium",
        "precio_mxn": 99,
        "renovacion": "1 de octubre",
        "horas_mes": 47,
        "generos_top": ["indie", "jazz", "electrónica"],
    },
}


def obtener_cuenta(usuario_id: str) -> dict | None:
    """Devuelve los datos de la cuenta de un usuario, o None si no existe.

    Esta es la frontera con los datos. Si mañana esto consulta una base real,
    la firma no cambia: recibe un usuario_id, devuelve un dict o None.
    """
    return _USUARIOS.get(usuario_id)
