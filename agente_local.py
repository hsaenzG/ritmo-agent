"""
agente_local.py — Ritmo corriendo SOLO en tu laptop.

Esta es la primera versión que se muestra en el video. No tiene una sola línea
de AgentCore. Es un agente de Strands puro: modelo, instrucciones, una
herramienta, la función invocar y un loop de chat en la terminal.

El punto de este archivo es enseñar el agente "antes": funciona, pero solo aquí.
Si cierras la terminal, deja de existir. La versión con AgentCore (agente.py)
toma exactamente este mismo agente y la misma función invocar, y les agrega
cuatro líneas para llevarlo a producción. Compáralos lado a lado.

Correr:
    python agente_local.py
Escribe una pregunta. Escribe "salir" para terminar.

La regla del proyecto ya vive aquí: el agente NUNCA importa la base de datos ni
arma consultas. Solo llama a la herramienta consultar_cuenta, y esa herramienta
le pide los datos a servicio_datos.py.
"""

from strands import Agent, tool

# El agente importa la HERRAMIENTA hacia el servicio, no la base de datos.
from servicio_datos import obtener_cuenta


SYSTEM_PROMPT = """Eres Ritmo, el asistente de una plataforma de streaming de música.
Tono: cercano, directo, usa 'tú'. Responde en español. Máximo 3 frases.
Ayudas al usuario con dudas de su cuenta: su plan, su actividad, recomendaciones.
Nunca inventes datos de la cuenta. Si no tienes el dato, dilo y ofrece verificar."""


@tool
def consultar_cuenta(usuario_id: str) -> str:
    """Devuelve el resumen de la cuenta del usuario: plan, precio, renovación y actividad.
    Úsala cuando el usuario pregunte por su plan, facturación o su actividad de escucha.

    usuario_id: identificador del usuario
    """
    cuenta = obtener_cuenta(usuario_id)
    if cuenta is None:
        return "No encuentro esa cuenta. ¿Puedes confirmar el identificador?"
    return (
        f"Plan {cuenta['plan']}, ${cuenta['precio_mxn']} MXN al mes, "
        f"renueva el {cuenta['renovacion']}. "
        f"Este mes: {cuenta['horas_mes']} horas escuchadas."
    )


agente = Agent(system_prompt=SYSTEM_PROMPT, tools=[consultar_cuenta])


def invocar(payload, context=None):
    """Puerta de entrada del agente. Recibe {"prompt": ...} y devuelve un dict."""
    mensaje = payload.get("prompt", "")
    if not isinstance(mensaje, str) or not mensaje.strip():
        return {"error": "El campo 'prompt' debe ser un texto no vacío"}

    resultado = agente(mensaje)
    return {"result": resultado.message}


if __name__ == "__main__":
    print("Ritmo (local). Escribe 'salir' para terminar.\n")
    while True:
        pregunta = input("\nUsuario: ")
        if pregunta.lower() == "salir":
            break
        print("\nRitmo: ", end="")
        invocar({"prompt": pregunta})
        print()
