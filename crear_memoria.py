"""
crear_memoria.py — crea el recurso de AgentCore Memory para Ritmo.

Se corre UNA sola vez. Crea la memoria, espera a que quede ACTIVA e imprime su
ID. Copia ese ID a la variable de entorno RITMO_MEMORY_ID y agente_memoria.py
activará la memoria solo.

    python crear_memoria.py
    export RITMO_MEMORY_ID=<el-id-que-imprime>

Usamos memoria de CORTO PLAZO: AgentCore guarda el hilo de la conversación de una
sesión y lo trae de vuelta cuando el agente responde. Con eso Ritmo mantiene el
contexto de lo que se han dicho dentro de la sesión, sin que nosotros montemos
ningún almacenamiento. (La memoria de largo plazo entre sesiones distintas existe
en AgentCore vía estrategias, pero no la usamos aquí para mantener la demo simple.)

Necesita credenciales de AWS con acceso a AgentCore Memory en tu región.
La creación es asíncrona y tarda ~1-2 min: créala ANTES de grabar, no en cámara.
Después de grabar, borra el recurso para no dejar cosas colgando en la cuenta.
"""

import os

from bedrock_agentcore.memory import MemoryClient


def main():
    region = os.environ.get("AWS_REGION", "us-west-2")
    client = MemoryClient(region_name=region)

    print("Creando la memoria y esperando a que quede ACTIVA (puede tardar ~1-2 min)...")

    # create_memory_and_wait bloquea hasta que el recurso está ACTIVE, así que el
    # agente no fallará con "Memory status is not active" al usarla enseguida.
    memoria = client.create_memory_and_wait(
        name="RitmoMemory",
        description="Memoria de conversación del asistente Ritmo (demo).",
        strategies=[],  # corto plazo: sin estrategias de largo plazo
    )

    memory_id = memoria.get("id")
    print("\nMemoria ACTIVA y lista para usar.")
    print(f"  ID: {memory_id}")
    print("\nExporta esto en tu terminal para activarlo en el agente:")
    print(f"  export RITMO_MEMORY_ID={memory_id}\n")


if __name__ == "__main__":
    main()
