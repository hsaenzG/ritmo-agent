"""
agente_langgraph.py — el mismo Ritmo, construido con LangGraph.

Este es el cierre del video (Parte 6): la prueba de que AgentCore no te casa con
un framework. Compáralo con agente.py y fíjate en qué es idéntico:

  - El entrypoint: @app.entrypoint, la misma firma (payload, context).
  - El arranque: app.run().
  - La herramienta: consultar_cuenta llama al MISMO servicio_datos.py y nunca
    toca la base directo.
  - El deploy: agentcore configure / launch / invoke, exactamente igual.

Lo ÚNICO que cambia es cómo se arma el agente por dentro: aquí es un grafo de
LangGraph en vez de un Agent de Strands.

Correr como servicio de AgentCore:
    python agente_langgraph.py
Desplegar:
    agentcore configure --entrypoint agente_langgraph.py
    agentcore launch
    agentcore invoke '{"prompt": "¿Qué plan tengo?"}'

Dependencias en requirements-langgraph.txt.
"""

from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

# La misma frontera hacia los datos que usa el agente de Strands.
from servicio_datos import obtener_cuenta

from bedrock_agentcore.runtime import BedrockAgentCoreApp


SYSTEM_PROMPT = """Eres Ritmo, el asistente de una plataforma de streaming de música.
Tono: cercano, directo, usa 'tú'. Responde en español. Máximo 3 frases.
Ayudas al usuario con dudas de su cuenta: su plan, su actividad, recomendaciones.
Nunca inventes datos de la cuenta. Si no tienes el dato, dilo y ofrece verificar."""


# La MISMA herramienta que en agente.py, con el mismo contrato. Recibe un
# usuario_id, le pide los datos al servicio, y nunca ve la base.
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


# El modelo, sobre Bedrock, igual que el agente de Strands.
llm = init_chat_model(
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    model_provider="bedrock_converse",
)

# Aquí está la única diferencia real: el agente es un grafo de LangGraph.
grafo = create_react_agent(
    llm,
    tools=[consultar_cuenta],
    prompt=SYSTEM_PROMPT,
)


# --- Entrypoint de AgentCore: idéntico al de agente.py ------------------------
app = BedrockAgentCoreApp()


@app.entrypoint
def invocar(payload, context):
    """Puerta de entrada del agente cuando corre en AgentCore."""
    mensaje = payload.get("prompt", "")
    if not isinstance(mensaje, str) or not mensaje.strip():
        return {"error": "El campo 'prompt' debe ser un texto no vacío"}

    salida = grafo.invoke({"messages": [{"role": "user", "content": mensaje}]})
    return {"result": salida["messages"][-1].content}


if __name__ == "__main__":
    app.run()
