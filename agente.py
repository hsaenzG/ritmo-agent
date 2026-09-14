"""
agente.py — el mismo Ritmo de agente_local.py, ahora listo para producción.

Compara este archivo con agente_local.py. El agente por dentro es IDÉNTICO:
el mismo modelo, las mismas instrucciones, la misma herramienta que llama al
mismo servicio, y la MISMA función invocar. La ÚNICA diferencia son las cuatro
líneas de AgentCore, marcadas abajo. Eso es todo lo que hace falta para que algo
externo pueda invocar al agente.

Fíjate: la función invocar no cambia entre las dos versiones. En agente_local.py
la llama un loop de terminal; aquí la registra AgentCore como entrypoint. La
lógica del agente es la misma; solo cambia quién toca la puerta.

Este archivo se mantiene deliberadamente limpio: nada de memoria ni de otras
capas, para que la comparación lado a lado con agente_local.py sea exacta. La
memoria vive en agente_memoria.py (Parte 4 del video).

Correr como servicio de AgentCore (levanta el servidor en el puerto 8080):
    python agente.py
Invocarlo mientras corre:
    curl -X POST http://localhost:8080/invocations \
         -H "Content-Type: application/json" \
         -d '{"prompt": "¿Qué plan tengo?"}'

Es también lo que corre cuando se despliega:
    agentcore configure --entrypoint agente.py
    agentcore launch
    agentcore invoke '{"prompt": "¿Qué plan tengo?"}'
"""

from strands import Agent, tool

from servicio_datos import obtener_cuenta

# --- Línea 1 de AgentCore: importar -------------------------------------------
from bedrock_agentcore.runtime import BedrockAgentCoreApp


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


# --- Línea 2 de AgentCore: inicializar ----------------------------------------
app = BedrockAgentCoreApp()

# --- Línea 3 de AgentCore: marcar invocar como la puerta de entrada -----------
app.entrypoint(invocar)

# --- Línea 4 de AgentCore: correr ---------------------------------------------
if __name__ == "__main__":
    app.run()
