"""
agente_memoria.py — el mismo agente.py, ahora con memoria entre sesiones.

Esta es la Parte 4 del video. Toma el agente ya desplegable (agente.py) y le
suma AgentCore Memory, para que Ritmo recuerde al usuario entre una sesión y
otra sin que montemos ningún almacenamiento nosotros.

Compara con agente.py: lo único nuevo es el session manager de memoria, que se
construye a partir de RITMO_MEMORY_ID y se le pasa al Agent. El resto (modelo,
instrucciones, herramienta, entrypoint) es igual.

Requisito: crear una vez el recurso de memoria y exportar su ID.
    python crear_memoria.py
    export RITMO_MEMORY_ID=<el-id>

Correr como servicio de AgentCore:
    python agente_memoria.py
Desplegar:
    agentcore configure --entrypoint agente_memoria.py
    agentcore launch

Nota: Memory nunca se ha corrido de punta a punta aquí. Verificar contra la doc
actual del SDK antes de grabar (ver demo-agentcore.md, Parte 4).
"""

import os

from strands import Agent, tool

from servicio_datos import obtener_cuenta

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)


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


# --- Lo único nuevo respecto a agente.py: la memoria --------------------------
# El session manager persiste el hilo de la conversación por usuario. El código
# del agente no monta almacenamiento; declara que quiere memoria y AgentCore la
# maneja. El recurso se crea una vez con `python crear_memoria.py`.

def _crear_agente_con_memoria(session_id: str) -> Agent:
    memory_id = os.environ["RITMO_MEMORY_ID"]  # falla claro si no está configurado

    config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id="usuario-demo",
    )
    session_manager = AgentCoreMemorySessionManager(agentcore_memory_config=config)

    return Agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[consultar_cuenta],
        session_manager=session_manager,
    )


app = BedrockAgentCoreApp()


@app.entrypoint
def invocar(payload, context):
    """Puerta de entrada del agente, ahora con memoria por sesión."""
    mensaje = payload.get("prompt", "")
    if not isinstance(mensaje, str) or not mensaje.strip():
        return {"error": "El campo 'prompt' debe ser un texto no vacío"}

    session_id = getattr(context, "session_id", None) or "sesion-runtime"
    agente = _crear_agente_con_memoria(session_id)
    resultado = agente(mensaje)
    return {"result": resultado.message}


if __name__ == "__main__":
    app.run()
