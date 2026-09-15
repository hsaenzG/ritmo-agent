"""
agente_memoria.py — el mismo agente.py, ahora con memoria de conversación.

Esta es la Parte 4 del video. Toma el agente ya desplegable (agente.py) y le
suma AgentCore Memory, para que Ritmo recuerde el hilo de la conversación sin que
montemos ningún almacenamiento nosotros.

Usamos memoria de CORTO PLAZO: AgentCore guarda los turnos de una sesión y los
trae de vuelta en cada respuesta. Mientras el usuario siga en la misma sesión,
Ritmo recuerda lo que ya se dijeron (por ejemplo, un gusto musical que mencionó
antes) y lo usa para responder mejor.

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
    agentcore deploy
"""

import os
import re

from strands import Agent, tool

from servicio_datos import obtener_cuenta

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)


# Modelo sobre Amazon Bedrock. Nova Lite: rápido, barato y disponible en la región.
MODELO = "us.amazon.nova-lite-v1:0"

# Sesión por defecto para la demo local. Al ser fija, si reinicias el proceso
# Ritmo se reconecta al mismo hilo y recuerda lo que ya se dijeron. En AgentCore
# el session_id real lo pone el runtime por cada usuario (ver invocar()).
SESION_DEMO = "sesion-demo-ritmo"

SYSTEM_PROMPT = """Eres Ritmo, el asistente de una plataforma de streaming de música.
Tono: cercano, directo, usa 'tú'. Responde en español. Máximo 3 frases.
Ayudas al usuario con dudas de su cuenta: su plan, su actividad, recomendaciones.
Usa lo que el usuario te haya contado antes en la conversación (por ejemplo, sus
gustos musicales) para responder mejor. Nunca inventes datos de la cuenta: si no
tienes el dato, dilo y ofrece verificar.
Responde solo con el mensaje final para el usuario. No muestres tu razonamiento
ni uses etiquetas como <thinking>."""


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
# El session manager persiste el hilo de la conversación por sesión. El código
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
        model=MODELO,
        system_prompt=SYSTEM_PROMPT,
        tools=[consultar_cuenta],
        session_manager=session_manager,
    )


def _solo_texto(message) -> str:
    """Extrae el texto de la respuesta y quita bloques <thinking> del modelo.

    Algunos modelos (como Nova) a veces incluyen su razonamiento entre etiquetas
    <thinking>. Al usuario solo le mostramos el mensaje final, limpio.
    """
    partes = message.get("content", []) if isinstance(message, dict) else []
    texto = "".join(p.get("text", "") for p in partes)
    texto = re.sub(r"<thinking>.*?</thinking>", "", texto, flags=re.DOTALL)
    return texto.strip()


app = BedrockAgentCoreApp()


@app.entrypoint
def invocar(payload, context=None):
    """Puerta de entrada del agente, ahora con memoria por sesión."""
    mensaje = payload.get("prompt", "")
    if not isinstance(mensaje, str) or not mensaje.strip():
        return {"error": "El campo 'prompt' debe ser un texto no vacío"}

    # En AgentCore el runtime trae un session_id por usuario; en local usamos la
    # sesión fija de la demo para que el hilo se conserve entre reinicios.
    session_id = getattr(context, "session_id", None) or SESION_DEMO
    agente = _crear_agente_con_memoria(session_id)
    resultado = agente(mensaje)
    return {"result": _solo_texto(resultado.message)}


if __name__ == "__main__":
    app.run()
